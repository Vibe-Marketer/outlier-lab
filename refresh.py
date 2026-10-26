#!/usr/bin/env python3
"""
Weekly refresh pipeline. Idempotent:
  1. Call Apify reel-scraper for all CREATORS (stats only)
  2. Poll until done
  3. Merge stats; fill missing transcripts through the TokScript MCP account
  4. Refresh each creator's profile details
  5. Extract local 3-sec hook clips for new reels (ffmpeg)
  6. Prune reels + clips older than 28 days
  7. Build the dashboard HTML

Requires APIFY_TOKEN and TOKSCRIPT_API_KEY. Also supports local private .env.
"""
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
CLIPS = ROOT / "clips"
THUMBS = ROOT / "thumbs"

from catalog import ALL, select_creators
from reel_coverage import summarize_coverage
from storage import write_json, file_lock
from tokscript import load_key
CONFIG = json.loads((ROOT / "config.json").read_text())
SCOPE = os.environ.get("OUTLIER_SCOPE", ALL)
CREATORS = [c["handle"] for c in select_creators(CONFIG, SCOPE)]

from serve import load_env_token
APIFY_TOKEN = os.environ.get("APIFY_TOKEN") or load_env_token()
if not APIFY_TOKEN:
    print("ERROR: APIFY_TOKEN env var required")
    sys.exit(1)

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
WINDOW_DAYS = 28
CLIP_SECONDS = 3
REEL_SCRAPER = "apify~instagram-reel-scraper"
PROFILE_SCRAPER = "apify~instagram-scraper"
SETTINGS = CONFIG.get("refresh", {})


