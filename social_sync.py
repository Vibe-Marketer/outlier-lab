#!/usr/bin/env python3
"""
Outlier Lab — Sandcastles-Style Multi-Platform Account & Video Sync.

Supports Instagram, YouTube (Shorts + Videos), TikTok, and Facebook (Pages / Reels)
using handle or profile/video URL ingestion — no Meta/Google OAuth app review needed.

Powered by local `yt-dlp` (free, zero API keys) with optional Apify / TokScript
enrichment for Instagram. Pure stdlib — no pip installs required.
"""

import hashlib
import json
import os
import re
import shutil
import statistics
import subprocess
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from storage import write_json

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
SOCIALS_DIR = DATA / "socials"
ENV_FILE = ROOT / ".env"


def _ytdlp_bin():
    return shutil.which("yt-dlp") or ("/opt/homebrew/bin/yt-dlp" if Path("/opt/homebrew/bin/yt-dlp").exists() else None)


def _slug(text):
    return re.sub(r"[^a-z0-9_-]+", "-", (text or "").lower().strip().lstrip("@")).strip("-") or "channel"


def detect_platform_from_url(raw):
    s = (raw or "").strip().lower()
    if "youtube.com" in s or "youtu.be" in s:
        return "youtube"
    if "tiktok.com" in s:
        return "tiktok"
    if "facebook.com" in s or "fb.watch" in s or "fb.com" in s:
        return "facebook"
    if "instagram.com" in s:
        return "instagram"
    if "x.com" in s or "twitter.com" in s:
        return "x"
    return ""


def normalize_social_target(platform, handle_or_url):
    """Return (platform, display_handle, fetch_urls) for a handle or profile URL."""
    raw = (handle_or_url or "").strip()
    inferred = detect_platform_from_url(raw)
    plat = (platform or inferred or "instagram").lower().strip()
    if plat in {"yt", "youtube_shorts"}:
        plat = "youtube"
    elif plat in {"ig", "insta"}:
        plat = "instagram"
    elif plat in {"tt"}:
        plat = "tiktok"
    elif plat in {"fb"}:
        plat = "facebook"

    if raw.startswith("http://") or raw.startswith("https://"):
        parsed = urllib.parse.urlparse(raw)
        path_parts = [p for p in parsed.path.split("/") if p]
        handle = path_parts[0] if path_parts else "account"
        if handle.lower() in {"channel", "c", "user", "pages", "profile.php"} and len(path_parts) > 1:
            handle = path_parts[1]
        clean_handle = handle if handle.startswith("@") else f"@{handle}"
        if plat == "youtube":
            base = raw.rstrip("/")
            if not base.endswith(("/shorts", "/videos")):
                return (plat, clean_handle, [f"{base}/shorts", f"{base}/videos"])
            return (plat, clean_handle, [base])
        if plat == "facebook":
            base = raw.rstrip("/")
            if not base.endswith(("/reels", "/videos")):
                return (plat, clean_handle, [f"{base}/reels", f"{base}/videos", base])
            return (plat, clean_handle, [base])
        return (plat, clean_handle, [raw])

    bare = raw.lstrip("@").strip().strip("/")
    display = f"@{bare}"
    if plat == "youtube":
        return (plat, display, [f"https://www.youtube.com/@{bare}/shorts", f"https://www.youtube.com/@{bare}/videos"])
    if plat == "tiktok":
        return (plat, display, [f"https://www.tiktok.com/@{bare}"])
    if plat == "facebook":
        return (plat, display, [f"https://www.facebook.com/{bare}/reels", f"https://www.facebook.com/{bare}/videos", f"https://www.facebook.com/{bare}"])
    if plat == "instagram":
        return (plat, display, [f"https://www.instagram.com/{bare}/reels/"])
    return (plat, display, [raw])


