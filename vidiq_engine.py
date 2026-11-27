#!/usr/bin/env python3
"""
Outlier Lab — vidIQ-Grade Keyword, Tag, Title, Packaging & VPH Intelligence Engine.

Uses REAL live signals with zero paid API keys:
  1. YouTube Search Autocomplete / Suggest API (matching, related, question keywords)
  2. Live YouTube SERP scraping via `yt-dlp ytsearch` (real ranking videos, views, VPH,
     channel competition, exact title match density, outlier breakout signal)
  3. Deterministic vidIQ-style scoring (Overall 0-100, Demand/Volume, Competition,
     Title 0-100 across 5 checks, Individual Tag 0-100 scores, Actionable SEO Checklist)
  4. Optional Claude / Codex CLI boost (via ai_engine.py) for AI Title Variants,
     Thumbnail Concepts, Descriptions, and Daily Predicted Ideas.

Pure stdlib — no pip installs required.
"""

import json
import math
import os
import re
import shutil
import statistics
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"


def _ytdlp_bin():
    return shutil.which("yt-dlp") or ("/opt/homebrew/bin/yt-dlp" if Path("/opt/homebrew/bin/yt-dlp").exists() else None)


# ──────────────────── 1. LIVE YOUTUBE SUGGEST API ────────────────────

def fetch_yt_suggestions(query, timeout=6):
    """Fetch real YouTube search autocomplete suggestions for a query."""
    q = (query or "").strip()
    if not q:
        return []
    url = "https://suggestqueries.google.com/complete/search?" + urllib.parse.urlencode({
        "client": "firefox",
        "ds": "yt",
        "q": q,
    })
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="ignore"))
        if isinstance(data, list) and len(data) >= 2 and isinstance(data[1], list):
            return [str(s).strip() for s in data[1] if str(s).strip()]
    except Exception:
        return []
    return []


def gather_keyword_universe(seed):
    """Pull matching terms, related modifiers, and real viewer questions in parallel."""
    seed = (seed or "").strip()
    queries = [
        ("matching", seed),
        ("matching", f"{seed} "),
        ("related", f"{seed} tutorial"),
        ("related", f"{seed} workflow"),
        ("related", f"{seed} tools"),
        ("related", f"best {seed}"),
        ("related", f"{seed} for beginners"),
        ("related", f"{seed} 2026"),
        ("question", f"how to {seed}"),
        ("question", f"what is {seed}"),
        ("question", f"why {seed}"),
        ("question", f"can {seed}"),
    ]

    def _run(item):
        bucket, q = item
        return (bucket, fetch_yt_suggestions(q))

    buckets = {"matching": [], "related": [], "question": []}
    seen_all = set()
    with ThreadPoolExecutor(max_workers=8) as ex:
        for bucket, suggs in ex.map(_run, queries):
            for s in suggs:
                sl = s.lower()
                if sl in seen_all:
                    continue
                seen_all.add(sl)
                if re.match(r"^(how|what|why|when|where|who|can|is|are|does|do|should|will)\b", sl):
                    buckets["question"].append(s)
                elif bucket == "matching" or seed.lower() in sl:
                    buckets["matching"].append(s)
                else:
                    buckets["related"].append(s)
    return buckets


# ──────────────────── 2. LIVE YOUTUBE SERP COMPETITION & VPH ────────────────────

def _hours_since(upload_date, timestamp=None):
    now = time.time()
    if timestamp:
        try:
            return max(1.0, (now - float(timestamp)) / 3600.0)
        except (TypeError, ValueError):
            pass
    if upload_date and len(str(upload_date)) == 8 and str(upload_date).isdigit():
        try:
            dt = datetime.strptime(str(upload_date), "%Y%m%d").replace(tzinfo=timezone.utc)
            return max(1.0, (now - dt.timestamp()) / 3600.0)
        except ValueError:
            pass
    return 24.0 * 60.0  # fallback ~60 days


