#!/usr/bin/env python3
"""
Outlier Lab — local admin dashboard.

Run this and a browser tab will open at http://localhost:4747/admin
where you can:
  • paste/save your Apify API token
  • search for Instagram creators live (typeahead via Apify)
  • see each result's profile pic, follower count, verified badge
  • one-click add / remove from your tracking list
  • trigger a fresh refresh on demand (also runs every Sunday via GH Actions)

Pure stdlib — no pip install needed. Localhost-only binding.
"""

import io
import json
import os
import re
import socketserver
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from catalog import ALL, scopes_for, select_creators, validate_scope, validate_memberships, valid_handle, parse_handles
from creator_jobs import ProfileJobs
from storage import write_json, file_lock, update_env
from tokscript import load_key as load_tokscript_key

ROOT = Path(__file__).resolve().parent
ENV_FILE = ROOT / ".env"
CONFIG_FILE = ROOT / "config.json"
ADMIN_HTML = ROOT / "admin.html"

PORT = 4747
HOST = "127.0.0.1"
CONFIG_LOCK = threading.RLock()

# Apify actor IDs
IG_SCRAPER = "shu8hvrXbJbY3Eb9W"  # apify/instagram-scraper (general)


# ───────────────────────── helpers ─────────────────────────

def load_env_token():
    if not ENV_FILE.exists():
        return ""
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if line.startswith("APIFY_TOKEN="):
            return line.split("=", 1)[1].strip()
    return ""


def save_env_token(token):
    update_env(ENV_FILE, "APIFY_TOKEN", token)


def load_config():
    if not CONFIG_FILE.exists():
        return {"creators": []}
    try:
        return json.loads(CONFIG_FILE.read_text())
    except json.JSONDecodeError:
        return {"creators": []}


def save_config(config):
    with CONFIG_LOCK:
        write_json(CONFIG_FILE, config)


def apply_profile_details(handles, profiles):
    """Only enrich still-saved accounts; preserve edits made while lookup was running."""
    by_handle = {p["handle"]: p for p in profiles if p.get("handle") in handles}
    with CONFIG_LOCK:
        config = load_config()
        for creator in config.get("creators", []):
            handle = creator["handle"]
            if handle not in handles:
                continue
            profile = by_handle.get(handle)
            if profile and profile.get("profileStatus") in {"ready", "private"}:
                creator.update({k: v for k, v in profile.items() if k not in {"handle", "scopes", "trackingEnabled"}})
                creator.pop("profileError", None)
            else:
                creator["profileStatus"] = "unavailable"
                creator["profileError"] = "No matching profile details returned. Check the handle; it remains saved."
        save_config(config)


def profile_details_failed(handles, message):
    with CONFIG_LOCK:
        config = load_config()
        for creator in config.get("creators", []):
            if creator["handle"] in handles:
                creator.update(profileStatus="unavailable", profileError=message)
        save_config(config)


def get_jobs(server):
    with server.jobs_lock:
        if server.profile_jobs is None:
            server.profile_jobs = ProfileJobs(ROOT / ".cache" / "creator-jobs.json", load_env_token,
                                               normalize_profile, apply_profile_details, profile_details_failed)
        return server.profile_jobs