def _run_ytdlp_playlist(url, limit=18, timeout=55):
    ytdlp = _ytdlp_bin()
    if not ytdlp:
        raise RuntimeError("yt-dlp is not installed (run `brew install yt-dlp`).")
    cmd = [
        ytdlp,
        "--flat-playlist",
        "--playlist-end", str(limit),
        "--dump-json",
        "--no-warnings",
        "--ignore-errors",
    ]
    cookies_browser = os.environ.get("OUTLIER_COOKIES_BROWSER", "").strip()
    if cookies_browser:
        cmd += ["--cookies-from-browser", cookies_browser]
    cmd.append(url)
    env = {**os.environ, "PATH": f"/opt/homebrew/bin:/usr/local/bin:{os.environ.get('PATH', '/usr/bin:/bin')}"}
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)
    items = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            items.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return items, (proc.stderr or "").strip()


def _parse_vtt_to_text(vtt_text):
    lines = []
    seen = set()
    for raw in (vtt_text or "").splitlines():
        s = raw.strip()
        if not s or s.startswith("WEBVTT") or s.startswith("Kind:") or s.startswith("Language:") or "-->" in s or re.fullmatch(r"\d+", s):
            continue
        s = re.sub(r"<[^>]+>", "", s)
        s = re.sub(r"\s+", " ", s).strip()
        if s and s not in seen:
            seen.add(s)
            lines.append(s)
    return " ".join(lines)


def _normalize_ytdlp_entry(entry, platform, display_handle):
    vid = str(entry.get("id") or "")
    title = (entry.get("title") or entry.get("description") or "").strip()
    desc = (entry.get("description") or "").strip()
    url = entry.get("webpage_url") or entry.get("url") or ""
    if platform == "youtube" and vid and not url.startswith("http"):
        url = f"https://www.youtube.com/shorts/{vid}"
    if not url and vid:
        url = f"https://www.youtube.com/watch?v={vid}"
    views = int(entry.get("view_count") or 0)
    likes = int(entry.get("like_count") or 0)
    comments = int(entry.get("comment_count") or 0)
    dur = int(round(float(entry.get("duration") or 0))) if entry.get("duration") else 0
    thumbs = entry.get("thumbnails") or []
    thumb_url = entry.get("thumbnail") or (thumbs[-1].get("url") if thumbs and isinstance(thumbs[-1], dict) else "")
    ts = entry.get("timestamp")
    upload_date = entry.get("upload_date") or ""
    if ts:
        iso_ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(int(ts)))
    elif len(upload_date) == 8 and upload_date.isdigit():
        iso_ts = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:8]}T12:00:00Z"
    else:
        iso_ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    short_code = f"{platform[:2]}_{vid}" if vid else f"{platform[:2]}_{hashlib.sha1((url or title).encode()).hexdigest()[:10]}"
    handle_clean = display_handle.lstrip("@")
    return {
        "shortCode": short_code,
        "id": short_code,
        "platform": platform,
        "creator_username": handle_clean,
        "creator_name": entry.get("channel") or entry.get("uploader") or display_handle,
        "url": url,
        "title": title,
        "caption": desc or title,
        "transcript": "",
        "transcript_source": "caption" if (desc or title) else "none",
        "plays": views,
        "likes": likes,
        "comments": comments,
        "duration": dur,
        "timestamp": iso_ts,
        "thumbUrl": thumb_url,
    }


def _compute_ratios(items):
    counts = [int(i.get("plays") or 0) for i in items if int(i.get("plays") or 0) > 0]
    median = int(statistics.median(counts)) if counts else 0
    for i in items:
        vp = int(i.get("plays") or 0)
        i["ratio"] = round(vp / median, 1) if (median and vp) else 1.0
    items.sort(key=lambda x: (x.get("ratio", 0), x.get("plays", 0)), reverse=True)
    return median


