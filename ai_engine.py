#!/usr/bin/env python3
"""
Outlier Lab — Local AI Engine (Claude CLI, Codex CLI, optional API fallback).

Produces Sandcastles-grade (and deeper, with Dan Kennedy Magnetic Story Selling)
per-video breakdowns and 4-step scripts using your local `claude` or `codex` CLI
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
    # Strip markdown code fences if present
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.S)
    if fenced:
        try:
            return json.loads(fenced.group(1))
        except json.JSONDecodeError:
            pass
    # Direct parse
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
    except json.JSONDecodeError:
        pass
    # Scan from first '{' to last '}'
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


def _run_anthropic_api(prompt, timeout=90):
    key = _env_var("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY is not configured.")
    body = json.dumps({
        "model": os.environ.get("OUTLIER_CLAUDE_MODEL", "claude-sonnet-4-20250514"),
        "max_tokens": 3200,
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


# ──────────────────── SANDCASTLES + DAN KENNEDY PROMPT ────────────────────

def _workspace_brief(ws):
    ws = ws or {}
    ch = ws.get("character") or {}
    off = ws.get("offer") or {}
    el = ch.get("elements") or {}
    pr = ch.get("profits") or {}
    return f"""Active Workspace: {ws.get('name', 'AI Simple')}
Tagline: {ws.get('tagline', '')}
Core Offer: {off.get('name', '')} | Audience: {off.get('audience', '')} | Transformation: {off.get('transformation', '')} | Mechanism: {off.get('mechanism', '')}
Dan Kennedy Archetype: {ch.get('archetype', '')} | Superhero Identity: {ch.get('superhero', '')} | Mighty Theme: {ch.get('mightyTheme', '')}
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
1. Kallaway / Sandcastles Video Breakdown precision (Hook Alignment, Mad-Lib Formula, Beat-by-Beat Retention Architecture, Idea Contrast Mechanism, Storytelling Format & Scriptwriting Tactics, Visual Layout Blueprint), AND
2. Dan Kennedy's Magnetic Story Selling 6-Dimension Content Audit & 7 Magnetic Elements (Character vs Plot, Polarization, Magnification, Regis Context Anchor, Core Story Advancement, Character Deficit Score 0–12).

Analyze THIS specific video deeply. Be concrete, sharp, non-generic, and cite exact phrases from the transcript/caption. Never output filler.

VIDEO DATA:
- Creator: @{creator} ({platform})
- Outlier Multiple: {ratio}x creator median | Views: {plays} | Likes: {likes} | Comments: {comments} | Duration: {duration}s
- Spoken Transcript:
\"\"\"{transcript or '[No spoken transcript captured — analyze from caption + context]'}\"\"\"
- Caption:
\"\"\"{caption[:1600]}\"\"\"

ACTIVE WORKSPACE CHARACTER & OFFER (use this to write hyper-specific remixes & characterRewrite):
{_workspace_brief(workspace_profile)}

