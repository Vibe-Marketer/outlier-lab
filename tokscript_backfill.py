#!/usr/bin/env python3
"""Fill saved Reels from TokScript's existing library, then resumable bulk jobs.

Requires TOKSCRIPT_API_KEY in the environment or private .env. Never calls Apify.
Only transcript fields are merged; statistics and niche memberships are retained.
"""
import argparse
import html
import json
import re
import statistics
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from storage import file_lock, write_json
from tokscript import TokScript

ROOT = Path(__file__).resolve().parent


def shortcode(url):
    parts = urllib.parse.urlsplit(url or "")
    if parts.hostname not in {"instagram.com", "www.instagram.com"}:
        return None
    match = re.match(r"/(?:reel|reels|p)/([A-Za-z0-9_-]+)(?:/|$)", parts.path)
    return match[1] if match else None


def plain_transcript(value):
    if isinstance(value, list):
        return " ".join(plain_transcript(v) for v in value).strip()
    if isinstance(value, dict):
        return plain_transcript(value.get("text") or value.get("segments") or "")
    if not isinstance(value, str):
        return ""
    lines = value.splitlines()
    spoken = []
    for index, line in enumerate(lines):
        line = line.strip()
        if not line or line == "WEBVTT" or "-->" in line:
            continue
        if line.isdigit() and index + 1 < len(lines) and "-->" in lines[index + 1]:
            continue  # SRT cue index; preserve numeric speech lines.
        spoken.append(line)
    return html.unescape(" ".join(spoken)).strip()


def saved_reels(root, handles=None):
    config = json.loads((root / "config.json").read_text())
    saved = {}
    for creator in config.get("creators", []):
        handle = creator["handle"]
        if handles is not None and handle not in handles:
            continue
        path = root / "data" / f"{handle}_posts.json"
        posts = json.loads(path.read_text()).get("items", []) if path.exists() else []
        baseline = statistics.median([p.get("videoPlayCount") or p.get("videoViewCount") or 0 for p in posts]) if posts else 0
        for post in posts:
            sc = post.get("shortCode")
            if not sc or not re.fullmatch(r"[A-Za-z0-9_-]+", sc):
                continue
            ratio = (post.get("videoPlayCount") or post.get("videoViewCount") or 0) / baseline if baseline else 0
            saved[sc] = {"handle": handle, "post": post, "ratio": ratio,
                         "url": f"https://www.instagram.com/reel/{sc}/"}
    return saved


def needs_tokscript(post):
    meta = post.get("transcription") or {}
    if meta.get("provider") == "tokscript" and meta.get("status") == "no_speech":
        return False
    text = (post.get("transcript") or "").strip()
    return not any(c.isalnum() for c in text) or meta.get("provider") == "mlx-whisper"


def import_rows(root, rows, saved, source):
    """Match exact Reel IDs. Never overwrite metrics with TokScript's null stats."""
    found = {}
    for row in rows:
        sc = shortcode(row.get("source_url") or row.get("url"))
        text = plain_transcript(row.get("transcript"))
        if sc in saved and text:
            spoken = any(c.isalnum() for c in text)
            found[sc] = (text if spoken else "", "ready" if spoken else "no_speech")
    with file_lock(root / "data/.posts.lock"):
        for handle in {saved[sc]["handle"] for sc in found}:
            path = root / "data" / f"{handle}_posts.json"
            if not path.exists():
                continue
            doc = json.loads(path.read_text())
            for post in doc.get("items", []):
                sc = post.get("shortCode")
                if sc in found and needs_tokscript(post):
                    text, status = found[sc]
                    post["transcript"] = text
                    post["transcription"] = {"status": status, "provider": "tokscript",
                        "source": source, "attemptedAt": datetime.now(timezone.utc).isoformat()}
                    if text and len(text.split()) < 3:
                        post["transcription"]["shortResult"] = True
            write_json(path, doc)
    return set(found)


def download_export(client, result_key, dest):
    exported = client.call("export_results", result_key=result_key, format="json")
    # Download without Authorization: the export is a distinct, public R2 URL.
    url = exported.get("download_url")
    parts = urllib.parse.urlsplit(url or "")
    if parts.scheme != "https" or not parts.hostname or not parts.hostname.endswith(".r2.dev"):
        raise RuntimeError("TokScript returned an unsupported export location")
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://tokscript.com/"})
    with urllib.request.urlopen(request, timeout=120) as response:
        rows = json.load(response)
    if not isinstance(rows, list):
        raise RuntimeError("TokScript export was not a list")
    write_json(dest, rows)
    return rows


def poll_export(client, job, cache, persist):
    started = time.monotonic()
    while True:
        status = client.call("get_job_status", job_id=job["job_id"], include_results=True)
        job["remote"] = status
        persist()
        print(f"TokScript {job['job_id']}: {status.get('status')} · {status.get('completed', 0)}/{status.get('total', len(job['urls']))}", flush=True)
        if status.get("status") == "failed":
            job["terminalFailed"] = True
            persist()
            return [], status
        if status.get("status") == "complete":
            rows = download_export(client, status["result_key"], cache / f"{job['job_id']}.json")
            job["exported"] = True
            persist()
            return rows, status
        if time.monotonic() - started > 1200:
            raise RuntimeError("TokScript is still processing; rerun to resume the saved job ID")
        time.sleep(8)