def _sync_local_instagram(bare_handle):
    """Reuse already-scraped data/<handle>_posts.json instantly at $0 cost."""
    p = DATA / f"{bare_handle.lower()}_posts.json"
    if not p.exists():
        return []
    try:
        doc = json.loads(p.read_text())
    except json.JSONDecodeError:
        return []
    out = []
    for item in doc.get("items") or []:
        sc = item.get("shortCode")
        if not sc:
            continue
        out.append({
            "shortCode": sc,
            "id": sc,
            "platform": "instagram",
            "creator_username": bare_handle.lower(),
            "creator_name": item.get("ownerFullName") or f"@{bare_handle}",
            "url": item.get("url") or f"https://www.instagram.com/reel/{sc}/",
            "title": (item.get("caption") or "").split("\n")[0][:120],
            "caption": item.get("caption") or "",
            "transcript": item.get("transcript") or "",
            "transcript_source": item.get("transcript_source") or ("tokscript" if item.get("transcript") else "caption"),
            "plays": int(item.get("videoPlayCount") or 0),
            "likes": int(item.get("likesCount") or 0),
            "comments": int(item.get("commentsCount") or 0),
            "duration": int(round(float(item.get("videoDuration") or 0))) if item.get("videoDuration") else 0,
            "timestamp": item.get("timestamp") or "",
            "thumbUrl": f"thumbs/{sc}.jpg" if (ROOT / "thumbs" / f"{sc}.jpg").exists() else (item.get("displayUrl") or ""),
            "clipUrl": f"clips/{sc}.mp4" if (ROOT / "clips" / f"{sc}.mp4").exists() else "",
            "breakdown": item.get("breakdown"),
        })
    return out


def sync_social_account(platform, handle_or_url, workspace_id="aisimple", role="owned", scope="all", limit=18):
    """
    Sync an owned account OR watchlist channel on Instagram, YouTube, TikTok, or Facebook.
    Saves results to data/socials/<role>_<platform>_<slug>.json and returns summary + items.
    """
    plat, display_handle, urls = normalize_social_target(platform, handle_or_url)
    bare = display_handle.lstrip("@")
    SOCIALS_DIR.mkdir(parents=True, exist_ok=True)
    slug = _slug(f"{workspace_id}_{role}_{plat}_{bare}")
    out_file = SOCIALS_DIR / f"{slug}.json"

    # Preserve any previously saved AI breakdowns on re-sync
    prev_breakdowns = {}
    if out_file.exists():
        try:
            old_doc = json.loads(out_file.read_text())
            for it in old_doc.get("items") or []:
                if it.get("shortCode") and it.get("breakdown"):
                    prev_breakdowns[it["shortCode"]] = it["breakdown"]
        except json.JSONDecodeError:
            pass

    items = []
    note = ""
    if plat == "instagram":
        items = _sync_local_instagram(bare)
        if not items:
            # Try yt-dlp fallback cleanly
            for u in urls:
                try:
                    raw_entries, err = _run_ytdlp_playlist(u, limit=limit, timeout=35)
                    if raw_entries:
                        items = [_normalize_ytdlp_entry(e, plat, display_handle) for e in raw_entries]
                        break
                    if err:
                        note = "Instagram profile saved. Run Admin → Refresh (Apify) to pull full 28-day Instagram Reel stats."
                except Exception:
                    note = "Instagram profile saved. Run Admin → Refresh (Apify) to pull full 28-day Instagram Reel stats."
    else:
        seen_ids = set()
        last_err = ""
        for u in urls:
            try:
                raw_entries, err = _run_ytdlp_playlist(u, limit=limit, timeout=55)
                if err:
                    last_err = err
                for e in raw_entries:
                    norm = _normalize_ytdlp_entry(e, plat, display_handle)
                    if norm["shortCode"] not in seen_ids:
                        seen_ids.add(norm["shortCode"])
                        items.append(norm)
                if len(items) >= limit:
                    break
            except subprocess.TimeoutExpired:
                last_err = f"Timed out fetching {u}"
            except Exception as exc:
                last_err = str(exc)
        if not items and plat == "facebook":
            note = "Facebook saved — public Page Reels sync automatically; personal profiles or login-gated Pages require setting OUTLIER_COOKIES_BROWSER=chrome in .env."
        elif not items and last_err:
            note = f"Account connected, but live video fetch returned no public videos ({last_err[:140]})."

    # Restore cached AI breakdowns
    for it in items:
        if not it.get("breakdown") and it["shortCode"] in prev_breakdowns:
            it["breakdown"] = prev_breakdowns[it["shortCode"]]

    items = items[:limit]
    median = _compute_ratios(items)
    total_views = sum(int(i.get("plays") or 0) for i in items)
    outliers_2x = sum(1 for i in items if (i.get("ratio") or 0) >= 2.0)

    record = {
        "workspaceId": workspace_id,
        "role": role,
        "scope": scope,
        "platform": plat,
        "handle": display_handle,
        "sourceUrl": urls[0] if urls else handle_or_url,
        "syncedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "videoCount": len(items),
        "medianViews": median,
        "totalViews": total_views,
        "outlierCount": outliers_2x,
        "note": note,
        "items": items,
    }
    write_json(out_file, record)
    return record


