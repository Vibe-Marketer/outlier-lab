#!/usr/bin/env python3
"""
Outlier Lab — Local AI Engine (Claude CLI, Codex CLI, optional API fallback).

Produces high-precision Video Breakdown Architecture analyses, Magnetic Story
Audits, 4-step scripts, Brain-Aware AI Chat, Founder Persona Coaching, and
Complete Creative Arsenal generation using your local `claude` or `codex` CLI
subscription with zero extra API keys required.

Pure stdlib — no pip installs required.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

from storage import write_json

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
CONFIG_FILE = ROOT / "config.json"
ENV_FILE = ROOT / ".env"


def _load_env_map():
    env = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            s = line.strip()
            if not s or s.startswith("#") or "=" not in s:
                continue
            k, v = s.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def _env_var(name):
    return os.environ.get(name) or _load_env_map().get(name, "")


def detect_providers():
    """Return available AI engines on this machine."""
    claude_bin = shutil.which("claude") or ("/Users/admin/.local/bin/claude" if Path("/Users/admin/.local/bin/claude").exists() else None)
    codex_bin = shutil.which("codex") or ("/Users/admin/.bun/bin/codex" if Path("/Users/admin/.bun/bin/codex").exists() else None)
    anthropic_key = bool(_env_var("ANTHROPIC_API_KEY"))
    openai_key = bool(_env_var("OPENAI_API_KEY"))

    default = "local"
    if claude_bin:
        default = "claude"
    elif codex_bin:
        default = "codex"
    elif anthropic_key:
        default = "anthropic_api"
    elif openai_key:
        default = "openai_api"

    return {
        "claude": bool(claude_bin),
        "claudePath": claude_bin or "",
        "codex": bool(codex_bin),
        "codexPath": codex_bin or "",
        "anthropicApi": anthropic_key,
        "openaiApi": openai_key,
        "default": default,
    }


def _extract_json_object(raw_text):
    """Robustly pull the outermost JSON object from CLI/model stdout."""
    text = (raw_text or "").strip()
    if not text:
        raise ValueError("Empty response from AI provider.")
    # 1. Direct parse first (avoids false matches if JSON strings contain ``` blocks)
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
    except json.JSONDecodeError:
        pass
    # 2. Outer markdown code fence wrapping the whole payload
    outer_fenced = re.match(r"^```(?:json)?\s*(\{.*\})\s*```$", text, re.S)
    if outer_fenced:
        try:
            obj = json.loads(outer_fenced.group(1))
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            pass
    # 3. Scan from first '{' to last '}' (most reliable for prose + JSON)
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        candidate = text[start:end + 1]
        try:
            obj = json.loads(candidate)
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            pass
    # 4. Fallback: any fenced json block
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.S)
    if fenced:
        try:
            obj = json.loads(fenced.group(1))
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            pass
    raise ValueError(f"Could not parse JSON object from AI output: {text[:240]}")


def _run_claude_cli(prompt, timeout=120):
    info = detect_providers()
    if not info["claude"]:
        raise RuntimeError("Claude CLI is not installed on this machine.")
    cmd = [
        info["claudePath"],
        "-p",
        "--output-format", "text",
        "--tools", "",
        "--no-session-persistence",
        "--disable-slash-commands",
        "--strict-mcp-config",
        "--mcp-config", '{"mcpServers":{}}',
    ]
    env = {**os.environ}
    env["PATH"] = f"{Path(info['claudePath']).parent}:{env.get('PATH', '/usr/bin:/bin')}"
    proc = subprocess.run(
        cmd,
        input=prompt,
        text=True,
        capture_output=True,
        timeout=timeout,
        env=env,
        cwd="/tmp",
    )
    if proc.returncode != 0 and not proc.stdout.strip():
        raise RuntimeError((proc.stderr or "Claude CLI exited with an error.").strip()[:300])
    return proc.stdout


def _run_codex_cli(prompt, timeout=150):
    info = detect_providers()
    if not info["codex"]:
        raise RuntimeError("Codex CLI is not installed on this machine.")
    with tempfile.NamedTemporaryFile(prefix="outlier_codex_", suffix=".txt", delete=False) as tf:
        out_path = Path(tf.name)
    try:
        cmd = [
            info["codexPath"],
            "exec",
            "--skip-git-repo-check",
            "--sandbox",
            "read-only",
            "-o",
            str(out_path),
            "-",
        ]
        env = {**os.environ}
        env["PATH"] = f"{Path(info['codexPath']).parent}:{env.get('PATH', '/usr/bin:/bin')}"
        proc = subprocess.run(
            cmd,
            input=prompt,
            text=True,
            capture_output=True,
            timeout=timeout,
            env=env,
            cwd="/tmp",
        )
        text = out_path.read_text().strip() if out_path.exists() else ""
        if not text:
            text = proc.stdout.strip()
        if proc.returncode != 0 and not text:
            raise RuntimeError((proc.stderr or "Codex CLI exited with an error.").strip()[:300])
        return text
    finally:
        try:
            out_path.unlink(missing_ok=True)
        except OSError:
            pass


def _run_anthropic_api(prompt, timeout=90, max_tokens=4096):
    key = _env_var("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY is not configured.")
    body = json.dumps({
        "model": os.environ.get("OUTLIER_CLAUDE_MODEL", "claude-sonnet-4-20250514"),
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        payload = json.loads(resp.read().decode())
    parts = [b.get("text", "") for b in payload.get("content", []) if b.get("type") == "text"]
    return "\n".join(parts)


def _run_openai_api(prompt, timeout=90):
    key = _env_var("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY is not configured.")
    body = json.dumps({
        "model": os.environ.get("OUTLIER_OPENAI_MODEL", "gpt-4.1-mini"),
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": "Return strictly valid JSON with no markdown commentary."},
            {"role": "user", "content": prompt},
        ],
    }).encode()
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {key}",
            "content-type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        payload = json.loads(resp.read().decode())
    return payload["choices"][0]["message"]["content"]


def call_llm_json(prompt, provider="auto", timeout=150):
    """Execute prompt against selected provider and return (engine_used, parsed_json)."""
    info = detect_providers()
    chosen = provider if provider and provider != "auto" else info["default"]
    if chosen == "claude":
        raw = _run_claude_cli(prompt, timeout=timeout)
        return ("claude", _extract_json_object(raw))
    if chosen == "codex":
        raw = _run_codex_cli(prompt, timeout=timeout)
        return ("codex", _extract_json_object(raw))
    if chosen == "anthropic_api":
        raw = _run_anthropic_api(prompt, timeout=timeout)
        return ("anthropic_api", _extract_json_object(raw))
    if chosen == "openai_api":
        raw = _run_openai_api(prompt, timeout=timeout)
        return ("openai_api", _extract_json_object(raw))
    raise RuntimeError("No local AI CLI (claude/codex) or API key detected.")


# ──────────── VIDEO BREAKDOWN ARCHITECTURE + MAGNETIC STORY AUDIT ────────────

def _workspace_brief(ws):
    ws = ws or {}
    ch = ws.get("character") or ws.get("persona") or {}
    off = ws.get("offer") or {}
    if not off and isinstance(ws.get("offers"), list) and ws["offers"]:
        first_off = ws["offers"][0] if isinstance(ws["offers"][0], dict) else {}
        off = {
            "name": first_off.get("name") or first_off.get("title") or "",
            "audience": "",
            "transformation": first_off.get("corePromise") or "",
            "mechanism": first_off.get("guarantee") or "",
        }
    el = ch.get("elements") or ch.get("sevenElements") or {}
    pr = ch.get("profits") or {}
    return f"""Active Workspace: {ws.get('name', 'AI Simple')}
Tagline: {ws.get('tagline', '')}
Core Offer: {off.get('name', '')} | Audience: {off.get('audience', '')} | Transformation: {off.get('transformation', '')} | Mechanism: {off.get('mechanism', '')}
Founder Persona Archetype: {ch.get('archetype', '')} | Superhero Identity: {ch.get('superhero') or ch.get('superheroIdentity', '')} | Mighty Theme: {ch.get('mightyTheme', '')}
Stand FOR: {ch.get('standFor', '')}
Stand AGAINST (Enemy): {ch.get('standAgainst', '')}
Insider Language: {el.get('insiderLanguage', '')}
Dogma: {el.get('dogma', '')}
Audience Pain: {pr.get('pain', '')} | Frustration: {pr.get('frustration', '')} | Dreams: {pr.get('dreams', '')}
Writing Style: {ch.get('writingStyle', '')}"""


def build_breakdown_prompt(reel, workspace_profile=None):
    transcript = (reel.get("transcript") or "").strip()
    caption = (reel.get("caption") or "").strip()
    creator = reel.get("creator_username") or reel.get("ownerUsername") or "creator"
    platform = reel.get("platform") or "instagram"
    plays = reel.get("plays") or reel.get("videoPlayCount") or 0
    likes = reel.get("likes") or reel.get("likesCount") or 0
    comments = reel.get("comments") or reel.get("commentsCount") or 0
    duration = reel.get("duration") or reel.get("videoDuration") or 0
    ratio = reel.get("ratio") or 1.0

    return f"""You are an elite short-form viral content reverse-engineer combining:
1. Video Breakdown Architecture precision (Hook Alignment, Mad-Lib Formula, Beat-by-Beat Retention Architecture, Idea Contrast Mechanism, Storytelling Format & Scriptwriting Craft Tactics, Visual Layout Blueprint), AND
2. Magnetic Story Audit & the 7 Magnetism Elements (Character vs Plot, Polarization, Magnification, Context Anchor, Core Story Advancement, Persona Deficit Score 0–12, plus Origin, Parables, Miracles, Insider Language, Dogma, Enemies, and Flaws).

Analyze THIS specific video deeply. Be concrete, sharp, forensic, and cite exact phrases from the transcript/caption. Never output filler.
WHITE-LABEL RULE: Never mention third-party tool or guru names (do NOT write "Sandcastles", "vidIQ", "Kallaway", "Dan Kennedy", or "Attractive Character") anywhere inside your JSON values. Always refer cleanly to "Video Breakdown Architecture", "Founder Persona", "Magnetic Story Audit", and "7 Magnetism Elements".

VIDEO DATA:
- Creator: @{creator} ({platform})
- Outlier Multiple: {ratio}x creator median | Views: {plays} | Likes: {likes} | Comments: {comments} | Duration: {duration}s
- Spoken Transcript:
\"\"\"{transcript or '[No spoken transcript captured — analyze from caption + context]'}\"\"\"
- Caption:
\"\"\"{caption[:1600]}\"\"\"

ACTIVE WORKSPACE FOUNDER PERSONA & OFFER (use this to write hyper-specific remixes & characterRewrite):
{_workspace_brief(workspace_profile)}