def apify_post(path, body, **params):
    url = f"https://api.apify.com/v2/{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {APIFY_TOKEN}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def apify_get(path, **params):
    qs = urllib.parse.urlencode(params)
    url = f"https://api.apify.com/v2/{path}?{qs}"
    # Retry with exponential backoff on transient 5xx errors (Apify's API
    # occasionally returns 502/503/504 under load).
    delays = [2, 5, 10, 20, 40]
    last_err = None
    for attempt, delay in enumerate([0] + delays):
        if delay:
            time.sleep(delay)
        try:
            req = urllib.request.Request(url, headers={"Authorization": f"Bearer {APIFY_TOKEN}"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            last_err = e
            if e.code in (429, 500, 502, 503, 504):
                print(f"  ! apify_get {path} → HTTP {e.code}, retrying (attempt {attempt+1}/{len(delays)+1})")
                continue
            raise
        except urllib.error.URLError as e:
            last_err = e
            print(f"  ! apify_get {path} → URLError {e}, retrying (attempt {attempt+1}/{len(delays)+1})")
            continue
    raise RuntimeError(f"apify_get failed after retries: {last_err}") from last_err


def start_actor(actor_id, body, max_charge=0.10):
    run = apify_post(f"acts/{actor_id}/runs", body, maxTotalChargeUsd=max_charge, timeout=900)["data"]
    print(f"  actor run: {run['id']} (cap ${max_charge:.2f})")
    return run


def wait_for_run(run_id, label="run", interval=8, max_wait=900):
    start = time.time()
    while True:
        r = apify_get(f"actor-runs/{run_id}")["data"]
        status = r["status"]
        if status in ("SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"):
            print(f"  [{label}] {status} after {int(time.time()-start)}s")
            return r
        if time.time() - start > max_wait:
            apify_post(f"actor-runs/{run_id}/abort", {})
            raise RuntimeError(f"{label} run {run_id} did not finish in {max_wait}s")
        time.sleep(interval)


def fetch_dataset(dataset_id, fields=None):
    params = {"clean": "true"}
    if fields:
        params["fields"] = ",".join(fields)
    return apify_get(f"datasets/{dataset_id}/items", **params)


def load_existing_posts(handle):
    p = DATA / f"{handle}_posts.json"
    if not p.exists():
        return []
    try:
        return json.load(open(p))["items"]
    except (json.JSONDecodeError, KeyError):
        return []


def save_posts(handle, items):
    write_json(DATA / f"{handle}_posts.json", {"items": items})


def save_details(handle, details):
    DATA.mkdir(parents=True, exist_ok=True)
    wrapper = {"dataset": {"previewItems": [details]}}
    with open(DATA / f"{handle}_details.json", "w") as f:
        json.dump(wrapper, f)


def ts_to_dt(ts):
    if not ts:
        return None
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


REEL_FIELDS = [
    "shortCode", "url", "caption", "timestamp", "videoDuration",
    "videoPlayCount", "videoViewCount", "likesCount", "commentsCount",
    "displayUrl", "videoUrl", "musicInfo", "transcript",
    "ownerUsername", "ownerFullName",
    "inputUrl", "coauthorProducers",
]


def pass1_stats_refresh():
    """Cheap: scrape last 28 days for all creators WITHOUT transcripts.
    Gives us current plays/likes/comments + identifies which reels are new."""
    print(f"PASS 1 (stats only, no transcripts) for {len(CREATORS)} creators…")
    run = start_actor(REEL_SCRAPER, {
        "username": list(CREATORS),
        "resultsLimit": SETTINGS.get("reelsPerCreator", 40),
        "onlyPostsNewerThan": f"{WINDOW_DAYS} days",
        "includeTranscript": False,  # cheap pass
        "skipPinnedPosts": True,
    }, max_charge=SETTINGS.get("statsMaxChargeUsd", 0.25))
    run = wait_for_run(run["id"], "pass1-stats")
    if run["status"] != "SUCCEEDED":
        raise RuntimeError(f"pass1 scrape failed: {run['status']}")
    items = fetch_dataset(run["defaultDatasetId"], fields=REEL_FIELDS)
    coverage_path = DATA / "coverage.json"
    coverage = json.loads(coverage_path.read_text()) if coverage_path.exists() else {}
    coverage.update(summarize_coverage(CREATORS, items, SETTINGS.get("reelsPerCreator", 40)))
    write_json(coverage_path, coverage)
    valid = [it for it in items if it.get("shortCode") and it.get("ownerUsername") in CREATORS]
    print(f"  scraped {len(valid)} usable reels (stats only)")
    if not valid:
        raise RuntimeError("No accessible reels returned. Check the creator handles, account privacy, and 28-day date window.")
    return valid


def fetch_profile_details_for_all_creators():
    print(f"refreshing profile details for {len(CREATORS)} creators…")
    run = start_actor(PROFILE_SCRAPER, {
        "directUrls": [f"https://www.instagram.com/{h}/" for h in CREATORS],
        "resultsType": "details",
        "resultsLimit": 1,
    })
    run = wait_for_run(run["id"], "details")
    if run["status"] != "SUCCEEDED":
        raise RuntimeError(f"profile scrape failed: {run['status']}")
    items = fetch_dataset(run["defaultDatasetId"])
    by_handle = {it.get("username"): it for it in items if it.get("username") and not it.get("error")}
    for handle in CREATORS:
        if handle in by_handle:
            save_details(handle, by_handle[handle])
    print(f"  refreshed {len(by_handle)} profile records")


def merge_pass1_stats(scraped_items):
    with file_lock(DATA / ".posts.lock"):
        return _merge_pass1_stats(scraped_items)


def _merge_pass1_stats(scraped_items):
    """Merge pass-1 (stats-only) results into existing per-creator JSON.
    Preserves transcripts from existing records; updates plays/likes/comments
    from the fresh scrape."""
    grouped = {}
    for it in scraped_items:
        u = it.get("ownerUsername")
        if u not in CREATORS:
            continue
        grouped.setdefault(u, []).append(it)

    for handle, fresh in grouped.items():
        existing = load_existing_posts(handle)
        by_sc = {p["shortCode"]: p for p in existing if p.get("shortCode")}
        new_count = 0
        for p in fresh:
            sc = p.get("shortCode")
            if not sc:
                continue
            old = by_sc.get(sc, {})
            merged = {**old, **p}  # new stats overwrite
            # PRESERVE transcript if we already had it (pass 1 has no transcript)
            if old.get("transcript") and not p.get("transcript"):
                merged["transcript"] = old["transcript"]
            if sc not in by_sc:
                new_count += 1
            by_sc[sc] = merged
        cutoff = datetime.now(timezone.utc) - timedelta(days=WINDOW_DAYS)
        kept = [
            p for p in by_sc.values()
            if (dt := ts_to_dt(p.get("timestamp"))) and dt >= cutoff
        ]
        kept.sort(key=lambda p: p.get("timestamp", ""), reverse=True)
        save_posts(handle, kept)
        print(f"  @{handle}: kept {len(kept)} reels in {WINDOW_DAYS}-day window ({new_count} new)")


def refresh_transcripts():
    if not load_key():
        raise RuntimeError("Configure TOKSCRIPT_API_KEY; Apify transcription fallback is disabled.")
    subprocess.run([sys.executable, str(ROOT / "tokscript_backfill.py"), "--handles", *CREATORS],
                   check=True, timeout=7200)


def fetch_image(args):
    url, dest = args
    if dest.exists() and dest.stat().st_size > 0:
        return True
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=15) as r:
            dest.write_bytes(r.read())
        return True
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
        print(f"  ! image fetch failed ({dest.name}): {e}")
        return False


def download_thumbnails():
    THUMBS.mkdir(parents=True, exist_ok=True)
    jobs = []
    for handle in CREATORS:
        d = DATA / f"{handle}_details.json"
        if d.exists():
            try:
                details = json.load(open(d))["dataset"]["previewItems"][0]
                purl = details.get("profilePicUrlHD") or details.get("profilePicUrl")
                if purl:
                    jobs.append((purl, THUMBS / f"_profile_{handle}.jpg"))
            except (KeyError, IndexError):
                pass
        for p in load_existing_posts(handle):
            sc = p.get("shortCode")
            url = p.get("displayUrl")
            if sc and url:
                jobs.append((url, THUMBS / f"{sc}.jpg"))
    pending = [(u, d) for (u, d) in jobs if not (d.exists() and d.stat().st_size > 0)]
    if pending:
        print(f"downloading {len(pending)} thumbnails…")
        with ThreadPoolExecutor(max_workers=16) as ex:
            list(ex.map(fetch_image, pending))


def extract_clip(post):
    sc = post.get("shortCode")
    url = post.get("videoUrl")
    if not sc or not url:
        return (sc or "?", "skip")
    out = CLIPS / f"{sc}.mp4"
    if out.exists() and out.stat().st_size > 0:
        return (sc, "have")
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-user_agent", UA,
        "-i", url,
        "-t", str(CLIP_SECONDS),
        "-vf", "scale=-2:480",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "30",
        "-an", "-movflags", "+faststart",
        str(out),
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=60)
        if r.returncode == 0 and out.exists() and out.stat().st_size > 0:
            return (sc, "ok")
        else:
            if out.exists():
                out.unlink()
            return (sc, "fail")
    except subprocess.TimeoutExpired:
        return (sc, "timeout")