Return ONLY ONE valid JSON object (no markdown, no explanation outside JSON) with this EXACT schema:
{{
  "summary": "2-3 razor-sharp sentences explaining the video's thesis, retention engine, and why it hit {ratio}x median.",
  "topic": "Specific 2-4 word topic cluster (e.g. 'Claude AI Prompt Engineering', 'Short-Form Hook Psychology', 'Meta Ads Creative Testing')",
  "beatsOverview": "1 crisp Sandcastles-style sentence summarizing the structural progression of the video.",
  "beats": [
    {{
      "label": "Specific named beat (e.g. 'Scientific Hook', 'Step 1: The Context', 'Contrarian Snapback', 'Synthesis & CTA')",
      "timeRange": "0:00 – 0:04",
      "text": "Exact portion of the transcript belonging to this beat.",
      "why": "1 concise sentence explaining the retention/psychological job this beat performs."
    }}
  ],
  "idea": {{
    "ideaSeed": "Concise 1-line core premise of this video.",
    "uniqueAngle": "The strategic reframing that makes this feel fresh instead of generic advice.",
    "commonBelief": "The default status-quo belief the audience walks in holding.",
    "contrarianReality": "The sharper contrarian truth or tension the creator introduces.",
    "evidence": [
      "3 to 4 concrete proof points, numbers, demos, or examples actually used in this video."
    ],
    "remixes": [
      "Option 1: Specific ready-to-film video premise + opening hook tailored to the active workspace's Offer, Enemy, and Character.",
      "Option 2: A second distinct angle using the active workspace's Insider Language or Mechanism.",
      "Option 3: A contrarian polarization angle attacking the workspace's named Enemy."
    ]
  }},
  "hook": {{
    "category": "One of: Trap Mistake | Comparison | Tutorial | Secret Reveal Breakdown | Case Study | Personal Experience | Question | List | Problem | Authority",
    "formula": "Exact fill-in-the-blank Mad-Lib template parameterized from this video's real opening line (using [Bracketed Slots]).",
    "spokenHook": "Exact opening 1-2 sentences spoken in the first 3-5 seconds.",
    "visualHook": "Best concrete visual framing / motion / text-overlay hook for seconds 0-3.",
    "alignmentAssessment": "Sharp Sandcastles-style diagnosis of spoken + visual + on-screen text alignment AND one specific tweak to make it hit even harder."
  }},
  "format": {{
    "category": "One of: Breakdown Explainer | Common Trap Mistake | A Vs B Comparison | Listicle | Case Study | Personal Learning Epiphany | Problem Solution | Yap / Hot Take",
    "description": "1-sentence definition of how this structural archetype works.",
    "analysis": "2-3 sentences on why THIS specific video's narrative flow keeps viewers watching and what to copy when modeling it.",
    "tactics": [
      "3 to 5 specific Sandcastles-style scriptwriting craft tactics actually observed in this script (e.g. 'Direct Problem Callout Then Rapid-Fire Proof', 'Named Tool Specificity Anchor', 'Contrarian Snapback Before Payoff')."
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
    "characterRewrite": "2-3 concrete spoken sentences showing how the active workspace's Character (using their Superhero Identity, Enemy, and Dogma) would open and reframe this exact outlier."
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
    """Power Sandcastles 4-step Script Builder & Draft Fixer via Claude/Codex."""
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
        prompt = f"""You are a Kallaway-grade viral researcher + Dan Kennedy direct-response strategist.
Build Step 2 (Research Brief) for a short-form video.
TOPIC: {topic}
CUSTOM DIRECTION: {custom}
{src_block}
WORKSPACE CHARACTER & OFFER:
{ws_block}

Return ONLY valid JSON:
{{
  "executiveSummary": "2-3 punchy sentences framing the core thesis and audience tension.",
  "howToEngage": ["3 concrete psychological engagement triggers for seconds 0-15"],
  "surprisingFacts": ["3 sharp, concrete proof/contrast facts or realizations"],
  "contrastMoments": ["3 crisp Common Belief vs Contrarian Reality contrasts"]
}}"""
    elif step == "hooks":
        prompt = f"""You are Kallaway's Hook Genius + Dan Kennedy.
Generate 6 elite, film-ready short-form opening hooks (12-24 words each, ZERO generic fluff, strong visual + spoken alignment, injecting the workspace's Character/Enemy where sharp).
TOPIC: {topic}
CUSTOM DIRECTION: {custom}
RESEARCH SUMMARY: {research.get('executiveSummary', '')}
{src_block}
WORKSPACE CHARACTER & OFFER:
{ws_block}

Return ONLY valid JSON:
{{
  "hooks": [
    {{
      "style": "Trap Mistake | Secret Reveal Breakdown | Case Study | Comparison | Authority | Personal Experience",
      "inspiredBy": "@creator or Dan Kennedy Pattern",
      "text": "Exact spoken opening line ready to read to camera.",
      "visualCue": "Exact 0-3s visual action or on-screen text."
    }}
  ]
}}"""
    elif step == "script":
        prompt = f"""You are an elite short-form viral scriptwriter combining Kallaway retention architecture with Dan Kennedy Magnetic Story Selling.
Write Step 4: a complete, high-retention 45-75 second spoken short-form script.
Include clear beat headers ([0:00 HOOK], [0:04 REGIS CONTEXT ANCHOR], [0:10 ENEMY & CONTRAST], [0:22 MECHANISM & PROOF], [0:42 PAYOFF & CTA]) plus brief [VISUAL: ...] cues, written strictly in the workspace's voice, injecting at least 3 of their Dan Kennedy Magnetic Elements naturally.
TOPIC: {topic}
CHOSEN HOOK: {selected_hook}
CUSTOM DIRECTION: {custom}
RESEARCH BRIEF: {json.dumps(research)[:1200]}
{src_block}
WORKSPACE CHARACTER & OFFER:
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
        prompt = f"""You are Kallaway + Dan Kennedy ruthlessly upgrading a rough short-form script draft.
Keep the creator's core idea, eliminate throat-clearing, sharpen seconds 0-3, add a Contrarian Snapback, inject the workspace's Dan Kennedy Character/Enemy/Dogma, and tighten pacing to high-retention short-form cadence.
DRAFT TO FIX:
\"\"\"{existing_draft}\"\"\"
WORKSPACE CHARACTER & OFFER:
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