def fetch_single_video(url):
    """
    Auto-fetch metadata and spoken captions/transcript for ANY YouTube, TikTok,
    Facebook, or Instagram video URL using yt-dlp (zero API key required).
    """
    raw_url = (url or "").strip()
    plat = detect_platform_from_url(raw_url) or "instagram"
    ytdlp = _ytdlp_bin()
    if not ytdlp:
        return {"platform": plat, "url": raw_url, "error": "yt-dlp not installed"}

    with tempfile.TemporaryDirectory(prefix="outlier_vid_") as td:
        cmd = [
            ytdlp,
            "--skip-download",
            "--write-auto-sub",
            "--write-sub",
            "--sub-lang", "en,en-US",
            "--sub-format", "vtt",
            "--dump-single-json",
            "--no-warnings",
            "-o", str(Path(td) / "%(id)s.%(ext)s"),
        ]
        cookies_browser = os.environ.get("OUTLIER_COOKIES_BROWSER", "").strip()
        if cookies_browser:
            cmd += ["--cookies-from-browser", cookies_browser]
        cmd.append(raw_url)
        env = {**os.environ, "PATH": f"/opt/homebrew/bin:/usr/local/bin:{os.environ.get('PATH', '/usr/bin:/bin')}"}
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=55, env=env)
        except subprocess.TimeoutExpired:
            return {"platform": plat, "url": raw_url, "error": "Timed out fetching video metadata"}

        meta = {}
        for line in proc.stdout.splitlines():
            line = line.strip()
            if line.startswith("{"):
                try:
                    meta = json.loads(line)
                    break
                except json.JSONDecodeError:
                    pass

        # Collect auto-subtitles / captions if yt-dlp wrote a .vtt
        transcript = ""
        for vtt in sorted(Path(td).glob("*.vtt")):
            transcript = _parse_vtt_to_text(vtt.read_text(errors="ignore"))
            if transcript:
                break

        if not meta:
            return {"platform": plat, "url": raw_url, "transcript": transcript, "error": (proc.stderr or "").strip()[:200]}

        vid = str(meta.get("id") or hashlib.sha1(raw_url.encode()).hexdigest()[:10])
        creator = (meta.get("uploader_id") or meta.get("channel") or meta.get("uploader") or "creator").lstrip("@")
        title = (meta.get("title") or "").strip()
        desc = (meta.get("description") or "").strip()
        return {
            "shortCode": f"{plat[:2]}_{vid}",
            "platform": plat,
            "url": meta.get("webpage_url") or raw_url,
            "creator_username": creator,
            "creator_name": meta.get("channel") or meta.get("uploader") or f"@{creator}",
            "title": title,
            "caption": desc or title,
            "transcript": transcript,
            "transcript_source": "yt-dlp-captions" if transcript else ("caption" if (desc or title) else "none"),
            "plays": int(meta.get("view_count") or 0),
            "likes": int(meta.get("like_count") or 0),
            "comments": int(meta.get("comment_count") or 0),
            "duration": int(round(float(meta.get("duration") or 0))) if meta.get("duration") else 0,
            "thumbUrl": meta.get("thumbnail") or "",
        }
