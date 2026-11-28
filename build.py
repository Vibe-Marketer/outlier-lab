#!/usr/bin/env python3
"""
AI Simple — Outlier Lab Studio renderer.

Generates a self-contained static HTML application combining:
  - AI Simple brand design system (Sora + Manrope + Space Mono, #FFC71D yellow,
    #F5F4EF warm paper, #1F1F1F charcoal, lavender/sage/cream cards)
  - Full per-video breakdown studio (6 tabs: Transcript w/
    Beat-by-Beat timestamps, Idea Analysis, Hook Formula, Storytelling Format,
    Visual Layout, and Magnetic Story Audit)
  - Ideas Inbox, Viral Hook Vault + Pre-Flight Checker, Collections Taxonomy,
    Projects, Content Strategy Audit + Success Formula, 4-Step Script Builder,
    Brand Brain, Founder Persona & Offer Studio, My Socials, and Zero-Friction Setup.
"""
import json
import re
import statistics
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from html import escape
from pathlib import Path
from catalog import select_creators, scopes_for

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
THUMBS = ROOT / "thumbs"
OUT = ROOT / "index.html"

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"

DEFAULT_WORKSPACES = [
    {
        "id": "aisimple",
        "name": "AI Simple",
        "initials": "AS",
        "accent": "#ffc71d",
        "accentInk": "#1f1f1f",
        "tagline": "AI workflows, automation & high-leverage founder systems",
        "scopes": ["ai", "ai-dtc", "marketing-sales", "notion-swipes"],
        "socials": [
            {"platform": "instagram", "handle": "@aisimple.co", "followers": "—", "medianViews": "—", "connected": False},
            {"platform": "youtube", "handle": "@aisimple", "followers": "—", "medianViews": "—", "connected": False},
            {"platform": "tiktok", "handle": "@aisimple.co", "followers": "—", "medianViews": "—", "connected": False},
            {"platform": "facebook", "handle": "aisimple", "followers": "—", "medianViews": "—", "connected": False},
        ],
        "offer": {
            "whatYouSell": "The SIMPLE Method — AI workflow audits, team implementation, and done-for-you AI operating systems",
            "whoYouSellTo": "Founders and operators ($500K–$20M+) drowning in repetitive work who want real leverage without hype",
            "coreTransformation": "Turn scattered manual work and missed opportunities into one calm, measurable AI system your team actually uses",
            "ctaMechanism": "Comment 'SIMPLE' or take the free AI Bottleneck Assessment at aisimple.co",
        },
        "character": {
            "archetype": "The Stern but Loving Parent",
            "superheroIdentity": "The Systems Architect (Iron Operator)",
            "mightyTheme": "Build a better business and get your life back by fixing the real bottleneck before adding another AI tool.",
            "standFor": "Simplicity over complexity, diagnosing before prescribing, real workflows over prompt hype, human-in-the-loop leverage, measurable ROI",
            "standAgainst": "AI grifters selling shiny prompt packs, tool-hoarding without a process, agency bloat, fake hustle theater, over-explaining instead of simplifying",
            "sevenElements": {
                "origin": "Spent years inside high-velocity marketing, funnels, and agency ops watching smart founders burn out on messy processes before codifying the SIMPLE Method.",
                "parables": "The 2-Hour Launch Rescue (fixing an 8-figure founder's broken prompt stack right before launch); The $100K Bottleneck Trap (why adding AI to a broken workflow multiplies chaos).",
                "miracles": "Helped scale LeadGenJay $39K → $300K+/mo; 49 of 50 customers retained via Refund Save Funnel; built autonomous local Mac agent fleets.",
                "insiderLanguage": "The SIMPLE Method, HINGES, Leveraged Exhaust, Diagnosis Before Prescription, Bottleneck-First AI, Reps Shipped",
                "dogma": "1) Never automate chaos. 2) Diagnose before you prescribe. 3) Simplify, don't explain. 4) One real workflow beats 50 shiny tools. 5) Reps shipped is the only compounding metric.",
                "enemies": "Shiny-object AI gurus, prompt-pack sellers, bloated SaaS stacks, 'make it engaging' lazy prompting, complexity theater",
                "flaws": "ADHD operator who used to chase every new tool and overbuild before learning that restraint and simple systems win every time.",
            },
            "jamesBondTest": [
                "Founder of AI Simple & creator of the SIMPLE Method",
                "ADHD systems builder who turns messy founder exhaust into calm leverage",
                "Diagnoses the single bottleneck before touching an AI tool",
                "Fixes broken prompts & workflows live (2-hour launch rescues)",
                "Writes HINGES on Substack — small changes, useful leverage",
                "Anti-hype, no-BS operator who simplifies instead of over-explaining",
                "Runs local-first AI agents & Life OS across multiple businesses",
            ],
            "profits": {
                "pain": "Bought 12 AI subscriptions, still doing everything manually, team won't adopt tools, overwhelmed by daily AI news",
                "results": "10+ hours/week back, consistent lead follow-up, repeatable content & ops systems, $39K→$300K+ growth proof",
                "obstacles": "No time to learn complex code, burned by hype courses, don't know which workflow to fix first",
                "fear": "Falling behind competitors using AI, wasting money on another shelfware tool or agency",
                "identity": "Pragmatic founder, builder, operator who hates fluff and wants systems that work on Monday morning",
                "triggers": "Missed leads, key team member quitting, hitting a revenue ceiling where working harder stops working",
                "dreams": "A calm, high-margin business that runs smoothly without needing the founder in every single conversation",
            },
            "writingStyle": "Direct, punchy, short sentences (<11 words average). Concrete numbers and real named tools. Open with a sharp pattern interrupt or contrarian diagnosis, simplify one mechanism cleanly, zero corporate buzzwords.",
        },
    },
    {
        "id": "clickable-impact",
        "name": "Clickable Impact",
        "initials": "CI",
        "accent": "#1f1f1f",
        "accentInk": "#ffc71d",
        "tagline": "DTC performance creative, paid social & ecommerce scale",
        "scopes": ["dtc-agencies", "dtc-ecommerce", "ai-dtc"],
        "socials": [
            {"platform": "instagram", "handle": "@clickableimpact", "followers": "—", "medianViews": "—", "connected": False},
            {"platform": "youtube", "handle": "@clickableimpact", "followers": "—", "medianViews": "—", "connected": False},
            {"platform": "tiktok", "handle": "@clickableimpact", "followers": "—", "medianViews": "—", "connected": False},
            {"platform": "facebook", "handle": "clickableimpact", "followers": "—", "medianViews": "—", "connected": False},
        ],
        "offer": {
            "whatYouSell": "High-converting paid social creative engines, ad testing frameworks, and DTC acquisition systems",
            "whoYouSellTo": "7- and 8-figure DTC ecommerce brands and performance agencies scaling Meta & TikTok spend",
            "coreTransformation": "Turn unpredictable ad fatigue into a repeatable creative-testing machine that lowers CAC and scales winning angles",
            "ctaMechanism": "Comment 'CREATIVE' for the breakdown doc or book a Paid Social Creative Audit",
        },
        "character": {
            "archetype": "The Patient Teacher / Philosopher",
            "superheroIdentity": "The Creative Strategist",
            "mightyTheme": "Creative is the targeting — win the first 3 seconds with real buyer psychology and the ad account prints.",
            "standFor": "Data-backed creative testing, thumbstop-to-hold mechanics, customer language mining, contribution margin over vanity ROAS",
            "standAgainst": "Pretty brand ads that don't convert, guessing hooks in a vacuum, media-buyer button pushing, ignoring retention & LTV",
            "sevenElements": {
                "origin": "Grew out of managing millions in direct-response ad spend where ugly, specific, buyer-voiced creative consistently crushed $50K studio shoots.",
                "parables": "The $50K Studio Flop vs. The 30-Second iPhone Winner; The First-3-Seconds Tax (why 80% of ad budgets die before sentence two).",
                "miracles": "Doubled thumbstop rates and scaled cold DTC accounts past $100K/mo spend using modular hook testing.",
                "insiderLanguage": "Hook Matrix, Creative Velocity, Thumbstop Tax, Buyer-Voice Mining, Profitable Scale Architecture",
                "dogma": "1) Creative is the new targeting. 2) Test hooks before rewriting whole scripts. 3) Mine reviews and sales calls for verbatim copy. 4) Measure contribution margin, not vanity views.",
                "enemies": "Vanity brand agencies, media-buying hacks, recycled generic UGC scripts, guessing without outlier data",
                "flaws": "Used to over-obsess over ad-account bidding structures before realizing 80% of scale lives in the first 3 seconds of the creative.",
            },
            "jamesBondTest": [
                "Performance creative team for 7–8 figure DTC brands",
                "Obsessed with the first 3 seconds (thumbstop & hold rate)",
                "Turns real customer reviews into winning video scripts",
                "Tests modular hook variations systematically every week",
                "Measures real profit & contribution margin, not vanity ROAS",
                "Blends AI speed with direct-response human psychology",
                "Calm, executive, numbers-first creative direction",
            ],
            "profits": {
                "pain": "Ad fatigue every 10 days, rising CPMs, UGC creators delivering flat scripts that burn budget",
                "results": "Consistent winning angles every sprint, 35%+ thumbstop rates, profitable cold acquisition scale",
                "obstacles": "Creative bottlenecks, slow turnarounds, agencies that don't understand direct-response economics",
                "fear": "Scaling spend and watching MER collapse overnight",
                "identity": "Data-driven DTC founder or CMO who treats creative as a measurable growth lever",
                "triggers": "Q4/peak season approaching, winning ad dying, plateauing at $50K–$300K/mo",
                "dreams": "A predictable weekly creative pipeline that unlocks profitable scale on command",
            },
            "writingStyle": "Crisp, executive, evidence-led. Lead with the ad metric or visual contrast, break down the exact 3-second hook mechanic, end with a concrete test to run this week.",
        },
    },
]

CREATIVE_COLLECTIONS = [
    {
        "group": "Visual Hooks",
        "tone": "butter",
        "description": "What happens visually in seconds 0–3 to arrest the scroll before the viewer even processes your words.",
        "items": [
            {"name": "Move In Frame", "sub": "Subject Motion", "desc": "Walk into frame or lean toward lens right as line 1 lands to create kinetic momentum."},
            {"name": "Write On Screen", "sub": "Subject Motion", "desc": "Write a bold claim or number on a whiteboard, glass, or tablet while delivering the hook."},
            {"name": "Holding Prop", "sub": "Subject Motion", "desc": "Hold a concrete physical object (phone, receipt, book, dollar bill) that anchors the hook."},
            {"name": "A vs B Split", "sub": "Graphic / Text Overlay", "desc": "Split the screen immediately comparing the broken old way vs. the winning new way."},
            {"name": "Image Overlay Motion", "sub": "Graphic / Text Overlay", "desc": "Pop a screenshot, chart, or tweet onto screen in sync with the first concrete number."},
            {"name": "Beat Match Visual Switch", "sub": "Pattern Interrupt", "desc": "Cut camera angle, zoom, or B-roll on the stressed word of sentence 1."},
            {"name": "Yap Cold Open", "sub": "Subject Motion", "desc": "Mid-thought, zero throat-clearing direct-to-camera opener as if texting one friend."},
            {"name": "High Motion Base B-Roll", "sub": "Visual Selection", "desc": "Fast screen recording or real-world action underneath tight voiceover pacing."},
        ],
    },
    {
        "group": "Storytelling Formats",
        "tone": "lavender",
        "description": "Proven narrative skeletons that hold retention from second 3 through the final payoff.",
        "items": [
            {"name": "Breakdown Explainer", "sub": "Authority & Teaching", "desc": "Dissect a real example, system, or phenomenon step-by-step with proof."},
            {"name": "Common Trap / Mistake", "sub": "Diagnosis", "desc": "Call out a recognizable mistake viewers know they make, reveal why it fails, give the fix."},
            {"name": "A vs B Comparison", "sub": "Contrast", "desc": "Contrast the amateur approach against the pro mechanism to create an instant curiosity gap."},
            {"name": "Listicle", "sub": "High-Value Compression", "desc": "Pack 3–7 specific, concrete points with a named time cap ('5 prompts in 45 seconds')."},
            {"name": "Case Study", "sub": "Proof-Led", "desc": "Walk through a specific before → mechanism → after transformation with exact numbers."},
            {"name": "Personal Learning / Epiphany", "sub": "Character & Parable", "desc": "Real incident + hard lesson + perspective shift (Parable story format)."},
            {"name": "Problem → Solution", "sub": "Direct Utility", "desc": "Name the live pain in line 1, deliver the first useful step by second 8."},
            {"name": "Yap / Hot Take", "sub": "Polarization", "desc": "Unfiltered contrarian stance against a named industry enemy that forces comments."},
        ],
    },
    {
        "group": "Editing Styles",
        "tone": "sage",
        "description": "Production layouts and visual rhythm patterns that match your recording environment.",
        "items": [
            {"name": "Office Room Yap", "sub": "Studio / Set", "desc": "Clean desk/office frame with tight jump cuts and subtle punch-in zooms on key beats."},
            {"name": "Screen Demo + Face Cam", "sub": "Full Screen / Hybrid", "desc": "Live tool or workflow walkthrough with circular/split talking-head overlay."},
            {"name": "Notes / Article Greenscreen", "sub": "Greenscreen", "desc": "Creator keyed over a real tweet, headline, chart, or Notion doc pointing to specifics."},
            {"name": "Whiteboard Breakdown", "sub": "Studio / Set", "desc": "Hand-drawn 3-box diagram or equation built live as the explanation unfolds."},
            {"name": "Car Yap / Walk-and-Talk", "sub": "In-World", "desc": "Raw, unpolished candid energy that disarms 'this is an ad' resistance immediately."},
            {"name": "Faceless Visual Explainer", "sub": "Faceless", "desc": "Kinetic text, motion graphics, and screen captures narrated with zero dead air."},
        ],
    },
    {
        "group": "Signature Series",
        "tone": "cream",
        "description": "Repeatable show concepts that turn one-off viewers into binge-watching subscribers.",
        "items": [
            {"name": "Case Study Teardown Series", "sub": "Recurring Authority", "desc": "Break down one real business, funnel, or ad account every week with receipts."},
            {"name": "Numbered Countdown / Challenge", "sub": "Episodic Stakes", "desc": "'Day X of building Y' anchored to one concrete, verifiable outcome."},
            {"name": "Live Roast / Free Audit", "sub": "Demonstrated Care", "desc": "Take real audience submissions and fix their hook, offer, or workflow live."},
            {"name": "Docuseries / Build in Public", "sub": "Character Evolution", "desc": "Follow an ongoing mission with real wins, flaws, and Regis-style context moments."},
        ],
    },
]


def _load_creators():
    import sys
    config_path = ROOT / "config.json"
    if not config_path.exists():
        print(
            "ERROR: config.json not found.\n"
            "Run `python3 configure.py` first to set up your creator list.",
            file=sys.stderr,
        )
        sys.exit(1)
    try:
        data = json.loads(config_path.read_text())
    except json.JSONDecodeError as e:
        print(f"ERROR: config.json is malformed: {e}", file=sys.stderr)
        sys.exit(1)
    return [c["handle"] for c in select_creators(data, tracked_only=False)]


CREATORS = _load_creators()
CONFIG = json.loads((ROOT / "config.json").read_text())
SCOPES = scopes_for(CONFIG)
CREATOR_CONFIG = {c["handle"]: c for c in select_creators(CONFIG, tracked_only=False)}
COVERAGE_PATH = DATA / "coverage.json"
COVERAGE = json.loads(COVERAGE_PATH.read_text()) if COVERAGE_PATH.exists() else {}


def load(path):
    with open(path) as f:
        return json.load(f)


def fetch(url, dest):
    if dest.exists() and dest.stat().st_size > 0:
        return True
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=15) as r:
            dest.write_bytes(r.read())
        return True
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
        print(f"  ! fetch failed for {url[:60]}: {e}")
        return False


def first_sentence(text, max_len=200):
    if not text:
        return ""
    text = text.strip()
    m = re.split(r"(?<=[\.\!\?])\s+", text, maxsplit=1)
    out = m[0].strip() if m else text
    return out[:max_len] + ("…" if len(out) > max_len else "")


def hook_of(transcript, caption):
    if transcript:
        return first_sentence(transcript, 200)
    if caption:
        return first_sentence(caption, 180)
    return ""


def fmt_num(n):
    if n is None:
        return "—"
    n = int(n)
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 10_000:
        return f"{n/1_000:.0f}K"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


def fmt_dur(seconds):
    if not seconds:
        return "—"
    s = int(round(seconds))
    m, s = divmod(s, 60)
    return f"{m}:{s:02d}" if m else f"{s}s"


def fmt_ts(sec):
    sec = max(0, int(round(sec)))
    m, s = divmod(sec, 60)
    return f"{m}:{s:02d}"


def outlier_band(ratio):
    if ratio is None:
        return ("normal", "Normal", "#e8e6dd")
    if ratio >= 15:
        return ("breakout", "Breakout", "#d4276b")
    if ratio >= 5:
        return ("strong", "Replicable", "#ffc71d")
    if ratio >= 2:
        return ("good", "Working", "#2e7d52")
    return ("normal", "Normal", "#e8e6dd")


# ───────────── VIDEO BREAKDOWN & MAGNETIC STORY ENGINE ─────────────

def _classify_topic(text_lower):
    rules = [
        ("AI Agents & Automation", r"\b(agent|agents|workflow|automat|claude|openclaw|n8n|mcp|cursor|codex|zapier|bot)\b"),
        ("Short-Form Hooks & Content", r"\b(hook|viral|reel|reels|algorithm|retention|views|script|storytelling|attention|caption|scroll)\b"),
        ("Paid Ads & Creative", r"\b(meta ads|facebook ads|creative|roas|cpm|cac|thumbstop|ugc|ad account|media buy|static ad)\b"),
        ("DTC Scale & Ecommerce", r"\b(shopify|dtc|ecommerce|e-commerce|brand|aov|ltv|retention|email flow|klaviyo|product)\b"),
        ("Offer & Sales Psychology", r"\b(offer|sales|close|closing|pricing|client|leads|funnel|copywriting|headline|objection|webinar|convert)\b"),
        ("AI Tools & Demos", r"\b(ai|chatgpt|openai|gemini|midjourney|sora|prompt|llm|model|robot|deepseek|kimi)\b"),
        ("Founder Systems & Mindset", r"\b(founder|ceo|business|team|hire|delegate|habit|focus|productivity|million|revenue|scale)\b"),
    ]
    best, best_hits = "Growth & Strategy", 0
    for label, pat in rules:
        hits = len(re.findall(pat, text_lower))
        if hits > best_hits:
            best, best_hits = label, hits
    return best


def _classify_hook(hook_text):
    h = (hook_text or "").strip()
    hl = h.lower()
    if re.search(r"^(stop|don't|never|quit|why most|the biggest mistake|mistake)", hl) or "wrong" in hl:
        return ("Trap Mistake", "Stop [common action / mistake] — here's why it [hidden cost] and what to do instead.")
    if re.search(r"\b(vs\.?|versus|instead of|difference between|amateur|rich vs|poor vs)\b", hl):
        return ("Comparison", "Why [Winning Approach] outperforms [Common Approach] by [specific gap].")
    if re.search(r"^(how to|here's how|here is how|the exact way|step by step)", hl):
        return ("Tutorial", "Here's how to [specific outcome] in [short timeframe] without [common friction].")
    if re.search(r"\b(secret|nobody talks about|hidden|quietly|just dropped|just released|just integrated|wild|insane)\b", hl):
        return ("Secret Reveal Breakdown", "[Specific Company / Tool] just [concrete shift] — and almost nobody realizes [implication].")
    if re.search(r"\b(\$|million|billion|k\b|%\b|\d+x|\d+ years|\d+ days|\d+ clients)\b", hl):
        return ("Case Study", "How [Specific Subject] achieved [concrete number/result] using [single mechanism].")
    if re.search(r"^(i |my |when i |last week|yesterday|3 years ago|after )", hl):
        return ("Personal Experience", "I [specific personal action/test] for [timeframe] — here's the [surprising result].")
    if "?" in h or re.search(r"^(why |what |how |did you |have you |are you |can )", hl):
        return ("Question", "Why does [specific observable phenomenon] happen when [common assumption]?")
    if re.search(r"\b(3 |5 |7 |top \d|\d+ ways|\d+ things|\d+ rules|\d+ tips)\b", hl):
        return ("List", "[Number] [specific craft items] that [concrete measurable payoff].")
    if re.search(r"\b(problem|struggling|stuck|killing|losing|broken|failing)\b", hl):
        return ("Problem", "The real reason your [specific asset] isn't [desired result] is [diagnosable culprit].")
    return ("Authority", "If you want [specific outcome], stop focusing on [surface tactic] and fix [core lever].")


def _extract_madlib(hook_text, fallback_formula):
    h = (hook_text or "").strip()
    if not h or len(h) < 12:
        return fallback_formula
    out = re.sub(r"\$\d[\d,\.]*[kKmMbB]?", "[Specific Dollar Figure]", h)
    out = re.sub(r"\b\d+(?:\.\d+)?%", "[Specific %]", out)
    out = re.sub(r"\b\d+\s+(days?|hours?|minutes?|seconds?|weeks?|months?|years?)\b", "[Timeframe]", out, flags=re.I)
    out = re.sub(r"\b(ChatGPT|Claude|Gemini|OpenAI|Meta|Instagram|TikTok|Shopify|Elon|Google|Apple|Microsoft|Anthropic)\b", "[Named Platform/Brand]", out, flags=re.I)
    if out == h:
        return fallback_formula
    return out[:180]


def _classify_format(text_lower, hook_cat, duration):
    if hook_cat == "Trap Mistake" or re.search(r"\b(mistake|trap|stop doing|doing it wrong)\b", text_lower):
        return ("Common Trap Mistake", "Calls out a recognizable error viewers already make, proves why it hurts them, and installs the corrected frame.")
    if hook_cat == "Comparison" or re.search(r"\b(vs\.?|versus|instead of|compare|difference between)\b", text_lower):
        return ("A Vs B Comparison", "Contrasts the default/amateur approach against a sharper mechanism so the viewer sees the gap immediately.")
    if hook_cat == "List" or len(re.findall(r"\b(first|second|third|number one|number two|step 1|step 2|1\.|2\.|3\.)\b", text_lower)) >= 2:
        return ("Listicle", "Compresses multiple concrete, high-signal points into rapid beats with minimal transition fluff.")
    if hook_cat == "Case Study" or re.search(r"\b(case study|from \$|went from|grew to|scaled to|revenue)\b", text_lower):
        return ("Case Study", "Anchors the teaching inside a real verifiable transformation with before-and-after receipts.")
    if hook_cat == "Personal Experience" or re.search(r"\b(story|happened to me|i learned|i realized|i failed|years ago)\b", text_lower):
        return ("Personal Learning Epiphany", "Turns a lived incident into a portable principle (Parable story structure).")
    if re.search(r"\b(step|how to|framework|system|here's how|breakdown|works)\b", text_lower):
        return ("Breakdown Explainer", "Opens a strong promise, then dissects the underlying mechanism step-by-step with concrete examples.")
    if hook_cat == "Problem":
        return ("Problem Solution", "Diagnoses a painful bottleneck in the opening line and delivers the actionable fix within 10 seconds.")
    if duration and duration < 25:
        return ("Yap / Hot Take", "Tight, high-conviction direct-to-camera punch that sparks debate, saves, and shares.")
    return ("Breakdown Explainer", "Structured explanation pairing a clear hook with concrete proof and a takeaway.")


def _extract_tactics(text_lower, duration):
    tactics = []
    if re.search(r"(\$\d|\d+%|\d+\s*(million|billion|thousand|k\b|x\b))", text_lower):
        tactics.append("Data-backed Claim As Proof")
    if re.search(r"\b(stop|mistake|wrong|problem)\b", text_lower):
        tactics.append("Direct Problem Callout")
    if re.search(r"\b(first|second|third|step 1|number one|3 ways|5 )\b", text_lower):
        tactics.append("Rapid-Fire Numbered Structure")
    if re.search(r"\b(but here's|except|the catch|actually|instead|nobody)\b", text_lower):
        tactics.append("Contrarian Snapback")
    if re.search(r"\b(comment|dm me|link in bio|follow|save this)\b", text_lower):
        tactics.append("Comment-Trigger DM CTA")
    if re.search(r"\b(i |my |when i )\b", text_lower) and re.search(r"\b(learned|realized|mistake|story|years ago)\b", text_lower):
        tactics.append("Personal Anecdote → Moral Lesson")
    if re.search(r"\b(claude|chatgpt|gemini|shopify|meta|instagram|tiktok|google|elon|apple)\b", text_lower):
        tactics.append("Specific Named Object / Brand Anchor")
    if duration and duration <= 35:
        tactics.append("High-Density Tight Pacing (<35s)")
    return tactics[:5] if tactics else ["Direct Conversational Delivery"]


def _build_beats(transcript, caption, duration, fmt_cat):
    source = (transcript or caption or "").strip()
    if not source:
        return ("No spoken transcript captured yet — run TokScript backfill to unlock beat-by-beat timing.", [])
    sents = [s.strip() for s in re.split(r"(?<=[\.\!\?])\s+", source) if s.strip()]
    if not sents:
        sents = [source]
    dur = max(12, int(round(duration or max(18, len(source.split()) / 2.6))))
    n = len(sents)
    if n == 1:
        beats = [{"label": "Full Hook & Core Point", "timeRange": f"0:00 – {fmt_ts(dur)}", "text": sents[0]}]
    elif n <= 3:
        split1 = max(3, int(dur * 0.2))
        split2 = max(split1 + 3, int(dur * 0.78))
        beats = [
            {"label": "Opening Hook", "timeRange": f"0:00 – {fmt_ts(split1)}", "text": sents[0]},
            {"label": "Core Mechanism", "timeRange": f"{fmt_ts(split1)} – {fmt_ts(split2)}", "text": " ".join(sents[1:-1]) if n == 3 else sents[1]},
        ]
        if n == 3:
            beats.append({"label": "Payoff & CTA", "timeRange": f"{fmt_ts(split2)} – {fmt_ts(dur)}", "text": sents[-1]})
    else:
        hook_text = sents[0]
        cta_text = sents[-1]
        mid = sents[1:-1]
        k = min(3, max(1, len(mid)))
        chunk_size = max(1, (len(mid) + k - 1) // k)
        mid_chunks = [" ".join(mid[i:i + chunk_size]) for i in range(0, len(mid), chunk_size)]
        mid_labels = {
            "Listicle": ["Point 1 & Framing", "Core Rapid-Fire Points", "High-Leverage Climax"],
            "Common Trap Mistake": ["Why The Common Way Fails", "The Hidden Mechanism", "The Winning Fix"],
            "A Vs B Comparison": ["The Default Approach", "The Contrast & Proof", "The Winning Shift"],
            "Case Study": ["The Before State", "The Mechanism & Proof", "The Outcome"],
        }.get(fmt_cat, ["Context & Tension", "Core Breakdown", "Proof & Reframe"])
        raw_parts = [("Opening Hook", hook_text)]
        for idx, ch in enumerate(mid_chunks):
            raw_parts.append((mid_labels[min(idx, len(mid_labels) - 1)], ch))
        raw_parts.append(("Synthesis & CTA", cta_text))
        total_words = max(1, sum(len(t.split()) for _, t in raw_parts))
        cursor = 0.0
        beats = []
        for idx, (lbl, txt) in enumerate(raw_parts):
            share = (len(txt.split()) / total_words) * dur
            end = dur if idx == len(raw_parts) - 1 else min(dur, cursor + max(2.0, share))
            beats.append({"label": lbl, "timeRange": f"{fmt_ts(cursor)} – {fmt_ts(end)}", "text": txt})
            cursor = end
    overview = f"A {fmt_cat.lower()} sequence pacing {len(source.split())} words across {len(beats)} distinct retention beats ({fmt_ts(dur)} total)."
    return (overview, beats)


def _kennedy_audit(text, hook_text):
    t = (text or "").strip()
    tl = t.lower()
    sents = [s.strip() for s in re.split(r"(?<=[\.\!\?])\s+", t) if s.strip()]

    def find_quote(pat):
        for s in sents:
            if re.search(pat, s, re.I):
                return s[:135] + ("…" if len(s) > 135 else "")
        return ""

    el_rules = {
        "origin": r"\b(years ago|when i started|used to be|back in 20|my story|grew up|broke|started from)\b",
        "parables": r"\b(one day|a client|a guy|came up to me|told me|reminds me of|story|last week i)\b",
        "miracles": r"(\$\d[\d,\.]*[kKmMbB]?|\b\d+x\b|\b\d+%\b|\b\d+\s*(million|clients|hours|days)\b)",
        "insiderLanguage": r"(\bframework\b|\bmethod\b|\bsystem\b|\bprotocol\b|\bformula\b|\"[^\"]{3,28}\")",
        "dogma": r"\b(rule|never |always |the only |truth is|principle|must |non-negotiable)\b",
        "enemies": r"\b(gurus?|scam|bs|bullshit|most people|agencies|broken|lie|myth|stop telling|stop doing|hate)\b",
        "flaws": r"\b(i failed|my mistake|i was wrong|i lost|struggled|embarrass|admit|used to suck)\b",
    }
    elements = {}
    absent_count = 0
    for key, pat in el_rules.items():
        q = find_quote(pat)
        if q:
            elements[key] = {"status": "Present", "evidence": q}
        else:
            elements[key] = {"status": "Absent", "evidence": "Not deployed in this video"}
            absent_count += 1

    # 6 Kennedy Dimensions
    first_person_hits = len(re.findall(r"\b(i|my|me|we|our)\b", tl))
    instruction_hits = len(re.findall(r"\b(step|click|open|type|use|go to|first|second|third)\b", tl))
    if first_person_hits >= 5 and (elements["enemies"]["status"] == "Present" or elements["dogma"]["status"] == "Present" or elements["flaws"]["status"] == "Present"):
        char_vs_plot = "Character-Led"
    elif first_person_hits >= 2 and instruction_hits >= 2:
        char_vs_plot = "Balanced"
    else:
        char_vs_plot = "Plot-Led"

    if elements["enemies"]["status"] == "Present" and re.search(r"\b(stop|never|hate|lie|scam|wrong|bs|kill)\b", tl):
        polarization = "Strong"
    elif elements["dogma"]["status"] == "Present" or elements["enemies"]["status"] == "Present":
        polarization = "Weak"
    else:
        polarization = "None"

    if re.search(r"\b(biggest|impossible|insane|never|every single|destroyed|crushed|100%|zero)\b", tl):
        magnification = "Fully Magnified"
    elif len(sents) >= 3:
        magnification = "Moderately Magnified"
    else:
        magnification = "Diminished"

    if re.search(r"\b(today|yesterday|this week|this month|just announced|just dropped|right now|2025|2026|last night)\b", tl):
        context_anchor = "Fully Anchored"
    elif re.search(r"\b(recently|lately|now|new)\b", tl):
        context_anchor = "Partially Anchored"
    else:
        context_anchor = "Floating"

    if char_vs_plot == "Character-Led":
        core_story = "Advances Character"
    elif char_vs_plot == "Balanced":
        core_story = "Hybrid"
    else:
        core_story = "Information Delivery"

    deficit = absent_count
    if context_anchor == "Floating":
        deficit += 1
    if core_story == "Information Delivery":
        deficit += 1
    if magnification == "Diminished":
        deficit += 1
    if polarization == "None":
        deficit += 1
    if char_vs_plot == "Plot-Led":
        deficit += 1

    return {
        "elements": elements,
        "characterVsPlot": char_vs_plot,
        "polarization": polarization,
        "magnification": magnification,
        "contextAnchor": context_anchor,
        "coreStory": core_story,
        "deficitScore": min(12, deficit),
    }


def analyze_reel(row):
    transcript = (row.get("transcript") or "").strip()
    caption = (row.get("caption") or "").strip()
    full_text = transcript or caption
    text_lower = full_text.lower()
    hook_text = (row.get("hook") or "").strip()
    duration = row.get("duration") or 0

    topic = _classify_topic(text_lower + " " + caption.lower())
    hook_cat, fallback_formula = _classify_hook(hook_text)
    madlib = _extract_madlib(hook_text, fallback_formula)
    fmt_cat, fmt_desc = _classify_format(text_lower, hook_cat, duration)
    tactics = _extract_tactics(text_lower, duration)
    beat_overview, beats = _build_beats(transcript, caption, duration, fmt_cat)
    kennedy = _kennedy_audit(full_text, hook_text)

    # Extract supporting evidence sentences
    sents = [s.strip() for s in re.split(r"(?<=[\.\!\?])\s+", full_text) if len(s.strip()) > 25]
    evidence = [s[:160] + ("…" if len(s) > 160 else "") for s in sents[1:5] if re.search(r"(\d|\$|%|because|shows|means|result|step|instead|actually)", s, re.I)]
    if not evidence:
        evidence = [s[:155] + ("…" if len(s) > 155 else "") for s in sents[1:4]]

    # Visual layout heuristic
    if re.search(r"\b(screen|click|prompt|dashboard|app|claude|chatgpt|demo|workflow)\b", text_lower):
        vis_cat, vis_sub, vis_hook = "Screen Demo / Hybrid", "Screen Walkthrough + Face Cam", "Image Overlay Motion"
    elif re.search(r"\b(article|study|news|announced|paper|chart|report)\b", text_lower):
        vis_cat, vis_sub, vis_hook = "Greenscreen / Article", "Notes / Article Greenscreen", "Write On Screen"
    else:
        vis_cat, vis_sub, vis_hook = "Studio Set", "Office Room Yap", "Move In Frame"

    hook_words = len(hook_text.split())
    has_num = bool(re.search(r"\d", hook_text))
    alignment_notes = (
        f"Spoken hook runs {hook_words} words ({'tight & punchy' if hook_words <= 18 else 'slightly dense — tighten under 18 words'}) "
        f"using a {hook_cat} opener. "
        f"{'Includes a concrete number/anchor that raises perceived value immediately.' if has_num else 'Add one specific number, timeframe, or named tool in line 1 to widen the curiosity gap.'} "
        f"Pair with '{vis_hook}' visual framing and a 4–6 word on-screen headline echoing the spoken hook."
    )

    ratio = row.get("ratio") or 0
    summary = (
        f"A {fmt_cat.lower()} reel on {topic} by @{row.get('creator_username', '')} "
        f"performing at {ratio:.1f}× their median ({fmt_num(row.get('plays', 0))} plays). "
        f"Opens with a {hook_cat.lower()} hook and holds attention via {', '.join(tactics[:2]).lower()}."
    )

    common_belief_map = {
        "AI Agents & Automation": "Most people think AI means manually chatting with prompts one task at a time.",
        "Short-Form Hooks & Content": "Most creators think better editing or posting more volume fixes low views.",
        "Paid Ads & Creative": "Most advertisers think media-buying hacks and bidding tweaks drive ad scale.",
        "DTC Scale & Ecommerce": "Most brands think spending more on ads solves stagnant revenue.",
        "Offer & Sales Psychology": "Most sellers think explaining more features makes prospects buy.",
        "AI Tools & Demos": "Most viewers assume new AI features require technical skill or complex setup.",
    }
    common_belief = common_belief_map.get(topic, "Most people default to surface-level tactics instead of fixing the underlying mechanism.")
    contrarian = sents[1][:180] if len(sents) > 1 else (hook_text or "Reframes the problem around one specific, immediately verifiable lever.")

    return {
        "wordCount": len(full_text.split()) if full_text else 0,
        "summary": summary,
        "beatOverview": beat_overview,
        "beats": beats,
        "idea": {
            "topic": topic,
            "ideaSeed": hook_text or f"{topic} breakdown from @{row.get('creator_username', '')}",
            "uniqueAngle": f"Uses a {hook_cat} entry point into a {fmt_cat} structure ({ratio:.1f}× outlier signal).",
            "commonBelief": common_belief,
            "contrarianReality": contrarian,
            "supportingEvidence": evidence[:4],
        },
        "hook": {
            "category": hook_cat,
            "formula": madlib,
            "spokenHook": hook_text or "(no spoken hook)",
            "analysis": alignment_notes,
        },
        "format": {
            "category": fmt_cat,
            "description": fmt_desc,
            "analysis": f"Worked at {ratio:.1f}× median because it compresses {len(beats)} clear beats into {fmt_dur(duration)} without losing the central curiosity loop.",
            "tactics": tactics,
        },
        "visual": {
            "category": vis_cat,
            "subCategory": vis_sub,
            "visualHook": vis_hook,
            "pacingNote": f"Target cut/visual refresh every 2.5–4s across this {fmt_dur(duration)} runtime; reinforce line 1 with bold on-screen text.",
        },
        "kennedy": kennedy,
    }


def load_creator(handle):
    posts_path = DATA / f"{handle}_posts.json"
    details_path = DATA / f"{handle}_details.json"
    posts = load(posts_path)["items"] if posts_path.exists() else []
    saved = CREATOR_CONFIG.get(handle, {})
    details = load(details_path)["dataset"]["previewItems"][0] if details_path.exists() else {
        "username": handle,
        "fullName": saved.get("name", ""),
        "followersCount": saved.get("followers", 0),
        "postsCount": saved.get("posts", 0),
        "verified": saved.get("verified", False),
        "profilePicUrl": saved.get("profilePic", ""),
    }
    return posts, details


HTML_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Outlier Lab · AI Simple — __TODAY__</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=Sora:wght@400;500;600;700&family=Space+Mono:wght@400;700&display=swap" rel="stylesheet">
<style>
  :root {
    --yellow: #ffc71d;
    --yellow-hover: #f0b800;
    --yellow-soft: #fff2ba;
    --yellow-tint: #fff8da;
    --yellow-ink: #856000;
    --ink: #1f1f1f;
    --ink-2: #575650;
    --ink-3: #686469;
    --ink-muted: #77746e;
    --surface: #ffffff;
    --paper: #f5f4ef;
    --paper-alt: #f7f7f2;
    --input-bg: #fbfaf7;
    --charcoal: #1f1f1f;
    --lavender: #f0e5ff;
    --lavender-ink: #4f3d68;
    --sage: #eaf3e3;
    --sage-ink: #255a3b;
    --cream: #f9f3e5;
    --border: #e8e6dd;
    --border-strong: #d8d6ce;
    --breakout: #d4276b;
    --breakout-bg: #fce8f0;
    --working: #2e7d52;
    --working-bg: #eaf3e3;
    --blue-ink: #1e4b8f;
    --blue-bg: #e7f0fe;
    --radius-xl: 25px;
    --radius-lg: 22px;
    --radius-md: 14px;
    --radius-pill: 999px;
    --shadow-soft: 0 10px 30px rgba(31, 31, 31, 0.05);
    --shadow-card: 0 16px 36px rgba(31, 31, 31, 0.08);
    --shadow-pop: 0 24px 60px rgba(15, 12, 20, 0.18);
    --font-display: "Sora", -apple-system, BlinkMacSystemFont, sans-serif;
    --font-sans: "Manrope", -apple-system, BlinkMacSystemFont, "Inter", system-ui, sans-serif;
    --font-mono: "Space Mono", ui-monospace, SFMono-Regular, Menlo, monospace;
    --ease: cubic-bezier(0.2, 0.7, 0.2, 1);
  }
  *, *::before, *::after { box-sizing: border-box; }
  html { scroll-behavior: smooth; }
  body {
    margin: 0; background: var(--paper); color: var(--ink);
    font-family: var(--font-sans); font-size: 15px; line-height: 1.6;
    -webkit-font-smoothing: antialiased; min-height: 100vh;
  }
  ::selection { background: var(--yellow); color: var(--ink); }
  h1, h2, h3, h4 { font-family: var(--font-display); font-weight: 400; letter-spacing: -0.05em; margin: 0; }
  p { margin: 0; }
  a { color: inherit; text-decoration: none; }
  button, input, textarea, select { font: inherit; color: inherit; }
  button { border: 0; background: none; cursor: pointer; padding: 0; -webkit-tap-highlight-color: transparent; }
  a:focus-visible, button:focus-visible, input:focus-visible, textarea:focus-visible, select:focus-visible, summary:focus-visible {
    outline: 3px solid var(--yellow-ink); outline-offset: 3px;
  }

  .skip-link {
    position: fixed; top: 0; left: 24px; transform: translateY(-130%);
    background: var(--yellow); color: #111; font-weight: 800; font-size: 13px;
    padding: 12px 20px; border-radius: 0 0 12px 12px; z-index: 200;
  }
  .skip-link:focus { transform: translateY(0); }

  /* ===== CLEAN AI SIMPLE SIDEBAR SHELL ===== */
  .app-shell {
    display: grid; grid-template-columns: 244px minmax(0, 1fr); min-height: 100vh;
  }
  .app-sidebar {
    position: sticky; top: 0; height: 100vh; z-index: 60;
    background: var(--surface); border-right: 1px solid var(--border);
    padding: 18px 14px 16px; display: flex; flex-direction: column; gap: 16px;
    overflow-y: auto;
  }
  .sidebar-brand {
    display: flex; align-items: center; justify-content: space-between; gap: 8px; padding: 2px 4px;
  }
  .brand-lockup { display: inline-flex; align-items: center; gap: 9px; white-space: nowrap; flex-shrink: 0; }
  .brand-mark { width: 34px; height: 34px; border-radius: 10px; background: var(--yellow); display: grid; place-items: center; flex-shrink: 0; }
  .brand-wordmark { font-family: var(--font-sans); font-size: 16.5px; font-weight: 800; letter-spacing: -0.05em; line-height: 1; display: block; }
  .brand-sub { display: block; font-size: 10px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: var(--ink-3); margin-top: 2px; }

  /* Workspace Switcher (Sidebar) */
  .ws-wrap { position: relative; width: 100%; }
  .ws-trigger {
    width: 100%; display: flex; align-items: center; gap: 10px;
    padding: 8px 10px; border-radius: 14px;
    background: var(--paper); border: 1px solid var(--border);
    transition: border-color 0.15s, background 0.15s;
  }
  .ws-trigger:hover { border-color: var(--ink); background: var(--surface); }
  .ws-badge { width: 28px; height: 28px; border-radius: 9px; display: grid; place-items: center; font-size: 11px; font-weight: 800; flex-shrink: 0; }
  .ws-trigger-meta { text-align: left; line-height: 1.15; flex: 1; min-width: 0; }
  .ws-trigger-label { display: block; font-size: 9px; font-weight: 800; letter-spacing: 0.1em; text-transform: uppercase; color: var(--ink-3); }
  .ws-trigger-name { display: block; font-size: 13px; font-weight: 800; color: var(--ink); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .ws-chevron { width: 14px; height: 14px; color: var(--ink-3); transition: transform 0.2s; flex-shrink: 0; }
  .ws-trigger[aria-expanded="true"] .ws-chevron { transform: rotate(180deg); }
  .ws-menu {
    position: absolute; top: calc(100% + 8px); left: 0; width: 320px; max-width: calc(100vw - 28px);
    background: var(--surface); border: 1px solid var(--border-strong);
    border-radius: 18px; padding: 10px; box-shadow: var(--shadow-pop); z-index: 95;
  }
  .ws-menu[hidden] { display: none; }
  .ws-menu-title { font-size: 10px; font-weight: 800; letter-spacing: 0.12em; text-transform: uppercase; color: var(--ink-3); padding: 6px 10px 6px; }
  .ws-option { width: 100%; display: flex; align-items: center; gap: 11px; padding: 9px 10px; border-radius: 12px; text-align: left; overflow: hidden; transition: background 0.14s; }
  .ws-option:hover { background: var(--paper); }
  .ws-option.active { background: var(--yellow-tint); box-shadow: inset 0 0 0 1px rgba(133, 96, 0, 0.28); }
  .ws-option-info { flex: 1; min-width: 0; overflow: hidden; }
  .ws-option-name { font-size: 13px; font-weight: 800; color: var(--ink); display: flex; align-items: center; gap: 6px; }
  .ws-option-desc { display: block; font-size: 11.5px; color: var(--ink-3); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .ws-menu-divider { height: 1px; background: var(--border); margin: 8px 6px; }
  .ws-create-btn {
    width: 100%; display: flex; align-items: center; justify-content: center; gap: 8px;
    padding: 9px 12px; border-radius: 12px; background: var(--paper);
    border: 1px dashed var(--border-strong); font-size: 12.5px; font-weight: 700; transition: all 0.15s;
  }
  .ws-create-btn:hover { background: var(--yellow-soft); border-color: var(--yellow-ink); border-style: solid; }

  /* Primary Sidebar Navigation */
  .primary-tabs {
    display: flex; flex-direction: column; gap: 2px; flex: 1;
  }
  .nav-group-label {
    font-size: 10px; font-weight: 800; letter-spacing: 0.12em; text-transform: uppercase;
    color: var(--ink-3); padding: 12px 10px 5px;
  }
  .nav-group-label:first-child { padding-top: 2px; }
  .primary-tab {
    width: 100%; display: flex; align-items: center; justify-content: space-between; gap: 8px;
    padding: 9px 12px; border-radius: 12px;
    font-size: 13.5px; font-weight: 600; color: var(--ink-2); text-align: left;
    transition: background 0.14s, color 0.14s;
  }
  .primary-tab:hover { background: var(--paper); color: var(--ink); }
  .primary-tab[aria-selected="true"] {
    background: var(--charcoal); color: #ffffff; font-weight: 700;
  }
  .primary-tab-left { display: inline-flex; align-items: center; gap: 9px; min-width: 0; }
  .nav-ico { width: 16px; text-align: center; font-size: 13px; opacity: 0.85; flex-shrink: 0; }
  .tab-count {
    font-size: 10.5px; font-weight: 800; padding: 2px 7px; border-radius: var(--radius-pill);
    background: var(--paper); color: var(--ink-3); font-variant-numeric: tabular-nums;
  }
  .primary-tab[aria-selected="true"] .tab-count { background: var(--yellow); color: var(--ink); }
  .sidebar-footer {
    margin-top: auto; padding-top: 12px; border-top: 1px solid var(--border);
    display: flex; flex-direction: column; gap: 8px;
  }
  .sidebar-ai-pill {
    display: flex; align-items: center; gap: 8px; padding: 8px 10px; border-radius: 12px;
    background: var(--paper); font-size: 11.5px; font-weight: 700; color: var(--ink-2);
  }
  .sidebar-ai-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--ink-3); flex-shrink: 0; }
  .sidebar-ai-pill.ready .sidebar-ai-dot { background: var(--working); box-shadow: 0 0 0 3px rgba(46,125,82,0.18); }

  /* Minimal Top Bar + Canvas */
  .app-canvas { min-width: 0; display: flex; flex-direction: column; }
  .app-header {
    position: sticky; top: 0; z-index: 45; height: 60px;
    background: rgba(245, 244, 239, 0.88); backdrop-filter: blur(14px);
    border-bottom: 1px solid var(--border);
    padding: 0 32px; display: flex; align-items: center; justify-content: space-between; gap: 14px;
    transition: background 0.2s;
  }
  .app-header.scrolled { background: rgba(255, 255, 255, 0.96); }
  .topbar-left { display: flex; align-items: center; gap: 12px; min-width: 0; }
  .mobile-menu-btn {
    display: none; width: 36px; height: 36px; border-radius: 10px;
    background: var(--surface); border: 1px solid var(--border);
    align-items: center; justify-content: center; font-size: 16px;
  }
  .topbar-title { font-family: var(--font-display); font-size: 18px; font-weight: 500; letter-spacing: -0.03em; }
  .topbar-sep { color: var(--border-strong); }
  .topbar-sub { font-size: 12.5px; color: var(--ink-3); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .header-actions { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }

  /* Buttons */
  .btn {
    display: inline-flex; align-items: center; justify-content: center; gap: 8px;
    border-radius: var(--radius-pill); padding: 9px 17px;
    font-size: 13px; font-weight: 800; line-height: 1.2; white-space: nowrap;
    transition: background 0.16s var(--ease), transform 0.16s var(--ease), border-color 0.16s, color 0.16s;
  }
  .btn:hover { transform: translateY(-1px); }
  .btn:active { transform: translateY(0); }
  .btn:disabled { opacity: 0.55; cursor: not-allowed; transform: none; }
  .btn-yellow { background: var(--yellow); color: #151515; }
  .btn-yellow:hover { background: var(--yellow-hover); }
  .btn-dark { background: var(--charcoal); color: #ffffff; }
  .btn-dark:hover { background: #333; }
  .btn-outline { background: var(--surface); color: var(--ink); border: 1px solid var(--border-strong); }
  .btn-outline:hover { border-color: var(--ink); background: var(--paper); }
  .btn-ghost-dark { background: var(--paper); color: var(--ink); border: 1px solid var(--border); }
  .btn-ghost-dark:hover { border-color: var(--ink); background: var(--surface); }
  .btn-sm { padding: 7px 13px; font-size: 12px; }
  .btn-xs { padding: 5px 10px; font-size: 11px; }
  .kbd {
    display: inline-grid; place-items: center; min-width: 19px; height: 19px; padding: 0 5px;
    border-radius: 5px; background: rgba(31,31,31,0.08); font-family: var(--font-mono);
    font-size: 10px; font-weight: 700; color: var(--ink-2);
  }
  .btn-yellow .kbd { background: rgba(21,21,21,0.14); color: #151515; }
  .btn-dark .kbd { background: rgba(255,255,255,0.16); color: #fff; }

  /* Main Container — Calm, Centered, Generous Whitespace */
  .app-main { width: 100%; max-width: 1240px; margin: 0 auto; padding: 28px 34px 84px; }
  [hidden] { display: none !important; }
  .tab-panel[hidden], .sub-panel[hidden] { display: none; }
  .panel-inner { display: flex; flex-direction: column; gap: 30px; }

  /* Sub-tabs inside major sections */
  .sub-nav {
    display: inline-flex; align-items: center; gap: 4px; flex-wrap: wrap;
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius-pill); padding: 4px; align-self: flex-start;
  }
  .sub-nav button {
    padding: 7px 15px; border-radius: var(--radius-pill);
    font-size: 12.5px; font-weight: 700; color: var(--ink-2); transition: all 0.15s;
  }
  .sub-nav button:hover { color: var(--ink); }
  .sub-nav button.active { background: var(--charcoal); color: #ffffff; font-weight: 700; }

  /* Eyebrows & Highlights */
  .eyebrow-slash { font-size: 11.5px; font-weight: 700; letter-spacing: 0.04em; color: var(--ink-3); margin-bottom: 6px; display: inline-block; }
  .eyebrow-dot {
    display: inline-flex; align-items: center; gap: 7px;
    font-size: 10.5px; font-weight: 800; letter-spacing: 0.12em; text-transform: uppercase; color: var(--ink-3);
  }
  .eyebrow-dot::before { content: ""; width: 7px; height: 7px; border-radius: 50%; background: var(--yellow); flex-shrink: 0; }
  .highlight-mark { background: linear-gradient(transparent 66%, var(--yellow) 66%, var(--yellow) 94%, transparent 94%); padding-inline: 2px; }
  .gradient-highlight { background: linear-gradient(transparent 66%, var(--yellow) 66%, var(--yellow) 94%, transparent 94%); padding-inline: 2px; color: var(--ink); }

  /* Pills & Badges */
  .band-pill {
    display: inline-flex; align-items: center; gap: 5px;
    padding: 4px 10px; border-radius: var(--radius-pill);
    font-size: 11px; font-weight: 800; letter-spacing: 0.02em; font-variant-numeric: tabular-nums;
  }
  .band-pill.breakout { background: var(--breakout-bg); color: var(--breakout); }
  .band-pill.strong { background: var(--yellow-soft); color: var(--ink); }
  .band-pill.good { background: var(--working-bg); color: var(--working); }
  .band-pill.normal { background: var(--paper); color: var(--ink-3); }
  .metric-pill-blue { background: var(--blue-bg); color: var(--blue-ink); }
  .metric-pill-lav { background: var(--lavender); color: var(--lavender-ink); }
  .status-chip {
    display: inline-flex; align-items: center; gap: 5px; flex-shrink: 0;
    padding: 4px 10px; border-radius: var(--radius-pill);
    font-size: 11px; font-weight: 800; background: var(--yellow-soft); color: var(--ink);
  }
  .status-chip.live { background: var(--sage); color: var(--sage-ink); }
  .status-chip.warn { background: var(--breakout-bg); color: var(--breakout); }
  .status-chip.muted { background: var(--paper); color: var(--ink-3); border: 1px solid var(--border); }

  /* Calm Light Editorial Greeting (replaces heavy dark billboard) */
  .hero-banner {
    background: var(--surface); color: var(--ink); border: 1px solid var(--border);
    border-radius: 22px; padding: 26px 30px;
    display: flex; align-items: center; justify-content: space-between; gap: 24px; flex-wrap: wrap;
  }
  .hero-copy { flex: 1; min-width: 280px; }
  .hero-eyebrow {
    display: inline-flex; align-items: center; gap: 8px; font-size: 10.5px; font-weight: 800;
    letter-spacing: 0.12em; text-transform: uppercase; color: var(--ink-3); margin-bottom: 8px;
  }
  .hero-eyebrow .live-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--yellow); }
  .hero-banner h1 { font-size: clamp(24px, 2.4vw, 34px); line-height: 1.15; margin-bottom: 8px; color: var(--ink); }
  .hero-sub { color: var(--ink-2); font-size: 14px; line-height: 1.55; max-width: 58ch; margin-bottom: 16px; }
  .hero-actions { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
  .hero-side {
    display: flex; flex-direction: column; gap: 10px; align-items: flex-end;
  }
  .hero-ws-pills { display: flex; flex-wrap: wrap; gap: 6px; justify-content: flex-end; }
  .hero-ws-pill {
    padding: 6px 12px; border-radius: var(--radius-pill); background: var(--paper);
    border: 1px solid var(--border); color: var(--ink-2); font-size: 12px; font-weight: 700; transition: all 0.15s;
  }
  .hero-ws-pill:hover { border-color: var(--ink); color: var(--ink); }
  .hero-ws-pill.active { background: var(--charcoal); color: #fff; border-color: var(--charcoal); }
  .hero-side-stats { display: flex; gap: 18px; padding-top: 6px; }
  .hero-mini-stat { text-align: right; }
  .hero-mini-stat strong { display: block; font-family: var(--font-display); font-size: 20px; font-weight: 500; color: var(--ink); line-height: 1.1; font-variant-numeric: tabular-nums; }
  .hero-mini-stat span { font-size: 11px; color: var(--ink-3); }

  /* Keyword Score Dials, Tag Pills & SEO Checklist */
  .score-ring {
    width: 64px; height: 64px; border-radius: 50%; display: grid; place-items: center;
    font-family: var(--font-display); font-size: 22px; font-weight: 600; flex-shrink: 0;
    border: 5px solid var(--working); color: var(--working); background: var(--working-bg);
    font-variant-numeric: tabular-nums;
  }
  .score-ring.med { border-color: var(--yellow); color: var(--yellow-ink); background: var(--yellow-tint); }
  .score-ring.low { border-color: var(--breakout); color: var(--breakout); background: var(--breakout-bg); }
  .tag-score-pill {
    display: inline-flex; align-items: center; gap: 6px; padding: 5px 10px; border-radius: var(--radius-pill);
    background: var(--surface); border: 1px solid var(--border); font-size: 12px; font-weight: 700;
    cursor: pointer; transition: border-color 0.14s, background 0.14s;
  }
  .tag-score-pill:hover { border-color: var(--ink); background: var(--paper); }
  .tag-score-num {
    padding: 1px 6px; border-radius: var(--radius-pill); font-size: 10.5px; font-weight: 800; font-variant-numeric: tabular-nums;
  }
  .tag-score-num.hi { background: var(--sage); color: var(--sage-ink); }
  .tag-score-num.med { background: var(--yellow-soft); color: var(--yellow-ink); }
  .tag-score-num.lo { background: var(--breakout-bg); color: var(--breakout); }
  .seo-check-row {
    display: flex; align-items: flex-start; gap: 10px; padding: 9px 12px;
    border-radius: 12px; background: var(--paper); font-size: 13px;
  }
  .seo-dot { width: 18px; height: 18px; border-radius: 50%; display: grid; place-items: center; font-size: 11px; font-weight: 800; flex-shrink: 0; margin-top: 1px; }
  .seo-dot.pass { background: var(--sage); color: var(--sage-ink); }
  .seo-dot.fail { background: var(--breakout-bg); color: var(--breakout); }
  .calm-details {
    background: var(--surface); border: 1px solid var(--border); border-radius: 20px; padding: 18px 22px;
  }
  .calm-details > summary {
    cursor: pointer; list-style: none; display: flex; align-items: center; justify-content: space-between; gap: 12px;
    font-family: var(--font-display); font-size: 19px; letter-spacing: -0.03em;
  }
  .calm-details > summary::-webkit-details-marker { display: none; }
  .calm-details[open] > summary { padding-bottom: 14px; margin-bottom: 14px; border-bottom: 1px solid var(--border); }
  .sidebar-backdrop { display: none; position: fixed; inset: 0; background: rgba(15,12,20,0.4); z-index: 55; }
  .sidebar-backdrop.open { display: block; }

  /* AI Chat, Modality Tiers (S/A/B/C) & Integration Cards */
  .chat-shell { display: grid; grid-template-columns: minmax(0, 1fr) 280px; gap: 20px; align-items: start; }
  .chat-log { display: flex; flex-direction: column; gap: 12px; min-height: 360px; max-height: 540px; overflow-y: auto; padding: 18px; border-radius: 18px; background: var(--paper); border: 1px solid var(--border); }
  .chat-msg { max-width: 86%; padding: 13px 16px; border-radius: 16px; font-size: 14px; line-height: 1.6; white-space: pre-wrap; }
  .chat-msg.user { align-self: flex-end; background: var(--charcoal); color: #ffffff; border-bottom-right-radius: 5px; }
  .chat-msg.assistant { align-self: flex-start; background: var(--surface); color: var(--ink); border: 1px solid var(--border); border-bottom-left-radius: 5px; }
  .tier-group { padding: 12px 14px; border-radius: 14px; background: var(--paper); border: 1px solid var(--border); display: flex; flex-direction: column; gap: 8px; }
  .tier-badge { display: inline-flex; align-items: center; padding: 2px 8px; border-radius: 999px; font-size: 10.5px; font-weight: 800; letter-spacing: 0.06em; text-transform: uppercase; }
  .tier-badge.tier-s { background: var(--charcoal); color: var(--yellow); }
  .tier-badge.tier-a { background: var(--yellow); color: #151515; }
  .tier-badge.tier-b { background: var(--lavender); color: var(--lavender-ink); }
  .tier-badge.tier-c { background: var(--surface); color: var(--ink-3); border: 1px solid var(--border-strong); }
  .mod-chip { display: inline-flex; align-items: center; gap: 5px; padding: 5px 10px; border-radius: 999px; background: var(--surface); border: 1px solid var(--border-strong); font-size: 12px; font-weight: 700; cursor: pointer; transition: all 0.14s; }
  .mod-chip:hover { border-color: var(--ink); }
  .mod-chip.active { background: var(--charcoal); color: var(--yellow); border-color: var(--charcoal); }
  .toolkit-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }
  .toolkit-card { padding: 14px 16px; border-radius: 16px; background: var(--surface); border: 1px solid var(--border); display: flex; flex-direction: column; gap: 8px; }
  @media (max-width: 1120px) { .chat-shell, .toolkit-grid { grid-template-columns: 1fr; } }

  /* Section Headings & Segmented */
  .section-head { display: flex; align-items: flex-end; justify-content: space-between; gap: 14px; flex-wrap: wrap; }
  .section-head h2 { font-size: clamp(23px, 2.3vw, 32px); line-height: 1.15; }
  .section-head p { color: var(--ink-3); font-size: 14px; margin-top: 4px; }
  .segmented {
    display: inline-flex; align-items: center; gap: 3px;
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius-pill); padding: 4px;
  }
  .segmented button { padding: 6px 13px; border-radius: var(--radius-pill); font-size: 12px; font-weight: 700; color: var(--ink-3); transition: all 0.15s; }
  .segmented button:hover { color: var(--ink); }
  .segmented button.active { background: var(--charcoal); color: #fff; }

  /* Spotlight Grid (Top 5 Outliers) */
  .spotlight-grid { display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 18px; }
  .spotlight-card {
    grid-column: span 2; background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius-lg); overflow: hidden; display: flex; flex-direction: column;
    transition: transform 0.2s var(--ease), box-shadow 0.2s var(--ease), border-color 0.2s; cursor: pointer;
  }
  .spotlight-card:hover { transform: translateY(-4px); box-shadow: var(--shadow-card); border-color: var(--ink); }
  .spotlight-card.featured { grid-column: span 3; flex-direction: row; min-height: 290px; }
  .spotlight-card.featured.rank-1 { background: linear-gradient(145deg, #fffdf4 0%, #fff6cf 100%); border-color: rgba(255,199,29,0.7); }
  .spotlight-card.featured.rank-2 { background: linear-gradient(145deg, #ffffff 0%, #f5eeff 100%); border-color: #e2d5f5; }
  .spotlight-thumb { position: relative; background: #161618; overflow: hidden; aspect-ratio: 16/10; flex-shrink: 0; }
  .spotlight-card.featured .spotlight-thumb { width: 205px; aspect-ratio: auto; min-height: 100%; }
  .spotlight-thumb img { width: 100%; height: 100%; object-fit: cover; display: block; transition: transform 0.35s var(--ease); }
  .spotlight-card:hover .spotlight-thumb img { transform: scale(1.04); }
  .spotlight-thumb::after { content: ""; position: absolute; inset: 0; background: linear-gradient(180deg, rgba(0,0,0,0.2) 0%, transparent 40%, rgba(0,0,0,0.68) 100%); pointer-events: none; }
  .spotlight-rank { position: absolute; top: 11px; left: 11px; z-index: 2; padding: 3px 10px; border-radius: var(--radius-pill); background: var(--charcoal); color: var(--yellow); font-size: 11px; font-weight: 800; }
  .spotlight-play-btn {
    position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%) scale(0.92); z-index: 2;
    width: 46px; height: 46px; border-radius: 50%; background: var(--yellow); color: #151515;
    display: grid; place-items: center; padding-left: 3px; font-size: 15px; opacity: 0; transition: all 0.2s;
  }
  .spotlight-card:hover .spotlight-play-btn { opacity: 1; transform: translate(-50%,-50%) scale(1); }
  .spotlight-thumb-foot { position: absolute; bottom: 10px; left: 11px; right: 11px; z-index: 2; display: flex; justify-content: space-between; color: #fff; font-size: 11px; font-weight: 700; }
  .spotlight-pill { padding: 3px 8px; border-radius: var(--radius-pill); background: rgba(0,0,0,0.66); backdrop-filter: blur(4px); font-variant-numeric: tabular-nums; }
  .spotlight-body { padding: 18px 20px; display: flex; flex-direction: column; gap: 10px; flex: 1; min-width: 0; }
  .spotlight-top-meta { display: flex; align-items: center; justify-content: space-between; gap: 8px; flex-wrap: wrap; }
  .creator-mini { display: inline-flex; align-items: center; gap: 7px; font-size: 12px; font-weight: 700; color: var(--ink-2); }
  .creator-mini img, .creator-mini .avatar-dot { width: 22px; height: 22px; border-radius: 50%; object-fit: cover; background: var(--border); }
  .spotlight-hook { font-family: var(--font-display); font-size: 16.5px; line-height: 1.35; letter-spacing: -0.03em; font-weight: 500; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
  .spotlight-card.featured .spotlight-hook { font-size: 18.5px; -webkit-line-clamp: 4; }
  .tag-row { display: flex; flex-wrap: wrap; gap: 6px; }
  .micro-tag { font-size: 10.5px; font-weight: 800; padding: 3px 9px; border-radius: var(--radius-pill); background: rgba(31,31,31,0.06); color: var(--ink-2); }
  .spotlight-metrics { margin-top: auto; padding-top: 10px; border-top: 1px solid rgba(31,31,31,0.08); display: flex; align-items: center; justify-content: space-between; gap: 8px; flex-wrap: wrap; }
  .metric-cluster { display: flex; align-items: center; gap: 11px; font-size: 12px; color: var(--ink-2); font-variant-numeric: tabular-nums; }
  .metric-cluster strong { color: var(--ink); font-weight: 800; }

  /* Success Formula Banner */
  .formula-card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius-xl); padding: 26px 30px;
    display: flex; flex-direction: column; gap: 16px; box-shadow: var(--shadow-soft);
  }
  .formula-equation {
    display: grid; grid-template-columns: 1fr auto 1fr auto 1fr; gap: 12px; align-items: center;
  }
  .formula-slot {
    padding: 16px 18px; border-radius: 18px; border: 1px solid var(--border); background: var(--paper);
  }
  .formula-slot.s-topic { background: var(--yellow-tint); border-color: rgba(255,199,29,0.65); }
  .formula-slot.s-format { background: var(--lavender); border-color: #dfd0f5; }
  .formula-slot.s-hook { background: var(--sage); border-color: #c8dfc0; }
  .formula-slot span { display: block; font-size: 10px; font-weight: 800; letter-spacing: 0.11em; text-transform: uppercase; color: var(--ink-3); margin-bottom: 4px; }
  .formula-slot strong { display: block; font-family: var(--font-display); font-size: 18px; line-height: 1.2; }
  .formula-slot small { display: block; font-size: 11.5px; font-weight: 700; color: var(--ink-2); margin-top: 5px; }
  .formula-plus { font-family: var(--font-display); font-size: 24px; color: var(--ink-3); text-align: center; }

  /* KPI Grid */
  .kpi-grid { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 14px; }
  .kpi-card { border-radius: var(--radius-lg); padding: 20px 22px; border: 1px solid var(--border); background: var(--surface); display: flex; flex-direction: column; gap: 5px; }
  .kpi-card.tone-yellow { background: var(--yellow); border-color: var(--yellow); }
  .kpi-card.tone-lavender { background: var(--lavender); border-color: var(--lavender); }
  .kpi-card.tone-sage { background: var(--sage); border-color: var(--sage); }
  .kpi-card.tone-cream { background: var(--cream); border-color: var(--cream); }
  .kpi-label { font-size: 10px; font-weight: 800; letter-spacing: 0.11em; text-transform: uppercase; color: var(--ink-3); }
  .kpi-card.tone-yellow .kpi-label { color: #514715; }
  .kpi-val { font-family: var(--font-display); font-size: clamp(25px, 2.2vw, 34px); line-height: 1.05; letter-spacing: -0.05em; font-variant-numeric: tabular-nums; }
  .kpi-delta { font-size: 12px; color: var(--ink-2); }

  /* Dual Action Banner */
  .dual-banner { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; }
  .action-card { border-radius: var(--radius-xl); padding: 30px 32px; display: flex; flex-direction: column; gap: 12px; }
  .action-card.charcoal { background: var(--charcoal); color: #fff; }
  .action-card.yellow { background: var(--yellow); color: var(--ink); }
  .action-card h3 { font-size: clamp(22px, 2vw, 30px); line-height: 1.15; }
  .action-card p { font-size: 14px; line-height: 1.6; max-width: 50ch; }
  .action-card.charcoal p { color: #cfcfcf; }
  .action-card.yellow p { color: #473e12; }
  .action-card-foot { margin-top: auto; padding-top: 8px; display: flex; gap: 10px; flex-wrap: wrap; }

  /* Feed Controls, Table & Grid */
  .niche-nav { display: flex; flex-wrap: wrap; gap: 7px; }
  .niche-nav button { padding: 8px 15px; border-radius: var(--radius-pill); background: var(--surface); border: 1px solid var(--border); font-size: 12.5px; font-weight: 700; color: var(--ink-2); transition: all 0.15s; }
  .niche-nav button:hover { border-color: var(--ink); color: var(--ink); }
  .niche-nav button.active { background: var(--yellow); color: #151515; border-color: var(--yellow); font-weight: 800; }

  .creators-row { display: flex; gap: 10px; overflow-x: auto; padding: 2px 2px 8px; scrollbar-width: thin; }
  .creator-chip {
    display: flex; align-items: center; gap: 10px; padding: 8px 14px 8px 8px;
    background: var(--surface); border: 1px solid var(--border); border-radius: 16px;
    flex-shrink: 0; text-align: left; transition: all 0.15s;
  }
  .creator-chip:hover { border-color: var(--ink); transform: translateY(-1px); }
  .creator-chip.active { background: var(--yellow-tint); border-color: var(--yellow-ink); box-shadow: inset 0 0 0 1px rgba(133,96,0,0.25); }
  .creator-chip img, .creator-chip .avatar-fallback { width: 36px; height: 36px; border-radius: 50%; object-fit: cover; background: var(--paper); flex-shrink: 0; }
  .chip-name { font-size: 12.5px; font-weight: 800; }
  .chip-stats { font-size: 11px; color: var(--ink-3); }
  .creator-add-chip { border-style: dashed; border-color: var(--border-strong); font-weight: 800; font-size: 12.5px; justify-content: center; padding: 8px 16px; min-width: 140px; }
  .creator-add-chip:hover { background: var(--yellow-soft); border-style: solid; border-color: var(--yellow-ink); }

  .filter-card {
    background: var(--surface); border: 1px solid var(--border); border-radius: 20px;
    padding: 14px 16px; display: flex; flex-direction: column; gap: 10px;
  }
  .filter-row { display: flex; align-items: center; gap: 9px; flex-wrap: wrap; }
  .filter-search {
    flex: 1; min-width: 220px; padding: 9px 14px; background: var(--input-bg);
    border: 1px solid var(--border-strong); border-radius: 12px; font-size: 13.5px; outline: none;
  }
  .filter-search:focus { border-color: var(--yellow-ink); background: #fff; box-shadow: 0 0 0 3px rgba(255,199,29,0.28); }
  .filter-select {
    padding: 8px 12px; border-radius: 12px; background: var(--input-bg);
    border: 1px solid var(--border-strong); font-size: 12.5px; font-weight: 700; outline: none;
  }
  .band-filter { display: inline-flex; gap: 3px; background: var(--paper); border: 1px solid var(--border); border-radius: var(--radius-pill); padding: 3px; flex-wrap: wrap; }
  .band-filter button { padding: 5px 11px; border-radius: var(--radius-pill); font-size: 12px; font-weight: 700; color: var(--ink-2); display: inline-flex; align-items: center; gap: 5px; }
  .band-filter button.active { background: var(--charcoal); color: #fff; }
  .band-filter .swatch { width: 8px; height: 8px; border-radius: 50%; }
  .toggle-pill { padding: 7px 12px; border-radius: var(--radius-pill); background: var(--paper); border: 1px solid var(--border); font-size: 12px; font-weight: 700; color: var(--ink-2); }
  .toggle-pill.on { background: var(--sage); border-color: var(--working); color: var(--sage-ink); }

  body[data-view="grid"] .table-view { display: none; }
  body[data-view="table"] .grid-view { display: none; }

  .table-wrap { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-lg); overflow-x: auto; box-shadow: var(--shadow-soft); }
  table.reels-table { width: 100%; border-collapse: collapse; font-size: 13px; }
  table.reels-table thead th {
    background: var(--paper-alt); padding: 12px 10px; text-align: left;
    font-size: 10px; letter-spacing: 0.11em; text-transform: uppercase; color: var(--ink-3);
    font-weight: 800; border-bottom: 1px solid var(--border); white-space: nowrap; user-select: none;
  }
  table.reels-table thead th:first-child, table.reels-table tbody td:first-child { padding-left: 14px; }
  table.reels-table thead th:last-child, table.reels-table tbody td:last-child { padding-right: 16px; }
  table.reels-table thead th[data-sort] { cursor: pointer; }
  table.reels-table thead th.sort-active { color: var(--ink); }
  table.reels-table thead th .arrow { display: inline-block; margin-left: 4px; opacity: 0.25; font-size: 9px; }
  table.reels-table thead th.sort-active .arrow { opacity: 1; color: var(--yellow-ink); }
  table.reels-table tbody tr { border-bottom: 1px solid #f0eee7; cursor: pointer; transition: background 0.12s; }
  table.reels-table tbody tr:hover { background: #fffdf5; }
  table.reels-table td { padding: 10px 10px; vertical-align: middle; white-space: nowrap; }
  table.reels-table td.num, table.reels-table th.num { text-align: right; font-variant-numeric: tabular-nums; }
  table.reels-table td.hook-cell { white-space: normal; min-width: 220px; max-width: 340px; }
  .row-hook { display: block; max-width: 320px; font-size: 13px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .row-hook-sub { display: block; font-size: 11px; color: var(--ink-3); margin-top: 2px; }
  body[data-density="compact"] table.reels-table td { padding: 6px 10px; font-size: 12px; }
  .row-check { width: 18px; height: 18px; border-radius: 5px; border: 1.5px solid var(--border-strong); display: inline-flex; align-items: center; justify-content: center; background: #fff; vertical-align: middle; }
  .row-check.checked { background: var(--working); border-color: var(--working); color: #fff; }
  .row-check.checked::after { content: "✓"; font-size: 11px; font-weight: 800; }
  .row-delete { color: var(--ink-muted); font-size: 15px; margin-left: 7px; vertical-align: middle; }
  tr.completed { opacity: 0.45; }
  tr.completed .row-hook { text-decoration: line-through; }

  .reel-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(255px, 1fr)); gap: 16px; }
  .reel-card { background: var(--surface); border: 1px solid var(--border); border-radius: 20px; overflow: hidden; display: flex; flex-direction: column; cursor: pointer; transition: all 0.2s var(--ease); }
  .reel-card:hover { transform: translateY(-3px); box-shadow: var(--shadow-card); border-color: var(--ink); }
  .reel-card .thumb { position: relative; aspect-ratio: 9/11; background: #19191b; overflow: hidden; }
  .reel-card .thumb img { width: 100%; height: 100%; object-fit: cover; display: block; }
  .reel-card .thumb-top { position: absolute; top: 10px; right: 10px; display: flex; gap: 5px; }
  .reel-card .thumb-bot { position: absolute; bottom: 10px; left: 10px; padding: 3px 9px; border-radius: var(--radius-pill); background: rgba(0,0,0,0.72); color: #fff; font-size: 11px; font-weight: 700; }
  .reel-card .meta { padding: 14px 16px; display: flex; flex-direction: column; gap: 8px; flex: 1; }
  .reel-card .hook { font-size: 13.5px; line-height: 1.4; font-weight: 600; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
  .reel-card .stats { display: flex; gap: 9px; flex-wrap: wrap; font-size: 11.5px; color: var(--ink-3); border-top: 1px solid #f0eee7; padding-top: 9px; margin-top: auto; }

  /* ===== IDEAS, HOOK VAULT, PRE-FLIGHT CHECKER, COLLECTIONS, PROJECTS ===== */
  .card-grid-2 { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; }
  .card-grid-3 { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; }
  .panel-card {
    background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-lg);
    padding: 24px 26px; display: flex; flex-direction: column; gap: 14px;
  }
  .panel-card.tone-butter { background: linear-gradient(180deg, #fffdf5 0%, #fff7d6 100%); border-color: #f0dfa0; }
  .panel-card.tone-lavender { background: linear-gradient(180deg, #ffffff 0%, #f5eeff 100%); border-color: #e3d6f5; }
  .panel-card.tone-sage { background: linear-gradient(180deg, #ffffff 0%, #eef6e8 100%); border-color: #cfe0c4; }
  .panel-card.tone-cream { background: var(--cream); border-color: #e9dec8; }

  .idea-card {
    background: var(--surface); border: 1px solid var(--border); border-radius: 20px;
    padding: 20px 22px; display: flex; flex-direction: column; gap: 12px;
  }
  .idea-card.shortlisted { border-color: var(--working); background: linear-gradient(180deg, #fff 0%, #f4faf0 100%); }
  .contrast-box {
    display: grid; grid-template-columns: 1fr 1fr; gap: 10px;
    padding: 12px; border-radius: 14px; background: var(--paper); font-size: 12.5px;
  }
  .contrast-box strong { display: block; font-size: 10px; text-transform: uppercase; letter-spacing: 0.1em; color: var(--ink-3); margin-bottom: 3px; }
  .remix-box {
    padding: 13px 15px; border-radius: 14px; background: var(--yellow-tint);
    border: 1px solid rgba(255,199,29,0.55); font-size: 13px;
  }

  .hook-vault-card {
    background: var(--surface); border: 1px solid var(--border); border-radius: 18px;
    padding: 18px 20px; display: flex; flex-direction: column; gap: 10px;
  }
  .madlib-text {
    font-family: var(--font-display); font-size: 16px; line-height: 1.4; letter-spacing: -0.02em;
  }
  .madlib-slot { background: var(--yellow-soft); color: var(--ink); padding: 1px 6px; border-radius: 6px; font-weight: 600; }

  /* Pre-flight Hook Checker */
  .checker-box {
    background: var(--charcoal); color: #fff; border-radius: var(--radius-xl);
    padding: 28px 30px; display: grid; grid-template-columns: 1.2fr 0.8fr; gap: 24px; align-items: start;
  }
  .checker-textarea {
    width: 100%; min-height: 92px; padding: 14px 16px; border-radius: 14px;
    background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.2);
    color: #fff; font-size: 16px; font-family: var(--font-display); resize: vertical; outline: none;
  }
  .checker-textarea:focus { border-color: var(--yellow); background: rgba(255,255,255,0.12); }
  .checker-results {
    background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.14);
    border-radius: 18px; padding: 18px 20px; display: flex; flex-direction: column; gap: 10px;
  }
  .verdict-pill { display: inline-flex; padding: 5px 12px; border-radius: var(--radius-pill); font-size: 12px; font-weight: 800; align-self: flex-start; }
  .verdict-pill.ships { background: var(--sage); color: var(--sage-ink); }
  .verdict-pill.fix { background: var(--breakout-bg); color: var(--breakout); }
  .verdict-pill.neutral { background: var(--yellow); color: #151515; }

  /* Strategy Audit Bars */
  .audit-layout { display: grid; grid-template-columns: 1.15fr 0.85fr; gap: 20px; align-items: start; }
  .bar-row {
    width: 100%; text-align: left; padding: 12px 14px; border-radius: 14px;
    border: 1px solid var(--border); background: var(--surface);
    display: flex; flex-direction: column; gap: 7px; transition: all 0.14s;
  }
  .bar-row:hover { border-color: var(--ink); }
  .bar-row.active { background: var(--yellow-tint); border-color: var(--yellow-ink); box-shadow: inset 0 0 0 1px rgba(133,96,0,0.25); }
  .bar-track { height: 10px; border-radius: 999px; background: var(--paper); overflow: hidden; }
  .bar-fill { height: 100%; border-radius: 999px; background: var(--charcoal); }
  .bar-row.active .bar-fill { background: var(--yellow); }

  /* 4-Step Script Builder */
  .wizard-steps { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }
  .wizard-step {
    padding: 13px 16px; border-radius: 16px; background: var(--surface);
    border: 1px solid var(--border); text-align: left; display: flex; align-items: center; gap: 10px;
  }
  .wizard-step.active { background: var(--charcoal); color: #fff; border-color: var(--charcoal); }
  .wizard-num {
    width: 26px; height: 26px; border-radius: 50%; display: grid; place-items: center;
    background: var(--paper); color: var(--ink); font-size: 12px; font-weight: 800; flex-shrink: 0;
  }
  .wizard-step.active .wizard-num { background: var(--yellow); color: #151515; }

  /* Form Controls */
  .field-label { display: block; font-size: 12px; font-weight: 800; color: var(--ink); margin-bottom: 5px; }
  .field-input, .field-textarea, .field-select {
    width: 100%; padding: 11px 14px; border-radius: 12px;
    border: 1px solid var(--border-strong); background: var(--surface);
    color: var(--ink); font-size: 14px; outline: none;
  }
  .field-textarea { resize: vertical; min-height: 82px; line-height: 1.55; }
  .field-input:focus, .field-textarea:focus, .field-select:focus { border-color: var(--yellow-ink); box-shadow: 0 0 0 3px rgba(255,199,29,0.3); }
  .form-row-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
  .platform-pills { display: flex; gap: 6px; flex-wrap: wrap; }
  .platform-pill { padding: 6px 12px; border-radius: var(--radius-pill); background: var(--surface); border: 1px solid var(--border-strong); font-size: 12px; font-weight: 700; color: var(--ink-2); }
  .platform-pill.active { background: var(--charcoal); color: #fff; border-color: var(--charcoal); }

  /* Character Archetype Cards */
  .archetype-grid { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 10px; }
  .archetype-opt {
    padding: 14px; border-radius: 16px; background: var(--paper); border: 1px solid var(--border-strong);
    text-align: left; display: flex; flex-direction: column; gap: 5px; transition: all 0.14s;
  }
  .archetype-opt:hover { border-color: var(--ink); background: var(--surface); }
  .archetype-opt.active { background: var(--yellow-tint); border-color: var(--yellow-ink); box-shadow: inset 0 0 0 1px var(--yellow-ink); }
  .archetype-opt strong { font-size: 13px; font-weight: 800; }
  .archetype-opt span { font-size: 11.5px; color: var(--ink-2); line-height: 1.4; }

  /* Channels / Socials / Setup */
  .socials-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 16px; }
  .social-card { background: var(--surface); border: 1px solid var(--border); border-radius: 22px; padding: 20px; display: flex; flex-direction: column; gap: 12px; }
  .social-card.connected { background: linear-gradient(180deg, #fff 0%, #f3faee 100%); border-color: #c7e0ba; }
  .roster-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(290px, 1fr)); gap: 16px; }
  .roster-card { background: var(--surface); border: 1px solid var(--border); border-radius: 20px; padding: 18px; display: flex; flex-direction: column; gap: 12px; }
  .progress-bar { height: 6px; border-radius: 999px; background: var(--paper); overflow: hidden; }
  .progress-bar > span { display: block; height: 100%; background: var(--yellow); border-radius: 999px; }

  .code-block {
    font-family: var(--font-mono); font-size: 12px; background: var(--charcoal); color: #f6f6f4;
    padding: 14px 16px; border-radius: 14px; overflow-x: auto; white-space: pre-wrap;
  }

  /* ===== NATIVE <dialog> — FULL 6-TAB VIDEO BREAKDOWN STUDIO ===== */
  dialog { padding: 0; border: 0; background: transparent; max-width: min(1240px, 96vw); max-height: 94vh; overflow: visible; color: var(--ink); }
  dialog:modal { overscroll-behavior: contain; }
  dialog::backdrop { background: rgba(15, 13, 18, 0.74); backdrop-filter: blur(8px); overflow: hidden; overscroll-behavior: contain; }
  .dialog-shell { background: var(--surface); border-radius: 26px; overflow: hidden; border: 1px solid var(--border); box-shadow: var(--shadow-pop); position: relative; }
  .dialog-close {
    width: 36px; height: 36px; border-radius: 50%; background: var(--paper); color: var(--ink);
    font-size: 19px; display: grid; place-items: center; border: 1px solid var(--border); flex-shrink: 0;
  }
  .dialog-close:hover { background: var(--yellow); }

  .bd-shell { width: min(1220px, 95vw); max-height: 92vh; display: flex; flex-direction: column; }
  .bd-topbar {
    padding: 14px 22px; border-bottom: 1px solid var(--border); background: var(--paper-alt);
    display: flex; align-items: center; justify-content: space-between; gap: 14px;
  }
  .bd-topbar h1 { font-size: 18px; line-height: 1.25; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 760px; }
  .bd-body { display: grid; grid-template-columns: 340px minmax(0, 1fr); flex: 1; min-height: 0; overflow: hidden; }
  .bd-left {
    border-right: 1px solid var(--border); background: var(--paper);
    padding: 18px; overflow-y: auto; display: flex; flex-direction: column; gap: 14px;
  }
  .bd-video-stage {
    position: relative; aspect-ratio: 9/14; max-height: 410px; width: 100%;
    background: #0e0e11; border-radius: 18px; overflow: hidden;
  }
  .bd-video-stage video, .bd-video-stage iframe { width: 100%; height: 100%; border: 0; object-fit: cover; background: #000; }
  .hook-clip-badge { position: absolute; top: 10px; left: 10px; padding: 4px 10px; border-radius: var(--radius-pill); background: var(--yellow); color: #151515; font-size: 10px; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; }
  .modal-source-toggle { position: absolute; bottom: 10px; left: 10px; padding: 7px 12px; border-radius: var(--radius-pill); background: rgba(15,15,18,0.82); color: #fff; border: 1px solid rgba(255,255,255,0.22); font-size: 10.5px; font-weight: 800; text-transform: uppercase; }
  .modal-source-toggle:hover { background: var(--yellow); color: #151515; }

  .bd-actions { display: flex; flex-direction: column; gap: 7px; }
  .bd-actions .btn { width: 100%; justify-content: space-between; }

  .bd-right { padding: 22px 26px; overflow-y: auto; display: flex; flex-direction: column; gap: 16px; min-width: 0; }
  .bd-summary { padding: 15px 18px; border-radius: 16px; background: var(--yellow-tint); border: 1px solid rgba(255,199,29,0.55); font-size: 13.5px; line-height: 1.55; }
  .bd-tabs { display: flex; gap: 4px; flex-wrap: wrap; border-bottom: 1px solid var(--border); padding-bottom: 10px; }
  .bd-tab { padding: 7px 13px; border-radius: var(--radius-pill); font-size: 12px; font-weight: 700; color: var(--ink-2); background: var(--paper); }
  .bd-tab.active { background: var(--charcoal); color: #fff; }
  .bd-tab-panel[hidden] { display: none; }
  .bd-card { padding: 18px 20px; border-radius: 18px; background: var(--paper); border: 1px solid var(--border); display: flex; flex-direction: column; gap: 12px; }
  .beat-item { padding: 12px 14px; border-radius: 12px; background: var(--surface); border: 1px solid var(--border); }
  .beat-head { display: flex; justify-content: space-between; align-items: center; gap: 10px; margin-bottom: 5px; }
  .beat-time { font-family: var(--font-mono); font-size: 11px; font-weight: 700; color: var(--yellow-ink); background: var(--yellow-soft); padding: 2px 8px; border-radius: 999px; }

  .k7-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 9px; }
  .k7-item { padding: 11px 13px; border-radius: 12px; background: var(--surface); border: 1px solid var(--border); font-size: 12.5px; }
  .k7-item.present { border-color: #a9d19a; background: #f4faf0; }

  /* Compact Form Dialogs */
  .form-dialog-shell { width: min(580px, 94vw); padding: 28px 30px; display: flex; flex-direction: column; gap: 16px; }
  .form-dialog-shell h1 { font-size: 24px; padding-right: 36px; }
  .swatch-row { display: flex; gap: 8px; }
  .color-swatch { width: 28px; height: 28px; border-radius: 50%; border: 2px solid transparent; }
  .color-swatch.active { border-color: var(--ink); box-shadow: 0 0 0 2px #fff inset; }

  .app-footer {
    width: calc(100% - 40px); max-width: 1560px; margin: 0 auto 32px;
    background: var(--charcoal); color: #fff; border-radius: var(--radius-xl);
    padding: 24px 32px; display: flex; align-items: center; justify-content: space-between; gap: 18px; flex-wrap: wrap;
  }
  .footer-meta { font-size: 12.5px; color: #a9a9a9; display: flex; gap: 16px; flex-wrap: wrap; }
  .footer-meta a { color: var(--yellow); font-weight: 700; }

  .toast {
    position: fixed; bottom: 22px; right: 22px; z-index: 250;
    padding: 12px 20px; border-radius: var(--radius-pill); background: var(--charcoal); color: #fff;
    font-size: 13px; font-weight: 700; box-shadow: var(--shadow-pop); opacity: 0;
    transform: translateY(10px); transition: opacity 0.2s, transform 0.2s; pointer-events: none;
    display: flex; align-items: center; gap: 8px;
  }
  .toast.show { opacity: 1; transform: translateY(0); }
  .toast-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--yellow); }
  .empty-box { padding: 36px 22px; text-align: center; border-radius: 20px; background: var(--surface); border: 1px dashed var(--border-strong); color: var(--ink-2); }

  @media (max-width: 1260px) {
    .checker-box, .audit-layout { grid-template-columns: 1fr; }
    .kpi-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
    .socials-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .archetype-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .spotlight-card.featured { grid-column: span 6; }
    .spotlight-card { grid-column: span 3; }
    .formula-equation { grid-template-columns: 1fr; }
    .formula-plus { display: none; }
  }
  @media (max-width: 980px) {
    .app-shell { grid-template-columns: 1fr; }
    .app-sidebar { position: fixed; left: 0; top: 0; width: 260px; transform: translateX(-105%); transition: transform 0.22s var(--ease); box-shadow: var(--shadow-pop); }
    .app-sidebar.open { transform: translateX(0); }
    .mobile-menu-btn { display: inline-flex; }
    .app-header { padding: 0 18px; }
    .app-main { padding: 20px 18px 64px; }
    .card-grid-2, .card-grid-3, .dual-banner, .wizard-steps, .bd-body, .k7-grid, .contrast-box { grid-template-columns: 1fr; }
    .bd-left { border-right: 0; border-bottom: 1px solid var(--border); }
  }
  @media (max-width: 680px) {
    .spotlight-card, .spotlight-card.featured { grid-column: span 6; flex-direction: column; }
    .spotlight-card.featured .spotlight-thumb { width: 100%; aspect-ratio: 16/10; min-height: 190px; }
    .kpi-grid, .socials-grid, .form-row-2, .archetype-grid { grid-template-columns: 1fr; }
    .hero-side { align-items: flex-start; }
  }
  @media (prefers-reduced-motion: reduce) {
    *, *::before, *::after { transition: none !important; animation: none !important; scroll-behavior: auto !important; }
  }
</style>
</head>
<body data-view="table" data-density="comfy">
<a class="skip-link" href="#main-content">Skip to workspace</a>

<!-- CLEAN AI SIMPLE SIDEBAR LAYOUT -->
<div class="sidebar-backdrop" id="sidebar-backdrop"></div>
<div class="app-shell">
  <aside class="app-sidebar" id="app-sidebar" aria-label="Outlier Lab Navigation">
    <div class="sidebar-brand">
      <a class="brand-lockup" href="#today" id="brand-home-link" aria-label="AI Simple Outlier Lab Home">
        <span class="brand-mark" aria-hidden="true">
          <svg width="20" height="20" viewBox="0 0 64 64" fill="none">
            <path d="M16 48L28.8 18.6C30.1 15.6 33.9 15.6 35.2 18.6L48 48" stroke="#111111" stroke-width="10.5" stroke-linecap="round" stroke-linejoin="round"/>
            <circle cx="32" cy="44" r="6.8" fill="#111111"/>
          </svg>
        </span>
        <span>
          <span class="brand-wordmark">AI SIMPLE</span>
          <span class="brand-sub">Outlier Lab</span>
        </span>
      </a>
    </div>

    <div class="ws-wrap">
      <button type="button" class="ws-trigger" id="ws-trigger" aria-haspopup="menu" aria-expanded="false" aria-controls="ws-menu">
        <span class="ws-badge" id="ws-active-badge" style="background:#ffc71d;color:#1f1f1f">AS</span>
        <span class="ws-trigger-meta">
          <span class="ws-trigger-label">Workspace</span>
          <span class="ws-trigger-name" id="ws-active-name">AI Simple</span>
        </span>
        <svg class="ws-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg>
      </button>
      <div class="ws-menu" id="ws-menu" role="menu" hidden>
        <div class="ws-menu-title">Switch workspace</div>
        <div id="ws-options"></div>
        <div class="ws-menu-divider"></div>
        <button type="button" class="ws-create-btn" id="open-create-ws"><span aria-hidden="true">＋</span> Create new workspace</button>
      </div>
    </div>

    <nav class="primary-tabs" role="tablist" aria-orientation="vertical" aria-label="Outlier Lab Studio" id="primary-tablist">
      <div class="nav-group-label">Discover</div>
      <button type="button" class="primary-tab" role="tab" id="tab-today" data-tab="today" aria-selected="true"><span class="primary-tab-left"><span class="nav-ico">◈</span><span>Today</span></span><span class="tab-count" id="tab-count-today">5</span></button>
      <button type="button" class="primary-tab" role="tab" id="tab-feed" data-tab="feed" aria-selected="false"><span class="primary-tab-left"><span class="nav-ico">▶</span><span>Outliers</span></span><span class="tab-count" id="tab-count-feed">__TOTAL_REELS__</span></button>
      <button type="button" class="primary-tab" role="tab" id="tab-seo" data-tab="seo" aria-selected="false"><span class="primary-tab-left"><span class="nav-ico">⌕</span><span>Keywords &amp; SEO</span></span><span class="tab-count">SEO</span></button>

      <div class="nav-group-label">Brain &amp; Strategy</div>
      <button type="button" class="primary-tab" role="tab" id="tab-chat" data-tab="chat" aria-selected="false"><span class="primary-tab-left"><span class="nav-ico">⌘</span><span>AI Chat &amp; Coach</span></span></button>
      <button type="button" class="primary-tab" role="tab" id="tab-character" data-tab="character" aria-selected="false"><span class="primary-tab-left"><span class="nav-ico">★</span><span>Brand Brain</span></span></button>

      <div class="nav-group-label">Create</div>
      <button type="button" class="primary-tab" role="tab" id="tab-ideas" data-tab="ideas" aria-selected="false"><span class="primary-tab-left"><span class="nav-ico">✦</span><span>Ideas &amp; Swipe Hooks</span></span><span class="tab-count" id="tab-count-ideas">__TOTAL_OUTLIERS__</span></button>
      <button type="button" class="primary-tab" role="tab" id="tab-scripts" data-tab="scripts" aria-selected="false"><span class="primary-tab-left"><span class="nav-ico">✎</span><span>Arsenal &amp; Scripts</span></span></button>

      <div class="nav-group-label">Workspace</div>
      <button type="button" class="primary-tab" role="tab" id="tab-channels" data-tab="channels" aria-selected="false"><span class="primary-tab-left"><span class="nav-ico">◎</span><span>Accounts &amp; Tools</span></span></button>
    </nav>

    <div class="sidebar-footer">
      <div class="sidebar-ai-pill" id="sidebar-ai-pill">
        <span class="sidebar-ai-dot" aria-hidden="true"></span>
        <span id="sidebar-ai-label">Instant Local Mode</span>
      </div>
    </div>
  </aside>

  <div class="app-canvas">
    <header class="app-header" id="app-header">
      <div class="topbar-left">
        <button type="button" class="mobile-menu-btn" id="mobile-menu-btn" aria-label="Toggle navigation">☰</button>
        <span class="topbar-title" id="topbar-title">Today</span>
        <span class="topbar-sep" aria-hidden="true">/</span>
        <span class="topbar-sub" id="topbar-sub">AI Simple · __TODAY__</span>
      </div>
      <div class="header-actions">
        <button type="button" class="btn btn-yellow btn-sm" id="open-quick-add">＋ Add Video / Channel</button>
      </div>
    </header>

<main class="app-main" id="main-content">

  <!-- ==================== TAB 1: TODAY ==================== -->
  <section class="tab-panel" id="panel-today" role="tabpanel" aria-labelledby="tab-today">
    <div class="panel-inner">
      <section class="hero-banner" aria-labelledby="hero-heading">
        <div class="hero-copy">
          <div class="hero-eyebrow"><span class="live-dot" aria-hidden="true"></span><span id="hero-eyebrow-text">AI SIMPLE WORKSPACE · __TODAY__</span></div>
          <h1 id="hero-heading">What's <span class="gradient-highlight">outperforming</span> for AI Simple today.</h1>
          <p class="hero-sub" id="hero-sub">Click any outlier for its full 6-tab Video & Story Breakdown, or jump straight into keyword &amp; title scoring.</p>
          <div class="hero-actions">
            <button type="button" class="btn btn-yellow btn-sm" id="hero-seo-btn">⌕ Research Keywords &amp; Titles</button>
            <button type="button" class="btn btn-outline btn-sm" id="hero-socials-btn">Connect Socials (IG/YT/TT/FB)</button>
            <button type="button" class="btn btn-outline btn-sm" id="hero-script-btn">Write a Script</button>
            <button type="button" class="btn btn-outline btn-sm" id="hero-add-btn" hidden>Add</button>
            <button type="button" class="btn btn-outline btn-sm" id="hero-character-btn" hidden>Character</button>
            <button type="button" class="btn btn-outline btn-sm" id="hero-setup-btn" hidden>Setup</button>
          </div>
        </div>
        <aside class="hero-side" aria-label="Workspace quick switcher">
          <div class="hero-ws-pills" id="hero-ws-pills"></div>
          <span style="display:none" id="hero-side-tagline"></span>
          <div class="hero-side-stats">
            <div class="hero-mini-stat"><strong id="hero-stat-outliers">__TOTAL_OUTLIERS__</strong><span>Outliers (≥2×)</span></div>
            <div class="hero-mini-stat"><strong id="hero-stat-channels">__TOTAL_CREATORS__</strong><span>Channels</span></div>
            <div class="hero-mini-stat"><strong id="hero-stat-reels">__TOTAL_REELS__</strong><span>Tracked</span></div>
          </div>
        </aside>
      </section>

      <!-- TOP 5 APPLICABLE OUTLIERS -->
      <section aria-labelledby="spotlight-heading">
        <div class="section-head" style="margin-bottom:16px">
          <div>
            <span class="eyebrow-dot">Start Here · Full 6-Tab Breakdown on Every Card</span>
            <h2 id="spotlight-heading">Top 5 <span class="highlight-mark">outliers</span> to model today.</h2>
          </div>
          <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
            <div class="segmented" id="spotlight-mode" role="group" aria-label="Top outlier mode">
              <button type="button" data-mode="top5" class="active">Top 5</button>
              <button type="button" data-mode="replicable">Replicable (5–15×)</button>
              <button type="button" data-mode="recent">Freshest</button>
            </div>
            <button type="button" class="btn btn-outline btn-sm" id="spotlight-see-all">All Outliers →</button>
          </div>
        </div>
        <div class="spotlight-grid" id="spotlight-grid"></div>
      </section>

      <!-- DAILY VIEW PREDICTIONS -->
      <section aria-labelledby="daily-pred-heading">
        <div class="section-head" style="margin-bottom:14px">
          <div>
            <span class="eyebrow-dot">Daily View Predictions</span>
            <h2 id="daily-pred-heading" style="font-size:24px">High-probability videos to film next.</h2>
          </div>
          <button type="button" class="btn btn-outline btn-sm" id="today-open-seo">Open Keyword &amp; Title Lab →</button>
        </div>
        <div class="card-grid-3" id="daily-predictions-grid"></div>
      </section>

      <!-- WORKSPACE PULSE KPIs -->
      <section class="kpi-grid" id="scope-kpis" aria-label="Workspace metrics">
        <div class="kpi-card"><div class="kpi-label">Outliers (≥2×)</div><div class="kpi-val" id="kpi-outliers">__TOTAL_OUTLIERS__</div><div class="kpi-delta" id="kpi-outliers-delta">__OUTLIER_PCT__% of workspace</div></div>
        <div class="kpi-card"><div class="kpi-label">Top Outlier</div><div class="kpi-val" id="kpi-top">__TOP_REEL_PLAYS__</div><div class="kpi-delta" id="kpi-top-delta">__TOP_REEL_DELTA__</div></div>
        <div class="kpi-card"><div class="kpi-label">Median Plays</div><div class="kpi-val" id="kpi-median">__MEDIAN_OVERALL__</div><div class="kpi-delta" id="kpi-median-delta">Across workspace</div></div>
        <div class="kpi-card"><div class="kpi-label">28d Sample Plays</div><div class="kpi-val" id="kpi-plays">__TOTAL_PLAYS__</div><div class="kpi-delta" id="kpi-plays-delta">All reels combined</div></div>
        <div class="kpi-card"><div class="kpi-label">Transcripts Ready</div><div class="kpi-val" id="kpi-transcripts">__TOTAL_TRANSCRIPTS__</div><div class="kpi-delta" id="kpi-transcripts-delta">Spoken hooks ready</div></div>
      </section>

      <!-- THE SUCCESS FORMULA -->
      <section class="formula-card" aria-labelledby="today-formula-heading">
        <div class="section-head">
          <div>
            <span class="eyebrow-dot">The Success Formula</span>
            <h3 id="today-formula-heading" style="font-size:22px">Winning combination for this workspace.</h3>
          </div>
          <div style="display:flex;gap:8px;flex-wrap:wrap">
            <button type="button" class="btn btn-outline btn-sm" id="today-shuffle-formula">↻ Shuffle</button>
            <button type="button" class="btn btn-yellow btn-sm" id="today-formula-script">Turn Into Script →</button>
          </div>
        </div>
        <div class="formula-equation" id="today-formula-slots"></div>
        <span style="display:none" id="cta-ws-name"></span>
        <span style="display:none"><button id="cta-open-character"></button><button id="cta-open-ideas"></button><button id="cta-open-scripts"></button><button id="cta-open-socials"></button></span>
      </section>
    </div>
  </section>

  <!-- ==================== TAB 2B: KEYWORDS, TAGS, TITLES & SEO (KEYWORD, PACKAGING & SEO SUITE) ==================== -->
  <section class="tab-panel" id="panel-seo" role="tabpanel" aria-labelledby="tab-seo" hidden>
    <div class="panel-inner">
      <div class="section-head">
        <div>
          <span class="eyebrow-dot">Live YouTube Suggest · SERP Competition · VPH · Title &amp; Tag Scoring</span>
          <h2>Keywords, Titles &amp; <span class="highlight-mark">SEO</span> Lab</h2>
          <p>Overall Keyword Scores (0–100), Demand, Competition, Views Per Hour (VPH), Top Ranking Outliers, Title Scoring, Scored Tags, and Thumbnail Critique — with zero credit limits.</p>
        </div>
        <div class="sub-nav" id="seo-subnav" role="tablist">
          <button type="button" data-sub="seo-keywords" class="active">Keyword &amp; SERP Explorer</button>
          <button type="button" data-sub="seo-optimizer">Title, Tags &amp; SEO Optimizer</button>
        </div>
      </div>

      <!-- SUB 1: KEYWORD & SERP EXPLORER -->
      <div class="sub-panel" id="sub-seo-keywords">
        <div class="panel-inner" style="gap:22px">
          <form id="kw-search-form" class="panel-card" style="padding:20px 22px;gap:12px">
            <div style="display:flex;gap:10px;flex-wrap:wrap;align-items:center">
              <input class="filter-search" id="kw-search-input" type="text" value="AI automation" placeholder="Search any keyword or topic (e.g. AI automation, claude code, meta ads creative)..." style="flex:1;min-width:240px;font-size:15px;padding:12px 16px">
              <button type="submit" class="btn btn-yellow" id="kw-search-btn">Search Keyword →</button>
            </div>
            <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
              <span style="font-size:11.5px;font-weight:700;color:var(--ink-3)">Quick ideas:</span>
              <button type="button" class="tag-score-pill" data-quick-kw="AI automation">AI automation</button>
              <button type="button" class="tag-score-pill" data-quick-kw="claude code workflow">claude code workflow</button>
              <button type="button" class="tag-score-pill" data-quick-kw="meta ads creative">meta ads creative</button>
              <button type="button" class="tag-score-pill" data-quick-kw="viral short form hooks">viral short form hooks</button>
              <button type="button" class="tag-score-pill" data-quick-kw="ai agents for business">ai agents for business</button>
              <span id="kw-source-note" style="margin-left:auto;font-size:11.5px;color:var(--ink-3)"></span>
            </div>
          </form>

          <!-- 4 KEYWORD HEADLINE METRICS -->
          <div class="kpi-grid" style="grid-template-columns:repeat(4,minmax(0,1fr))" id="kw-headline-metrics"></div>

          <!-- UNIFIED 2-COLUMN VIEW (KEYWORDS + TAGS & TOP RANKING VIDEOS) -->
          <div class="card-grid-2" style="align-items:start;grid-template-columns:minmax(0,1.25fr) minmax(0,0.95fr)">
            <section class="panel-card" style="min-width:0;padding:20px">
              <div style="display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap">
                <div class="segmented" id="kw-bucket-switch">
                  <button type="button" data-kwb="matching" class="active">Matching</button>
                  <button type="button" data-kwb="related">Related</button>
                  <button type="button" data-kwb="questions">Questions</button>
                </div>
                <button type="button" class="btn btn-outline btn-xs" id="kw-export-csv">↓ CSV</button>
              </div>
              <div style="overflow-x:auto">
                <table class="reels-table" style="font-size:12.5px;table-layout:fixed;width:100%">
                  <thead><tr><th style="width:48%;padding:8px 8px">Keyword</th><th style="width:15%;padding:8px 6px">Vol</th><th style="width:18%;padding:8px 6px">Comp</th><th style="width:11%;padding:8px 6px">Score</th><th style="width:8%;padding:8px 4px"></th></tr></thead>
                  <tbody id="kw-table-body"></tbody>
                </table>
              </div>
            </section>

            <div style="display:flex;flex-direction:column;gap:20px;min-width:0">
              <section class="panel-card">
                <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap">
                  <div>
                    <span class="eyebrow-dot">Scored Tags (0–100)</span>
                    <h3 style="font-size:19px;margin-top:3px">High-opportunity tags</h3>
                  </div>
                  <div style="display:flex;gap:6px">
                    <button type="button" class="btn btn-outline btn-xs" id="kw-copy-tags">Copy All</button>
                    <button type="button" class="btn btn-yellow btn-xs" id="kw-send-optimizer">Send to Optimizer →</button>
                  </div>
                </div>
                <div id="kw-tags-wrap" style="display:flex;flex-wrap:wrap;gap:7px"></div>
              </section>

              <section class="panel-card">
                <div>
                  <span class="eyebrow-dot">Live YouTube SERP · Outliers &amp; VPH</span>
                  <h3 style="font-size:19px;margin-top:3px">Top ranking videos right now</h3>
                </div>
                <div id="kw-top-videos" style="display:flex;flex-direction:column;gap:10px"></div>
              </section>
            </div>
          </div>
        </div>
      </div>

      <!-- SUB 2: TITLE, TAGS, THUMBNAIL & ACTIONABLE SEO OPTIMIZER -->
      <div class="sub-panel" id="sub-seo-optimizer" hidden>
        <div class="card-grid-2" style="align-items:start">
          <section class="panel-card">
            <div style="display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap">
              <div>
                <span class="eyebrow-dot">Zero-Credit Packaging Studio</span>
                <h3 style="font-size:21px;margin-top:2px">Draft &amp; optimize your video</h3>
              </div>
              <button type="button" class="btn btn-yellow btn-sm" id="seo-ai-package-btn">✦ Generate AI Packaging</button>
            </div>
            <div>
              <label class="field-label" for="opt-keyword">Primary Target Keyword</label>
              <input class="field-input" id="opt-keyword" type="text" value="AI automation" placeholder="e.g. AI automation">
            </div>
            <div>
              <div style="display:flex;justify-content:space-between"><label class="field-label" for="opt-title">Video Title (aim for 35–60 chars for mobile)</label><span id="opt-title-chars" style="font-size:11.5px;font-family:var(--font-mono);color:var(--ink-3)">0/60</span></div>
              <input class="field-input" id="opt-title" type="text" value="Stop Building 47-Node AI Automation (Do This 3-Step Fix Instead)" placeholder="Write your title to score it live...">
            </div>
            <div>
              <label class="field-label" for="opt-thumb">Thumbnail Overlay Text (2–4 bold words — don't repeat title)</label>
              <input class="field-input" id="opt-thumb" type="text" value="KILL THE BLOAT" placeholder="e.g. 3-STEP FIX">
            </div>
            <div>
              <label class="field-label" for="opt-desc">Description (put primary keyword in first 180 chars)</label>
              <textarea class="field-textarea" id="opt-desc" rows="4">Most AI automation tutorials hand you a 47-node workflow that breaks by Friday. Here is the exact 3-step AI Simple Stack we use with founders to replace 15 hours of manual ops every week without complex code. Comment SIMPLE for the blueprint.</textarea>
            </div>
            <div>
              <div style="display:flex;justify-content:space-between"><label class="field-label" for="opt-tags">Tags (comma-separated · max 500 chars)</label><span id="opt-tags-chars" style="font-size:11.5px;font-family:var(--font-mono);color:var(--ink-3)">0/500</span></div>
              <textarea class="field-textarea" id="opt-tags" rows="2">ai automation, ai automation for beginners, ai workflow, claude ai automation, business automation, ai agents, simple ai systems, how to automate business</textarea>
              <div id="opt-scored-tags" style="display:flex;flex-wrap:wrap;gap:6px;margin-top:10px"></div>
            </div>
          </section>

          <div style="display:flex;flex-direction:column;gap:20px">
            <section class="panel-card">
              <div style="display:flex;align-items:center;gap:16px">
                <div class="score-ring" id="opt-title-ring">88</div>
                <div>
                  <span class="eyebrow-dot">Title & CTR Prediction Score</span>
                  <h3 style="font-size:21px;margin-top:2px" id="opt-title-verdict">Strong CTR Potential</h3>
                  <p style="font-size:12.5px;color:var(--ink-3)">Scored live across intrigue, clarity, readability, mobile fit, and contrast.</p>
                </div>
              </div>
              <div id="opt-title-checks" style="display:flex;flex-direction:column;gap:7px"></div>
            </section>

            <section class="panel-card">
              <div style="display:flex;align-items:center;justify-content:space-between;gap:12px">
                <div>
                  <span class="eyebrow-dot">Classic Actionable SEO Checklist</span>
                  <h3 style="font-size:19px;margin-top:2px">Search &amp; Discovery Score</h3>
                </div>
                <span class="status-chip live" id="opt-seo-badge">100 / 100</span>
              </div>
              <div id="opt-seo-checklist" style="display:flex;flex-direction:column;gap:7px"></div>
              <div style="padding-top:10px;border-top:1px solid var(--border)">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
                  <strong style="font-size:12.5px">Thumbnail Glanceability Critique</strong>
                  <span class="status-chip" id="opt-thumb-badge">85 / 100</span>
                </div>
                <div id="opt-thumb-notes" style="font-size:12.5px;color:var(--ink-2)"></div>
              </div>
            </section>

            <section class="panel-card" id="opt-ai-variants-card" hidden>
              <span class="eyebrow-dot">AI-Generated Packaging Variants (Click any title to apply)</span>
              <div id="opt-ai-variants" style="display:flex;flex-direction:column;gap:8px"></div>
            </section>
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- ==================== TAB 2: OUTLIER FEED ==================== -->
  <section class="tab-panel" id="panel-feed" role="tabpanel" aria-labelledby="tab-feed" hidden>
    <div class="panel-inner">
      <div class="section-head">
        <div>
          <span class="eyebrow-slash">/ Video Discovery &amp; Analyzed Library · Click Any Video for Full 6-Tab Breakdown /</span>
          <h2>Outlier Feed</h2>
          <p id="niche-summary"></p>
        </div>
        <div style="display:flex;gap:8px;flex-wrap:wrap">
          <button type="button" class="btn btn-outline btn-sm" id="export-feed-btn">↓ Export CSV / JSON</button>
          <button type="button" class="btn btn-yellow btn-sm" id="feed-quick-add">＋ Add Video URL / Channel</button>
        </div>
      </div>

      <nav class="niche-nav" id="niche-nav" aria-label="Niche lists"></nav>

      <div>
        <div class="eyebrow-dot" style="margin-bottom:8px">Filter by tracked channel</div>
        <div class="creators-row" id="creators-row">
          <button class="creator-chip all active" data-creator="__all__" type="button">
            <div class="avatar-fallback" style="display:grid;place-items:center;font-weight:800;font-size:15px" aria-hidden="true">◎</div>
            <div class="chip-info"><div class="chip-name">All channels in view</div><div class="chip-stats" id="all-chip-stats">__TOTAL_REELS__ reels</div></div>
          </button>
          __CREATOR_CHIPS__
          <button type="button" class="creator-chip creator-add-chip" id="add-creator-chip">＋ Track channel</button>
        </div>
      </div>

      <div class="filter-card">
        <div class="filter-row">
          <input type="search" class="filter-search" id="search-input" placeholder="Search hooks, spoken transcripts, captions, topics, or @creators…" aria-label="Search reels">
          <select class="filter-select" id="filter-hook-cat" aria-label="Filter by hook category"><option value="all">All Hook Types</option></select>
          <select class="filter-select" id="filter-format-cat" aria-label="Filter by storytelling format"><option value="all">All Formats</option></select>
          <select class="filter-select" id="filter-topic" aria-label="Filter by topic"><option value="all">All Topics</option></select>
          <select class="filter-select" id="filter-sort" aria-label="Sort reels">
            <option value="ratio:desc">Sort: Outlier Score ↓</option>
            <option value="plays:desc">Sort: Views ↓</option>
            <option value="engagements:desc">Sort: Engagements ↓</option>
            <option value="posted_ts:desc">Sort: Newest ↓</option>
            <option value="duration:asc">Sort: Shortest ↑</option>
          </select>
        </div>
        <div class="filter-row" style="justify-content:space-between">
          <div class="filter-row">
            <div class="band-filter" id="band-filter" role="group" aria-label="Outlier band filter">
              <button type="button" data-band="all" class="active">All</button>
              <button type="button" data-band="breakout"><span class="swatch" style="background:var(--breakout)"></span>Breakout ≥15×</button>
              <button type="button" data-band="strong"><span class="swatch" style="background:var(--yellow)"></span>Replicable 5–15×</button>
              <button type="button" data-band="good"><span class="swatch" style="background:var(--working)"></span>Working 2–5×</button>
              <button type="button" data-band="normal"><span class="swatch" style="background:#b8b5ac"></span>Normal</button>
            </div>
            <button class="toggle-pill" id="toggle-completed" type="button">Hide studied</button>
            <button class="toggle-pill" id="toggle-deleted" type="button">Show removed</button>
            <button class="btn btn-xs btn-outline" id="filter-reset" type="button">Reset</button>
          </div>
          <div class="filter-row">
            <span style="font-size:12.5px;font-weight:700;color:var(--ink-3)" id="row-count">__TOTAL_REELS__</span>
            <span id="filter-status"></span>
            <div class="segmented density-toggle"><button type="button" data-density="comfy" class="active">Comfy</button><button type="button" data-density="compact">Compact</button></div>
            <div class="segmented view-toggle"><button type="button" data-view="table" class="active">☰ Table</button><button type="button" data-view="grid">▦ Grid</button></div>
          </div>
        </div>
      </div>

      <div class="table-view">
        <div class="table-wrap">
          <table class="reels-table">
            <thead>
              <tr>
                <th></th>
                <th data-sort="ratio" class="sort-active sort-desc">Outlier<span class="arrow">▼</span></th>
                <th data-sort="creator_username">Creator<span class="arrow">▼</span></th>
                <th>Spoken Hook &amp; Framework</th>
                <th>Hook / Format</th>
                <th data-sort="plays" class="num">Plays<span class="arrow">▼</span></th>
                <th data-sort="engagements" class="num">Engage<span class="arrow">▼</span></th>
                <th data-sort="duration" class="num">Length<span class="arrow">▼</span></th>
                <th data-sort="posted_ts">Posted<span class="arrow">▼</span></th>
                <th></th>
              </tr>
            </thead>
            <tbody id="reels-tbody"></tbody>
          </table>
        </div>
      </div>

      <div class="grid-view">
        <div class="reel-grid" id="reels-grid"></div>
      </div>
    </div>
  </section>

  <!-- ==================== TAB 3: IDEAS & HOOKS (INBOX + VAULT + CHECKER + COLLECTIONS + PROJECTS) ==================== -->
  <section class="tab-panel" id="panel-ideas" role="tabpanel" aria-labelledby="tab-ideas" hidden>
    <div class="panel-inner">
      <div class="section-head">
        <div>
          <span class="eyebrow-slash">/ Research Vault · Ideas Inbox, Creator Swipe Hooks, Collections &amp; Projects /</span>
          <h2>Ideas, Hooks &amp; Frameworks</h2>
          <p>Auto-extracted content ideas personalized to your Character &amp; Offer, parameterized Mad-Lib hooks, Pre-Flight Checker, and visual taxonomy.</p>
        </div>
        <div class="sub-nav" id="ideas-subnav" role="tablist" aria-label="Ideas and Hooks sub-sections">
          <button type="button" data-sub="ideas-inbox" class="active">Ideas Inbox</button>
          <button type="button" data-sub="hooks-vault">Viral Hook Vault &amp; Checker</button>
          <button type="button" data-sub="collections-lib">Collections &amp; Formats</button>
          <button type="button" data-sub="projects-dir">Projects (Folders)</button>
        </div>
      </div>

      <!-- SUB 1: IDEAS INBOX -->
      <div class="sub-panel" id="sub-ideas-inbox">
        <div class="panel-inner">
          <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap">
            <div class="segmented" id="idea-bucket-switch">
              <button type="button" data-bucket="inbox" class="active">Inbox (<span id="count-ideas-inbox">0</span>)</button>
              <button type="button" data-bucket="shortlist">Shortlist (<span id="count-ideas-shortlist">0</span>)</button>
              <button type="button" data-bucket="discarded">Discarded (<span id="count-ideas-discarded">0</span>)</button>
            </div>
            <input type="search" class="filter-search" id="idea-search" style="max-width:340px" placeholder="Search idea seeds, angles, topics…">
          </div>
          <div class="card-grid-2" id="ideas-grid"></div>
        </div>
      </div>

      <!-- SUB 2: VIRAL HOOK VAULT + HOOK GENIUS PRE-FLIGHT CHECKER -->
      <div class="sub-panel" id="sub-hooks-vault" hidden>
        <div class="panel-inner">
          <section class="checker-box" aria-labelledby="checker-heading">
            <div style="display:flex;flex-direction:column;gap:12px">
              <span class="eyebrow-dot" style="color:var(--yellow)">Hook Genius · Instant Pre-Flight Checker</span>
              <h3 id="checker-heading" style="font-size:25px">Test your hook before you hit record.</h3>
              <p style="font-size:13.5px;color:#ccc">Checks your draft live against winning hook shapes, specificity & curiosity rules, and common scroll-killing traps (bare numbers, vague categories, yes/no openers, >26 words).</p>
              <textarea class="checker-textarea" id="preflight-input" placeholder="Paste or type your spoken opening line...">Stop telling Claude to make your copy engaging — here's the 3-part prompt rule that doubled our reply rate in 14 days.</textarea>
              <div style="display:flex;gap:8px;flex-wrap:wrap">
                <button type="button" class="btn btn-yellow btn-sm" id="preflight-to-script">Build Script From This Hook →</button>
                <button type="button" class="btn btn-ghost-dark btn-sm" id="preflight-sample-trap">Load Trap Example</button>
              </div>
            </div>
            <div class="checker-results" id="preflight-output"></div>
          </section>

          <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap">
            <div>
              <h3 style="font-size:22px">Viral Hook Vault (<span id="hooks-vault-count">0</span>)</h3>
              <p style="font-size:13px;color:var(--ink-3)">Parameterized fill-in-the-blank formulas extracted from your workspace's top performing videos + saved hooks.</p>
            </div>
            <div style="display:flex;gap:8px;flex-wrap:wrap">
              <select class="filter-select" id="vault-hook-cat"><option value="all">All Hook Categories</option></select>
              <button type="button" class="toggle-pill" id="vault-saved-only">Saved hooks only</button>
            </div>
          </div>
          <div class="card-grid-3" id="hooks-vault-grid"></div>
        </div>
      </div>

      <!-- SUB 3: COLLECTIONS & REFERENCE LIBRARY -->
      <div class="sub-panel" id="sub-collections-lib" hidden>
        <div class="panel-inner" id="collections-body"></div>
      </div>

      <!-- SUB 4: PROJECTS / FOLDERS -->
      <div class="sub-panel" id="sub-projects-dir" hidden>
        <div class="panel-inner">
          <div class="panel-card tone-butter" style="flex-direction:row;align-items:flex-end;justify-content:space-between;flex-wrap:wrap">
            <div style="flex:1;min-width:240px">
              <span class="eyebrow-dot">Inspiration Folders</span>
              <h3 style="font-size:22px;margin-top:4px">Create a Project folder</h3>
              <p style="font-size:13.5px;color:var(--ink-2)">Group outlier breakdowns by campaign, series, or client (e.g. "About Me", "AI Hooks", "Q4 Paid Ads").</p>
            </div>
            <form id="new-project-form" style="display:flex;gap:8px;flex-wrap:wrap;align-items:center">
              <input class="field-input" id="new-project-name" type="text" required placeholder="Folder name…" style="width:240px">
              <button type="submit" class="btn btn-dark btn-sm">＋ Create Folder</button>
            </form>
          </div>
          <div class="card-grid-2" id="projects-grid"></div>
        </div>
      </div>
    </div>
  </section>

  <!-- ==================== TAB 4: STRATEGY & SCRIPTS ==================== -->
  <!-- ==================== TAB: AI CHAT & COACH (CLAUDE / CODEX + ZERODRIVE BRAIN) ==================== -->
  <section class="tab-panel" id="panel-chat" role="tabpanel" aria-labelledby="tab-chat" hidden>
    <div class="panel-inner">
      <div class="section-head">
        <div>
          <span class="eyebrow-dot">Local Claude &amp; Codex Subscription · Connected to Your Brand Brain &amp; ZeroDrive</span>
          <h2>AI Studio <span class="highlight-mark">Chat</span> &amp; Coach</h2>
          <p>Converse directly with your workspace's Memories, Founder Persona, Customer Avatars, Products &amp; Offers, and Asset Library — and save any output or extracted memory straight to ZeroDrive.</p>
        </div>
        <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
          <div class="segmented" id="chat-mode-switch">
            <button type="button" data-chatmode="chief_of_staff" class="active">Chief of Staff</button>
            <button type="button" data-chatmode="persona_coach">Persona Coach</button>
            <button type="button" data-chatmode="offer_architect">Offer Architect</button>
          </div>
          <select id="chat-provider-select" class="field-select" style="width:auto;padding:7px 12px;font-size:12.5px" aria-label="Chat AI Provider">
            <option value="claude">Claude CLI</option>
            <option value="codex">Codex CLI</option>
          </select>
        </div>
      </div>

      <div class="chat-shell">
        <div class="panel-card" style="gap:14px">
          <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap">
            <span class="status-chip live" id="chat-context-pill">Brain Loaded</span>
            <div style="display:flex;gap:6px;flex-wrap:wrap">
              <button type="button" class="btn btn-outline btn-xs" id="chat-clear-btn">New Chat</button>
              <button type="button" class="btn btn-outline btn-xs" id="chat-save-zd-btn">☁ Save Transcript to ZeroDrive</button>
            </div>
          </div>
          <div id="chat-attached-bar" style="display:flex;flex-wrap:wrap;gap:6px"></div>
          <div class="chat-log" id="chat-log"></div>
          <div style="display:flex;flex-wrap:wrap;gap:6px" id="chat-quick-prompts">
            <button type="button" class="tag-score-pill" data-chat-prompt="Interview me to extract a powerful origin story and 5 original account hooks for my Founder Persona.">Extract Story &amp; Hooks</button>
            <button type="button" class="tag-score-pill" data-chat-prompt="Audit my current Products & Offers using S/A/B/C Offer Modalities and show me 3 ways to double perceived value.">Audit Offer Modalities</button>
            <button type="button" class="tag-score-pill" data-chat-prompt="Give me 3 high-leverage content angles this week combining our Customer Avatar's 3 false beliefs with our core offer.">Plan This Week's Content</button>
            <button type="button" class="tag-score-pill" data-chat-prompt="Turn our primary offer into a 5-minute mini-webinar pitch script using our Founder Persona voice.">Draft 5-Min Pitch</button>
          </div>
          <form id="chat-form" style="display:flex;gap:10px;align-items:flex-end">
            <textarea class="field-textarea" id="chat-input" rows="2" placeholder="Ask your Chief of Staff, run a Persona Coaching session, or draft with your Brand Brain..." style="flex:1"></textarea>
            <button type="submit" class="btn btn-yellow" id="chat-send-btn">Send →</button>
          </form>
        </div>

        <aside style="display:flex;flex-direction:column;gap:16px">
          <div class="panel-card" style="padding:18px;gap:10px">
            <span class="eyebrow-dot">Active Context</span>
            <div id="chat-brain-summary" style="font-size:12.5px;color:var(--ink-2);display:flex;flex-direction:column;gap:6px"></div>
            <button type="button" class="btn btn-outline btn-xs" id="chat-open-brain">Edit Brand Brain →</button>
          </div>
          <div class="panel-card" style="padding:18px;gap:10px">
            <span class="eyebrow-dot">Attach From Asset Library</span>
            <div id="chat-asset-picker" style="display:flex;flex-direction:column;gap:6px"></div>
          </div>
        </aside>
      </div>
    </div>
  </section>

  <!-- ==================== TAB 4: ARSENAL & SCRIPTS ==================== -->
  <section class="tab-panel" id="panel-scripts" role="tabpanel" aria-labelledby="tab-scripts" hidden>
    <div class="panel-inner">
      <div class="section-head">
        <div>
          <span class="eyebrow-slash">/ One-to-Many Presentations · Emails · Socials (36 Formats) · Script Builder · Strategy Audit /</span>
          <h2>Creative Arsenal &amp; Scripts</h2>
          <p>Turn your Brand Brain, Founder Persona, Customer Avatars, and Offer Stack into complete presentations, email sequences, social content, and scripts.</p>
        </div>
        <div class="sub-nav" id="scripts-subnav" role="tablist">
          <button type="button" data-sub="arsenal-presentations" class="active">Presentations</button>
          <button type="button" data-sub="arsenal-emails">Emails</button>
          <button type="button" data-sub="arsenal-socials">Socials (36 Formats)</button>
          <button type="button" data-sub="script-builder">4-Step Script Builder</button>
          <button type="button" data-sub="strategy-audit">Strategy Audit</button>
          <button type="button" data-sub="saved-scripts">Saved (<span id="saved-scripts-count">0</span>)</button>
        </div>
      </div>

      <!-- ARSENAL 1: ONE-TO-MANY PRESENTATIONS -->
      <div class="sub-panel" id="sub-arsenal-presentations">
        <div class="card-grid-2" style="align-items:start">
          <form id="ars-pres-form" class="panel-card">
            <span class="eyebrow-dot">One-to-Many Presentations</span>
            <h3 style="font-size:22px">Webinars, VSLs &amp; Stage Talks</h3>
            <div class="form-row-2">
              <div>
                <label class="field-label" for="ap-format">Presentation Format</label>
                <select class="field-select" id="ap-format">
                  <option>Perfect Webinar</option>
                  <option>Mini-Workshop / Masterclass</option>
                  <option>Funny VSL Explainer</option>
                  <option>Analogy VSL Explainer</option>
                  <option>AGORA Style VSL</option>
                  <option>Continuity VSL</option>
                  <option>Keynote / Stage Talk</option>
                </select>
              </div>
              <div>
                <label class="field-label" for="ap-offer">Offer Stack to Pitch</label>
                <select class="field-select" id="ap-offer"></select>
              </div>
            </div>
            <div class="form-row-2">
              <div><label class="field-label" for="ap-avatar">Target Customer Avatar</label><select class="field-select" id="ap-avatar"></select></div>
              <div><label class="field-label" for="ap-story-fmt">Lead Story Arc</label><select class="field-select" id="ap-story-fmt"><option>Epiphany Bridge</option><option>Three-Act Structure</option><option>Before vs. After</option><option>Case Study Proof</option><option>Contrarian Myth-Buster</option></select></div>
            </div>
            <div><label class="field-label" for="ap-topic">Big Promise / Presentation Topic</label><textarea class="field-textarea" id="ap-topic" rows="2" required placeholder="e.g. How founders replace 15 hrs/week of manual ops with 3 simple AI workflows without writing code"></textarea></div>
            <div><label class="field-label" for="ap-notes">Extra direction (optional)</label><input class="field-input" id="ap-notes" type="text" placeholder="e.g. Emphasize S-tier Done-For-You bonus and 30-day guarantee"></div>
            <button type="submit" class="btn btn-yellow" id="ap-submit">✦ Generate Full Presentation →</button>
          </form>
          <section class="panel-card" style="min-height:360px">
            <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap">
              <strong style="font-size:15px">Presentation Blueprint &amp; Script</strong>
              <div style="display:flex;gap:6px">
                <button type="button" class="btn btn-outline btn-xs" id="ap-copy">Copy</button>
                <button type="button" class="btn btn-outline btn-xs" id="ap-save-lib">Save to Library</button>
                <button type="button" class="btn btn-yellow btn-xs" id="ap-save-zd">☁ Save to ZeroDrive</button>
              </div>
            </div>
            <textarea class="field-textarea" id="ap-output" rows="16" placeholder="Your generated presentation (Hook, Origin Story, 3 False-Belief Secrets, Transition, S/A/B/C Offer Stack & Close) will appear here..."></textarea>
          </section>
        </div>
      </div>

      <!-- ARSENAL 2: ONE-TO-MANY EMAILS -->
      <div class="sub-panel" id="sub-arsenal-emails" hidden>
        <div class="card-grid-2" style="align-items:start">
          <form id="ars-email-form" class="panel-card">
            <span class="eyebrow-dot">One-to-Many Emails</span>
            <h3 style="font-size:22px">Broadcasts &amp; Automated Sequences</h3>
            <div class="form-row-2">
              <div>
                <label class="field-label" for="ae-format">Email Framework</label>
                <select class="field-select" id="ae-format">
                  <option>Daily Seinfeld Story Email</option>
                  <option>Soap Opera Sequence (3-Day)</option>
                  <option>Problem → Agitate → Mechanism</option>
                  <option>Contrarian Enemy Callout</option>
                  <option>Case Study Proof Email</option>
                  <option>Product Launch / Cart Close</option>
                </select>
              </div>
              <div><label class="field-label" for="ae-offer">Offer / CTA Target</label><select class="field-select" id="ae-offer"></select></div>
            </div>
            <div class="form-row-2">
              <div><label class="field-label" for="ae-avatar">Target Customer Avatar</label><select class="field-select" id="ae-avatar"></select></div>
              <div><label class="field-label" for="ae-voice">Founder Voice</label><select class="field-select" id="ae-voice"></select></div>
            </div>
            <div><label class="field-label" for="ae-topic">Story Seed or Angle</label><textarea class="field-textarea" id="ae-topic" rows="2" required placeholder="e.g. A founder spent $14K on AI tools last quarter and still runs sales follow-ups manually"></textarea></div>
            <div><label class="field-label" for="ae-notes">Extra notes (optional)</label><input class="field-input" id="ae-notes" type="text" placeholder="e.g. Include a punchy PS linking to the assessment"></div>
            <button type="submit" class="btn btn-yellow" id="ae-submit">✦ Generate Email(s) →</button>
          </form>
          <section class="panel-card" style="min-height:360px">
            <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap">
              <strong style="font-size:15px">Subject Lines &amp; Email Copy</strong>
              <div style="display:flex;gap:6px">
                <button type="button" class="btn btn-outline btn-xs" id="ae-copy">Copy</button>
                <button type="button" class="btn btn-outline btn-xs" id="ae-save-lib">Save to Library</button>
                <button type="button" class="btn btn-yellow btn-xs" id="ae-save-zd">☁ Save to ZeroDrive</button>
              </div>
            </div>
            <textarea class="field-textarea" id="ae-output" rows="16" placeholder="Subject line options, preview text, story body, and PS CTA will appear here..."></textarea>
          </section>
        </div>
      </div>

      <!-- ARSENAL 3: ONE-TO-MANY SOCIALS (ALL 36 STORYTELLING FORMATS + SEPARATE ACCOUNT HOOKS) -->
      <div class="sub-panel" id="sub-arsenal-socials" hidden>
        <div class="card-grid-2" style="align-items:start">
          <form id="ars-social-form" class="panel-card">
            <span class="eyebrow-dot">One-to-Many Socials · 36 Storytelling Formats</span>
            <h3 style="font-size:22px">Reels, Shorts, Carousels &amp; Posts</h3>
            <div class="form-row-2">
              <div>
                <label class="field-label" for="as-platform">Platform &amp; Format</label>
                <select class="field-select" id="as-platform">
                  <option>Instagram Reel</option>
                  <option>YouTube Short</option>
                  <option>YouTube Long-Form</option>
                  <option>TikTok</option>
                  <option>Facebook Reel / Post</option>
                  <option>Carousel / Swipe Post</option>
                  <option>Text Post (IG/FB/LI/X/Threads)</option>
                  <option>Broadcast Channel Message</option>
                </select>
              </div>
              <div>
                <label class="field-label" for="as-story-fmt">Storytelling Format (36 Frameworks)</label>
                <select class="field-select" id="as-story-fmt"></select>
              </div>
            </div>
            <div class="form-row-2">
              <div><label class="field-label" for="as-avatar">Target Customer Avatar</label><select class="field-select" id="as-avatar"></select></div>
              <div><label class="field-label" for="as-acct-hook">Your Brand Account Hook (Separate from Swipes)</label><select class="field-select" id="as-acct-hook"></select></div>
            </div>
            <div><label class="field-label" for="as-topic">Core Idea / Angle</label><textarea class="field-textarea" id="as-topic" rows="2" required placeholder="e.g. Why automating a broken workflow just creates chaos faster"></textarea></div>
            <button type="submit" class="btn btn-yellow" id="as-submit">✦ Generate Social Asset →</button>
          </form>
          <section class="panel-card" style="min-height:360px">
            <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap">
              <strong style="font-size:15px">Generated Script / Post</strong>
              <div style="display:flex;gap:6px">
                <button type="button" class="btn btn-outline btn-xs" id="as-copy">Copy</button>
                <button type="button" class="btn btn-outline btn-xs" id="as-save-lib">Save to Library</button>
                <button type="button" class="btn btn-yellow btn-xs" id="as-save-zd">☁ Save to ZeroDrive</button>
              </div>
            </div>
            <textarea class="field-textarea" id="as-output" rows="16" placeholder="3 original hooks + beat-by-beat script/slides + visual & caption cues will appear here..."></textarea>
          </section>
        </div>
      </div>

      <!-- SUB 1: CONTENT STRATEGY AUDIT -->
      <div class="sub-panel" id="sub-strategy-audit" hidden>
        <div class="panel-inner">
          <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap">
            <div class="segmented" id="audit-dim-switch" role="group" aria-label="Audit dimension">
              <button type="button" data-dim="topics" class="active">Performance by Topics</button>
              <button type="button" data-dim="hooks">Performance by Hooks</button>
              <button type="button" data-dim="formats">Performance by Formats</button>
              <button type="button" data-dim="tactics">Scriptwriting Tactics</button>
              <button type="button" data-dim="kennedy">7 Magnetism Elements</button>
            </div>
            <span class="status-chip live">Computed live · 0 credits</span>
          </div>

          <div class="audit-layout">
            <div class="panel-card">
              <h3 id="audit-list-title" style="font-size:21px">Median Outlier Multiple by Topic</h3>
              <div id="audit-bars" style="display:flex;flex-direction:column;gap:8px"></div>
            </div>
            <div class="panel-card tone-cream" id="audit-drilldown" style="min-width:0;overflow:hidden"></div>
          </div>

          <section class="formula-card">
            <div class="section-head">
              <div>
                <span class="eyebrow-dot">The Success Formula</span>
                <h3 style="font-size:22px">Highest-lift content recipe for this workspace</h3>
              </div>
              <div style="display:flex;gap:8px">
                <button type="button" class="btn btn-outline btn-sm" id="audit-shuffle-formula">↻ Shuffle</button>
                <button type="button" class="btn btn-yellow btn-sm" id="audit-formula-script">Build Script From Formula →</button>
              </div>
            </div>
            <div class="formula-equation" id="audit-formula-slots"></div>
          </section>
        </div>
      </div>

      <!-- SUB 2: 4-STEP SCRIPT BUILDER -->
      <div class="sub-panel" id="sub-script-builder" hidden>
        <div class="panel-inner">
          <div class="wizard-steps" id="script-wizard-steps">
            <button type="button" class="wizard-step active" data-wstep="1"><span class="wizard-num">1</span><div><strong style="display:block;font-size:13px">Topic &amp; Source</strong><small style="opacity:0.7;font-size:11px">Idea or fix draft</small></div></button>
            <button type="button" class="wizard-step" data-wstep="2"><span class="wizard-num">2</span><div><strong style="display:block;font-size:13px">Research Brief</strong><small style="opacity:0.7;font-size:11px">Facts &amp; contrast</small></div></button>
            <button type="button" class="wizard-step" data-wstep="3"><span class="wizard-num">3</span><div><strong style="display:block;font-size:13px">6 Hook Drafts</strong><small style="opacity:0.7;font-size:11px">Creator-inspired</small></div></button>
            <button type="button" class="wizard-step" data-wstep="4"><span class="wizard-num">4</span><div><strong style="display:block;font-size:13px">Line-by-Line Script</strong><small style="opacity:0.7;font-size:11px">Persona + beats</small></div></button>
          </div>

          <div class="panel-card" id="script-wizard-body"></div>
        </div>
      </div>

      <!-- SUB 3: SAVED SCRIPTS -->
      <div class="sub-panel" id="sub-saved-scripts" hidden>
        <div class="card-grid-2" id="saved-scripts-grid"></div>
      </div>
    </div>
  </section>

  <!-- ==================== TAB 5: BRAND BRAIN (MEMORIES, FOUNDER PERSONA, AVATARS, OFFERS, ASSETS) ==================== -->
  <section class="tab-panel" id="panel-character" role="tabpanel" aria-labelledby="tab-character" hidden>
    <div class="panel-inner">
      <div class="section-head">
        <div>
          <span class="eyebrow-slash">/ Workspace Brain · ZeroDrive-Backed Context for <strong id="char-ws-label">AI Simple</strong> /</span>
          <h2>Brand <span class="highlight-mark">Brain</span> &amp; Offer Architecture</h2>
          <p>Everything your AI Studio, Arsenal, and Script Builder need to know — Memories, Founder Persona, Customer Avatars, Products &amp; Offers (with S/A/B/C Offer Modalities), and your Asset Library.</p>
        </div>
        <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center">
          <span class="status-chip live" id="char-completeness-badge">Ready</span>
          <button type="button" class="btn btn-outline btn-sm" id="brain-sync-zd-btn">☁ Sync Brain to ZeroDrive</button>
          <button type="button" class="btn btn-outline btn-sm" id="export-character-md">↓ Copy Bible</button>
          <button type="button" class="btn btn-yellow btn-sm" id="save-character-btn">Save Brain ✓</button>
        </div>
      </div>

      <div class="sub-nav" id="brain-subnav" role="tablist">
        <button type="button" data-sub="brain-persona" class="active">Founder Persona</button>
        <button type="button" data-sub="brain-memories">Memories (<span id="mem-count-badge">0</span>)</button>
        <button type="button" data-sub="brain-avatars">Customer Avatars (<span id="av-count-badge">0</span>)</button>
        <button type="button" data-sub="brain-offers">Products &amp; Offers (<span id="off-count-badge">0</span>)</button>
        <button type="button" data-sub="brain-assets">Asset Library (<span id="asset-count-badge">0</span>)</button>
      </div>

      <!-- BRAIN SUB 1: FOUNDER PERSONA (IDENTITY, VOICES, ACCOUNT STORIES & HOOKS, COACHING BOT) -->
      <div class="sub-panel" id="sub-brain-persona">
        <div class="panel-inner" style="gap:20px">
          <div style="display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap">
            <div class="segmented" id="persona-inner-switch">
              <button type="button" data-pview="identity" class="active">Identity &amp; Magnetism</button>
              <button type="button" data-pview="voices">Voices (<span id="voices-count">0</span>)</button>
              <button type="button" data-pview="account-hooks">Account Stories &amp; Hooks (<span id="acct-hooks-count">0</span>)</button>
              <button type="button" data-pview="coach-bot">Coaching Bot</button>
            </div>
            <button type="button" class="btn btn-outline btn-sm" id="ai-gen-persona-btn">✦ Generate / Expand Persona with AI</button>
          </div>

          <div id="pview-identity" style="display:flex;flex-direction:column;gap:16px">
            <!-- STEP 1: 2-MINUTE OFFER CLARITY (OPEN BY DEFAULT) -->
            <details class="calm-details" open>
              <summary><span>1. Core Positioning &amp; Offer Summary</span><span class="status-chip">Positioning</span></summary>
              <div style="display:flex;flex-direction:column;gap:14px">
                <div class="form-row-2">
                  <div><label class="field-label" for="ch-what-sell">What do you sell?</label><textarea class="field-textarea" id="ch-what-sell" rows="2"></textarea></div>
                  <div><label class="field-label" for="ch-who-sell">Who do you sell it to?</label><textarea class="field-textarea" id="ch-who-sell" rows="2"></textarea></div>
                </div>
                <div class="form-row-2">
                  <div><label class="field-label" for="ch-transform">Core Transformation / Promise</label><input class="field-input" id="ch-transform" type="text"></div>
                  <div><label class="field-label" for="ch-cta">Primary Content CTA / Conversion Mechanism</label><input class="field-input" id="ch-cta" type="text"></div>
                </div>
              </div>
            </details>

            <!-- STEP 2: FOUNDER ARCHETYPE & POLARITY -->
            <details class="calm-details" open>
              <summary><span>2. Founder Persona Archetype, Identity &amp; Polarity</span><span class="status-chip muted">Identity</span></summary>
              <div style="display:flex;flex-direction:column;gap:14px">
                <div class="archetype-grid" id="archetype-grid"></div>
                <div class="form-row-2" style="margin-top:4px">
                  <div><label class="field-label" for="ch-superhero">Persona Name / Identity Title</label><input class="field-input" id="ch-superhero" type="text" placeholder="e.g. The Systems Architect"></div>
                  <div><label class="field-label" for="ch-mighty">The Mighty Theme (Your Core Obsession)</label><input class="field-input" id="ch-mighty" type="text"></div>
                </div>
                <div class="form-row-2">
                  <div><label class="field-label" for="ch-stand-for">What You Stand FOR (Values &amp; Pillars)</label><textarea class="field-textarea" id="ch-stand-for" rows="2"></textarea></div>
                  <div><label class="field-label" for="ch-stand-against">What You Stand AGAINST (Named Enemies &amp; Polarity)</label><textarea class="field-textarea" id="ch-stand-against" rows="2"></textarea></div>
                </div>
              </div>
            </details>

            <!-- STEP 3: THE 7 MAGNETISM ELEMENTS -->
            <details class="calm-details">
              <summary><span>3. The 7 Magnetism Elements (Origin, Parables, Miracles, Language, Dogma, Enemies, Flaws)</span><span class="status-chip muted">Expand</span></summary>
              <div style="display:flex;flex-direction:column;gap:14px">
                <div class="card-grid-2">
                  <div><label class="field-label" for="k7-origin">1. Origin Story / Backstory</label><textarea class="field-textarea" id="k7-origin" rows="3"></textarea></div>
                  <div><label class="field-label" for="k7-parables">2. Signature Parables</label><textarea class="field-textarea" id="k7-parables" rows="3"></textarea></div>
                  <div><label class="field-label" for="k7-miracles">3. Miracles (Verifiable Proof)</label><textarea class="field-textarea" id="k7-miracles" rows="3"></textarea></div>
                  <div><label class="field-label" for="k7-language">4. Insider Language</label><textarea class="field-textarea" id="k7-language" rows="3"></textarea></div>
                  <div><label class="field-label" for="k7-dogma">5. Dogma (Non-Negotiable Rules)</label><textarea class="field-textarea" id="k7-dogma" rows="3"></textarea></div>
                  <div><label class="field-label" for="k7-enemies">6. Named Enemies</label><textarea class="field-textarea" id="k7-enemies" rows="3"></textarea></div>
                </div>
                <div><label class="field-label" for="k7-flaws">7. Core Flaw &amp; Evolution</label><textarea class="field-textarea" id="k7-flaws" rows="2"></textarea></div>
              </div>
            </details>

            <!-- STEP 4: REPEATABLE SIGNATURE TRAITS + VOICE + PROFITS -->
            <details class="calm-details">
              <summary><span>4. Signature Traits (7 Repeatable Facts), Writing Cadence &amp; Buyer Language</span><span class="status-chip muted">Expand</span></summary>
              <div class="card-grid-2">
                <div style="display:flex;flex-direction:column;gap:12px">
                  <p style="font-size:13px;color:var(--ink-2)">7 signature facts repeated across your content until your audience knows them cold.</p>
                  <textarea class="field-textarea" id="ch-bond" rows="7"></textarea>
                  <div><label class="field-label" for="ch-style">Default Writing Style &amp; Cadence</label><textarea class="field-textarea" id="ch-style" rows="3"></textarea></div>
                </div>
                <div style="display:flex;flex-direction:column;gap:10px">
                  <div class="form-row-2">
                    <div><label class="field-label" for="pr-pain">P — Pain</label><textarea class="field-textarea" id="pr-pain" rows="2"></textarea></div>
                    <div><label class="field-label" for="pr-results">R — Results</label><textarea class="field-textarea" id="pr-results" rows="2"></textarea></div>
                    <div><label class="field-label" for="pr-obstacles">O — Obstacles</label><textarea class="field-textarea" id="pr-obstacles" rows="2"></textarea></div>
                    <div><label class="field-label" for="pr-fear">F — Fear</label><textarea class="field-textarea" id="pr-fear" rows="2"></textarea></div>
                    <div><label class="field-label" for="pr-identity">I — Identity</label><textarea class="field-textarea" id="pr-identity" rows="2"></textarea></div>
                    <div><label class="field-label" for="pr-triggers">T — Triggers</label><textarea class="field-textarea" id="pr-triggers" rows="2"></textarea></div>
                  </div>
                  <div><label class="field-label" for="pr-dreams">S — Dreams</label><input class="field-input" id="pr-dreams" type="text"></div>
                </div>
              </div>
            </details>
          </div>

          <!-- PERSONA INNER 2: VOICES -->
          <div id="pview-voices" hidden style="display:flex;flex-direction:column;gap:16px">
            <div class="card-grid-2" style="align-items:start">
              <form id="voice-add-form" class="panel-card">
                <span class="eyebrow-dot">Channel Voices</span>
                <h3 style="font-size:20px">Add a Voice Style Sheet</h3>
                <div class="form-row-2">
                  <div><label class="field-label" for="v-name">Voice Name</label><input class="field-input" id="v-name" type="text" required placeholder="e.g. Direct Video Voice"></div>
                  <div><label class="field-label" for="v-type">Channel Type</label><select class="field-select" id="v-type"><option>Video</option><option>Writing</option><option>Email</option><option>Social</option><option>Stage</option><option>Ads</option><option>Coaching</option></select></div>
                </div>
                <div><label class="field-label" for="v-notes">Style Rules &amp; Cadence</label><textarea class="field-textarea" id="v-notes" rows="3" required placeholder="Short punchy sentences, zero fluff, open with a concrete mistake..."></textarea></div>
                <div><label class="field-label" for="v-sample">Sample Passage / Transcript (optional)</label><textarea class="field-textarea" id="v-sample" rows="3" placeholder="Paste a real sample in this voice..."></textarea></div>
                <button type="submit" class="btn btn-yellow btn-sm" style="align-self:flex-start">＋ Save Voice</button>
              </form>
              <div id="voices-list" style="display:flex;flex-direction:column;gap:12px"></div>
            </div>
          </div>

          <!-- PERSONA INNER 3: SEPARATE ACCOUNT STORY & HOOK INVENTORY -->
          <div id="pview-account-hooks" hidden style="display:flex;flex-direction:column;gap:16px">
            <div class="panel-card" style="background:var(--yellow-tint);border-color:rgba(255,199,29,0.55);padding:16px 20px;flex-direction:row;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px">
              <div><strong style="font-size:14px">Your Workspace's Private Story &amp; Hook Inventory</strong><p style="font-size:12.5px;color:var(--ink-2)">Kept 100% separate from other creators' swipe hooks and templates — these belong exclusively to this workspace's Founder Persona.</p></div>
              <button type="button" class="btn btn-yellow btn-sm" id="ai-gen-acct-hooks-btn">✦ Generate 10 Account Hooks</button>
            </div>
            <div class="card-grid-2" style="align-items:start">
              <form id="story-add-form" class="panel-card">
                <span class="eyebrow-dot">Tell a Story &amp; Capture Hooks</span>
                <h3 style="font-size:20px">Add Brand Story / Hook</h3>
                <div><label class="field-label" for="st-title">Story Title</label><input class="field-input" id="st-title" type="text" required placeholder="e.g. The 2-Hour Launch Rescue"></div>
                <div><label class="field-label" for="st-false-belief">False Belief Destroyed</label><input class="field-input" id="st-false-belief" type="text" placeholder="e.g. Thinking more AI tools equals more leverage"></div>
                <div><label class="field-label" for="st-body">Story Narrative (Before → Struggle → Epiphany → Result)</label><textarea class="field-textarea" id="st-body" rows="3" required placeholder="Tell the concrete story..."></textarea></div>
                <div><label class="field-label" for="st-hooks">Account Hooks From This Story (one per line)</label><textarea class="field-textarea" id="st-hooks" rows="3" placeholder="Last Tuesday an 8-figure founder called me 2 hours before launch..."></textarea></div>
                <button type="submit" class="btn btn-yellow btn-sm" style="align-self:flex-start">＋ Save to Account Inventory</button>
              </form>
              <div style="display:flex;flex-direction:column;gap:14px">
                <div class="panel-card">
                  <strong style="font-size:15px">Saved Account Hooks (<span id="acct-hooks-list-count">0</span>)</strong>
                  <div id="acct-hooks-list" style="display:flex;flex-direction:column;gap:8px;max-height:280px;overflow-y:auto"></div>
                </div>
                <div class="panel-card">
                  <strong style="font-size:15px">Saved Brand Stories (<span id="acct-stories-count">0</span>)</strong>
                  <div id="acct-stories-list" style="display:flex;flex-direction:column;gap:8px;max-height:260px;overflow-y:auto"></div>
                </div>
              </div>
            </div>
          </div>

          <!-- PERSONA INNER 4: COACHING BOT -->
          <div id="pview-coach-bot" hidden>
            <div class="card-grid-2" style="align-items:start">
              <form id="coach-bot-form" class="panel-card">
                <span class="eyebrow-dot">Founder Persona Coaching Bot</span>
                <h3 style="font-size:20px">Configure Your Interactive Coach</h3>
                <div><label class="field-label" for="cb-bio">Coach Bio (400 chars)</label><textarea class="field-textarea" id="cb-bio" rows="2" placeholder="Direct systems architect helping founders diagnose bottlenecks before adding AI tools."></textarea></div>
                <div><label class="field-label" for="cb-rules">Answering Rules &amp; Guardrails</label><textarea class="field-textarea" id="cb-rules" rows="3" placeholder="Always diagnose before prescribing. Ask 1 sharp clarifying question before giving a 3-step plan."></textarea></div>
                <div><label class="field-label" for="cb-starters">Starter Questions (one per line)</label><textarea class="field-textarea" id="cb-starters" rows="3" placeholder="Where is my biggest AI bottleneck right now?&#10;Help me extract 5 stories from my business.&#10;How should I structure my offer stack?"></textarea></div>
                <div class="form-row-2">
                  <div><label class="field-label" for="cb-cta-label">Offer CTA Button</label><input class="field-input" id="cb-cta-label" type="text" placeholder="Take the AI Bottleneck Assessment"></div>
                  <div><label class="field-label" for="cb-cta-url">Offer CTA URL</label><input class="field-input" id="cb-cta-url" type="url" placeholder="https://aisimple.co"></div>
                </div>
                <div style="display:flex;gap:8px;flex-wrap:wrap">
                  <button type="submit" class="btn btn-yellow btn-sm">Save Bot Config ✓</button>
                  <button type="button" class="btn btn-dark btn-sm" id="launch-coach-chat-btn">Test Coaching Bot Live →</button>
                </div>
              </form>
              <div class="panel-card tone-cream">
                <span class="eyebrow-dot">Live Preview</span>
                <h3 style="font-size:20px" id="cb-preview-title">AI Simple Coach</h3>
                <p style="font-size:13.5px;color:var(--ink-2)" id="cb-preview-bio"></p>
                <div id="cb-preview-starters" style="display:flex;flex-direction:column;gap:8px;margin-top:6px"></div>
                <div id="cb-preview-cta" style="margin-top:8px"></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- BRAIN SUB 2: MEMORIES -->
      <div class="sub-panel" id="sub-brain-memories" hidden>
        <div class="card-grid-2" style="align-items:start;grid-template-columns:minmax(0,0.9fr) minmax(0,1.25fr)">
          <form id="memory-add-form" class="panel-card">
            <span class="eyebrow-dot">Feed Your Workspace Brain</span>
            <h3 style="font-size:21px">Add a Memory</h3>
            <div><label class="field-label" for="mem-title">Short Title</label><input class="field-input" id="mem-title" type="text" required placeholder="e.g. Core Pricing Rule / Client Proof"></div>
            <div class="form-row-2">
              <div>
                <label class="field-label" for="mem-cat">Category</label>
                <select class="field-select" id="mem-cat">
                  <option>About Your Business</option><option>Your Goals</option><option>People</option><option>Decisions Made</option>
                  <option>From Conversations</option><option>Preferences</option><option>Audience</option><option>Projects</option>
                  <option>Offers</option><option>Leads</option><option>Your Corrections</option><option>Other</option>
                </select>
              </div>
              <div>
                <label class="field-label" for="mem-scope">Scope</label>
                <select class="field-select" id="mem-scope"><option value="workspace">Workspace Shared</option><option value="personal">Personal (User-Level)</option></select>
              </div>
            </div>
            <div><label class="field-label" for="mem-content">Memory Content (up to 2,000 chars)</label><textarea class="field-textarea" id="mem-content" rows="4" required placeholder="Facts about your business, rules to follow, client wins, or things AI should never forget..."></textarea></div>
            <button type="submit" class="btn btn-yellow btn-sm" style="align-self:flex-start">Save to Memories ✓</button>
          </form>

          <section class="panel-card">
            <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap">
              <strong style="font-size:16px">What Your Brain Knows (<span id="mem-list-count">0</span>)</strong>
              <div style="display:flex;gap:8px;flex-wrap:wrap">
                <input class="filter-search" id="mem-search" type="search" placeholder="Search memories..." style="min-width:160px;padding:6px 10px;font-size:12.5px">
                <select class="field-select" id="mem-filter-cat" style="width:auto;padding:6px 10px;font-size:12px"><option value="all">All Categories</option></select>
              </div>
            </div>
            <div id="memories-list" style="display:flex;flex-direction:column;gap:10px;max-height:520px;overflow-y:auto"></div>
          </section>
        </div>
      </div>

      <!-- BRAIN SUB 3: CUSTOMER AVATARS -->
      <div class="sub-panel" id="sub-brain-avatars" hidden>
        <div class="panel-inner" style="gap:18px">
          <div style="display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap">
            <div id="avatar-selector-row" style="display:flex;gap:8px;flex-wrap:wrap"></div>
            <div style="display:flex;gap:8px;flex-wrap:wrap">
              <button type="button" class="btn btn-outline btn-sm" id="av-new-btn">＋ New Avatar</button>
              <button type="button" class="btn btn-yellow btn-sm" id="av-ai-gen-btn">✦ Generate Avatar with AI</button>
            </div>
          </div>

          <form id="avatar-edit-form" class="panel-card">
            <div class="form-row-2">
              <div><label class="field-label" for="av-name">Avatar Name *</label><input class="field-input" id="av-name" type="text" required></div>
              <div><label class="field-label" for="av-occ">Occupation / Role</label><input class="field-input" id="av-occ" type="text" placeholder="e.g. Agency Founder / $50K-$300K/mo Operator"></div>
            </div>
            <div class="form-row-2">
              <div><label class="field-label" for="av-age">Age / Stage</label><input class="field-input" id="av-age" type="text" placeholder="e.g. 30–48"></div>
              <div>
                <span class="field-label">Active Platforms</span>
                <div id="av-platforms-row" style="display:flex;flex-wrap:wrap;gap:6px;margin-top:4px"></div>
              </div>
            </div>
            <div class="form-row-2">
              <div><label class="field-label" for="av-fear">Biggest Fear</label><input class="field-input" id="av-fear" type="text"></div>
              <div><label class="field-label" for="av-desire">Biggest Desire</label><input class="field-input" id="av-desire" type="text"></div>
            </div>
            <div class="form-row-2">
              <div><label class="field-label" for="av-pains">Pains (one per line)</label><textarea class="field-textarea" id="av-pains" rows="3"></textarea></div>
              <div><label class="field-label" for="av-dreams">Dreams (one per line)</label><textarea class="field-textarea" id="av-dreams" rows="3"></textarea></div>
            </div>
            <div style="padding:14px 16px;border-radius:14px;background:var(--paper);border:1px solid var(--border);display:flex;flex-direction:column;gap:10px">
              <strong style="font-size:13px">The 3 False Beliefs</strong>
              <div class="card-grid-3">
                <div><label class="field-label" for="av-fb-method">About the Method</label><textarea class="field-textarea" id="av-fb-method" rows="2"></textarea></div>
                <div><label class="field-label" for="av-fb-self">About Themselves</label><textarea class="field-textarea" id="av-fb-self" rows="2"></textarea></div>
                <div><label class="field-label" for="av-fb-external">About Outside Forces</label><textarea class="field-textarea" id="av-fb-external" rows="2"></textarea></div>
              </div>
              <div><label class="field-label" for="av-fb-other">Other False Beliefs / Objections</label><textarea class="field-textarea" id="av-fb-other" rows="2"></textarea></div>
            </div>
            <div><label class="field-label" for="av-file-notes">Attached Research / Verbatim Quotes / Call Transcripts</label><textarea class="field-textarea" id="av-file-notes" rows="2" placeholder="Paste customer interviews, review language, or call notes..."></textarea></div>

            <!-- CUSTOM NOTES / MORE DETAILS -->
            <div style="padding:14px 16px;border-radius:14px;background:var(--cream);border:1px solid var(--border);display:flex;flex-direction:column;gap:10px">
              <div style="display:flex;justify-content:space-between;align-items:center">
                <strong style="font-size:13px">More Details &amp; Custom Notes (Revenue Band, Trigger Moment, How They Talk, etc.)</strong>
                <button type="button" class="btn btn-outline btn-xs" id="av-add-detail-btn">＋ Add Custom Detail</button>
              </div>
              <div id="av-custom-details-list" style="display:flex;flex-direction:column;gap:8px"></div>
            </div>

            <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap">
              <button type="button" class="btn btn-outline btn-sm" id="av-delete-btn">Delete Avatar</button>
              <button type="submit" class="btn btn-yellow btn-sm">Save Customer Avatar ✓</button>
            </div>
          </form>
        </div>
      </div>

      <!-- BRAIN SUB 4: PRODUCTS & OFFERS (WITH S/A/B/C OFFER MODALITIES + PERCEIVED VALUE) -->
      <div class="sub-panel" id="sub-brain-offers" hidden>
        <div class="panel-inner" style="gap:24px">
          <div class="card-grid-2" style="align-items:start">
            <!-- CREATE / EDIT PRODUCT WITH S/A/B/C MODALITIES -->
            <form id="product-form" class="panel-card">
              <span class="eyebrow-dot">Products &amp; Offer Modalities (S / A / B / C Tier)</span>
              <h3 style="font-size:21px">Add a Product or Bonus Deliverable</h3>
              <div class="form-row-2">
                <div><label class="field-label" for="prod-name">Product Name *</label><input class="field-input" id="prod-name" type="text" required placeholder="e.g. Done-For-You AI Operating Stack"></div>
                <div><label class="field-label" for="prod-status">Status</label><select class="field-select" id="prod-status"><option>Active</option><option>Retired</option></select></div>
              </div>
              <div><label class="field-label" for="prod-desc">What it is</label><textarea class="field-textarea" id="prod-desc" rows="2" placeholder="Describe the deliverable clearly..."></textarea></div>
              <div><label class="field-label" for="prod-solves">What problem does it solve?</label><input class="field-input" id="prod-solves" type="text" placeholder="Eliminates 15 hrs/wk of manual follow-up and reporting"></div>
              <div class="form-row-2">
                <div><label class="field-label" for="prod-pvalue">Perceived Value ($)</label><input class="field-input" id="prod-pvalue" type="number" min="0" step="50" value="2500" placeholder="2500"></div>
                <div><label class="field-label" for="prod-price">Standalone Price ($ optional)</label><input class="field-input" id="prod-price" type="number" min="0" step="10" value="997" placeholder="997"></div>
              </div>
              <div>
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
                  <span class="field-label" style="margin:0">Select Offer Modalities (multi-select)</span>
                  <span class="status-chip" id="prod-modality-score">Leverage Score: 0</span>
                </div>
                <div id="prod-modalities-picker" style="display:flex;flex-direction:column;gap:8px"></div>
              </div>
              <button type="submit" class="btn btn-yellow btn-sm" style="align-self:flex-start">＋ Save Product to Catalog</button>
            </form>

            <!-- CREATE OFFER + ATTACH PRODUCTS STACK -->
            <form id="offer-form" class="panel-card">
              <span class="eyebrow-dot">Offer Stack &amp; Value Ladder</span>
              <h3 style="font-size:21px">Build an Offer Stack</h3>
              <div class="form-row-2">
                <div><label class="field-label" for="off-name">Offer Name *</label><input class="field-input" id="off-name" type="text" required placeholder="e.g. AI Simple Accelerator"></div>
                <div><label class="field-label" for="off-tier">Value Ladder Tier</label><select class="field-select" id="off-tier"><option>Lead Gen</option><option>Core</option><option>Mid-Ticket</option><option>High-Ticket</option></select></div>
              </div>
              <div><label class="field-label" for="off-promise">The Core Promise</label><textarea class="field-textarea" id="off-promise" rows="2" placeholder="Install 3 reliable AI workflows that save 15+ hrs/week in 30 days."></textarea></div>
              <div class="form-row-2">
                <div><label class="field-label" for="off-price">Offer Price ($)</label><input class="field-input" id="off-price" type="number" min="0" step="10" value="2997"></div>
                <div><label class="field-label" for="off-billing">Billing</label><select class="field-select" id="off-billing"><option>One-time</option><option>Recurring</option></select></div>
              </div>
              <div class="form-row-2">
                <div><label class="field-label" for="off-pvalue">Override Perceived Value ($ optional)</label><input class="field-input" id="off-pvalue" type="number" min="0" step="100" placeholder="Auto-summed from attached products"></div>
                <div><label class="field-label" for="off-guarantee">Guarantee / Risk Reversal</label><input class="field-input" id="off-guarantee" type="text" placeholder="30-day unconditional guarantee"></div>
              </div>
              <div>
                <span class="field-label">Attach Products to This Offer Stack (Core or Bonus)</span>
                <div id="offer-product-picker" style="display:flex;flex-direction:column;gap:6px;max-height:200px;overflow-y:auto"></div>
              </div>
              <button type="submit" class="btn btn-dark btn-sm" style="align-self:flex-start">＋ Save Offer Stack</button>
            </form>
          </div>

          <section class="panel-card">
            <strong style="font-size:16px">Your Offers &amp; Stacked Perceived Value</strong>
            <div class="card-grid-2" id="offers-list-grid"></div>
          </section>

          <section class="panel-card">
            <strong style="font-size:16px">Your Product Catalog (<span id="products-count">0</span>)</strong>
            <div class="card-grid-3" id="products-list-grid"></div>
          </section>
        </div>
      </div>

      <!-- BRAIN SUB 5: ASSET LIBRARY -->
      <div class="sub-panel" id="sub-brain-assets" hidden>
        <div class="card-grid-2" style="align-items:start;grid-template-columns:minmax(0,0.9fr) minmax(0,1.3fr)">
          <form id="asset-add-form" class="panel-card">
            <span class="eyebrow-dot">Save &amp; Attach Resources</span>
            <h3 style="font-size:21px">Add to Asset Library</h3>
            <div><label class="field-label" for="al-title">Resource Title *</label><input class="field-input" id="al-title" type="text" required placeholder="e.g. Q4 Webinar Slide Deck / Offer SOP"></div>
            <div class="form-row-2">
              <div><label class="field-label" for="al-type">Type</label><select class="field-select" id="al-type"><option>Reference</option><option>Brief</option><option>Presentation</option><option>Email</option><option>Social</option><option>Document</option></select></div>
              <div><label class="field-label" for="al-url">Link / ZeroDrive Path (optional)</label><input class="field-input" id="al-url" type="text" placeholder="https://... or OutlierLab/docs/..."></div>
            </div>
            <div><label class="field-label" for="al-content">Content / Key Takeaways (attachable to AI Chat)</label><textarea class="field-textarea" id="al-content" rows="5" required placeholder="Paste SOP, framework, training notes, or key bullet points..."></textarea></div>
            <button type="submit" class="btn btn-yellow btn-sm" style="align-self:flex-start">＋ Save to Asset Library</button>
          </form>

          <section class="panel-card">
            <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap">
              <strong style="font-size:16px">Workspace Asset Library</strong>
              <div class="segmented" id="asset-origin-filter">
                <button type="button" data-aorig="all" class="active">Everything</button>
                <button type="button" data-aorig="ai">AI Generated</button>
                <button type="button" data-aorig="user">My Resources</button>
              </div>
            </div>
            <div id="asset-library-list" style="display:flex;flex-direction:column;gap:10px;max-height:540px;overflow-y:auto"></div>
          </section>
        </div>
      </div>
    </div>
  </section>

  <!-- ==================== TAB 6: CHANNELS, SOCIALS & ZERO-FRICTION SETUP ==================== -->
  <section class="tab-panel" id="panel-channels" role="tabpanel" aria-labelledby="tab-channels" hidden>
    <div class="panel-inner">
      <div class="section-head">
        <div>
          <span class="eyebrow-slash">/ Intake Studio · My Socials · Automations · Zero-Friction Setup &amp; Optional Go Live /</span>
          <h2>Channels, Socials &amp; Easy Setup</h2>
          <p>Add any single video or channel, connect your owned socials, or use the zero-friction setup &amp; optional Go Live checklist.</p>
        </div>
        <div class="sub-nav" id="channels-subnav" role="tablist">
          <button type="button" data-sub="ch-intake" class="active">Channels &amp; Free Discovery</button>
          <button type="button" data-sub="ch-socials">My Socials &amp; Trends</button>
          <button type="button" data-sub="ch-integrations">ZeroDrive &amp; Composio</button>
          <button type="button" data-sub="ch-setup">AI Engine &amp; Setup</button>
        </div>
      </div>

      <!-- SUB 1: ADD VIDEO & CHANNELS -->
      <div class="sub-panel" id="sub-ch-intake">
        <div class="panel-inner">
          <div class="card-grid-2">
            <article class="panel-card tone-butter">
              <span class="eyebrow-dot">Instant 6-Tab Breakdown</span>
              <h3 style="font-size:24px">Add a single video</h3>
              <p style="font-size:13.5px;color:var(--ink-2)">Paste any Instagram Reel, TikTok, or YouTube Short URL (plus optional spoken transcript/caption) to instantly generate its full 6-tab video & story breakdown and add it to your feed &amp; Ideas Inbox.</p>
              <form id="inline-single-video-form" style="display:flex;flex-direction:column;gap:10px">
                <div class="platform-pills" data-platform-group="single-video">
                  <button type="button" class="platform-pill active" data-platform="instagram">Instagram</button>
                  <button type="button" class="platform-pill" data-platform="youtube">YouTube</button>
                  <button type="button" class="platform-pill" data-platform="tiktok">TikTok</button>
                  <button type="button" class="platform-pill" data-platform="facebook">Facebook</button>
                </div>
                <div><label class="field-label" for="sv-url">Video URL (IG Reel, YT Short/Video, TikTok, or Facebook Reel)</label><input class="field-input" id="sv-url" type="url" required placeholder="https://www.youtube.com/shorts/... or https://www.instagram.com/reel/..."></div>
                <div><label class="field-label" for="sv-transcript">Spoken transcript or hook (optional — auto-fetched on localhost for YT/TT/FB)</label><textarea class="field-textarea" id="sv-transcript" rows="3" placeholder="Leave blank to auto-fetch captions on localhost, or paste transcript/hook here..."></textarea></div>
                <div class="form-row-2">
                  <div><label class="field-label" for="sv-workspace">Workspace</label><select class="field-select" id="sv-workspace"></select></div>
                  <div><label class="field-label" for="sv-tag">Creator handle or tag</label><input class="field-input" id="sv-tag" type="text" placeholder="@creator or Hook tag"></div>
                </div>
                <button type="submit" class="btn btn-yellow" style="align-self:flex-start">Analyze &amp; Open Breakdown →</button>
              </form>
              <div id="single-video-queue" style="display:flex;flex-direction:column;gap:8px"></div>
            </article>

            <article class="panel-card tone-lavender">
              <span class="eyebrow-dot">Ongoing Watchlist</span>
              <h3 style="font-size:24px">Track an entire channel</h3>
              <p style="font-size:13.5px;color:var(--ink-2)">Paste up to 25 handles or profile links. Shared channels are scraped once across workspaces so you never double-spend.</p>
              <form id="inline-channel-form" style="display:flex;flex-direction:column;gap:10px">
                <div class="platform-pills" data-platform-group="channel">
                  <button type="button" class="platform-pill active" data-platform="instagram">Instagram</button>
                  <button type="button" class="platform-pill" data-platform="youtube">YouTube</button>
                  <button type="button" class="platform-pill" data-platform="tiktok">TikTok</button>
                  <button type="button" class="platform-pill" data-platform="facebook">Facebook</button>
                </div>
                <div><label class="field-label" for="ch-handles">Handle(s) or Profile / Page URLs</label><textarea class="field-textarea" id="ch-handles" required placeholder="@creator, https://youtube.com/@handle, https://facebook.com/page"></textarea></div>
                <div class="form-row-2">
                  <div><label class="field-label" for="ch-workspace">Workspace</label><select class="field-select" id="ch-workspace"></select></div>
                  <div><label class="field-label" for="ch-scope">Niche list</label><select class="field-select" id="ch-scope"></select></div>
                </div>
                <div style="display:flex;gap:8px;flex-wrap:wrap">
                  <button type="submit" class="btn btn-dark">Track Entire Channel →</button>
                  <a class="btn btn-outline" id="add-creator" href="/admin#add-creators">Open Local Admin ↗</a>
                </div>
              </form>
              <div id="channel-queue" style="display:flex;flex-direction:column;gap:8px"></div>
            </article>
          </div>

          <!-- FREE LIVE CREATOR DISCOVERY & SEARCH ($0) -->
          <section class="panel-card">
            <div class="section-head">
              <div>
                <span class="eyebrow-dot">Free Live Creator Discovery · $0 Scraping</span>
                <h3 style="font-size:22px">Find &amp; add new channels across YouTube, TikTok, Instagram &amp; Facebook</h3>
              </div>
              <div class="segmented" id="disc-mode-switch">
                <button type="button" data-dmode="search" class="active">Search</button>
                <button type="button" data-dmode="describe">Describe with AI</button>
                <button type="button" data-dmode="suggested">Suggested</button>
              </div>
            </div>
            <form id="creator-discover-form" style="display:flex;gap:10px;flex-wrap:wrap;align-items:center">
              <select class="field-select" id="disc-platform" style="width:auto;padding:10px 14px">
                <option value="youtube">YouTube</option>
                <option value="tiktok">TikTok</option>
                <option value="instagram">Instagram</option>
                <option value="facebook">Facebook</option>
                <option value="all">All Platforms</option>
              </select>
              <input class="filter-search" id="disc-query" type="text" placeholder="Search topic, handle, or describe the creators you want (e.g. 'founders teaching AI automation')..." style="flex:1;min-width:220px">
              <button type="submit" class="btn btn-yellow btn-sm" id="disc-submit-btn">Find Creators Live →</button>
            </form>
            <div class="roster-grid" id="disc-results-grid"></div>
          </section>

          <section>
            <div class="section-head" style="margin-bottom:14px">
              <div><span class="eyebrow-dot">Active Watchlist</span><h3 style="font-size:24px">Tracked channels in this workspace</h3></div>
              <span style="font-size:13px;font-weight:700;color:var(--ink-3)" id="roster-count"></span>
            </div>
            <div class="roster-grid" id="roster-grid"></div>
          </section>

          <details class="panel-card" id="coverage-details">
            <summary id="coverage-summary" style="cursor:pointer;font-weight:800">Data coverage &amp; transcript readiness</summary>
            <div style="overflow-x:auto"><table class="reels-table"><thead><tr><th>Creator</th><th>Reels</th><th>Transcripts</th><th>Status</th><th>Last Request</th></tr></thead><tbody id="coverage-body"></tbody></table></div>
          </details>
        </div>
      </div>

      <!-- SUB 2: MY SOCIALS & TRENDS -->
      <div class="sub-panel" id="sub-ch-socials" hidden>
        <div class="panel-inner">
          <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap">
            <p id="socials-subtitle" style="font-size:14px;color:var(--ink-2)"></p>
            <div style="display:flex;gap:8px;flex-wrap:wrap">
              <button type="button" class="toggle-pill" id="preview-connected-toggle">Preview connected layout</button>
              <button type="button" class="btn btn-yellow btn-sm" id="sync-all-socials">↻ Sync Accounts</button>
            </div>
          </div>
          <div class="socials-grid" id="socials-grid"></div>
          <section class="panel-card">
            <div class="section-head">
              <div><span class="eyebrow-dot">Owned Performance</span><h3 style="font-size:24px">Your own top outliers</h3></div>
              <span class="status-chip" id="own-outliers-status">Ready to connect</span>
            </div>
            <div id="own-outliers-body"></div>
          </section>
          <div class="card-grid-3" id="trends-grid"></div>
        </div>
      </div>

      <!-- SUB 3: ZERODRIVE & COMPOSIO INTEGRATIONS -->
      <div class="sub-panel" id="sub-ch-integrations" hidden>
        <div class="panel-inner" style="gap:24px">
          <!-- ZERODRIVE AGENTIC STORAGE -->
          <section class="panel-card tone-butter">
            <div class="section-head">
              <div>
                <span class="eyebrow-dot">Agentic Cloud Brain Storage</span>
                <h3 style="font-size:24px">ZeroDrive · 1-Click Connect &amp; Sync</h3>
              </div>
              <span class="status-chip muted" id="zd-status-chip">Checking ZeroDrive…</span>
            </div>
            <p style="font-size:13.5px;color:var(--ink-2)">Connect your ZeroDrive vault so every Memory, Founder Persona, Customer Avatar, Product/Offer Stack, Asset Library resource, and AI Chat deliverable saves directly to your personal cloud drive (and mirrors locally when offline).</p>
            <form id="zd-connect-form" class="form-row-2" style="align-items:end">
              <div><label class="field-label" for="zd-vault-root">ZeroDrive Vault Folder</label><input class="field-input" id="zd-vault-root" type="text" value="OutlierLab" placeholder="OutlierLab"></div>
              <div><label class="field-label" for="zd-api-url">Hosted ZeroDrive API URL (optional)</label><input class="field-input" id="zd-api-url" type="url" placeholder="https://api.zerodrive.dev"></div>
              <div><label class="field-label" for="zd-api-key">ZeroDrive API Key (optional — stored only in local .env)</label><input class="field-input" id="zd-api-key" type="password" placeholder="Leave blank to use local zd CLI"></div>
              <div style="display:flex;gap:8px;flex-wrap:wrap">
                <button type="submit" class="btn btn-yellow btn-sm" id="zd-connect-btn">⚡ 1-Click Connect ZeroDrive</button>
                <button type="button" class="btn btn-dark btn-sm" id="zd-sync-now-btn">☁ Sync Active Brain Now</button>
              </div>
            </form>
            <div id="zd-files-list" style="display:flex;flex-wrap:wrap;gap:8px;margin-top:6px"></div>
          </section>

          <!-- COMPLETE COMPOSIO INTEGRATION -->
          <section class="panel-card">
            <div class="section-head">
              <div>
                <span class="eyebrow-dot">Complete Tool &amp; App Automation</span>
                <h3 style="font-size:24px">Composio Integration · Connect 15+ Apps &amp; Execute Tools</h3>
              </div>
              <span class="status-chip muted" id="comp-status-chip">Checking Composio…</span>
            </div>
            <p style="font-size:13.5px;color:var(--ink-2)">Attach your Composio API key once (saved privately in local <code>.env</code>) to connect Gmail, Notion, Slack, Google Drive, YouTube, Instagram, Meta Ads, HubSpot, Calendar, Linear, GitHub, Stripe, and more — and run any Composio tool action directly from Outlier Lab.</p>
            <form id="comp-config-form" style="display:flex;gap:10px;flex-wrap:wrap;align-items:end">
              <div style="flex:1;min-width:220px"><label class="field-label" for="comp-api-key">Composio API Key</label><input class="field-input" id="comp-api-key" type="password" placeholder="Paste COMPOSIO_API_KEY..."></div>
              <div style="width:200px"><label class="field-label" for="comp-user-id">Entity / User ID</label><input class="field-input" id="comp-user-id" type="text" value="aisimple-default"></div>
              <button type="submit" class="btn btn-yellow btn-sm" id="comp-save-btn">Save &amp; Verify Composio ✓</button>
            </form>

            <div>
              <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;margin-bottom:10px;flex-wrap:wrap">
                <strong style="font-size:14.5px">Available Toolkits &amp; 1-Click OAuth Connect</strong>
                <input class="filter-search" id="comp-search" type="search" placeholder="Filter toolkits (gmail, notion, slack, youtube...)" style="max-width:280px;padding:7px 12px;font-size:12.5px">
              </div>
              <div class="toolkit-grid" id="comp-toolkits-grid"></div>
            </div>

            <div style="padding-top:16px;border-top:1px solid var(--border);display:flex;flex-direction:column;gap:10px">
              <strong style="font-size:14.5px">Live Composio Tool Runner</strong>
              <form id="comp-exec-form" class="form-row-2" style="align-items:end">
                <div><label class="field-label" for="comp-tool-slug">Tool Slug (e.g. GMAIL_FETCH_EMAILS, NOTION_SEARCH_NOTION_PAGE)</label><input class="field-input" id="comp-tool-slug" type="text" placeholder="GMAIL_FETCH_EMAILS"></div>
                <div><label class="field-label" for="comp-tool-args">Arguments JSON</label><input class="field-input" id="comp-tool-args" type="text" value="{}"></div>
                <button type="submit" class="btn btn-dark btn-sm" style="align-self:start" id="comp-exec-btn">▶ Execute Tool Action</button>
              </form>
              <pre id="comp-exec-output" style="display:none;white-space:pre-wrap;font-family:var(--font-mono);font-size:11.5px;background:var(--paper);padding:12px;border-radius:12px;border:1px solid var(--border);max-height:240px;overflow:auto;margin:0"></pre>
            </div>
          </section>
        </div>
      </div>

      <!-- SUB 4: ZERO-FRICTION SETUP & OPTIONAL GO LIVE -->
      <div class="sub-panel" id="sub-ch-setup" hidden>
        <div class="panel-inner">
          <section class="panel-card tone-lavender" id="ai-engine-panel">
            <div class="section-head">
              <div>
                <span class="eyebrow-dot">Local AI Brain · Claude CLI &amp; Codex CLI</span>
                <h3 style="font-size:24px">Local Deep AI Analysis & Brain Engine</h3>
              </div>
              <span class="status-chip muted" id="ai-engine-status-chip">Checking local CLIs…</span>
            </div>
            <p style="font-size:13.5px;color:var(--ink-2)">When running locally on <code>http://127.0.0.1:4747</code>, Outlier Lab plugs directly into your installed <strong>Claude Code CLI</strong> or <strong>Codex CLI</strong> (using your existing login — zero extra API billing) to run true LLM beat-by-beat breakdowns, Founder Persona rewrites, and 4-step script generation. Upgraded breakdowns are cached into <code>data/</code> and publish live to <code>outlier.aisimple.co</code>.</p>
            <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
              <div class="segmented" id="ai-provider-switch" role="group" aria-label="AI Engine">
                <button type="button" data-ai-provider="claude">✦ Claude CLI</button>
                <button type="button" data-ai-provider="codex">✦ Codex CLI</button>
                <button type="button" data-ai-provider="local" class="active">⚡ Instant Local</button>
              </div>
              <button type="button" class="btn btn-yellow btn-sm" id="ai-batch-upgrade-btn">✦ Deep-Analyze Top 5 Outliers</button>
              <span id="ai-batch-status-msg" style="font-size:12.5px;font-weight:700;color:var(--ink-2)"></span>
            </div>
          </section>

          <section class="panel-card tone-butter">
            <span class="eyebrow-dot">Zero-Friction Local Setup · 2 Minutes · Zero Cloud Accounts Required</span>
            <h3 style="font-size:26px">Run Outlier Lab on any Mac or Linux machine in one command.</h3>
            <p style="font-size:14px;color:var(--ink-2)">No database, no Docker, no Clerk, no Vercel, and no AI API keys required to start breaking down videos, building your Character profile, checking hooks, and writing scripts.</p>
            <div class="code-block">git clone https://github.com/Vibe-Marketer/outlier-lab.git
cd outlier-lab
./setup.sh</div>
            <div class="card-grid-3">
              <div class="panel-card" style="padding:18px"><span class="status-chip live">Step 1 · Included</span><strong style="font-size:15px">Instant Local App</strong><p style="font-size:13px;color:var(--ink-2)">Creates starter <code>config.json</code>, builds the AI Simple studio, and opens <code>http://127.0.0.1:4747</code> automatically.</p></div>
              <div class="panel-card" style="padding:18px"><span class="status-chip muted">Step 2 · Optional</span><strong style="font-size:15px">Auto-Scrape Creators</strong><p style="font-size:13px;color:var(--ink-2)">Paste a free Apify token in Admin only when you want automated 28-day Instagram scrapes.</p></div>
              <div class="panel-card" style="padding:18px"><span class="status-chip muted">Step 3 · Optional</span><strong style="font-size:15px">Bulk Transcripts</strong><p style="font-size:13px;color:var(--ink-2)">Add a TokScript key in <code>.env</code> only if you want bulk spoken transcription across 400+ reels.</p></div>
            </div>
          </section>

          <section class="panel-card">
            <span class="eyebrow-dot">Optional "Go Live" Publishing · Never Required</span>
            <h3 style="font-size:24px">Turn on live web hosting only if &amp; when you want it.</h3>
            <p style="font-size:14px;color:var(--ink-2)">Everything works 100% locally first. Each "Go Live" capability below is completely optional and independent.</p>
            <div class="card-grid-2">
              <div class="panel-card tone-cream" style="padding:20px">
                <div style="display:flex;justify-content:space-between;align-items:center"><strong>1. Publish Live to Vercel (e.g. outlier.aisimple.co)</strong><span class="status-chip muted">Optional</span></div>
                <p style="font-size:13px;color:var(--ink-2)">Push static dashboard + thumbnails + 3s clips to Vercel Hobby (free). Never exposes local admin or <code>.env</code> secrets.</p>
                <div class="code-block">vercel --prod</div>
              </div>
              <div class="panel-card tone-lavender" style="padding:20px">
                <div style="display:flex;justify-content:space-between;align-items:center"><strong>2. Team Login / Clerk Protection</strong><span class="status-chip muted">Optional</span></div>
                <p style="font-size:13px;color:var(--ink-2)">Skip completely for local use. For hosted team access, set <code>CLERK_PUBLISHABLE_KEY</code> &amp; <code>CLERK_SECRET_KEY</code> in Vercel env vars and edit <code>ALLOWED_EMAILS</code> in <code>auth.js</code>.</p>
              </div>
              <div class="panel-card tone-sage" style="padding:20px">
                <div style="display:flex;justify-content:space-between;align-items:center"><strong>3. Auto-Refresh Cron (GitHub Actions)</strong><span class="status-chip muted">Optional</span></div>
                <p style="font-size:13px;color:var(--ink-2)">Defaults to manual so you never get surprise bills. Enable daily/weekly cloud refreshes anytime in Admin → Refresh Schedule.</p>
              </div>
              <div class="panel-card" style="padding:20px">
                <div style="display:flex;justify-content:space-between;align-items:center"><strong>4. Portable Workspace Backup &amp; Share</strong><span class="status-chip live">Ready Now</span></div>
                <p style="font-size:13px;color:var(--ink-2)">Export your Workspaces, Founder Persona & Brain Profiles, Shortlisted Ideas, Projects, Saved Hooks, and Scripts as one JSON file — or import someone else's setup in 2 seconds.</p>
                <div style="display:flex;gap:8px;flex-wrap:wrap">
                  <button type="button" class="btn btn-yellow btn-sm" id="export-backup-btn">↓ Export Full Backup JSON</button>
                  <label class="btn btn-outline btn-sm" style="cursor:pointer">↑ Import Backup JSON<input type="file" id="import-backup-input" accept="application/json" hidden></label>
                </div>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  </section>

</main>

<footer class="app-footer">
  <div style="display:flex;align-items:center;gap:12px">
    <span class="brand-mark" style="width:32px;height:32px;border-radius:8px" aria-hidden="true">
      <svg width="19" height="19" viewBox="0 0 64 64" fill="none">
        <path d="M16 48L28.8 18.6C30.1 15.6 33.9 15.6 35.2 18.6L48 48" stroke="#111111" stroke-width="11" stroke-linecap="round" stroke-linejoin="round"/>
        <circle cx="32" cy="44" r="6.8" fill="#111111"/>
      </svg>
    </span>
    <div>
      <div style="font-weight:800;font-size:14px">AI SIMPLE · Outlier Lab Studio</div>
      <div style="font-size:11.5px;color:#9e9e9e">AI Simple Outlier Lab · Video Intelligence, Brand Brain & Creative Arsenal.</div>
    </div>
  </div>
  <div class="footer-meta">
    <span>__TOTAL_CREATORS__ channels · __TOTAL_REELS__ analyzed reels</span>
    <span>Built __BUILT_AT__</span>
    <a id="footer-admin-link" href="/admin">Local Admin ↗</a>
  </div>
</footer>
  </div>
</div>

<!-- ==================== FULL 6-TAB VIDEO BREAKDOWN DIALOG ==================== -->
<dialog id="reel-dialog" closedby="any" aria-labelledby="bd-title">
  <div class="dialog-shell bd-shell">
    <div class="bd-topbar">
      <div style="display:flex;align-items:center;gap:10px;min-width:0;flex:1">
        <span id="bd-badge" class="band-pill">—</span>
        <h1 id="bd-title">Video Breakdown</h1>
      </div>
      <div style="display:flex;align-items:center;gap:7px;flex-shrink:0">
        <button type="button" class="btn btn-outline btn-xs" id="bd-prev" title="Previous video (←)">← Prev</button>
        <button type="button" class="btn btn-outline btn-xs" id="bd-next" title="Next video (→)">Next →</button>
        <button type="button" class="dialog-close" data-close-dialog aria-label="Close breakdown">×</button>
      </div>
    </div>

    <div class="bd-body">
      <!-- LEFT RAIL: VIDEO PLAYER + METRICS + 7 SINGLE-KEY ACTIONS -->
      <aside class="bd-left">
        <div class="bd-video-stage">
          <video id="modal-video" autoplay muted loop playsinline preload="metadata" hidden></video>
          <iframe id="modal-iframe" src="" allow="autoplay; encrypted-media" hidden title="Instagram Reel embed"></iframe>
          <span class="hook-clip-badge" id="modal-clip-badge" hidden>● Hook · first 3s</span>
          <button class="modal-source-toggle" id="modal-source-toggle" type="button" hidden>Show full reel ↗</button>
        </div>

        <div style="display:flex;align-items:center;justify-content:space-between;gap:8px">
          <div id="modal-creator" class="creator-mini"></div>
          <span id="bd-date-dur" style="font-size:11.5px;color:var(--ink-3)"></span>
        </div>

        <div style="display:flex;gap:6px;flex-wrap:wrap" id="bd-metric-pills"></div>

        <div class="bd-actions">
          <button type="button" class="btn btn-yellow btn-sm" id="bd-act-script"><span>Create script</span><span class="kbd">C</span></button>
          <button type="button" class="btn btn-outline btn-sm" id="bd-act-shortlist"><span id="bd-shortlist-lbl">Shortlist idea</span><span class="kbd">S</span></button>
          <button type="button" class="btn btn-outline btn-sm" id="bd-act-project"><span>Add to project</span><span class="kbd">A</span></button>
          <button type="button" class="btn btn-outline btn-sm" id="bd-act-hook"><span id="bd-hook-lbl">Save hook format</span><span class="kbd">H</span></button>
          <button type="button" class="btn btn-outline btn-sm" id="bd-act-llm"><span>Export for LLM</span><span class="kbd">E</span></button>
          <a class="btn btn-outline btn-sm" id="bd-act-open" href="#" target="_blank" rel="noopener noreferrer"><span>Open original</span><span class="kbd">O</span></a>
          <button type="button" class="btn btn-outline btn-sm" id="bd-act-done"><span id="bd-done-lbl">Mark as studied</span><span class="kbd">R</span></button>
        </div>
      </aside>

      <!-- RIGHT COLUMN: SUMMARY + 6 BREAKDOWN TABS -->
      <div class="bd-right">
        <div style="display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap;padding:10px 14px;border-radius:14px;background:var(--paper);border:1px solid var(--border)">
          <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
            <span class="status-chip muted" id="bd-engine-badge">⚡ Instant Breakdown</span>
            <span id="bd-platform-badge" class="micro-tag">INSTAGRAM</span>
          </div>
          <div style="display:flex;align-items:center;gap:7px;flex-wrap:wrap">
            <select id="bd-ai-provider" class="field-select" style="padding:5px 10px;font-size:12px;width:auto" aria-label="AI Breakdown Provider">
              <option value="claude">Claude CLI</option>
              <option value="codex">Codex CLI</option>
            </select>
            <button type="button" class="btn btn-yellow btn-xs" id="bd-ai-upgrade">✦ Deep Analyze with AI</button>
          </div>
        </div>
        <div class="bd-summary" id="bd-summary"></div>

        <div class="bd-tabs" id="bd-tabs" role="tablist" aria-label="Video breakdown sections">
          <button type="button" class="bd-tab active" data-bdtab="transcript">1. Transcript</button>
          <button type="button" class="bd-tab" data-bdtab="idea">2. Idea Analysis</button>
          <button type="button" class="bd-tab" data-bdtab="hook">3. Hook</button>
          <button type="button" class="bd-tab" data-bdtab="format">4. Storytelling Format</button>
          <button type="button" class="bd-tab" data-bdtab="visual">5. Visual Layout</button>
          <button type="button" class="bd-tab" data-bdtab="kennedy">6. Magnetic Story Audit</button>
        </div>

        <!-- BD TAB 1: TRANSCRIPT (PARAGRAPH + BEAT-BY-BEAT) -->
        <div class="bd-tab-panel" id="bdpanel-transcript">
          <div class="bd-card">
            <div style="display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap">
              <div style="display:flex;align-items:center;gap:8px">
                <strong style="font-size:15px">Transcript</strong>
                <span class="status-chip muted" id="bd-word-count">0 words</span>
              </div>
              <div style="display:flex;gap:6px;align-items:center">
                <div class="segmented" id="bd-tr-mode">
                  <button type="button" data-trmode="beats" class="active">Beat-by-Beat</button>
                  <button type="button" data-trmode="paragraph">Paragraph</button>
                </div>
                <button type="button" class="btn btn-outline btn-xs" id="bd-copy-tr">Copy</button>
              </div>
            </div>
            <div id="bd-tr-beats-view" style="display:flex;flex-direction:column;gap:10px"></div>
            <div id="bd-tr-para-view" hidden style="white-space:pre-wrap;font-size:13.5px;line-height:1.68;color:var(--ink-2)"></div>
          </div>
          <div class="bd-card" style="margin-top:12px">
            <div style="display:flex;justify-content:space-between;align-items:center">
              <strong style="font-size:14px">Original Caption</strong>
              <button type="button" class="btn btn-outline btn-xs" id="bd-copy-cap">Copy</button>
            </div>
            <div id="bd-caption-text" style="white-space:pre-wrap;font-size:13px;color:var(--ink-2);max-height:160px;overflow-y:auto"></div>
          </div>
        </div>

        <!-- BD TAB 2: IDEA ANALYSIS -->
        <div class="bd-tab-panel" id="bdpanel-idea" hidden></div>

        <!-- BD TAB 3: HOOK -->
        <div class="bd-tab-panel" id="bdpanel-hook" hidden></div>

        <!-- BD TAB 4: STORYTELLING FORMAT -->
        <div class="bd-tab-panel" id="bdpanel-format" hidden></div>

        <!-- BD TAB 5: VISUAL LAYOUT -->
        <div class="bd-tab-panel" id="bdpanel-visual" hidden></div>

        <!-- BD TAB 6: MAGNETIC STORY AUDIT -->
        <div class="bd-tab-panel" id="bdpanel-kennedy" hidden></div>
      </div>
    </div>
  </div>
</dialog>

<!-- ==================== QUICK ADD VIDEO / CHANNEL DIALOG ==================== -->
<dialog id="quick-add-dialog" closedby="any" aria-labelledby="quick-add-title">
  <div class="dialog-shell form-dialog-shell">
    <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px">
      <div><span class="eyebrow-dot">Quick Intake</span><h1 id="quick-add-title" style="margin-top:6px">Add a video or channel</h1></div>
      <button type="button" class="dialog-close" data-close-dialog aria-label="Close">×</button>
    </div>
    <div class="segmented" id="qa-mode-switch" style="align-self:flex-start">
      <button type="button" data-qa-mode="video" class="active">Single Video (Instant Breakdown)</button>
      <button type="button" data-qa-mode="channel">Entire Channel</button>
    </div>
    <form id="qa-form" style="display:flex;flex-direction:column;gap:12px">
      <div class="platform-pills" id="qa-platforms">
        <button type="button" class="platform-pill active" data-platform="instagram">Instagram</button>
        <button type="button" class="platform-pill" data-platform="youtube">YouTube</button>
        <button type="button" class="platform-pill" data-platform="tiktok">TikTok</button>
        <button type="button" class="platform-pill" data-platform="facebook">Facebook</button>
      </div>
      <div><label class="field-label" id="qa-input-label" for="qa-input">Video URL</label><input class="field-input" id="qa-input" type="text" required autofocus placeholder="https://www.instagram.com/reel/..."></div>
      <div id="qa-transcript-wrap"><label class="field-label" for="qa-transcript">Paste spoken transcript or hook (optional — breaks down immediately)</label><textarea class="field-textarea" id="qa-transcript" rows="3" placeholder="Paste transcript or hook to generate beats, mad-lib hook, and Magnetic Story Audit right away..."></textarea></div>
      <div class="form-row-2">
        <div><label class="field-label" for="qa-workspace">Workspace</label><select class="field-select" id="qa-workspace"></select></div>
        <div><label class="field-label" for="qa-extra" id="qa-extra-label">Creator handle or tag</label><input class="field-input" id="qa-extra" type="text" placeholder="@creator"></div>
      </div>
      <div style="display:flex;justify-content:flex-end;gap:10px;margin-top:4px">
        <button type="button" class="btn btn-outline" data-close-dialog>Cancel</button>
        <button type="submit" class="btn btn-yellow" id="qa-submit-btn">Analyze &amp; Open Breakdown →</button>
      </div>
    </form>
  </div>
</dialog>

<!-- ==================== ADD TO PROJECT DIALOG ==================== -->
<dialog id="project-dialog" closedby="any" aria-labelledby="proj-dialog-title">
  <div class="dialog-shell form-dialog-shell">
    <div style="display:flex;justify-content:space-between;align-items:flex-start">
      <div><span class="eyebrow-dot">Save to Project</span><h1 id="proj-dialog-title" style="margin-top:6px">Add video to a folder</h1></div>
      <button type="button" class="dialog-close" data-close-dialog aria-label="Close">×</button>
    </div>
    <form id="save-to-project-form" style="display:flex;flex-direction:column;gap:12px">
      <div><label class="field-label" for="proj-select">Choose existing folder</label><select class="field-select" id="proj-select"></select></div>
      <div><label class="field-label" for="proj-new">Or create a new folder</label><input class="field-input" id="proj-new" type="text" placeholder="e.g. Q4 Winning Hooks"></div>
      <div style="display:flex;justify-content:flex-end;gap:8px">
        <button type="button" class="btn btn-outline" data-close-dialog>Cancel</button>
        <button type="submit" class="btn btn-yellow">Save to Project →</button>
      </div>
    </form>
  </div>
</dialog>

<!-- ==================== CREATE WORKSPACE DIALOG ==================== -->
<dialog id="workspace-dialog" closedby="any" aria-labelledby="ws-dialog-title">
  <div class="dialog-shell form-dialog-shell">
    <div style="display:flex;justify-content:space-between;align-items:flex-start">
      <div><span class="eyebrow-dot">Multi-Account Workspaces</span><h1 id="ws-dialog-title" style="margin-top:6px">Create a workspace</h1></div>
      <button type="button" class="dialog-close" data-close-dialog aria-label="Close">×</button>
    </div>
    <form id="create-ws-form" style="display:flex;flex-direction:column;gap:12px">
      <div class="form-row-2">
        <div><label class="field-label" for="new-ws-name">Workspace name</label><input class="field-input" id="new-ws-name" type="text" required autofocus placeholder="e.g. Prompt Cowboy"></div>
        <div><label class="field-label" for="new-ws-initials">2-letter badge</label><input class="field-input" id="new-ws-initials" type="text" maxlength="3" placeholder="PC"></div>
      </div>
      <div><label class="field-label" for="new-ws-tagline">What do you sell / focus on?</label><input class="field-input" id="new-ws-tagline" type="text" placeholder="Short-form hooks, product demos &amp; founder stories"></div>
      <div>
        <span class="field-label">Badge accent</span>
        <div class="swatch-row" id="ws-color-swatches">
          <button type="button" class="color-swatch active" data-accent="#ffc71d" data-ink="#1f1f1f" style="background:#ffc71d" aria-label="Yellow"></button>
          <button type="button" class="color-swatch" data-accent="#1f1f1f" data-ink="#ffc71d" style="background:#1f1f1f" aria-label="Charcoal"></button>
          <button type="button" class="color-swatch" data-accent="#f0e5ff" data-ink="#4f3d68" style="background:#f0e5ff" aria-label="Lavender"></button>
          <button type="button" class="color-swatch" data-accent="#eaf3e3" data-ink="#255a3b" style="background:#eaf3e3" aria-label="Sage"></button>
          <button type="button" class="color-swatch" data-accent="#d4276b" data-ink="#ffffff" style="background:#d4276b" aria-label="Crimson"></button>
        </div>
      </div>
      <div><span class="field-label">Include niche lists</span><div id="new-ws-scopes" style="display:flex;flex-wrap:wrap;gap:7px"></div></div>
      <div style="display:flex;justify-content:flex-end;gap:8px"><button type="button" class="btn btn-outline" data-close-dialog>Cancel</button><button type="submit" class="btn btn-yellow">Create Workspace →</button></div>
    </form>
  </div>
</dialog>

<!-- ==================== CONNECT SOCIAL DIALOG ==================== -->
<dialog id="connect-social-dialog" closedby="any" aria-labelledby="connect-social-title">
  <div class="dialog-shell form-dialog-shell">
    <div style="display:flex;justify-content:space-between;align-items:flex-start">
      <div><span class="eyebrow-dot" id="cs-workspace-eyebrow">Connect Account · Direct Sync</span><h1 id="connect-social-title" style="margin-top:6px">Connect Instagram</h1></div>
      <button type="button" class="dialog-close" data-close-dialog aria-label="Close">×</button>
    </div>
    <p style="font-size:13px;color:var(--ink-2)">Just paste your handle or profile/page URL — <strong>no OAuth developer app or API approval needed</strong>. Running locally on <code>:4747</code> syncs your recent videos, computes your real median views &amp; outlier multiples, and makes every video clickable for a full 6-tab breakdown.</p>
    <form id="connect-social-form" style="display:flex;flex-direction:column;gap:12px">
      <input type="hidden" id="cs-platform" value="instagram">
      <div><label class="field-label" for="cs-handle">Account handle or channel/page URL</label><input class="field-input" id="cs-handle" type="text" required autofocus placeholder="@yourhandle or https://youtube.com/@yourchannel"></div>
      <div style="padding:12px 14px;border-radius:14px;background:var(--paper);border:1px solid var(--border);display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap">
        <div><strong style="font-size:12px;display:block">Optional Bio Verification Code</strong><span style="font-size:11.5px;color:var(--ink-3)">Paste into your bio only if you want a Verified Owner badge — never required to sync.</span></div>
        <code id="cs-verify-code" style="font-family:var(--font-mono);font-weight:700;padding:5px 10px;border-radius:8px;background:var(--yellow-soft);color:var(--ink)">AIS-4829</code>
      </div>
      <div style="display:flex;justify-content:flex-end;gap:8px"><button type="button" class="btn btn-outline" data-close-dialog>Cancel</button><button type="submit" class="btn btn-yellow" id="cs-submit-btn">Connect &amp; Sync Now →</button></div>
    </form>
  </div>
</dialog>

<div class="toast" id="toast" role="status" aria-live="polite"><span class="toast-dot"></span><span id="toast-msg"></span></div>

<script>
const BASE_REELS = __REELS_JSON__;
const CREATORS = __CREATORS_JSON__;
const SCOPES = __SCOPES_JSON__;
const RESEARCH = __RESEARCH_JSON__;
const ADMIN_URL = __ADMIN_URL_JSON__;
const DEFAULT_WORKSPACES = __WORKSPACES_JSON__;
const COLLECTIONS = __COLLECTIONS_JSON__;
const SYNCED_OWN_SOCIALS = __OWN_SOCIALS_JSON__;
const CREATOR_MAP = new Map(CREATORS.map(c => [c.handle, c]));

const ARCHETYPES = [
  { name: "The Stern but Loving Parent", desc: "Cares deeply, holds you accountable. Tough love & harsh truths (Direct, high-accountability mentor)." },
  { name: "The Patient Teacher / Philosopher", desc: "Wisdom-centered, calm principles & clarity (Jim Rohn, Earl Nightingale)." },
  { name: "The Dysfunctional Eccentric Genius", desc: "Brilliant, unconventional, polarizing edge (Gary Halbert)." },
  { name: "The Everyman", desc: "\"If I can do it, you can do it\" — relatable transformation & grit." },
  { name: "The Mystical Seer", desc: "Sees patterns and shifts before anyone else in the room." },
];

const fmtNum = (n) => {
  if (n === null || n === undefined) return "—";
  n = Number(n);
  if (n >= 1e6) return (n / 1e6).toFixed(1) + "M";
  if (n >= 1e4) return Math.round(n / 1e3) + "K";
  if (n >= 1e3) return (n / 1e3).toFixed(1) + "K";
  return String(Math.round(n));
};
const fmtDur = (s) => {
  if (!s) return "—";
  s = Math.round(s);
  const m = Math.floor(s / 60), sec = s % 60;
  return m ? `${m}:${sec.toString().padStart(2, "0")}` : `${s}s`;
};
function escapeHtml(s) {
  if (s === null || s === undefined) return "";
  return String(s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;" })[c]);
}
function highlightMadlib(str) {
  return escapeHtml(str).replace(/\[([^\]]+)\]/g, '<span class="madlib-slot">[$1]</span>');
}

const KEYS = {
  view: "ig-dashboard-view",
  density: "ig-dashboard-density",
  filter: "ig-dashboard-filter",
  completed: "ig-dashboard-completed",
  deleted: "ig-dashboard-deleted",
  search: "ig-dashboard-search",
  band: "ig-dashboard-band",
  hideCompleted: "ig-dashboard-hide-completed",
  showDeleted: "ig-dashboard-show-deleted",
  scope: "outlier-niche-list",
  workspace: "outlier-active-workspace",
  customWorkspaces: "outlier-custom-workspaces",
  wsOverrides: "outlier-ws-overrides",
  tab: "outlier-active-tab",
  singleVideos: "outlier-single-videos",
  queuedChannels: "outlier-queued-channels",
  connectedSocials: "outlier-connected-socials",
  shortlistedIdeas: "outlier-shortlisted-ideas",
  discardedIdeas: "outlier-discarded-ideas",
  ideaNotes: "outlier-idea-notes",
  savedHooks: "outlier-saved-hooks",
  projects: "outlier-projects",
  savedScripts: "outlier-saved-scripts",
};
function loadJSON(k, fb) { try { return JSON.parse(localStorage.getItem(k) || "null") ?? fb; } catch { return fb; } }
function saveJSON(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch {} }

let customWorkspaces = loadJSON(KEYS.customWorkspaces, []);
let wsOverrides = loadJSON(KEYS.wsOverrides, {});
let connectedSocialOverrides = loadJSON(KEYS.connectedSocials, {});
let singleVideos = loadJSON(KEYS.singleVideos, []);
let queuedChannels = loadJSON(KEYS.queuedChannels, []);
let shortlistedIdeas = new Set(loadJSON(KEYS.shortlistedIdeas, []));
let discardedIdeas = new Set(loadJSON(KEYS.discardedIdeas, []));
let ideaNotes = loadJSON(KEYS.ideaNotes, {});
let savedHooks = new Set(loadJSON(KEYS.savedHooks, []));
let projects = loadJSON(KEYS.projects, [
  { id: "proj-hooks", name: "Winning Hooks", shortCodes: [] },
  { id: "proj-about", name: "About Me & Origin", shortCodes: [] },
  { id: "proj-ads", name: "High-Leverage Demos", shortCodes: [] },
]);
let savedScripts = loadJSON(KEYS.savedScripts, []);
let ownOutliersByWorkspace = {};
let syncedOwnedReels = [];
let aiCapabilities = { claude: false, codex: false, ytdlp: false, default: "local" };
let activeAiProvider = localStorage.getItem("outlier-ai-provider") || "local";
let previewConnectedMode = false;

// Hydrate pre-synced owned socials from build time (data/socials/*.json)
(SYNCED_OWN_SOCIALS || []).forEach(acc => {
  const wsId = acc.workspaceId || "aisimple";
  if (!connectedSocialOverrides[wsId]) connectedSocialOverrides[wsId] = {};
  if (!connectedSocialOverrides[wsId][acc.platform]) {
    connectedSocialOverrides[wsId][acc.platform] = {
      handle: acc.handle,
      connected: true,
      syncedAt: acc.syncedAt,
      medianViews: fmtNum(acc.medianViews),
      followers: acc.followers && acc.followers !== "—" ? acc.followers : (acc.followerCount ? fmtNum(acc.followerCount) : (acc.videoCount ? `${acc.videoCount} vids` : "Synced")),
      note: acc.note || "",
    };
  }
  const list = ownOutliersByWorkspace[wsId] || [];
  (acc.items || []).forEach(it => {
    syncedOwnedReels.push({ ...it, workspaceId: wsId });
    list.push({
      shortCode: it.shortCode,
      ratio: `${(it.ratio || 1).toFixed(1)}×`,
      band: it.band_class || (it.ratio >= 15 ? "breakout" : it.ratio >= 5 ? "strong" : it.ratio >= 2 ? "good" : "normal"),
      platform: `${(it.platform || acc.platform || "").toUpperCase()} · ${acc.handle}`,
      hook: it.hook || it.title || it.caption || "Synced Video",
      plays: fmtNum(it.plays || 0),
      likes: fmtNum(it.likes || 0),
    });
  });
  ownOutliersByWorkspace[wsId] = list.slice(0, 12);
});

function allReels() {
  const custom = singleVideos.filter(v => v.reelObj).map(v => v.reelObj);
  const seen = new Set();
  const out = [];
  for (const r of [...custom, ...BASE_REELS, ...syncedOwnedReels]) {
    if (!r || !r.shortCode || seen.has(r.shortCode)) continue;
    seen.add(r.shortCode);
    out.push(r);
  }
  return out;
}

function allWorkspaces() {
  const merged = [...DEFAULT_WORKSPACES, ...customWorkspaces].map(w => {
    const ov = wsOverrides[w.id] || {};
    return {
      ...w,
      ...ov,
      offer: { ...(w.offer || {}), ...(ov.offer || {}) },
      character: {
        ...(w.character || {}),
        ...(ov.character || {}),
        sevenElements: { ...(w.character?.sevenElements || {}), ...(ov.character?.sevenElements || {}) },
        profits: { ...(w.character?.profits || {}), ...(ov.character?.profits || {}) },
      },
    };
  });
  merged.push({
    id: "__all__", name: "All Workspaces", initials: "ALL", accent: "#f0e5ff", accentInk: "#4f3d68",
    tagline: "Unified feed across every brand, client & niche list",
    scopes: SCOPES.map(s => s.id), socials: [], offer: merged[0]?.offer || {}, character: merged[0]?.character || {},
  });
  return merged;
}

const urlParams = new URLSearchParams(location.search);
let activeWorkspaceId = urlParams.get("workspace") || localStorage.getItem(KEYS.workspace) || DEFAULT_WORKSPACES[0].id;
if (!allWorkspaces().some(w => w.id === activeWorkspaceId)) activeWorkspaceId = DEFAULT_WORKSPACES[0].id;
let activeTab = urlParams.get("tab") || localStorage.getItem(KEYS.tab) || "today";
if (!["today", "feed", "seo", "chat", "ideas", "scripts", "character", "channels"].includes(activeTab)) activeTab = "today";

let activeScope = urlParams.get("scope") || localStorage.getItem(KEYS.scope) || "__workspace__";
let activeFilter = localStorage.getItem(KEYS.filter) || "__all__";
let completed = new Set(loadJSON(KEYS.completed, []));
let deleted = new Set(loadJSON(KEYS.deleted, []));
let searchText = localStorage.getItem(KEYS.search) || "";
let bandFilter = localStorage.getItem(KEYS.band) || "all";
let hookCatFilter = "all";
let formatCatFilter = "all";
let topicFilter = "all";
let hideCompleted = localStorage.getItem(KEYS.hideCompleted) === "1";
let showDeleted = localStorage.getItem(KEYS.showDeleted) === "1";
let sortKey = "ratio";
let sortDir = "desc";
let spotlightMode = "top5";
let ideaBucket = "inbox";
let ideaSearch = "";
let vaultHookCat = "all";
let vaultSavedOnly = false;
let auditDim = "topics";
let auditSelectedKey = null;
let formulaOffset = 0;

// Script Wizard State
let wizard = {
  step: 1,
  sourceShortCode: null,
  topic: "",
  existingDraft: "",
  format: "Breakdown Explainer",
  hookStyle: "Trap Mistake",
  research: null,
  hooks: [],
  selectedHookIdx: 0,
  scriptText: "",
};

function getActiveWorkspace() { return allWorkspaces().find(w => w.id === activeWorkspaceId) || allWorkspaces()[0]; }
function workspaceScopes(ws = getActiveWorkspace()) {
  if (ws.id === "__all__") return SCOPES;
  const set = new Set(ws.scopes || []);
  return SCOPES.filter(s => set.has(s.id));
}
function workspaceCreators(ws = getActiveWorkspace()) {
  if (ws.id === "__all__") return CREATORS;
  const scopeSet = new Set(ws.scopes || []);
  const explicitHandles = new Set((ws.creatorHandles || []).map(h => h.toLowerCase()));
  return CREATORS.filter(c => explicitHandles.has(c.handle.toLowerCase()) || (c.scopes || []).some(s => scopeSet.has(s)));
}
function workspaceRows(ws = getActiveWorkspace()) {
  const reels = allReels();
  if (ws.id === "__all__") return reels;
  const allowed = new Set(workspaceCreators(ws).map(c => c.handle.toLowerCase()));
  const wsOwnedHandles = new Set(Object.values(connectedSocialOverrides[ws.id] || {}).map(x => (x.handle || "").replace(/^@/, "").toLowerCase()).filter(Boolean));
  return reels.filter(r => {
    if (r.customWorkspace) return r.customWorkspace === ws.id;
    if (r.workspaceId) return r.workspaceId === ws.id;
    const ch = (r.creator_handle || r.creator_username || "").toLowerCase();
    return allowed.has(ch) || wsOwnedHandles.has(ch);
  });
}
function scopeRows() {
  const ws = getActiveWorkspace();
  if (activeScope === "__all__") return allReels();
  if (activeScope === "__workspace__") return workspaceRows(ws);
  return allReels().filter(r => r.customWorkspace === ws.id || (CREATOR_MAP.get(r.creator_handle)?.scopes || []).includes(activeScope));
}

function showToast(msg) {
  const el = document.getElementById("toast");
  document.getElementById("toast-msg").textContent = msg;
  el.classList.add("show");
  clearTimeout(el._t);
  el._t = setTimeout(() => el.classList.remove("show"), 2600);
}
function copyText(txt, msg = "Copied to clipboard ✓") {
  navigator.clipboard?.writeText(txt).then(() => showToast(msg)).catch(() => showToast("Ready to copy"));
}
function emitEvent(name, detail) { window.dispatchEvent(new CustomEvent(name, { detail })); }
function syncUrl() {
  const url = new URL(location.href);
  url.searchParams.set("workspace", activeWorkspaceId);
  url.searchParams.set("tab", activeTab);
  if (activeScope && activeScope !== "__workspace__") url.searchParams.set("scope", activeScope);
  else url.searchParams.delete("scope");
  history.replaceState(null, "", url);
}
function saveFeedState() {
  saveJSON(KEYS.completed, [...completed]);
  saveJSON(KEYS.deleted, [...deleted]);
  localStorage.setItem(KEYS.search, searchText);
  localStorage.setItem(KEYS.band, bandFilter);
  localStorage.setItem(KEYS.hideCompleted, hideCompleted ? "1" : "0");
  localStorage.setItem(KEYS.showDeleted, showDeleted ? "1" : "0");
}

// ---- Client-side instant breakdown for pasted single videos ----
function buildClientBreakdown({ url, platform, workspace, tag, transcript }) {
  const cleanText = (transcript || "").trim() || `Single ${platform} video added from ${url}`;
  const firstLine = cleanText.split(/(?<=[\.\!\?])\s+/)[0].slice(0, 180);
  const words = cleanText.split(/\s+/).filter(Boolean);
  const dur = Math.max(15, Math.round(words.length / 2.5));
  const hookCat = /^(stop|don't|never|mistake)/i.test(firstLine) ? "Trap Mistake" : /\?/.test(firstLine) ? "Question" : /\d/.test(firstLine) ? "Case Study" : "Authority";
  const fmtCat = hookCat === "Trap Mistake" ? "Common Trap Mistake" : /step|how to|1\.|2\./i.test(cleanText) ? "Breakdown Explainer" : "Yap / Hot Take";
  const sents = cleanText.split(/(?<=[\.\!\?])\s+/).filter(Boolean);
  const beats = sents.slice(0, 5).map((s, i) => ({
    label: i === 0 ? "Opening Hook" : i === sents.length - 1 ? "Payoff & CTA" : `Beat ${i + 1}`,
    timeRange: `0:${String(i * 6).padStart(2, "0")} – 0:${String((i + 1) * 6).padStart(2, "0")}`,
    text: s,
  }));
  const sc = "custom_" + Date.now();
  const handle = (tag || platform).replace(/^@/, "").replace(/\s+/g, "_").toLowerCase().slice(0, 24) || "custom_video";
  return {
    shortCode: sc, url, thumb: null, hasClip: false, customWorkspace: workspace,
    hook: firstLine, transcript: transcript || "", caption: cleanText,
    plays: 0, likes: 0, comments: 0, engagements: 0, duration: dur,
    posted_human: "Just added", posted_ts: Math.floor(Date.now() / 1000),
    ratio: 5.0, band_class: "strong", band_label: "Custom Analysis", band_color: "#ffc71d",
    creator_handle: handle, creator_username: handle, creator_avatar: null, creator_verified: false,
    breakdown: {
      wordCount: words.length,
      summary: `Custom ${platform} video analyzed inside your ${workspace} workspace using a ${hookCat} hook and ${fmtCat} structure.`,
      beatOverview: `Segmented ${words.length} words into ${beats.length} clear beats.`,
      beats,
      idea: {
        topic: "Custom Inspiration",
        ideaSeed: firstLine,
        uniqueAngle: `Custom ${platform} breakdown tagged "${tag || "Swipe"}".`,
        commonBelief: "Most viewers overlook the structural mechanism behind why this hook stops the scroll.",
        contrarianReality: sents[1] || firstLine,
        supportingEvidence: sents.slice(1, 4),
      },
      hook: {
        category: hookCat,
        formula: firstLine.replace(/\d+/g, "[Number]"),
        spokenHook: firstLine,
        analysis: `Spoken opener is ${firstLine.split(/\s+/).length} words (${hookCat}). Pair with bold 4–6 word on-screen text and immediate visual motion.`,
      },
      format: {
        category: fmtCat,
        description: "Replicable short-form structure captured from your pasted URL/transcript.",
        analysis: "Keep each beat tight and reopen a curiosity loop around the 60% mark.",
        tactics: ["Custom Swipe", "Direct Conversational Delivery"],
      },
      visual: { category: "Studio Set", subCategory: "Direct-to-Camera / Hybrid", visualHook: "Move In Frame", pacingNote: "Cut every 3 seconds; anchor sentence 1 visually." },
      kennedy: {
        elements: {
          origin: { status: /started|years ago|my story/i.test(cleanText) ? "Present" : "Absent", evidence: "Detected from transcript" },
          parables: { status: /story|client|one day/i.test(cleanText) ? "Present" : "Absent", evidence: "Detected from transcript" },
          miracles: { status: /\$\d|\d+%|\d+x/i.test(cleanText) ? "Present" : "Absent", evidence: "Detected from transcript" },
          insiderLanguage: { status: /method|system|framework/i.test(cleanText) ? "Present" : "Absent", evidence: "Detected from transcript" },
          dogma: { status: /never|always|rule|truth/i.test(cleanText) ? "Present" : "Absent", evidence: "Detected from transcript" },
          enemies: { status: /stop|wrong|mistake|guru|broken/i.test(cleanText) ? "Present" : "Absent", evidence: "Detected from transcript" },
          flaws: { status: /failed|wrong|mistake|struggled/i.test(cleanText) ? "Present" : "Absent", evidence: "Detected from transcript" },
        },
        characterVsPlot: /i |my /i.test(cleanText) ? "Balanced" : "Plot-Led",
        polarization: /stop|never|wrong|mistake/i.test(cleanText) ? "Strong" : "Weak",
        magnification: "Moderately Magnified",
        contextAnchor: /today|now|this week|just/i.test(cleanText) ? "Fully Anchored" : "Floating",
        coreStory: "Hybrid",
        deficitScore: 5,
      },
    },
  };
}

// ---- Header scroll & Tabs ----
window.addEventListener("scroll", () => {
  document.getElementById("app-header").classList.toggle("scrolled", window.scrollY > 20);
}, { passive: true });

const TAB_TITLES = {
  today: "Today",
  feed: "Outliers",
  seo: "Keywords & SEO Lab",
  chat: "AI Chat & Coach",
  ideas: "Ideas & Swipe Hooks",
  scripts: "Arsenal & Scripts",
  character: "Brand Brain",
  channels: "Accounts & Tools",
};
const sidebarEl = document.getElementById("app-sidebar");
const sidebarBackdrop = document.getElementById("sidebar-backdrop");
const closeMobileSidebar = () => { sidebarEl?.classList.remove("open"); sidebarBackdrop?.classList.remove("open"); };
document.getElementById("mobile-menu-btn")?.addEventListener("click", () => { sidebarEl?.classList.toggle("open"); sidebarBackdrop?.classList.toggle("open"); });
sidebarBackdrop?.addEventListener("click", closeMobileSidebar);

const tabs = [...document.querySelectorAll('#primary-tablist [role="tab"]')];
function setActiveTab(tabId, { focus = false } = {}) {
  activeTab = tabId;
  localStorage.setItem(KEYS.tab, tabId);
  syncUrl();
  tabs.forEach(btn => {
    const sel = btn.dataset.tab === tabId;
    btn.setAttribute("aria-selected", String(sel));
    btn.tabIndex = sel ? 0 : -1;
    if (sel && focus) btn.focus();
  });
  ["today", "feed", "seo", "chat", "ideas", "scripts", "character", "channels"].forEach(id => {
    const el = document.getElementById(`panel-${id}`);
    if (el) el.hidden = id !== tabId;
  });
  const tt = document.getElementById("topbar-title");
  if (tt) tt.textContent = TAB_TITLES[tabId] || "Outlier Lab";
  const ts = document.getElementById("topbar-sub");
  if (ts) ts.textContent = `${getActiveWorkspace().name} · __TODAY__`;
  closeMobileSidebar();
  emitEvent("outlier:tab-change", { tab: tabId, workspace: activeWorkspaceId });
}
document.getElementById("primary-tablist").addEventListener("click", e => {
  const t = e.target.closest('[role="tab"]');
  if (t) setActiveTab(t.dataset.tab);
});
document.getElementById("primary-tablist").addEventListener("keydown", e => {
  const i = tabs.indexOf(document.activeElement);
  if (i === -1) return;
  let n = i;
  if (e.key === "ArrowRight") n = (i + 1) % tabs.length;
  else if (e.key === "ArrowLeft") n = (i - 1 + tabs.length) % tabs.length;
  else if (e.key === "Home") n = 0;
  else if (e.key === "End") n = tabs.length - 1;
  else return;
  e.preventDefault();
  setActiveTab(tabs[n].dataset.tab, { focus: true });
});
document.getElementById("brand-home-link").addEventListener("click", e => { e.preventDefault(); setActiveTab("today"); window.scrollTo({ top: 0, behavior: "smooth" }); });

// Sub-nav helper
function bindSubNav(navId, prefix) {
  const nav = document.getElementById(navId);
  if (!nav) return;
  nav.addEventListener("click", e => {
    const btn = e.target.closest("[data-sub]");
    if (!btn) return;
    activateSubNav(navId, btn.dataset.sub);
  });
}
function activateSubNav(navId, subId) {
  const nav = document.getElementById(navId);
  nav.querySelectorAll("[data-sub]").forEach(b => {
    const on = b.dataset.sub === subId;
    b.classList.toggle("active", on);
    const panel = document.getElementById(`sub-${b.dataset.sub}`);
    if (panel) panel.hidden = !on;
  });
}
bindSubNav("ideas-subnav");
bindSubNav("scripts-subnav");
bindSubNav("channels-subnav");

// ---- Workspace Switcher ----
const wsTrigger = document.getElementById("ws-trigger");
const wsMenu = document.getElementById("ws-menu");
function closeWsMenu() { wsMenu.hidden = true; wsTrigger.setAttribute("aria-expanded", "false"); }
wsTrigger.addEventListener("click", e => { e.stopPropagation(); const open = wsMenu.hidden; wsMenu.hidden = !open; wsTrigger.setAttribute("aria-expanded", String(open)); });
document.addEventListener("click", e => { if (!e.target.closest(".ws-wrap")) closeWsMenu(); });

function renderWorkspaceControls() {
  const list = allWorkspaces();
  const ws = getActiveWorkspace();
  const badge = document.getElementById("ws-active-badge");
  badge.textContent = ws.initials; badge.style.background = ws.accent; badge.style.color = ws.accentInk;
  document.getElementById("ws-active-name").textContent = ws.name;

  document.getElementById("ws-options").innerHTML = list.map(item => {
    const active = item.id === ws.id;
    const count = workspaceRows(item).filter(r => r.ratio >= 2).length;
    return `
      <button type="button" class="ws-option ${active ? "active" : ""}" role="menuitemradio" aria-checked="${active}" data-ws-id="${escapeHtml(item.id)}">
        <span class="ws-badge" style="background:${escapeHtml(item.accent)};color:${escapeHtml(item.accentInk)}">${escapeHtml(item.initials)}</span>
        <span class="ws-option-info">
          <span class="ws-option-name">${escapeHtml(item.name)} <span style="font-size:11px;font-weight:700;color:var(--ink-3)">· ${count} outliers</span></span>
          <span class="ws-option-desc">${escapeHtml(item.tagline || "")}</span>
        </span>
        ${active ? '<span style="font-weight:800;color:var(--yellow-ink)">✓</span>' : ""}
      </button>`;
  }).join("");

  document.getElementById("hero-ws-pills").innerHTML = list.map(item =>
    `<button type="button" class="hero-ws-pill ${item.id === ws.id ? "active" : ""}" data-ws-id="${escapeHtml(item.id)}">${escapeHtml(item.name)}</button>`
  ).join("");

  const selectHtml = list.filter(w => w.id !== "__all__").map(item =>
    `<option value="${escapeHtml(item.id)}" ${item.id === ws.id ? "selected" : ""}>${escapeHtml(item.name)}</option>`
  ).join("");
  ["sv-workspace", "ch-workspace", "qa-workspace"].forEach(id => { const el = document.getElementById(id); if (el) el.innerHTML = selectHtml; });
  const scSel = document.getElementById("ch-scope");
  if (scSel) scSel.innerHTML = SCOPES.map(s => `<option value="${escapeHtml(s.id)}">${escapeHtml(s.name)}</option>`).join("");
}
function selectWorkspace(wsId) {
  activeWorkspaceId = wsId;
  localStorage.setItem(KEYS.workspace, wsId);
  activeScope = "__workspace__";
  activeFilter = "__all__";
  auditSelectedKey = null;
  renderAll();
  syncUrl();
  showToast(`Switched to ${getActiveWorkspace().name}`);
  emitEvent("outlier:workspace-change", { workspace: getActiveWorkspace() });
}

// ---- Compute Strategy Audit Stats & Success Formula ----
function computeAuditGroups(rows, dim) {
  const map = new Map();
  const add = (key, r) => {
    if (!key) return;
    if (!map.has(key)) map.set(key, []);
    map.get(key).push(r);
  };
  for (const r of rows) {
    const bd = r.breakdown;
    if (!bd) continue;
    if (dim === "topics") add(bd.idea.topic, r);
    else if (dim === "hooks") add(bd.hook.category, r);
    else if (dim === "formats") add(bd.format.category, r);
    else if (dim === "tactics") (bd.format.tactics || []).forEach(t => add(t, r));
    else if (dim === "kennedy") {
      Object.entries(bd.kennedy.elements || {}).forEach(([k, v]) => {
        if (v.status === "Present") add(k.charAt(0).toUpperCase() + k.slice(1).replace(/([A-Z])/g, " $1"), r);
      });
    }
  }
  const allRatios = rows.map(r => r.ratio || 0).sort((a, b) => a - b);
  const wsAvg = allRatios.length ? allRatios.reduce((a, b) => a + b, 0) / allRatios.length : 1;
  return [...map.entries()].map(([name, vids]) => {
    const sorted = [...vids].sort((a, b) => b.ratio - a.ratio);
    const rs = sorted.map(v => v.ratio || 0).sort((a, b) => a - b);
    const med = rs.length ? rs[Math.floor(rs.length / 2)] : 0;
    const uplift = wsAvg > 0 ? Math.round(((med - wsAvg) / wsAvg) * 100) : 0;
    return { name, count: vids.length, median: med, best: sorted[0], videos: sorted, uplift };
  }).sort((a, b) => b.median - a.median);
}

function getSuccessFormula(rows) {
  const topics = computeAuditGroups(rows, "topics");
  const formats = computeAuditGroups(rows, "formats");
  const hooks = computeAuditGroups(rows, "hooks");
  const pick = (arr, off) => arr.length ? arr[off % Math.min(arr.length, 5)] : { name: "AI Workflows", median: 3.0, uplift: 120 };
  return {
    topic: pick(topics, formulaOffset),
    format: pick(formats, formulaOffset),
    hook: pick(hooks, formulaOffset),
  };
}

function renderFormulaInto(elId, rows) {
  const f = getSuccessFormula(rows);
  document.getElementById(elId).innerHTML = `
    <div class="formula-slot s-topic"><span>1. Topic</span><strong>${escapeHtml(f.topic.name)}</strong><small>${f.topic.median.toFixed(1)}× median · ${f.topic.uplift >= 0 ? "+" : ""}${f.topic.uplift}% vs workspace avg</small></div>
    <div class="formula-plus">+</div>
    <div class="formula-slot s-format"><span>2. Storytelling Format</span><strong>${escapeHtml(f.format.name)}</strong><small>${f.format.median.toFixed(1)}× median · ${f.format.uplift >= 0 ? "+" : ""}${f.format.uplift}% vs workspace avg</small></div>
    <div class="formula-plus">+</div>
    <div class="formula-slot s-hook"><span>3. Hook Framework</span><strong>${escapeHtml(f.hook.name)}</strong><small>${f.hook.median.toFixed(1)}× median · ${f.hook.uplift >= 0 ? "+" : ""}${f.hook.uplift}% vs workspace avg</small></div>
  `;
}

// ---- TAB 1: TODAY ----
function renderToday() {
  const ws = getActiveWorkspace();
  const rows = workspaceRows(ws);
  const creators = workspaceCreators(ws);
  const outliers = rows.filter(r => r.ratio >= 2);
  const transcribed = rows.filter(r => (r.transcript || "").trim()).length;

  document.getElementById("hero-eyebrow-text").textContent = `/ ${ws.name.toUpperCase()} WORKSPACE · __TODAY__ /`;
  document.getElementById("hero-heading").innerHTML = ws.id === "__all__"
    ? `Top <span class="gradient-highlight">viral outliers</span> across every workspace.`
    : `What's <span class="gradient-highlight">outperforming</span> for ${escapeHtml(ws.name)} today.`;
  document.getElementById("hero-sub").textContent = `${ws.tagline}. Click any video for its full 6-tab Video & Story Breakdown.`;
  document.getElementById("hero-side-tagline").textContent = ws.tagline;
  document.getElementById("cta-ws-name").textContent = ws.name;
  document.getElementById("hero-stat-outliers").textContent = String(outliers.length);
  document.getElementById("hero-stat-channels").textContent = String(creators.length);
  document.getElementById("hero-stat-reels").textContent = String(rows.length);
  document.getElementById("tab-count-feed").textContent = String(rows.length);
  document.getElementById("tab-count-ideas").textContent = String(outliers.length);

  const plays = rows.map(r => r.plays).sort((a, b) => a - b);
  const mid = Math.floor(plays.length / 2);
  const median = plays.length ? (plays.length % 2 ? plays[mid] : (plays[mid - 1] + plays[mid]) / 2) : 0;
  const top = [...rows].sort((a, b) => b.ratio - a.ratio)[0];
  document.getElementById("kpi-outliers").textContent = String(outliers.length);
  document.getElementById("kpi-outliers-delta").textContent = `${rows.length ? Math.round(100 * outliers.length / rows.length) : 0}% of workspace`;
  document.getElementById("kpi-top").textContent = fmtNum(top?.plays || 0);
  document.getElementById("kpi-top-delta").textContent = top ? `${top.band_label} · ${top.ratio.toFixed(1)}× median` : "No reels yet";
  document.getElementById("kpi-median").textContent = fmtNum(median);
  document.getElementById("kpi-median-delta").textContent = `Across ${creators.length} channels`;
  document.getElementById("kpi-plays").textContent = fmtNum(rows.reduce((n, r) => n + r.plays, 0));
  document.getElementById("kpi-plays-delta").textContent = `${fmtNum(rows.reduce((n, r) => n + r.engagements, 0))} engagements`;
  document.getElementById("kpi-transcripts").textContent = `${transcribed}/${rows.length}`;
  document.getElementById("kpi-transcripts-delta").textContent = `${rows.length ? Math.round(100 * transcribed / rows.length) : 0}% spoken hooks ready`;

  renderFormulaInto("today-formula-slots", rows);

  let pool = rows.filter(r => !deleted.has(r.shortCode));
  if (spotlightMode === "replicable") {
    const rep = pool.filter(r => r.ratio >= 5 && r.ratio < 15);
    pool = (rep.length ? rep : pool.filter(r => r.ratio >= 2)).sort((a, b) => b.ratio - a.ratio);
  } else if (spotlightMode === "recent") {
    const ro = pool.filter(r => r.ratio >= 2);
    pool = (ro.length ? ro : pool).sort((a, b) => b.posted_ts - a.posted_ts);
  } else {
    pool.sort((a, b) => (b.ratio - a.ratio) || (b.plays - a.plays));
  }
  const top5 = pool.slice(0, 5);
  document.getElementById("tab-count-today").textContent = String(top5.length);

  const grid = document.getElementById("spotlight-grid");
  if (!top5.length) {
    grid.innerHTML = `<div class="empty-box" style="grid-column:1/-1"><strong>No reels yet</strong> in this workspace. Add a single video or track a channel to unlock your Top 5 briefing.</div>`;
    return;
  }
  grid.innerHTML = top5.map((r, idx) => {
    const feat = idx < 2;
    const ratioStr = r.ratio ? `${r.ratio.toFixed(1)}×` : "—";
    const thumb = r.thumb ? `thumbs/${escapeHtml(r.thumb)}` : "";
    const bd = r.breakdown || {};
    return `
      <article class="spotlight-card ${feat ? `featured rank-${idx + 1}` : ""}" data-open-reel="${escapeHtml(r.shortCode)}" tabindex="0" role="button">
        <div class="spotlight-thumb">
          ${thumb ? `<img src="${thumb}" alt="" loading="lazy">` : `<div style="display:grid;place-items:center;height:100%;color:#888;font-size:12px">No preview</div>`}
          <span class="spotlight-rank">#${idx + 1}</span>
          <span class="spotlight-play-btn" aria-hidden="true">▶</span>
          <div class="spotlight-thumb-foot"><span class="spotlight-pill">▶ ${fmtNum(r.plays)}</span><span class="spotlight-pill">${fmtDur(r.duration)}</span></div>
        </div>
        <div class="spotlight-body">
          <div class="spotlight-top-meta">
            <span class="band-pill ${escapeHtml(r.band_class)}">${ratioStr} · ${escapeHtml(r.band_label)}</span>
            <span class="creator-mini">${r.creator_avatar ? `<img src="${escapeHtml(r.creator_avatar)}" alt="">` : `<span class="avatar-dot"></span>`}<span>@${escapeHtml(r.creator_username)}</span></span>
          </div>
          <div class="spotlight-hook">“${escapeHtml(r.hook || "No hook")}”</div>
          <div class="tag-row">
            <span class="micro-tag">${escapeHtml(bd.hook?.category || "Hook")}</span>
            ${r.vph ? `<span class="micro-tag">${fmtNum(r.vph)} VPH</span>` : ""}
            ${bd.engine === "claude" || bd.engine === "codex" ? `<span class="status-chip live" style="font-size:10px;padding:2px 8px">✦ ${escapeHtml(bd.engine)}</span>` : ""}
          </div>
          <div class="spotlight-metrics">
            <div class="metric-cluster"><span><strong>${fmtNum(r.plays)}</strong> plays</span><span>♥ ${fmtNum(r.likes)}</span></div>
            <span style="font-size:12px;font-weight:800">Inspect ↗</span>
          </div>
        </div>
      </article>`;
  }).join("");

  // Daily View Predictions (Very High / High / Medium)
  const predGrid = document.getElementById("daily-predictions-grid");
  if (predGrid) {
    const ch = ws.character || {}, off = ws.offer || {};
    const enemyShort = (ch.standAgainst || "overcomplicated tactics").split(",")[0].trim().split(/\s+/).slice(0, 4).join(" ");
    const insiderShort = (ch.sevenElements?.insiderLanguage || ws.name + " System").split(",")[0].trim().split(/\s+/).slice(0, 4).join(" ");
    const topics = computeAuditGroups(rows, "topics");
    const t1 = topics[0]?.name || "AI Workflows";
    const t2 = topics[1]?.name || "Short-Form Hooks";
    const t3 = topics[2]?.name || "Offer Psychology";
    const preds = [
      { tier: "Very High", badge: "live", icon: "🚀", kw: t1.toLowerCase(), title: `Stop Chasing ${enemyShort} — Use This 3-Step ${t1} Fix`, reason: `Top workspace topic (${(topics[0]?.median || 4.2).toFixed(1)}× median) paired with high-contrast Trap Mistake hook.` },
      { tier: "High", badge: "", icon: "↑", kw: t2.toLowerCase(), title: `How ${insiderShort} Beats 99% of ${t2} Advice`, reason: `Injects your brand Insider Language into a proven A vs B Comparison format.` },
      { tier: "Medium", badge: "muted", icon: "●", kw: t3.toLowerCase(), title: `The Real Reason Your ${t3} Isn't Converting (5-Min Audit)`, reason: `Direct buyer-pain search demand aligned with ${off.whatYouSell ? "your core offer CTA" : "inbound conversion"}.` },
    ];
    predGrid.innerHTML = preds.map(p => `
      <article class="panel-card" style="padding:20px;gap:10px">
        <div style="display:flex;justify-content:space-between;align-items:center;gap:8px">
          <span class="status-chip ${p.badge}">${p.icon} ${p.tier} Prediction</span>
          <span style="font-size:11px;font-weight:700;color:var(--ink-3)">${escapeHtml(p.kw)}</span>
        </div>
        <strong style="font-family:var(--font-display);font-size:16.5px;line-height:1.35">${escapeHtml(p.title)}</strong>
        <p style="font-size:12.5px;color:var(--ink-2)">${escapeHtml(p.reason)}</p>
        <div style="display:flex;gap:7px;margin-top:auto;padding-top:6px">
          <button type="button" class="btn btn-outline btn-xs" data-optimize-idea-title="${escapeHtml(p.title)}" data-optimize-idea-kw="${escapeHtml(p.kw)}">Score Title &amp; Tags</button>
          <button type="button" class="btn btn-yellow btn-xs" data-script-idea="${escapeHtml(p.title)}">Write Script →</button>
        </div>
      </article>`).join("");
  }
}

// ---- TAB 2: OUTLIER FEED ----
function renderScopeNav() {
  const ws = getActiveWorkspace();
  const wsScopes = workspaceScopes(ws);
  const items = [
    { id: "__workspace__", name: ws.id === "__all__" ? "All workspaces" : `All ${ws.name}` },
    ...wsScopes,
    ...(ws.id === "__all__" ? [] : [{ id: "__all__", name: "All niche lists" }]),
  ];
  if (!items.some(i => i.id === activeScope)) activeScope = "__workspace__";
  document.getElementById("niche-nav").innerHTML = items.map(s =>
    `<button type="button" data-scope="${escapeHtml(s.id)}" aria-pressed="${s.id === activeScope}" class="${s.id === activeScope ? "active" : ""}">${escapeHtml(s.name)}</button>`
  ).join("");

  const rows = scopeRows();
  const sel = SCOPES.find(s => s.id === activeScope);
  document.getElementById("niche-summary").textContent = sel
    ? `${sel.description} · ${rows.length} analyzed videos.`
    : `${ws.tagline} · ${rows.length} analyzed videos across ${workspaceCreators(ws).length} channels.`;

  const wsCreatorSet = new Set((activeScope === "__workspace__" ? workspaceCreators(ws) : CREATORS.filter(c => activeScope === "__all__" || (c.scopes || []).includes(activeScope))).map(c => c.handle));
  document.querySelectorAll(".creator-chip[data-creator]").forEach(chip => {
    const h = chip.dataset.creator;
    const hide = h !== "__all__" && !wsCreatorSet.has(h);
    chip.hidden = hide; chip.style.display = hide ? "none" : "";
  });
  document.getElementById("all-chip-stats").textContent = `${rows.length} reels · ${rows.filter(r => r.ratio >= 2).length} outliers`;

  // Populate breakdown filter dropdowns
  const fillSel = (id, label, vals, cur) => {
    const el = document.getElementById(id);
    if (!el) return;
    el.innerHTML = `<option value="all">${label}</option>` + [...new Set(vals.filter(Boolean))].sort().map(v =>
      `<option value="${escapeHtml(v)}" ${v === cur ? "selected" : ""}>${escapeHtml(v)}</option>`
    ).join("");
  };
  fillSel("filter-hook-cat", "All Hook Types", rows.map(r => r.breakdown?.hook?.category), hookCatFilter);
  fillSel("filter-format-cat", "All Formats", rows.map(r => r.breakdown?.format?.category), formatCatFilter);
  fillSel("filter-topic", "All Topics", rows.map(r => r.breakdown?.idea?.topic), topicFilter);
  fillSel("vault-hook-cat", "All Hook Categories", workspaceRows(ws).map(r => r.breakdown?.hook?.category), vaultHookCat);

  const adminScope = activeScope === "__workspace__" ? (ws.scopes?.[0] || "__all__") : activeScope;
  const baseAdmin = ["localhost", "127.0.0.1"].includes(location.hostname) ? "/admin" : ADMIN_URL;
  const adminUrl = new URL(baseAdmin, location.href);
  adminUrl.searchParams.set("scope", adminScope);
  document.getElementById("footer-admin-link").href = adminUrl.href;
  adminUrl.hash = "add-creators";
  document.getElementById("add-creator").href = adminUrl.href;
}

function getFiltered() {
  let rows = scopeRows();
  if (activeFilter !== "__all__") rows = rows.filter(r => r.creator_handle === activeFilter);
  if (bandFilter !== "all") rows = rows.filter(r => r.band_class === bandFilter);
  if (hookCatFilter !== "all") rows = rows.filter(r => r.breakdown?.hook?.category === hookCatFilter);
  if (formatCatFilter !== "all") rows = rows.filter(r => r.breakdown?.format?.category === formatCatFilter);
  if (topicFilter !== "all") rows = rows.filter(r => r.breakdown?.idea?.topic === topicFilter);
  if (searchText.trim()) {
    const q = searchText.trim().toLowerCase();
    rows = rows.filter(r =>
      (r.hook || "").toLowerCase().includes(q) || (r.caption || "").toLowerCase().includes(q) ||
      (r.transcript || "").toLowerCase().includes(q) || (r.creator_username || "").toLowerCase().includes(q) ||
      (r.breakdown?.idea?.topic || "").toLowerCase().includes(q)
    );
  }
  if (!showDeleted) rows = rows.filter(r => !deleted.has(r.shortCode));
  if (hideCompleted) rows = rows.filter(r => !completed.has(r.shortCode));
  return rows;
}

function getSortedFiltered() {
  return [...getFiltered()].sort((a, b) => {
    const va = a[sortKey], vb = b[sortKey];
    if (typeof va === "string" || typeof vb === "string") {
      return sortDir === "desc" ? String(vb || "").localeCompare(String(va || "")) : String(va || "").localeCompare(String(vb || ""));
    }
    return sortDir === "desc" ? (vb || 0) - (va || 0) : (va || 0) - (vb || 0);
  });
}

function renderFeed() {
  const filtered = getSortedFiltered();
  document.getElementById("row-count").textContent = `${filtered.length} of ${scopeRows().length}`;
  const status = document.getElementById("filter-status");
  status.innerHTML = activeFilter === "__all__" ? "" : `<span class="status-chip">@${escapeHtml(CREATOR_MAP.get(activeFilter)?.username || activeFilter)} <button type="button" data-clear-creator>×</button></span>`;
  document.querySelectorAll(".creator-chip[data-creator]").forEach(c => c.classList.toggle("active", c.dataset.creator === activeFilter));

  const tbody = document.getElementById("reels-tbody");
  tbody.innerHTML = filtered.length ? filtered.map(r => {
    const ratioStr = r.ratio ? `${r.ratio.toFixed(1)}×` : "—";
    const isDone = completed.has(r.shortCode), isDel = deleted.has(r.shortCode);
    const bd = r.breakdown || {};
    return `
      <tr data-shortcode="${escapeHtml(r.shortCode)}" class="${isDone ? "completed" : ""}">
        <td onclick="event.stopPropagation()">
          <button type="button" class="row-check ${isDone ? "checked" : ""}" data-action="toggle-done" aria-label="Mark studied"></button>
          <button type="button" class="row-delete" data-action="${isDel ? "restore" : "delete"}" title="${isDel ? "Restore" : "Hide"}">${isDel ? "↺" : "×"}</button>
        </td>
        <td><span class="band-pill ${escapeHtml(r.band_class)}">${ratioStr}</span></td>
        <td><strong style="font-size:12.5px">@${escapeHtml(r.creator_username)}</strong></td>
        <td class="hook-cell">
          <span class="row-hook" title="${escapeHtml(r.hook || "")}">${r.hook ? escapeHtml(r.hook) : "<em>no hook</em>"}</span>
          <span class="row-hook-sub">${escapeHtml(bd.idea?.topic || "")} · ${bd.wordCount || 0} words</span>
        </td>
        <td><span class="micro-tag">${escapeHtml(bd.hook?.category || "—")}</span> <span class="micro-tag">${escapeHtml(bd.format?.category || "—")}</span></td>
        <td class="num"><strong>${fmtNum(r.plays)}</strong></td>
        <td class="num">${fmtNum(r.engagements)}</td>
        <td class="num">${fmtDur(r.duration)}</td>
        <td>${escapeHtml(r.posted_human)}</td>
        <td><span style="font-size:12px;font-weight:800">Breakdown ↗</span></td>
      </tr>`;
  }).join("") : `<tr><td colspan="10" style="text-align:center;padding:34px;color:var(--ink-3)">No reels match the current filters.</td></tr>`;

  const grid = document.getElementById("reels-grid");
  grid.innerHTML = filtered.length ? filtered.map(r => {
    const ratioStr = r.ratio ? `${r.ratio.toFixed(1)}×` : "—";
    const thumb = r.thumb ? `thumbs/${escapeHtml(r.thumb)}` : "";
    const bd = r.breakdown || {};
    return `
      <article class="reel-card" data-open-reel="${escapeHtml(r.shortCode)}">
        <div class="thumb">
          ${thumb ? `<img src="${thumb}" alt="" loading="lazy">` : `<div style="display:grid;place-items:center;height:100%;color:#888;font-size:12px">No preview</div>`}
          <div class="thumb-top"><span class="band-pill ${escapeHtml(r.band_class)}">${ratioStr}</span><span class="status-chip live">Analyzed</span></div>
          <span class="thumb-bot">▶ ${fmtNum(r.plays)} · ${fmtDur(r.duration)}</span>
        </div>
        <div class="meta">
          <div class="creator-mini">${r.creator_avatar ? `<img src="${escapeHtml(r.creator_avatar)}" alt="">` : `<span class="avatar-dot"></span>`}<span>@${escapeHtml(r.creator_username)}</span></div>
          <div class="hook">${escapeHtml(r.hook || "(no hook)")}</div>
          <div class="tag-row"><span class="micro-tag">${escapeHtml(bd.hook?.category || "—")}</span><span class="micro-tag">${escapeHtml(bd.format?.category || "—")}</span></div>
          <div class="stats"><span><b>${fmtNum(r.plays)}</b> plays</span><span>♥ ${fmtNum(r.likes)}</span><span>💬 ${fmtNum(r.comments)}</span></div>
        </div>
      </article>`;
  }).join("") : `<div class="empty-box" style="grid-column:1/-1">No reels match the current filters.</div>`;
}

// ---- TAB 3: IDEAS INBOX, HOOK VAULT, PRE-FLIGHT CHECKER, COLLECTIONS, PROJECTS ----
function personalizeIdeaForWorkspace(r, ws) {
  const ch = ws.character || {};
  const off = ws.offer || {};
  const enemy = (ch.standAgainst || "generic hype").split(",")[0].trim();
  const insider = (ch.sevenElements?.insiderLanguage || "your system").split(",")[0].trim();
  const pain = (ch.profits?.pain || "wasted effort").split(",")[0].trim();
  const bd = r.breakdown || {};
  return [
    `Option 1 (${ch.archetype || "Character"} Angle): Reframe "${bd.idea?.topic || "this trend"}" by calling out "${enemy}" and showing how ${insider} eliminates "${pain}" for ${ws.name}.`,
    `Option 2 (Offer Bridge): Use the ${bd.hook?.category || "Authority"} hook + ${bd.format?.category || "Breakdown"} beats, then close with: "${off.ctaMechanism || "DM for the breakdown"}".`,
  ];
}

function renderIdeasAndHooks() {
  const ws = getActiveWorkspace();
  const rows = workspaceRows(ws).filter(r => r.ratio >= 2 || r.customWorkspace === ws.id);
  const inbox = rows.filter(r => !shortlistedIdeas.has(r.shortCode) && !discardedIdeas.has(r.shortCode));
  const shortlist = rows.filter(r => shortlistedIdeas.has(r.shortCode));
  const discarded = rows.filter(r => discardedIdeas.has(r.shortCode));

  document.getElementById("count-ideas-inbox").textContent = String(inbox.length);
  document.getElementById("count-ideas-shortlist").textContent = String(shortlist.length);
  document.getElementById("count-ideas-discarded").textContent = String(discarded.length);

  let visible = ideaBucket === "shortlist" ? shortlist : ideaBucket === "discarded" ? discarded : inbox;
  if (ideaSearch.trim()) {
    const q = ideaSearch.trim().toLowerCase();
    visible = visible.filter(r => (r.hook || "").toLowerCase().includes(q) || (r.breakdown?.idea?.topic || "").toLowerCase().includes(q) || (r.creator_username || "").toLowerCase().includes(q));
  }

  document.getElementById("ideas-grid").innerHTML = visible.slice(0, 24).map(r => {
    const bd = r.breakdown || {};
    const remixes = personalizeIdeaForWorkspace(r, ws);
    const isShort = shortlistedIdeas.has(r.shortCode);
    const note = ideaNotes[r.shortCode] || "";
    return `
      <article class="idea-card ${isShort ? "shortlisted" : ""}">
        <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap">
          <div style="display:flex;gap:6px;align-items:center;flex-wrap:wrap">
            <span class="band-pill ${escapeHtml(r.band_class)}">${r.ratio.toFixed(1)}×</span>
            <span class="status-chip muted">${escapeHtml(bd.idea?.topic || "Strategy")}</span>
            <span class="micro-tag">${escapeHtml(bd.format?.category || "")}</span>
          </div>
          <span style="font-size:12px;font-weight:700;color:var(--ink-3)">@${escapeHtml(r.creator_username)} · ${fmtNum(r.plays)}</span>
        </div>
        <h3 style="font-size:18px;line-height:1.3">“${escapeHtml(bd.idea?.ideaSeed || r.hook)}”</h3>
        <div class="contrast-box">
          <div><strong>Common Belief</strong>${escapeHtml(bd.idea?.commonBelief || "")}</div>
          <div><strong>Contrarian Reality</strong>${escapeHtml(bd.idea?.contrarianReality || "")}</div>
        </div>
        <div class="remix-box">
          <strong style="display:block;font-size:10.5px;text-transform:uppercase;letter-spacing:0.1em;color:var(--yellow-ink);margin-bottom:5px">Personalized for ${escapeHtml(ws.name)} (${escapeHtml(ws.character?.archetype || "Character")})</strong>
          <div style="margin-bottom:5px">${escapeHtml(remixes[0])}</div>
          <div>${escapeHtml(remixes[1])}</div>
        </div>
        <input class="field-input" style="font-size:12.5px;padding:8px 11px" data-idea-note="${escapeHtml(r.shortCode)}" value="${escapeHtml(note)}" placeholder="Your angle notes for filming…">
        <div style="display:flex;gap:7px;flex-wrap:wrap;margin-top:auto">
          <button type="button" class="btn btn-yellow btn-xs" data-launch-script="${escapeHtml(r.shortCode)}">Turn into Script (C) →</button>
          <button type="button" class="btn btn-outline btn-xs" data-open-reel="${escapeHtml(r.shortCode)}">Full Breakdown</button>
          <button type="button" class="btn btn-outline btn-xs" data-toggle-shortlist="${escapeHtml(r.shortCode)}">${isShort ? "✓ Shortlisted" : "Shortlist (S)"}</button>
          <button type="button" class="btn btn-outline btn-xs" data-toggle-discard="${escapeHtml(r.shortCode)}">${discardedIdeas.has(r.shortCode) ? "Restore" : "Discard"}</button>
        </div>
      </article>`;
  }).join("") || `<div class="empty-box" style="grid-column:1/-1">No ideas in this bucket yet.</div>`;

  // Viral Hook Vault
  let hooksPool = workspaceRows(ws).filter(r => r.ratio >= 2 || savedHooks.has(r.shortCode));
  if (vaultHookCat !== "all") hooksPool = hooksPool.filter(r => r.breakdown?.hook?.category === vaultHookCat);
  if (vaultSavedOnly) hooksPool = hooksPool.filter(r => savedHooks.has(r.shortCode));
  document.getElementById("hooks-vault-count").textContent = String(hooksPool.length);
  document.getElementById("hooks-vault-grid").innerHTML = hooksPool.slice(0, 30).map(r => {
    const h = r.breakdown?.hook || {};
    const isSaved = savedHooks.has(r.shortCode);
    return `
      <article class="hook-vault-card">
        <div style="display:flex;justify-content:space-between;align-items:center;gap:6px">
          <span class="status-chip muted">${escapeHtml(h.category || "Hook")}</span>
          <span class="band-pill ${escapeHtml(r.band_class)}">${r.ratio.toFixed(1)}× · ${fmtNum(r.plays)}</span>
        </div>
        <div class="madlib-text">${highlightMadlib(h.formula || r.hook)}</div>
        <div style="font-size:12px;color:var(--ink-3)">Inspired by <strong>@${escapeHtml(r.creator_username)}</strong>: “${escapeHtml((r.hook || "").slice(0, 95))}”</div>
        <div style="display:flex;gap:7px;margin-top:auto">
          <button type="button" class="btn btn-outline btn-xs" data-copy-hook="${escapeHtml(h.formula || r.hook)}">Copy Formula</button>
          <button type="button" class="btn btn-outline btn-xs" data-test-hook="${escapeHtml(r.hook || "")}">Test in Checker</button>
          <button type="button" class="btn btn-outline btn-xs" data-save-hook="${escapeHtml(r.shortCode)}">${isSaved ? "★ Saved" : "☆ Save"}</button>
        </div>
      </article>`;
  }).join("") || `<div class="empty-box" style="grid-column:1/-1">No hooks match this filter.</div>`;

  // Collections & Frameworks
  document.getElementById("collections-body").innerHTML = COLLECTIONS.map(col => `
    <section class="panel-card tone-${escapeHtml(col.tone)}">
      <div class="section-head">
        <div><span class="eyebrow-dot">Creative Format Library</span><h3 style="font-size:24px">${escapeHtml(col.group)}</h3><p style="font-size:13.5px;color:var(--ink-2)">${escapeHtml(col.description)}</p></div>
        <span class="status-chip muted">${col.items.length} patterns</span>
      </div>
      <div class="card-grid-3">
        ${col.items.map(it => {
          const matchCount = workspaceRows(ws).filter(r =>
            (r.breakdown?.format?.category || "").toLowerCase().includes(it.name.toLowerCase().split(" ")[0]) ||
            (r.breakdown?.visual?.visualHook || "").toLowerCase() === it.name.toLowerCase() ||
            (r.breakdown?.visual?.subCategory || "").toLowerCase() === it.name.toLowerCase()
          ).length;
          return `
            <article class="panel-card" style="padding:18px;gap:8px">
              <div style="display:flex;justify-content:space-between;gap:8px"><span class="micro-tag">${escapeHtml(it.sub)}</span>${matchCount ? `<span class="status-chip live">${matchCount} in feed</span>` : ""}</div>
              <strong style="font-family:var(--font-display);font-size:17px">${escapeHtml(it.name)}</strong>
              <p style="font-size:13px;color:var(--ink-2)">${escapeHtml(it.desc)}</p>
            </article>`;
        }).join("")}
      </div>
    </section>
  `).join("");

  // Projects
  document.getElementById("projects-grid").innerHTML = projects.map(p => {
    const vids = p.shortCodes.map(sc => allReels().find(r => r.shortCode === sc)).filter(Boolean);
    return `
      <article class="panel-card">
        <div style="display:flex;justify-content:space-between;align-items:center">
          <div><strong style="font-family:var(--font-display);font-size:20px">${escapeHtml(p.name)}</strong><div style="font-size:12px;color:var(--ink-3)">${vids.length} saved video(s)</div></div>
          <button type="button" class="btn btn-outline btn-xs" data-del-project="${escapeHtml(p.id)}">Delete</button>
        </div>
        ${vids.length ? vids.map(v => `
          <div style="display:flex;justify-content:space-between;align-items:center;gap:10px;padding:10px 12px;border-radius:12px;background:var(--paper)">
            <div style="min-width:0;flex:1"><strong style="font-size:12.5px">@${escapeHtml(v.creator_username)} · ${v.ratio.toFixed(1)}×</strong><div style="font-size:12px;color:var(--ink-2);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${escapeHtml(v.hook)}</div></div>
            <button type="button" class="btn btn-outline btn-xs" data-open-reel="${escapeHtml(v.shortCode)}">Open ↗</button>
          </div>`).join("") : `<div style="font-size:13px;color:var(--ink-3);padding:14px;border-radius:12px;background:var(--paper)">Open any video breakdown and press <span class="kbd">A</span> to save it to this folder.</div>`}
      </article>`;
  }).join("");
}

// ---- Pre-Flight Hook Checker (Hook Genius + Content Principles) ----
function runPreflightCheck() {
  const txt = (document.getElementById("preflight-input")?.value || "").trim();
  const out = document.getElementById("preflight-output");
  if (!out) return;
  if (!txt) { out.innerHTML = `<span class="verdict-pill neutral">Type a hook to test</span>`; return; }
  const words = txt.split(/\s+/).filter(Boolean);
  const traps = [];
  const wins = [];

  if (words.length > 26) traps.push(`Too long (${words.length} words) — trim under 22 words so the viewer prices time cost low.`);
  else wins.push(`Tight opening length (${words.length} words).`);

  if (/^(hey guys|what's up|today i want to|in this video)/i.test(txt)) traps.push("Throat-clearing opener — kills the first 3 seconds. Cut straight to the tension.");
  if (/^(do you want|have you ever|are you still|did you know)\b/i.test(txt)) traps.push("Weak yes/no question opener — viewers silently say 'no' and scroll.");
  if (/\b(it's called the|i call this|meet the)\b/i.test(txt) && txt.indexOf("called") < 35) traps.push("Named framework before promise — earn curiosity before naming the framework.");
  if (/\b(content|growth|engagement|marketing|success)\b/i.test(txt) && !/\b(hook|script|prompt|email|ad|funnel|reply|call|video|reel|offer)\b/i.test(txt)) traps.push("Abstract category word — swap for one concrete craft object (e.g. 'reply rate', 'ad hook', 'Claude prompt').");
  if (/\d/.test(txt)) {
    if (/\b(rule|prompt|step|system|mistake|way|reason|script|method|framework|days|hours|%|x|\$)\b/i.test(txt)) wins.push("Specific number paired with a concrete mechanism/timeframe.");
    else traps.push("Bare number with no mechanism in the same sentence — attach what caused it.");
  } else {
    traps.push("No concrete number, dollar figure, or timeframe — specificity is the cheapest upgrade.");
  }
  if (/!/.test(txt)) traps.push("Exclamation mark reads hypey — calm, declarative authority outperforms.");

  let shape = "Authority / Declarative";
  if (/^(stop|don't|never|the biggest mistake)/i.test(txt)) { shape = "Trap / Mistake Diagnosis"; wins.push("Strong Trap/Mistake pattern interrupt."); }
  else if (/\b(here's how|how to)\b/i.test(txt)) { shape = "How-To Transformation"; wins.push("Clear outcome-driven How-To shape."); }
  else if (/\b(vs\.?|instead of|difference between)\b/i.test(txt)) { shape = "A vs B Contrast"; wins.push("Sharp contrast loop opens immediate curiosity."); }

  const verdict = traps.length === 0 ? ["ships", "✓ Ships — Ready to Film"] : traps.length <= 2 ? ["neutral", "⚠ Fix 1–2 Traps First"] : ["fix", "✕ High Scroll Risk — Rewrite"];
  out.innerHTML = `
    <span class="verdict-pill ${verdict[0]}">${verdict[1]}</span>
    <div style="font-size:12.5px;color:rgba(255,255,255,0.8)">Detected Shape: <strong style="color:var(--yellow)">${escapeHtml(shape)}</strong></div>
    ${wins.map(w => `<div style="font-size:12.5px;color:#b8e6be">✓ ${escapeHtml(w)}</div>`).join("")}
    ${traps.map(t => `<div style="font-size:12.5px;color:#ffb4c8">✕ ${escapeHtml(t)}</div>`).join("")}
  `;
}
document.getElementById("preflight-input").addEventListener("input", runPreflightCheck);
document.getElementById("preflight-sample-trap").addEventListener("click", () => {
  document.getElementById("preflight-input").value = "Hey guys! Do you want to learn 3 tips for better content growth today?! It's called the Synergy Method!";
  runPreflightCheck();
});
document.getElementById("preflight-to-script").addEventListener("click", () => {
  const h = document.getElementById("preflight-input").value.trim();
  wizard.topic = h; wizard.hooks = [{ text: h, by: "Your Pre-Flight Hook", style: "Custom Tested" }]; wizard.selectedHookIdx = 0; wizard.step = 1;
  setActiveTab("scripts"); activateSubNav("scripts-subnav", "script-builder"); renderScriptWizard();
});

// ---- TAB 4: CONTENT STRATEGY AUDIT & 4-STEP SCRIPT BUILDER ----
function renderStrategyAudit() {
  const rows = workspaceRows();
  const groups = computeAuditGroups(rows, auditDim);
  const titles = {
    topics: "Median Outlier Multiple by Topic",
    hooks: "Median Outlier Multiple by Hook Category",
    formats: "Median Outlier Multiple by Storytelling Format",
    tactics: "Median Outlier Multiple by Scriptwriting Tactic",
    kennedy: "Median Outlier Multiple by Magnetism Element",
  };
  document.getElementById("audit-list-title").textContent = titles[auditDim] || "Performance Breakdown";
  renderFormulaInto("audit-formula-slots", rows);

  if (!groups.length) {
    document.getElementById("audit-bars").innerHTML = `<div class="empty-box">No analyzed reels in this workspace yet.</div>`;
    document.getElementById("audit-drilldown").innerHTML = `<p style="color:var(--ink-3)">Add videos to generate a live Content Strategy Audit.</p>`;
    return;
  }
  if (!auditSelectedKey || !groups.some(g => g.name === auditSelectedKey)) auditSelectedKey = groups[0].name;
  const maxMed = Math.max(1, ...groups.map(g => g.median));

  document.getElementById("audit-bars").innerHTML = groups.map(g => `
    <button type="button" class="bar-row ${g.name === auditSelectedKey ? "active" : ""}" data-audit-key="${escapeHtml(g.name)}">
      <div style="display:flex;justify-content:space-between;align-items:center;gap:10px">
        <strong style="font-size:13.5px">${escapeHtml(g.name)}</strong>
        <span style="font-size:12.5px;font-weight:800;font-variant-numeric:tabular-nums">${g.median.toFixed(1)}× median · ${g.count} vids</span>
      </div>
      <div class="bar-track"><div class="bar-fill" style="width:${Math.max(8, Math.round((g.median / maxMed) * 100))}%"></div></div>
    </button>
  `).join("");

  const sel = groups.find(g => g.name === auditSelectedKey) || groups[0];
  document.getElementById("audit-drilldown").innerHTML = `
    <span class="eyebrow-dot">Diagnostic Drilldown</span>
    <h3 style="font-size:23px">${escapeHtml(sel.name)}</h3>
    <div style="display:flex;gap:8px;flex-wrap:wrap">
      <span class="band-pill strong">${sel.median.toFixed(1)}× median outlier</span>
      <span class="status-chip ${sel.uplift >= 0 ? "live" : "warn"}">${sel.uplift >= 0 ? "+" : ""}${sel.uplift}% vs workspace avg</span>
      <span class="status-chip muted">${sel.count} videos</span>
    </div>
    <ul style="margin:4px 0;padding-left:18px;font-size:13.5px;color:var(--ink-2);display:flex;flex-direction:column;gap:6px">
      <li>Top video in this bucket hit <strong>${sel.best.ratio.toFixed(1)}×</strong> (${fmtNum(sel.best.plays)} plays) by <strong>@${escapeHtml(sel.best.creator_username)}</strong>.</li>
      <li>Model the opening structure: “${escapeHtml((sel.best.hook || "").slice(0, 120))}”</li>
      <li>Combine this with your workspace's Stand-Against enemy for maximum polarity.</li>
    </ul>
    <strong style="font-size:11px;text-transform:uppercase;letter-spacing:0.1em;color:var(--ink-3);margin-top:6px">Supporting Videos</strong>
    <div style="display:flex;flex-direction:column;gap:8px;min-width:0">
      ${sel.videos.slice(0, 4).map(v => `
        <button type="button" style="width:100%;max-width:100%;min-width:0;overflow:hidden;text-align:left;padding:10px 12px;border-radius:12px;background:var(--surface);border:1px solid var(--border);display:flex;justify-content:space-between;align-items:center;gap:10px" data-open-reel="${escapeHtml(v.shortCode)}">
          <div style="min-width:0;flex:1;overflow:hidden"><strong style="font-size:12.5px;display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">@${escapeHtml(v.creator_username)} · ${v.ratio.toFixed(1)}×</strong><div style="font-size:12px;color:var(--ink-2);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${escapeHtml(v.hook)}</div></div>
          <span style="font-size:11.5px;font-weight:800;flex-shrink:0;white-space:nowrap">Inspect ↗</span>
        </button>`).join("")}
    </div>
  `;
}

// ---- 4-Step Script Builder ----
function generateResearchBrief() {
  const ws = getActiveWorkspace();
  const ch = ws.character || {}, off = ws.offer || {};
  const src = wizard.sourceShortCode ? allReels().find(r => r.shortCode === wizard.sourceShortCode) : null;
  const topic = wizard.topic || src?.breakdown?.idea?.ideaSeed || "Fixing the #1 bottleneck in your business with AI";
  const enemy = (ch.standAgainst || "overcomplicated tactics").split(",")[0].trim();
  const pain = (ch.profits?.pain || "wasting hours on manual work").split(",")[0].trim();
  const miracle = (ch.sevenElements?.miracles || "verified client results").split(";")[0].trim();
  wizard.research = {
    execSummary: `Deliver one sharp, simplified perspective shift on "${topic}" for ${off.whoYouSellTo || "your target audience"} — leading with your ${ch.archetype || "Character"} voice instead of generic instruction.`,
    engage: `Speak to ONE specific person currently feeling "${pain}". Open a curiosity loop in sentence 1, deliver the first tangible insight by second 8, and reopen a fresh loop at 65% before pitching.`,
    facts: [
      miracle,
      src ? `Reference outlier benchmark: @${src.creator_username} hit ${src.ratio.toFixed(1)}× median (${fmtNum(src.plays)} plays) using ${src.breakdown?.format?.category || "this format"}.` : `Insider anchor: ${(ch.sevenElements?.insiderLanguage || "Your core method").split(",")[0].trim()}.`,
      `Regis Context Anchor: Tie this to a real conversation, client call, or launch from this week so it isn't floating generic advice.`,
    ],
    contrast: [
      `Common Belief: Most people think solving "${topic.slice(0, 60)}" requires more tools or harder hustle.`,
      `Contrarian Reality (${ch.superheroIdentity || ws.name}): Name "${enemy}" as the real culprit — simplify the single bottleneck first.`,
    ],
  };
}

function generateHookDrafts() {
  const ws = getActiveWorkspace();
  const ch = ws.character || {};
  const topic = (wizard.topic || "fixing your workflow bottleneck").replace(/\.$/, "");
  const enemy = (ch.standAgainst || "shiny object hype").split(",")[0].trim();
  const insider = (ch.sevenElements?.insiderLanguage || "the SIMPLE Method").split(",")[0].trim();
  const topRefs = workspaceRows(ws).filter(r => r.ratio >= 2).slice(0, 6);
  const byRef = (i) => topRefs[i] ? `Inspired by @${topRefs[i].creator_username} · ${topRefs[i].ratio.toFixed(1)}× (${fmtNum(topRefs[i].plays)})` : "Proven High-Retention Shape";
  wizard.hooks = [
    { style: "Trap Mistake", by: byRef(0), text: `Stop falling for ${enemy} — here's the exact 3-step fix for ${topic.slice(0, 68)}.` },
    { style: "Authority", by: byRef(1), text: `The only reason ${topic.slice(0, 58)} isn't working yet is you're automating before you diagnose.` },
    { style: "Case Study / Miracle", by: byRef(2), text: `We used ${insider} on ${topic.slice(0, 55)} and cut the manual work in half in 7 days.` },
    { style: "A vs B Contrast", by: byRef(3), text: `Amateurs chase ${enemy}; operators use ${insider} to solve ${topic.slice(0, 55)}.` },
    { style: "Parable / Story", by: byRef(4), text: `Last week a founder came to me stuck on ${topic.slice(0, 58)} — 20 minutes later we spotted the real bottleneck.` },
    { style: "Time-Capped List", by: byRef(5), text: `Here are the 3 moves that fix ${topic.slice(0, 58)} in under 45 seconds.` },
  ];
  wizard.selectedHookIdx = 0;
}

function generateFullScript() {
  const ws = getActiveWorkspace();
  const ch = ws.character || {}, off = ws.offer || {};
  const hook = wizard.hooks[wizard.selectedHookIdx]?.text || wizard.topic;
  const enemy = (ch.standAgainst || "shiny object hype").split(",")[0].trim();
  const insider = (ch.sevenElements?.insiderLanguage || "The SIMPLE Method").split(",")[0].trim();
  const parable = (ch.sevenElements?.parables || "a real client call this week").split(";")[0].trim();
  const miracle = (ch.sevenElements?.miracles || "verified measurable outcomes").split(";")[0].trim();
  const flaw = (ch.sevenElements?.flaws || "I used to overcomplicate this myself before learning restraint.").slice(0, 140);
  const cta = off.ctaMechanism || "Comment 'SIMPLE' and I'll send you the exact breakdown.";

  wizard.scriptText = `[0:00 – 0:04 · HOOK + PATTERN INTERRUPT]
${hook}

[0:05 – 0:14 · CONTEXT + POLARIZATION (NAME THE ENEMY)]
Most people are told to chase ${enemy}.
Honestly? ${flaw}
That's why 90% of operators stay busy without getting leverage.

[0:15 – 0:30 · THE MECHANISM + PROOF (${insider})]
Here's what actually moves the needle — we call it ${insider}.
1. Diagnose the single step leaking time or leads before touching a tool.
2. Simplify the workflow to 3 repeatable beats your team can run without you.
3. Plug AI into the narrowest bottleneck — not the whole business.
Proof: ${miracle}.

[0:31 – 0:42 · CHARACTER PARABLE + CURIOSITY RE-OPEN]
It reminds me of ${parable}.
Once you see that shift, you can't unsee it — and here's the part almost nobody catches:
The goal isn't more tools. It's fewer decisions on your plate every Monday.

[0:43 – 0:52 · PAYOFF + OFFER CTA]
${cta}

---
Character Archetype: ${ch.archetype || "Operator"} | Format: ${wizard.format} | Voice: ${(ch.writingStyle || "").slice(0, 90)}`;
}

function launchScriptFromReel(sc) {
  const r = allReels().find(x => x.shortCode === sc);
  if (!r) return;
  wizard.sourceShortCode = sc;
  wizard.topic = r.breakdown?.idea?.ideaSeed || r.hook;
  wizard.format = r.breakdown?.format?.category || "Breakdown Explainer";
  wizard.hookStyle = r.breakdown?.hook?.category || "Trap Mistake";
  wizard.existingDraft = "";
  wizard.research = null; wizard.hooks = []; wizard.scriptText = ""; wizard.step = 1;
  document.getElementById("reel-dialog").close();
  setActiveTab("scripts");
  activateSubNav("scripts-subnav", "script-builder");
  renderScriptWizard();
  showToast(`Loaded @${r.creator_username}'s structure into Script Builder`);
}

function renderScriptWizard() {
  document.querySelectorAll("#script-wizard-steps .wizard-step").forEach(b => {
    b.classList.toggle("active", Number(b.dataset.wstep) === wizard.step);
  });
  const box = document.getElementById("script-wizard-body");
  const ws = getActiveWorkspace();
  const src = wizard.sourceShortCode ? allReels().find(r => r.shortCode === wizard.sourceShortCode) : null;

  if (wizard.step === 1) {
    box.innerHTML = `
      <span class="eyebrow-dot">Step 1 of 4 · Topic or Fix Existing Script</span>
      <h3 style="font-size:24px">What are we filming for ${escapeHtml(ws.name)}?</h3>
      ${src ? `<div style="padding:12px 15px;border-radius:14px;background:var(--yellow-tint);border:1px solid rgba(255,199,29,0.6);display:flex;justify-content:space-between;align-items:center;gap:10px"><div><strong style="font-size:12.5px">Modeling @${escapeHtml(src.creator_username)} (${src.ratio.toFixed(1)}× · ${escapeHtml(src.breakdown?.format?.category || "")})</strong><div style="font-size:12.5px;color:var(--ink-2)">“${escapeHtml(src.hook)}”</div></div><button type="button" class="btn btn-outline btn-xs" id="wiz-clear-src">Clear</button></div>` : ""}
      <div><label class="field-label" for="wiz-topic">Topic / Core Idea</label><textarea class="field-textarea" id="wiz-topic" rows="3" placeholder="e.g. Why adding AI to a messy sales process makes it worse (and the 3-step SIMPLE fix)">${escapeHtml(wizard.topic)}</textarea></div>
      <div class="form-row-2">
        <div><label class="field-label" for="wiz-format">Storytelling Format</label><select class="field-select" id="wiz-format">${["Breakdown Explainer", "Common Trap Mistake", "A Vs B Comparison", "Listicle", "Case Study", "Personal Learning Epiphany", "Problem Solution", "Yap / Hot Take"].map(f => `<option ${f === wizard.format ? "selected" : ""}>${f}</option>`).join("")}</select></div>
        <div><label class="field-label" for="wiz-hook-style">Target Hook Framework</label><select class="field-select" id="wiz-hook-style">${["Trap Mistake", "Authority", "Case Study", "Comparison", "Tutorial", "Secret Reveal Breakdown", "Personal Experience", "List", "Question"].map(h => `<option ${h === wizard.hookStyle ? "selected" : ""}>${h}</option>`).join("")}</select></div>
      </div>
      <details style="background:var(--paper);padding:14px 16px;border-radius:14px;border:1px solid var(--border)">
        <summary style="cursor:pointer;font-weight:800;font-size:13px">Or fix an existing script draft (optional)</summary>
        <textarea class="field-textarea" id="wiz-draft" style="margin-top:10px" rows="4" placeholder="Paste your rough draft here to tighten pacing, inject your Founder Persona elements, and upgrade the hook...">${escapeHtml(wizard.existingDraft)}</textarea>
      </details>
      <div style="display:flex;justify-content:flex-end"><button type="button" class="btn btn-yellow" id="wiz-next-1">Generate Research Brief →</button></div>
    `;
  } else if (wizard.step === 2) {
    if (!wizard.research) generateResearchBrief();
    const res = wizard.research;
    box.innerHTML = `
      <span class="eyebrow-dot">Step 2 of 4 · Research &amp; Contrast Brief</span>
      <h3 style="font-size:24px">Angle, proof &amp; tension points</h3>
      <div class="card-grid-2">
        <div class="bd-card"><strong style="font-size:12px;text-transform:uppercase;color:var(--ink-3)">Executive Summary</strong><textarea class="field-textarea" id="wiz-res-exec" rows="3">${escapeHtml(res.execSummary)}</textarea></div>
        <div class="bd-card"><strong style="font-size:12px;text-transform:uppercase;color:var(--ink-3)">How to Engage Viewers</strong><textarea class="field-textarea" id="wiz-res-eng" rows="3">${escapeHtml(res.engage)}</textarea></div>
        <div class="bd-card"><strong style="font-size:12px;text-transform:uppercase;color:var(--ink-3)">Surprising Facts &amp; Proof</strong><ul style="margin:0;padding-left:18px;font-size:13px">${res.facts.map(f => `<li>${escapeHtml(f)}</li>`).join("")}</ul></div>
        <div class="bd-card"><strong style="font-size:12px;text-transform:uppercase;color:var(--ink-3)">Contrast Moments (Polarization)</strong><ul style="margin:0;padding-left:18px;font-size:13px">${res.contrast.map(c => `<li>${escapeHtml(c)}</li>`).join("")}</ul></div>
      </div>
      <div style="display:flex;justify-content:space-between"><button type="button" class="btn btn-outline" id="wiz-back-2">← Back</button><button type="button" class="btn btn-yellow" id="wiz-next-2">Generate 6 Hook Drafts →</button></div>
    `;
  } else if (wizard.step === 3) {
    if (!wizard.hooks.length) generateHookDrafts();
    box.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap">
        <div><span class="eyebrow-dot">Step 3 of 4 · Hook Selection</span><h3 style="font-size:24px">Pick your winning opening line</h3></div>
        <button type="button" class="btn btn-outline btn-sm" id="wiz-regen-hooks">↻ Regenerate 6 Hooks</button>
      </div>
      <div class="card-grid-2">
        ${wizard.hooks.map((h, i) => `
          <button type="button" class="panel-card ${i === wizard.selectedHookIdx ? "tone-butter" : ""}" style="text-align:left;padding:18px;cursor:pointer;border-color:${i === wizard.selectedHookIdx ? "var(--yellow-ink)" : "var(--border)"}" data-pick-hook="${i}">
            <div style="display:flex;justify-content:space-between;align-items:center;gap:6px"><span class="status-chip muted">${escapeHtml(h.style)}</span>${i === wizard.selectedHookIdx ? '<span class="status-chip live">✓ Selected</span>' : ""}</div>
            <strong style="font-family:var(--font-display);font-size:16px;line-height:1.35">“${escapeHtml(h.text)}”</strong>
            <span style="font-size:11.5px;color:var(--ink-3)">${escapeHtml(h.by)}</span>
          </button>`).join("")}
      </div>
      <div style="display:flex;justify-content:space-between"><button type="button" class="btn btn-outline" id="wiz-back-3">← Back</button><button type="button" class="btn btn-yellow" id="wiz-next-3">Build Line-by-Line Script →</button></div>
    `;
  } else {
    if (!wizard.scriptText) generateFullScript();
    const wc = wizard.scriptText.trim().split(/\s+/).filter(Boolean).length;
    box.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap">
        <div><span class="eyebrow-dot">Step 4 of 4 · Ready-to-Film Script</span><h3 style="font-size:24px">Beat-by-Beat Script (${wc} words · ~${fmtDur(wc / 2.6)})</h3></div>
        <div style="display:flex;gap:8px;flex-wrap:wrap">
          <button type="button" class="btn btn-outline btn-sm" id="wiz-copy-script">Copy Script</button>
          <button type="button" class="btn btn-outline btn-sm" id="wiz-export-llm">Copy LLM Polish Prompt</button>
          <button type="button" class="btn btn-yellow btn-sm" id="wiz-save-script">Save to Scripts ✓</button>
        </div>
      </div>
      <textarea class="field-textarea" id="wiz-final-script" rows="16" style="font-family:var(--font-sans);font-size:14.5px;line-height:1.7">${escapeHtml(wizard.scriptText)}</textarea>
      <div style="display:flex;justify-content:space-between"><button type="button" class="btn btn-outline" id="wiz-back-4">← Back to Hooks</button><button type="button" class="btn btn-dark btn-sm" id="wiz-reset">Start New Script</button></div>
    `;
  }
}

function renderSavedScripts() {
  document.getElementById("saved-scripts-count").textContent = String(savedScripts.length);
  document.getElementById("saved-scripts-grid").innerHTML = savedScripts.length ? savedScripts.map(s => `
    <article class="panel-card">
      <div style="display:flex;justify-content:space-between;align-items:center;gap:8px">
        <span class="status-chip muted">${escapeHtml(s.workspace)} · ${escapeHtml(s.format)}</span>
        <span style="font-size:11.5px;color:var(--ink-3)">${escapeHtml(s.createdAt?.slice(0, 10) || "")}</span>
      </div>
      <h3 style="font-size:19px">${escapeHtml(s.title)}</h3>
      <pre style="white-space:pre-wrap;font-family:var(--font-sans);font-size:13px;color:var(--ink-2);max-height:180px;overflow-y:auto;background:var(--paper);padding:12px;border-radius:12px;margin:0">${escapeHtml(s.script)}</pre>
      <div style="display:flex;gap:8px"><button type="button" class="btn btn-outline btn-xs" data-copy-script-id="${escapeHtml(s.id)}">Copy</button><button type="button" class="btn btn-outline btn-xs" data-del-script-id="${escapeHtml(s.id)}">Delete</button></div>
    </article>
  `).join("") : `<div class="empty-box" style="grid-column:1/-1">No saved scripts yet. Open any outlier and press <span class="kbd">C</span> or use the 4-Step Script Builder above.</div>`;
}

// ---- TAB 5: BRAND BRAIN STUDIO ----
function renderCharacterStudio() {
  const ws = getActiveWorkspace();
  const off = ws.offer || {};
  const ch = ws.character || {};
  const k7 = ch.sevenElements || {};
  const pr = ch.profits || {};

  document.getElementById("char-ws-label").textContent = ws.name;
  document.getElementById("ch-what-sell").value = off.whatYouSell || "";
  document.getElementById("ch-who-sell").value = off.whoYouSellTo || "";
  document.getElementById("ch-transform").value = off.coreTransformation || "";
  document.getElementById("ch-cta").value = off.ctaMechanism || "";

  document.getElementById("archetype-grid").innerHTML = ARCHETYPES.map(a => `
    <button type="button" class="archetype-opt ${ch.archetype === a.name ? "active" : ""}" data-archetype="${escapeHtml(a.name)}">
      <strong>${escapeHtml(a.name)}</strong>
      <span>${escapeHtml(a.desc)}</span>
    </button>
  `).join("");

  document.getElementById("ch-superhero").value = ch.superheroIdentity || "";
  document.getElementById("ch-mighty").value = ch.mightyTheme || "";
  document.getElementById("ch-stand-for").value = ch.standFor || "";
  document.getElementById("ch-stand-against").value = ch.standAgainst || "";

  document.getElementById("k7-origin").value = k7.origin || "";
  document.getElementById("k7-parables").value = k7.parables || "";
  document.getElementById("k7-miracles").value = k7.miracles || "";
  document.getElementById("k7-language").value = k7.insiderLanguage || "";
  document.getElementById("k7-dogma").value = k7.dogma || "";
  document.getElementById("k7-enemies").value = k7.enemies || "";
  document.getElementById("k7-flaws").value = k7.flaws || "";

  document.getElementById("ch-bond").value = (ch.jamesBondTest || []).join("\n");
  document.getElementById("ch-style").value = ch.writingStyle || "";

  document.getElementById("pr-pain").value = pr.pain || "";
  document.getElementById("pr-results").value = pr.results || "";
  document.getElementById("pr-obstacles").value = pr.obstacles || "";
  document.getElementById("pr-fear").value = pr.fear || "";
  document.getElementById("pr-identity").value = pr.identity || "";
  document.getElementById("pr-triggers").value = pr.triggers || "";
  document.getElementById("pr-dreams").value = pr.dreams || "";

  const filled7 = ["origin", "parables", "miracles", "insiderLanguage", "dogma", "enemies", "flaws"].filter(k => (k7[k] || "").trim().length > 8).length;
  document.getElementById("char-completeness-badge").textContent = `7 Elements: ${filled7}/7 Ready`;
}

async function saveCharacterProfile() {
  const ws = getActiveWorkspace();
  if (ws.id === "__all__") { showToast("Switch to a specific workspace (e.g. AI Simple) to edit its Character"); return; }
  const activeArch = document.querySelector("#archetype-grid .archetype-opt.active")?.dataset.archetype || ws.character?.archetype || ARCHETYPES[0].name;
  wsOverrides[ws.id] = {
    ...(wsOverrides[ws.id] || {}),
    offer: {
      whatYouSell: document.getElementById("ch-what-sell").value.trim(),
      whoYouSellTo: document.getElementById("ch-who-sell").value.trim(),
      coreTransformation: document.getElementById("ch-transform").value.trim(),
      ctaMechanism: document.getElementById("ch-cta").value.trim(),
    },
    character: {
      archetype: activeArch,
      superheroIdentity: document.getElementById("ch-superhero").value.trim(),
      mightyTheme: document.getElementById("ch-mighty").value.trim(),
      standFor: document.getElementById("ch-stand-for").value.trim(),
      standAgainst: document.getElementById("ch-stand-against").value.trim(),
      sevenElements: {
        origin: document.getElementById("k7-origin").value.trim(),
        parables: document.getElementById("k7-parables").value.trim(),
        miracles: document.getElementById("k7-miracles").value.trim(),
        insiderLanguage: document.getElementById("k7-language").value.trim(),
        dogma: document.getElementById("k7-dogma").value.trim(),
        enemies: document.getElementById("k7-enemies").value.trim(),
        flaws: document.getElementById("k7-flaws").value.trim(),
      },
      jamesBondTest: document.getElementById("ch-bond").value.split("\n").map(s => s.trim()).filter(Boolean),
      writingStyle: document.getElementById("ch-style").value.trim(),
      profits: {
        pain: document.getElementById("pr-pain").value.trim(),
        results: document.getElementById("pr-results").value.trim(),
        obstacles: document.getElementById("pr-obstacles").value.trim(),
        fear: document.getElementById("pr-fear").value.trim(),
        identity: document.getElementById("pr-identity").value.trim(),
        triggers: document.getElementById("pr-triggers").value.trim(),
        dreams: document.getElementById("pr-dreams").value.trim(),
      },
    },
  };
  saveJSON(KEYS.wsOverrides, wsOverrides);
  if (["localhost", "127.0.0.1"].includes(location.hostname)) {
    fetch("/api/workspaces", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ workspaces: allWorkspaces().filter(w => w.id !== "__all__") }) }).catch(() => {});
  }
  renderCharacterStudio();
  renderIdeasAndHooks();
  showToast(`Saved ${ws.name} Character & Offer Profile ✓`);
}

// ---- TAB 6: CHANNELS, SOCIALS & SETUP ----
const PLATFORM_META = {
  instagram: { name: "Instagram", icon: "IG" },
  youtube: { name: "YouTube", icon: "YT" },
  tiktok: { name: "TikTok", icon: "TT" },
  facebook: { name: "Facebook", icon: "FB" },
  x: { name: "X / Twitter", icon: "X" },
};
function renderChannelsAndSocials() {
  const ws = getActiveWorkspace();
  const creators = workspaceCreators(ws);
  const rows = workspaceRows(ws);

  document.getElementById("roster-count").textContent = `${creators.length} tracked channels`;
  document.getElementById("roster-grid").innerHTML = creators.map(c => {
    const pct = c.reels_in_window ? Math.round(100 * c.transcripts_ready / c.reels_in_window) : 0;
    return `
      <article class="roster-card">
        <div style="display:flex;align-items:center;gap:11px">
          ${c.profile_pic ? `<img src="${escapeHtml(c.profile_pic)}" alt="" style="width:44px;height:44px;border-radius:50%;object-fit:cover">` : `<div style="width:44px;height:44px;border-radius:50%;background:var(--paper)"></div>`}
          <div style="min-width:0;flex:1"><strong style="display:block;font-size:14.5px">${escapeHtml(c.fullName || c.username)}</strong><span style="font-size:12px;color:var(--ink-3)">@${escapeHtml(c.username)}</span></div>
          <span class="status-chip ${c.trackingEnabled ? "live" : "muted"}">${c.trackingEnabled ? "Active" : "Paused"}</span>
        </div>
        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;padding:10px;border-radius:12px;background:var(--paper);font-size:11.5px">
          <div><strong style="display:block;font-size:14px">${fmtNum(c.followers)}</strong>Followers</div>
          <div><strong style="display:block;font-size:14px">${fmtNum(c.median_plays)}</strong>Median</div>
          <div><strong style="display:block;font-size:14px">${c.reels_in_window}</strong>Reels</div>
        </div>
        <div class="progress-bar"><span style="width:${pct}%"></span></div>
        <button type="button" class="btn btn-outline btn-xs" style="align-self:flex-end" data-jump-creator="${escapeHtml(c.handle)}">View Reels →</button>
      </article>`;
  }).join("") || `<div class="empty-box" style="grid-column:1/-1">No channels tracked yet.</div>`;

  const wsVideos = singleVideos.filter(v => ws.id === "__all__" || v.workspace === ws.id);
  document.getElementById("single-video-queue").innerHTML = wsVideos.slice(0, 6).map(v => `
    <div style="display:flex;justify-content:space-between;align-items:center;gap:10px;padding:10px 12px;border-radius:12px;background:var(--surface);border:1px solid var(--border);font-size:12.5px">
      <div style="min-width:0"><strong style="display:block">${escapeHtml(v.platform.toUpperCase())}${v.tag ? ` · ${escapeHtml(v.tag)}` : ""}</strong><div style="font-family:var(--font-mono);font-size:11px;color:var(--ink-3);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${escapeHtml(v.url)}</div></div>
      ${v.reelObj ? `<button type="button" class="btn btn-yellow btn-xs" data-open-reel="${escapeHtml(v.reelObj.shortCode)}">Open Breakdown ↗</button>` : `<span class="status-chip">Queued</span>`}
    </div>`).join("");

  const wsCh = queuedChannels.filter(c => ws.id === "__all__" || c.workspace === ws.id);
  document.getElementById("channel-queue").innerHTML = wsCh.slice(0, 5).map(c => `
    <div style="display:flex;justify-content:space-between;align-items:center;padding:10px 12px;border-radius:12px;background:var(--surface);border:1px solid var(--border);font-size:12.5px">
      <div><strong>${escapeHtml(c.platform.toUpperCase())}</strong> · ${escapeHtml(c.handles)}</div>
      <span class="status-chip ${c.live ? "live" : ""}">${escapeHtml(c.status)}</span>
    </div>`).join("");

  document.getElementById("coverage-summary").textContent = `Data coverage · ${creators.filter(c => c.reels_in_window > 0).length} of ${creators.length} channels have reels · ${rows.filter(r => (r.transcript || "").trim()).length}/${rows.length} spoken transcripts`;
  document.getElementById("coverage-body").innerHTML = creators.map(c => `<tr><td>@${escapeHtml(c.handle)}</td><td>${c.reels_in_window}</td><td>${c.transcripts_ready}/${c.reels_in_window}</td><td>${c.trackingEnabled ? "Active" : "Paused"}</td><td>${escapeHtml(c.coverage?.requestedAt?.slice(0, 16).replace("T", " ") || "—")}</td></tr>`).join("");

  // My Socials
  const baseSocials = ws.socials?.length ? ws.socials : [
    { platform: "instagram", handle: `@${ws.id}`, followers: "—", medianViews: "—", connected: false },
    { platform: "youtube", handle: `@${ws.id}`, followers: "—", medianViews: "—", connected: false },
    { platform: "tiktok", handle: `@${ws.id}`, followers: "—", medianViews: "—", connected: false },
    { platform: "facebook", handle: `${ws.id}`, followers: "—", medianViews: "—", connected: false },
  ];
  const ov = connectedSocialOverrides[ws.id] || {};
  const socials = baseSocials.map(s => ({ ...s, ...(ov[s.platform] || {}), connected: previewConnectedMode ? true : Boolean(ov[s.platform]?.connected ?? s.connected) }));
  const connCount = socials.filter(s => s.connected).length;
  document.getElementById("socials-subtitle").textContent = `Connect owned Instagram, YouTube, TikTok & Facebook accounts for ${ws.name} — just paste your handle or page URL (no OAuth app needed).`;

  document.getElementById("socials-grid").innerHTML = socials.map(s => {
    const m = PLATFORM_META[s.platform] || { name: s.platform, icon: "◎" };
    return `
      <article class="social-card ${s.connected ? "connected" : ""}">
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span style="width:38px;height:38px;border-radius:10px;background:${s.connected ? "var(--charcoal)" : "var(--paper)"};color:${s.connected ? "var(--yellow)" : "var(--ink)"};display:grid;place-items:center;font-weight:800;font-size:12px">${m.icon}</span>
          <span class="status-chip ${s.connected ? "live" : "muted"}">${s.connected ? "● Connected" : "Not connected"}</span>
        </div>
        <div><strong style="font-family:var(--font-display);font-size:18px;display:block">${m.name}</strong><span style="font-family:var(--font-mono);font-size:12px;color:var(--ink-3)">${escapeHtml(s.handle)}</span></div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;padding:10px;border-radius:12px;background:var(--paper);font-size:11.5px">
          <div><strong style="display:block;font-size:14px">${s.connected ? escapeHtml(s.followers || "Synced") : "—"}</strong>Account</div>
          <div><strong style="display:block;font-size:14px">${s.connected ? escapeHtml(s.medianViews || "—") : "—"}</strong>Median</div>
        </div>
        ${s.note ? `<p style="font-size:11.5px;color:var(--ink-3)">${escapeHtml(s.note)}</p>` : ""}
        <button type="button" class="btn ${s.connected ? "btn-outline" : "btn-yellow"} btn-sm" data-connect-platform="${escapeHtml(s.platform)}" data-default-handle="${escapeHtml(s.handle)}">${s.connected ? "Manage / Sync" : "Connect Account"}</button>
      </article>`;
  }).join("");

  const ownBody = document.getElementById("own-outliers-body");
  const ownStatus = document.getElementById("own-outliers-status");
  if (connCount > 0 || ownOutliersByWorkspace[ws.id]?.length) {
    ownStatus.textContent = previewConnectedMode ? "Connected Preview" : `${connCount} account(s) connected`;
    ownStatus.className = "status-chip live";
    const items = ownOutliersByWorkspace[ws.id]?.length ? ownOutliersByWorkspace[ws.id] : [
      { ratio: "8.4×", band: "strong", platform: "Instagram Reel", hook: `How ${ws.name} fixed one workflow bottleneck and saved 12 hours a week.`, plays: "119K", likes: "6.4K" },
      { ratio: "5.2×", band: "strong", platform: "YouTube Short", hook: `Stop buying new tools until you diagnose this one step in your business.`, plays: "51K", likes: "2.9K" },
      { ratio: "3.1×", band: "good", platform: "TikTok", hook: `3 things we stopped doing this quarter that doubled inbound replies.`, plays: "35K", likes: "1.8K" },
    ];
    ownBody.innerHTML = `<div class="card-grid-3">${items.map((it, i) => `
      <article class="panel-card ${i === 0 ? "tone-butter" : ""}" style="padding:18px;gap:8px;${it.shortCode ? "cursor:pointer" : ""}" ${it.shortCode ? `data-open-reel="${escapeHtml(it.shortCode)}"` : ""}>
        <div style="display:flex;justify-content:space-between;gap:6px"><span class="band-pill ${it.band}">${escapeHtml(it.ratio)}</span><span class="micro-tag">${escapeHtml(it.platform)}</span></div>
        <strong style="font-family:var(--font-display);font-size:16px">“${escapeHtml(it.hook)}”</strong>
        <div style="display:flex;justify-content:space-between;align-items:center;font-size:12px;color:var(--ink-3)"><span><strong>${escapeHtml(it.plays)}</strong> plays · ♥ ${escapeHtml(it.likes)}</span>${it.shortCode ? `<strong style="color:var(--ink)">Breakdown ↗</strong>` : ""}</div>
      </article>`).join("")}</div>`;
  } else {
    ownStatus.textContent = "Connect to pull live outliers";
    ownStatus.className = "status-chip muted";
    ownBody.innerHTML = `<div class="empty-box"><strong style="display:block;margin-bottom:6px">No owned socials connected for ${escapeHtml(ws.name)} yet</strong><p style="font-size:13.5px;margin-bottom:14px">Connect an account above or click Preview Connected Layout to inspect how your personal outliers appear.</p><button type="button" class="btn btn-yellow btn-sm" id="empty-preview-connected">Preview Connected Layout</button></div>`;
  }

  const outliers = rows.filter(r => r.ratio >= 2);
  const topTopics = computeAuditGroups(rows, "topics").slice(0, 3);
  const topHooks = computeAuditGroups(rows, "hooks").slice(0, 3);
  const topK7 = computeAuditGroups(rows, "kennedy").slice(0, 3);
  document.getElementById("trends-grid").innerHTML = `
    <article class="panel-card tone-butter"><span class="eyebrow-dot">Winning Topics</span><h3 style="font-size:20px">Top Topics in ${escapeHtml(ws.name)}</h3>${topTopics.map(t => `<div style="display:flex;justify-content:space-between;font-size:13px;padding:8px 10px;border-radius:10px;background:rgba(255,255,255,0.7)"><span>${escapeHtml(t.name)}</span><strong>${t.median.toFixed(1)}×</strong></div>`).join("")}</article>
    <article class="panel-card tone-lavender"><span class="eyebrow-dot">Winning Hooks</span><h3 style="font-size:20px">Highest-Lift Hook Shapes</h3>${topHooks.map(h => `<div style="display:flex;justify-content:space-between;font-size:13px;padding:8px 10px;border-radius:10px;background:rgba(255,255,255,0.7)"><span>${escapeHtml(h.name)}</span><strong>${h.median.toFixed(1)}×</strong></div>`).join("")}</article>
    <article class="panel-card tone-sage"><span class="eyebrow-dot">Magnetism Signal</span><h3 style="font-size:20px">Most Active Character Elements</h3>${topK7.map(k => `<div style="display:flex;justify-content:space-between;font-size:13px;padding:8px 10px;border-radius:10px;background:rgba(255,255,255,0.7)"><span>${escapeHtml(k.name)}</span><strong>${k.count} vids</strong></div>`).join("") || `<p style="font-size:13px;color:var(--ink-2)">${outliers.length} workspace outliers analyzed.</p>`}</article>
  `;
}

// ---- FULL 6-TAB VIDEO BREAKDOWN DIALOG ----
const reelDialog = document.getElementById("reel-dialog");
const modalVideo = document.getElementById("modal-video");
const modalIframe = document.getElementById("modal-iframe");
const modalClipBadge = document.getElementById("modal-clip-badge");
const modalSourceToggle = document.getElementById("modal-source-toggle");
let modalShortCode = null;
let modalShowingClip = true;

function showClipMode(sc) {
  modalShowingClip = true;
  modalVideo.src = `clips/${sc}.mp4`; modalVideo.hidden = false; modalVideo.play().catch(() => {});
  modalIframe.src = ""; modalIframe.hidden = true;
  modalClipBadge.hidden = false; modalSourceToggle.hidden = false; modalSourceToggle.textContent = "Show full reel ↗";
}
function showIframeMode(sc) {
  modalShowingClip = false;
  modalVideo.pause(); modalVideo.src = ""; modalVideo.hidden = true;
  modalIframe.src = `https://www.instagram.com/p/${sc}/embed/captioned/`; modalIframe.hidden = false;
  modalClipBadge.hidden = true; modalSourceToggle.hidden = false; modalSourceToggle.textContent = "← Back to 3s hook";
}
modalSourceToggle.addEventListener("click", () => { if (!modalShortCode) return; modalShowingClip ? showIframeMode(modalShortCode) : showClipMode(modalShortCode); });

function setBdTab(tabName) {
  document.querySelectorAll("#bd-tabs .bd-tab").forEach(b => b.classList.toggle("active", b.dataset.bdtab === tabName));
  ["transcript", "idea", "hook", "format", "visual", "kennedy"].forEach(id => {
    document.getElementById(`bdpanel-${id}`).hidden = id !== tabName;
  });
}
document.getElementById("bd-tabs").addEventListener("click", e => {
  const b = e.target.closest("[data-bdtab]");
  if (b) setBdTab(b.dataset.bdtab);
});
document.getElementById("bd-tr-mode").addEventListener("click", e => {
  const b = e.target.closest("[data-trmode]");
  if (!b) return;
  document.querySelectorAll("#bd-tr-mode button").forEach(x => x.classList.toggle("active", x === b));
  document.getElementById("bd-tr-beats-view").hidden = b.dataset.trmode !== "beats";
  document.getElementById("bd-tr-para-view").hidden = b.dataset.trmode !== "paragraph";
});

function buildLlmExportPayload(r) {
  const bd = r.breakdown || {};
  const ws = getActiveWorkspace();
  const ch = ws.character || {};
  return `# Video Breakdown Export — @${r.creator_username} (${r.ratio.toFixed(1)}x outlier · ${fmtNum(r.plays)} plays)
URL: ${r.url}
Summary: ${bd.summary}

## Idea Analysis
- Topic: ${bd.idea?.topic}
- Idea Seed: ${bd.idea?.ideaSeed}
- Unique Angle: ${bd.idea?.uniqueAngle}
- Common Belief: ${bd.idea?.commonBelief}
- Contrarian Reality: ${bd.idea?.contrarianReality}

## Hook & Format
- Hook Category: ${bd.hook?.category}
- Mad-Lib Formula: ${bd.hook?.formula}
- Verbatim Spoken Hook: "${bd.hook?.spokenHook}"
- Storytelling Format: ${bd.format?.category}
- Scriptwriting Tactics: ${(bd.format?.tactics || []).join(", ")}
- Visual Layout: ${bd.visual?.category} / ${bd.visual?.subCategory} (Visual Hook: ${bd.visual?.visualHook})

## Magnetic Story Audit
- Character vs Plot: ${bd.kennedy?.characterVsPlot} | Polarization: ${bd.kennedy?.polarization} | Magnification: ${bd.kennedy?.magnification} | Context Anchor: ${bd.kennedy?.contextAnchor} | Deficit: ${bd.kennedy?.deficitScore}/12

## Transcript (${bd.wordCount} words)
${r.transcript || r.caption}

## Remix Target Workspace: ${ws.name}
- Offer: ${ws.offer?.whatYouSell || ""}
- Archetype: ${ch.archetype || ""} | Stand Against: ${ch.standAgainst || ""}
- Insider Language: ${ch.sevenElements?.insiderLanguage || ""}`;
}

function openReelModal(shortCode) {
  const r = allReels().find(x => x.shortCode === shortCode);
  if (!r) return;
  modalShortCode = shortCode;
  const bd = r.breakdown || {};
  const ws = getActiveWorkspace();

  if (r.hasClip) showClipMode(shortCode);
  else if ((r.url || "").includes("instagram.com")) { showIframeMode(shortCode); modalSourceToggle.hidden = true; }
  else { modalVideo.hidden = true; modalIframe.hidden = true; modalClipBadge.hidden = true; modalSourceToggle.hidden = true; }

  document.getElementById("bd-title").textContent = r.hook || `Reel by @${r.creator_username}`;
  const bdg = document.getElementById("bd-badge");
  bdg.className = `band-pill ${r.band_class}`;
  bdg.textContent = `${r.ratio ? r.ratio.toFixed(1) + "× · " : ""}${r.band_label}`;
  document.getElementById("modal-creator").innerHTML = r.creator_avatar
    ? `<img src="${escapeHtml(r.creator_avatar)}" alt=""><span>@${escapeHtml(r.creator_username)}</span>`
    : `<span>@${escapeHtml(r.creator_username)}</span>`;
  document.getElementById("bd-date-dur").textContent = `${r.posted_human} · ${fmtDur(r.duration)}`;
  const engRate = r.plays ? ((r.engagements / r.plays) * 100).toFixed(1) + "%" : "—";
  document.getElementById("bd-metric-pills").innerHTML = `
    <span class="band-pill ${r.band_class}">${r.ratio.toFixed(1)}× Outlier</span>
    <span class="band-pill metric-pill-blue">▶ ${fmtNum(r.plays)} views</span>
    <span class="band-pill metric-pill-lav">${engRate} eng.</span>
  `;

  document.getElementById("bd-act-open").href = r.url || "#";
  document.getElementById("bd-shortlist-lbl").textContent = shortlistedIdeas.has(shortCode) ? "✓ Shortlisted idea" : "Shortlist idea";
  document.getElementById("bd-hook-lbl").textContent = savedHooks.has(shortCode) ? "★ Hook saved" : "Save hook format";
  document.getElementById("bd-done-lbl").textContent = completed.has(shortCode) ? "✓ Studied (Undo)" : "Mark as studied";

  const engBadge = document.getElementById("bd-engine-badge");
  const eng = bd.engine || "local";
  if (eng === "claude" || eng === "anthropic_api") { engBadge.className = "status-chip live"; engBadge.textContent = "✦ Claude Deep Breakdown"; }
  else if (eng === "codex" || eng === "openai_api") { engBadge.className = "status-chip live"; engBadge.textContent = "✦ Codex Deep Breakdown"; }
  else { engBadge.className = "status-chip muted"; engBadge.textContent = "⚡ Instant Local Breakdown"; }
  document.getElementById("bd-platform-badge").textContent = (r.platform || "instagram").toUpperCase();
  const bdProvSel = document.getElementById("bd-ai-provider");
  if (bdProvSel && (activeAiProvider === "claude" || activeAiProvider === "codex")) bdProvSel.value = activeAiProvider;

  document.getElementById("bd-summary").innerHTML = `<strong style="display:block;font-size:10.5px;text-transform:uppercase;letter-spacing:0.1em;color:var(--yellow-ink);margin-bottom:4px">Executive Summary</strong>${escapeHtml(bd.summary || "")}`;

  // Tab 1: Transcript
  document.getElementById("bd-word-count").textContent = `${bd.wordCount || 0} words`;
  document.getElementById("bd-tr-beats-view").innerHTML = `
    <div style="font-size:13px;color:var(--ink-2);font-style:italic">${escapeHtml(bd.beatOverview || "")}</div>
    ${(bd.beats || []).map(b => `
      <div class="beat-item">
        <div class="beat-head"><strong style="font-size:13px">${escapeHtml(b.label)}</strong><span class="beat-time">${escapeHtml(b.timeRange)}</span></div>
        <div style="font-size:13.5px;color:var(--ink-2);line-height:1.58">${escapeHtml(b.text)}</div>
        ${b.why ? `<div style="margin-top:6px;padding:6px 10px;border-radius:8px;background:var(--yellow-tint);font-size:12px;color:var(--ink)"><strong>Retention Job:</strong> ${escapeHtml(b.why)}</div>` : ""}
      </div>`).join("") || `<div style="font-size:13px;color:var(--ink-3)">No spoken transcript available yet.</div>`}
  `;
  document.getElementById("bd-tr-para-view").textContent = r.transcript || "(No spoken transcript yet — caption is below)";
  document.getElementById("bd-caption-text").textContent = r.caption || "(no caption)";

  // Tab 2: Idea Analysis
  const idea = bd.idea || {};
  const remixes = (idea.remixes && idea.remixes.length) ? idea.remixes : personalizeIdeaForWorkspace(r, ws);
  document.getElementById("bdpanel-idea").innerHTML = `
    <div class="bd-card">
      <div style="display:flex;gap:8px;flex-wrap:wrap"><span class="status-chip">${escapeHtml(idea.topic || "General")}</span></div>
      <div><strong class="field-label">Idea Seed</strong><div style="font-family:var(--font-display);font-size:17px">${escapeHtml(idea.ideaSeed || "")}</div></div>
      <div><strong class="field-label">Unique Angle</strong><p style="font-size:13.5px;color:var(--ink-2)">${escapeHtml(idea.uniqueAngle || "")}</p></div>
      <div class="contrast-box">
        <div><strong>Common Belief to Challenge</strong>${escapeHtml(idea.commonBelief || "")}</div>
        <div><strong>Contrarian Reality (Contrast)</strong>${escapeHtml(idea.contrarianReality || "")}</div>
      </div>
      <div><strong class="field-label">Supporting Evidence From Script</strong><ul style="margin:4px 0 0;padding-left:18px;font-size:13px;color:var(--ink-2)">${(idea.supportingEvidence || []).map(e => `<li>${escapeHtml(e)}</li>`).join("") || "<li>No explicit proof claims extracted.</li>"}</ul></div>
      <div class="remix-box"><strong style="display:block;font-size:11px;text-transform:uppercase;letter-spacing:0.1em;color:var(--yellow-ink);margin-bottom:6px">How to Personalize for ${escapeHtml(ws.name)}</strong>${remixes.map(rm => `<div style="margin-bottom:6px">${escapeHtml(rm)}</div>`).join("")}</div>
    </div>`;

  // Tab 3: Hook
  const hk = bd.hook || {};
  document.getElementById("bdpanel-hook").innerHTML = `
    <div class="bd-card">
      <div style="display:flex;justify-content:space-between;align-items:center;gap:8px"><span class="status-chip">${escapeHtml(hk.category || "Hook")}</span><button type="button" class="btn btn-outline btn-xs" data-copy-hook="${escapeHtml(hk.formula || "")}">Copy Formula</button></div>
      <div><strong class="field-label">Mad-Lib Formula</strong><div class="madlib-text">${highlightMadlib(hk.formula || "")}</div></div>
      <div><strong class="field-label">Verbatim Spoken Hook</strong><div style="padding:12px 14px;border-radius:12px;background:var(--surface);border:1px solid var(--border);font-size:14px;font-weight:700">“${escapeHtml(hk.spokenHook || "")}”</div></div>
      ${hk.visualHook ? `<div><strong class="field-label">0–3s Visual &amp; Text Hook Cue</strong><div style="padding:10px 12px;border-radius:12px;background:var(--yellow-tint);border:1px solid rgba(255,199,29,0.5);font-size:13px;font-weight:700">${escapeHtml(hk.visualHook)}</div></div>` : ""}
      <div><strong class="field-label">Hook Alignment &amp; Craft Analysis</strong><p style="font-size:13.5px;color:var(--ink-2)">${escapeHtml(hk.analysis || "")}</p></div>
    </div>`;

  // Tab 4: Storytelling Format
  const fm = bd.format || {};
  document.getElementById("bdpanel-format").innerHTML = `
    <div class="bd-card">
      <div><span class="status-chip">${escapeHtml(fm.category || "Format")}</span></div>
      <div><strong class="field-label">Format Definition</strong><p style="font-size:13.5px;color:var(--ink-2)">${escapeHtml(fm.description || "")}</p></div>
      <div><strong class="field-label">Why This Structure Worked</strong><p style="font-size:13.5px;color:var(--ink-2)">${escapeHtml(fm.analysis || "")}</p></div>
      <div><strong class="field-label">Detected Scriptwriting Tactics</strong><div class="tag-row" style="margin-top:4px">${(fm.tactics || []).map(t => `<span class="status-chip muted">${escapeHtml(t)}</span>`).join("")}</div></div>
    </div>`;

  // Tab 5: Visual Layout
  const vis = bd.visual || {};
  document.getElementById("bdpanel-visual").innerHTML = `
    <div class="bd-card">
      <div class="form-row-2">
        <div style="padding:14px;border-radius:14px;background:var(--surface);border:1px solid var(--border)"><strong class="field-label">Visual Layout Category</strong><div style="font-family:var(--font-display);font-size:18px">${escapeHtml(vis.category || "Studio Set")}</div></div>
        <div style="padding:14px;border-radius:14px;background:var(--surface);border:1px solid var(--border)"><strong class="field-label">Sub-Category</strong><div style="font-family:var(--font-display);font-size:18px">${escapeHtml(vis.subCategory || "Office Room Yap")}</div></div>
      </div>
      <div style="padding:14px;border-radius:14px;background:var(--yellow-tint);border:1px solid rgba(255,199,29,0.55)"><strong class="field-label">Recommended Visual Hook</strong><div style="font-weight:800;font-size:15px">${escapeHtml(vis.visualHook || "Move In Frame")}</div><p style="font-size:13px;color:var(--ink-2);margin-top:4px">${escapeHtml(vis.pacingNote || "")}</p></div>
      ${vis.textCues ? `<div style="padding:14px;border-radius:14px;background:var(--surface);border:1px solid var(--border)"><strong class="field-label">On-Screen Text &amp; B-Roll Recipe</strong><p style="font-size:13px;color:var(--ink-2);margin-top:4px">${escapeHtml(vis.textCues)}</p></div>` : ""}
    </div>`;

  // Tab 6: Magnetic Story Audit
  const dk = bd.kennedy || {};
  const els = dk.elements || {};
  const elNames = [["origin", "1. Origin / Legend"], ["parables", "2. Parables"], ["miracles", "3. Miracles / Proof"], ["insiderLanguage", "4. Insider Language"], ["dogma", "5. Dogma"], ["enemies", "6. Named Enemies"], ["flaws", "7. Flaws & Evolution"]];
  document.getElementById("bdpanel-kennedy").innerHTML = `
    <div class="bd-card">
      <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap">
        <strong style="font-size:15px">6-Dimension Magnetic Story Audit</strong>
        <span class="status-chip ${(dk.deficitScore || 0) <= 5 ? "live" : "warn"}">Character Deficit: ${dk.deficitScore ?? 0}/12</span>
      </div>
      <div class="tag-row">
        <span class="status-chip muted">Payload: ${escapeHtml(dk.characterVsPlot || "—")}</span>
        <span class="status-chip muted">Polarization: ${escapeHtml(dk.polarization || "—")}</span>
        <span class="status-chip muted">Magnification: ${escapeHtml(dk.magnification || "—")}</span>
        <span class="status-chip muted">Regis Context: ${escapeHtml(dk.contextAnchor || "—")}</span>
        <span class="status-chip muted">Core Story: ${escapeHtml(dk.coreStory || "—")}</span>
      </div>
      ${dk.characterRewrite ? `<div class="remix-box"><strong style="display:block;font-size:11px;text-transform:uppercase;letter-spacing:0.1em;color:var(--yellow-ink);margin-bottom:5px">How ${escapeHtml(ws.name)}'s Character Would Open &amp; Reframe This</strong><div style="font-size:13.5px;line-height:1.58">${escapeHtml(dk.characterRewrite)}</div></div>` : ""}
      <div class="k7-grid">
        ${elNames.map(([k, lbl]) => {
          const item = els[k] || { status: "Absent", evidence: "" };
          const pres = item.status === "Present";
          return `<div class="k7-item ${pres ? "present" : ""}"><div style="display:flex;justify-content:space-between;gap:6px;margin-bottom:4px"><strong>${lbl}</strong><span class="status-chip ${pres ? "live" : "muted"}">${item.status}</span></div><div style="font-size:11.5px;color:var(--ink-2)">${escapeHtml(item.evidence)}</div></div>`;
        }).join("")}
      </div>
      <button type="button" class="btn btn-yellow btn-sm" style="align-self:flex-start" data-launch-script="${escapeHtml(r.shortCode)}">Rewrite With ${escapeHtml(ws.name)}'s Character &amp; Offer →</button>
    </div>`;

  setBdTab("transcript");
  if (!reelDialog.open) reelDialog.showModal();
}

function stepModalReel(delta) {
  if (!modalShortCode) return;
  const list = getSortedFiltered();
  const idx = list.findIndex(r => r.shortCode === modalShortCode);
  if (idx === -1) return;
  const next = list[(idx + delta + list.length) % list.length];
  if (next) openReelModal(next.shortCode);
}
document.getElementById("bd-prev").addEventListener("click", () => stepModalReel(-1));
document.getElementById("bd-next").addEventListener("click", () => stepModalReel(1));
document.getElementById("bd-copy-tr").addEventListener("click", () => {
  const r = allReels().find(x => x.shortCode === modalShortCode);
  if (r) copyText(r.transcript || r.caption || "", "Transcript copied ✓");
});
document.getElementById("bd-copy-cap").addEventListener("click", () => {
  const r = allReels().find(x => x.shortCode === modalShortCode);
  if (r) copyText(r.caption || "", "Caption copied ✓");
});

document.getElementById("bd-act-script").addEventListener("click", () => { if (modalShortCode) launchScriptFromReel(modalShortCode); });
document.getElementById("bd-act-shortlist").addEventListener("click", () => {
  if (!modalShortCode) return;
  if (shortlistedIdeas.has(modalShortCode)) shortlistedIdeas.delete(modalShortCode);
  else { shortlistedIdeas.add(modalShortCode); discardedIdeas.delete(modalShortCode); }
  saveJSON(KEYS.shortlistedIdeas, [...shortlistedIdeas]); saveJSON(KEYS.discardedIdeas, [...discardedIdeas]);
  document.getElementById("bd-shortlist-lbl").textContent = shortlistedIdeas.has(modalShortCode) ? "✓ Shortlisted idea" : "Shortlist idea";
  renderIdeasAndHooks(); showToast(shortlistedIdeas.has(modalShortCode) ? "Added to Ideas Shortlist ✓" : "Removed from Shortlist");
});
document.getElementById("bd-act-hook").addEventListener("click", () => {
  if (!modalShortCode) return;
  if (savedHooks.has(modalShortCode)) savedHooks.delete(modalShortCode); else savedHooks.add(modalShortCode);
  saveJSON(KEYS.savedHooks, [...savedHooks]);
  document.getElementById("bd-hook-lbl").textContent = savedHooks.has(modalShortCode) ? "★ Hook saved" : "Save hook format";
  renderIdeasAndHooks(); showToast(savedHooks.has(modalShortCode) ? "Saved to Viral Hook Vault ✓" : "Removed from Hook Vault");
});
document.getElementById("bd-act-llm").addEventListener("click", () => {
  const r = allReels().find(x => x.shortCode === modalShortCode);
  if (r) copyText(buildLlmExportPayload(r), "Full LLM Breakdown copied ✓");
});
document.getElementById("bd-act-done").addEventListener("click", () => {
  if (!modalShortCode) return;
  if (completed.has(modalShortCode)) completed.delete(modalShortCode); else completed.add(modalShortCode);
  saveFeedState(); renderFeed();
  document.getElementById("bd-done-lbl").textContent = completed.has(modalShortCode) ? "✓ Studied (Undo)" : "Mark as studied";
});
document.getElementById("bd-act-project").addEventListener("click", () => {
  if (!modalShortCode) return;
  document.getElementById("proj-select").innerHTML = projects.map(p => `<option value="${escapeHtml(p.id)}">${escapeHtml(p.name)} (${p.shortCodes.length})</option>`).join("");
  document.getElementById("proj-new").value = "";
  document.getElementById("project-dialog").showModal();
});
document.getElementById("save-to-project-form").addEventListener("submit", e => {
  e.preventDefault();
  if (!modalShortCode) return;
  const newName = document.getElementById("proj-new").value.trim();
  let target;
  if (newName) {
    target = { id: "proj_" + Date.now(), name: newName, shortCodes: [] };
    projects.unshift(target);
  } else {
    target = projects.find(p => p.id === document.getElementById("proj-select").value);
  }
  if (target && !target.shortCodes.includes(modalShortCode)) target.shortCodes.unshift(modalShortCode);
  saveJSON(KEYS.projects, projects);
  renderIdeasAndHooks();
  document.getElementById("project-dialog").close();
  showToast(`Saved to "${target?.name}" ✓`);
});

reelDialog.addEventListener("close", () => {
  reelDialog.returnValue = ""; modalVideo.pause(); modalVideo.src = ""; modalIframe.src = ""; modalShortCode = null;
});

// Single-key shortcuts while Breakdown modal is open
document.addEventListener("keydown", e => {
  if (!reelDialog.open) return;
  if (["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement?.tagName)) return;
  const k = e.key.toLowerCase();
  if (e.key === "ArrowLeft") { e.preventDefault(); stepModalReel(-1); }
  else if (e.key === "ArrowRight") { e.preventDefault(); stepModalReel(1); }
  else if (k === "c") { e.preventDefault(); document.getElementById("bd-act-script").click(); }
  else if (k === "s") { e.preventDefault(); document.getElementById("bd-act-shortlist").click(); }
  else if (k === "a") { e.preventDefault(); document.getElementById("bd-act-project").click(); }
  else if (k === "h") { e.preventDefault(); document.getElementById("bd-act-hook").click(); }
  else if (k === "e") { e.preventDefault(); document.getElementById("bd-act-llm").click(); }
  else if (k === "o") { e.preventDefault(); const href = document.getElementById("bd-act-open").href; if (href && href !== "#") window.open(href, "_blank"); }
  else if (k === "r") { e.preventDefault(); document.getElementById("bd-act-done").click(); }
});

// ---- Dialog light-dismiss fallback ----
if (!("closedBy" in HTMLDialogElement.prototype)) {
  const outside = (e, d) => { const r = d.getBoundingClientRect(); return e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom; };
  document.querySelectorAll('dialog[closedby="any"]').forEach(d => {
    let down = false;
    d.addEventListener("pointerdown", e => { down = outside(e, d); });
    d.addEventListener("pointerup", e => { if (down && outside(e, d)) d.close(); });
  });
}
document.addEventListener("click", e => {
  const c = e.target.closest("[data-close-dialog]");
  if (c) c.closest("dialog")?.close();
});

// ---- Quick Add, Single Video & Channel Handlers ----
const quickAddDialog = document.getElementById("quick-add-dialog");
let qaMode = "video", qaPlatform = "instagram";
function openQuickAdd(mode = "video") {
  qaMode = mode;
  document.querySelectorAll("#qa-mode-switch button").forEach(b => b.classList.toggle("active", b.dataset.qaMode === mode));
  document.getElementById("qa-input-label").textContent = mode === "video" ? "Video URL" : "Channel handle(s) or profile URL";
  document.getElementById("qa-input").placeholder = mode === "video" ? "https://www.instagram.com/reel/..." : "@creator_one, @creator_two";
  document.getElementById("qa-transcript-wrap").hidden = mode !== "video";
  document.getElementById("qa-extra-label").textContent = mode === "video" ? "Creator handle or tag" : "Niche list ID (optional)";
  document.getElementById("qa-submit-btn").textContent = mode === "video" ? "Analyze & Open Breakdown →" : "Track Entire Channel →";
  quickAddDialog.showModal();
}
document.getElementById("qa-mode-switch").addEventListener("click", e => { const b = e.target.closest("[data-qa-mode]"); if (b) openQuickAdd(b.dataset.qaMode); });
document.getElementById("qa-platforms").addEventListener("click", e => {
  const p = e.target.closest("[data-platform]"); if (!p) return;
  qaPlatform = p.dataset.platform;
  document.querySelectorAll("#qa-platforms .platform-pill").forEach(x => x.classList.toggle("active", x === p));
});

const isLocalServer = () => ["localhost", "127.0.0.1"].includes(location.hostname);

async function initAiEngineStatus() {
  const chip = document.getElementById("ai-engine-status-chip");
  if (!isLocalServer()) {
    if (chip) { chip.textContent = "Hosted static mode (use localhost:4747 for live Claude/Codex)"; chip.className = "status-chip muted"; }
    return;
  }
  try {
    const r = await fetch("/api/ai/status");
    if (!r.ok) return;
    aiCapabilities = await r.json();
    if (activeAiProvider === "local" && (aiCapabilities.claude || aiCapabilities.codex)) {
      activeAiProvider = aiCapabilities.default || "claude";
      localStorage.setItem("outlier-ai-provider", activeAiProvider);
    }
    const found = [];
    if (aiCapabilities.claude) found.push("Claude CLI ✓");
    if (aiCapabilities.codex) found.push("Codex CLI ✓");
    if (aiCapabilities.ytdlp) found.push("yt-dlp IG/YT/TT/FB ✓");
    if (chip) {
      chip.textContent = found.length ? found.join(" · ") : "Instant Local Mode";
      chip.className = `status-chip ${found.length ? "live" : "muted"}`;
    }
    const sbPill = document.getElementById("sidebar-ai-pill");
    const sbLbl = document.getElementById("sidebar-ai-label");
    if (sbPill && sbLbl) {
      sbPill.classList.toggle("ready", Boolean(aiCapabilities.claude || aiCapabilities.codex));
      sbLbl.textContent = aiCapabilities.claude ? "✦ Claude & Codex Ready" : aiCapabilities.codex ? "✦ Codex CLI Ready" : "Instant Local Mode";
    }
    document.querySelectorAll("#ai-provider-switch button").forEach(b => b.classList.toggle("active", b.dataset.aiProvider === activeAiProvider));
  } catch {}
}

document.getElementById("ai-provider-switch")?.addEventListener("click", e => {
  const b = e.target.closest("[data-ai-provider]"); if (!b) return;
  activeAiProvider = b.dataset.aiProvider;
  localStorage.setItem("outlier-ai-provider", activeAiProvider);
  document.querySelectorAll("#ai-provider-switch button").forEach(x => x.classList.toggle("active", x === b));
  showToast(`AI Engine set to ${b.textContent.trim()} ✓`);
});

document.getElementById("ai-batch-upgrade-btn")?.addEventListener("click", async () => {
  if (!isLocalServer()) { showToast("Open http://127.0.0.1:4747 to run local Claude/Codex batch analysis"); return; }
  const prov = activeAiProvider === "local" ? (aiCapabilities.default || "claude") : activeAiProvider;
  const msg = document.getElementById("ai-batch-status-msg");
  if (msg) msg.textContent = `Running ${prov} on Top 5 outliers…`;
  try {
    const r = await fetch("/api/ai/batch", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ limit: 5, provider: prov, workspaceId: activeWorkspaceId }) });
    const d = await r.json();
    if (!r.ok) { showToast(d.message || "Batch could not start"); return; }
    showToast(`Started ${prov} deep analysis on Top 5 outliers ✦`);
    const poll = setInterval(async () => {
      try {
        const sr = await fetch("/api/ai/batch");
        const st = await sr.json();
        if (!st.running) {
          clearInterval(poll);
          const okCount = (st.results || []).filter(x => x.ok).length;
          if (msg) msg.textContent = st.error ? `Error: ${st.error}` : `✓ Upgraded ${okCount} reels via ${prov} — reload to view all`;
          showToast(`Upgraded ${okCount} reels with ${prov} ✓`);
        }
      } catch { clearInterval(poll); }
    }, 3500);
  } catch { showToast("Could not reach local server on :4747"); }
});

document.getElementById("bd-ai-upgrade")?.addEventListener("click", async () => {
  if (!modalShortCode) return;
  if (!isLocalServer()) { showToast("Open http://127.0.0.1:4747 to run live Claude/Codex deep breakdowns"); return; }
  const btn = document.getElementById("bd-ai-upgrade");
  const prov = document.getElementById("bd-ai-provider")?.value || (aiCapabilities.default || "claude");
  const r = allReels().find(x => x.shortCode === modalShortCode);
  if (!r) return;
  btn.disabled = true; btn.textContent = `Analyzing with ${prov}…`;
  showToast(`Running deep 6-tab video breakdown via ${prov}…`);
  try {
    const resp = await fetch("/api/ai/breakdown", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ shortCode: modalShortCode, provider: prov, workspaceProfile: getActiveWorkspace(), reel: r }),
    });
    const data = await resp.json();
    if (!resp.ok || !data.breakdown) throw new Error(data.message || "Breakdown failed");
    r.breakdown = data.breakdown;
    const sv = singleVideos.find(v => v.id === modalShortCode || v.reelObj?.shortCode === modalShortCode);
    if (sv?.reelObj) { sv.reelObj.breakdown = data.breakdown; saveJSON(KEYS.singleVideos, singleVideos); }
    openReelModal(modalShortCode);
    renderAll();
    showToast(`✦ Upgraded with ${data.breakdown.engine} & saved to disk ✓`);
  } catch (err) {
    showToast(`AI breakdown failed: ${err.message}`);
  } finally {
    btn.disabled = false; btn.textContent = "✦ Deep Analyze with AI";
  }
});

async function handleAddSingleVideo({ url, platform, workspace, tag, transcript }) {
  let finalTranscript = transcript, finalCaption = "", finalPlays = 0, finalDur = 0, finalCreator = tag, finalShortCode = null, aiBreakdown = null;
  if (isLocalServer()) {
    showToast("Fetching video metadata & captions…");
    try {
      const prov = activeAiProvider === "local" ? "" : activeAiProvider;
      const resp = await fetch("/api/videos/analyze", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, platform, workspace, tag, transcript, provider: prov, workspaceProfile: getActiveWorkspace(), autoFetch: true }),
      });
      if (resp.ok) {
        const d = await resp.json();
        const v = d.video || {};
        if (v.transcript) finalTranscript = v.transcript;
        if (v.caption) finalCaption = v.caption;
        if (v.plays) finalPlays = v.plays;
        if (v.duration) finalDur = v.duration;
        if (v.creator_username) finalCreator = v.creator_username;
        if (v.shortCode) finalShortCode = v.shortCode;
        if (v.breakdown) aiBreakdown = v.breakdown;
      }
    } catch {}
  }
  const reelObj = buildClientBreakdown({ url, platform, workspace, tag: finalCreator, transcript: finalTranscript || finalCaption });
  if (finalShortCode) reelObj.shortCode = finalShortCode;
  if (finalPlays) reelObj.plays = finalPlays;
  if (finalDur) reelObj.duration = finalDur;
  if (finalCaption) reelObj.caption = finalCaption;
  if (aiBreakdown) reelObj.breakdown = aiBreakdown;
  const entry = { id: reelObj.shortCode, url, platform, workspace, tag: finalCreator, transcript: finalTranscript, reelObj, createdAt: new Date().toISOString() };
  singleVideos = [entry, ...singleVideos.filter(v => v.id !== entry.id && v.url !== url)];
  saveJSON(KEYS.singleVideos, singleVideos.slice(0, 40));
  renderAll();
  showToast(aiBreakdown ? `✦ Video broken down via ${aiBreakdown.engine} ✓` : "Video broken down & added to workspace ✓");
  emitEvent("outlier:add-video", entry);
  openReelModal(reelObj.shortCode);
}

async function handleAddChannel({ handles, platform, workspace, scope }) {
  let status = "Queued for tracking", live = false;
  if (isLocalServer()) {
    if (platform === "instagram") {
      try {
        const r = await fetch("/api/creators/import", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ handles, scopes: scope ? [scope] : [] }) });
        if (r.ok) { status = "Saved to Local Admin ✓"; live = true; }
      } catch {}
    } else {
      showToast(`Syncing ${platform.toUpperCase()} channel ${handles}…`);
      try {
        const firstHandle = handles.split(/[\n,]+/)[0].trim();
        const r = await fetch("/api/socials/connect", {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ platform, handle: firstHandle, workspaceId: workspace, role: "watchlist", scope: scope || "all", limit: 15 }),
        });
        const d = await r.json();
        if (r.ok && d.ok) {
          status = d.items?.length ? `Synced ${d.items.length} videos ✓` : (d.account?.note || "Saved to Watchlist ✓");
          live = true;
          (d.items || []).forEach(it => {
            const ro = buildClientBreakdown({ url: it.url, platform, workspace, tag: it.creator_username, transcript: it.transcript || it.caption || it.title });
            const _wsId = typeof workspace !== "undefined" ? workspace : ws.id; ro.shortCode = it.shortCode; ro.workspaceId = _wsId; ro.customWorkspace = _wsId; ro.plays = it.plays || 0; ro.likes = it.likes || 0; ro.duration = it.duration || 0; ro.ratio = it.ratio || 1;
            ro.band_class = ro.ratio >= 15 ? "breakout" : ro.ratio >= 5 ? "strong" : ro.ratio >= 2 ? "good" : "normal";
            ro.band_label = ro.ratio >= 15 ? "Breakout" : ro.ratio >= 5 ? "Replicable" : ro.ratio >= 2 ? "Working" : "Normal";
            if (it.breakdown) ro.breakdown = it.breakdown;
            syncedOwnedReels.unshift(ro);
          });
        }
      } catch {}
    }
  }
  // Attach tracked handles to custom workspace so switching workspaces isolates them cleanly
  const targetWs = customWorkspaces.find(w => w.id === workspace);
  if (targetWs) {
    targetWs.creatorHandles = targetWs.creatorHandles || [];
    handles.split(/[\n,]+/).map(h => h.trim().replace(/^@/, "").replace(/^https?:\/\/[^/]+\/@?/i, "").split("/")[0].toLowerCase()).filter(Boolean).forEach(h => {
      if (!targetWs.creatorHandles.includes(h)) targetWs.creatorHandles.push(h);
    });
    saveJSON(KEYS.customWorkspaces, customWorkspaces);
  }
  const entry = { id: "ch_" + Date.now(), handles, platform, workspace, scope, status, live, createdAt: new Date().toISOString() };
  queuedChannels.unshift(entry);
  saveJSON(KEYS.queuedChannels, queuedChannels.slice(0, 30));
  renderAll();
  showToast(live ? `${platform.toUpperCase()}: ${status}` : "Channel queued ✓");
  emitEvent("outlier:add-channel", entry);
}

document.getElementById("qa-form").addEventListener("submit", async e => {
  e.preventDefault();
  const val = document.getElementById("qa-input").value.trim();
  const ws = document.getElementById("qa-workspace").value;
  const extra = document.getElementById("qa-extra").value.trim();
  const tr = document.getElementById("qa-transcript").value.trim();
  if (!val) return;
  quickAddDialog.close();
  if (qaMode === "video") await handleAddSingleVideo({ url: val, platform: qaPlatform, workspace: ws, tag: extra, transcript: tr });
  else await handleAddChannel({ handles: val, platform: qaPlatform, workspace: ws, scope: extra || SCOPES[0]?.id });
  e.target.reset();
});
document.querySelectorAll("[data-platform-group]").forEach(g => g.addEventListener("click", e => {
  const p = e.target.closest("[data-platform]"); if (p) g.querySelectorAll(".platform-pill").forEach(x => x.classList.toggle("active", x === p));
}));
document.getElementById("inline-single-video-form").addEventListener("submit", async e => {
  e.preventDefault();
  const platform = document.querySelector('[data-platform-group="single-video"] .platform-pill.active')?.dataset.platform || "instagram";
  await handleAddSingleVideo({
    url: document.getElementById("sv-url").value.trim(), platform,
    workspace: document.getElementById("sv-workspace").value,
    tag: document.getElementById("sv-tag").value.trim(),
    transcript: document.getElementById("sv-transcript").value.trim(),
  });
  e.target.reset();
});
document.getElementById("inline-channel-form").addEventListener("submit", async e => {
  e.preventDefault();
  const platform = document.querySelector('[data-platform-group="channel"] .platform-pill.active')?.dataset.platform || "instagram";
  await handleAddChannel({
    handles: document.getElementById("ch-handles").value.trim(), platform,
    workspace: document.getElementById("ch-workspace").value, scope: document.getElementById("ch-scope").value,
  });
  e.target.reset();
});

// ---- Create Workspace & Connect Social Dialogs ----
const wsDialog = document.getElementById("workspace-dialog");
let newWsAccent = "#ffc71d", newWsInk = "#1f1f1f";
document.getElementById("open-create-ws").addEventListener("click", () => {
  closeWsMenu();
  document.getElementById("new-ws-scopes").innerHTML = SCOPES.map(s => `<label style="display:inline-flex;align-items:center;gap:6px;padding:6px 11px;border-radius:999px;background:var(--paper);border:1px solid var(--border);font-size:12px;font-weight:700"><input type="checkbox" value="${escapeHtml(s.id)}"> ${escapeHtml(s.name)}</label>`).join("") + `<p style="width:100%;font-size:11.5px;color:var(--ink-3);margin-top:4px">Leave unchecked to start this workspace 100% clean with its own channels, socials &amp; brand brain.</p>`;
  wsDialog.showModal();
});
document.getElementById("ws-color-swatches").addEventListener("click", e => {
  const sw = e.target.closest(".color-swatch"); if (!sw) return;
  newWsAccent = sw.dataset.accent; newWsInk = sw.dataset.ink;
  document.querySelectorAll(".color-swatch").forEach(x => x.classList.toggle("active", x === sw));
});
document.getElementById("create-ws-form").addEventListener("submit", e => {
  e.preventDefault();
  const name = document.getElementById("new-ws-name").value.trim(); if (!name) return;
  const initials = (document.getElementById("new-ws-initials").value.trim() || name.split(/\s+/).map(w => w[0]).join("").slice(0, 2)).toUpperCase();
  const tagline = document.getElementById("new-ws-tagline").value.trim() || `${name} outlier intelligence & content studio`;
  const scopes = [...document.querySelectorAll("#new-ws-scopes input:checked")].map(i => i.value);
  const id = name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || ("ws-" + Date.now());
  const ws = {
    id, name, initials, accent: newWsAccent, accentInk: newWsInk, tagline,
    scopes, creatorHandles: [], isCustom: true,
    socials: [
      { platform: "instagram", handle: "@" + id, followers: "—", medianViews: "—", connected: false },
      { platform: "youtube", handle: "@" + id, followers: "—", medianViews: "—", connected: false },
      { platform: "tiktok", handle: "@" + id, followers: "—", medianViews: "—", connected: false },
      { platform: "facebook", handle: id, followers: "—", medianViews: "—", connected: false },
    ],
    offer: { whatYouSell: tagline },
    character: { archetype: ARCHETYPES[0].name, sevenElements: {}, profits: {}, jamesBondTest: [] }
  };
  customWorkspaces.push(ws); saveJSON(KEYS.customWorkspaces, customWorkspaces);
  if (isLocalServer()) {
    fetch("/api/workspaces", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ workspaces: allWorkspaces().filter(w => w.id !== "__all__") }) }).catch(() => {});
  }
  e.target.reset(); wsDialog.close(); selectWorkspace(ws.id);
});

const connectDialog = document.getElementById("connect-social-dialog");
document.getElementById("connect-social-form").addEventListener("submit", async e => {
  e.preventDefault();
  const ws = getActiveWorkspace(), platform = document.getElementById("cs-platform").value, handle = document.getElementById("cs-handle").value.trim();
  const verifyCode = document.getElementById("cs-verify-code")?.textContent || "";
  if (!handle) return;
  const subBtn = document.getElementById("cs-submit-btn");
  if (subBtn) { subBtn.disabled = true; subBtn.textContent = "Syncing account…"; }

  let syncedMeta = { handle, connected: true, syncedAt: new Date().toISOString() };
  if (isLocalServer()) {
    showToast(`Syncing ${handle} (${platform.toUpperCase()})…`);
    try {
      const resp = await fetch("/api/socials/connect", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ workspaceId: ws.id, platform, handle, role: "owned", verifiedCode: verifyCode, limit: 15 }),
      });
      const data = await resp.json();
      if (resp.ok && data.ok) {
        const acc = data.account || {};
        syncedMeta = {
          handle: acc.handle || handle,
          connected: true,
          syncedAt: acc.syncedAt || new Date().toISOString(),
          followers: acc.followers && acc.followers !== "—" ? acc.followers : (acc.followerCount ? fmtNum(acc.followerCount) : (acc.videoCount ? `${acc.videoCount} vids` : "Connected")),
          medianViews: acc.medianViews ? fmtNum(acc.medianViews) : "—",
          videoCount: acc.videoCount || 0,
          note: acc.note || "",
        };
        if (data.items?.length) {
          const cards = data.items.slice(0, 9).map(it => {
            const ro = buildClientBreakdown({ url: it.url, platform, workspace: ws.id, tag: it.creator_username || handle, transcript: it.transcript || it.caption || it.title });
            const _wsId = typeof workspace !== "undefined" ? workspace : ws.id; ro.shortCode = it.shortCode; ro.workspaceId = _wsId; ro.customWorkspace = _wsId; ro.plays = it.plays || 0; ro.likes = it.likes || 0; ro.duration = it.duration || 0; ro.ratio = it.ratio || 1;
            ro.band_class = ro.ratio >= 15 ? "breakout" : ro.ratio >= 5 ? "strong" : ro.ratio >= 2 ? "good" : "normal";
            ro.band_label = ro.ratio >= 15 ? "Breakout" : ro.ratio >= 5 ? "Replicable" : ro.ratio >= 2 ? "Working" : "Normal";
            if (it.breakdown) ro.breakdown = it.breakdown;
            syncedOwnedReels.unshift(ro);
            return {
              shortCode: it.shortCode,
              ratio: `${(it.ratio || 1).toFixed(1)}×`,
              band: ro.band_class,
              platform: `${platform.toUpperCase()} · ${acc.handle || handle}`,
              hook: it.title || it.caption || "Synced Video",
              plays: fmtNum(it.plays || 0),
              likes: fmtNum(it.likes || 0),
            };
          });
          ownOutliersByWorkspace[ws.id] = [...cards, ...(ownOutliersByWorkspace[ws.id] || []).filter(x => !cards.some(c => c.shortCode === x.shortCode))].slice(0, 12);
        }
      }
    } catch {}
  }

  if (!connectedSocialOverrides[ws.id]) connectedSocialOverrides[ws.id] = {};
  connectedSocialOverrides[ws.id][platform] = syncedMeta;
  saveJSON(KEYS.connectedSocials, connectedSocialOverrides);
  if (subBtn) { subBtn.disabled = false; subBtn.textContent = "Connect & Sync Now →"; }
  connectDialog.close();
  renderChannelsAndSocials();
  showToast(`Connected ${syncedMeta.handle} (${platform.toUpperCase()}) ✓`);
  emitEvent("outlier:connect-social", { workspaceId: ws.id, platform, handle: syncedMeta.handle });
});

// ---- Export Feed CSV/JSON & Portable Workspace Backup ----
document.getElementById("export-feed-btn").addEventListener("click", () => {
  const rows = getSortedFiltered();
  const header = ["outlier_ratio", "creator", "topic", "hook_category", "format", "plays", "likes", "comments", "duration_s", "posted", "hook", "url"];
  const csv = [header.join(","), ...rows.map(r => [
    r.ratio.toFixed(2), r.creator_username, r.breakdown?.idea?.topic || "", r.breakdown?.hook?.category || "", r.breakdown?.format?.category || "",
    r.plays, r.likes, r.comments, Math.round(r.duration || 0), r.posted_human, r.hook || "", r.url || ""
  ].map(v => `"${String(v).replaceAll('"', '""')}"`).join(","))].join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = `outlier-lab-${activeWorkspaceId}.csv`; a.click();
  showToast(`Exported ${rows.length} videos as CSV ✓`);
});

document.getElementById("export-backup-btn").addEventListener("click", () => {
  const payload = { version: 2, exportedAt: new Date().toISOString(), customWorkspaces, wsOverrides, singleVideos, queuedChannels, shortlistedIdeas: [...shortlistedIdeas], savedHooks: [...savedHooks], projects, savedScripts };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = `aisimple-outlier-lab-backup.json`; a.click();
  showToast("Full workspace backup exported ✓");
});
document.getElementById("import-backup-input").addEventListener("change", async e => {
  const file = e.target.files?.[0]; if (!file) return;
  try {
    const data = JSON.parse(await file.text());
    if (Array.isArray(data.customWorkspaces)) { customWorkspaces = data.customWorkspaces; saveJSON(KEYS.customWorkspaces, customWorkspaces); }
    if (data.wsOverrides) { wsOverrides = data.wsOverrides; saveJSON(KEYS.wsOverrides, wsOverrides); }
    if (Array.isArray(data.singleVideos)) { singleVideos = data.singleVideos; saveJSON(KEYS.singleVideos, singleVideos); }
    if (Array.isArray(data.projects)) { projects = data.projects; saveJSON(KEYS.projects, projects); }
    if (Array.isArray(data.savedScripts)) { savedScripts = data.savedScripts; saveJSON(KEYS.savedScripts, savedScripts); }
    renderAll(); showToast("Workspace backup imported ✓");
  } catch { showToast("Could not parse backup JSON"); }
});

// ---- All Click & Form Event Wiring ----
document.getElementById("open-quick-add").addEventListener("click", () => openQuickAdd("video"));
document.getElementById("hero-add-btn").addEventListener("click", () => openQuickAdd("video"));
document.getElementById("feed-quick-add").addEventListener("click", () => openQuickAdd("video"));
document.getElementById("add-creator-chip").addEventListener("click", () => openQuickAdd("channel"));
document.getElementById("hero-seo-btn")?.addEventListener("click", () => setActiveTab("seo"));
document.getElementById("today-open-seo")?.addEventListener("click", () => setActiveTab("seo"));
document.getElementById("hero-socials-btn").addEventListener("click", () => { setActiveTab("channels"); activateSubNav("channels-subnav", "ch-socials"); });
document.getElementById("hero-script-btn").addEventListener("click", () => { setActiveTab("scripts"); activateSubNav("scripts-subnav", "script-builder"); renderScriptWizard(); });
document.getElementById("hero-character-btn").addEventListener("click", () => setActiveTab("character"));
document.getElementById("hero-setup-btn").addEventListener("click", () => { setActiveTab("channels"); activateSubNav("channels-subnav", "ch-setup"); });
document.getElementById("spotlight-see-all").addEventListener("click", () => setActiveTab("feed"));
document.getElementById("cta-open-character").addEventListener("click", () => setActiveTab("character"));
document.getElementById("cta-open-ideas").addEventListener("click", () => setActiveTab("ideas"));
document.getElementById("cta-open-scripts").addEventListener("click", () => { setActiveTab("scripts"); activateSubNav("scripts-subnav", "script-builder"); renderScriptWizard(); });
document.getElementById("cta-open-socials").addEventListener("click", () => { setActiveTab("channels"); activateSubNav("channels-subnav", "ch-socials"); });

const shuffleFormula = () => { formulaOffset++; renderToday(); renderStrategyAudit(); };
document.getElementById("today-shuffle-formula").addEventListener("click", shuffleFormula);
document.getElementById("audit-shuffle-formula").addEventListener("click", shuffleFormula);
const formulaToScript = () => {
  const f = getSuccessFormula(workspaceRows());
  wizard.sourceShortCode = null; wizard.topic = `${f.topic.name} for ${getActiveWorkspace().name}`; wizard.format = f.format.name; wizard.hookStyle = f.hook.name;
  wizard.research = null; wizard.hooks = []; wizard.scriptText = ""; wizard.step = 1;
  setActiveTab("scripts"); activateSubNav("scripts-subnav", "script-builder"); renderScriptWizard();
};
document.getElementById("today-formula-script").addEventListener("click", formulaToScript);
document.getElementById("audit-formula-script").addEventListener("click", formulaToScript);

document.getElementById("spotlight-mode").addEventListener("click", e => {
  const b = e.target.closest("[data-mode]"); if (!b) return;
  spotlightMode = b.dataset.mode;
  document.querySelectorAll("#spotlight-mode button").forEach(x => x.classList.toggle("active", x === b));
  renderToday();
});
document.getElementById("niche-nav").addEventListener("click", e => {
  const b = e.target.closest("[data-scope]"); if (!b) return;
  activeScope = b.dataset.scope; localStorage.setItem(KEYS.scope, activeScope); activeFilter = "__all__";
  syncUrl(); renderScopeNav(); renderFeed();
});
document.getElementById("idea-bucket-switch").addEventListener("click", e => {
  const b = e.target.closest("[data-bucket]"); if (!b) return;
  ideaBucket = b.dataset.bucket;
  document.querySelectorAll("#idea-bucket-switch button").forEach(x => x.classList.toggle("active", x === b));
  renderIdeasAndHooks();
});
document.getElementById("idea-search").addEventListener("input", e => { ideaSearch = e.target.value; renderIdeasAndHooks(); });
document.getElementById("vault-hook-cat").addEventListener("change", e => { vaultHookCat = e.target.value; renderIdeasAndHooks(); });
document.getElementById("vault-saved-only").addEventListener("click", e => { vaultSavedOnly = !vaultSavedOnly; e.target.classList.toggle("on", vaultSavedOnly); renderIdeasAndHooks(); });
document.getElementById("new-project-form").addEventListener("submit", e => {
  e.preventDefault();
  const n = document.getElementById("new-project-name").value.trim(); if (!n) return;
  projects.unshift({ id: "proj_" + Date.now(), name: n, shortCodes: [] });
  saveJSON(KEYS.projects, projects); e.target.reset(); renderIdeasAndHooks(); showToast(`Created folder "${n}" ✓`);
});
document.getElementById("audit-dim-switch").addEventListener("click", e => {
  const b = e.target.closest("[data-dim]"); if (!b) return;
  auditDim = b.dataset.dim; auditSelectedKey = null;
  document.querySelectorAll("#audit-dim-switch button").forEach(x => x.classList.toggle("active", x === b));
  renderStrategyAudit();
});
document.getElementById("script-wizard-steps").addEventListener("click", e => {
  const b = e.target.closest("[data-wstep]"); if (!b) return;
  wizard.step = Number(b.dataset.wstep); renderScriptWizard();
});
document.getElementById("save-character-btn").addEventListener("click", saveCharacterProfile);
document.getElementById("export-character-md").addEventListener("click", () => {
  const ws = getActiveWorkspace(), ch = ws.character || {}, k7 = ch.sevenElements || {}, off = ws.offer || {};
  copyText(`# ${ws.name} — Founder Persona & Offer Bible\n\n**Offer:** ${off.whatYouSell}\n**Audience:** ${off.whoYouSellTo}\n**Archetype:** ${ch.archetype} (${ch.superheroIdentity})\n**Mighty Theme:** ${ch.mightyTheme}\n**Stand FOR:** ${ch.standFor}\n**Stand AGAINST:** ${ch.standAgainst}\n\n## 7 Elements\n1. Origin: ${k7.origin}\n2. Parables: ${k7.parables}\n3. Miracles: ${k7.miracles}\n4. Insider Language: ${k7.insiderLanguage}\n5. Dogma: ${k7.dogma}\n6. Enemies: ${k7.enemies}\n7. Flaws: ${k7.flaws}\n\n## James Bond Test\n${(ch.jamesBondTest || []).map((x, i) => `${i + 1}. ${x}`).join("\n")}`, "Character Bible copied ✓");
});
document.getElementById("preview-connected-toggle").addEventListener("click", e => {
  previewConnectedMode = !previewConnectedMode; e.target.classList.toggle("on", previewConnectedMode);
  e.target.textContent = previewConnectedMode ? "✓ Previewing connected state" : "Preview connected layout";
  renderChannelsAndSocials();
});
document.getElementById("sync-all-socials").addEventListener("click", async () => {
  const ws = getActiveWorkspace();
  if (!isLocalServer()) { showToast("Open http://127.0.0.1:4747 to run live social sync"); return; }
  const ov = connectedSocialOverrides[ws.id] || {};
  const targets = (ws.socials || []).map(s => ({ platform: s.platform, handle: ov[s.platform]?.handle || s.handle, connected: Boolean(ov[s.platform]?.connected ?? s.connected) })).filter(x => x.connected && x.handle);
  if (!targets.length) { showToast("Connect at least one social account below first"); return; }
  showToast(`Live-syncing ${targets.length} account(s) for ${ws.name}…`);
  for (const t of targets) {
    try {
      const resp = await fetch("/api/socials/sync", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ workspaceId: ws.id, platform: t.platform, handle: t.handle, role: "owned", limit: 15 }) });
      const data = await resp.json();
      if (resp.ok && data.ok) {
        const acc = data.account || {};
        connectedSocialOverrides[ws.id][t.platform] = {
          handle: acc.handle || t.handle, connected: true, syncedAt: acc.syncedAt,
          followers: acc.followers && acc.followers !== "—" ? acc.followers : (acc.followerCount ? fmtNum(acc.followerCount) : "Synced"),
          medianViews: acc.medianViews ? fmtNum(acc.medianViews) : "—", note: acc.note || "",
        };
        if (data.items?.length) {
          const cards = data.items.slice(0, 9).map(it => {
            const ro = buildClientBreakdown({ url: it.url, platform: t.platform, workspace: ws.id, tag: it.creator_username || t.handle, transcript: it.transcript || it.caption || it.title });
            const _wsId = typeof workspace !== "undefined" ? workspace : ws.id; ro.shortCode = it.shortCode; ro.workspaceId = _wsId; ro.customWorkspace = _wsId; ro.plays = it.plays || 0; ro.likes = it.likes || 0; ro.duration = it.duration || 0; ro.ratio = it.ratio || 1;
            ro.band_class = ro.ratio >= 15 ? "breakout" : ro.ratio >= 5 ? "strong" : ro.ratio >= 2 ? "good" : "normal";
            ro.band_label = ro.ratio >= 15 ? "Breakout" : ro.ratio >= 5 ? "Replicable" : ro.ratio >= 2 ? "Working" : "Normal";
            syncedOwnedReels = [ro, ...syncedOwnedReels.filter(x => x.shortCode !== ro.shortCode)];
            return { shortCode: it.shortCode, ratio: `${(it.ratio || 1).toFixed(1)}×`, band: ro.band_class, platform: `${t.platform.toUpperCase()} · ${acc.handle || t.handle}`, hook: it.title || it.caption || "Synced Video", plays: fmtNum(it.plays || 0), likes: fmtNum(it.likes || 0) };
          });
          ownOutliersByWorkspace[ws.id] = [...cards, ...(ownOutliersByWorkspace[ws.id] || []).filter(x => !cards.some(c => c.shortCode === x.shortCode))].slice(0, 12);
        }
      }
    } catch {}
  }
  saveJSON(KEYS.connectedSocials, connectedSocialOverrides);
  renderAll();
  showToast(`Synced ${targets.length} live account(s) with real views ✓`);
});

// Feed filter & sort listeners
const searchInput = document.getElementById("search-input");
searchInput.value = searchText;
searchInput.addEventListener("input", () => { searchText = searchInput.value; saveFeedState(); renderFeed(); });
document.getElementById("filter-hook-cat").addEventListener("change", e => { hookCatFilter = e.target.value; renderFeed(); });
document.getElementById("filter-format-cat").addEventListener("change", e => { formatCatFilter = e.target.value; renderFeed(); });
document.getElementById("filter-topic").addEventListener("change", e => { topicFilter = e.target.value; renderFeed(); });
document.getElementById("filter-sort").addEventListener("change", e => { const [k, d] = e.target.value.split(":"); sortKey = k; sortDir = d; renderFeed(); });
document.querySelectorAll("#band-filter button").forEach(b => {
  b.classList.toggle("active", b.dataset.band === bandFilter);
  b.addEventListener("click", () => { bandFilter = b.dataset.band; document.querySelectorAll("#band-filter button").forEach(x => x.classList.toggle("active", x === b)); saveFeedState(); renderFeed(); });
});
const tComp = document.getElementById("toggle-completed"), tDel = document.getElementById("toggle-deleted");
function syncToggles() { tComp.classList.toggle("on", hideCompleted); tComp.textContent = hideCompleted ? "✓ Hiding studied" : "Hide studied"; tDel.classList.toggle("on", showDeleted); tDel.textContent = showDeleted ? "✓ Showing removed" : "Show removed"; }
tComp.addEventListener("click", () => { hideCompleted = !hideCompleted; syncToggles(); saveFeedState(); renderFeed(); });
tDel.addEventListener("click", () => { showDeleted = !showDeleted; syncToggles(); saveFeedState(); renderFeed(); });
syncToggles();
document.getElementById("filter-reset").addEventListener("click", () => {
  searchText = ""; bandFilter = "all"; hookCatFilter = "all"; formatCatFilter = "all"; topicFilter = "all"; hideCompleted = false; showDeleted = false; activeFilter = "__all__";
  searchInput.value = ""; document.querySelectorAll("#band-filter button").forEach(x => x.classList.toggle("active", x.dataset.band === "all"));
  syncToggles(); saveFeedState(); renderScopeNav(); renderFeed();
});
document.querySelectorAll(".view-toggle button").forEach(b => b.addEventListener("click", () => { document.body.dataset.view = b.dataset.view; localStorage.setItem(KEYS.view, b.dataset.view); document.querySelectorAll(".view-toggle button").forEach(x => x.classList.toggle("active", x === b)); }));
document.body.dataset.view = localStorage.getItem(KEYS.view) || "table";
document.querySelectorAll(".view-toggle button").forEach(x => x.classList.toggle("active", x.dataset.view === document.body.dataset.view));
document.querySelectorAll(".density-toggle button").forEach(b => b.addEventListener("click", () => { document.body.dataset.density = b.dataset.density; localStorage.setItem(KEYS.density, b.dataset.density); document.querySelectorAll(".density-toggle button").forEach(x => x.classList.toggle("active", x === b)); }));
document.querySelectorAll("th[data-sort]").forEach(th => th.addEventListener("click", () => {
  const k = th.dataset.sort; sortDir = k === sortKey ? (sortDir === "desc" ? "asc" : "desc") : "desc"; sortKey = k;
  document.querySelectorAll("th[data-sort]").forEach(t => { t.classList.remove("sort-active", "sort-desc", "sort-asc"); t.querySelector(".arrow").textContent = "▼"; });
  th.classList.add("sort-active", `sort-${sortDir}`); th.querySelector(".arrow").textContent = sortDir === "desc" ? "▼" : "▲"; renderFeed();
}));

// Global Delegated Handlers
document.addEventListener("change", e => {
  if (e.target.hasAttribute("data-idea-note")) {
    ideaNotes[e.target.dataset.ideaNote] = e.target.value;
    saveJSON(KEYS.ideaNotes, ideaNotes);
  }
});

document.addEventListener("click", e => {
  const t = e.target;
  const wsBtn = t.closest("[data-ws-id]"); if (wsBtn) { selectWorkspace(wsBtn.dataset.wsId); closeWsMenu(); return; }
  const arch = t.closest("[data-archetype]"); if (arch) { document.querySelectorAll("#archetype-grid .archetype-opt").forEach(x => x.classList.toggle("active", x === arch)); return; }
  const auditBtn = t.closest("[data-audit-key]"); if (auditBtn) { auditSelectedKey = auditBtn.dataset.auditKey; renderStrategyAudit(); return; }
  const pickHook = t.closest("[data-pick-hook]"); if (pickHook) { wizard.selectedHookIdx = Number(pickHook.dataset.pickHook); renderScriptWizard(); return; }
  const launchSc = t.closest("[data-launch-script]"); if (launchSc) { launchScriptFromReel(launchSc.dataset.launchScript); return; }
  const copyHk = t.closest("[data-copy-hook]"); if (copyHk) { copyText(copyHk.dataset.copyHook, "Hook formula copied ✓"); return; }
  const testHk = t.closest("[data-test-hook]"); if (testHk) { document.getElementById("preflight-input").value = testHk.dataset.testHook; runPreflightCheck(); document.getElementById("preflight-input").scrollIntoView({ behavior: "smooth", block: "center" }); return; }
  const saveHk = t.closest("[data-save-hook]"); if (saveHk) { const sc = saveHk.dataset.saveHook; savedHooks.has(sc) ? savedHooks.delete(sc) : savedHooks.add(sc); saveJSON(KEYS.savedHooks, [...savedHooks]); renderIdeasAndHooks(); return; }
  const togShort = t.closest("[data-toggle-shortlist]"); if (togShort) { const sc = togShort.dataset.toggleShortlist; if (shortlistedIdeas.has(sc)) shortlistedIdeas.delete(sc); else { shortlistedIdeas.add(sc); discardedIdeas.delete(sc); } saveJSON(KEYS.shortlistedIdeas, [...shortlistedIdeas]); saveJSON(KEYS.discardedIdeas, [...discardedIdeas]); renderIdeasAndHooks(); return; }
  const togDisc = t.closest("[data-toggle-discard]"); if (togDisc) { const sc = togDisc.dataset.toggleDiscard; if (discardedIdeas.has(sc)) discardedIdeas.delete(sc); else { discardedIdeas.add(sc); shortlistedIdeas.delete(sc); } saveJSON(KEYS.discardedIdeas, [...discardedIdeas]); saveJSON(KEYS.shortlistedIdeas, [...shortlistedIdeas]); renderIdeasAndHooks(); return; }
  const delProj = t.closest("[data-del-project]"); if (delProj) { projects = projects.filter(p => p.id !== delProj.dataset.delProject); saveJSON(KEYS.projects, projects); renderIdeasAndHooks(); return; }
  const cpScript = t.closest("[data-copy-script-id]"); if (cpScript) { const s = savedScripts.find(x => x.id === cpScript.dataset.copyScriptId); if (s) copyText(s.script, "Script copied ✓"); return; }
  const dlScript = t.closest("[data-del-script-id]"); if (dlScript) { savedScripts = savedScripts.filter(x => x.id !== dlScript.dataset.delScriptId); saveJSON(KEYS.savedScripts, savedScripts); renderSavedScripts(); return; }
  if (t.id === "empty-preview-connected") { previewConnectedMode = true; document.getElementById("preview-connected-toggle").classList.add("on"); renderChannelsAndSocials(); return; }
  const connBtn = t.closest("[data-connect-platform]"); if (connBtn) { document.getElementById("cs-workspace-eyebrow").textContent = `${getActiveWorkspace().name} Workspace`; document.getElementById("connect-social-title").textContent = `Connect ${PLATFORM_META[connBtn.dataset.connectPlatform]?.name || connBtn.dataset.connectPlatform}`; document.getElementById("cs-platform").value = connBtn.dataset.connectPlatform; document.getElementById("cs-handle").value = connBtn.dataset.defaultHandle || ""; connectDialog.showModal(); return; }
  const jumpCr = t.closest("[data-jump-creator]"); if (jumpCr) { activeFilter = jumpCr.dataset.jumpCreator; setActiveTab("feed"); renderFeed(); return; }
  if (t.closest("[data-clear-creator]")) { activeFilter = "__all__"; renderFeed(); return; }
  const chip = t.closest(".creator-chip[data-creator]"); if (chip) { activeFilter = chip.dataset.creator; localStorage.setItem(KEYS.filter, activeFilter); renderFeed(); return; }

  // Wizard buttons (uses local Claude/Codex CLI when available, falls back cleanly to Instant Local)
  if (t.id === "wiz-clear-src") { wizard.sourceShortCode = null; renderScriptWizard(); return; }
  if (t.id === "wiz-next-1") {
    wizard.topic = document.getElementById("wiz-topic").value.trim() || wizard.topic || "Fixing the #1 workflow bottleneck";
    wizard.format = document.getElementById("wiz-format").value;
    wizard.hookStyle = document.getElementById("wiz-hook-style").value;
    wizard.existingDraft = document.getElementById("wiz-draft")?.value || "";
    const runStep1 = async () => {
      if (isLocalServer() && activeAiProvider !== "local") {
        t.disabled = true; t.textContent = `Generating via ${activeAiProvider}…`;
        try {
          const src = wizard.sourceShortCode ? allReels().find(r => r.shortCode === wizard.sourceShortCode) : null;
          const stepName = wizard.existingDraft.trim() ? "fix" : "research";
          const resp = await fetch("/api/ai/script", {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ step: stepName, provider: activeAiProvider, topic: wizard.topic, draft: wizard.existingDraft, workspaceProfile: getActiveWorkspace(), sourceReel: src ? { creator: src.creator_username, ratio: src.ratio, plays: src.plays, hook: src.hook, format: src.breakdown?.format?.category, transcript: src.transcript } : null }),
          });
          const d = await resp.json();
          if (resp.ok && d.result) {
            if (stepName === "fix" && d.result.fixedScript) {
              wizard.scriptText = d.result.fixedScript;
              wizard.step = 4; renderScriptWizard(); showToast(`✦ Draft upgraded via ${d.result.engine} ✓`); return;
            }
            wizard.research = {
              execSummary: d.result.executiveSummary || "",
              engage: Array.isArray(d.result.howToEngage) ? d.result.howToEngage.join(" · ") : (d.result.howToEngage || ""),
              facts: d.result.surprisingFacts || [],
              contrast: d.result.contrastMoments || [],
            };
            wizard.step = 2; renderScriptWizard(); showToast(`✦ Research brief generated via ${d.result.engine} ✓`); return;
          }
        } catch {}
      }
      generateResearchBrief(); wizard.step = 2; renderScriptWizard();
    };
    runStep1();
    return;
  }
  if (t.id === "wiz-back-2") { wizard.step = 1; renderScriptWizard(); return; }
  if (t.id === "wiz-next-2" || t.id === "wiz-regen-hooks") {
    if (t.id === "wiz-next-2") {
      wizard.research.execSummary = document.getElementById("wiz-res-exec").value;
      wizard.research.engage = document.getElementById("wiz-res-eng").value;
    }
    const runHooks = async () => {
      if (isLocalServer() && activeAiProvider !== "local") {
        t.disabled = true; t.textContent = `Drafting hooks via ${activeAiProvider}…`;
        try {
          const resp = await fetch("/api/ai/script", {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ step: "hooks", provider: activeAiProvider, topic: wizard.topic, research: wizard.research, workspaceProfile: getActiveWorkspace() }),
          });
          const d = await resp.json();
          if (resp.ok && Array.isArray(d.result?.hooks) && d.result.hooks.length) {
            wizard.hooks = d.result.hooks.map(h => ({ style: h.style || "Hook", by: `${h.inspiredBy || "AI"} · ✦ ${d.result.engine}${h.visualCue ? " · Visual: " + h.visualCue : ""}`, text: h.text || "" }));
            wizard.selectedHookIdx = 0; wizard.step = 3; renderScriptWizard(); showToast(`✦ 6 hooks generated via ${d.result.engine} ✓`); return;
          }
        } catch {}
      }
      generateHookDrafts(); wizard.step = 3; renderScriptWizard();
      if (t.id === "wiz-regen-hooks") showToast("Generated fresh hook variations ✓");
    };
    runHooks();
    return;
  }
  if (t.id === "wiz-back-3") { wizard.step = 2; renderScriptWizard(); return; }
  if (t.id === "wiz-next-3") {
    const runScript = async () => {
      if (isLocalServer() && activeAiProvider !== "local") {
        t.disabled = true; t.textContent = `Writing script via ${activeAiProvider}…`;
        try {
          const resp = await fetch("/api/ai/script", {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ step: "script", provider: activeAiProvider, topic: wizard.topic, research: wizard.research, selectedHook: wizard.hooks[wizard.selectedHookIdx]?.text || "", workspaceProfile: getActiveWorkspace() }),
          });
          const d = await resp.json();
          if (resp.ok && d.result?.script) {
            wizard.scriptText = d.result.script; wizard.step = 4; renderScriptWizard(); showToast(`✦ Script written via ${d.result.engine} ✓`); return;
          }
        } catch {}
      }
      generateFullScript(); wizard.step = 4; renderScriptWizard();
    };
    runScript();
    return;
  }
  if (t.id === "wiz-back-4") { wizard.step = 3; renderScriptWizard(); return; }
  if (t.id === "wiz-copy-script") { copyText(document.getElementById("wiz-final-script").value, "Script copied ✓"); return; }
  if (t.id === "wiz-export-llm") { const ws = getActiveWorkspace(); copyText(`Polish this short-form script using ${ws.name}'s voice (${ws.character?.writingStyle || ""}) and the 7 Magnetism Elements:\n\n` + document.getElementById("wiz-final-script").value, "LLM Polish Prompt copied ✓"); return; }
  if (t.id === "wiz-save-script") {
    const text = document.getElementById("wiz-final-script").value;
    savedScripts.unshift({ id: "sc_" + Date.now(), title: wizard.topic.slice(0, 80) || "Untitled Script", format: wizard.format, workspace: getActiveWorkspace().name, script: text, createdAt: new Date().toISOString() });
    saveJSON(KEYS.savedScripts, savedScripts); renderSavedScripts(); showToast("Saved to Scripts ✓"); return;
  }
  if (t.id === "wiz-reset") { wizard = { step: 1, sourceShortCode: null, topic: "", existingDraft: "", format: "Breakdown Explainer", hookStyle: "Trap Mistake", research: null, hooks: [], selectedHookIdx: 0, scriptText: "" }; renderScriptWizard(); return; }

  const openCard = t.closest("[data-open-reel]"); if (openCard) { openReelModal(openCard.dataset.openReel); return; }
  if (t.matches(".row-check")) { const sc = t.closest("tr[data-shortcode]")?.dataset.shortcode; if (sc) { completed.has(sc) ? completed.delete(sc) : completed.add(sc); saveFeedState(); renderFeed(); } return; }
  if (t.matches(".row-delete")) { const sc = t.closest("tr[data-shortcode]")?.dataset.shortcode; if (sc) { t.dataset.action === "delete" ? deleted.add(sc) : deleted.delete(sc); saveFeedState(); renderFeed(); renderToday(); } return; }
  const row = t.closest("tr[data-shortcode]"); if (row && !t.closest("td:first-child")) openReelModal(row.dataset.shortcode);
});

// ---- KEYWORDS, SERP, VPH, TITLE & TAG SEO LAB ----
bindSubNav("seo-subnav");
let kwBucket = "matching";
let activeKeywordData = {
  keyword: "AI automation",
  overallScore: 66,
  overallLabel: "High",
  volumeScore: 84,
  monthlySearches: 540000,
  competitionScore: 64,
  competitionLabel: "Medium",
  viewsPerHour: 7087.1,
  freshBreakouts: 4,
  source: "starter_snapshot",
  matching: [
    { keyword: "ai automation for beginners", searchVolume: 182000, competitionLabel: "Low", overall: 70 },
    { keyword: "ai automation agency", searchVolume: 215000, competitionLabel: "Medium", overall: 67 },
    { keyword: "ai automation workflow with n8n", searchVolume: 148000, competitionLabel: "Very low", overall: 74 },
    { keyword: "ai automation full course", searchVolume: 164000, competitionLabel: "Low", overall: 70 },
    { keyword: "ai automation tools for business", searchVolume: 112000, competitionLabel: "Very low", overall: 72 },
    { keyword: "claude code ai automation", searchVolume: 96000, competitionLabel: "Very low", overall: 78 },
  ],
  related: [
    { keyword: "best ai agents for small business", searchVolume: 124000, competitionLabel: "Low", overall: 75 },
    { keyword: "n8n vs make ai workflow", searchVolume: 84000, competitionLabel: "Very low", overall: 77 },
    { keyword: "ai operating system for founders", searchVolume: 48000, competitionLabel: "Very low", overall: 79 },
    { keyword: "automate content creation with ai", searchVolume: 138000, competitionLabel: "Medium", overall: 66 },
  ],
  questions: [
    { keyword: "how to start ai automation agency", searchVolume: 142000, competitionLabel: "Very low", overall: 73 },
    { keyword: "how to sell ai automation services", searchVolume: 91000, competitionLabel: "Very low", overall: 73 },
    { keyword: "how to automate business workflows with ai", searchVolume: 86000, competitionLabel: "Very low", overall: 75 },
    { keyword: "what is the best ai automation tool 2026", searchVolume: 74000, competitionLabel: "Low", overall: 72 },
  ],
  recommendedTags: [
    { tag: "how to start ai automation agency", score: 73 },
    { tag: "ai automation workflow with n8n", score: 74 },
    { tag: "claude code ai automation", score: 78 },
    { tag: "ai automation for beginners", score: 70 },
    { tag: "ai automation tools", score: 69 },
    { tag: "ai agents for business", score: 72 },
    { tag: "business automation", score: 65 },
    { tag: "ai workflow", score: 68 },
  ],
  topVideos: [
    { title: "AI Agents, Clearly Explained", channel: "Jeff Su", views: 5836695, vph: 4053.3, outlierScore: 15.5, url: "https://www.youtube.com/watch?v=FwOTs4UxQS4" },
    { title: "How I Build AI Workflows That Actually Save 15 Hrs/Week", channel: "Starter Benchmark", views: 412000, vph: 612.0, outlierScore: 6.4, url: "https://www.youtube.com/results?search_query=AI+automation" },
  ],
};

function scoreBadgeCls(s) { return s >= 70 ? "hi" : s >= 48 ? "med" : "lo"; }

function renderKeywordExplorer() {
  const d = activeKeywordData;
  if (!d) return;
  const note = document.getElementById("kw-source-note");
  if (note) note.textContent = d.source === "live_youtube_suggest_and_serp" ? "● Live YouTube Suggest + SERP data" : "Starter snapshot (search live on localhost:4747)";

  const ovCls = d.overallScore >= 65 ? "live" : d.overallScore >= 45 ? "" : "warn";
  const cmpCls = d.competitionScore <= 45 ? "live" : d.competitionScore <= 70 ? "" : "warn";
  document.getElementById("kw-headline-metrics").innerHTML = `
    <div class="kpi-card">
      <div class="kpi-label">Overall Score</div>
      <div style="display:flex;align-items:baseline;gap:8px"><div class="kpi-val">${d.overallScore}<span style="font-size:15px;color:var(--ink-3)">/100</span></div><span class="status-chip ${ovCls}">${escapeHtml(d.overallLabel)}</span></div>
      <div class="progress-bar" style="margin-top:6px"><span style="width:${d.overallScore}%"></span></div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Est. Monthly Searches</div>
      <div class="kpi-val">${fmtNum(d.monthlySearches)}</div>
      <div class="kpi-delta">Demand index ${d.volumeScore || 65}/100</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Competition</div>
      <div style="display:flex;align-items:baseline;gap:8px"><div class="kpi-val">${d.competitionScore}<span style="font-size:15px;color:var(--ink-3)">/100</span></div><span class="status-chip ${cmpCls}">${escapeHtml(d.competitionLabel)}</span></div>
      <div class="kpi-delta">${d.freshBreakouts ?? 0} recent breakouts in top 12</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Views Per Hour (VPH)</div>
      <div class="kpi-val">${fmtNum(d.viewsPerHour)}</div>
      <div class="kpi-delta">Combined top-10 search velocity</div>
    </div>
  `;

  const rows = d[kwBucket] || d.matching || [];
  document.getElementById("kw-table-body").innerHTML = rows.slice(0, 18).map(r => `
    <tr>
      <td style="font-weight:700;padding:8px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis" title="${escapeHtml(r.keyword)}">${escapeHtml(r.keyword)}</td>
      <td style="padding:8px 6px;font-variant-numeric:tabular-nums;white-space:nowrap">${fmtNum(r.searchVolume)}</td>
      <td style="padding:8px 6px"><span class="status-chip ${r.competitionLabel?.includes("low") || r.competitionLabel?.includes("Low") ? "live" : "muted"}" style="font-size:10px;padding:3px 7px">${escapeHtml(r.competitionLabel || "Med")}</span></td>
      <td style="padding:8px 6px"><span class="tag-score-num ${scoreBadgeCls(r.overall)}">${r.overall}</span></td>
      <td style="padding:8px 4px;text-align:right"><button type="button" class="btn btn-outline btn-xs" style="padding:4px 7px" title="Send to Title & SEO Optimizer" data-optimize-kw="${escapeHtml(r.keyword)}">→</button></td>
    </tr>`).join("") || `<tr><td colspan="5" style="text-align:center;color:var(--ink-3);padding:20px">No keywords in this bucket.</td></tr>`;

  document.getElementById("kw-tags-wrap").innerHTML = (d.recommendedTags || []).map(t => `
    <button type="button" class="tag-score-pill" data-add-opt-tag="${escapeHtml(t.tag)}" title="Click to add to Optimizer tags">
      <span>${escapeHtml(t.tag)}</span>
      <span class="tag-score-num ${scoreBadgeCls(t.score)}">${t.score}</span>
    </button>`).join("");

  document.getElementById("kw-top-videos").innerHTML = (d.topVideos || []).slice(0, 6).map(v => `
    <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;padding:10px 12px;border-radius:12px;background:var(--paper);border:1px solid var(--border)">
      <div style="min-width:0;flex:1">
        <a href="${escapeHtml(v.url)}" target="_blank" rel="noopener noreferrer" style="font-weight:700;font-size:13px;display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${escapeHtml(v.title)}</a>
        <div style="font-size:11.5px;color:var(--ink-3)">${escapeHtml(v.channel)} · <strong>${fmtNum(v.views)}</strong> views · <strong>${fmtNum(v.vph)} VPH</strong> · ${v.outlierScore || 1}×</div>
      </div>
      <button type="button" class="btn btn-outline btn-xs" style="flex-shrink:0" data-model-yt-title="${escapeHtml(v.title)}">Model Title</button>
    </div>`).join("") || `<p style="font-size:13px;color:var(--ink-3)">Run a live keyword search on localhost:4747 to pull top ranking YouTube videos.</p>`;
}

async function runKeywordSearch(term) {
  const q = (term || "").trim();
  if (!q) return;
  document.getElementById("kw-search-input").value = q;
  if (!isLocalServer()) {
    activeKeywordData = { ...activeKeywordData, keyword: q, source: "static_estimate" };
    renderKeywordExplorer();
    showToast("Open http://127.0.0.1:4747 for live YouTube Suggest + SERP lookup");
    return;
  }
  const btn = document.getElementById("kw-search-btn");
  if (btn) { btn.disabled = true; btn.textContent = "Searching YouTube…"; }
  try {
    const r = await fetch(`/api/seo/keyword?q=${encodeURIComponent(q)}`);
    const d = await r.json();
    if (!r.ok) throw new Error(d.message || "Search failed");
    activeKeywordData = d;
    renderKeywordExplorer();
    showToast(`Live YouTube keyword & SERP scored for "${q}" ✓`);
  } catch (err) {
    showToast(`Keyword search error: ${err.message}`);
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = "Search Keyword →"; }
  }
}

const SEO_POWER_WORDS = new Set(["stop","secret","nobody","mistake","wrong","never","exact","free","simple","fast","actually","truth","hidden","killed","replaced","insane","scientifically","proven","framework","system","hours","minutes","days","million","blueprint","trap","without","before","instead","tested","honest","brutal","weird","only"]);
function runLiveSeoOptimizer() {
  const titleEl = document.getElementById("opt-title");
  if (!titleEl) return;
  const title = titleEl.value.trim();
  const kw = (document.getElementById("opt-keyword")?.value || "").trim().toLowerCase();
  const thumb = (document.getElementById("opt-thumb")?.value || "").trim();
  const desc = (document.getElementById("opt-desc")?.value || "").trim();
  const tagsRaw = (document.getElementById("opt-tags")?.value || "").trim();
  const tags = tagsRaw ? tagsRaw.split(",").map(s => s.trim()).filter(Boolean) : [];

  const tl = title.toLowerCase(), dl = desc.toLowerCase();
  const words = title.split(/\s+/).filter(Boolean);
  const hasNum = /\b\d+[\d,.%kKmMxX]*\b/.test(title);
  const powerHits = (tl.match(/[a-z]+/g) || []).filter(w => SEO_POWER_WORDS.has(w));
  const hasContrast = /\b(vs\.?|instead of|without|stop|never|not|why most|actually|before you)\b/i.test(title);
  const hasCuriosity = /(\?|here's|this one|the real reason|nobody|secret|what happened|i tested|i tried)/i.test(title);

  const sparks = Boolean(powerHits.length || hasContrast || hasCuriosity || hasNum);
  const clear = words.length >= 4 && (!kw || kw.split(/\s+/).some(tok => tok.length > 2 && tl.includes(tok)));
  const readable = words.length >= 5 && words.length <= 14;
  const mobile = title.length >= 22 && title.length <= 62;
  const polarity = hasContrast || /\b(stop|lie|trap|wrong|guru|scam|truth|never|kill)\b/i.test(title);

  let tScore = 38 + (sparks ? 18 : 0) + (hasNum ? 8 : 0) + (hasContrast ? 8 : 0) + (clear ? 12 : 0) + (readable ? 8 : 0) + (mobile ? 8 : 0);
  if (title.length > 75) tScore -= 10;
  if (title.length < 18) tScore -= 12;
  tScore = Math.max(12, Math.min(99, tScore));

  document.getElementById("opt-title-chars").textContent = `${title.length}/60`;
  const tagsChars = tags.reduce((n, x) => n + x.length + 1, 0);
  document.getElementById("opt-tags-chars").textContent = `${tagsChars}/500`;

  const ring = document.getElementById("opt-title-ring");
  ring.textContent = String(tScore);
  ring.className = `score-ring ${tScore >= 75 ? "" : tScore >= 55 ? "med" : "low"}`;
  document.getElementById("opt-title-verdict").textContent = tScore >= 82 ? "High-CTR Winner" : tScore >= 65 ? "Strong Title — Minor Polish" : "Needs Stronger Hook & Clarity";

  const checks = [
    { label: "Sparks intrigue", pass: sparks, detail: sparks ? `Triggers detected (${powerHits.slice(0, 3).join(", ") || "number/contrast"}).` : "Add a concrete number, curiosity gap, or power word." },
    { label: "Clear topic", pass: clear, detail: clear ? "Topic & keyword signal are immediately clear." : "Include your target keyword or concrete outcome in the first 5 words." },
    { label: "Easy to read", pass: readable, detail: `${words.length} words (sweet spot: 6–13 words).` },
    { label: "Fits on phones", pass: mobile, detail: `${title.length}/60 chars — ${mobile ? "clean mobile display" : "trim under 60 chars so it won't truncate"}.` },
    { label: "Contrast / polarity edge", pass: polarity, detail: polarity ? "Strong Us-vs-Them or Old-Way-vs-New-Way tension." : "Add 'without X', 'stop doing Y', or name an enemy." },
  ];
  document.getElementById("opt-title-checks").innerHTML = checks.map(c => `
    <div class="seo-check-row"><span class="seo-dot ${c.pass ? "pass" : "fail"}">${c.pass ? "✓" : "!"}</span><div><strong style="display:block;font-size:12.5px">${c.label}</strong><span style="font-size:12px;color:var(--ink-2)">${escapeHtml(c.detail)}</span></div></div>`).join("");

  // Scored Tag Pills (0-100)
  document.getElementById("opt-scored-tags").innerHTML = tags.map(tag => {
    const tgl = tag.toLowerCase(), tw = tgl.split(/\s+/).length;
    let s = 46 + (kw && (tgl.includes(kw) || kw.includes(tgl)) ? 22 : 0) + (tgl.split(/\s+/).some(w => w.length > 3 && tl.includes(w)) ? 12 : 0) + (tw >= 2 && tw <= 4 ? 10 : tw === 1 ? -10 : -12) + (dl && dl.includes(tgl) ? 6 : 0);
    s = Math.max(14, Math.min(96, s));
    return `<span class="tag-score-pill"><span>${escapeHtml(tag)}</span><span class="tag-score-num ${scoreBadgeCls(s)}">${s}</span></span>`;
  }).join("");

  // Actionable SEO Checklist
  const kwTitle = Boolean(kw && tl.includes(kw));
  const kwDesc = Boolean(kw && dl.slice(0, 180).includes(kw));
  const kwTags = Boolean(kw && tags.some(x => x.toLowerCase().includes(kw)));
  const tripled = kwTitle && kwDesc && kwTags;
  const tagBudgetOk = tags.length >= 8 && tags.length <= 20 && tagsChars <= 500;
  const descOk = desc.length >= 200;
  const seoItems = [
    { label: "Primary keyword in Title", pass: kw ? kwTitle : Boolean(title), w: 20 },
    { label: "Primary keyword in first 180 chars of Description", pass: kw ? kwDesc : descOk, w: 20 },
    { label: "Primary keyword in Tags", pass: kw ? kwTags : tags.length >= 5, w: 15 },
    { label: "Tripled Keyword (Title + Description + Tags)", pass: tripled, w: 20 },
    { label: `Tag count & budget (${tags.length} tags · ${tagsChars}/500 chars)`, pass: tagBudgetOk, w: 15 },
    { label: `Description depth (${desc.length} chars · target 200+)`, pass: descOk, w: 10 },
  ];
  const seoTotal = seoItems.reduce((n, x) => n + (x.pass ? x.w : 0), 0);
  const seoBdg = document.getElementById("opt-seo-badge");
  seoBdg.textContent = `${seoTotal} / 100`;
  seoBdg.className = `status-chip ${seoTotal >= 75 ? "live" : seoTotal >= 50 ? "" : "warn"}`;
  document.getElementById("opt-seo-checklist").innerHTML = seoItems.map(c => `
    <div class="seo-check-row" style="padding:7px 10px"><span class="seo-dot ${c.pass ? "pass" : "fail"}">${c.pass ? "✓" : "!"}</span><span>${escapeHtml(c.label)}</span></div>`).join("");

  // Thumbnail Critique
  const tw = thumb ? thumb.split(/\s+/).filter(Boolean).length : 0;
  const repeat = Boolean(thumb && tl.includes(thumb.toLowerCase()));
  let thScore = 72 + (thumb ? (tw <= 4 ? 14 : -16) + (repeat ? -12 : 8) : 0);
  thScore = Math.max(15, Math.min(98, thScore));
  document.getElementById("opt-thumb-badge").textContent = `${thScore} / 100`;
  document.getElementById("opt-thumb-notes").textContent = !thumb
    ? "Add 2–4 bold words that amplify (not repeat) your title alongside 1 clear visual focal point."
    : `${tw <= 4 ? `Crisp mobile legibility (${tw} words).` : `Trim to 2–4 bold words (currently ${tw}).`} ${repeat ? "Avoid repeating your title verbatim — add contrast instead." : "Great complement to the title."}`;
}

document.getElementById("kw-search-form")?.addEventListener("submit", e => { e.preventDefault(); runKeywordSearch(document.getElementById("kw-search-input").value); });
document.getElementById("kw-bucket-switch")?.addEventListener("click", e => {
  const b = e.target.closest("[data-kwb]"); if (!b) return;
  kwBucket = b.dataset.kwb;
  document.querySelectorAll("#kw-bucket-switch button").forEach(x => x.classList.toggle("active", x === b));
  renderKeywordExplorer();
});
document.getElementById("kw-copy-tags")?.addEventListener("click", () => {
  const tags = (activeKeywordData?.recommendedTags || []).map(t => t.tag).join(", ");
  if (tags) copyText(tags, "Scored YouTube tags copied ✓");
});
document.getElementById("kw-send-optimizer")?.addEventListener("click", () => {
  document.getElementById("opt-keyword").value = activeKeywordData.keyword || "";
  document.getElementById("opt-tags").value = (activeKeywordData.recommendedTags || []).map(t => t.tag).join(", ");
  activateSubNav("seo-subnav", "seo-optimizer");
  runLiveSeoOptimizer();
  showToast("Loaded keyword & scored tags into Optimizer ✓");
});
document.getElementById("kw-export-csv")?.addEventListener("click", () => {
  const rows = activeKeywordData[kwBucket] || [];
  const csv = ["keyword,est_monthly_searches,competition,overall_score", ...rows.map(r => `"${r.keyword.replaceAll('"','""')}",${r.searchVolume},"${r.competitionLabel}",${r.overall}`)].join("\n");
  const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([csv], { type: "text/csv" })); a.download = `keywords-${(activeKeywordData.keyword || "search").replace(/\s+/g, "-")}.csv`; a.click();
  showToast(`Exported ${rows.length} keywords as CSV ✓`);
});
["opt-keyword", "opt-title", "opt-thumb", "opt-desc", "opt-tags"].forEach(id => document.getElementById(id)?.addEventListener("input", runLiveSeoOptimizer));

document.getElementById("seo-ai-package-btn")?.addEventListener("click", async () => {
  const kw = document.getElementById("opt-keyword").value.trim() || "AI automation";
  const topic = document.getElementById("opt-title").value.trim() || kw;
  if (!isLocalServer()) { showToast("Open http://127.0.0.1:4747 to generate Claude/Codex AI Packaging"); return; }
  const btn = document.getElementById("seo-ai-package-btn");
  const prov = activeAiProvider === "local" ? (aiCapabilities.default || "claude") : activeAiProvider;
  btn.disabled = true; btn.textContent = `Generating via ${prov}…`;
  try {
    const resp = await fetch("/api/seo/package", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ topic, keyword: kw, provider: prov, workspaceProfile: getActiveWorkspace() }),
    });
    const d = await resp.json();
    if (!resp.ok || !d.ok) throw new Error(d.message || "Packaging failed");
    if (d.titles?.[0]?.title) document.getElementById("opt-title").value = d.titles[0].title;
    if (d.thumbnails?.[0]?.overlayText) document.getElementById("opt-thumb").value = d.thumbnails[0].overlayText;
    if (d.description) document.getElementById("opt-desc").value = d.description;
    if (d.tags?.length) document.getElementById("opt-tags").value = d.tags.map(x => x.tag).join(", ");
    const card = document.getElementById("opt-ai-variants-card");
    const box = document.getElementById("opt-ai-variants");
    card.hidden = false;
    box.innerHTML = [
      ...(d.titles || []).map(t => `<button type="button" class="seo-check-row" style="text-align:left;width:100%;justify-content:space-between" data-apply-title="${escapeHtml(t.title)}"><div><strong style="display:block">${escapeHtml(t.title)}</strong><span style="font-size:11.5px;color:var(--ink-3)">${escapeHtml(t.angle)} · ${escapeHtml(t.whyItClicks)}</span></div><span class="tag-score-num ${scoreBadgeCls(t.score)}">${t.score}</span></button>`),
      ...(d.thumbnails || []).map(th => `<div class="seo-check-row" style="background:var(--yellow-tint)"><div><strong style="display:block">Thumbnail Concept: “${escapeHtml(th.overlayText)}”</strong><span style="font-size:12px;color:var(--ink-2)">${escapeHtml(th.visualScene)} — ${escapeHtml(th.curiosityHook)}</span></div></div>`),
    ].join("");
    runLiveSeoOptimizer();
    showToast(`✦ Generated AI titles, thumbnails, description & tags via ${d.engine} ✓`);
  } catch (err) {
    showToast(`AI packaging error: ${err.message}`);
  } finally {
    btn.disabled = false; btn.textContent = "✦ Generate AI Packaging";
  }
});

// Delegated SEO & Prediction Clicks
document.addEventListener("click", e => {
  const t = e.target;
  const qk = t.closest("[data-quick-kw]"); if (qk) { runKeywordSearch(qk.dataset.quickKw); return; }
  const okw = t.closest("[data-optimize-kw]"); if (okw) { document.getElementById("opt-keyword").value = okw.dataset.optimizeKw; activateSubNav("seo-subnav", "seo-optimizer"); runLiveSeoOptimizer(); return; }
  const at = t.closest("[data-add-opt-tag]"); if (at) { const el = document.getElementById("opt-tags"); const cur = el.value.trim(); if (!cur.toLowerCase().includes(at.dataset.addOptTag.toLowerCase())) el.value = cur ? `${cur}, ${at.dataset.addOptTag}` : at.dataset.addOptTag; runLiveSeoOptimizer(); showToast(`Added tag "${at.dataset.addOptTag}" ✓`); return; }
  const mt = t.closest("[data-model-yt-title]"); if (mt) { document.getElementById("opt-title").value = mt.dataset.modelYtTitle; document.getElementById("opt-keyword").value = activeKeywordData.keyword || ""; activateSubNav("seo-subnav", "seo-optimizer"); runLiveSeoOptimizer(); return; }
  const ap = t.closest("[data-apply-title]"); if (ap) { document.getElementById("opt-title").value = ap.dataset.applyTitle; runLiveSeoOptimizer(); showToast("Applied title variant ✓"); return; }
  const optIdea = t.closest("[data-optimize-idea-title]"); if (optIdea) { document.getElementById("opt-title").value = optIdea.dataset.optimizeIdeaTitle; document.getElementById("opt-keyword").value = optIdea.dataset.optimizeIdeaKw; setActiveTab("seo"); activateSubNav("seo-subnav", "seo-optimizer"); runLiveSeoOptimizer(); return; }
  const scIdea = t.closest("[data-script-idea]"); if (scIdea) { wizard.sourceShortCode = null; wizard.topic = scIdea.dataset.scriptIdea; wizard.research = null; wizard.hooks = []; wizard.scriptText = ""; wizard.step = 1; setActiveTab("scripts"); activateSubNav("scripts-subnav", "script-builder"); renderScriptWizard(); return; }
});

// ==================== BRAND BRAIN, OFFER MODALITIES, AI CHAT, ARSENAL, FREE DISCOVERY, ZERODRIVE & COMPOSIO ====================
bindSubNav("brain-subnav");

const OFFER_MODALITIES = {
  S: { label: "S-Tier", weight: 40, cls: "tier-s", items: ["Done For You", "Software", "1-on-1 Coaching", "Reseller License", "Live Event"] },
  A: { label: "A-Tier", weight: 25, cls: "tier-a", items: ["Community", "Group Coaching", "Critique", "Templates", "Certification"] },
  B: { label: "B-Tier", weight: 15, cls: "tier-b", items: ["Swipe Files", "Training", "Case Studies", "Support", "Physical Products", "AI Prompts"] },
  C: { label: "C-Tier", weight: 8, cls: "tier-c", items: ["Graphics", "Resources", "Over The Shoulder", "Updates", "Agreements / Contracts", "Spreadsheets"] },
};
const MODALITY_TIER_MAP = {};
Object.entries(OFFER_MODALITIES).forEach(([t, cfg]) => cfg.items.forEach(m => { MODALITY_TIER_MAP[m] = { tier: t, weight: cfg.weight, cls: cfg.cls }; }));

const SOCIAL_STORY_FORMATS = [
  "Walking Listicle", "Visual Metaphor", "Is It Worth It?", "Deconstruction", "Three-Act Structure", "Narrative",
  "Before vs. After", "Untold Stories", "Do This", "30-Day Challenge", "Impossible Challenge", "Experiment",
  "Myth-Busting", "Contrarian Take", "List / Countdown", "Reaction / Breakdown", "Expert Interview",
  "Education with Dramatization", "Case Study", "Story-Driven", "Watch Me Work", "Tutorial Teaser",
  "Side-by-Side", "A/B Breakdown", "What Not To Do", "Common Mistakes", "Tips on the Move",
  "Man on the Street", "Two Characters", "Expert vs. Novice", "Trial Reels", "Day in the Life",
  "I Did This", "Wrong Way / Right Way", "Resultable Video", "Problem Path",
];

const SEEDED_LIBRARY_ASSETS = [
  {
    id: "asset-offer-modalities",
    title: "Offer Modalities Playbook (S / A / B / C Tier Perceived Value Guide)",
    type: "Reference",
    origin: "user",
    url: "OutlierLab/reference/offer-modalities-playbook.md",
    createdAt: "Pre-seeded",
    content: `# Offer Modalities & Perceived Value Hierarchy\n\nHigher-tier modalities carry exponentially higher perceived value because they collapse effort, time, and execution risk for the buyer.\n\n## S-Tier (Highest Perceived Value — Execution & Access)\n- Done For You, Software, 1-on-1 Coaching, Reseller License, Live Event\n\n## A-Tier (High Leverage — Feedback & Speed)\n- Community, Group Coaching, Critique, Templates, Certification\n\n## B-Tier (Structured Proof & Enablement)\n- Swipe Files, Training, Case Studies, Support, Physical Products, AI Prompts\n\n## C-Tier (Supporting Enhancers & Stack Fillers)\n- Graphics, Resources, Over The Shoulder, Updates, Agreements / Contracts, Spreadsheets\n\n## Offer Stack Rule\nPair at least one S-Tier or A-Tier anchor with targeted B/C-Tier bonuses that remove every objection (time, skill, confidence). Spend 2-3x more pitch time presenting the Bonuses than the Core Offer.`,
  },
  {
    id: "asset-close-sequence",
    title: "High-Converting Offer Close & Bonus Stack Sequence",
    type: "Reference",
    origin: "user",
    url: "OutlierLab/reference/offer-close-sequence.md",
    createdAt: "Pre-seeded",
    content: `# 6-Part Offer Close Sequence\n1. OFFER (3-5 min): Name/Tagline -> One-Sentence Transformation -> Core Components (keep simple).\n2. PRICE ANCHOR CASCADE (3-5 min): Anchor astronomically high -> Industry alternative -> Reveal actual price early.\n3. BONUSES (20-30 min — Longest section): Reveal Bonus 1 -> Review Stack -> Reveal Bonus 2 -> Review Differently -> Save strongest S/A-Tier bonus for last.\n4. GUARANTEE (2-3 min): Remove all downside risk.\n5. OBJECTION REFRAMES: Reframe Time & Money objections as informed decision questions.\n6. SCARCITY & HAND-HOLD CLOSE: Clear deadline + walk through exact next step.`,
  },
];

let brainsByWorkspace = loadJSON("outlier-brains-v1", {});
let activeAvatarId = null;
let selectedProductModalities = new Set(["Done For You", "Templates"]);
let attachedAssetIds = new Set(["asset-offer-modalities"]);
let chatMode = "chief_of_staff";
let chatHistories = loadJSON("outlier-chats-v1", {});
let discoverMode = "search";
let composioToolkitsCache = [];

function getWorkspaceBrain(ws = getActiveWorkspace()) {
  const id = ws.id;
  if (!brainsByWorkspace[id]) {
    const isAIS = id === "aisimple";
    const isCI = id === "clickable-impact";
    brainsByWorkspace[id] = {
      memories: isAIS ? [
        { id: "m1", title: "Core Philosophy: Diagnose Before Prescribing", category: "About Your Business", scope: "workspace", content: "Never automate chaos. Always fix the single real bottleneck before introducing another AI tool.", createdAt: "2026-11-26" },
        { id: "m2", title: "Flagship Proof Point", category: "Offers", scope: "workspace", content: "Helped scale LeadGenJay $39K -> $300K+/mo and retained 49 of 50 customers with our Refund Save Funnel.", createdAt: "2026-11-26" },
      ] : [],
      voices: [
        { id: "v1", name: `${ws.name} Video Voice`, type: "Video", notes: ws.character?.writingStyle || "Direct, punchy, short sentences (<12 words), concrete examples, zero corporate buzzwords.", sample: "" },
        { id: "v2", name: `${ws.name} Story Email Voice`, type: "Email", notes: "Conversational 1-to-1 story opening, sharp bridge to core lesson, clean single CTA in PS.", sample: "" },
      ],
      stories: isAIS ? [
        { id: "st1", title: "The 2-Hour Launch Rescue", falseBelief: "More AI tools equals more output", body: "Two hours before a major launch, an 8-figure founder's 20-step prompt chain broke. We stripped it down to 3 calm steps and saved the entire launch.", createdAt: "2026-11-26" },
      ] : [],
      accountHooks: isAIS ? [
        { id: "ah1", text: "Stop building 47-node AI automations that break by Friday — fix this 1 bottleneck first.", angle: "Contrarian", storyTitle: "The 2-Hour Launch Rescue" },
        { id: "ah2", text: "Two hours before an 8-figure launch, their entire AI stack collapsed. Here is the 3-step fix we installed.", angle: "Origin", storyTitle: "The 2-Hour Launch Rescue" },
        { id: "ah3", text: "If an AI workflow takes longer to maintain than to run, kill it today.", angle: "Dogma", storyTitle: "Core Rule" },
      ] : [],
      coachBot: {
        bio: `Interactive Founder Persona Coach for ${ws.name}. Helps diagnose bottlenecks, extract stories, and architect high-converting offers.`,
        rules: "Diagnose before prescribing. Be direct, practical, and specific. Keep answers actionable.",
        starters: "Where is our highest-leverage bottleneck right now?\nInterview me to extract a story + 5 account hooks.\nAudit my offer stack using S/A/B/C modalities.",
        ctaLabel: ws.offer?.ctaMechanism || `Work with ${ws.name}`,
        ctaUrl: isAIS ? "https://aisimple.co" : "",
      },
      avatars: [
        {
          id: "av1",
          name: isAIS ? "Overwhelmed 7-Figure Founder" : isCI ? "DTC Growth CMO / Founder" : `${ws.name} Dream Customer`,
          occupation: isAIS ? "Founder / Agency Operator ($500K–$15M)" : isCI ? "DTC Brand Founder ($1M–$25M)" : "Primary Buyer",
          age: "30–48",
          platforms: ["Instagram", "YouTube", "LinkedIn"],
          biggestFear: ws.character?.profits?.fear || "Falling behind while wasting time and money on complex tools that don't convert.",
          biggestDesire: ws.character?.profits?.dreams || "A calm, predictable growth engine that scales without burning out the founder.",
          pains: (ws.character?.profits?.pain || "Drowning in manual work\nTool sprawl with zero ROI").replace(/,\s*/g, "\n"),
          dreams: (ws.character?.profits?.results || "15+ hours/week back\nPredictable inbound leads").replace(/,\s*/g, "\n"),
          fbMethod: "AI systems require coding and 47-step automations to work.",
          fbSelf: "I'm not technical enough and don't have time to learn another tool.",
          fbExternal: "My team won't adopt new workflows anyway.",
          fbOther: "Every course or agency just sells hype without implementation.",
          fileNotes: "",
          customDetails: [
            { key: "Revenue Band", value: isAIS ? "$500K – $10M/yr" : "$1M – $20M/yr" },
            { key: "Trigger Moment", value: ws.character?.profits?.triggers || "Hitting a growth ceiling where working harder stops working" },
            { key: "How They Talk", value: "Cut the fluff — just show me what actually works Monday morning." },
          ],
        },
      ],
      products: isAIS ? [
        { id: "p1", name: "Done-For-You AI Operating Stack", desc: "3 production AI workflows installed into your business in 30 days.", solves: "Eliminates 15+ hrs/wk of repetitive manual ops", modalities: ["Done For You", "Software", "1-on-1 Coaching"], perceivedValue: 7500, price: 3500, status: "Active" },
        { id: "p2", name: "Weekly Live Implementation & Critique Lab", desc: "Direct workflow audits, prompt teardown, and peer founder room.", solves: "Stops teams from stalling after week 1", modalities: ["Group Coaching", "Critique", "Community", "Templates"], perceivedValue: 3000, price: 997, status: "Active" },
        { id: "p3", name: "The SIMPLE Prompt & SOP Vault", desc: "Plug-and-play prompt packs, SOPs, and team onboarding contracts.", solves: "Gives your team instant execution playbooks", modalities: ["Swipe Files", "AI Prompts", "Case Studies", "Spreadsheets"], perceivedValue: 1500, price: 297, status: "Active" },
      ] : [],
      offers: isAIS ? [
        { id: "o1", name: "AI Simple Accelerator", tier: "Core", promise: "Replace 15+ hours/week of manual founder bottlenecks with 3 calm, reliable AI systems in 30 days.", price: 2997, billing: "One-time", overridePerceivedValue: 0, guarantee: "30-day implementation guarantee — if it doesn't save you 10+ hrs/wk, we keep working free.", stack: [{ productId: "p1", role: "Core" }, { productId: "p2", role: "Bonus" }, { productId: "p3", role: "Bonus" }] },
      ] : [],
      assets: SEEDED_LIBRARY_ASSETS.map(a => ({ ...a })),
    };
    saveJSON("outlier-brains-v1", brainsByWorkspace);
  }
  return brainsByWorkspace[id];
}

function persistWorkspaceBrain(syncCloud = false) {
  saveJSON("outlier-brains-v1", brainsByWorkspace);
  const ws = getActiveWorkspace();
  if (isLocalServer() && ws.id !== "__all__") {
    fetch("/api/brain", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ workspaceId: ws.id, brain: buildFullBrainPayload(), syncZeroDrive: syncCloud }),
    }).catch(() => {});
  }
}

function calcModalityScore(modalities) {
  return (modalities || []).reduce((sum, m) => sum + (MODALITY_TIER_MAP[m]?.weight || 5), 0);
}

function buildFullBrainPayload() {
  const ws = getActiveWorkspace();
  const b = getWorkspaceBrain(ws);
  const attachedAssets = (b.assets || []).filter(a => attachedAssetIds.has(a.id));
  return {
    workspace: { id: ws.id, name: ws.name, tagline: ws.tagline },
    persona: { ...(ws.character || {}), offer: ws.offer || {}, voices: b.voices || [], stories: b.stories || [], accountHooks: b.accountHooks || [], coachBot: b.coachBot || {} },
    avatars: b.avatars || [],
    products: b.products || [],
    offers: b.offers || [],
    memories: b.memories || [],
    attachedAssets,
  };
}

// ---- Render Brand Brain (All 5 Sub-Tabs) ----
function renderBrandBrain() {
  const ws = getActiveWorkspace();
  const b = getWorkspaceBrain(ws);
  document.getElementById("mem-count-badge").textContent = String((b.memories || []).length);
  document.getElementById("av-count-badge").textContent = String((b.avatars || []).length);
  document.getElementById("off-count-badge").textContent = String((b.offers || []).length);
  document.getElementById("asset-count-badge").textContent = String((b.assets || []).length);
  document.getElementById("voices-count").textContent = String((b.voices || []).length);
  document.getElementById("acct-hooks-count").textContent = String((b.accountHooks || []).length);

  // 1. Voices
  const vList = document.getElementById("voices-list");
  if (vList) {
    vList.innerHTML = (b.voices || []).map(v => `
      <article class="panel-card" style="padding:16px;gap:8px">
        <div style="display:flex;justify-content:space-between;align-items:center;gap:8px">
          <div><strong style="font-size:15px">${escapeHtml(v.name)}</strong> <span class="status-chip muted">${escapeHtml(v.type)}</span></div>
          <button type="button" class="btn btn-outline btn-xs" data-del-voice="${escapeHtml(v.id)}">Remove</button>
        </div>
        <p style="font-size:13px;color:var(--ink-2)">${escapeHtml(v.notes)}</p>
        ${v.sample ? `<div style="font-size:12px;color:var(--ink-3);background:var(--paper);padding:8px 10px;border-radius:10px;white-space:pre-wrap">${escapeHtml(v.sample.slice(0, 220))}</div>` : ""}
      </article>`).join("") || `<div class="empty-box">No custom voices yet.</div>`;
  }

  // 2. Separate Account Stories & Hooks
  const ahList = document.getElementById("acct-hooks-list");
  document.getElementById("acct-hooks-list-count").textContent = String((b.accountHooks || []).length);
  if (ahList) {
    ahList.innerHTML = (b.accountHooks || []).map(h => `
      <div style="padding:10px 12px;border-radius:12px;background:var(--paper);border:1px solid var(--border);display:flex;justify-content:space-between;align-items:flex-start;gap:10px">
        <div style="min-width:0;flex:1">
          <div style="font-weight:700;font-size:13.5px">“${escapeHtml(h.text)}”</div>
          <div style="font-size:11px;color:var(--ink-3);margin-top:3px">${escapeHtml(h.angle || "Brand Hook")}${h.storyTitle ? ` · From: ${escapeHtml(h.storyTitle)}` : ""}</div>
        </div>
        <div style="display:flex;gap:5px;flex-shrink:0">
          <button type="button" class="btn btn-outline btn-xs" data-copy-hook="${escapeHtml(h.text)}">Copy</button>
          <button type="button" class="btn btn-outline btn-xs" data-del-acct-hook="${escapeHtml(h.id)}">×</button>
        </div>
      </div>`).join("") || `<p style="font-size:13px;color:var(--ink-3)">No brand account hooks yet — add a story or click Generate 10 Account Hooks.</p>`;
  }
  const stList = document.getElementById("acct-stories-list");
  document.getElementById("acct-stories-count").textContent = String((b.stories || []).length);
  if (stList) {
    stList.innerHTML = (b.stories || []).map(s => `
      <div style="padding:10px 12px;border-radius:12px;background:var(--paper);border:1px solid var(--border)">
        <div style="display:flex;justify-content:space-between;gap:8px"><strong style="font-size:13.5px">${escapeHtml(s.title)}</strong><button type="button" class="btn btn-outline btn-xs" data-del-story="${escapeHtml(s.id)}">×</button></div>
        ${s.falseBelief ? `<div style="font-size:11.5px;color:var(--yellow-ink);font-weight:700;margin-top:2px">Destroys: ${escapeHtml(s.falseBelief)}</div>` : ""}
        <p style="font-size:12.5px;color:var(--ink-2);margin-top:4px">${escapeHtml(s.body)}</p>
      </div>`).join("") || `<p style="font-size:13px;color:var(--ink-3)">No brand stories captured yet.</p>`;
  }

  // 3. Coaching Bot
  const cb = b.coachBot || {};
  const setVal = (id, v) => { const el = document.getElementById(id); if (el) el.value = v || ""; };
  setVal("cb-bio", cb.bio); setVal("cb-rules", cb.rules); setVal("cb-starters", cb.starters); setVal("cb-cta-label", cb.ctaLabel); setVal("cb-cta-url", cb.ctaUrl);
  document.getElementById("cb-preview-title").textContent = `${ws.character?.superheroIdentity || ws.name} · Coaching Bot`;
  document.getElementById("cb-preview-bio").textContent = cb.bio || "";
  document.getElementById("cb-preview-starters").innerHTML = (cb.starters || "").split("\n").filter(Boolean).slice(0, 4).map(q =>
    `<button type="button" class="tag-score-pill" style="justify-content:flex-start" data-launch-coach-q="${escapeHtml(q)}">💬 ${escapeHtml(q)}</button>`
  ).join("");
  document.getElementById("cb-preview-cta").innerHTML = cb.ctaLabel ? `<span class="btn btn-yellow btn-xs">${escapeHtml(cb.ctaLabel)} →</span>` : "";

  // 4. Memories
  const memSearch = (document.getElementById("mem-search")?.value || "").toLowerCase();
  const memCat = document.getElementById("mem-filter-cat")?.value || "all";
  const allMems = b.memories || [];
  const cats = [...new Set(allMems.map(m => m.category))];
  const catSel = document.getElementById("mem-filter-cat");
  if (catSel) {
    const cur = catSel.value;
    catSel.innerHTML = `<option value="all">All Categories (${allMems.length})</option>` + cats.map(c => `<option value="${escapeHtml(c)}" ${c === cur ? "selected" : ""}>${escapeHtml(c)}</option>`).join("");
  }
  const filteredMems = allMems.filter(m => (memCat === "all" || m.category === memCat) && (!memSearch || `${m.title} ${m.content} ${m.category}`.toLowerCase().includes(memSearch)));
  document.getElementById("mem-list-count").textContent = String(filteredMems.length);
  document.getElementById("memories-list").innerHTML = filteredMems.map(m => `
    <div style="padding:12px 14px;border-radius:14px;background:var(--paper);border:1px solid var(--border);display:flex;flex-direction:column;gap:5px">
      <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap">
        <div style="display:flex;gap:6px;align-items:center"><strong style="font-size:14px">${escapeHtml(m.title)}</strong><span class="status-chip muted">${escapeHtml(m.category)}</span><span class="micro-tag">${m.scope === "personal" ? "Personal" : "Workspace"}</span></div>
        <button type="button" class="btn btn-outline btn-xs" data-del-mem="${escapeHtml(m.id)}">Forget</button>
      </div>
      <p style="font-size:13px;color:var(--ink-2)">${escapeHtml(m.content)}</p>
    </div>`).join("") || `<div class="empty-box">No memories saved for ${escapeHtml(ws.name)} yet.</div>`;

  // 5. Customer Avatars
  const avs = b.avatars || [];
  if (!activeAvatarId || !avs.some(a => a.id === activeAvatarId)) activeAvatarId = avs[0]?.id || null;
  document.getElementById("avatar-selector-row").innerHTML = avs.map(a =>
    `<button type="button" class="btn ${a.id === activeAvatarId ? "btn-dark" : "btn-outline"} btn-sm" data-pick-avatar="${escapeHtml(a.id)}">${escapeHtml(a.name)}</button>`
  ).join("");
  const av = avs.find(a => a.id === activeAvatarId);
  if (av) {
    setVal("av-name", av.name); setVal("av-occ", av.occupation); setVal("av-age", av.age);
    setVal("av-fear", av.biggestFear); setVal("av-desire", av.biggestDesire);
    setVal("av-pains", av.pains); setVal("av-dreams", av.dreams);
    setVal("av-fb-method", av.fbMethod); setVal("av-fb-self", av.fbSelf); setVal("av-fb-external", av.fbExternal); setVal("av-fb-other", av.fbOther);
    setVal("av-file-notes", av.fileNotes);
    const platSet = new Set(av.platforms || []);
    document.getElementById("av-platforms-row").innerHTML = ["Instagram", "YouTube", "TikTok", "Facebook", "LinkedIn", "X/Twitter"].map(pl =>
      `<button type="button" class="mod-chip ${platSet.has(pl) ? "active" : ""}" data-toggle-av-plat="${pl}">${pl}</button>`
    ).join("");
    document.getElementById("av-custom-details-list").innerHTML = (av.customDetails || []).map((cd, i) => `
      <div style="display:grid;grid-template-columns:180px 1fr auto;gap:8px;align-items:center">
        <input class="field-input" style="padding:7px 10px;font-size:12.5px" data-cd-key="${i}" value="${escapeHtml(cd.key)}" placeholder="Label (e.g. Trigger Moment)">
        <input class="field-input" style="padding:7px 10px;font-size:12.5px" data-cd-val="${i}" value="${escapeHtml(cd.value)}" placeholder="Detail...">
        <button type="button" class="btn btn-outline btn-xs" data-del-cd="${i}">×</button>
      </div>`).join("") || `<p style="font-size:12px;color:var(--ink-3)">No custom notes yet — click + Add Custom Detail.</p>`;
  }

  // 6. Products & Offers (S/A/B/C Offer Modalities + Perceived Value Stack)
  const mpBox = document.getElementById("prod-modalities-picker");
  if (mpBox) {
    mpBox.innerHTML = Object.entries(OFFER_MODALITIES).map(([tier, cfg]) => `
      <div class="tier-group">
        <div style="display:flex;align-items:center;gap:8px"><span class="tier-badge ${cfg.cls}">${cfg.label}</span><span style="font-size:11px;color:var(--ink-3)">+${cfg.weight} leverage pts each</span></div>
        <div style="display:flex;flex-wrap:wrap;gap:6px">
          ${cfg.items.map(m => `<button type="button" class="mod-chip ${selectedProductModalities.has(m) ? "active" : ""}" data-toggle-mod="${escapeHtml(m)}">${escapeHtml(m)}</button>`).join("")}
        </div>
      </div>`).join("");
    document.getElementById("prod-modality-score").textContent = `Leverage Score: ${calcModalityScore([...selectedProductModalities])}`;
  }

  const prods = b.products || [];
  document.getElementById("products-count").textContent = String(prods.length);
  const opBox = document.getElementById("offer-product-picker");
  if (opBox) {
    opBox.innerHTML = prods.map(p => `
      <label style="display:flex;align-items:center;justify-content:space-between;gap:8px;padding:7px 10px;border-radius:10px;background:var(--paper);border:1px solid var(--border);font-size:12.5px">
        <span style="display:flex;align-items:center;gap:7px"><input type="checkbox" data-stack-prod="${escapeHtml(p.id)}"><strong>${escapeHtml(p.name)}</strong> <span style="color:var(--ink-3)">($${Number(p.perceivedValue || 0).toLocaleString()} val)</span></span>
        <select data-stack-role="${escapeHtml(p.id)}" class="field-select" style="width:auto;padding:3px 8px;font-size:11.5px"><option value="Core">Core</option><option value="Bonus">Bonus</option></select>
      </label>`).join("") || `<p style="font-size:12px;color:var(--ink-3)">Add a product on the left first to stack it into offers.</p>`;
  }

  document.getElementById("products-list-grid").innerHTML = prods.map(p => {
    const score = calcModalityScore(p.modalities);
    return `
      <article class="panel-card" style="padding:16px;gap:8px">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:6px">
          <strong style="font-size:15px">${escapeHtml(p.name)}</strong>
          <button type="button" class="btn btn-outline btn-xs" data-del-prod="${escapeHtml(p.id)}">×</button>
        </div>
        <p style="font-size:12.5px;color:var(--ink-2)">${escapeHtml(p.desc || p.solves || "")}</p>
        <div style="display:flex;flex-wrap:wrap;gap:5px">${(p.modalities || []).map(m => `<span class="tier-badge ${MODALITY_TIER_MAP[m]?.cls || "tier-c"}">${escapeHtml(MODALITY_TIER_MAP[m]?.tier || "?")}: ${escapeHtml(m)}</span>`).join("")}</div>
        <div style="display:flex;justify-content:space-between;align-items:center;padding-top:8px;border-top:1px solid var(--border);font-size:12px">
          <span>Perceived: <strong>$${Number(p.perceivedValue || 0).toLocaleString()}</strong></span>
          <span class="status-chip live">Score ${score}</span>
        </div>
      </article>`;
  }).join("") || `<div class="empty-box" style="grid-column:1/-1">No products created for ${escapeHtml(ws.name)} yet.</div>`;

  const prodMap = new Map(prods.map(p => [p.id, p]));
  document.getElementById("offers-list-grid").innerHTML = (b.offers || []).map(o => {
    const stackedItems = (o.stack || []).map(s => ({ ...s, prod: prodMap.get(s.productId) })).filter(x => x.prod);
    const stackedVal = o.overridePerceivedValue || stackedItems.reduce((n, x) => n + Number(x.prod.perceivedValue || 0), 0);
    const mult = o.price > 0 && stackedVal > 0 ? (stackedVal / o.price).toFixed(1) : "—";
    return `
      <article class="panel-card tone-butter" style="padding:18px;gap:10px">
        <div style="display:flex;justify-content:space-between;align-items:center;gap:8px">
          <span class="tier-badge tier-s">${escapeHtml(o.tier || "Core")}</span>
          <div style="display:flex;gap:6px;align-items:center"><span class="status-chip live">${mult}× Value Stack</span><button type="button" class="btn btn-outline btn-xs" data-del-offer="${escapeHtml(o.id)}">×</button></div>
        </div>
        <h3 style="font-size:20px">${escapeHtml(o.name)}</h3>
        <p style="font-size:13px;color:var(--ink-2)">${escapeHtml(o.promise)}</p>
        <div style="display:flex;gap:16px;font-size:13px;padding:10px 12px;border-radius:12px;background:rgba(255,255,255,0.75)">
          <span>Price: <strong>$${Number(o.price || 0).toLocaleString()}</strong> (${escapeHtml(o.billing || "One-time")})</span>
          <span>Stacked Value: <strong>$${Number(stackedVal || 0).toLocaleString()}</strong></span>
        </div>
        <div style="display:flex;flex-direction:column;gap:5px">
          ${stackedItems.map(x => `<div style="display:flex;justify-content:space-between;font-size:12px;padding:6px 10px;border-radius:9px;background:rgba(255,255,255,0.65)"><span><strong>${x.role}:</strong> ${escapeHtml(x.prod.name)}</span><span>$${Number(x.prod.perceivedValue || 0).toLocaleString()}</span></div>`).join("")}
        </div>
      </article>`;
  }).join("") || `<div class="empty-box" style="grid-column:1/-1">No offers built for ${escapeHtml(ws.name)} yet.</div>`;

  // 7. Asset Library
  const origFilter = document.querySelector("#asset-origin-filter button.active")?.dataset.aorig || "all";
  const assets = (b.assets || []).filter(a => origFilter === "all" || a.origin === origFilter);
  document.getElementById("asset-library-list").innerHTML = assets.map(a => {
    const attached = attachedAssetIds.has(a.id);
    return `
      <div style="padding:12px 14px;border-radius:14px;background:var(--paper);border:1px solid ${attached ? "var(--yellow-ink)" : "var(--border)"};display:flex;flex-direction:column;gap:6px">
        <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap">
          <div><strong style="font-size:14px">${escapeHtml(a.title)}</strong> <span class="status-chip muted">${escapeHtml(a.type)}</span></div>
          <div style="display:flex;gap:5px;flex-wrap:wrap">
            <button type="button" class="btn ${attached ? "btn-dark" : "btn-outline"} btn-xs" data-attach-asset="${escapeHtml(a.id)}">${attached ? "✓ Attached in Chat" : "Attach in Chat"}</button>
            <button type="button" class="btn btn-outline btn-xs" data-zd-asset="${escapeHtml(a.id)}">☁ ZeroDrive</button>
            <button type="button" class="btn btn-outline btn-xs" data-del-asset="${escapeHtml(a.id)}">×</button>
          </div>
        </div>
        <p style="font-size:12.5px;color:var(--ink-2);white-space:pre-wrap;max-height:90px;overflow:hidden">${escapeHtml((a.content || "").slice(0, 260))}</p>
      </div>`;
  }).join("") || `<div class="empty-box">No assets in this filter.</div>`;

  // Populate Arsenal dropdowns
  const avOpts = (b.avatars || []).map(a => `<option value="${escapeHtml(a.name)}">${escapeHtml(a.name)}</option>`).join("") || `<option value="">Default Audience</option>`;
  const offOpts = (b.offers || []).map(o => `<option value="${escapeHtml(o.name)}">${escapeHtml(o.name)} ($${Number(o.price || 0).toLocaleString()})</option>`).join("") || `<option value="">Primary Offer</option>`;
  const vOpts = (b.voices || []).map(v => `<option value="${escapeHtml(v.name)}">${escapeHtml(v.name)} (${escapeHtml(v.type)})</option>`).join("") || `<option value="">Default Voice</option>`;
  const ahOpts = `<option value="">Auto-pick from Account Hooks</option>` + (b.accountHooks || []).map(h => `<option value="${escapeHtml(h.text)}">${escapeHtml(h.text.slice(0, 75))}</option>`).join("");
  ["ap-avatar", "ae-avatar", "as-avatar"].forEach(id => { const el = document.getElementById(id); if (el) el.innerHTML = avOpts; });
  ["ap-offer", "ae-offer"].forEach(id => { const el = document.getElementById(id); if (el) el.innerHTML = offOpts; });
  const aeV = document.getElementById("ae-voice"); if (aeV) aeV.innerHTML = vOpts;
  const asH = document.getElementById("as-acct-hook"); if (asH) asH.innerHTML = ahOpts;
  const asF = document.getElementById("as-story-fmt");
  if (asF && !asF.options.length) asF.innerHTML = SOCIAL_STORY_FORMATS.map(f => `<option>${escapeHtml(f)}</option>`).join("");

  renderChatView();
}

// ---- Render AI Chat & Coach ----
function renderChatView() {
  const ws = getActiveWorkspace();
  const b = getWorkspaceBrain(ws);
  const hist = chatHistories[ws.id] || [];
  const pill = document.getElementById("chat-context-pill");
  if (pill) pill.textContent = `${ws.name} Brain · ${(b.memories || []).length} Memories · ${(b.avatars || []).length} Avatars · ${(b.offers || []).length} Offers · ${attachedAssetIds.size} Attached`;
  const sum = document.getElementById("chat-brain-summary");
  if (sum) sum.innerHTML = `<div><strong>Persona:</strong> ${escapeHtml(ws.character?.superheroIdentity || ws.name)}</div><div><strong>Offers:</strong> ${(b.offers || []).map(o => escapeHtml(o.name)).join(", ") || "None yet"}</div><div><strong>Account Hooks:</strong> ${(b.accountHooks || []).length} saved</div>`;
  const picker = document.getElementById("chat-asset-picker");
  if (picker) picker.innerHTML = (b.assets || []).map(a => `<button type="button" class="tag-score-pill" style="justify-content:space-between;width:100%" data-attach-asset="${escapeHtml(a.id)}"><span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${escapeHtml(a.title)}</span><span class="tag-score-num ${attachedAssetIds.has(a.id) ? "hi" : "med"}">${attachedAssetIds.has(a.id) ? "ON" : "+"}</span></button>`).join("");
  const attBar = document.getElementById("chat-attached-bar");
  if (attBar) attBar.innerHTML = (b.assets || []).filter(a => attachedAssetIds.has(a.id)).map(a => `<span class="status-chip">📎 ${escapeHtml(a.title)}</span>`).join("");

  const log = document.getElementById("chat-log");
  if (!log) return;
  if (!hist.length) {
    log.innerHTML = `<div class="chat-msg assistant"><strong>${escapeHtml(ws.name)} ${chatMode === "persona_coach" ? "Persona Coach" : chatMode === "offer_architect" ? "Offer Architect" : "Chief of Staff"}</strong>\nYour workspace Brain is loaded (${(b.memories || []).length} memories, ${(b.offers || []).length} offers, ${attachedAssetIds.size} attached assets). Ask anything or click a quick prompt below — powered directly by your local Claude or Codex CLI.</div>`;
    return;
  }
  log.innerHTML = hist.map((m, idx) => `
    <div class="chat-msg ${m.role}">
      ${escapeHtml(m.content)}
      ${m.role === "assistant" && (m.suggestedMemories?.length || m.saveableMarkdown) ? `<div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:10px;padding-top:8px;border-top:1px solid var(--border)">
        ${(m.suggestedMemories || []).map((sm, si) => `<button type="button" class="btn btn-outline btn-xs" data-save-chat-mem="${idx}:${si}">＋ Save Memory: ${escapeHtml((sm.title || "").slice(0, 28))}</button>`).join("")}
        <button type="button" class="btn btn-yellow btn-xs" data-save-chat-doc="${idx}">☁ Save Doc to ZeroDrive</button>
      </div>` : ""}
    </div>`).join("");
  log.scrollTop = log.scrollHeight;
}

async function sendChatPrompt(text) {
  const q = (text || "").trim(); if (!q) return;
  const ws = getActiveWorkspace();
  if (!chatHistories[ws.id]) chatHistories[ws.id] = [];
  chatHistories[ws.id].push({ role: "user", content: q });
  renderChatView();
  const btn = document.getElementById("chat-send-btn");
  if (btn) { btn.disabled = true; btn.textContent = "Thinking…"; }
  const prov = document.getElementById("chat-provider-select")?.value || "claude";
  try {
    if (!isLocalServer()) throw new Error("Open http://127.0.0.1:4747 to chat live with your local Claude/Codex CLI.");
    const resp = await fetch("/api/ai/chat", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ messages: chatHistories[ws.id].slice(-12), brain: buildFullBrainPayload(), mode: chatMode, provider: prov }),
    });
    const d = await resp.json();
    if (!resp.ok || !d.ok) throw new Error(d.message || "Chat failed");
    chatHistories[ws.id].push({ role: "assistant", content: d.reply || "(no reply)", suggestedMemories: d.suggestedMemories || [], suggestedTitle: d.suggestedTitle || "AI Chat Output", saveableMarkdown: d.saveableMarkdown || d.reply || "" });
  } catch (err) {
    chatHistories[ws.id].push({ role: "assistant", content: `⚠️ ${err.message}` });
  } finally {
    saveJSON("outlier-chats-v1", chatHistories);
    if (btn) { btn.disabled = false; btn.textContent = "Send →"; }
    renderChatView();
  }
}

// ---- Creative Arsenal Runner (Presentations, Emails, Socials) ----
async function runArsenal(toolType, params, outElId, btnEl) {
  const outEl = document.getElementById(outElId);
  if (btnEl) { btnEl.disabled = true; btnEl.dataset.orig = btnEl.textContent; btnEl.textContent = "Generating via AI…"; }
  const prov = activeAiProvider === "local" ? (aiCapabilities.default || "claude") : activeAiProvider;
  try {
    if (!isLocalServer()) throw new Error("Connect to local http://127.0.0.1:4747 to run Claude/Codex generation.");
    const resp = await fetch("/api/ai/arsenal", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ toolType, params, brain: buildFullBrainPayload(), provider: prov }),
    });
    const d = await resp.json();
    if (!resp.ok || !d.ok) throw new Error(d.message || "Generation failed");
    if (outEl) outEl.value = d.fullMarkdown || JSON.stringify(d, null, 2);
    showToast(`✦ Generated via ${d.engine || prov} ✓`);
    return d;
  } catch (err) {
    if (outEl) outEl.value = `# ${params.format || toolType} Blueprint — ${params.topic || ""}\n\n(Offline fallback — open http://127.0.0.1:4747 for live Claude/Codex generation)\n\n${err.message}`;
    showToast(err.message);
    return null;
  } finally {
    if (btnEl) { btnEl.disabled = false; btnEl.textContent = btnEl.dataset.orig || "Generate →"; }
  }
}

// ---- ZeroDrive & Composio Loaders ----
async function refreshIntegrationsUI() {
  if (!isLocalServer()) return;
  try {
    const zr = await fetch("/api/zerodrive/status");
    if (zr.ok) {
      const z = await zr.json();
      const chip = document.getElementById("zd-status-chip");
      if (chip) { chip.textContent = z.connected ? `● Connected (${z.vaultRoot})` : (z.cliAvailable ? "CLI Detected · Local Mirror Active" : "Local Mirror Ready"); chip.className = `status-chip ${z.connected ? "live" : ""}`; }
      const fr = await fetch(`/api/zerodrive/files?workspace=${encodeURIComponent(activeWorkspaceId)}`);
      if (fr.ok) {
        const fd = await fr.json();
        const fl = document.getElementById("zd-files-list");
        if (fl) fl.innerHTML = (fd.files || []).slice(0, 12).map(f => `<span class="status-chip muted">📄 ${escapeHtml(f.name || f.path || f)}</span>`).join("") || `<span style="font-size:12px;color:var(--ink-3)">Click Sync Active Brain Now to push your workspace Brain to ZeroDrive.</span>`;
      }
    }
  } catch {}
  try {
    const cr = await fetch("/api/composio/status");
    if (cr.ok) {
      const c = await cr.json();
      const chip = document.getElementById("comp-status-chip");
      if (chip) { chip.textContent = c.configured ? `● Connected (${c.userId})` : "Paste API Key to Activate"; chip.className = `status-chip ${c.configured ? "live" : "muted"}`; }
      const uid = document.getElementById("comp-user-id"); if (uid && c.userId) uid.value = c.userId;
    }
    const tr = await fetch("/api/composio/toolkits");
    if (tr.ok) {
      const td = await tr.json();
      composioToolkitsCache = td.toolkits || [];
      renderComposioToolkits();
    }
  } catch {}
}

function renderComposioToolkits() {
  const q = (document.getElementById("comp-search")?.value || "").toLowerCase();
  const grid = document.getElementById("comp-toolkits-grid");
  if (!grid) return;
  const list = composioToolkitsCache.filter(t => !q || `${t.name} ${t.slug} ${t.category || ""}`.toLowerCase().includes(q));
  grid.innerHTML = list.slice(0, 15).map(t => `
    <div class="toolkit-card">
      <div style="display:flex;justify-content:space-between;align-items:center;gap:6px"><strong style="font-size:14px">${escapeHtml(t.name)}</strong><span class="micro-tag">${escapeHtml(t.category || "App")}</span></div>
      <p style="font-size:12px;color:var(--ink-3)">${escapeHtml((t.description || t.slug).slice(0, 72))}</p>
      <button type="button" class="btn btn-outline btn-xs" style="align-self:flex-start" data-comp-connect="${escapeHtml(t.slug)}">1-Click OAuth Connect →</button>
    </div>`).join("") || `<p style="font-size:13px;color:var(--ink-3)">No matching toolkits.</p>`;
}

// ---- Free Live Creator Discovery ----
async function runCreatorDiscovery() {
  const q = document.getElementById("disc-query")?.value.trim() || "";
  const plat = document.getElementById("disc-platform")?.value || "youtube";
  const grid = document.getElementById("disc-results-grid");
  const btn = document.getElementById("disc-submit-btn");
  if (!isLocalServer()) { showToast("Open http://127.0.0.1:4747 for live $0 creator discovery"); return; }
  if (btn) { btn.disabled = true; btn.textContent = "Discovering…"; }
  try {
    const resp = await fetch(`/api/creators/discover?q=${encodeURIComponent(q)}&platform=${encodeURIComponent(plat)}&mode=${encodeURIComponent(discoverMode)}&limit=9`);
    const d = await resp.json();
    const list = d.creators || [];
    grid.innerHTML = list.map(c => `
      <article class="roster-card">
        <div style="display:flex;justify-content:space-between;align-items:center;gap:8px">
          <div style="min-width:0"><strong style="display:block;font-size:14px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${escapeHtml(c.name || c.handle)}</strong><span style="font-size:11.5px;color:var(--ink-3)">${escapeHtml(c.handle || "")} · ${(c.platform || plat).toUpperCase()}</span></div>
          <span class="status-chip live">${c.medianViews ? fmtNum(c.medianViews) + " med" : "Live"}</span>
        </div>
        ${c.topVideoTitle ? `<p style="font-size:12px;color:var(--ink-2)">Top: ${escapeHtml(c.topVideoTitle.slice(0, 88))}</p>` : ""}
        <button type="button" class="btn btn-yellow btn-xs" style="align-self:flex-start" data-track-discovered-handle="${escapeHtml(c.url || c.handle)}" data-track-discovered-plat="${escapeHtml(c.platform || plat)}">＋ Track in ${escapeHtml(getActiveWorkspace().name)}</button>
      </article>`).join("") || `<div class="empty-box" style="grid-column:1/-1">No matching creators found — try another topic or switch to Suggested.</div>`;
  } catch { showToast("Discovery lookup failed"); }
  finally { if (btn) { btn.disabled = false; btn.textContent = "Find Creators Live →"; } }
}

// ---- Event Wiring for Brain, Chat, Arsenal, Discovery, ZeroDrive & Composio ----
document.getElementById("persona-inner-switch")?.addEventListener("click", e => {
  const b = e.target.closest("[data-pview]"); if (!b) return;
  document.querySelectorAll("#persona-inner-switch button").forEach(x => x.classList.toggle("active", x === b));
  ["identity", "voices", "account-hooks", "coach-bot"].forEach(id => { const el = document.getElementById(`pview-${id}`); if (el) el.hidden = id !== b.dataset.pview; });
});
document.getElementById("chat-mode-switch")?.addEventListener("click", e => {
  const b = e.target.closest("[data-chatmode]"); if (!b) return;
  chatMode = b.dataset.chatmode;
  document.querySelectorAll("#chat-mode-switch button").forEach(x => x.classList.toggle("active", x === b));
  renderChatView();
});
document.getElementById("chat-form")?.addEventListener("submit", e => { e.preventDefault(); const inp = document.getElementById("chat-input"); const v = inp.value; inp.value = ""; sendChatPrompt(v); });
document.getElementById("chat-clear-btn")?.addEventListener("click", () => { chatHistories[getActiveWorkspace().id] = []; saveJSON("outlier-chats-v1", chatHistories); renderChatView(); });
document.getElementById("chat-open-brain")?.addEventListener("click", () => setActiveTab("character"));
document.getElementById("chat-save-zd-btn")?.addEventListener("click", async () => {
  const hist = chatHistories[getActiveWorkspace().id] || [];
  if (!hist.length) { showToast("Nothing in chat yet"); return; }
  const md = hist.map(m => `## ${m.role.toUpperCase()}\n${m.content}`).join("\n\n");
  if (isLocalServer()) {
    await fetch("/api/zerodrive/save", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ workspaceId: activeWorkspaceId, category: "chats", filename: `chat-${Date.now()}.md`, content: md }) });
    showToast("☁ Saved chat transcript to ZeroDrive ✓");
    refreshIntegrationsUI();
  } else copyText(md, "Chat transcript copied ✓");
});

document.getElementById("voice-add-form")?.addEventListener("submit", e => {
  e.preventDefault();
  const b = getWorkspaceBrain();
  b.voices.unshift({ id: "v_" + Date.now(), name: document.getElementById("v-name").value.trim(), type: document.getElementById("v-type").value, notes: document.getElementById("v-notes").value.trim(), sample: document.getElementById("v-sample").value.trim() });
  persistWorkspaceBrain(); e.target.reset(); renderBrandBrain(); showToast("Voice saved ✓");
});
document.getElementById("story-add-form")?.addEventListener("submit", e => {
  e.preventDefault();
  const b = getWorkspaceBrain();
  const title = document.getElementById("st-title").value.trim();
  b.stories.unshift({ id: "st_" + Date.now(), title, falseBelief: document.getElementById("st-false-belief").value.trim(), body: document.getElementById("st-body").value.trim(), createdAt: new Date().toISOString().slice(0, 10) });
  const hooks = document.getElementById("st-hooks").value.split("\n").map(x => x.trim()).filter(Boolean);
  hooks.forEach(h => b.accountHooks.unshift({ id: "ah_" + Date.now() + Math.random().toString(36).slice(2, 5), text: h, angle: "Story", storyTitle: title }));
  persistWorkspaceBrain(); e.target.reset(); renderBrandBrain(); showToast(`Saved story & ${hooks.length} account hook(s) ✓`);
});
document.getElementById("coach-bot-form")?.addEventListener("submit", e => {
  e.preventDefault();
  const b = getWorkspaceBrain();
  b.coachBot = { bio: document.getElementById("cb-bio").value.trim(), rules: document.getElementById("cb-rules").value.trim(), starters: document.getElementById("cb-starters").value.trim(), ctaLabel: document.getElementById("cb-cta-label").value.trim(), ctaUrl: document.getElementById("cb-cta-url").value.trim() };
  persistWorkspaceBrain(); renderBrandBrain(); showToast("Coaching Bot saved ✓");
});
document.getElementById("launch-coach-chat-btn")?.addEventListener("click", () => {
  chatMode = "persona_coach";
  document.querySelectorAll("#chat-mode-switch button").forEach(x => x.classList.toggle("active", x.dataset.chatmode === "persona_coach"));
  setActiveTab("chat"); renderChatView();
});
document.getElementById("memory-add-form")?.addEventListener("submit", e => {
  e.preventDefault();
  const b = getWorkspaceBrain();
  b.memories.unshift({ id: "m_" + Date.now(), title: document.getElementById("mem-title").value.trim(), category: document.getElementById("mem-cat").value, scope: document.getElementById("mem-scope").value, content: document.getElementById("mem-content").value.trim(), createdAt: new Date().toISOString().slice(0, 10) });
  persistWorkspaceBrain(); e.target.reset(); renderBrandBrain(); showToast("Memory saved to Brain ✓");
});
document.getElementById("mem-search")?.addEventListener("input", renderBrandBrain);
document.getElementById("mem-filter-cat")?.addEventListener("change", renderBrandBrain);

document.getElementById("av-new-btn")?.addEventListener("click", () => {
  const b = getWorkspaceBrain();
  const id = "av_" + Date.now();
  b.avatars.push({ id, name: "New Customer Avatar", occupation: "", age: "", platforms: ["Instagram", "YouTube"], biggestFear: "", biggestDesire: "", pains: "", dreams: "", fbMethod: "", fbSelf: "", fbExternal: "", fbOther: "", fileNotes: "", customDetails: [{ key: "Trigger Moment", value: "" }] });
  activeAvatarId = id; persistWorkspaceBrain(); renderBrandBrain();
});
document.getElementById("av-add-detail-btn")?.addEventListener("click", () => {
  const b = getWorkspaceBrain(); const av = b.avatars.find(a => a.id === activeAvatarId); if (!av) return;
  av.customDetails = av.customDetails || []; av.customDetails.push({ key: "", value: "" });
  persistWorkspaceBrain(); renderBrandBrain();
});
document.getElementById("av-delete-btn")?.addEventListener("click", () => {
  const b = getWorkspaceBrain(); if (b.avatars.length <= 1) { showToast("Keep at least 1 avatar"); return; }
  b.avatars = b.avatars.filter(a => a.id !== activeAvatarId); activeAvatarId = b.avatars[0]?.id;
  persistWorkspaceBrain(); renderBrandBrain(); showToast("Avatar deleted");
});
document.getElementById("avatar-edit-form")?.addEventListener("submit", e => {
  e.preventDefault();
  const b = getWorkspaceBrain(); const av = b.avatars.find(a => a.id === activeAvatarId); if (!av) return;
  av.name = document.getElementById("av-name").value.trim() || "Customer Avatar";
  av.occupation = document.getElementById("av-occ").value.trim(); av.age = document.getElementById("av-age").value.trim();
  av.biggestFear = document.getElementById("av-fear").value.trim(); av.biggestDesire = document.getElementById("av-desire").value.trim();
  av.pains = document.getElementById("av-pains").value.trim(); av.dreams = document.getElementById("av-dreams").value.trim();
  av.fbMethod = document.getElementById("av-fb-method").value.trim(); av.fbSelf = document.getElementById("av-fb-self").value.trim();
  av.fbExternal = document.getElementById("av-fb-external").value.trim(); av.fbOther = document.getElementById("av-fb-other").value.trim();
  av.fileNotes = document.getElementById("av-file-notes").value.trim();
  av.customDetails = [...document.querySelectorAll("[data-cd-key]")].map((kEl, i) => ({ key: kEl.value.trim(), value: document.querySelector(`[data-cd-val="${i}"]`)?.value.trim() || "" })).filter(x => x.key || x.value);
  persistWorkspaceBrain(); renderBrandBrain(); showToast(`Saved avatar "${av.name}" ✓`);
});

document.getElementById("product-form")?.addEventListener("submit", e => {
  e.preventDefault();
  const b = getWorkspaceBrain();
  b.products.unshift({
    id: "p_" + Date.now(), name: document.getElementById("prod-name").value.trim(), status: document.getElementById("prod-status").value,
    desc: document.getElementById("prod-desc").value.trim(), solves: document.getElementById("prod-solves").value.trim(),
    perceivedValue: Number(document.getElementById("prod-pvalue").value || 0), price: Number(document.getElementById("prod-price").value || 0),
    modalities: [...selectedProductModalities],
  });
  persistWorkspaceBrain(); e.target.reset(); renderBrandBrain(); showToast("Product saved with Offer Modalities ✓");
});
document.getElementById("offer-form")?.addEventListener("submit", e => {
  e.preventDefault();
  const b = getWorkspaceBrain();
  const stack = [...document.querySelectorAll("[data-stack-prod]:checked")].map(cb => ({ productId: cb.dataset.stackProd, role: document.querySelector(`[data-stack-role="${cb.dataset.stackProd}"]`)?.value || "Core" }));
  b.offers.unshift({
    id: "o_" + Date.now(), name: document.getElementById("off-name").value.trim(), tier: document.getElementById("off-tier").value,
    promise: document.getElementById("off-promise").value.trim(), price: Number(document.getElementById("off-price").value || 0),
    billing: document.getElementById("off-billing").value, overridePerceivedValue: Number(document.getElementById("off-pvalue").value || 0),
    guarantee: document.getElementById("off-guarantee").value.trim(), stack,
  });
  persistWorkspaceBrain(); e.target.reset(); renderBrandBrain(); showToast("Offer stack saved ✓");
});
document.getElementById("asset-add-form")?.addEventListener("submit", e => {
  e.preventDefault();
  const b = getWorkspaceBrain();
  b.assets.unshift({ id: "al_" + Date.now(), title: document.getElementById("al-title").value.trim(), type: document.getElementById("al-type").value, origin: "user", url: document.getElementById("al-url").value.trim(), content: document.getElementById("al-content").value.trim(), createdAt: new Date().toISOString().slice(0, 10) });
  persistWorkspaceBrain(); e.target.reset(); renderBrandBrain(); showToast("Resource saved to Asset Library ✓");
});
document.getElementById("asset-origin-filter")?.addEventListener("click", e => {
  const btn = e.target.closest("[data-aorig]"); if (!btn) return;
  document.querySelectorAll("#asset-origin-filter button").forEach(x => x.classList.toggle("active", x === btn));
  renderBrandBrain();
});
document.getElementById("brain-sync-zd-btn")?.addEventListener("click", async () => {
  persistWorkspaceBrain(true);
  if (!isLocalServer()) { showToast("Saved locally (connect on localhost:4747 to push to ZeroDrive)"); return; }
  const r = await fetch("/api/zerodrive/sync", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ workspaceId: activeWorkspaceId, brain: buildFullBrainPayload() }) });
  const d = await r.json();
  showToast(d.syncedToCloud ? "☁ Synced Brand Brain to ZeroDrive Cloud ✓" : "✓ Synced Brain to local ZeroDrive mirror");
  refreshIntegrationsUI();
});

// AI Generators for Persona, Avatar & Account Hooks
document.getElementById("ai-gen-acct-hooks-btn")?.addEventListener("click", async () => {
  const btn = document.getElementById("ai-gen-acct-hooks-btn");
  const res = await runArsenal("generate_hooks", { count: 10 }, null, btn);
  if (res?.hooks?.length) {
    const b = getWorkspaceBrain();
    res.hooks.forEach(h => b.accountHooks.unshift({ id: "ah_" + Date.now() + Math.random().toString(36).slice(2, 5), text: typeof h === "string" ? h : (h.text || h.hook || ""), angle: h.angle || "AI Generated", storyTitle: "AI Hook Lab" }));
    persistWorkspaceBrain(); renderBrandBrain(); showToast(`✦ Added ${res.hooks.length} Account Hooks ✓`);
  }
});
document.getElementById("av-ai-gen-btn")?.addEventListener("click", async () => {
  const btn = document.getElementById("av-ai-gen-btn");
  const res = await runArsenal("generate_avatar", { brief: getActiveWorkspace().tagline }, null, btn);
  if (res?.avatar) {
    const b = getWorkspaceBrain(); const av = { id: "av_" + Date.now(), platforms: ["Instagram", "YouTube"], customDetails: [], ...res.avatar };
    b.avatars.push(av); activeAvatarId = av.id; persistWorkspaceBrain(); renderBrandBrain(); showToast(`✦ Generated Avatar "${av.name}" ✓`);
  }
});
document.getElementById("ai-gen-persona-btn")?.addEventListener("click", async () => {
  const btn = document.getElementById("ai-gen-persona-btn");
  const res = await runArsenal("generate_persona", { brief: getActiveWorkspace().tagline }, null, btn);
  if (res?.hooks?.length) {
    const b = getWorkspaceBrain();
    res.hooks.forEach(h => b.accountHooks.unshift({ id: "ah_" + Date.now() + Math.random().toString(36).slice(2, 5), text: typeof h === "string" ? h : (h.text || ""), angle: "Persona", storyTitle: "Generated Persona" }));
    (res.stories || []).forEach(s => b.stories.unshift({ id: "st_" + Date.now() + Math.random().toString(36).slice(2, 5), title: s.title || "Origin Story", body: s.body || s.narrative || "", falseBelief: s.falseBelief || "" }));
    persistWorkspaceBrain(); renderBrandBrain(); showToast("✦ Expanded Founder Persona stories & hooks ✓");
  }
});

// Arsenal Forms
document.getElementById("ars-pres-form")?.addEventListener("submit", e => { e.preventDefault(); runArsenal("presentation", { format: document.getElementById("ap-format").value, offerName: document.getElementById("ap-offer").value, avatarName: document.getElementById("ap-avatar").value, storytellingFormat: document.getElementById("ap-story-fmt").value, topic: document.getElementById("ap-topic").value.trim(), customInstructions: document.getElementById("ap-notes").value.trim() }, "ap-output", document.getElementById("ap-submit")); });
document.getElementById("ars-email-form")?.addEventListener("submit", e => { e.preventDefault(); runArsenal("email", { format: document.getElementById("ae-format").value, offerName: document.getElementById("ae-offer").value, avatarName: document.getElementById("ae-avatar").value, voice: document.getElementById("ae-voice").value, topic: document.getElementById("ae-topic").value.trim(), customInstructions: document.getElementById("ae-notes").value.trim() }, "ae-output", document.getElementById("ae-submit")); });
document.getElementById("ars-social-form")?.addEventListener("submit", e => { e.preventDefault(); runArsenal("social", { platform: document.getElementById("as-platform").value, storytellingFormat: document.getElementById("as-story-fmt").value, avatarName: document.getElementById("as-avatar").value, accountHook: document.getElementById("as-acct-hook").value, topic: document.getElementById("as-topic").value.trim() }, "as-output", document.getElementById("as-submit")); });

[["ap", "Presentation"], ["ae", "Email"], ["as", "Social"]].forEach(([pfx, kind]) => {
  document.getElementById(`${pfx}-copy`)?.addEventListener("click", () => copyText(document.getElementById(`${pfx}-output`).value, `${kind} copied ✓`));
  document.getElementById(`${pfx}-save-lib`)?.addEventListener("click", () => {
    const content = document.getElementById(`${pfx}-output`).value.trim(); if (!content) return;
    const b = getWorkspaceBrain();
    b.assets.unshift({ id: "al_" + Date.now(), title: `${kind} · ${new Date().toLocaleDateString()}`, type: kind, origin: "ai", url: "", content, createdAt: new Date().toISOString().slice(0, 10) });
    persistWorkspaceBrain(); renderBrandBrain(); showToast(`Saved ${kind} to Asset Library ✓`);
  });
  document.getElementById(`${pfx}-save-zd`)?.addEventListener("click", async () => {
    const content = document.getElementById(`${pfx}-output`).value.trim(); if (!content) return;
    if (!isLocalServer()) { copyText(content, "Copied (connect on :4747 to save to ZeroDrive)"); return; }
    await fetch("/api/zerodrive/save", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ workspaceId: activeWorkspaceId, category: kind.toLowerCase() + "s", filename: `${kind.toLowerCase()}-${Date.now()}.md`, content }) });
    showToast(`☁ Saved ${kind} to ZeroDrive ✓`); refreshIntegrationsUI();
  });
});

// Discovery, ZeroDrive & Composio Forms
document.getElementById("disc-mode-switch")?.addEventListener("click", e => {
  const b = e.target.closest("[data-dmode]"); if (!b) return;
  discoverMode = b.dataset.dmode;
  document.querySelectorAll("#disc-mode-switch button").forEach(x => x.classList.toggle("active", x === b));
  if (discoverMode === "suggested") runCreatorDiscovery();
});
document.getElementById("creator-discover-form")?.addEventListener("submit", e => { e.preventDefault(); runCreatorDiscovery(); });
document.getElementById("zd-connect-form")?.addEventListener("submit", async e => {
  e.preventDefault();
  if (!isLocalServer()) { showToast("Open http://127.0.0.1:4747 to connect ZeroDrive"); return; }
  const r = await fetch("/api/zerodrive/connect", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ vaultRoot: document.getElementById("zd-vault-root").value.trim(), apiUrl: document.getElementById("zd-api-url").value.trim(), apiKey: document.getElementById("zd-api-key").value.trim() }) });
  const d = await r.json(); showToast(d.message || "ZeroDrive connected ✓"); refreshIntegrationsUI();
});
document.getElementById("zd-sync-now-btn")?.addEventListener("click", () => document.getElementById("brain-sync-zd-btn")?.click());
document.getElementById("comp-config-form")?.addEventListener("submit", async e => {
  e.preventDefault();
  if (!isLocalServer()) { showToast("Open http://127.0.0.1:4747 to configure Composio"); return; }
  const r = await fetch("/api/composio/configure", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ apiKey: document.getElementById("comp-api-key").value.trim(), userId: document.getElementById("comp-user-id").value.trim() }) });
  const d = await r.json(); showToast(d.message || (d.ok ? "Composio saved ✓" : "Composio error")); refreshIntegrationsUI();
});
document.getElementById("comp-search")?.addEventListener("input", renderComposioToolkits);
document.getElementById("comp-exec-form")?.addEventListener("submit", async e => {
  e.preventDefault();
  if (!isLocalServer()) { showToast("Open http://127.0.0.1:4747 to run Composio tools"); return; }
  let args = {}; try { args = JSON.parse(document.getElementById("comp-tool-args").value || "{}"); } catch { showToast("Invalid JSON arguments"); return; }
  const r = await fetch("/api/composio/execute", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ toolSlug: document.getElementById("comp-tool-slug").value.trim(), arguments: args }) });
  const d = await r.json();
  const out = document.getElementById("comp-exec-output"); out.style.display = "block"; out.textContent = JSON.stringify(d, null, 2);
});

// Delegated clicks for Brain, Chat, Modalities, Discovery & Composio
document.addEventListener("click", async e => {
  const t = e.target;
  const mod = t.closest("[data-toggle-mod]"); if (mod) { const m = mod.dataset.toggleMod; selectedProductModalities.has(m) ? selectedProductModalities.delete(m) : selectedProductModalities.add(m); renderBrandBrain(); return; }
  const avP = t.closest("[data-pick-avatar]"); if (avP) { activeAvatarId = avP.dataset.pickAvatar; renderBrandBrain(); return; }
  const avPl = t.closest("[data-toggle-av-plat]"); if (avPl) { const b = getWorkspaceBrain(); const av = b.avatars.find(a => a.id === activeAvatarId); if (av) { const s = new Set(av.platforms || []); s.has(avPl.dataset.toggleAvPlat) ? s.delete(avPl.dataset.toggleAvPlat) : s.add(avPl.dataset.toggleAvPlat); av.platforms = [...s]; persistWorkspaceBrain(); renderBrandBrain(); } return; }
  const dCd = t.closest("[data-del-cd]"); if (dCd) { const b = getWorkspaceBrain(); const av = b.avatars.find(a => a.id === activeAvatarId); if (av) { av.customDetails.splice(Number(dCd.dataset.delCd), 1); persistWorkspaceBrain(); renderBrandBrain(); } return; }
  const dMem = t.closest("[data-del-mem]"); if (dMem) { const b = getWorkspaceBrain(); b.memories = b.memories.filter(x => x.id !== dMem.dataset.delMem); persistWorkspaceBrain(); renderBrandBrain(); return; }
  const dV = t.closest("[data-del-voice]"); if (dV) { const b = getWorkspaceBrain(); b.voices = b.voices.filter(x => x.id !== dV.dataset.delVoice); persistWorkspaceBrain(); renderBrandBrain(); return; }
  const dAh = t.closest("[data-del-acct-hook]"); if (dAh) { const b = getWorkspaceBrain(); b.accountHooks = b.accountHooks.filter(x => x.id !== dAh.dataset.delAcctHook); persistWorkspaceBrain(); renderBrandBrain(); return; }
  const dSt = t.closest("[data-del-story]"); if (dSt) { const b = getWorkspaceBrain(); b.stories = b.stories.filter(x => x.id !== dSt.dataset.delStory); persistWorkspaceBrain(); renderBrandBrain(); return; }
  const dPr = t.closest("[data-del-prod]"); if (dPr) { const b = getWorkspaceBrain(); b.products = b.products.filter(x => x.id !== dPr.dataset.delProd); persistWorkspaceBrain(); renderBrandBrain(); return; }
  const dOf = t.closest("[data-del-offer]"); if (dOf) { const b = getWorkspaceBrain(); b.offers = b.offers.filter(x => x.id !== dOf.dataset.delOffer); persistWorkspaceBrain(); renderBrandBrain(); return; }
  const dAs = t.closest("[data-del-asset]"); if (dAs) { const b = getWorkspaceBrain(); b.assets = b.assets.filter(x => x.id !== dAs.dataset.delAsset); attachedAssetIds.delete(dAs.dataset.delAsset); persistWorkspaceBrain(); renderBrandBrain(); return; }
  const attAs = t.closest("[data-attach-asset]"); if (attAs) { const id = attAs.dataset.attachAsset; attachedAssetIds.has(id) ? attachedAssetIds.delete(id) : attachedAssetIds.add(id); renderBrandBrain(); showToast(attachedAssetIds.has(id) ? "Attached resource to AI Chat ✓" : "Detached resource"); return; }
  const zdAs = t.closest("[data-zd-asset]"); if (zdAs) { const a = (getWorkspaceBrain().assets || []).find(x => x.id === zdAs.dataset.zdAsset); if (a && isLocalServer()) { await fetch("/api/zerodrive/save", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ workspaceId: activeWorkspaceId, category: "assets", filename: a.title.toLowerCase().replace(/[^a-z0-9]+/g, "-") + ".md", content: a.content }) }); showToast(`☁ Saved "${a.title}" to ZeroDrive ✓`); refreshIntegrationsUI(); } return; }
  const cp = t.closest("[data-chat-prompt]"); if (cp) { sendChatPrompt(cp.dataset.chatPrompt); return; }
  const lcq = t.closest("[data-launch-coach-q]"); if (lcq) { chatMode = "persona_coach"; setActiveTab("chat"); sendChatPrompt(lcq.dataset.launchCoachQ); return; }
  const scm = t.closest("[data-save-chat-mem]"); if (scm) { const [mi, si] = scm.dataset.saveChatMem.split(":").map(Number); const sm = (chatHistories[activeWorkspaceId]?.[mi]?.suggestedMemories || [])[si]; if (sm) { getWorkspaceBrain().memories.unshift({ id: "m_" + Date.now(), title: sm.title || "From Chat", category: sm.category || "From Conversations", scope: "workspace", content: sm.content || "", createdAt: new Date().toISOString().slice(0, 10) }); persistWorkspaceBrain(); renderBrandBrain(); showToast("Saved memory to Brand Brain ✓"); } return; }
  const scd = t.closest("[data-save-chat-doc]"); if (scd) { const msg = chatHistories[activeWorkspaceId]?.[Number(scd.dataset.saveChatDoc)]; if (msg && isLocalServer()) { await fetch("/api/zerodrive/save", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ workspaceId: activeWorkspaceId, category: "deliverables", filename: `${(msg.suggestedTitle || "output").toLowerCase().replace(/[^a-z0-9]+/g, "-")}.md`, content: msg.saveableMarkdown || msg.content }) }); showToast("☁ Saved document to ZeroDrive ✓"); refreshIntegrationsUI(); } return; }
  const td = t.closest("[data-track-discovered-handle]"); if (td) { await handleAddChannel({ handles: td.dataset.trackDiscoveredHandle, platform: td.dataset.trackDiscoveredPlat, workspace: activeWorkspaceId, scope: workspaceScopes()[0]?.id || SCOPES[0]?.id }); return; }
  const cc = t.closest("[data-comp-connect]"); if (cc) { if (!isLocalServer()) { showToast("Open http://127.0.0.1:4747 to connect Composio apps"); return; } const r = await fetch("/api/composio/connect", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ toolkit: cc.dataset.compConnect, redirectUrl: location.href }) }); const d = await r.json(); if (d.redirectUrl) { window.open(d.redirectUrl, "_blank", "noopener"); showToast(`Opened ${cc.dataset.compConnect} OAuth window ✓`); } else showToast(d.message || "Configure Composio API key above first"); return; }
});

function renderAll() {
  renderWorkspaceControls();
  renderToday();
  renderKeywordExplorer();
  runLiveSeoOptimizer();
  renderScopeNav();
  renderFeed();
  renderIdeasAndHooks();
  runPreflightCheck();
  renderStrategyAudit();
  renderScriptWizard();
  renderSavedScripts();
  renderCharacterStudio();
  renderBrandBrain();
  renderChannelsAndSocials();
}

window.OUTLIER_APP = {
  getState: () => ({ workspace: getActiveWorkspace(), workspaces: allWorkspaces(), tab: activeTab, scope: activeScope, singleVideos, queuedChannels, projects, savedScripts }),
  selectWorkspace, setActiveTab, openQuickAdd, openReelModal, launchScriptFromReel,
  setOwnOutliers: (wsId, items) => { ownOutliersByWorkspace[wsId] = items; renderChannelsAndSocials(); },
  refreshUI: renderAll,
};

renderAll();
setActiveTab(activeTab);
initAiEngineStatus();
refreshIntegrationsUI();
</script>
</body>
</html>
"""


def main():
    THUMBS.mkdir(parents=True, exist_ok=True)

    fetch_jobs = []
    for handle in CREATORS:
        try:
            details = load(DATA / f"{handle}_details.json")["dataset"]["previewItems"][0]
        except (FileNotFoundError, KeyError, IndexError):
            continue
        purl = details.get("profilePicUrlHD") or details.get("profilePicUrl")
        if purl:
            fetch_jobs.append((purl, THUMBS / f"_profile_{handle}.jpg"))
        try:
            posts = load(DATA / f"{handle}_posts.json")["items"]
        except FileNotFoundError:
            continue
        for p in posts:
            sc = p.get("shortCode") or ""
            thumb_url = p.get("displayUrl")
            if sc and thumb_url:
                fetch_jobs.append((thumb_url, THUMBS / f"{sc}.jpg"))

    pending = [(u, d) for (u, d) in fetch_jobs if not (d.exists() and d.stat().st_size > 0)]
    if pending:
        print(f"downloading {len(pending)} images in parallel (of {len(fetch_jobs)} total)…")
        with ThreadPoolExecutor(max_workers=16) as ex:
            list(ex.map(lambda j: fetch(j[0], j[1]), pending))

    creators = []
    all_rows = []

    for handle in CREATORS:
        posts, details = load_creator(handle)
        views_list = [p.get("videoPlayCount") or p.get("videoViewCount") or 0 for p in posts]
        median_plays = statistics.median(views_list) if views_list else 0

        profile_url = details.get("profilePicUrlHD") or details.get("profilePicUrl")
        profile_local = THUMBS / f"_profile_{handle}.jpg"
        if profile_url:
            fetch(profile_url, profile_local)
        profile_path = f"thumbs/_profile_{handle}.jpg" if profile_local.exists() else None

        creator_meta = {
            "handle": handle,
            "username": details.get("username") or handle,
            "fullName": details.get("fullName") or "",
            "followers": details.get("followersCount") or 0,
            "posts": details.get("postsCount") or 0,
            "verified": bool(details.get("verified")),
            "profile_pic": profile_path,
            "median_plays": median_plays,
            "reels_in_window": len(posts),
            "transcripts_ready": sum(bool((p.get("transcript") or "").strip()) for p in posts),
            "transcripts_no_speech": sum((p.get("transcription") or {}).get("status") == "no_speech" for p in posts),
            "transcripts_review": sum((p.get("transcription") or {}).get("status") == "needs_review" for p in posts),
            "scopes": CREATOR_CONFIG[handle].get("scopes", []),
            "trackingEnabled": CREATOR_CONFIG[handle].get("trackingEnabled", True),
            "coverage": COVERAGE.get(handle, {}),
        }
        creators.append(creator_meta)

        for p in posts:
            plays = p.get("videoPlayCount") or p.get("videoViewCount") or 0
            ratio = (plays / median_plays) if median_plays else None
            sc = p.get("shortCode", "unknown")
            thumb_url = p.get("displayUrl")
            thumb_local = THUMBS / f"{sc}.jpg"
            if thumb_url:
                fetch(thumb_url, thumb_local)
            ts = p.get("timestamp")
            posted_dt = datetime.fromisoformat(ts.replace("Z", "+00:00")) if ts else None
            likes = p.get("likesCount") or 0
            comments = p.get("commentsCount") or 0
            band = outlier_band(ratio)
            transcript = p.get("transcript") or ""
            caption = p.get("caption") or ""
            row = {
                "shortCode": sc,
                "url": p.get("url"),
                "thumb": thumb_local.name if thumb_local.exists() else None,
                "hook": hook_of(transcript, caption),
                "transcript": transcript,
                "transcription": p.get("transcription") or {},
                "caption": caption,
                "plays": plays,
                "likes": likes,
                "comments": comments,
                "engagements": likes + comments,
                "duration": p.get("videoDuration") or 0,
                "posted_human": posted_dt.strftime("%b %-d") if posted_dt else "—",
                "posted_ts": int(posted_dt.timestamp()) if posted_dt else 0,
                "vph": round(plays / max(1.0, (datetime.now().timestamp() - posted_dt.timestamp()) / 3600.0), 1) if (posted_dt and plays) else 0,
                "ratio": ratio or 0,
                "band_class": band[0],
                "band_label": band[1],
                "band_color": band[2],
                "creator_handle": handle,
                "creator_username": creator_meta["username"],
                "creator_avatar": profile_path,
                "creator_verified": creator_meta["verified"],
            }
            row["breakdown"] = p.get("breakdown") or analyze_reel(row)
            all_rows.append(row)

    # Merge synced multi-platform social accounts (Instagram, YouTube, TikTok, Facebook)
    synced_own_socials = []
    socials_dir = DATA / "socials"
    if socials_dir.exists():
        for sp in sorted(socials_dir.glob("*.json")):
            try:
                doc = json.loads(sp.read_text())
            except json.JSONDecodeError:
                continue
            role = doc.get("role") or "owned"
            plat = doc.get("platform") or "youtube"
            handle = (doc.get("handle") or "account").lstrip("@")
            norm_items = []
            for it in doc.get("items") or []:
                sc = it.get("shortCode") or it.get("id")
                if not sc:
                    continue
                ratio = float(it.get("ratio") or 1.0)
                band = outlier_band(ratio)
                tr = it.get("transcript") or ""
                cap = it.get("caption") or it.get("title") or ""
                ts = it.get("timestamp") or ""
                try:
                    pdt = datetime.fromisoformat(ts.replace("Z", "+00:00")) if ts else None
                except ValueError:
                    pdt = None
                row = {
                    "shortCode": sc,
                    "platform": it.get("platform") or plat,
                    "url": it.get("url") or "",
                    "thumb": None,
                    "thumbUrl": it.get("thumbUrl") or "",
                    "hook": hook_of(tr, cap),
                    "transcript": tr,
                    "transcription": {},
                    "caption": cap,
                    "plays": int(it.get("plays") or 0),
                    "likes": int(it.get("likes") or 0),
                    "comments": int(it.get("comments") or 0),
                    "engagements": int(it.get("likes") or 0) + int(it.get("comments") or 0),
                    "duration": int(it.get("duration") or 0),
                    "posted_human": pdt.strftime("%b %-d") if pdt else "—",
                    "posted_ts": int(pdt.timestamp()) if pdt else 0,
                    "vph": round(int(it.get("plays") or 0) / max(1.0, (datetime.now().timestamp() - pdt.timestamp()) / 3600.0), 1) if (pdt and it.get("plays")) else 0,
                    "ratio": ratio,
                    "band_class": band[0],
                    "band_label": band[1],
                    "band_color": band[2],
                    "creator_handle": handle,
                    "creator_username": it.get("creator_username") or handle,
                    "creator_avatar": None,
                    "creator_verified": False,
                }
                row["breakdown"] = it.get("breakdown") or analyze_reel(row)
                norm_items.append(row)
                if role == "watchlist" and not any(r["shortCode"] == sc for r in all_rows):
                    all_rows.append(row)
            if role == "owned":
                synced_own_socials.append({
                    "workspaceId": doc.get("workspaceId") or "aisimple",
                    "platform": plat,
                    "handle": doc.get("handle") or f"@{handle}",
                    "syncedAt": doc.get("syncedAt") or "",
                    "videoCount": len(norm_items), "followerCount": doc.get("followerCount") or 0, "followers": doc.get("followers") or "—",
                    "medianViews": doc.get("medianViews") or 0,
                    "totalViews": doc.get("totalViews") or 0,
                    "note": doc.get("note") or "",
                    "items": norm_items,
                })

    all_rows.sort(key=lambda r: (r["ratio"], r["posted_ts"]), reverse=True)
    outliers = [r for r in all_rows if r["ratio"] >= 2]
    transcribed_count = sum(1 for r in all_rows if (r["transcript"] or "").strip())

    today = datetime.now().strftime("%A %B %-d, %Y")
    total_plays = sum(r["plays"] for r in all_rows)
    median_overall = statistics.median([r["plays"] for r in all_rows]) if all_rows else 0

    clips_dir = ROOT / "clips"
    available_clips = {p.stem for p in clips_dir.glob("*.mp4")} if clips_dir.exists() else set()
    for r in all_rows:
        r["hasClip"] = r["shortCode"] in available_clips

    def safe_json(obj):
        return json.dumps(obj, default=str).replace("<", "\\u003c")

    research = CONFIG.get("research", {})
    roster = []
    for candidate in research.get("candidates", []):
        creator = CREATOR_CONFIG.get(candidate.get("handle"), {})
        roster.append({
            **candidate,
            "scopes": creator.get("scopes", candidate.get("scopes", [])),
            "trackingEnabled": creator.get("trackingEnabled", False),
        })

    workspaces = CONFIG.get("workspaces") or DEFAULT_WORKSPACES

    def creator_chip(c):
        verified = '<span style="color:var(--yellow-ink);margin-left:3px">✓</span>' if c["verified"] else ""
        avatar = f'<img src="{escape(c["profile_pic"])}" alt="">' if c["profile_pic"] else '<div class="avatar-fallback"></div>'
        paused = " · paused" if not c["trackingEnabled"] else ""
        return (
            f'<button class="creator-chip" data-creator="{escape(c["handle"])}" type="button">'
            f'{avatar}'
            f'<div class="chip-info">'
            f'<div class="chip-name">@{escape(c["username"])}{verified}</div>'
            f'<div class="chip-stats">{fmt_num(c["followers"])} · med {fmt_num(c["median_plays"])} · {c["reels_in_window"]} reels{paused}</div>'
            f'</div></button>'
        )

    replacements = {
        "__TODAY__": escape(today),
        "__BUILT_AT__": escape(datetime.now().strftime("%Y-%m-%d %H:%M")),
        "__TOTAL_REELS__": str(len(all_rows)),
        "__TOTAL_CREATORS__": str(len(creators)),
        "__TOTAL_OUTLIERS__": str(len(outliers)),
        "__OUTLIER_PCT__": str(round(100 * len(outliers) / len(all_rows)) if all_rows else 0),
        "__TOP_REEL_PLAYS__": fmt_num(all_rows[0]["plays"] if all_rows else 0),
        "__TOP_REEL_DELTA__": (
            f"{all_rows[0]['band_label']} · {all_rows[0]['ratio']:.1f}× median"
            if all_rows else "No reels yet"
        ),
        "__MEDIAN_OVERALL__": fmt_num(median_overall),
        "__TOTAL_PLAYS__": fmt_num(total_plays),
        "__TOTAL_TRANSCRIPTS__": f"{transcribed_count}/{len(all_rows)}",
        "__CREATOR_CHIPS__": "\n          ".join(creator_chip(c) for c in creators),
        "__REELS_JSON__": safe_json(all_rows),
        "__CREATORS_JSON__": safe_json(creators),
        "__SCOPES_JSON__": safe_json(SCOPES),
        "__RESEARCH_JSON__": safe_json({**research, "candidates": roster}),
        "__ADMIN_URL_JSON__": safe_json(CONFIG.get("adminUrl", "/admin")),
        "__WORKSPACES_JSON__": safe_json(workspaces),
        "__COLLECTIONS_JSON__": safe_json(CREATIVE_COLLECTIONS),
        "__OWN_SOCIALS_JSON__": safe_json(synced_own_socials),
    }

    html = HTML_TEMPLATE
    for token, val in replacements.items():
        html = html.replace(token, val)

    OUT.write_text("\n".join(line.rstrip() for line in html.splitlines()) + "\n")
    print(f"\n✓ Wrote {OUT}")
    print(f"  {len(creators)} creator(s) · {len(all_rows)} reels (all broken down) · {len(outliers)} outliers (≥2×)")
    if all_rows:
        print(f"  Top reel: {fmt_num(all_rows[0]['plays'])} plays, {all_rows[0]['ratio']:.1f}× median by @{all_rows[0]['creator_username']}")


if __name__ == "__main__":
    main()
