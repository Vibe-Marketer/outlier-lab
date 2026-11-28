#!/usr/bin/env python3
"""
Outlier Lab — Sandcastles-Style Multi-Platform Account, Video Sync & Creator Discovery.

Supports Instagram, YouTube (Shorts + Videos), TikTok, and Facebook (Pages / Reels)
using handle or profile/video URL ingestion — no Meta/Google OAuth app review needed.

Powered by local `yt-dlp` (free, zero API keys) with parallel single-video metadata
enrichment for exact live views/likes/comments/followers and free live creator discovery.
Pure stdlib — no pip installs required.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
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
CONFIG_FILE = ROOT / "config.json"
ENV_FILE = ROOT / ".env"

_HTTP_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)

_STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "best", "by", "channel", "channels",
    "content", "creator", "creators", "do", "doing", "find", "for", "from", "good",
    "great", "how", "i", "in", "influencer", "influencers", "into", "is", "it",
    "looking", "make", "making", "me", "my", "of", "on", "or", "people", "person",
    "posting", "recommend", "search", "share", "sharing", "show", "some", "talk",
    "talking", "teach", "teaching", "that", "the", "their", "them", "they", "this",
    "to", "top", "video", "videos", "want", "who", "with", "youtube", "tiktok",
    "instagram", "facebook", "shorts", "reels", "about", "using", "build", "building",
}

_CURATED_CREATORS = [
    # AI & Automation
    {
        "platform": "youtube",
        "handle": "@kallaway",
        "name": "Kallaway",
        "url": "https://www.youtube.com/@kallaway",
        "niche": "AI & Short-Form Growth",
        "description": "AI tech explainers, short-form storytelling architecture, and viral hooks.",
    },
    {
        "platform": "youtube",
        "handle": "@LiamOttley",
        "name": "Liam Ottley",
        "url": "https://www.youtube.com/@LiamOttley",
        "niche": "AI & Automation",
        "description": "AI Automation Agency (AAA) frameworks, agent systems, and founder ops.",
    },
    {
        "platform": "youtube",
        "handle": "@nateherk",
        "name": "Nate Herk",
        "url": "https://www.youtube.com/@nateherk",
        "niche": "AI & Automation",
        "description": "Practical n8n and AI agent workflow tutorials for operators and agencies.",
    },
    {
        "platform": "youtube",
        "handle": "@GregIsenberg",
        "name": "Greg Isenberg",
        "url": "https://www.youtube.com/@GregIsenberg",
        "niche": "AI & Automation",
        "description": "AI startup ideas, distribution playbooks, and founder strategy breakdowns.",
    },
    {
        "platform": "youtube",
        "handle": "@mreflow",
        "name": "Matt Wolfe",
        "url": "https://www.youtube.com/@mreflow",
        "niche": "AI & Automation",
        "description": "Weekly AI tools, workflows, and no-fluff product demos.",
    },
    {
        "platform": "tiktok",
        "handle": "@aisimple.co",
        "name": "AI Simple",
        "url": "https://www.tiktok.com/@aisimple.co",
        "niche": "AI & Automation",
        "description": "Founder-focused AI workflows and practical business automation.",
    },
    {
        "platform": "instagram",
        "handle": "@aisimple.co",
        "name": "AI Simple",
        "url": "https://www.instagram.com/aisimple.co/reels/",
        "niche": "AI & Automation",
        "description": "Simple AI operating systems and workflow breakdowns for founders.",
    },
    # DTC & Paid Ads
    {
        "platform": "youtube",
        "handle": "@DaraDenney",
        "name": "Dara Denney",
        "url": "https://www.youtube.com/@DaraDenney",
        "niche": "DTC & Paid Ads",
        "description": "Meta Ads creative strategy, hook testing, and performance UGC breakdowns.",
    },
    {
        "platform": "instagram",
        "handle": "@daradenney",
        "name": "Dara Denney",
        "url": "https://www.instagram.com/daradenney/reels/",
        "niche": "DTC & Paid Ads",
        "description": "Paid social creative strategy and DTC ecommerce ad frameworks.",
    },
    {
        "platform": "youtube",
        "handle": "@NickTheriot",
        "name": "Nick Theriot",
        "url": "https://www.youtube.com/@NickTheriot",
        "niche": "DTC & Paid Ads",
        "description": "Facebook Ads scaling systems, creative testing, and ecommerce CRO.",
    },
    {
        "platform": "youtube",
        "handle": "@DavieFogarty",
        "name": "Davie Fogarty",
        "url": "https://www.youtube.com/@DavieFogarty",
        "niche": "DTC & Paid Ads",
        "description": "9-figure DTC brand building, offer positioning, and paid acquisition.",
    },
    {
        "platform": "youtube",
        "handle": "@LukeIha",
        "name": "Luke Iha",
        "url": "https://www.youtube.com/@LukeIha",
        "niche": "DTC & Paid Ads",
        "description": "Direct-response ad formats, copywriting DNA, and creative stacking.",
    },
    {
        "platform": "tiktok",
        "handle": "@sarahlevinger",
        "name": "Sarah Levinger",
        "url": "https://www.tiktok.com/@sarahlevinger",
        "niche": "DTC & Paid Ads",
        "description": "Buyer psychology and emotional creative testing for DTC paid social.",
    },
    # Marketing & Sales
    {
        "platform": "youtube",
        "handle": "@AlexHormozi",
        "name": "Alex Hormozi",
        "url": "https://www.youtube.com/@AlexHormozi",
        "niche": "Marketing & Sales",
        "description": "Offers, sales frameworks, lead generation, and high-retention business hooks.",
    },
    {
        "platform": "tiktok",
        "handle": "@hormozi",
        "name": "Alex Hormozi",
        "url": "https://www.tiktok.com/@hormozi",
        "niche": "Marketing & Sales",
        "description": "Short-form direct-response marketing, pricing, and founder leverage.",
    },
    {
        "platform": "youtube",
        "handle": "@danmartell",
        "name": "Dan Martell",
        "url": "https://www.youtube.com/@danmartell",
        "niche": "Marketing & Sales",
        "description": "Buy Back Your Time systems, SaaS/agency growth, and executive leverage.",
    },
    {
        "platform": "instagram",
        "handle": "@danmartell",
        "name": "Dan Martell",
        "url": "https://www.instagram.com/danmartell/reels/",
        "niche": "Marketing & Sales",
        "description": "Founder productivity, sales positioning, and scaling playbooks.",
    },
    {
        "platform": "facebook",
        "handle": "@AlexHormozi",
        "name": "Alex Hormozi",
        "url": "https://www.facebook.com/AlexHormozi/reels",
        "niche": "Marketing & Sales",
        "description": "Business offers, direct-response marketing, and high-converting Reels.",
    },
    {
        "platform": "facebook",
        "handle": "@gary",
        "name": "GaryVee",
        "url": "https://www.facebook.com/gary/reels",
        "niche": "Marketing & Sales",
        "description": "Organic attention, social media volume, and brand-building Reels.",
    },
    # Short-Form Growth
    {
        "platform": "youtube",
        "handle": "@DevinJatho",
        "name": "Devin Jatho",
        "url": "https://www.youtube.com/@DevinJatho",
        "niche": "Short-Form Growth",
        "description": "Viral short-form packaging, hook breakdowns, and retention editing.",
    },
    {
        "platform": "youtube",
        "handle": "@CalebRalston",
        "name": "Caleb Ralston",
        "url": "https://www.youtube.com/@CalebRalston",
        "niche": "Short-Form Growth",
        "description": "Brand strategy, personal brand content engines, and distribution systems.",
    },
    {
        "platform": "youtube",
        "handle": "@PaddyGalloway",
        "name": "Paddy Galloway",
        "url": "https://www.youtube.com/@PaddyGalloway",
        "niche": "Short-Form Growth",
        "description": "YouTube packaging, outlier analysis, and audience retention strategy.",
    },
    {
        "platform": "tiktok",
        "handle": "@jennyhoyoslol",
        "name": "Jenny Hoyos",
        "url": "https://www.tiktok.com/@jennyhoyoslol",
        "niche": "Short-Form Growth",
        "description": "Retention-engineered short-form storytelling and sub-60s pacing.",
    },
    {
        "platform": "instagram",
        "handle": "@kallaway",
        "name": "Kallaway",
        "url": "https://www.instagram.com/kallaway/reels/",
        "niche": "Short-Form Growth",
        "description": "Sandcastles-style storytelling frameworks, hooks, and AI commentary.",
    },
    {
        "platform": "facebook",
        "handle": "@danmartell",
        "name": "Dan Martell",
        "url": "https://www.facebook.com/danmartell/reels",
        "niche": "Short-Form Growth",
        "description": "High-retention founder clips and business systems Reels.",
    },
]


def _ytdlp_bin():
    return shutil.which("yt-dlp") or ("/opt/homebrew/bin/yt-dlp" if Path("/opt/homebrew/bin/yt-dlp").exists() else None)


def _ytdlp_env():
    return {**os.environ, "PATH": f"/opt/homebrew/bin:/usr/local/bin:{os.environ.get('PATH', '/usr/bin:/bin')}"}


def _slug(text):
    return re.sub(r"[^a-z0-9_-]+", "-", (text or "").lower().strip().lstrip("@")).strip("-") or "channel"


def _format_compact_num(value):
    try:
        n = int(round(float(value or 0)))
    except (TypeError, ValueError):
        return ""
    if n <= 0:
        return ""
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.1f}B"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def _parse_compact_num(text):
    """Parse strings like '40.5K', '1.2M', '12,345' into an integer."""
    if text is None:
        return 0
    if isinstance(text, (int, float)):
        return max(0, int(round(text)))
    s = str(text).strip().upper().replace(",", "")
    m = re.search(r"(\d+(?:\.\d+)?)\s*([KMB])?", s)
    if not m:
        return 0
    num = float(m.group(1))
    suffix = m.group(2) or ""
    mult = {"K": 1_000, "M": 1_000_000, "B": 1_000_000_000}.get(suffix, 1)
    return max(0, int(round(num * mult)))


def _extract_follower_count(entry):
    if not isinstance(entry, dict):
        return 0
    for key in (
        "channel_follower_count",
        "uploader_follower_count",
        "follower_count",
        "subscriber_count",
        "followersCount",
        "followers",
    ):
        val = entry.get(key)
        if val:
            parsed = _parse_compact_num(val)
            if parsed > 0:
                return parsed
    return 0


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


def _canonical_platform(platform, fallback="instagram"):
    plat = (platform or fallback or "instagram").lower().strip()
    if plat in {"yt", "youtube_shorts"}:
        return "youtube"
    if plat in {"ig", "insta"}:
        return "instagram"
    if plat in {"tt"}:
        return "tiktok"
    if plat in {"fb"}:
        return "facebook"
    return plat


def normalize_social_target(platform, handle_or_url):
    """Return (platform, display_handle, fetch_urls) for a handle or profile URL."""
    raw = (handle_or_url or "").strip()
    inferred = detect_platform_from_url(raw)
    plat = _canonical_platform(platform or inferred, fallback="instagram")

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
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=_ytdlp_env())
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


def _fetch_video_metadata_fast(url, timeout=15):
    """Fetch exact live single-video metadata via yt-dlp with a strict per-video timeout."""
    ytdlp = _ytdlp_bin()
    if not ytdlp or not url or not url.startswith(("http://", "https://")):
        return None
    cmd = [
        ytdlp,
        "--skip-download",
        "--dump-single-json",
        "--no-warnings",
    ]
    cookies_browser = os.environ.get("OUTLIER_COOKIES_BROWSER", "").strip()
    if cookies_browser:
        cmd += ["--cookies-from-browser", cookies_browser]
    cmd.append(url)
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=_ytdlp_env())
    except (subprocess.TimeoutExpired, OSError):
        return None
    for line in proc.stdout.splitlines():
        line = line.strip()
        if line.startswith("{"):
            try:
                data = json.loads(line)
                if isinstance(data, dict):
                    return data
            except json.JSONDecodeError:
                continue
    return None


def _fetch_profile_followers(platform, display_handle, source_url=""):
    """Lightweight stdlib fallback to retrieve real follower/subscriber counts when yt-dlp omits them."""
    bare = (display_handle or "").lstrip("@").strip()
    if not bare:
        return 0

    if platform == "instagram":
        # Reuse already-stored real follower count from config.json if tracked
        if CONFIG_FILE.exists():
            try:
                cfg = json.loads(CONFIG_FILE.read_text())
                for c in cfg.get("creators") or []:
                    if str(c.get("handle") or "").lstrip("@").lower() == bare.lower():
                        fc = _parse_compact_num(c.get("followers") or c.get("followersCount"))
                        if fc > 0:
                            return fc
            except (OSError, json.JSONDecodeError):
                pass
        return 0

    if platform == "tiktok":
        url = f"https://www.tiktok.com/@{urllib.parse.quote(bare)}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": _HTTP_UA, "Accept-Language": "en-US,en;q=0.9"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                html = resp.read().decode("utf-8", "ignore")
            m_script = re.search(
                r'<script[^>]+id=["\']__UNIVERSAL_DATA_FOR_REHYDRATION__["\'][^>]*>(.*?)</script>',
                html,
                re.S,
            )
            if m_script:
                try:
                    blob = json.loads(m_script.group(1))
                    default_scope = blob.get("__DEFAULT_SCOPE__") or {}
                    user_detail = default_scope.get("webapp.user-detail") or {}
                    stats = (user_detail.get("userInfo") or {}).get("stats") or {}
                    fc = _parse_compact_num(stats.get("followerCount"))
                    if fc > 0:
                        return fc
                except json.JSONDecodeError:
                    pass
            m_fc = re.search(r'"followerCount"\s*:\s*(\d+)', html)
            if m_fc:
                return int(m_fc.group(1))
        except Exception:
            return 0
        return 0

    if platform == "youtube":
        url = source_url if source_url.startswith("http") else f"https://www.youtube.com/@{urllib.parse.quote(bare)}"
        url = re.sub(r"/(shorts|videos)/?$", "", url.rstrip("/"))
        try:
            req = urllib.request.Request(url, headers={"User-Agent": _HTTP_UA, "Accept-Language": "en-US,en;q=0.9"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                html = resp.read().decode("utf-8", "ignore")
            m = re.search(r'"subscriberCountText"\s*:\s*\{[^{}]*"simpleText"\s*:\s*"([^"]+)"', html)
            if not m:
                m = re.search(r'([\d.,]+\s*[KMB]?)\s+subscribers', html, re.I)
            if m:
                return _parse_compact_num(m.group(1))
        except Exception:
            return 0
        return 0

    return 0


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


def _format_entry_timestamp(entry):
    ts = entry.get("timestamp")
    upload_date = str(entry.get("upload_date") or "")
    if ts:
        try:
            return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(int(ts))), True
        except (TypeError, ValueError, OSError):
            pass
    if len(upload_date) == 8 and upload_date.isdigit():
        return f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:8]}T12:00:00Z", True
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), False


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
    iso_ts, _ = _format_entry_timestamp(entry)

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


def _needs_enrichment(raw_entry, norm_item):
    """Return True when --flat-playlist omitted exact views, engagement, duration, or timestamp."""
    if int(norm_item.get("plays") or 0) <= 0:
        return True
    if raw_entry.get("view_count") is None:
        return True
    if (
        raw_entry.get("like_count") is None
        and raw_entry.get("comment_count") is None
        and not raw_entry.get("duration")
    ):
        return True
    if not raw_entry.get("timestamp") and not raw_entry.get("upload_date"):
        return True
    return False


def _merge_enriched_entry(item, enriched):
    """Merge live single-video yt-dlp JSON into a normalized item without clobbering clean URLs."""
    if not isinstance(enriched, dict):
        return item
    if enriched.get("view_count") is not None:
        vc = int(enriched.get("view_count") or 0)
        if vc > 0 or item.get("plays", 0) == 0:
            item["plays"] = vc
    if enriched.get("like_count") is not None:
        item["likes"] = int(enriched.get("like_count") or 0)
    if enriched.get("comment_count") is not None:
        item["comments"] = int(enriched.get("comment_count") or 0)
    if enriched.get("duration"):
        item["duration"] = int(round(float(enriched.get("duration") or 0)))
    iso_ts, has_real_ts = _format_entry_timestamp(enriched)
    if has_real_ts:
        item["timestamp"] = iso_ts
    creator_name = enriched.get("channel") or enriched.get("uploader")
    if creator_name:
        item["creator_name"] = creator_name
    title = (enriched.get("title") or "").strip()
    desc = (enriched.get("description") or "").strip()
    if title and not item.get("title"):
        item["title"] = title
    if desc and (not item.get("caption") or len(desc) > len(item.get("caption") or "")):
        item["caption"] = desc
        if not item.get("transcript"):
            item["transcript_source"] = "caption"
    wp = enriched.get("webpage_url") or ""
    if wp.startswith("http") and not item.get("url"):
        item["url"] = wp
    if enriched.get("thumbnail") and not item.get("thumbUrl"):
        item["thumbUrl"] = enriched["thumbnail"]
    return item


def _enrich_items_parallel(raw_pairs, platform, max_enrich=8, max_workers=4, per_video_timeout=15):
    """
    Parallel single-video enrichment for TikTok, YouTube, and Facebook.
    Returns (enriched_count, follower_count, detected_creator_name).
    """
    follower_count = 0
    detected_name = ""
    for raw, _ in raw_pairs:
        fc = _extract_follower_count(raw)
        if fc > follower_count:
            follower_count = fc
        if not detected_name and (raw.get("channel") or raw.get("uploader")):
            detected_name = str(raw.get("channel") or raw.get("uploader")).strip()

    if platform not in {"tiktok", "youtube", "facebook"} or not raw_pairs:
        return 0, follower_count, detected_name

    # Prioritize: (1) missing/zero view_count, (2) missing engagement/duration/timestamp,
    # (3) if follower_count is still 0, probe top entries to pull exact live counts & followers.
    missing_views = [i for i, (r, it) in enumerate(raw_pairs) if int(it.get("plays") or 0) <= 0]
    missing_meta = [
        i for i, (r, it) in enumerate(raw_pairs)
        if i not in missing_views and _needs_enrichment(r, it)
    ]

    targets = []
    for idx in missing_views + missing_meta:
        if idx not in targets:
            targets.append(idx)
        if len(targets) >= max_enrich:
            break

    # If flat-playlist had views/meta but no follower count (common on TikTok), enrich top entries
    if not targets and follower_count == 0:
        ranked = sorted(range(len(raw_pairs)), key=lambda i: int(raw_pairs[i][1].get("plays") or 0), reverse=True)
        targets = ranked[: min(4, len(ranked))]

    targets = [i for i in targets if (raw_pairs[i][1].get("url") or "").startswith("http")]
    if not targets:
        return 0, follower_count, detected_name

    enriched_count = 0
    with ThreadPoolExecutor(max_workers=min(max_workers, len(targets))) as pool:
        future_map = {
            pool.submit(_fetch_video_metadata_fast, raw_pairs[idx][1]["url"], per_video_timeout): idx
            for idx in targets
        }
        for fut in as_completed(future_map):
            idx = future_map[fut]
            try:
                meta = fut.result()
            except Exception:
                meta = None
            if not meta:
                continue
            enriched_count += 1
            _merge_enriched_entry(raw_pairs[idx][1], meta)
            fc = _extract_follower_count(meta)
            if fc > follower_count:
                follower_count = fc
            cname = (meta.get("channel") or meta.get("uploader") or "").strip()
            if cname and not detected_name:
                detected_name = cname

    return enriched_count, follower_count, detected_name


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
    Enriches missing/incomplete entries in parallel for exact live views, likes, comments,
    duration, timestamps, and follower counts. Saves results to
    data/socials/<workspace>_<role>_<platform>_<slug>.json and returns summary + items.
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

    raw_pairs = []
    items = []
    note = ""
    follower_count = 0
    detected_name = ""
    enriched_count = 0

    if plat == "instagram":
        items = _sync_local_instagram(bare)
        if items:
            detected_name = items[0].get("creator_name") or display_handle
        else:
            # Try yt-dlp fallback cleanly
            for u in urls:
                try:
                    raw_entries, err = _run_ytdlp_playlist(u, limit=limit, timeout=35)
                    if raw_entries:
                        for e in raw_entries:
                            fc = _extract_follower_count(e)
                            if fc > follower_count:
                                follower_count = fc
                            items.append(_normalize_ytdlp_entry(e, plat, display_handle))
                        break
                    if err:
                        note = "Instagram profile saved. Run Admin → Refresh (Apify) to pull full 28-day Instagram Reel stats."
                except Exception:
                    note = "Instagram profile saved. Run Admin → Refresh (Apify) to pull full 28-day Instagram Reel stats."
        if follower_count == 0:
            follower_count = _fetch_profile_followers("instagram", display_handle, urls[0] if urls else "")
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
                        raw_pairs.append((e, norm))
                if len(raw_pairs) >= limit:
                    break
            except subprocess.TimeoutExpired:
                last_err = f"Timed out fetching {u}"
            except Exception as exc:
                last_err = str(exc)

        raw_pairs = raw_pairs[:limit]
        enriched_count, follower_count, detected_name = _enrich_items_parallel(
            raw_pairs,
            plat,
            max_enrich=8,
            max_workers=4,
            per_video_timeout=15,
        )
        items = [it for _, it in raw_pairs]

        # Propagate resolved real channel/creator name to items that fell back to display_handle
        if detected_name:
            for it in items:
                if not it.get("creator_name") or it.get("creator_name") == display_handle:
                    it["creator_name"] = detected_name

        # Fallback profile lookup for real follower count if yt-dlp omitted it (e.g. TikTok)
        if follower_count == 0:
            follower_count = _fetch_profile_followers(plat, display_handle, urls[0] if urls else "")

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
        "creatorName": detected_name or display_handle,
        "sourceUrl": urls[0] if urls else handle_or_url,
        "syncedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "followerCount": follower_count,
        "followers": _format_compact_num(follower_count),
        "videoCount": len(items),
        "medianViews": median,
        "medianViewsFormatted": _format_compact_num(median),
        "totalViews": total_views,
        "outlierCount": outliers_2x,
        "enrichedCount": enriched_count,
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
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=55, env=_ytdlp_env())
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
        follower_count = _extract_follower_count(meta)
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
            "followerCount": follower_count,
            "followers": _format_compact_num(follower_count),
            "thumbUrl": meta.get("thumbnail") or "",
        }


# ──────────────────── FREE LIVE CREATOR DISCOVERY ($0) ────────────────────

def _platform_profile_url(platform, bare_handle):
    bare = (bare_handle or "").lstrip("@").strip().strip("/")
    if not bare:
        return ""
    if platform == "youtube":
        return f"https://www.youtube.com/@{bare}"
    if platform == "tiktok":
        return f"https://www.tiktok.com/@{bare}"
    if platform == "instagram":
        return f"https://www.instagram.com/{bare}/reels/"
    if platform == "facebook":
        return f"https://www.facebook.com/{bare}/reels"
    return ""


def _platform_search_url(platform, query):
    q = urllib.parse.quote_plus((query or "").strip())
    if platform == "tiktok":
        return f"https://www.tiktok.com/search/user?q={q}"
    if platform == "instagram":
        return f"https://www.instagram.com/explore/search/keyword/?q={q}"
    if platform == "facebook":
        return f"https://www.facebook.com/search/pages/?q={q}"
    return f"https://www.youtube.com/results?search_query={q}"


def _extract_search_terms_heuristic(description):
    """Pure-stdlib keyword extractor turning a natural-language brief into 2 crisp search queries."""
    raw = (description or "").strip()
    if not raw:
        return []
    cleaned = re.sub(r"https?://\S+", " ", raw)
    cleaned = re.sub(r"[^A-Za-z0-9\s&/+-]", " ", cleaned)
    tokens = [t.strip("+-/") for t in cleaned.split() if t.strip("+-/")]
    kept = []
    seen = set()
    for t in tokens:
        low = t.lower()
        if low in _STOP_WORDS or len(low) < 2:
            continue
        if low not in seen:
            seen.add(low)
            kept.append(t)
    if not kept:
        return [raw[:80]]
    primary = " ".join(kept[:5])
    terms = [primary]
    if len(kept) >= 4:
        alt = " ".join(kept[:3]) + " tutorial"
        if alt.lower() != primary.lower():
            terms.append(alt)
    elif len(kept) <= 3:
        terms.append(f"{primary} strategy")
    return terms[:2]


def _expand_description_to_queries(description):
    """Expand natural-language creator description into crisp search terms (LLM if available, else heuristic)."""
    desc = (description or "").strip()
    if not desc:
        return [], "heuristic"
    try:
        import ai_engine

        info = ai_engine.detect_providers()
        if info.get("default") and info["default"] != "local":
            prompt = (
                "Convert this creator-discovery brief into 2 concise YouTube/social search queries "
                "(3-5 words each) that will surface top active creators teaching or creating in this exact niche.\n"
                f"BRIEF: {desc[:400]}\n"
                'Return ONLY valid JSON: {"queries": ["query 1", "query 2"], "niche": "2-4 word niche label"}'
            )
            engine, obj = ai_engine.call_llm_json(prompt, provider="auto", timeout=22)
            qs = [str(q).strip() for q in (obj.get("queries") or []) if str(q).strip()]
            if qs:
                return qs[:2], engine
    except Exception:
        pass
    return _extract_search_terms_heuristic(desc), "heuristic"


def _discover_youtube_search(query, search_count=24, timeout=45):
    """Run live `yt-dlp --flat-playlist --dump-json ytsearch24:<query>` and aggregate by unique channel."""
    q = (query or "").strip()
    if not q:
        return [], "Empty search query."
    raw_entries, err = _run_ytdlp_playlist(f"ytsearch{search_count}:{q}", limit=search_count, timeout=timeout)
    if not raw_entries:
        return [], err or f"No live YouTube results returned for '{q}'."

    grouped = {}
    for entry in raw_entries:
        channel_name = (entry.get("channel") or entry.get("uploader") or "").strip()
        channel_id = (entry.get("channel_id") or "").strip()
        uploader_id = (entry.get("uploader_id") or "").strip()
        channel_url = (entry.get("uploader_url") or entry.get("channel_url") or "").strip()
        if not (channel_name or channel_id or uploader_id):
            continue

        key = (channel_id or uploader_id or channel_name).lower()
        if uploader_id:
            handle = uploader_id if uploader_id.startswith("@") else f"@{uploader_id}"
        elif "/@" in channel_url:
            handle = "@" + channel_url.split("/@", 1)[1].split("/", 1)[0]
        else:
            handle = f"@{_slug(channel_name or channel_id)}"

        if not channel_url:
            if channel_id:
                channel_url = f"https://www.youtube.com/channel/{channel_id}"
            else:
                channel_url = _platform_profile_url("youtube", handle)

        views = int(entry.get("view_count") or 0)
        vid = str(entry.get("id") or "")
        v_url = entry.get("webpage_url") or entry.get("url") or (f"https://www.youtube.com/watch?v={vid}" if vid else "")
        title = (entry.get("title") or "").strip()
        thumbs = entry.get("thumbnails") or []
        thumb = entry.get("thumbnail") or (thumbs[-1].get("url") if thumbs and isinstance(thumbs[-1], dict) else "")
        fc = _extract_follower_count(entry)

        bucket = grouped.setdefault(
            key,
            {
                "channelId": channel_id,
                "name": channel_name or handle,
                "handle": handle,
                "url": channel_url,
                "views": [],
                "followerCount": 0,
                "topViews": -1,
                "topVideoTitle": "",
                "topVideoUrl": "",
                "thumbUrl": "",
                "sampleCount": 0,
            },
        )
        bucket["sampleCount"] += 1
        if views > 0:
            bucket["views"].append(views)
        if fc > bucket["followerCount"]:
            bucket["followerCount"] = fc
        if views >= bucket["topViews"]:
            bucket["topViews"] = views
            bucket["topVideoTitle"] = title
            bucket["topVideoUrl"] = v_url
            if thumb:
                bucket["thumbUrl"] = thumb

    creators = []
    for bucket in grouped.values():
        pos_views = bucket["views"]
        median_views = int(statistics.median(pos_views)) if pos_views else 0
        max_views = max(pos_views) if pos_views else 0
        fc = bucket["followerCount"]
        creators.append({
            "platform": "youtube",
            "handle": bucket["handle"],
            "name": bucket["name"],
            "channelId": bucket["channelId"],
            "url": bucket["url"],
            "trackTarget": bucket["url"],
            "niche": q,
            "description": bucket["topVideoTitle"] or f"Active YouTube creator matching '{q}'",
            "medianViews": median_views,
            "medianViewsFormatted": _format_compact_num(median_views),
            "maxViews": max_views,
            "maxViewsFormatted": _format_compact_num(max_views),
            "followerCount": fc,
            "followers": _format_compact_num(fc),
            "sampleCount": bucket["sampleCount"],
            "topVideoTitle": bucket["topVideoTitle"],
            "topVideoUrl": bucket["topVideoUrl"],
            "thumbUrl": bucket["thumbUrl"],
            "verified": True,
            "source": "ytsearch",
        })

    creators.sort(
        key=lambda c: (
            int(c["medianViews"] * (1 + 0.45 * max(0, c["sampleCount"] - 1))),
            c["sampleCount"],
            c["maxViews"],
        ),
        reverse=True,
    )
    return creators, ""


def _probe_direct_social_profile(platform, handle_or_url):
    """Verify a direct handle/URL on TikTok, Instagram, Facebook, or YouTube via normalize_social_target + yt-dlp."""
    plat, display_handle, urls = normalize_social_target(platform, handle_or_url)
    bare = display_handle.lstrip("@")
    canonical_url = _platform_profile_url(plat, bare) or (urls[0] if urls else handle_or_url)

    raw_entries = []
    last_err = ""
    for u in urls[:2]:
        try:
            entries, err = _run_ytdlp_playlist(u, limit=6, timeout=20)
            if entries:
                raw_entries = entries
                break
            if err:
                last_err = err
        except (subprocess.TimeoutExpired, Exception) as exc:
            last_err = str(exc)

    follower_count = 0
    views_list = []
    top_title = ""
    top_url = ""
    top_views = -1
    thumb_url = ""
    creator_name = display_handle

    for e in raw_entries:
        fc = _extract_follower_count(e)
        if fc > follower_count:
            follower_count = fc
        if e.get("channel") or e.get("uploader"):
            creator_name = str(e.get("channel") or e.get("uploader")).strip()
        v = int(e.get("view_count") or 0)
        if v > 0:
            views_list.append(v)
        if v >= top_views:
            top_views = v
            top_title = (e.get("title") or e.get("description") or "").strip()
            top_url = e.get("webpage_url") or e.get("url") or ""
            thumbs = e.get("thumbnails") or []
            thumb_url = e.get("thumbnail") or (thumbs[-1].get("url") if thumbs and isinstance(thumbs[-1], dict) else "")

    if follower_count == 0:
        follower_count = _fetch_profile_followers(plat, display_handle, canonical_url)

    verified = bool(raw_entries or follower_count > 0)
    median_views = int(statistics.median(views_list)) if views_list else 0
    max_views = max(views_list) if views_list else 0

    return {
        "platform": plat,
        "handle": display_handle,
        "name": creator_name,
        "channelId": "",
        "url": canonical_url,
        "trackTarget": canonical_url,
        "niche": "Direct Profile",
        "description": top_title or (
            f"Verified {plat.title()} profile ({len(raw_entries)} recent videos)"
            if raw_entries
            else f"Direct {plat.title()} profile ready to track ({last_err[:80]})" if last_err
            else f"Direct {plat.title()} profile ready to track"
        ),
        "medianViews": median_views,
        "medianViewsFormatted": _format_compact_num(median_views),
        "maxViews": max_views,
        "maxViewsFormatted": _format_compact_num(max_views),
        "followerCount": follower_count,
        "followers": _format_compact_num(follower_count),
        "sampleCount": len(raw_entries),
        "topVideoTitle": top_title,
        "topVideoUrl": top_url,
        "thumbUrl": thumb_url,
        "verified": verified,
        "source": "direct_profile" if verified else "direct_profile_unverified",
    }


def _looks_like_handle_or_url(text):
    s = (text or "").strip()
    if not s:
        return False
    if s.startswith(("http://", "https://", "@")):
        return True
    if " " not in s and re.fullmatch(r"[A-Za-z0-9._-]{2,40}", s):
        return True
    return False


def _suggested_creators(query="", platform="all", limit=12):
    q = (query or "").strip().lower()
    plat = (platform or "all").strip().lower()
    if plat not in {"all", "youtube", "tiktok", "instagram", "facebook"}:
        plat = _canonical_platform(plat, fallback="all")

    q_tokens = [t for t in re.split(r"[^a-z0-9]+", q) if len(t) >= 2] if q else []
    scored = []
    for idx, c in enumerate(_CURATED_CREATORS):
        if plat != "all" and c["platform"] != plat:
            continue
        haystack = f"{c['niche']} {c['name']} {c['handle']} {c['description']} {c['platform']}".lower()
        score = 0
        if q_tokens:
            score = sum(2 if tok in c["niche"].lower() else (1 if tok in haystack else 0) for tok in q_tokens)
        scored.append((score, -idx, c))

    if q_tokens and any(s > 0 for s, _, _ in scored):
        scored = [row for row in scored if row[0] > 0]
    scored.sort(key=lambda r: (r[0], r[1]), reverse=True)

    cards = []
    for _, _, c in scored[:limit]:
        cards.append({
            "platform": c["platform"],
            "handle": c["handle"],
            "name": c["name"],
            "channelId": "",
            "url": c["url"],
            "trackTarget": c["url"],
            "niche": c["niche"],
            "description": c["description"],
            "medianViews": 0,
            "medianViewsFormatted": "",
            "maxViews": 0,
            "maxViewsFormatted": "",
            "followerCount": 0,
            "followers": "",
            "sampleCount": 0,
            "topVideoTitle": "",
            "topVideoUrl": "",
            "thumbUrl": "",
            "verified": True,
            "source": "curated",
        })
    return cards


def _merge_creator_cards(cards, limit):
    seen = set()
    out = []
    for c in cards:
        key = (c.get("platform", ""), (c.get("channelId") or c.get("handle") or c.get("url") or "").lower())
        if not key[1] or key in seen:
            continue
        seen.add(key)
        out.append(c)
        if len(out) >= limit:
            break
    return out


def discover_creators(query="", platform="youtube", mode="search", limit=12):
    """
    Free ($0) live creator discovery across YouTube, TikTok, Instagram & Facebook.

    Modes:
      - "search": Live YouTube channel discovery via yt-dlp ytsearch24 (grouped by unique
        channel with real sample median/max views & top video) OR direct handle/profile
        verification + searchable profile URLs + YouTube cross-matches for TikTok/IG/FB.
      - "describe": Expands a natural-language description (via ai_engine.call_llm_json if
        available, else smart keyword extraction) into crisp search terms and runs live search.
      - "suggested": Returns curated real handles across AI, DTC/Paid Ads, Marketing, and
        Short-Form Growth ready for 1-click tracking.
    """
    raw_query = (query or "").strip()
    plat_raw = (platform or "youtube").strip().lower()
    plat = "all" if plat_raw == "all" else _canonical_platform(plat_raw, fallback="youtube")
    mode_norm = (mode or "search").strip().lower()
    lim = max(1, min(30, int(limit or 12)))

    if mode_norm == "suggested":
        cards = _suggested_creators(query=raw_query, platform=plat, limit=lim)
        return {
            "ok": True,
            "query": raw_query,
            "platform": plat,
            "mode": "suggested",
            "searchTerms": [raw_query] if raw_query else [],
            "engine": "curated",
            "count": len(cards),
            "creators": cards,
            "note": "Curated real creator handles across AI, DTC/Paid Ads, Marketing, and Short-Form Growth.",
        }

    if not raw_query:
        cards = _suggested_creators(query="", platform=plat, limit=lim)
        return {
            "ok": True,
            "query": "",
            "platform": plat,
            "mode": mode_norm,
            "searchTerms": [],
            "engine": "curated",
            "count": len(cards),
            "creators": cards,
            "note": "Enter a topic, description, or @handle to discover live creators.",
        }

    search_terms = [raw_query]
    engine_used = "yt-dlp"
    if mode_norm == "describe":
        expanded, exp_engine = _expand_description_to_queries(raw_query)
        if expanded:
            search_terms = expanded
        engine_used = f"{exp_engine}+yt-dlp"

    creators = []
    notes = []

    if plat in {"youtube", "all"}:
        # If the user entered a direct handle/URL on YouTube (or any platform when plat == "all"), probe it first
        if _looks_like_handle_or_url(raw_query):
            inferred_plat = detect_platform_from_url(raw_query) or ("youtube" if plat == "youtube" else "tiktok")
            try:
                direct = _probe_direct_social_profile(inferred_plat, raw_query)
                if direct.get("verified"):
                    creators.append(direct)
            except Exception:
                pass

        # Run live YouTube search(es) in parallel
        with ThreadPoolExecutor(max_workers=min(2, len(search_terms))) as pool:
            futs = [pool.submit(_discover_youtube_search, term, 24, 45) for term in search_terms]
            for fut in as_completed(futs):
                try:
                    found, err = fut.result()
                    creators.extend(found)
                    if err and not found:
                        notes.append(err)
                except Exception as exc:
                    notes.append(str(exc)[:140])

        if plat == "all" and len(creators) < lim:
            creators.extend(_suggested_creators(query=raw_query, platform="all", limit=lim))

        merged = _merge_creator_cards(creators, lim)
        return {
            "ok": True,
            "query": raw_query,
            "platform": plat,
            "mode": mode_norm,
            "searchTerms": search_terms,
            "engine": engine_used,
            "count": len(merged),
            "creators": merged,
            "note": "; ".join(notes[:2]) if (notes and not merged) else "",
        }

    # Platform in {"tiktok", "instagram", "facebook"}
    # 1. Direct handle/profile verification if query looks like a handle or URL
    if _looks_like_handle_or_url(raw_query):
        try:
            direct_card = _probe_direct_social_profile(plat, raw_query)
            creators.append(direct_card)
        except Exception as exc:
            notes.append(str(exc)[:140])
    else:
        # Also include a clean searchable direct profile candidate for the primary keyword slug
        candidate_handle = _slug(search_terms[0]).replace("-", "")
        if candidate_handle:
            creators.append({
                "platform": plat,
                "handle": f"@{candidate_handle}",
                "name": f"Search '{raw_query}' on {plat.title()}",
                "channelId": "",
                "url": _platform_search_url(plat, raw_query),
                "trackTarget": _platform_profile_url(plat, candidate_handle),
                "niche": raw_query,
                "description": f"Open live {plat.title()} search for '{raw_query}', or track verified cross-matches below.",
                "medianViews": 0,
                "medianViewsFormatted": "",
                "maxViews": 0,
                "maxViewsFormatted": "",
                "followerCount": 0,
                "followers": "",
                "sampleCount": 0,
                "topVideoTitle": "",
                "topVideoUrl": "",
                "thumbUrl": "",
                "verified": False,
                "source": "platform_search",
            })

    # 2. Matching curated handles on the requested platform
    curated_matches = _suggested_creators(query=raw_query, platform=plat, limit=4)
    creators.extend(curated_matches)

    # 3. Live YouTube cross-matches (free via yt-dlp) enriched with searchable profile URLs for `plat`
    yt_query = search_terms[0].lstrip("@")
    try:
        yt_matches, err = _discover_youtube_search(yt_query, search_count=24, timeout=45)
        if err and not yt_matches:
            notes.append(err)
        for card in yt_matches:
            bare = card["handle"].lstrip("@")
            cross_url = _platform_profile_url(plat, bare)
            enriched_card = dict(card)
            enriched_card["crossMatchFor"] = plat
            enriched_card["suggestedPlatformUrl"] = cross_url
            enriched_card["platformSearchUrl"] = _platform_search_url(plat, card["name"] or bare)
            enriched_card["source"] = "youtube_cross_match"
            creators.append(enriched_card)
    except Exception as exc:
        notes.append(str(exc)[:140])

    merged = _merge_creator_cards(creators, lim)
    return {
        "ok": True,
        "query": raw_query,
        "platform": plat,
        "mode": mode_norm,
        "searchTerms": search_terms,
        "engine": engine_used,
        "count": len(merged),
        "creators": merged,
        "note": (
            f"Showing direct {plat.title()} profile lookup + live cross-platform creator matches (free via yt-dlp)."
            if merged
            else "; ".join(notes[:2])
        ),
    }