def mark_unavailable(root, urls, saved):
    with file_lock(root / "data/.posts.lock"):
        for handle in {saved[shortcode(u)]["handle"] for u in urls if shortcode(u) in saved}:
            path = root / "data" / f"{handle}_posts.json"
            if not path.exists():
                continue
            doc = json.loads(path.read_text())
            failed = {shortcode(u) for u in urls}
            for post in doc.get("items", []):
                if post.get("shortCode") in failed:
                    attempt = {"status": "error", "provider": "tokscript",
                        "attemptedAt": datetime.now(timezone.utc).isoformat(),
                        "message": "TokScript returned no transcript after bounded retries."}
                    if not post.get("transcript"):
                        post["transcription"] = attempt
                    else:
                        post["transcriptionAttempt"] = attempt
            write_json(path, doc)


def backfill(root=ROOT, handles=None, limit=None):
    cache = root / ".cache/tokscript"
    cache.mkdir(parents=True, exist_ok=True)
    with file_lock(root / ".cache/transcripts/worker.lock", blocking=False):
        client = TokScript()
        saved = saved_reels(root, handles)
        jobs_path = cache / "jobs.json"
        jobs = json.loads(jobs_path.read_text()) if jobs_path.exists() else []
        persist = lambda: write_json(jobs_path, jobs)
        # First recover exports / in-flight jobs from an interrupted invocation.
        for job in jobs:
            if job.get("job_id") and not job.get("exported") and not job.get("terminalFailed"):
                rows, _ = poll_export(client, job, cache, persist)
                import_rows(root, rows, saved, job["job_id"])
            elif job.get("exported"):
                file = cache / f"{job['job_id']}.json"
                if file.exists():
                    import_rows(root, json.loads(file.read_text()), saved, job["job_id"])

        # Read existing library before live processing. A page contains up to 50
        # library documents, which may flatten into hundreds of transcript rows.
        page = 1
        while True:
            library = client.call("get_user_library", platform="instagram", page=page, limit=50)
            if library.get("count"):
                rows = download_export(client, library["result_key"], cache / f"library-{page}.json")
                matched = import_rows(root, rows, saved, "library")
                print(f"Existing TokScript library page {page}: {len(matched)} matching saved Reels", flush=True)
            if not library.get("pagination", {}).get("has_next"):
                break
            page += 1

        saved = saved_reels(root, handles)
        # A timed-out submit may have been accepted remotely. Reconcile against
        # the library above; never silently resubmit an unconfirmed request.
        for job in jobs:
            if not job.get("job_id") and job.get("status") in {"submitting", "submission_uncertain"}:
                unresolved = [u for u in job["urls"] if shortcode(u) in saved and
                              needs_tokscript(saved[shortcode(u)]["post"])]
                if unresolved:
                    raise RuntimeError("An earlier TokScript submission has no confirmed job ID. "
                        f"{len(unresolved)} Reels are awaiting reconciliation. Check TokScript Imports, "
                        "then rerun after processing finishes; no duplicate job was submitted.")
                # Leave unrelated scopes' uncertain receipts intact.
                if all(shortcode(u) in saved for u in job["urls"]):
                    job["status"] = "reconciled"
                    persist()
        pending = [r for r in sorted(saved.values(), key=lambda r: r["ratio"], reverse=True)
                   if needs_tokscript(r["post"])]
        if limit is not None:
            pending = pending[:limit]
        print(f"TokScript: {len(pending)} Reels to fill; batches of 50; no Apify transcription", flush=True)
        summary = {"provider": "tokscript", "requested": len(pending), "completed": 0, "ready": 0,
                   "unavailable": 0, "no_speech": 0, "apifySpendUsd": 0, "startedAt": datetime.now(timezone.utc).isoformat()}
        for offset in range(0, len(pending), 50):
            urls = [r["url"] for r in pending[offset:offset + 50]]
            remaining = urls[:]
            for attempt in range(3):
                if not remaining:
                    break
                job = {"urls": remaining[:], "attempt": attempt + 1, "status": "submitting"}
                jobs.append(job)
                persist()
                # Persist the remote ID immediately; retries resume that ID.
                try:
                    submitted = client.call("submit_transcript_job", urls=remaining)
                    if not submitted.get("job_id"):
                        raise RuntimeError("TokScript did not confirm a job ID")
                except Exception:
                    job["status"] = "submission_uncertain"
                    persist()
                    raise RuntimeError("TokScript submission was not confirmed. Rerun to reconcile "
                                       "its library before any duplicate submission.") from None
                job.update(submitted, status="submitted")
                persist()
                rows, status = poll_export(client, job, cache, persist)
                imported = import_rows(root, rows, saved, job["job_id"])
                photo_urls = {r.get("url") for r in status.get("results", [])
                              if re.search(r"photo|carousel", str(r.get("error") or (r.get("data") or {}).get("error") or ""), re.I)}
                remaining = [u for u in remaining if shortcode(u) not in imported and u not in photo_urls]
            current = saved_reels(root, handles)
            ready = sum(current[shortcode(u)]["post"].get("transcription", {}).get("provider") == "tokscript"
                        and bool(current[shortcode(u)]["post"].get("transcript")) for u in urls)
            failed = [u for u in urls if needs_tokscript(current[shortcode(u)]["post"])]
            mark_unavailable(root, failed, saved)
            summary["completed"] += len(urls)
            summary["ready"] += ready
            summary["unavailable"] += len(failed)
            summary["no_speech"] += sum(current[shortcode(u)]["post"].get("transcription", {}).get("status") == "no_speech" for u in urls)
            summary["updatedAt"] = datetime.now(timezone.utc).isoformat()
            write_json(cache / "progress.json", summary)
            print(json.dumps(summary), flush=True)
        return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--handles", nargs="+")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--build", action="store_true")
    args = parser.parse_args()
    try:
        backfill(handles=args.handles, limit=args.limit)
        if args.build:
            subprocess.run([sys.executable, str(ROOT / "build.py")], cwd=ROOT, check=True)
    except BlockingIOError:
        print("Another transcript worker is already running.", file=sys.stderr)
        sys.exit(1)
