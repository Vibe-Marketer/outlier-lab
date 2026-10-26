"""Persistent, bounded Apify profile jobs. HTTP requests only queue or poll work."""
import hashlib
import json
import queue
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

from storage import write_json

TERMINAL = {"succeeded", "failed"}


def apify_request(path, token, body=None, **params):
    url = "https://api.apify.com/v2/" + path + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.load(response)


class ProfileJobs:
    def __init__(self, state_file, token_loader, normalize, apply_profiles, profile_error,
                 request=apify_request, poll_seconds=3, daily_cap=0.50):
        self.state_file = state_file
        self.token_loader = token_loader
        self.normalize = normalize
        self.apply_profiles = apply_profiles
        self.profile_error = profile_error
        self.request = request
        self.poll_seconds = poll_seconds
        self.daily_cap = daily_cap
        self.lock = threading.RLock()
        self.stop = threading.Event()
        self.queue = queue.Queue()
        self.jobs = json.loads(state_file.read_text()) if state_file.exists() else {}
        for job in self.jobs.values():
            if job["status"] == "starting" and not job.get("runId"):
                job.update(status="failed", message="Run submission was interrupted. Check Apify before retrying; creators remain saved.")
                if job["kind"] == "profiles":
                    self.profile_error(job["value"], job["message"])
            elif job["status"] not in TERMINAL:
                self.queue.put(job["id"])
        if self.jobs:
            self._save()
        self.worker = threading.Thread(target=self._work, daemon=True)
        self.worker.start()

    def _save(self):
        write_json(self.state_file, self.jobs)

    def _update(self, job_id, **updates):
        with self.lock:
            self.jobs[job_id].update(updates)
            self._save()

    def get(self, job_id):
        with self.lock:
            job = self.jobs.get(job_id)
            return json.loads(json.dumps(job)) if job else None

    def recent(self):
        with self.lock:
            return [self.get(j["id"]) for j in sorted(self.jobs.values(), key=lambda j: j["createdAt"], reverse=True)[:20]]

    def submit(self, kind, value):
        if kind not in {"profiles", "search"}:
            raise ValueError("Unknown profile job.")
        value = sorted(set(value)) if kind == "profiles" else value.strip().lower()
        key = hashlib.sha256(json.dumps([kind, value]).encode()).hexdigest()
        now = time.time()
        with self.lock:
            for job in reversed(list(self.jobs.values())):
                if job["key"] == key and job["status"] == "failed" and job.get("runId") and not job.get("runTerminalFailure") and now - job["createdAt"] < 86400:
                    job.update(status="queued", message="Resuming the existing lookup; no new paid run is being started.")
                    self._save()
                    self.queue.put(job["id"])
                    return self.get(job["id"])
                lifetime = 86400 if job["status"] == "succeeded" else 300
                if job["key"] == key and (job["status"] not in TERMINAL or now - job["createdAt"] < lifetime):
                    return self.get(job["id"])
            cap = 0.10 if kind == "profiles" else 0.03
            reserved = sum(j["capUsd"] for j in self.jobs.values() if now - j["createdAt"] < 86400)
            if reserved + cap > self.daily_cap + 1e-9:
                raise ValueError("Daily profile-lookup budget reached. Handles can still be saved; try loading details tomorrow.")
            job_id = uuid.uuid4().hex
            self.jobs[job_id] = {"id": job_id, "key": key, "kind": kind, "value": value,
                                 "createdAt": now, "capUsd": cap, "status": "queued", "message": "Waiting to load Instagram profile details."}
            self._save()
            self.queue.put(job_id)
            return self.get(job_id)

    def _work(self):
        while not self.stop.is_set():
            try:
                job_id = self.queue.get(timeout=0.2)
            except queue.Empty:
                continue
            try:
                self._run(job_id)
            except Exception as error:
                if self.stop.is_set():
                    return
                message = f"Apify returned HTTP {error.code}." if isinstance(error, urllib.error.HTTPError) else "Profile details are temporarily unavailable. Saved creators have not been removed."
                self._update(job_id, status="failed", message=message)
                job = self.get(job_id)
                if job["kind"] == "profiles":
                    try:
                        self.profile_error(job["value"], message)
                    except OSError:
                        pass
            finally:
                self.queue.task_done()

    def _get(self, path, token, **params):
        for attempt in range(3):
            try:
                return self.request(path, token, **params)
            except urllib.error.HTTPError as error:
                if error.code not in {429, 500, 502, 503, 504} or attempt == 2:
                    raise
            except (urllib.error.URLError, TimeoutError):
                if attempt == 2:
                    raise
            if self.stop.wait(attempt + 1):
                raise InterruptedError("Worker stopped; resume saved run later")

    def _run(self, job_id):
        job = self.get(job_id)
        token = self.token_loader()
        if not token:
            raise ValueError("Missing token")
        if not job.get("runId"):
            body = ({"directUrls": [f"https://www.instagram.com/{h}/" for h in job["value"]], "resultsType": "details", "resultsLimit": 1}
                    if job["kind"] == "profiles" else
                    {"search": job["value"], "searchType": "user", "searchLimit": 5, "resultsType": "details", "resultsLimit": 1})
            self._update(job_id, status="starting", message="Starting Instagram profile lookup…")
            # Do not retry this POST: an uncertain response must not start another paid run.
            run = self.request("acts/apify~instagram-scraper/runs", token, body,
                               maxTotalChargeUsd=job["capUsd"], timeout=300)["data"]
            self._update(job_id, runId=run["id"], status="running", message="Instagram is still responding. You can keep using the admin.")
        else:
            run = self._get("actor-runs/" + job["runId"], token)["data"]
        run_id = run["id"]
        deadline = time.monotonic() + 360
        while run["status"] not in {"SUCCEEDED", "FAILED", "TIMED-OUT", "ABORTED"}:
            if self.stop.wait(self.poll_seconds):
                return  # Keep runId on disk; resume this same run after restart.
            if time.monotonic() > deadline:
                self.request("actor-runs/" + run_id + "/abort", token, {})
                raise TimeoutError("Profile lookup exceeded its background limit")
            run = self._get("actor-runs/" + run_id, token)["data"]
        self._update(job_id, costUsd=run.get("usageTotalUsd", 0))
        if run["status"] != "SUCCEEDED":
            self._update(job_id, runTerminalFailure=True)
            raise RuntimeError("Actor did not succeed")
        items = self._get("datasets/" + run["defaultDatasetId"] + "/items", token, clean="true")
        profiles = []
        for item in items:
            if not item.get("username"):
                continue
            profile = self.normalize(item)
            profile["handle"] = profile["handle"].lower()
            if item.get("error"):
                profile["profileStatus"] = "unavailable"
            else:
                profile["profileStatus"] = "private" if profile["private"] else "ready"
            profiles.append(profile)
        if job["kind"] == "profiles":
            self.apply_profiles(job["value"], profiles)
        results = [p for p in profiles if p["profileStatus"] in {"ready", "private"}]
        self._update(job_id, status="succeeded", profiles=profiles, results=results,
                     message=f"Loaded {len(results)} profile(s)." if results else "No matching public profile details returned. Exact handles can still be saved.")

    def close(self):
        self.stop.set()
        self.worker.join(timeout=1)