def apify_run_sync(actor_id, input_body, token, timeout=90):
    """Call Apify's run-sync-get-dataset-items endpoint. Returns list of items."""
    url = f"https://api.apify.com/v2/acts/{actor_id}/run-sync-get-dataset-items?maxTotalChargeUsd=0.10"
    req = urllib.request.Request(
        url,
        data=json.dumps(input_body).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def normalize_profile(item):
    """Reduce a scraped profile/search-result to the shape we store."""
    return {
        "handle": item.get("username", ""),
        "name": item.get("fullName") or item.get("full_name") or "",
        "followers": item.get("followersCount") or item.get("edge_followed_by", {}).get("count") or 0,
        "posts": item.get("postsCount") or 0,
        "verified": bool(item.get("verified") or item.get("is_verified")),
        "private": bool(item.get("private") or item.get("is_private")),
        "profilePic": item.get("profilePicUrlHD") or item.get("profilePicUrl") or item.get("profile_pic_url") or "",
    }


# ───────────────────────── HTTP handler ─────────────────────────

class AdminHandler(BaseHTTPRequestHandler):

    # ---- request helpers ----

    def _json(self, status, payload):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _html(self, status, body, content_type="text/html; charset=utf-8"):
        if isinstance(body, str):
            body = body.encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        if content_type.startswith("text/html"):
            self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            value = json.loads(raw)
            return value if isinstance(value, dict) else {}
        except json.JSONDecodeError:
            return {}

    def log_message(self, fmt, *args):
        # Quieter logging — only show our own prints
        return

    # ---- routes ----

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path in ("/admin", "/admin/"):
            if not ADMIN_HTML.exists():
                self._html(500, "admin.html missing")
                return
            self._html(200, ADMIN_HTML.read_bytes())
            return

        if path == "/api/state":
            token = load_env_token()
            config = load_config()
            self._json(200, {
                "tokenSet": bool(token and token.startswith("apify_api_")),
                "tokenPrefix": "configured" if token else "",
                "creators": config.get("creators", []),
                "scopes": scopes_for(config),
                "research": config.get("research", {}),
                "refresh": config.get("refresh", {}),
                "jobs": self.server.profile_jobs.recent() if self.server.profile_jobs else [],
            })
            return

        if path == "/api/schedule":
            wf_path = ROOT / ".github" / "workflows" / "refresh.yml"
            if not wf_path.exists():
                self._json(200, {"cron": None})
                return
            content = wf_path.read_text()
            # commented out → off
            if re.search(r"^\s*#\s*schedule:", content, re.MULTILINE):
                self._json(200, {"cron": "off"})
                return
            m = re.search(r'-\s*cron:\s*"([^"]+)"', content)
            self._json(200, {"cron": m.group(1) if m else None})
            return

        if path == "/api/search":
            q = (query.get("q", [""])[0] or "").strip()
            if not q or len(q) < 2:
                self._json(200, {"results": []})
                return
            if not load_env_token():
                self._json(400, {"error": "no_token", "message": "Save your Apify token first."})
                return
            if len(q) > 100:
                self._json(400, {"message": "Search must be 100 characters or fewer."})
                return
            try:
                job = get_jobs(self.server).submit("search", q)
            except ValueError as e:
                self._json(429, {"message": str(e)})
                return
            self._json(200 if job["status"] in {"succeeded", "failed"} else 202, {"job": job, "results": job.get("results", [])})
            return

        if path.startswith("/api/jobs/"):
            job = get_jobs(self.server).get(path.rsplit("/", 1)[-1])
            self._json(200 if job else 404, {"job": job} if job else {"message": "Lookup not found. Your saved creators are unchanged."})
            return

        # serve any other static file in the project root (so admin.html can <link> styles/images if added later)
        relative = urllib.parse.unquote(path).lstrip("/") or "index.html"
        parts = Path(relative).parts
        if any(part.startswith(".") for part in parts) or not (
            relative in {"index.html", "admin.html", "refresh.log"}
            or (parts and parts[0] in {"data", "thumbs", "clips"})
        ):
            self._json(404, {"error": "not_found"})
            return
        safe_path = ROOT / relative
        try:
            safe_path = safe_path.resolve()
            safe_path.relative_to(ROOT)
        except (ValueError, OSError):
            self._json(404, {"error": "not_found"})
            return
        if safe_path.is_file():
            ext = safe_path.suffix.lower()
            ct = {
                ".html": "text/html; charset=utf-8",
                ".css": "text/css",
                ".js": "application/javascript",
                ".json": "application/json",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".mp4": "video/mp4",
                ".svg": "image/svg+xml",
            }.get(ext, "application/octet-stream")
            self._html(200, safe_path.read_bytes(), content_type=ct)
            return

        self._json(404, {"error": "not_found"})

    def do_POST(self):
        if self.headers.get_content_type() != "application/json":
            self._json(415, {"error": "json_required"})
            return
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        # Threaded requests must serialize the whole read/modify/write transaction.
        if path.startswith("/api/creators") or path == "/api/scopes":
            with CONFIG_LOCK:
                self._post(path)
        elif path in {"/api/build", "/api/refresh", "/api/transcripts", "/api/schedule"}:
            with self.server.operations_lock:
                self._post(path)
        else:
            self._post(path)

    def _post(self, path):

        if path == "/api/scopes":
            data = self._body()
            scope_id = data.get("id", "")
            name = data.get("name", "")
            description = data.get("description", "")
            if not isinstance(scope_id, str) or not re.fullmatch(r"[a-z][a-z0-9-]{0,39}", scope_id) or not isinstance(name, str) or not 1 <= len(name.strip()) <= 80 or not isinstance(description, str) or len(description) > 300:
                self._json(400, {"message": "Use a list ID, a name up to 80 characters, and a short description."})
                return
            config = load_config()
            scopes = scopes_for(config)
            if not any(s["id"] == scope_id for s in scopes):
                config["scopes"] = scopes + [{"id": scope_id, "name": name.strip(), "description": description}]
                save_config(config)
            self._json(200, {"scopes": scopes_for(config)})
            return

        if path == "/api/token":
            data = self._body()
            token = (data.get("token") or "").strip()
            if not token.startswith("apify_api_"):
                self._json(400, {"error": "invalid_token", "message": "Token should start with apify_api_"})
                return
            save_env_token(token)
            self._json(200, {"ok": True})
            return

        if path == "/api/lookup":
            data = self._body()
            try:
                handles = parse_handles([data.get("handle", "")])
            except ValueError as e:
                self._json(400, {"message": str(e)})
                return
            if not load_env_token():
                self._json(400, {"error": "no_token"})
                return
            try:
                job = get_jobs(self.server).submit("profiles", handles)
            except ValueError as e:
                self._json(429, {"message": str(e)})
                return
            self._json(200 if job["status"] in {"succeeded", "failed"} else 202, {"job": job, "profile": next(iter(job.get("results", [])), None)})
            return

        if path == "/api/creators/import":
            data = self._body()
            config = load_config()
            try:
                handles = parse_handles(data.get("handles"))
                scopes = validate_memberships(config, data.get("scopes", []))
            except ValueError as e:
                self._json(400, {"message": str(e)})
                return
            by_handle = {c["handle"].lower(): c for c in config.get("creators", [])}
            for handle in handles:
                if handle not in by_handle:
                    by_handle[handle] = {"handle": handle, "name": handle, "scopes": scopes[:],
                                         "trackingEnabled": True, "profileStatus": "pending"}
                else:
                    by_handle[handle]["scopes"] = list(dict.fromkeys(by_handle[handle].get("scopes", []) + scopes))
            config["creators"] = list(by_handle.values())
            save_config(config)  # Saving never depends on Apify completing (or even being configured).
            job = None
            warning = ""
            if load_env_token():
                try:
                    job = get_jobs(self.server).submit("profiles", handles)
                    if job["status"] == "succeeded":
                        apply_profile_details(handles, job.get("profiles", []))
                except ValueError as e:
                    warning = str(e)
            else:
                warning = "Creators saved. Set an Apify token to load profile details later."
            if warning:
                profile_details_failed(handles, warning)
            self._json(200, {"ok": True, "saved": handles, "creators": load_config()["creators"], "job": job, "warning": warning})
            return

        if path == "/api/creators":
            data = self._body()
            profile = data.get("profile")
            if not isinstance(profile, dict) or not valid_handle(profile.get("handle")):
                self._json(400, {"error": "no_profile"})
                return
            config = load_config()
            try:
                profile["scopes"] = validate_memberships(config, data.get("scopes", profile.get("scopes", [])))
            except ValueError as e:
                self._json(400, {"message": str(e)})
                return
            profile["handle"] = profile["handle"].lower()
            profile["trackingEnabled"] = True
            creators = config.get("creators", [])
            if any(c["handle"] == profile["handle"] for c in creators):
                self._json(409, {"error": "already_added"})
                return
            creators.append(profile)
            config["creators"] = creators
            save_config(config)
            self._json(200, {"creators": creators})
            return

        creator_match = re.fullmatch(r"/api/creators/([A-Za-z0-9_.]+)", path)
        if creator_match:
            data = self._body()
            config = load_config()
            creator = next((c for c in config.get("creators", []) if c["handle"] == creator_match[1]), None)
            if creator is None:
                self._json(404, {"message": "Creator not found."})
                return
            try:
                if "scopes" in data:
                    creator["scopes"] = validate_memberships(config, data["scopes"])
                if "trackingEnabled" in data:
                    if not isinstance(data["trackingEnabled"], bool):
                        raise ValueError("Tracking must be enabled or paused.")
                    creator["trackingEnabled"] = data["trackingEnabled"]
            except ValueError as e:
                self._json(400, {"message": str(e)})
                return
            save_config(config)
            self._json(200, {"creators": config["creators"]})
            return

        if path == "/api/build":
            if getattr(self.server, "refresh_process", None) is not None and self.server.refresh_process.poll() is None:
                self._json(409, {"message": "Wait for the current refresh to finish."})
                return
            try:
                result = subprocess.run([sys.executable, str(ROOT / "build.py")], cwd=str(ROOT), capture_output=True, timeout=120)
                if result.returncode:
                    self._json(500, {"message": "Build failed; check the creator configuration."})
                    return
            except (OSError, subprocess.TimeoutExpired):
                self._json(500, {"message": "Dashboard rebuild could not complete."})
                return
            self._json(200, {"ok": True})
            return

        if path == "/api/schedule":
            data = self._body()
            cron = (data.get("cron") or "").strip()
            wf_path = ROOT / ".github" / "workflows" / "refresh.yml"
            if not wf_path.exists():
                self._json(404, {"error": "workflow_missing"})
                return
            content = wf_path.read_text()

            if cron == "off":
                # Comment out the schedule block
                new_content = re.sub(
                    r"^(\s*)schedule:\s*\n(\s*-\s*cron:.*\n)",
                    lambda m: m.group(1) + "# schedule:\n" + re.sub(r"^", "# ", m.group(2)),
                    content,
                    count=1,
                    flags=re.MULTILINE,
                )
                if new_content == content:
                    # Maybe already off — try uncomment-target pattern
                    new_content = content
                wf_path.write_text(new_content)
                self._json(200, {"ok": True, "message": "Schedule disabled (cron commented out)."})
                return

            # Re-enable schedule if currently commented, and set the new cron
            if "# schedule:" in content:
                content = content.replace("# schedule:", "schedule:")
                content = re.sub(r"^# (\s*-\s*cron:.*)$", r"\1", content, flags=re.MULTILINE)
            new_content = re.sub(
                r'(-\s*cron:\s*")[^"]+(")',
                lambda m: m.group(1) + cron + m.group(2),
                content,
                count=1,
            )
            if not re.search(r'-\s*cron:\s*"[^"]+"', content):
                # No match — workflow file shape changed
                self._json(500, {"error": "cant_patch", "message": "Couldn't find cron line in refresh.yml."})
                return
            wf_path.write_text(new_content)
            self._json(200, {"ok": True, "message": f"Schedule set to: {cron}. Commit & push to apply."})
            return

        if path in {"/api/refresh", "/api/transcripts"}:
            transcript_only = path == "/api/transcripts"
            token = load_env_token() if not transcript_only else None
            if not token and not transcript_only:
                self._json(400, {"error": "no_token"})
                return
            if getattr(self.server, "refresh_process", None) is not None and self.server.refresh_process.poll() is None:
                self._json(409, {"message": "A refresh is already running."})
                return
            data = self._body()
            config = load_config()
            try:
                scope = validate_scope(config, data.get("scope", ALL))
                selected = select_creators(config, scope)
            except ValueError as e:
                self._json(400, {"message": str(e)})
                return
            if not selected:
                self._json(400, {"message": "No tracked creators in this list. Enable tracking or choose another list."})
                return
            if transcript_only:
                if not load_tokscript_key(ROOT):
                    self._json(400, {"message": "Configure the TokScript API key first. Apify transcription is disabled."})
                    return
                try:
                    with file_lock(ROOT / ".cache/transcripts/worker.lock", blocking=False):
                        pass
                except BlockingIOError:
                    self._json(409, {"message": "Transcription is already running. Existing results are being saved."})
                    return
                command = [sys.executable, "-u", str(ROOT / "tokscript_backfill.py"), "--build", "--handles", *[c["handle"] for c in selected]]
            else:
                command = [sys.executable, "-u", str(ROOT / "refresh.py")]
            # Fire refresh.py in a subprocess (long-running)
            env = {**os.environ, "OUTLIER_SCOPE": scope}
            if token:
                env["APIFY_TOKEN"] = token
            log_path = ROOT / "refresh.log"
            log_path.write_text(f"# Refresh started at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            with open(log_path, "ab") as logf:
                p = subprocess.Popen(
                    command,
                    cwd=str(ROOT), env=env, stdout=logf, stderr=subprocess.STDOUT,
                )
            self.server.refresh_process = p
            self._json(200, {"ok": True, "pid": p.pid, "logPath": str(log_path), "scope": scope, "creatorCount": len(selected)})
            return

        self._json(404, {"error": "not_found"})

    def do_DELETE(self):
        with CONFIG_LOCK:
            self._delete()

    def _delete(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        m = re.match(r"^/api/creators/(?P<handle>[^/]+)$", path)
        if m:
            handle = urllib.parse.unquote(m.group("handle"))
            config = load_config()
            before = len(config.get("creators", []))
            config["creators"] = [c for c in config.get("creators", []) if c["handle"] != handle]
            save_config(config)
            self._json(200, {"removed": before - len(config["creators"]), "creators": config["creators"]})
            return

        self._json(404, {"error": "not_found"})


# ───────────────────────── server ─────────────────────────

class ReusableTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, *args, **kwargs):
        self.profile_jobs = None
        self.jobs_lock = threading.Lock()
        self.operations_lock = threading.Lock()
        super().__init__(*args, **kwargs)

    def server_close(self):
        if self.profile_jobs is not None:
            self.profile_jobs.close()
        super().server_close()


def main():
    url = f"http://{HOST}:{PORT}/admin"
    print(f"\n  ╔══════════════════════════════════════════════════════╗")
    print(f"  ║                                                      ║")
    print(f"  ║   OUTLIER LAB — Admin dashboard                      ║")
    print(f"  ║                                                      ║")
    print(f"  ║   Open in your browser:                              ║")
    print(f"  ║   {url:<53} ║")
    print(f"  ║                                                      ║")
    print(f"  ║   Press Ctrl+C to stop the server.                   ║")
    print(f"  ║                                                      ║")
    print(f"  ╚══════════════════════════════════════════════════════╝\n")

    # Open browser tab after a tiny delay so the user sees the banner first
    def _open():
        time.sleep(0.6)
        webbrowser.open(url)
    if not os.environ.get("OUTLIER_NO_BROWSER"):
        threading.Thread(target=_open, daemon=True).start()

    with ReusableTCPServer((HOST, PORT), AdminHandler) as httpd:
        if (ROOT / ".cache" / "creator-jobs.json").exists():
            get_jobs(httpd)  # Resume saved run IDs after a server restart.
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n  Goodbye.")


if __name__ == "__main__":
    main()