Return ONLY ONE valid JSON object (no markdown, no explanation outside JSON) with this EXACT schema:
{{
  "summary": "2-3 razor-sharp sentences explaining the video's thesis, retention engine, psychological mechanism, and why it hit {ratio}x median.",
  "topic": "Specific 2-4 word topic cluster (e.g. 'Claude AI Prompt Engineering', 'Short-Form Hook Psychology', 'Meta Ads Creative Testing')",
  "beatsOverview": "1 crisp Video Breakdown Architecture sentence summarizing the structural progression and retention arc of the video.",
  "beats": [
    {{
      "label": "Specific named beat (e.g. 'Pattern-Interrupt Hook', 'Step 1: The Context Anchor', 'Contrarian Snapback', 'Mechanism Proof', 'Synthesis & CTA')",
      "timeRange": "0:00 – 0:04",
      "text": "Exact portion of the transcript belonging to this beat.",
      "why": "1 concise sentence explaining the retention/psychological job this beat performs."
    }}
  ],
  "idea": {{
    "ideaSeed": "Concise 1-line core premise of this video.",
    "uniqueAngle": "The strategic reframing that makes this feel fresh instead of generic commodity advice.",
    "commonBelief": "The default status-quo belief the audience walks in holding.",
    "contrarianReality": "The sharper contrarian truth or tension the creator introduces.",
    "evidence": [
      "3 to 4 concrete proof points, numbers, demos, or examples actually used in this video."
    ],
    "remixes": [
      "Option 1: Specific ready-to-film video premise + opening hook tailored to the active workspace's Offer, Enemy, and Founder Persona.",
      "Option 2: A second distinct angle using the active workspace's Insider Language or Proprietary Mechanism.",
      "Option 3: A contrarian polarization angle attacking the workspace's named Enemy."
    ]
  }},
  "hook": {{
    "category": "One of: Trap Mistake | Comparison | Tutorial | Secret Reveal Breakdown | Case Study | Personal Experience | Question | List | Problem | Authority",
    "formula": "Exact fill-in-the-blank Mad-Lib template parameterized from this video's real opening line (using [Bracketed Slots]).",
    "spokenHook": "Exact opening 1-2 sentences spoken in the first 3-5 seconds.",
    "visualHook": "Best concrete visual framing / motion / text-overlay hook for seconds 0-3.",
    "alignmentAssessment": "Sharp Video Breakdown Architecture diagnosis of spoken + visual + on-screen text alignment AND one specific tweak to make seconds 0-3 hit even harder."
  }},
  "format": {{
    "category": "One of: Breakdown Explainer | Common Trap Mistake | A Vs B Comparison | Listicle | Case Study | Personal Learning Epiphany | Problem Solution | Yap / Hot Take",
    "description": "1-sentence definition of how this structural archetype works.",
    "analysis": "2-3 sentences on why THIS specific video's narrative flow keeps viewers watching and what structural moves to model.",
    "tactics": [
      "3 to 5 specific scriptwriting craft tactics actually observed in this script (e.g. 'Direct Problem Callout Then Rapid-Fire Proof', 'Named Tool Specificity Anchor', 'Contrarian Snapback Before Payoff')."
    ]
  }},
  "visual": {{
    "category": "Studio Set | Full Screen / Hybrid | In-World | Greenscreen | Faceless",
    "subCategory": "Office Room Yap | Screen Demo + Face Cam | Notes / Article Greenscreen | Whiteboard Breakdown | Car Yap / Walk-and-Talk | Faceless Visual Explainer",
    "framing": "Specific framing, shot cadence, and visual proof recipe to recreate this.",
    "textCues": "Specific on-screen headline/caption/B-roll callouts for the first 3 seconds and key turns."
  }},
  "kennedy": {{
    "characterVsPlot": "Character-Led | Balanced | Plot-Led",
    "polarization": "Strong | Weak | None",
    "magnification": "Fully Magnified | Moderately Magnified | Diminished",
    "contextAnchor": "Fully Anchored | Partially Anchored | Floating",
    "coreStory": "Advances Character | Hybrid | Information Delivery",
    "deficitScore": 6,
    "elements": {{
      "origin": {{"status": "Present or Absent", "evidence": "Exact quote from video or concrete note on how to inject Origin"}},
      "parables": {{"status": "Present or Absent", "evidence": "Exact quote or missing opportunity"}},
      "miracles": {{"status": "Present or Absent", "evidence": "Exact proof/result cited or gap"}},
      "insiderLanguage": {{"status": "Present or Absent", "evidence": "Exact coined term/framework or gap"}},
      "dogma": {{"status": "Present or Absent", "evidence": "Exact non-negotiable rule stated or gap"}},
      "enemies": {{"status": "Present or Absent", "evidence": "Exact named enemy/anti-pattern or gap"}},
      "flaws": {{"status": "Present or Absent", "evidence": "Exact self-disclosure/vulnerability or gap"}}
    }},
    "characterRewrite": "2-3 concrete spoken sentences showing how the active workspace's Founder Persona (using their Superhero Identity, Enemy, and Dogma) would open and reframe this exact outlier."
  }}
}}"""


def generate_video_breakdown(reel, workspace_profile=None, provider="auto"):
    prompt = build_breakdown_prompt(reel, workspace_profile)
    engine, raw = call_llm_json(prompt, provider=provider, timeout=160)

    # Normalize & validate required keys so build.py UI never breaks
    beats = raw.get("beats") if isinstance(raw.get("beats"), list) else []
    clean_beats = []
    for b in beats[:8]:
        if not isinstance(b, dict):
            continue
        clean_beats.append({
            "label": str(b.get("label") or "Beat").strip(),
            "timeRange": str(b.get("timeRange") or "0:00").strip(),
            "text": str(b.get("text") or "").strip(),
            "why": str(b.get("why") or "").strip(),
        })

    idea = raw.get("idea") if isinstance(raw.get("idea"), dict) else {}
    hook = raw.get("hook") if isinstance(raw.get("hook"), dict) else {}
    fmt = raw.get("format") if isinstance(raw.get("format"), dict) else {}
    vis = raw.get("visual") if isinstance(raw.get("visual"), dict) else {}
    ken = raw.get("kennedy") if isinstance(raw.get("kennedy"), dict) else {}

    els_in = ken.get("elements") if isinstance(ken.get("elements"), dict) else {}
    clean_els = {}
    for k in ("origin", "parables", "miracles", "insiderLanguage", "dogma", "enemies", "flaws"):
        v = els_in.get(k) if isinstance(els_in.get(k), dict) else {}
        st = "Present" if str(v.get("status", "")).lower().startswith("pres") else "Absent"
        clean_els[k] = {
            "status": st,
            "evidence": str(v.get("evidence") or ("Present in script" if st == "Present" else "Not deployed in this video")).strip(),
        }

    try:
        deficit = max(0, min(12, int(round(float(ken.get("deficitScore", 6))))))
    except (TypeError, ValueError):
        deficit = 6

    full_text = (reel.get("transcript") or reel.get("caption") or "").strip()
    return {
        "engine": engine,
        "analyzedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "wordCount": len(full_text.split()) if full_text else 0,
        "summary": str(raw.get("summary") or "").strip(),
        "beatOverview": str(raw.get("beatsOverview") or raw.get("beatOverview") or "").strip(),
        "beats": clean_beats,
        "idea": {
            "topic": str(raw.get("topic") or idea.get("topic") or "Growth & Strategy").strip(),
            "ideaSeed": str(idea.get("ideaSeed") or "").strip(),
            "uniqueAngle": str(idea.get("uniqueAngle") or "").strip(),
            "commonBelief": str(idea.get("commonBelief") or "").strip(),
            "contrarianReality": str(idea.get("contrarianReality") or "").strip(),
            "supportingEvidence": [str(x).strip() for x in (idea.get("evidence") or idea.get("supportingEvidence") or []) if str(x).strip()][:5],
            "remixes": [str(x).strip() for x in (idea.get("remixes") or []) if str(x).strip()][:4],
        },
        "hook": {
            "category": str(hook.get("category") or "Authority").strip(),
            "formula": str(hook.get("formula") or "").strip(),
            "spokenHook": str(hook.get("spokenHook") or "").strip(),
            "visualHook": str(hook.get("visualHook") or "").strip(),
            "analysis": str(hook.get("alignmentAssessment") or hook.get("analysis") or "").strip(),
        },
        "format": {
            "category": str(fmt.get("category") or "Breakdown Explainer").strip(),
            "description": str(fmt.get("description") or "").strip(),
            "analysis": str(fmt.get("analysis") or "").strip(),
            "tactics": [str(x).strip() for x in (fmt.get("tactics") or []) if str(x).strip()][:6],
        },
        "visual": {
            "category": str(vis.get("category") or "Studio Set").strip(),
            "subCategory": str(vis.get("subCategory") or "Office Room Yap").strip(),
            "visualHook": str(hook.get("visualHook") or vis.get("visualHook") or "Move In Frame").strip(),
            "pacingNote": str(vis.get("framing") or vis.get("pacingNote") or "").strip(),
            "textCues": str(vis.get("textCues") or "").strip(),
        },
        "kennedy": {
            "characterVsPlot": str(ken.get("characterVsPlot") or "Balanced").strip(),
            "polarization": str(ken.get("polarization") or "Weak").strip(),
            "magnification": str(ken.get("magnification") or "Moderately Magnified").strip(),
            "contextAnchor": str(ken.get("contextAnchor") or "Partially Anchored").strip(),
            "coreStory": str(ken.get("coreStory") or "Hybrid").strip(),
            "deficitScore": deficit,
            "elements": clean_els,
            "characterRewrite": str(ken.get("characterRewrite") or "").strip(),
        },
    }


def generate_script_step(step, payload, workspace_profile=None, provider="auto"):
    """Power the 4-step Script Builder & Draft Fixer via Claude/Codex."""
    topic = (payload.get("topic") or "").strip()
    custom = (payload.get("customPrompt") or "").strip()
    source = payload.get("sourceReel") or {}
    research = payload.get("research") or {}
    selected_hook = (payload.get("selectedHook") or "").strip()
    existing_draft = (payload.get("draft") or "").strip()

    ws_block = _workspace_brief(workspace_profile)
    src_block = ""
    if source:
        src_block = f"""SOURCE OUTLIER TO MODEL:
- @{source.get('creator', '')} ({source.get('ratio', '')}x, {source.get('plays', '')} plays)
- Hook: {source.get('hook', '')}
- Format: {source.get('format', '')}
- Transcript excerpt: {(source.get('transcript') or '')[:900]}"""

    if step == "research":
        prompt = f"""You are an elite short-form viral content strategist combining Video Breakdown Architecture with Magnetic Story Audit principles.
Build Step 2 (Research Brief) for a short-form video. Never mention third-party tool or guru names in your output.
TOPIC: {topic}
CUSTOM DIRECTION: {custom}
{src_block}
WORKSPACE FOUNDER PERSONA & OFFER:
{ws_block}

Return ONLY valid JSON:
{{
  "executiveSummary": "2-3 punchy sentences framing the core thesis and audience tension.",
  "howToEngage": ["3 concrete psychological engagement triggers for seconds 0-15"],
  "surprisingFacts": ["3 sharp, concrete proof/contrast facts or realizations"],
  "contrastMoments": ["3 crisp Common Belief vs Contrarian Reality contrasts"]
}}"""
    elif step == "hooks":
        prompt = f"""You are an elite viral hook engineer specializing in Video Breakdown Architecture and Founder Persona positioning.