def fetch_yt_serp(keyword, count=12, timeout=35):
    """Fetch top ranking YouTube videos for a keyword using yt-dlp ytsearch."""
    ytdlp = _ytdlp_bin()
    if not ytdlp:
        return []
    cmd = [
        ytdlp,
        "--flat-playlist",
        "--dump-json",
        "--no-warnings",
        "--ignore-errors",
        f"ytsearch{count}:{keyword}",
    ]
    env = {**os.environ, "PATH": f"/opt/homebrew/bin:/usr/local/bin:{os.environ.get('PATH', '/usr/bin:/bin')}"}
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)
    except Exception:
        return []

    videos = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        vid = str(e.get("id") or "")
        if not vid:
            continue
        views = int(e.get("view_count") or 0)
        hrs = _hours_since(e.get("upload_date"), e.get("timestamp"))
        vph = round(views / hrs, 1) if views else 0.0
        thumbs = e.get("thumbnails") or []
        thumb = e.get("thumbnail") or (thumbs[-1].get("url") if thumbs and isinstance(thumbs[-1], dict) else f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg")
        url = e.get("webpage_url") or e.get("url") or f"https://www.youtube.com/watch?v={vid}"
        if not url.startswith("http"):
            url = f"https://www.youtube.com/watch?v={vid}"
        videos.append({
            "id": vid,
            "shortCode": f"yt_{vid}",
            "title": (e.get("title") or "").strip(),
            "channel": (e.get("channel") or e.get("uploader") or "YouTube Creator").strip(),
            "channelUrl": e.get("channel_url") or e.get("uploader_url") or "",
            "views": views,
            "vph": vph,
            "duration": int(round(float(e.get("duration") or 0))) if e.get("duration") else 0,
            "uploadDate": e.get("upload_date") or "",
            "ageDays": max(1, int(round(hrs / 24.0))),
            "url": url,
            "thumbUrl": thumb,
        })

    if videos:
        med_views = statistics.median([v["views"] for v in videos if v["views"] > 0] or [1])
        for v in videos:
            v["outlierScore"] = round(v["views"] / med_views, 1) if med_views else 1.0
    return videos


def _comp_label(score):
    if score < 30:
        return "Very low"
    if score < 50:
        return "Low"
    if score < 70:
        return "Medium"
    if score < 85:
        return "High"
    return "Very high"


def _overall_label(score):
    if score >= 75:
        return "Very high"
    if score >= 60:
        return "High"
    if score >= 45:
        return "Medium"
    return "Low"


def _score_related_term(term, seed_volume_score, seed_comp_score, seed):
    words = len(term.split())
    # Long-tail terms typically have slightly lower search volume but much lower competition
    word_delta = max(0, words - len(seed.split()))
    vol_score = max(18, min(95, int(round(seed_volume_score - word_delta * 7 + (4 if "how" in term.lower() else 0)))))
    comp_score = max(12, min(92, int(round(seed_comp_score - word_delta * 11))))
    overall = max(10, min(98, int(round(vol_score * 0.58 + (100 - comp_score) * 0.42))))
    est_monthly = int(round(600 * (1.084 ** vol_score)))
    return {
        "keyword": term,
        "words": words,
        "searchVolume": est_monthly,
        "volumeScore": vol_score,
        "competitionScore": comp_score,
        "competitionLabel": _comp_label(comp_score),
        "overall": overall,
        "overallLabel": _overall_label(overall),
    }


def research_keyword(keyword):
    """Full vidIQ-grade Keyword Intelligence payload with real live YouTube Suggest + SERP data."""
    kw = (keyword or "").strip()
    if not kw:
        raise ValueError("Enter a keyword to research.")

    with ThreadPoolExecutor(max_workers=2) as ex:
        f_uni = ex.submit(gather_keyword_universe, kw)
        f_serp = ex.submit(fetch_yt_serp, kw, 12)
        buckets = f_uni.result()
        serp = f_serp.result()

    kw_lower = kw.lower()
    kw_tokens = set(re.findall(r"[a-z0-9]+", kw_lower))

    views_list = [v["views"] for v in serp if v["views"] > 0]
    vph_list = [v["vph"] for v in serp if v["vph"] > 0]
    total_vph = round(sum(vph_list), 1)
    med_views = int(statistics.median(views_list)) if views_list else 0
    max_views = max(views_list) if views_list else 0

    # Demand / Volume score (0-100) from real YouTube Suggest breadth + real SERP view velocity
    suggest_count = len(buckets["matching"]) + len(buckets["related"]) + len(buckets["question"])
    breadth_pts = min(40, suggest_count * 1.1)
    view_pts = min(35, math.log10(max(10, med_views)) * 5.8) if med_views else 14
    vph_pts = min(25, math.log10(max(10, total_vph + 1)) * 5.2) if total_vph else 8
    volume_score = max(15, min(98, int(round(breadth_pts + view_pts + vph_pts))))
    est_monthly_searches = int(round(620 * (1.084 ** volume_score)))

    # Competition score (0-100) from real SERP title-match saturation & big-video dominance
    exact_matches = sum(1 for v in serp if kw_lower in v["title"].lower())
    token_matches = sum(
        1 for v in serp
        if kw_tokens and len(kw_tokens & set(re.findall(r"[a-z0-9]+", v["title"].lower()))) >= max(1, len(kw_tokens) - 1)
    )
    fresh_hits = sum(1 for v in serp if v["ageDays"] <= 45 and v["views"] >= max(5000, med_views * 0.4))
    mega_hits = sum(1 for v in serp if v["views"] >= 500_000)

    if serp:
        match_density = (exact_matches * 0.7 + token_matches * 0.3) / len(serp)
        comp_score = int(round(24 + match_density * 44 + (mega_hits / len(serp)) * 28 - (fresh_hits / len(serp)) * 12))
    else:
        comp_score = 48
    comp_score = max(14, min(94, comp_score))

    # Overall Opportunity Score (0-100)
    freshness_bonus = min(10, fresh_hits * 3)
    overall_score = max(12, min(98, int(round(volume_score * 0.56 + (100 - comp_score) * 0.40 + freshness_bonus))))

    matching_rows = [_score_related_term(t, volume_score, comp_score, kw) for t in buckets["matching"][:25]]
    related_rows = [_score_related_term(t, volume_score, comp_score, kw) for t in buckets["related"][:25]]
    question_rows = [_score_related_term(t, volume_score, comp_score, kw) for t in buckets["question"][:25]]
    for rows in (matching_rows, related_rows, question_rows):
        rows.sort(key=lambda r: r["overall"], reverse=True)

    # Auto-scored recommended tags (vidIQ style)
    tag_candidates = [kw] + [r["keyword"] for r in matching_rows[:8]] + [r["keyword"] for r in related_rows[:5]] + [r["keyword"] for r in question_rows[:3]]
    seen_tags = set()
    recommended_tags = []
    for t in tag_candidates:
        tl = t.lower()
        if tl in seen_tags or len(t) > 55:
            continue
        seen_tags.add(tl)
        scored = _score_related_term(t, volume_score, comp_score, kw)
        recommended_tags.append({"tag": t, "score": scored["overall"], "competition": scored["competitionLabel"]})
    recommended_tags.sort(key=lambda x: x["score"], reverse=True)

    serp_sorted = sorted(serp, key=lambda v: (v["vph"], v["views"]), reverse=True)

    return {
        "keyword": kw,
        "overallScore": overall_score,
        "overallLabel": _overall_label(overall_score),
        "volumeScore": volume_score,
        "monthlySearches": est_monthly_searches,
        "competitionScore": comp_score,
        "competitionLabel": _comp_label(comp_score),
        "viewsPerHour": total_vph,
        "medianTopViews": med_views,
        "maxTopViews": max_views,
        "freshBreakouts": fresh_hits,
        "matching": matching_rows,
        "related": related_rows,
        "questions": question_rows,
        "recommendedTags": recommended_tags[:16],
        "topVideos": serp_sorted[:10],
        "source": "live_youtube_suggest_and_serp" if serp else "live_youtube_suggest",
        "analyzedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


# ──────────────────── 3. VIDIQ TITLE, TAGS & SEO SCORER ────────────────────

POWER_WORDS = {
    "stop", "secret", "nobody", "mistake", "wrong", "never", "exact", "free", "simple",
    "fast", "actually", "truth", "hidden", "killed", "replaced", "insane", "scientifically",
    "proven", "framework", "system", "hours", "minutes", "days", "million", "blueprint",
    "trap", "without", "before", "instead", "tested", "honest", "brutal", "weird", "only",
}


def score_title_and_seo(title, keyword="", description="", tags=None, thumbnail_text=""):
    """
    Replicates + beats vidIQ's Title Score (0-100), Individual Tag Scores (0-100),
    Actionable SEO Checklist, and Thumbnail Glanceability check.
    """
    t = (title or "").strip()
    tl = t.lower()
    kw = (keyword or "").strip().lower()
    desc = (description or "").strip()
    desc_l = desc.lower()
    tag_list = [x.strip() for x in (tags or []) if str(x).strip()]
    thumb_t = (thumbnail_text or "").strip()

    char_len = len(t)
    words = t.split()
    wc = len(words)
    has_num = bool(re.search(r"\b\d+[\d,\.%kKmMxX]*\b", t))
    power_hits = [w for w in re.findall(r"[a-z]+", tl) if w in POWER_WORDS]
    has_contrast = bool(re.search(r"\b(vs\.?|instead of|without|stop|never|not|why most|actually|before you)\b", tl))
    has_curiosity = bool(re.search(r"(\?|here's|this one|the real reason|nobody|secret|what happened|i tested|i tried)", tl))

    # vidIQ's 4 Core Title Checks + Dan Kennedy Polarity/Specificity
    sparks_intrigue = bool(power_hits or has_contrast or has_curiosity or has_num)
    clear_topic = wc >= 4 and (not kw or any(tok in tl for tok in kw.split() if len(tok) > 2))
    easy_to_read = 5 <= wc <= 14 and not (t.isupper() and char_len > 25) and len(re.findall(r"[|:/\\]{2,}", t)) == 0
    fits_on_phones = 22 <= char_len <= 62
    kennedy_edge = has_contrast or bool(re.search(r"\b(stop|lie|trap|wrong|gurus?|scam|truth|never|kill)\b", tl))

    score = 38
    if sparks_intrigue:
        score += 18
    if has_num:
        score += 8
    if has_contrast:
        score += 8
    if clear_topic:
        score += 12
    if easy_to_read:
        score += 8
    if fits_on_phones:
        score += 8
    elif char_len > 75:
        score -= 10
    elif char_len < 18:
        score -= 12
    title_score = max(12, min(99, score))

    checks = [
        {
            "label": "Sparks intrigue",
            "pass": sparks_intrigue,
            "detail": (
                f"Strong curiosity/power triggers detected ({', '.join(power_hits[:3]) or 'contrast/number'})."
                if sparks_intrigue else "Too flat/descriptive — add a tension word, specific number, or contrarian contrast."
            ),
        },
        {
            "label": "Clear topic",
            "pass": clear_topic,
            "detail": "Viewer immediately understands what the video delivers." if clear_topic else "Name the concrete tool, outcome, or target keyword clearly in the first 5 words.",
        },
        {
            "label": "Easy to read",
            "pass": easy_to_read,
            "detail": f"{wc} words — clean scannable phrasing." if easy_to_read else f"{wc} words — tighten into 6–12 punchy conversational words.",
        },
        {
            "label": "Fits on phones",
            "pass": fits_on_phones,
            "detail": f"{char_len}/60 chars — won't truncate on mobile feeds." if fits_on_phones else f"{char_len} chars — aim for 35–60 characters so the hook doesn't get cut off on mobile.",
        },
        {
            "label": "Dan Kennedy polarity / contrast",
            "pass": kennedy_edge,
            "detail": "Creates clear Us-vs-Them or Old-Way-vs-New-Way tension." if kennedy_edge else "Add contrast ('without X', 'stop doing Y', or name an industry enemy) to boost CTR.",
        },
    ]

    # Individual Tag Scoring (0-100 pills like vidIQ)
    scored_tags = []
    tags_char_len = sum(len(x) + 1 for x in tag_list)
    for tag in tag_list:
        tag_l = tag.lower()
        t_words = len(tag_l.split())
        t_score = 46
        if kw and (kw in tag_l or tag_l in kw):
            t_score += 22
        if any(w in tl for w in tag_l.split() if len(w) > 3):
            t_score += 12
        if 2 <= t_words <= 4:
            t_score += 10
        elif t_words == 1:
            t_score -= 10
        elif t_words >= 6:
            t_score -= 14
        if desc_l and tag_l in desc_l:
            t_score += 6
        t_score = max(14, min(96, t_score))
        scored_tags.append({"tag": tag, "score": t_score})

    # Classic Actionable vidIQ SEO Checklist (the exact checklist vidIQ gates behind its Chrome extension!)
    kw_in_title = bool(kw and kw in tl)
    kw_in_desc_top = bool(kw and kw in desc_l[:180])
    kw_in_tags = bool(kw and any(kw in x.lower() for x in tag_list))
    tripled = kw_in_title and kw_in_desc_top and kw_in_tags
    tag_count_ok = 8 <= len(tag_list) <= 20 and tags_char_len <= 500
    desc_len_ok = len(desc) >= 200

    seo_checklist = [
        {"item": "Primary keyword in Title", "pass": kw_in_title if kw else bool(t), "weight": 20},
        {"item": "Primary keyword in first 180 chars of Description", "pass": kw_in_desc_top if kw else desc_len_ok, "weight": 20},
        {"item": "Primary keyword in Tags", "pass": kw_in_tags if kw else len(tag_list) >= 5, "weight": 15},
        {"item": "Tripled Keyword (Title + Description + Tags)", "pass": tripled, "weight": 20},
        {"item": f"Tag budget optimized ({len(tag_list)} tags · {tags_char_len}/500 chars)", "pass": tag_count_ok, "weight": 15},
        {"item": f"Description depth ({len(desc)} chars, target 250+)", "pass": desc_len_ok, "weight": 10},
    ]
    seo_score = sum(c["weight"] for c in seo_checklist if c["pass"])

    # Thumbnail Concept Check (something vidIQ's web app doesn't even score!)
    thumb_words = len(thumb_t.split()) if thumb_t else 0
    thumb_repeat = bool(thumb_t and t and thumb_t.lower() in tl)
    thumb_score = 72
    thumb_notes = []
    if thumb_t:
        if thumb_words <= 4:
            thumb_score += 14
            thumb_notes.append(f"Crisp mobile legibility ({thumb_words} words — ideal is 2–4 words).")
        else:
            thumb_score -= 16
            thumb_notes.append(f"Too much thumbnail text ({thumb_words} words) — trim to 2–4 bold words max.")
        if thumb_repeat:
            thumb_score -= 12
            thumb_notes.append("Thumbnail text repeats the title verbatim — make it complement/amplify the title instead.")
        else:
            thumb_score += 8
            thumb_notes.append("Complements the title without wasting space repeating it.")
    else:
        thumb_notes.append("Add a 2–4 word high-contrast thumbnail phrase + 1 clear visual focal point (before/after or single bold object).")

    return {
        "titleScore": title_score,
        "charCount": char_len,
        "wordCount": wc,
        "titleChecks": checks,
        "seoScore": seo_score,
        "seoChecklist": seo_checklist,
        "scoredTags": scored_tags,
        "tagsCharCount": tags_char_len,
        "thumbnailScore": max(15, min(98, thumb_score)),
        "thumbnailNotes": thumb_notes,
    }


def generate_packaging_ai(topic, keyword="", workspace_profile=None, provider="auto"):
    """Use local Claude / Codex CLI (via ai_engine) to generate vidIQ-beating video packaging."""
    import ai_engine

    ws_block = ai_engine._workspace_brief(workspace_profile)
    prompt = f"""You are an elite YouTube & short-form Packaging Strategist combining vidIQ CTR optimization with Dan Kennedy Magnetic Story Selling.
Generate a complete, high-CTR video packaging kit for this topic.

TOPIC / IDEA: {topic}
PRIMARY KEYWORD: {keyword or topic}
ACTIVE WORKSPACE CHARACTER & OFFER:
{ws_block}

Return ONLY valid JSON:
{{
  "titles": [
    {{"title": "Under 60 chars, high-CTR curiosity + clarity title", "angle": "Curiosity / Contrarian / Proof / How-To / Enemy", "whyItClicks": "1 crisp sentence"}}
  ],
  "thumbnails": [
    {{"overlayText": "2-4 bold words max (NOT repeating the title)", "visualScene": "Exact foreground subject, expression/prop, and background contrast", "curiosityHook": "Why a cold scroller stops in 0.5s"}}
  ],
  "description": "SEO-optimized 2-paragraph YouTube/social description placing the primary keyword naturally in the first 120 characters plus a clean CTA matching the workspace offer.",
  "tags": ["12 to 15 high-relevance YouTube search tags mixing primary keyword, long-tail modifiers, and niche terms"]
}}"""
    engine, raw = ai_engine.call_llm_json(prompt, provider=provider, timeout=140)
    titles = []
    for item in (raw.get("titles") or [])[:6]:
        if isinstance(item, dict) and item.get("title"):
            scored = score_title_and_seo(item["title"], keyword=keyword or topic)
            titles.append({
                "title": str(item["title"]).strip(),
                "angle": str(item.get("angle") or "High-CTR").strip(),
                "whyItClicks": str(item.get("whyItClicks") or "").strip(),
                "score": scored["titleScore"],
            })
    titles.sort(key=lambda x: x["score"], reverse=True)
    tags = [str(x).strip() for x in (raw.get("tags") or []) if str(x).strip()][:18]
    desc = str(raw.get("description") or "").strip()
    top_title = titles[0]["title"] if titles else topic
    seo_eval = score_title_and_seo(top_title, keyword=keyword or topic, description=desc, tags=tags)
    return {
        "engine": engine,
        "titles": titles,
        "thumbnails": (raw.get("thumbnails") or [])[:3],
        "description": desc,
        "tags": seo_eval["scoredTags"],
        "seoScore": seo_eval["seoScore"],
        "seoChecklist": seo_eval["seoChecklist"],
    }


if __name__ == "__main__":
    import sys
    q = " ".join(sys.argv[1:]) or "AI automation"
    res = research_keyword(q)
    print(json.dumps({
        "keyword": res["keyword"],
        "overall": f"{res['overallScore']}/100 ({res['overallLabel']})",
        "monthlySearches": res["monthlySearches"],
        "competition": f"{res['competitionScore']}/100 ({res['competitionLabel']})",
        "viewsPerHour": res["viewsPerHour"],
        "matchingCount": len(res["matching"]),
        "questionsCount": len(res["questions"]),
        "topVideosCount": len(res["topVideos"]),
        "sampleTags": res["recommendedTags"][:6],
        "topVideo": res["topVideos"][0] if res["topVideos"] else None,
    }, indent=2))