def extract_all_clips():
    CLIPS.mkdir(parents=True, exist_ok=True)
    all_posts = []
    for handle in CREATORS:
        all_posts.extend(load_existing_posts(handle))
    print(f"checking clips for {len(all_posts)} reels…")
    counts = {"ok": 0, "have": 0, "fail": 0, "skip": 0, "timeout": 0}
    with ThreadPoolExecutor(max_workers=8) as ex:
        for sc, status in ex.map(extract_clip, all_posts):
            counts[status] = counts.get(status, 0) + 1
    print(f"  clips: {counts}")


def prune_old_assets():
    """Delete thumbs/clips for reels no longer in our 28-day window."""
    keep = set()
    # A scoped refresh must preserve cached assets belonging to other lists.
    for creator in select_creators(CONFIG, tracked_only=False):
        handle = creator["handle"]
        for p in load_existing_posts(handle):
            sc = p.get("shortCode")
            if sc:
                keep.add(sc)
    pruned = 0
    for f in CLIPS.glob("*.mp4"):
        if f.stem not in keep:
            f.unlink(); pruned += 1
    for f in THUMBS.glob("*.jpg"):
        if f.stem.startswith("_profile_"):
            continue
        if f.stem not in keep:
            f.unlink(); pruned += 1
    if pruned:
        print(f"  pruned {pruned} aged-out clip/thumb files")


def build_dashboard():
    print("running build.py …")
    r = subprocess.run([sys.executable, str(ROOT / "build.py")], capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout); print(r.stderr)
        raise RuntimeError("build.py failed")
    print(r.stdout.strip())


def main():
    if not CREATORS:
        print("No tracked creators in this list; no Apify calls made.")
        return
    if not load_key():
        raise RuntimeError("Configure TOKSCRIPT_API_KEY before refreshing; Apify transcription is disabled.")
    print(f"=== refresh started · {datetime.now().isoformat()} ===")
    print(f"list: {SCOPE}; creators (deduplicated): {CREATORS}\n")

    # Pass 1: cheap stats refresh (no transcripts)
    scraped = pass1_stats_refresh()

    # Merge stats first (so pass 2 can layer transcripts on saved records)
    merge_pass1_stats(scraped)

    refresh_transcripts()

    fetch_profile_details_for_all_creators()
    download_thumbnails()
    extract_all_clips()
    prune_old_assets()
    build_dashboard()
    print(f"\n=== refresh done · {datetime.now().isoformat()} ===")


if __name__ == "__main__":
    main()