Generate 6 elite, film-ready short-form opening hooks (12-24 words each, ZERO generic fluff, strong visual + spoken alignment, injecting the workspace's Founder Persona / Enemy where sharp). Never mention third-party tool or guru names in your output.
TOPIC: {topic}
CUSTOM DIRECTION: {custom}
RESEARCH SUMMARY: {research.get('executiveSummary', '')}
{src_block}
WORKSPACE FOUNDER PERSONA & OFFER:
{ws_block}

Return ONLY valid JSON:
{{
  "hooks": [
    {{
      "style": "Trap Mistake | Secret Reveal Breakdown | Case Study | Comparison | Authority | Personal Experience",
      "inspiredBy": "@creator or Proven Hook Pattern",
      "text": "Exact spoken opening line ready to read to camera.",
      "visualCue": "Exact 0-3s visual action or on-screen text."
    }}
  ]
}}"""
    elif step == "script":
        prompt = f"""You are an elite short-form viral scriptwriter combining Video Breakdown Architecture with Magnetic Story Audit & the 7 Magnetism Elements.
Write Step 4: a complete, high-retention 45-75 second spoken short-form script.
Include clear beat headers ([0:00 HOOK], [0:04 CONTEXT ANCHOR], [0:10 ENEMY & CONTRAST], [0:22 MECHANISM & PROOF], [0:42 PAYOFF & CTA]) plus brief [VISUAL: ...] cues, written strictly in the workspace's Founder Persona voice, injecting at least 3 of the 7 Magnetism Elements naturally. Never mention third-party tool or guru names in your output.
TOPIC: {topic}
CHOSEN HOOK: {selected_hook}
CUSTOM DIRECTION: {custom}
RESEARCH BRIEF: {json.dumps(research)[:1200]}
{src_block}
WORKSPACE FOUNDER PERSONA & OFFER:
{ws_block}

Return ONLY valid JSON:
{{
  "title": "Short punchy script title",
  "script": "Full line-by-line script with timestamps and [VISUAL: ...] cues.",
  "wordCount": 165,
  "estimatedDuration": "0:58",
  "kennedyElementsUsed": ["Enemies", "Insider Language", "Dogma"]
}}"""
    elif step == "fix":
        prompt = f"""You are an elite short-form script editor using Video Breakdown Architecture and the 7 Magnetism Elements to ruthlessly upgrade a rough draft.
Keep the creator's core idea, eliminate throat-clearing, sharpen seconds 0-3, add a Contrarian Snapback, inject the workspace's Founder Persona / Enemy / Dogma, and tighten pacing to high-retention short-form cadence. Never mention third-party tool or guru names in your output.
DRAFT TO FIX:
\"\"\"{existing_draft}\"\"\"
WORKSPACE FOUNDER PERSONA & OFFER:
{ws_block}

Return ONLY valid JSON:
{{
  "diagnosis": ["3 specific flaws diagnosed in the original draft"],
  "fixedScript": "The complete rewritten line-by-line script with timestamps and [VISUAL: ...] cues.",
  "hookUpgrade": "The upgraded opening hook line."
}}"""
    else:
        raise ValueError(f"Unknown script step: {step}")

    engine, data = call_llm_json(prompt, provider=provider, timeout=140)
    data["engine"] = engine
    return data


# ──────────── BRAIN CONTEXT, AI CHAT & CREATIVE ARSENAL ENGINE ────────────

_WHITE_LABEL_RULE = (
    'WHITE-LABEL RULE: Never mention third-party tool or guru names (no "Sandcastles", '
    '"vidIQ", "Kallaway", "Dan Kennedy", or "Attractive Character") in your output. '
    'Refer cleanly to "Video Breakdown Architecture", "Founder Persona", '
    '"Magnetic Story Audit", and "7 Magnetism Elements".'
)


def _as_text(val):
    """Coerce strings, lists, or dicts into compact human-readable text."""
    if val is None:
        return ""
    if isinstance(val, str):
        return re.sub(r"\s+", " ", val).strip()
    if isinstance(val, (int, float, bool)):
        return str(val)
    if isinstance(val, list):
        parts = [_as_text(x) for x in val]
        return "; ".join(p for p in parts if p)
    if isinstance(val, dict):
        parts = []
        for k, v in val.items():
            txt = _as_text(v)
            if txt:
                parts.append(f"{k}: {txt}")
        return " | ".join(parts)
    return str(val).strip()


def _clip(text, limit):
    s = _as_text(text)
    if len(s) <= limit:
        return s
    return s[: max(0, limit - 1)].rstrip(" ,;:-") + "…"


def _format_modalities(modalities):
    """Format S/A/B/C-Tier modalities from string, list, or dict."""
    if not modalities:
        return ""
    if isinstance(modalities, str):
        return _clip(modalities, 140)
    if isinstance(modalities, list):
        items = []
        for m in modalities[:6]:
            if isinstance(m, dict):
                tier = m.get("tier") or m.get("grade") or ""
                name = m.get("name") or m.get("label") or m.get("title") or m.get("modality") or ""
                val = m.get("perceivedValue") or m.get("value") or ""
                piece = f"[{tier}] {name}" if tier and name else (name or tier)
                if val:
                    piece += f" ({val})"
                if piece.strip():
                    items.append(piece.strip())
            else:
                t = _as_text(m)
                if t:
                    items.append(t)
        return _clip(", ".join(items), 180)
    if isinstance(modalities, dict):
        parts = []
        for tier_key, val in modalities.items():
            t = _as_text(val)
            if t:
                parts.append(f"{tier_key}: {t}")
        return _clip(" | ".join(parts), 180)
    return _clip(modalities, 140)


def _brain_context_block(brain_payload, max_chars=4500):
    """Format a tight, high-signal workspace Brain context block (~2500-4500 chars max)."""
    bp = brain_payload if isinstance(brain_payload, dict) else {}
    ws = bp.get("workspace") if isinstance(bp.get("workspace"), dict) else {}
    persona = bp.get("persona") if isinstance(bp.get("persona"), dict) else (
        bp.get("character") if isinstance(bp.get("character"), dict) else {}
    )
    avatars = bp.get("avatars") if isinstance(bp.get("avatars"), list) else []
    products = bp.get("products") if isinstance(bp.get("products"), list) else []
    offers = bp.get("offers") if isinstance(bp.get("offers"), list) else []
    memories = bp.get("memories") if isinstance(bp.get("memories"), list) else []
    attached = bp.get("attachedAssets") if isinstance(bp.get("attachedAssets"), list) else []

    sections = []

    # 1. Workspace
    ws_name = _clip(ws.get("name") or bp.get("name") or "Active Workspace", 80)
    ws_tag = _clip(ws.get("tagline") or bp.get("tagline") or "", 140)
    ws_lines = [f"=== WORKSPACE: {ws_name} ==="]
    if ws_tag:
        ws_lines.append(f"Tagline: {ws_tag}")
    sections.append("\n".join(ws_lines))

    # 2. Founder Persona (~1300 chars budget)
    if persona:
        p_lines = ["=== FOUNDER PERSONA ==="]
        archetype = _clip(persona.get("archetype"), 80)
        superhero = _clip(persona.get("superheroIdentity") or persona.get("superhero"), 90)
        theme = _clip(persona.get("mightyTheme"), 120)
        header_bits = [b for b in [
            f"Archetype: {archetype}" if archetype else "",
            f"Superhero Identity: {superhero}" if superhero else "",
            f"Mighty Theme: {theme}" if theme else "",
        ] if b]
        if header_bits:
            p_lines.append(" | ".join(header_bits))
        if persona.get("identity"):
            p_lines.append(f"Identity: {_clip(persona.get('identity'), 200)}")
        if persona.get("standFor"):
            p_lines.append(f"Stand FOR: {_clip(persona.get('standFor'), 160)}")
        if persona.get("standAgainst"):
            p_lines.append(f"Stand AGAINST (Enemy): {_clip(persona.get('standAgainst'), 160)}")
        if persona.get("writingStyle"):
            p_lines.append(f"Writing Style: {_clip(persona.get('writingStyle'), 140)}")

        voices = persona.get("voices")
        if isinstance(voices, list) and voices:
            v_bits = []
            for v in voices[:4]:
                if isinstance(v, dict):
                    vn = _clip(v.get("name") or v.get("label") or v.get("mode") or "Voice", 40)
                    vd = _clip(v.get("tone") or v.get("description") or v.get("style") or v.get("context"), 90)
                    v_bits.append(f"{vn}: {vd}" if vd else vn)
                else:
                    t = _clip(v, 80)
                    if t:
                        v_bits.append(t)
            if v_bits:
                p_lines.append("Voices: " + " ; ".join(v_bits))

        seven = persona.get("sevenElements") or persona.get("elements")
        if isinstance(seven, dict) and seven:
            el_bits = []
            for key in ("origin", "parables", "miracles", "insiderLanguage", "dogma", "enemies", "flaws"):
                val = seven.get(key)
                txt = _clip(val, 110)
                if txt:
                    el_bits.append(f"  - {key}: {txt}")
            if el_bits:
                p_lines.append("7 Magnetism Elements:\n" + "\n".join(el_bits))

        jbt = persona.get("jamesBondTest")
        if jbt:
            p_lines.append(f"Signature Magnetism Test: {_clip(jbt, 160)}")

        stories = persona.get("stories")
        if isinstance(stories, list) and stories:
            st_bits = []
            for st in stories[:5]:
                if isinstance(st, dict):
                    title = _clip(st.get("title") or st.get("name") or "Story", 50)
                    summary = _clip(st.get("summary") or st.get("content") or st.get("lesson") or st.get("hook"), 110)
                    st_bits.append(f"{title}: {summary}" if summary else title)
                else:
                    t = _clip(st, 110)
                    if t:
                        st_bits.append(t)
            if st_bits:
                p_lines.append("Core Stories: " + " | ".join(st_bits))

        acc_hooks = persona.get("accountHooks")
        if isinstance(acc_hooks, list) and acc_hooks:
            h_bits = []
            for h in acc_hooks[:6]:
                if isinstance(h, dict):
                    ang = _clip(h.get("angle") or h.get("category") or "", 24)
                    ht = _clip(h.get("hook") or h.get("text") or "", 95)
                    if ht:
                        h_bits.append(f"[{ang}] {ht}" if ang else ht)
                else:
                    ht = _clip(h, 95)
                    if ht:
                        h_bits.append(ht)
            if h_bits:
                p_lines.append("Brand Account Hooks: " + " | ".join(h_bits))

        sections.append(_clip_block("\n".join(p_lines), 1450))

    # 3. Customer Avatars (~700 chars budget)
    if avatars:
        a_lines = ["=== CUSTOMER AVATARS ==="]
        for av in avatars[:4]:
            if not isinstance(av, dict):
                continue
            name = _clip(av.get("name") or "Avatar", 50)
            parts = [f"• {name}"]
            for lbl, key, lim in (
                ("Demo", "demographics", 90),
                ("Pain", "pain", 120),
                ("Desires", "desires", 110),
                ("Objections", "objections", 100),
                ("Triggers", "buyingTriggers", 100),
                ("Daily Life", "dailyLife", 90),
                ("Notes", "customNotes", 90),
            ):
                val = _clip(av.get(key), lim)
                if val:
                    parts.append(f"{lbl}: {val}")
            a_lines.append(" | ".join(parts))
        if len(a_lines) > 1:
            sections.append(_clip_block("\n".join(a_lines), 780))

    # 4. Products & Modality Tiers (~600 chars budget)
    product_name_by_id = {}
    if products:
        pr_lines = ["=== PRODUCTS & VALUE MODALITIES ==="]
        for prod in products[:6]:
            if not isinstance(prod, dict):
                continue
            pid = prod.get("id")
            pname = _clip(prod.get("name") or "Product", 60)
            if pid:
                product_name_by_id[str(pid)] = pname
            bits = [f"• {pname}"]
            if prod.get("price"):
                bits.append(f"Price: {_clip(prod.get('price'), 30)}")
            if prod.get("perceivedValue"):
                bits.append(f"Perceived Value: {_clip(prod.get('perceivedValue'), 35)}")
            if prod.get("delivery"):
                bits.append(f"Delivery: {_clip(prod.get('delivery'), 70)}")
            mods = _format_modalities(prod.get("modalities"))
            if mods:
                bits.append(f"Modalities: {mods}")
            if prod.get("description"):
                bits.append(f"Desc: {_clip(prod.get('description'), 100)}")
            pr_lines.append(" | ".join(bits))
        if len(pr_lines) > 1:
            sections.append(_clip_block("\n".join(pr_lines), 650))

    # 5. Offers (~600 chars budget)
    if offers:
        of_lines = ["=== OFFERS ==="]
        for off in offers[:4]:
            if not isinstance(off, dict):
                continue
            oname = _clip(off.get("name") or off.get("title") or "Offer", 60)
            bits = [f"• {oname}"]
            if off.get("corePromise"):
                bits.append(f"Promise: {_clip(off.get('corePromise'), 120)}")
            pids = off.get("productIds")
            if isinstance(pids, list) and pids:
                resolved = [product_name_by_id.get(str(pid), str(pid)) for pid in pids[:6]]
                bits.append(f"Bundled: {', '.join(resolved)}")
            if off.get("offerPrice"):
                bits.append(f"Offer Price: {_clip(off.get('offerPrice'), 30)}")
            if off.get("totalPerceivedValue"):
                bits.append(f"Total Value: {_clip(off.get('totalPerceivedValue'), 35)}")
            if off.get("guarantee"):
                bits.append(f"Guarantee: {_clip(off.get('guarantee'), 90)}")
            if off.get("urgency"):
                bits.append(f"Urgency: {_clip(off.get('urgency'), 70)}")
            if off.get("cta"):
                bits.append(f"CTA: {_clip(off.get('cta'), 80)}")
            of_lines.append(" | ".join(bits))
        if len(of_lines) > 1:
            sections.append(_clip_block("\n".join(of_lines), 620))

    # 6. Brain Memories (~550 chars budget)
    if memories:
        m_lines = ["=== BRAIN MEMORIES ==="]
        for mem in memories[:10]:
            if not isinstance(mem, dict):
                continue
            cat = _clip(mem.get("category") or "Note", 24)
            title = _clip(mem.get("title") or "", 55)
            content = _clip(mem.get("content") or "", 130)
            if title or content:
                m_lines.append(f"• [{cat}] {title}: {content}" if title else f"• [{cat}] {content}")
        if len(m_lines) > 1:
            sections.append(_clip_block("\n".join(m_lines), 560))

    # 7. Attached Assets (~600 chars budget)
    if attached:
        at_lines = ["=== ATTACHED ASSETS ==="]
        for asset in attached[:4]:
            if not isinstance(asset, dict):
                continue
            atype = _clip(asset.get("type") or "Doc", 24)
            title = _clip(asset.get("title") or "Untitled Asset", 60)
            content = _clip(asset.get("content") or "", 220)
            at_lines.append(f"• [{atype}] {title}: {content}" if content else f"• [{atype}] {title}")
        if len(at_lines) > 1:
            sections.append(_clip_block("\n".join(at_lines), 620))

    combined = "\n\n".join(s for s in sections if s.strip())
    if len(combined) > max_chars:
        return combined[: max_chars - 16].rstrip() + "\n[…truncated]"
    return combined


def _clip_block(text, limit):
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 2)].rstrip() + "…"


def _resolve_target_entities(brain_payload, params):
    """Resolve explicit target avatar, target offer (+ bundled products), and brand-owned account hooks."""
    bp = brain_payload if isinstance(brain_payload, dict) else {}
    p = params if isinstance(params, dict) else {}
    avatars = bp.get("avatars") if isinstance(bp.get("avatars"), list) else []
    offers = bp.get("offers") if isinstance(bp.get("offers"), list) else []
    products = bp.get("products") if isinstance(bp.get("products"), list) else []
    persona = bp.get("persona") if isinstance(bp.get("persona"), dict) else {}

    avatar_name = (p.get("avatarName") or "").strip()
    offer_name = (p.get("offerName") or "").strip()

    target_avatar = None
    if avatar_name:
        low = avatar_name.lower()
        for av in avatars:
            if isinstance(av, dict) and str(av.get("name") or "").strip().lower() == low:
                target_avatar = av
                break
        if not target_avatar:
            for av in avatars:
                if isinstance(av, dict) and low in str(av.get("name") or "").lower():
                    target_avatar = av
                    break
    elif avatars and isinstance(avatars[0], dict):
        target_avatar = avatars[0]

    target_offer = None
    if offer_name:
        low = offer_name.lower()
        for off in offers:
            if isinstance(off, dict) and str(off.get("name") or off.get("title") or "").strip().lower() == low:
                target_offer = off
                break
        if not target_offer:
            for off in offers:
                if isinstance(off, dict) and low in str(off.get("name") or off.get("title") or "").lower():
                    target_offer = off
                    break
    elif offers and isinstance(offers[0], dict):
        target_offer = offers[0]

    bundled_products = []
    if target_offer and isinstance(target_offer.get("productIds"), list):
        wanted = {str(pid) for pid in target_offer["productIds"]}
        for prod in products:
            if isinstance(prod, dict) and str(prod.get("id") or "") in wanted:
                bundled_products.append(prod)
    if not bundled_products and products:
        bundled_products = [pr for pr in products[:5] if isinstance(pr, dict)]

    account_hooks = []
    raw_hooks = persona.get("accountHooks") if isinstance(persona.get("accountHooks"), list) else []
    for h in raw_hooks:
        if isinstance(h, dict):
            txt = _as_text(h.get("hook") or h.get("text"))
            if txt:
                account_hooks.append({
                    "angle": _as_text(h.get("angle") or h.get("category") or "Brand Hook"),
                    "hook": txt,
                })
        else:
            txt = _as_text(h)
            if txt:
                account_hooks.append({"angle": "Brand Hook", "hook": txt})

    return {
        "avatar": target_avatar,
        "avatarName": (target_avatar.get("name") if target_avatar else avatar_name) or "Primary Customer Avatar",
        "offer": target_offer,
        "offerName": ((target_offer.get("name") or target_offer.get("title")) if target_offer else offer_name) or "Core Offer",
        "bundledProducts": bundled_products,
        "accountHooks": account_hooks,
    }


def _format_target_focus_block(targets):
    lines = []
    av = targets.get("avatar")
    if av:
        lines.append("PRIMARY TARGET AVATAR:")
        lines.append(json.dumps(av, ensure_ascii=False)[:750])
    elif targets.get("avatarName"):
        lines.append(f"PRIMARY TARGET AVATAR: {targets['avatarName']}")

    off = targets.get("offer")
    if off:
        lines.append("PRIMARY TARGET OFFER:")
        lines.append(json.dumps(off, ensure_ascii=False)[:700])
    elif targets.get("offerName"):
        lines.append(f"PRIMARY TARGET OFFER: {targets['offerName']}")

    bundled = targets.get("bundledProducts") or []
    if bundled:
        lines.append("BUNDLED PRODUCTS & S/A/B/C MODALITIES:")
        lines.append(json.dumps(bundled[:5], ensure_ascii=False)[:850])

    return "\n".join(lines)


def chat_with_brain(messages, brain_payload, mode="chief_of_staff", provider="auto"):
    """Brain-Aware AI Chat supporting chief_of_staff, persona_coach, and offer_architect modes."""
    valid_modes = {"chief_of_staff", "persona_coach", "offer_architect"}
    active_mode = mode if mode in valid_modes else "chief_of_staff"

    # Normalize incoming messages
    if isinstance(messages, str):
        norm_messages = [{"role": "user", "content": messages.strip()}]
    elif isinstance(messages, list):
        norm_messages = []
        for m in messages[-16:]:
            if isinstance(m, dict):
                role = "assistant" if str(m.get("role", "")).lower() == "assistant" else "user"
                content = str(m.get("content") or "").strip()
                if content:
                    norm_messages.append({"role": role, "content": content[:2000]})
            elif isinstance(m, str) and m.strip():
                norm_messages.append({"role": "user", "content": m.strip()[:2000]})
    else:
        norm_messages = []

    if not norm_messages:
        raise ValueError("At least one chat message is required.")

    transcript_lines = []
    for m in norm_messages:
        speaker = "FOUNDER" if m["role"] == "user" else "ASSISTANT"
        transcript_lines.append(f"{speaker}: {m['content']}")
    convo_block = "\n\n".join(transcript_lines)

    brain_block = _brain_context_block(brain_payload)

    mode_directives = {
        "chief_of_staff": (
            "ROLE: Strategic Chief of Staff & Growth Operator with full awareness of the workspace Brain "
            "(Founder Persona, Avatars, Products, Offers, Memories) and attached ZeroDrive / Asset Library documents.\n"
            "STYLE: Executive, incisive, zero-fluff, deeply grounded in the workspace's real positioning, numbers, and voice. "
            "Synthesize across Persona + Avatar + Offer + Assets to propose concrete next moves, angles, or drafts. "
            "If the user shares new strategic decisions, client results, positioning rules, or campaign facts, extract them cleanly into suggestedMemories."
        ),
        "persona_coach": (
            "ROLE: Elite Founder Persona & Magnetic Story Coach.\n"
            "MISSION: Interactively extract and sharpen the founder's unmistakable identity, voice traits, 7 Magnetism Elements "
            "(Origin, Parables, Miracles, Insider Language, Dogma, Enemies, Flaws), raw stories, and brand-owned Account Hooks.\n"
            "STYLE: Warm, incisive interviewer. Reflect back the sharpest gold from what the founder just said, upgrade its framing "
            "into punchy language, immediately capture any concrete stories, hooks, voice traits, dogma, or enemies into `suggestedMemories`, "
            "and end with 1 to 3 targeted, high-leverage follow-up questions to pull out the next layer of gold."
        ),
        "offer_architect": (
            "ROLE: Grand-Slam Offer Architect & Modality Value Engineer.\n"
            "MISSION: Audit and upgrade the workspace's Products and Offers using the S/A/B/C Modality Value Ladder:\n"
            "  - S-Tier (Highest Perceived Value / Asymmetric Leverage): Done-For-You / Done-With-You installations, proprietary AI systems/agents, 1:1 implementation sprints, revenue-linked workshops.\n"
            "  - A-Tier (High Leverage / Guided Speed): Live coaching/audits, tear-down reviews, battle-tested plug-and-play SOPs, bespoke templates, private peer rooms.\n"
            "  - B-Tier (Structured Utility): Recorded playbooks, swipe files, calculators, checklists.\n"
            "  - C-Tier (Commodity Baseline): Generic PDFs, passive video libraries, vague community access.\n"
            "STYLE: Quantify Total Perceived Value vs Offer Price (aim for 5x-10x+ believable value gap), upgrade weak C/B deliverables into A/S-Tier mechanisms, "
            "and sharpen Core Promise, Risk-Reversal Guarantee, Real Urgency, and CTA. Capture concrete offer upgrades into `suggestedMemories`."
        ),
    }

    prompt = f"""{mode_directives[active_mode]}

{_WHITE_LABEL_RULE}

ACTIVE WORKSPACE BRAIN & ATTACHED CONTEXT:
{brain_block}

CONVERSATION HISTORY:
{convo_block}

Respond to the FOUNDER's latest message with high precision and practical value.
Return ONLY ONE valid JSON object (no markdown fences around the JSON, no commentary outside JSON) with this EXACT schema:
{{
  "reply": "Your full conversational response formatted in clean Markdown.",
  "suggestedMemories": [
    {{
      "category": "One of: Story | Hook | Voice | Persona | Avatar | Offer | Product | Dogma | Enemy | Proof | Strategy",
      "title": "Concise 3-7 word memory title",
      "content": "Concrete, self-contained distilled insight, story beat, hook, or rule worth saving to Brain Memories."
    }}
  ],
  "suggestedTitle": "Concise 4-8 word title if the user saves this response to the Asset Library",
  "saveableMarkdown": "Clean standalone Markdown document version of the key takeaways, draft, or blueprint from this turn (ready to save directly to the Asset Library / ZeroDrive)."
}}

NOTE: Only populate `suggestedMemories` (0 to 4 items) when the conversation contains concrete, reusable facts, stories, hooks, voice traits, or offer decisions worth persisting; return [] if none yet."""

    engine, raw = call_llm_json(prompt, provider=provider, timeout=150)

    reply = str(raw.get("reply") or "").strip()
    if not reply:
        reply = "I reviewed your workspace Brain context—share a bit more detail on your target outcome and I'll map out the exact next step."

    suggested_title = str(raw.get("suggestedTitle") or "").strip() or (
        "Founder Persona Coaching Notes" if active_mode == "persona_coach"
        else "Offer Architecture Blueprint" if active_mode == "offer_architect"
        else "Chief of Staff Strategy Brief"
    )

    clean_memories = []
    raw_mems = raw.get("suggestedMemories") if isinstance(raw.get("suggestedMemories"), list) else []
    for item in raw_mems[:6]:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "").strip()
        content = str(item.get("content") or "").strip()
        category = str(item.get("category") or "Strategy").strip() or "Strategy"
        if title and content:
            clean_memories.append({
                "category": category,
                "title": title,
                "content": content,
            })

    saveable_md = str(raw.get("saveableMarkdown") or "").strip()
    if not saveable_md:
        saveable_md = f"# {suggested_title}\n\n{reply}"

    return {
        "engine": engine,
        "mode": active_mode,
        "reply": reply,
        "suggestedMemories": clean_memories,
        "suggestedTitle": suggested_title,
        "saveableMarkdown": saveable_md,
    }


def _build_presentation_markdown(data):
    lines = [f"# {data['title']}"]
    if data.get("subtitle"):
        lines.append(f"*{data['subtitle']}*")
    meta = [f"**Format:** {data['format']}", f"**Avatar:** {data['targetAvatar']}", f"**Offer:** {data['targetOffer']}"]
    if data.get("estimatedDuration"):
        meta.append(f"**Duration:** {data['estimatedDuration']}")
    lines.append("\n" + " | ".join(meta))
    if data.get("bigPromise"):
        lines.append(f"\n> **Big Promise:** {data['bigPromise']}")
    for sec in data.get("sections") or []:
        dur = f" ({sec['duration']})" if sec.get("duration") else ""
        lines.append(f"\n## {sec['name']}{dur}")
        if sec.get("falseBeliefBroken"):
            lines.append(f"- **False Belief Broken:** {sec['falseBeliefBroken']}")
        if sec.get("slideVisual"):
            lines.append(f"- **Slide / Visual Direction:** {sec['slideVisual']}")
        if sec.get("script"):
            lines.append(f"\n{sec['script']}")
    stack = data.get("offerStack") or {}
    if stack:
        lines.append("\n## Offer Stack & Modality Value Build")
        if stack.get("transitionScript"):
            lines.append(f"\n{stack['transitionScript']}\n")
        for it in stack.get("items") or []:
            tier = f"[{it['modalityTier']}] " if it.get("modalityTier") else ""
            val = f" — **{it['perceivedValue']}**" if it.get("perceivedValue") else ""
            ben = f": {it['benefit']}" if it.get("benefit") else ""
            lines.append(f"- {tier}**{it['name']}**{val}{ben}")
        if stack.get("totalPerceivedValue") or stack.get("offerPrice"):
            lines.append(f"\n**Total Perceived Value:** {stack.get('totalPerceivedValue', '')} | **Offer Price:** {stack.get('offerPrice', '')}")
        if stack.get("guarantee"):
            lines.append(f"**Guarantee:** {stack['guarantee']}")
        if stack.get("urgency"):
            lines.append(f"**Urgency:** {stack['urgency']}")
        if stack.get("cta"):
            lines.append(f"**CTA:** {stack['cta']}")
    objs = data.get("objectionHandlers") or []
    if objs:
        lines.append("\n## Q&A Objection Handlers")
        for o in objs:
            lines.append(f"- **\"{o['objection']}\"** → {o['reframe']}")
    return "\n".join(lines).strip()


def _build_email_markdown(data):
    lines = [f"# {data['title']}", f"**Format:** {data['format']} | **Avatar:** {data['targetAvatar']} | **Offer:** {data['targetOffer']}"]
    if data.get("subjectLines"):
        lines.append("\n## Subject Line Options")
        for idx, s in enumerate(data["subjectLines"], 1):
            lines.append(f"{idx}. {s}")
    if data.get("previewText"):
        lines.append(f"\n**Preview Text:** {data['previewText']}")
    emails = data.get("emails") or []
    if len(emails) > 1:
        for em in emails:
            lines.append(f"\n---\n## {em.get('day') or 'Email'}")
            if em.get("subjectLines"):
                lines.append("**Subjects:** " + " / ".join(em["subjectLines"]))
            if em.get("previewText"):
                lines.append(f"**Preview:** {em['previewText']}")
            if em.get("body"):
                lines.append(f"\n{em['body']}")
            if em.get("psCta"):
                lines.append(f"\n**P.S.** {em['psCta']}")
    else:
        if data.get("body"):
            lines.append(f"\n---\n\n{data['body']}")
        if data.get("psCta"):
            lines.append(f"\n**P.S.** {data['psCta']}")
    return "\n".join(lines).strip()


def _build_social_markdown(data):
    lines = [
        f"# {data['title']}",
        f"**Platform:** {data['platform']} | **Storytelling Format:** {data['storytellingFormat']} | **Avatar:** {data['targetAvatar']}",
    ]
    if data.get("hookOptions"):
        lines.append("\n## Hook Options (Brand-Owned)")
        for idx, h in enumerate(data["hookOptions"], 1):
            ang = f"[{h['angle']}] " if h.get("angle") else ""
            lines.append(f"{idx}. {ang}{h['hook']}")
            if h.get("visualCue"):
                lines.append(f"   - *Visual:* {h['visualCue']}")
    if data.get("beats"):
        lines.append("\n## Beat-by-Beat Script")
        for b in data["beats"]:
            tr = f" ({b['timeRange']})" if b.get("timeRange") else ""
            lines.append(f"\n### {b['label']}{tr}")
            if b.get("visualCue"):
                lines.append(f"*[VISUAL: {b['visualCue']}]*")
            if b.get("script"):
                lines.append(b["script"])
    elif data.get("fullScript"):
        lines.append(f"\n## Full Script\n\n{data['fullScript']}")
    if data.get("cta"):
        lines.append(f"\n## CTA\n{data['cta']}")
    if data.get("caption"):
        lines.append(f"\n## Caption\n{data['caption']}")
    if data.get("visualCues"):
        lines.append("\n## Visual & Production Cues")
        for vc in data["visualCues"]:
            lines.append(f"- {vc}")
    return "\n".join(lines).strip()


def _build_persona_markdown(persona):
    lines = [f"# Founder Persona: {persona.get('superheroIdentity') or persona.get('archetype') or 'Brand Leader'}"]
    if persona.get("mightyTheme"):
        lines.append(f"> **Mighty Theme:** {persona['mightyTheme']}")
    for lbl, key in (
        ("Archetype", "archetype"),
        ("Identity", "identity"),
        ("Stand FOR", "standFor"),
        ("Stand AGAINST (Enemy)", "standAgainst"),
        ("Writing Style", "writingStyle"),
        ("Signature Magnetism Test", "jamesBondTest"),
    ):
        val = _as_text(persona.get(key))
        if val:
            lines.append(f"- **{lbl}:** {val}")
    if persona.get("voices"):
        lines.append("\n## Voice Variations")
        for v in persona["voices"]:
            if isinstance(v, dict):
                lines.append(f"- **{v.get('name', 'Voice')}:** {v.get('tone', '')} — {v.get('usage', v.get('description', ''))}")
    seven = persona.get("sevenElements") or {}
    if seven:
        lines.append("\n## 7 Magnetism Elements")
        for k, v in seven.items():
            if v:
                lines.append(f"- **{k}:** {v}")
    if persona.get("stories"):
        lines.append("\n## 5 Original Stories")
        for s in persona["stories"]:
            lines.append(f"- **{s.get('title', 'Story')}** ({s.get('type', '')}): {s.get('summary', '')} *Lesson:* {s.get('lesson', '')}")
    if persona.get("accountHooks"):
        lines.append("\n## 8 Brand-Owned Account Hooks")
        for h in persona["accountHooks"]:
            lines.append(f"- **[{h.get('angle', 'Hook')}]** {h.get('hook', '')}")
    return "\n".join(lines).strip()


def _build_avatar_markdown(avatar):
    lines = [f"# Customer Avatar: {avatar.get('name') or 'Target Buyer'}"]
    if avatar.get("tagline"):
        lines.append(f"*{avatar['tagline']}*")
    for lbl, key in (
        ("Demographics", "demographics"),
        ("Daily Life", "dailyLife"),
        ("Core Pain", "pain"),
        ("Deep Desires", "desires"),
        ("Objections", "objections"),
        ("Buying Triggers", "buyingTriggers"),
        ("Watering Holes", "wateringHoles"),
        ("Verbatim Language", "verbatimLanguage"),
        ("Custom Notes", "customNotes"),
    ):
        val = avatar.get(key)
        if isinstance(val, list) and val:
            lines.append(f"\n## {lbl}")
            for x in val:
                lines.append(f"- {x}")
        elif _as_text(val):
            lines.append(f"\n## {lbl}\n{_as_text(val)}")
    return "\n".join(lines).strip()


def _build_hooks_markdown(hooks, topic=""):
    header = f"# Brand-Owned Account Hooks — {topic}" if topic else "# Brand-Owned Account Hooks"
    lines = [header]
    for idx, h in enumerate(hooks, 1):
        lines.append(f"\n{idx}. **[{h['angle']}]** {h['hook']}")
        if h.get("visualCue"):
            lines.append(f"   - *Visual:* {h['visualCue']}")
        if h.get("bestPlatform"):
            lines.append(f"   - *Best Platform:* {h['bestPlatform']}")
        if h.get("whyItWorks"):
            lines.append(f"   - *Why It Works:* {h['whyItWorks']}")
    return "\n".join(lines).strip()


def generate_arsenal_asset(tool_type, params, brain_payload, provider="auto"):
    """Generate complete Creative Arsenal assets grounded in the active workspace Brain."""
    tt = (tool_type or "").strip().lower()
    p = params if isinstance(params, dict) else {}
    brain_block = _brain_context_block(brain_payload)
    targets = _resolve_target_entities(brain_payload, p)
    target_focus = _format_target_focus_block(targets)

    topic = (p.get("topic") or p.get("brief") or "").strip()
    custom = (p.get("customInstructions") or "").strip()
    story_fmt = (p.get("storytellingFormat") or "").strip()

    if tt == "presentation":
        fmt = (p.get("format") or "Perfect Webinar").strip()
        prompt = f"""You are a world-class direct-response presentation architect and Founder Persona scriptwriter.
Build a COMPLETE, high-converting One-to-Many Presentation script tailored strictly to this workspace's Brain, Target Avatar, and Offer Stack.
Never write lazy placeholders like "[insert story here]" — write concrete, speakable, stage-ready copy grounded in the workspace Brain.

{_WHITE_LABEL_RULE}

PRESENTATION BRIEF:
- Format: {fmt} (supported archetypes: Perfect Webinar, Mini-Workshop / Masterclass, VSL (Video Sales Letter), Keynote / Stage Talk, Product Demo + Stack)
- Topic / Big Angle: {topic or "Flagship transformation & proprietary mechanism"}
- Storytelling Format: {story_fmt or "Epiphany Bridge + False-Belief Dominoes"}
- Custom Instructions: {custom or "None"}

{target_focus}

WORKSPACE BRAIN:
{brain_block}

REQUIRED ARCHITECTURE:
1. Hook & Big Promise (pattern interrupt, bold specific promise, who this is for / who should leave, open loop)
2. Origin / Epiphany Bridge Story (relatable struggle, wall hit, discovery of the new vehicle, proof/miracle)
3. Core Secret / Pillar 1 (break the Vehicle false belief with story + proof + reframe)
4. Core Secret / Pillar 2 (break the Internal false belief with story + proof + reframe)
5. Core Secret / Pillar 3 (break the External false belief with story + proof + reframe)
6. Transition to Offer (permission-based pivot from teaching to implementation)
7. Full Offer Stack with S/A/B/C Modality Perceived Value Build (itemize core program + bonuses with modality tier S/A/B/C, realistic perceived value, total value vs offer price, guarantee, urgency, clear CTA)
8. Close & Q&A Objection Handlers (4-5 sharpest buyer objections answered with conviction)

Return ONLY ONE valid JSON object with this EXACT schema:
{{
  "title": "Punchy presentation title",
  "subtitle": "Compelling 1-line subtitle",
  "bigPromise": "Exact 'How to [Desire] without [Pain] in [Timeframe]' Big Promise",
  "estimatedDuration": "e.g. 45-60 min or 14 min VSL",
  "sections": [
    {{
      "id": "hook_promise | origin_story | secret_1 | secret_2 | secret_3 | transition | close",
      "name": "Section display title",
      "duration": "e.g. 0:00 - 5:00",
      "goal": "Psychological job of this section",
      "falseBeliefBroken": "Exact false belief shattered here (or empty string if N/A)",
      "slideVisual": "Concrete slide headline / visual proof / demo cue",
      "script": "Full, speakable word-for-word script for this section."
    }}
  ],
  "offerStack": {{
    "transitionScript": "Word-for-word pivot from teaching into the Offer Stack.",
    "items": [
      {{
        "name": "Deliverable / Bonus Name",
        "modalityTier": "S-Tier | A-Tier | B-Tier | C-Tier",
        "perceivedValue": "$X,XXX",
        "benefit": "Specific transformation or objection solved by this deliverable."
      }}
    ],
    "totalPerceivedValue": "$XX,XXX",
    "offerPrice": "$X,XXX",
    "guarantee": "Specific risk-reversal guarantee",
    "urgency": "Ethical real urgency / scarcity mechanism",
    "cta": "Exact step-by-step call to action"
  }},
  "objectionHandlers": [
    {{
      "objection": "Exact customer objection verbatim",
      "reframe": "Sharp 2-4 sentence spoken answer that dissolves the objection."
    }}
  ],
  "fullMarkdown": ""
}}"""
        engine, raw = call_llm_json(prompt, provider=provider, timeout=180)

        clean_sections = []
        for idx, sec in enumerate(raw.get("sections") if isinstance(raw.get("sections"), list) else [], 1):
            if not isinstance(sec, dict):
                continue
            clean_sections.append({
                "id": str(sec.get("id") or f"section_{idx}").strip(),
                "name": str(sec.get("name") or f"Section {idx}").strip(),
                "duration": str(sec.get("duration") or "").strip(),
                "goal": str(sec.get("goal") or "").strip(),
                "falseBeliefBroken": str(sec.get("falseBeliefBroken") or "").strip(),
                "slideVisual": str(sec.get("slideVisual") or "").strip(),
                "script": str(sec.get("script") or "").strip(),
            })

        stack_in = raw.get("offerStack") if isinstance(raw.get("offerStack"), dict) else {}
        stack_items = []
        for it in (stack_in.get("items") if isinstance(stack_in.get("items"), list) else []):
            if not isinstance(it, dict):
                continue
            stack_items.append({
                "name": str(it.get("name") or "Deliverable").strip(),
                "modalityTier": str(it.get("modalityTier") or "A-Tier").strip(),
                "perceivedValue": str(it.get("perceivedValue") or "").strip(),
                "benefit": str(it.get("benefit") or "").strip(),
            })

        clean_objs = []
        for obj in (raw.get("objectionHandlers") if isinstance(raw.get("objectionHandlers"), list) else []):
            if not isinstance(obj, dict):
                continue
            q = str(obj.get("objection") or "").strip()
            a = str(obj.get("reframe") or "").strip()
            if q or a:
                clean_objs.append({"objection": q, "reframe": a})

        result = {
            "engine": engine,
            "toolType": "presentation",
            "format": fmt,
            "title": str(raw.get("title") or f"{fmt}: {topic or targets['offerName']}").strip(),
            "subtitle": str(raw.get("subtitle") or "").strip(),
            "bigPromise": str(raw.get("bigPromise") or "").strip(),
            "targetAvatar": targets["avatarName"],
            "targetOffer": targets["offerName"],
            "estimatedDuration": str(raw.get("estimatedDuration") or "").strip(),
            "sections": clean_sections,
            "offerStack": {
                "transitionScript": str(stack_in.get("transitionScript") or "").strip(),
                "items": stack_items,
                "totalPerceivedValue": str(stack_in.get("totalPerceivedValue") or "").strip(),
                "offerPrice": str(stack_in.get("offerPrice") or "").strip(),
                "guarantee": str(stack_in.get("guarantee") or "").strip(),
                "urgency": str(stack_in.get("urgency") or "").strip(),
                "cta": str(stack_in.get("cta") or "").strip(),
            },
            "objectionHandlers": clean_objs,
        }
        result["fullMarkdown"] = str(raw.get("fullMarkdown") or "").strip() or _build_presentation_markdown(result)
        return result

    if tt == "email":
        fmt = (p.get("format") or "Story Broadcast").strip()
        is_sequence = "sequence" in fmt.lower() or "3-day" in fmt.lower() or "soap-opera" in fmt.lower()
        seq_note = (
            "Generate a complete 3-Day Soap-Opera Sequence (Day 1: High-Drama Open Loop & Origin Tension; "
            "Day 2: Epiphany, Enemy Callout & Proprietary Mechanism; Day 3: Proof, Transformation & Direct Offer Close). "
            "Populate the `emails` array with all 3 complete emails AND put Day 1 in the top-level fields."
            if is_sequence
            else "Generate ONE complete, ready-to-send email (also place it as the single item inside `emails`)."
        )
        prompt = f"""You are an elite direct-response email copywriter writing strictly in the workspace's Founder Persona voice.
Write high-open, high-click, personality-driven email copy with crisp rhythm, zero corporate fluff, natural 7 Magnetism Elements, and an unmistakable CTA.

{_WHITE_LABEL_RULE}

EMAIL BRIEF:
- Format: {fmt} (Story Broadcast | Daily Soap-Opera Sequence (3-Day) | Problem → Agitate → Mechanism | Contrarian Rant / Enemy Callout | Case Study Proof | Direct Offer / Cart Close)
- Topic / Angle: {topic or "High-converting story broadcast for core offer"}
- Storytelling Format: {story_fmt or "Personality Story → Mechanism Bridge → CTA"}
- Custom Instructions: {custom or "None"}
- Sequence Requirement: {seq_note}

{target_focus}

WORKSPACE BRAIN:
{brain_block}

Return ONLY ONE valid JSON object with this EXACT schema:
{{
  "title": "Internal campaign / email title",
  "subjectLines": [
    "Option 1: Curiosity / story-driven high-open subject line",
    "Option 2: Contrarian / pattern-interrupt subject line",
    "Option 3: Direct benefit / specificity subject line"
  ],
  "previewText": "Punchy 45-90 char inbox preview text that completes the subject hook.",
  "body": "Full ready-to-send email body with short readable paragraphs and natural spoken cadence.",
  "psCta": "Sharp P.S. reinforcing urgency/benefit and clear link CTA.",
  "emails": [
    {{
      "day": "Day 1: Title (or Single Broadcast)",
      "subjectLines": ["Subject 1", "Subject 2", "Subject 3"],
      "previewText": "Inbox preview text",
      "body": "Full ready-to-send email body",
      "psCta": "P.S. CTA line"
    }}
  ],
  "fullMarkdown": ""
}}"""
        engine, raw = call_llm_json(prompt, provider=provider, timeout=160)

        raw_emails = raw.get("emails") if isinstance(raw.get("emails"), list) else []
        clean_emails = []
        for idx, em in enumerate(raw_emails[:5], 1):
            if not isinstance(em, dict):
                continue
            subs = [str(s).strip() for s in (em.get("subjectLines") or []) if str(s).strip()][:3]
            clean_emails.append({
                "day": str(em.get("day") or f"Email {idx}").strip(),
                "subjectLines": subs,
                "previewText": str(em.get("previewText") or "").strip(),
                "body": str(em.get("body") or "").strip(),
                "psCta": str(em.get("psCta") or "").strip(),
            })

        top_subs = [str(s).strip() for s in (raw.get("subjectLines") or []) if str(s).strip()][:3]
        if not top_subs and clean_emails:
            top_subs = clean_emails[0]["subjectLines"]

        top_preview = str(raw.get("previewText") or "").strip() or (clean_emails[0]["previewText"] if clean_emails else "")
        top_body = str(raw.get("body") or "").strip() or (clean_emails[0]["body"] if clean_emails else "")
        top_ps = str(raw.get("psCta") or "").strip() or (clean_emails[0]["psCta"] if clean_emails else "")

        if not clean_emails and top_body:
            clean_emails = [{
                "day": fmt,
                "subjectLines": top_subs,
                "previewText": top_preview,
                "body": top_body,
                "psCta": top_ps,
            }]

        result = {
            "engine": engine,
            "toolType": "email",
            "format": fmt,
            "title": str(raw.get("title") or f"{fmt}: {topic or targets['offerName']}").strip(),
            "targetAvatar": targets["avatarName"],
            "targetOffer": targets["offerName"],
            "subjectLines": top_subs,
            "previewText": top_preview,
            "body": top_body,
            "psCta": top_ps,
            "emails": clean_emails,
        }
        result["fullMarkdown"] = str(raw.get("fullMarkdown") or "").strip() or _build_email_markdown(result)
        return result

    if tt == "social":
        platform = (p.get("platform") or "Instagram Reel").strip()
        s_fmt = story_fmt or "Epiphany Bridge"
        own_hooks = targets.get("accountHooks") or []
        if own_hooks:
            hooks_block = "\n".join(f"- [{h['angle']}] {h['hook']}" for h in own_hooks[:12])
        else:
            hooks_block = "(No saved brand Account Hooks yet — craft 100% original hooks derived strictly from this workspace's Founder Persona, Enemy, Dogma, and Stories.)"

        prompt = f"""You are an elite social content strategist & scriptwriter combining Video Breakdown Architecture with this workspace's Founder Persona.
Build a complete, platform-native social script/post for {platform} using the `{s_fmt}` storytelling format.

{_WHITE_LABEL_RULE}

CRITICAL HOOK OWNERSHIP RULE:
Pull and adapt opening hooks STRICTLY from this workspace's OWN Account Hooks below and its own Founder Persona/Stories/Enemy. Do NOT mix in generic third-party swipe templates unless explicitly asked in Custom Instructions.

WORKSPACE'S OWN ACCOUNT HOOKS:
{hooks_block}

SOCIAL CONTENT BRIEF:
- Platform: {platform} (Instagram Reel | YouTube Short | YouTube Long-Form | TikTok | Facebook Reel / Post | LinkedIn / X Thread)
- Storytelling Format: {s_fmt} (Epiphany Bridge | Hero's Journey | Us vs Them Polarization | Contrarian Myth-Buster | Before → Mechanism → After Case Study | Trap / Mistake Diagnosis | Rapid-Fire Listicle | Origin Parable)
- Topic / Angle: {topic or "High-conviction signature insight for target avatar"}
- Custom Instructions: {custom or "None"}

{target_focus}

WORKSPACE BRAIN:
{brain_block}

Return ONLY ONE valid JSON object with this EXACT schema:
{{
  "title": "Punchy content title",
  "estimatedDuration": "e.g. 0:55 or 8 min video or 7-post thread",
  "hookOptions": [
    {{
      "angle": "Origin | Contrarian | Case Study | Enemy | Curiosity | Offer Tease",
      "hook": "Exact opening line ready to speak or post.",
      "visualCue": "Exact 0-3s visual action, framing, or on-screen text cue.",
      "sourceHookUsed": "Name/snippet of workspace Account Hook adapted, or 'Original from Founder Persona'"
    }}
  ],
  "beats": [
    {{
      "label": "Specific named beat (e.g. '01 Hook', '02 Context Anchor', '03 Conflict / Enemy', '04 Mechanism / Proof', '05 Payoff & CTA')",
      "timeRange": "0:00 - 0:04 (or Post 1 / Section 1 for threads)",
      "script": "Exact spoken line or post copy for this beat.",
      "visualCue": "Specific visual, B-roll, camera movement, or graphic cue."
    }}
  ],
  "fullScript": "Complete continuous copy-ready script or post/thread.",
  "caption": "Platform-native caption with crisp spacing and subtle CTA.",
  "visualCues": ["3-5 high-impact visual/editing/on-screen text cues for production."],
  "cta": "Clear, low-friction call to action aligned with the target offer.",
  "fullMarkdown": ""
}}"""
        engine, raw = call_llm_json(prompt, provider=provider, timeout=160)

        clean_hooks = []
        for h in (raw.get("hookOptions") if isinstance(raw.get("hookOptions"), list) else [])[:5]:
            if isinstance(h, dict):
                hk = str(h.get("hook") or h.get("text") or "").strip()
                if hk:
                    clean_hooks.append({
                        "angle": str(h.get("angle") or "Brand Hook").strip(),
                        "hook": hk,
                        "visualCue": str(h.get("visualCue") or "").strip(),
                        "sourceHookUsed": str(h.get("sourceHookUsed") or "Founder Persona").strip(),
                    })
            elif isinstance(h, str) and h.strip():
                clean_hooks.append({
                    "angle": "Brand Hook",
                    "hook": h.strip(),
                    "visualCue": "",
                    "sourceHookUsed": "Founder Persona",
                })

        clean_beats = []
        for idx, b in enumerate(raw.get("beats") if isinstance(raw.get("beats"), list) else [], 1):
            if not isinstance(b, dict):
                continue
            clean_beats.append({
                "label": str(b.get("label") or f"Beat {idx}").strip(),
                "timeRange": str(b.get("timeRange") or "").strip(),
                "script": str(b.get("script") or b.get("text") or "").strip(),
                "visualCue": str(b.get("visualCue") or "").strip(),
            })

        full_script = str(raw.get("fullScript") or "").strip()
        if not full_script and clean_beats:
            full_script = "\n\n".join(
                f"[{b['label']}{(' ' + b['timeRange']) if b['timeRange'] else ''}]\n{b['script']}"
                for b in clean_beats if b["script"]
            )

        result = {
            "engine": engine,
            "toolType": "social",
            "platform": platform,
            "storytellingFormat": s_fmt,
            "title": str(raw.get("title") or f"{platform}: {topic or s_fmt}").strip(),
            "targetAvatar": targets["avatarName"],
            "targetOffer": targets["offerName"],
            "estimatedDuration": str(raw.get("estimatedDuration") or "").strip(),
            "hookOptions": clean_hooks,
            "beats": clean_beats,
            "fullScript": full_script,
            "caption": str(raw.get("caption") or "").strip(),
            "visualCues": [str(x).strip() for x in (raw.get("visualCues") or []) if str(x).strip()][:8],
            "cta": str(raw.get("cta") or "").strip(),
        }
        result["fullMarkdown"] = str(raw.get("fullMarkdown") or "").strip() or _build_social_markdown(result)
        return result

    if tt == "generate_persona":
        brief = (p.get("brief") or topic or "").strip()
        founder_name = (p.get("founderName") or "").strip()
        niche = (p.get("niche") or "").strip()
        prompt = f"""You are a master brand positioning strategist & Founder Persona architect.
From the brief and workspace context below, forge a COMPLETE, unmistakable, high-magnetism Founder Persona with Identity, Voice Variations, all 7 Magnetism Elements, Signature Magnetism Test, 5 Original Stories, and 8 Brand-Owned Account Hooks.
Be specific, vivid, polarizing where helpful, and immediately usable across presentations, emails, and social scripts. Zero generic cliches.

{_WHITE_LABEL_RULE}

USER BRIEF:
- Founder / Brand Name: {founder_name or "Active Workspace Founder"}
- Niche / Market: {niche or "Infer from brief & workspace"}
- Brief: {brief or "Synthesize and upgrade the active workspace's Founder Persona"}
- Custom Instructions: {custom or "None"}

EXISTING WORKSPACE BRAIN (build on & sharpen what's already here):
{brain_block}

Return ONLY ONE valid JSON object with this EXACT schema:
{{
  "persona": {{
    "archetype": "Memorable founder archetype (e.g. 'The Reluctant Systems Architect', 'The Stern-but-Loving Operator')",
    "superheroIdentity": "Signature superhero/alter-ego title",
    "mightyTheme": "1 crisp unforgettable motto / battle cry (4-10 words)",
    "identity": "2-3 sentence sharp positioning bio & point of view",
    "standFor": "What this founder fiercely champions",
    "standAgainst": "The specific named Enemy / broken status quo they attack",
    "writingStyle": "Concrete cadence, vocabulary, and tone rules",
    "voices": [
      {{
        "name": "Voice mode name (e.g. 'Punchy Short-Form', 'Story Email', 'Keynote Authority', 'Contrarian Rant')",
        "tone": "3-5 descriptive tone words",
        "usage": "When to deploy this voice",
        "sampleLine": "1 authentic example sentence in this voice"
      }}
    ],
    "sevenElements": {{
      "origin": "Founder's defining origin turning point",
      "parables": "Signature teaching metaphor or repeatable analogy",
      "miracles": "Concrete breakthrough proof points / transformations",
      "insiderLanguage": "3-5 coined terms / proprietary mechanism names",
      "dogma": "Non-negotiable operating rules the brand lives by",
      "enemies": "Named industry villains, traps, or bad advice",
      "flaws": "Relatable human imperfections/quirks that build trust"
    }},
    "jamesBondTest": "2-3 unmistakable signature markers that make this founder instantly recognizable even if their name were removed",
    "stories": [
      {{
        "title": "Memorable story title",
        "type": "Origin | Epiphany | Client Miracle | Hard Lesson | Enemy Clash",
        "hook": "Opening 1-sentence story hook",
        "summary": "3-4 sentence arc (setup -> wall -> turn -> result)",
        "lesson": "Core takeaway linked to the brand's Mighty Theme",
        "useCase": "Best format to deploy this story (Webinar / Email / Reel)"
      }}
    ],
    "accountHooks": [
      {{
        "angle": "Origin | Contrarian | Case Study | Enemy | Curiosity | Offer Tease",
        "hook": "Exact brand-owned opening line",
        "visualCue": "0-3s visual framing / text cue",
        "storyLink": "Which story or Magnetism Element this hook opens"
      }}
    ]
  }}
}}

Ensure `voices` has 3-4 items, `stories` has EXACTLY 5 original stories, and `accountHooks` has EXACTLY 8 brand-owned hooks."""
        engine, raw = call_llm_json(prompt, provider=provider, timeout=180)
        pin = raw.get("persona") if isinstance(raw.get("persona"), dict) else raw

        raw_seven = pin.get("sevenElements") if isinstance(pin.get("sevenElements"), dict) else {}
        clean_seven = {
            k: str(raw_seven.get(k) or "").strip()
            for k in ("origin", "parables", "miracles", "insiderLanguage", "dogma", "enemies", "flaws")
        }

        clean_voices = []
        for v in (pin.get("voices") if isinstance(pin.get("voices"), list) else [])[:5]:
            if isinstance(v, dict):
                clean_voices.append({
                    "name": str(v.get("name") or "Voice").strip(),
                    "tone": str(v.get("tone") or "").strip(),
                    "usage": str(v.get("usage") or v.get("description") or "").strip(),
                    "sampleLine": str(v.get("sampleLine") or "").strip(),
                })
            elif isinstance(v, str) and v.strip():
                clean_voices.append({"name": v.strip(), "tone": "", "usage": "", "sampleLine": ""})

        clean_stories = []
        for s in (pin.get("stories") if isinstance(pin.get("stories"), list) else [])[:7]:
            if not isinstance(s, dict):
                continue
            clean_stories.append({
                "title": str(s.get("title") or "Story").strip(),
                "type": str(s.get("type") or "Origin").strip(),
                "hook": str(s.get("hook") or "").strip(),
                "summary": str(s.get("summary") or s.get("content") or "").strip(),
                "lesson": str(s.get("lesson") or "").strip(),
                "useCase": str(s.get("useCase") or "").strip(),
            })

        clean_hooks = []
        for h in (pin.get("accountHooks") if isinstance(pin.get("accountHooks"), list) else [])[:10]:
            if isinstance(h, dict):
                hk = str(h.get("hook") or h.get("text") or "").strip()
                if hk:
                    clean_hooks.append({
                        "angle": str(h.get("angle") or "Brand Hook").strip(),
                        "hook": hk,
                        "visualCue": str(h.get("visualCue") or "").strip(),
                        "storyLink": str(h.get("storyLink") or "").strip(),
                    })
            elif isinstance(h, str) and h.strip():
                clean_hooks.append({"angle": "Brand Hook", "hook": h.strip(), "visualCue": "", "storyLink": ""})

        persona_out = {
            "archetype": str(pin.get("archetype") or "").strip(),
            "superheroIdentity": str(pin.get("superheroIdentity") or pin.get("superhero") or "").strip(),
            "mightyTheme": str(pin.get("mightyTheme") or "").strip(),
            "identity": str(pin.get("identity") or "").strip(),
            "standFor": str(pin.get("standFor") or "").strip(),
            "standAgainst": str(pin.get("standAgainst") or "").strip(),
            "writingStyle": str(pin.get("writingStyle") or "").strip(),
            "voices": clean_voices,
            "sevenElements": clean_seven,
            "jamesBondTest": _as_text(pin.get("jamesBondTest")),
            "stories": clean_stories,
            "accountHooks": clean_hooks,
        }
        return {
            "engine": engine,
            "toolType": "generate_persona",
            "persona": persona_out,
            "fullMarkdown": _build_persona_markdown(persona_out),
        }

    if tt == "generate_avatar":
        brief = (p.get("brief") or topic or "").strip()
        av_name = (p.get("name") or p.get("avatarName") or "").strip()
        niche = (p.get("niche") or "").strip()
        prompt = f"""You are an elite consumer psychologist and direct-response market researcher.
Create a deeply vivid, razor-sharp Customer Avatar dossier that feels like you read the buyer's private diary. Avoid generic fluff — use concrete day-in-the-life details, exact objections, real buying triggers, watering holes, and verbatim quotes they actually say.

{_WHITE_LABEL_RULE}

AVATAR BRIEF:
- Name / Label: {av_name or "Create a memorable archetype name"}
- Niche / Market: {niche or "Infer from brief & workspace"}
- Brief: {brief or "Build the highest-leverage ideal buyer for this workspace"}
- Custom Instructions: {custom or "None"}

WORKSPACE BRAIN:
{brain_block}

Return ONLY ONE valid JSON object with this EXACT schema:
{{
  "avatar": {{
    "name": "Memorable avatar name & role (e.g. 'Overloaded Agency Founder Alex')",
    "tagline": "1-line snapshot of where they are right now",
    "demographics": "Age range, business/career stage, revenue/income band, team size, context",
    "dailyLife": "Vivid 3-4 sentence picture of a typical frustrating Tuesday for them",
    "pain": "Deepest surface + emotional + financial pains keeping them awake at 2am",
    "desires": "Concrete 90-day tangible outcomes AND deeper status/freedom desires",
    "objections": ["5 exact skeptical objections they raise before buying"],
    "buyingTriggers": ["4 specific breaking-point events that make them buy NOW"],
    "wateringHoles": ["5 exact places they hang out, watch, read, or follow"],
    "verbatimLanguage": ["6 exact raw quotes/phrases they type into Google or tell a friend"],
    "customNotes": "Strategic messaging notes on how to win their trust fastest and what turns them off immediately"
  }}
}}"""
        engine, raw = call_llm_json(prompt, provider=provider, timeout=150)
        ain = raw.get("avatar") if isinstance(raw.get("avatar"), dict) else raw

        def _str_list(val):
            if isinstance(val, list):
                return [str(x).strip() for x in val if str(x).strip()]
            s = _as_text(val)
            return [s] if s else []

        avatar_out = {
            "name": str(ain.get("name") or av_name or "Ideal Customer Avatar").strip(),
            "tagline": str(ain.get("tagline") or "").strip(),
            "demographics": _as_text(ain.get("demographics")),
            "dailyLife": _as_text(ain.get("dailyLife")),
            "pain": _as_text(ain.get("pain")),
            "desires": _as_text(ain.get("desires")),
            "objections": _str_list(ain.get("objections"))[:8],
            "buyingTriggers": _str_list(ain.get("buyingTriggers"))[:8],
            "wateringHoles": _str_list(ain.get("wateringHoles"))[:8],
            "verbatimLanguage": _str_list(ain.get("verbatimLanguage"))[:10],
            "customNotes": _as_text(ain.get("customNotes")),
        }
        return {
            "engine": engine,
            "toolType": "generate_avatar",
            "avatar": avatar_out,
            "fullMarkdown": _build_avatar_markdown(avatar_out),
        }

    if tt == "generate_hooks":
        prompt = f"""You are a master short-form & direct-response hook architect crafting 100% original, brand-owned Account Hooks for this active workspace.
Generate EXACTLY 10 scroll-stopping Account Hooks (10-22 words each, punchy, spoken-natural, ZERO generic filler) distributed across ALL 6 required angles:
- Origin
- Contrarian
- Case Study
- Enemy
- Curiosity
- Offer Tease

Every hook must feel unmistakably owned by THIS workspace's Founder Persona, Insider Language, Stories, Enemy, and Offer — never generic internet templates.

{_WHITE_LABEL_RULE}

HOOK GENERATION BRIEF:
- Focus Topic / Campaign: {topic or "Core brand pillars & flagship offer"}
- Custom Instructions: {custom or "None"}

{target_focus}

WORKSPACE BRAIN:
{brain_block}

Return ONLY ONE valid JSON object with this EXACT schema:
{{
  "hooks": [
    {{
      "angle": "One of: Origin | Contrarian | Case Study | Enemy | Curiosity | Offer Tease",
      "hook": "Exact spoken/written opening hook line",
      "visualCue": "Concrete 0-3s visual action or on-screen text cue",
      "bestPlatform": "Instagram Reel | YouTube Short | TikTok | YouTube Long-Form | LinkedIn / X | Email Subject",
      "whyItWorks": "1 crisp sentence on the psychological tension this hook triggers"
    }}
  ]
}}"""
        engine, raw = call_llm_json(prompt, provider=provider, timeout=150)
        valid_angles = {"Origin", "Contrarian", "Case Study", "Enemy", "Curiosity", "Offer Tease"}
        angle_map = {a.lower(): a for a in valid_angles}
        clean_hooks = []
        for h in (raw.get("hooks") if isinstance(raw.get("hooks"), list) else [])[:12]:
            if isinstance(h, dict):
                hk = str(h.get("hook") or h.get("text") or "").strip()
                if not hk:
                    continue
                raw_ang = str(h.get("angle") or h.get("category") or "Curiosity").strip()
                norm_ang = angle_map.get(raw_ang.lower(), raw_ang or "Curiosity")
                clean_hooks.append({
                    "angle": norm_ang,
                    "hook": hk,
                    "visualCue": str(h.get("visualCue") or "").strip(),
                    "bestPlatform": str(h.get("bestPlatform") or "Instagram Reel").strip(),
                    "whyItWorks": str(h.get("whyItWorks") or "").strip(),
                })
            elif isinstance(h, str) and h.strip():
                clean_hooks.append({
                    "angle": "Curiosity",
                    "hook": h.strip(),
                    "visualCue": "",
                    "bestPlatform": "Instagram Reel",
                    "whyItWorks": "",
                })
        return {
            "engine": engine,
            "toolType": "generate_hooks",
            "hooks": clean_hooks,
            "fullMarkdown": _build_hooks_markdown(clean_hooks, topic=topic),
        }

    raise ValueError(
        f"Unknown arsenal tool_type '{tool_type}'. Expected one of: "
        "presentation, email, social, generate_persona, generate_avatar, generate_hooks."
    )


# ──────────────────── PERSISTING UPGRADED BREAKDOWNS ────────────────────

def _default_workspace_from_config(workspace_id="aisimple"):
    if CONFIG_FILE.exists():
        try:
            cfg = json.loads(CONFIG_FILE.read_text())
            for ws in cfg.get("workspaces") or []:
                if ws.get("id") == workspace_id:
                    return ws
        except json.JSONDecodeError:
            pass
    # Fallback minimal AI Simple brief
    return {
        "id": "aisimple",
        "name": "AI Simple",
        "tagline": "AI workflows, automation & high-leverage founder systems",
        "offer": {
            "name": "AI Simple Accelerator & Done-With-You Systems",
            "audience": "Founders, operators & agencies ($30K-$500K/mo)",
            "transformation": "Replace 15-20 hrs/wk of manual busywork with reliable AI agent workflows in 30 days",
            "mechanism": "The AI Simple Operating Stack (3-layer prompt + workflow + distribution blueprint)",
        },
        "character": {
            "archetype": "The Stern but Loving Parent",
            "superhero": "The Systems Architect (Iron Operator)",
            "mightyTheme": "Simplicity Scales. Complexity Kills.",
            "standFor": "Practical AI systems that make money or buy back hours this week",
            "standAgainst": "Hype AI gurus, bloated 47-node demos that break, vanity prompts without revenue",
            "elements": {
                "insiderLanguage": "The AI Simple Stack, Leverage Audit, Prompt Slop, One-Click Ops",
                "dogma": "If an AI workflow takes longer to maintain than to run, kill it.",
            },
            "profits": {
                "pain": "Drowning in repetitive content, ops, and client fulfillment while competitors ship 5x faster",
                "frustration": "Every AI tutorial is either a surface-level toy or an unmaintainable nerd science project",
                "dreams": "A lean, automated business machine that ships world-class content and closes deals daily",
            },
            "writingStyle": "Direct, punchy, anti-fluff, zero throat-clearing. Concrete numbers + sharp contrast.",
        },
    }


def _find_and_update_reel(short_code, breakdown_obj):
    """Locate short_code in data/*_posts.json, data/socials/*.json, or config.json['singleVideos'] and persist breakdown."""
    # 1. Creator data files
    if DATA.exists():
        for p in sorted(DATA.glob("*_posts.json")):
            try:
                doc = json.loads(p.read_text())
            except json.JSONDecodeError:
                continue
            items = doc.get("items") if isinstance(doc, dict) else None
            if not isinstance(items, list):
                continue
            for item in items:
                if item.get("shortCode") == short_code or item.get("id") == short_code:
                    item["breakdown"] = breakdown_obj
                    write_json(p, doc)
                    return str(p)

        # 2. Synced multi-platform social files
        soc_dir = DATA / "socials"
        if soc_dir.exists():
            for p in sorted(soc_dir.glob("*.json")):
                try:
                    doc = json.loads(p.read_text())
                except json.JSONDecodeError:
                    continue
                items = doc.get("items") if isinstance(doc, dict) else None
                if not isinstance(items, list):
                    continue
                for item in items:
                    if item.get("shortCode") == short_code or item.get("id") == short_code:
                        item["breakdown"] = breakdown_obj
                        write_json(p, doc)
                        return str(p)

    # 3. Single videos in config.json
    if CONFIG_FILE.exists():
        try:
            cfg = json.loads(CONFIG_FILE.read_text())
            for item in cfg.get("singleVideos") or []:
                if item.get("shortCode") == short_code or item.get("id") == short_code:
                    item["breakdown"] = breakdown_obj
                    write_json(CONFIG_FILE, cfg)
                    return str(CONFIG_FILE)
        except json.JSONDecodeError:
            pass
    return None


def _load_reel_by_code(short_code):
    """Load raw reel item + creator median ratio if found on disk."""
    if DATA.exists():
        for p in sorted(DATA.glob("*_posts.json")):
            try:
                doc = json.loads(p.read_text())
            except json.JSONDecodeError:
                continue
            items = doc.get("items") if isinstance(doc, dict) else []
            plays = sorted([int(i.get("videoPlayCount") or i.get("plays") or 0) for i in items if (i.get("videoPlayCount") or i.get("plays"))])
            med = plays[len(plays) // 2] if plays else 1
            handle = p.name.replace("_posts.json", "")
            for item in items:
                if item.get("shortCode") == short_code or item.get("id") == short_code:
                    vp = int(item.get("videoPlayCount") or item.get("plays") or 0)
                    return {
                        "shortCode": short_code,
                        "creator_username": item.get("ownerUsername") or handle,
                        "platform": item.get("platform") or "instagram",
                        "plays": vp,
                        "likes": item.get("likesCount") or item.get("likes") or 0,
                        "comments": item.get("commentsCount") or item.get("comments") or 0,
                        "duration": item.get("videoDuration") or item.get("duration") or 0,
                        "ratio": round(vp / med, 1) if med else 1.0,
                        "transcript": item.get("transcript") or "",
                        "caption": item.get("caption") or "",
                        "existingBreakdown": item.get("breakdown"),
                    }
        soc_dir = DATA / "socials"
        if soc_dir.exists():
            for p in sorted(soc_dir.glob("*.json")):
                try:
                    doc = json.loads(p.read_text())
                except json.JSONDecodeError:
                    continue
                for item in doc.get("items") or []:
                    if item.get("shortCode") == short_code or item.get("id") == short_code:
                        return {
                            "shortCode": short_code,
                            "creator_username": item.get("creator_username") or doc.get("handle") or "creator",
                            "platform": item.get("platform") or doc.get("platform") or "youtube",
                            "plays": item.get("plays") or 0,
                            "likes": item.get("likes") or 0,
                            "comments": item.get("comments") or 0,
                            "duration": item.get("duration") or 0,
                            "ratio": item.get("ratio") or 1.0,
                            "transcript": item.get("transcript") or "",
                            "caption": item.get("caption") or item.get("title") or "",
                            "existingBreakdown": item.get("breakdown"),
                        }
    if CONFIG_FILE.exists():
        try:
            cfg = json.loads(CONFIG_FILE.read_text())
            for item in cfg.get("singleVideos") or []:
                if item.get("shortCode") == short_code or item.get("id") == short_code:
                    return item
        except json.JSONDecodeError:
            pass
    return None


def upgrade_reel(short_code, provider="auto", workspace_profile=None, reel_override=None):
    reel = reel_override or _load_reel_by_code(short_code)
    if not reel:
        raise ValueError(f"Reel '{short_code}' not found.")
    ws = workspace_profile or _default_workspace_from_config()
    breakdown = generate_video_breakdown(reel, workspace_profile=ws, provider=provider)
    saved_to = _find_and_update_reel(short_code, breakdown)
    return {"shortCode": short_code, "breakdown": breakdown, "savedTo": saved_to}


def batch_upgrade_top(limit=5, provider="auto", force=False, workspace_id="aisimple"):
    """Upgrade the top N outliers across data/*_posts.json that don't yet have an LLM breakdown."""
    candidates = []
    if DATA.exists():
        for p in sorted(DATA.glob("*_posts.json")):
            try:
                doc = json.loads(p.read_text())
            except json.JSONDecodeError:
                continue
            items = doc.get("items") if isinstance(doc, dict) else []
            plays_list = sorted([int(i.get("videoPlayCount") or 0) for i in items if i.get("videoPlayCount")])
            if not plays_list:
                continue
            med = plays_list[len(plays_list) // 2] or 1
            handle = p.name.replace("_posts.json", "")
            for item in items:
                sc = item.get("shortCode")
                if not sc:
                    continue
                b = item.get("breakdown") or {}
                if not force and b.get("engine") in {"claude", "codex", "anthropic_api", "openai_api"}:
                    continue
                vp = int(item.get("videoPlayCount") or 0)
                ratio = round(vp / med, 1)
                has_tr = bool((item.get("transcript") or "").strip())
                candidates.append((has_tr, ratio, vp, sc, handle))
    candidates.sort(key=lambda x: (x[0], x[1], x[2]), reverse=True)
    ws = _default_workspace_from_config(workspace_id)
    results = []
    for has_tr, ratio, vp, sc, handle in candidates[:limit]:
        print(f"→ Analyzing @{handle} ({sc}, {ratio}×, {vp:,} plays) via {provider}...", flush=True)
        try:
            res = upgrade_reel(sc, provider=provider, workspace_profile=ws)
            results.append({"shortCode": sc, "handle": handle, "ratio": ratio, "ok": True, "engine": res["breakdown"]["engine"]})
            print(f"  ✓ Upgraded ({res['breakdown']['engine']})", flush=True)
        except Exception as e:
            results.append({"shortCode": sc, "handle": handle, "ratio": ratio, "ok": False, "error": str(e)})
            print(f"  ✗ Failed: {e}", flush=True)
    return results


def main():
    ap = argparse.ArgumentParser(description="Outlier Lab Local AI Breakdown Engine (Claude / Codex)")
    ap.add_argument("--status", action="store_true", help="Print detected AI providers")
    ap.add_argument("--shortcode", help="Upgrade a single reel by shortCode")
    ap.add_argument("--top", type=int, default=0, help="Batch-upgrade top N outliers")
    ap.add_argument("--provider", default="auto", choices=["auto", "claude", "codex", "anthropic_api", "openai_api"])
    ap.add_argument("--force", action="store_true", help="Re-analyze even if already AI-upgraded")
    ap.add_argument("--build", action="store_true", help="Run build.py after upgrading")
    args = ap.parse_args()

    if args.status:
        print(json.dumps(detect_providers(), indent=2))
        return
    if args.shortcode:
        res = upgrade_reel(args.shortcode, provider=args.provider)
        print(json.dumps({"ok": True, "shortCode": res["shortCode"], "engine": res["breakdown"]["engine"], "savedTo": res["savedTo"]}, indent=2))
    elif args.top > 0:
        results = batch_upgrade_top(limit=args.top, provider=args.provider, force=args.force)
        print(json.dumps({"upgraded": sum(1 for r in results if r["ok"]), "results": results}, indent=2))
    else:
        ap.print_help()
        return

    if args.build:
        subprocess.run([sys.executable, str(ROOT / "build.py")], cwd=str(ROOT), check=True)


if __name__ == "__main__":
    main()
