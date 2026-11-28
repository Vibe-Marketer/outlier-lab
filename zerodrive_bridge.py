#!/usr/bin/env python3
"""
Outlier Lab — Agentic ZeroDrive Brain & File Sync Bridge.

Provides resilient workspace brain & document persistence across:
  1. Local mirror (`data/zerodrive_mirror/<workspace_id>/`) — always available offline.
  2. Local ZeroDrive CLI (`zd` / `zerodrive`) — pushes/pulls to `OutlierLab/<workspace_id>/...`
     in the ZeroDrive cloud vault via `zd cp` / `zd ls` / `zd cat`.
  3. Optional Finder mount & optional hosted ZeroDrive API URL/key (`ZERODRIVE_API_URL`,
     `ZERODRIVE_API_KEY` stored in gitignored `.env`).

Pure Python stdlib — zero third-party pip dependencies.
"""

import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from storage import file_lock, update_env, write_json

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
MIRROR_ROOT = DATA / "zerodrive_mirror"
CONFIG_FILE = ROOT / "config.json"
CONFIG_LOCK_FILE = ROOT / ".cache" / "config.lock"
ENV_FILE = ROOT / ".env"

DEFAULT_VAULT_ROOT = "OutlierLab"
MAX_READ_BYTES = 1024 * 1024  # 1 MiB safeguard for read_document


# ───────────────────────── env & config helpers ─────────────────────────


def _utc_now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _load_env_map():
    env = {}
    if ENV_FILE.exists():
        try:
            for line in ENV_FILE.read_text(encoding="utf-8", errors="replace").splitlines():
                s = line.strip()
                if not s or s.startswith("#") or "=" not in s:
                    continue
                k, v = s.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
        except OSError:
            pass
    return env


def _env_var(name):
    return (os.environ.get(name) or _load_env_map().get(name, "")).strip()


def _scrub_secret(text):
    """Ensure ZERODRIVE_API_KEY can never leak into warnings, logs, or responses."""
    out = str(text or "")
    secret = _env_var("ZERODRIVE_API_KEY")
    if secret and secret in out:
        out = out.replace(secret, "[REDACTED]")
    return out


def _load_config():
    if not CONFIG_FILE.exists():
        return {}
    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _zerodrive_config():
    cfg = _load_config().get("zerodrive")
    return cfg if isinstance(cfg, dict) else {}


def _save_zerodrive_config(patch):
    """Atomically merge non-secret fields into config.json['zerodrive']."""
    safe_patch = {
        k: v
        for k, v in (patch or {}).items()
        if k.lower() not in {"apikey", "api_key", "token", "secret", "password"}
    }
    with file_lock(CONFIG_LOCK_FILE):
        cfg = _load_config()
        zd_cfg = cfg.get("zerodrive")
        if not isinstance(zd_cfg, dict):
            zd_cfg = {}
        zd_cfg.update(safe_patch)
        cfg["zerodrive"] = zd_cfg
        write_json(CONFIG_FILE, cfg)
        return dict(zd_cfg)


def _get_vault_root():
    raw = _zerodrive_config().get("vaultRoot") or DEFAULT_VAULT_ROOT
    return _sanitize_vault_root(raw)


def _get_api_url():
    return (_zerodrive_config().get("apiUrl") or _env_var("ZERODRIVE_API_URL")).strip().rstrip("/")


def _is_api_configured():
    return bool(_get_api_url() and _env_var("ZERODRIVE_API_KEY"))


# ───────────────────────── path sanitization & safety ─────────────────────────


def _sanitize_segment(raw, default="default", max_len=64):
    text = str(raw or "").strip()
    text = text.replace("\x00", "").replace("\\", "/").strip("/")
    if "/" in text:
        text = text.split("/")[-1]
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", text).strip(".-")
    if not cleaned or cleaned in {".", ".."}:
        return default
    return cleaned[:max_len]


def _sanitize_filename(raw, default="document.md", max_len=120):
    text = str(raw or "").strip().replace("\x00", "").replace("\\", "/")
    if "/" in text:
        text = text.split("/")[-1]
    cleaned = re.sub(r"[^A-Za-z0-9._ -]+", "-", text).strip()
    cleaned = re.sub(r"\s+", "-", cleaned).strip(".-")
    if not cleaned or cleaned in {".", ".."}:
        return default
    return cleaned[:max_len]


def _sanitize_vault_root(raw):
    text = str(raw or "").strip().replace("\x00", "").replace("\\", "/").strip("/")
    if not text:
        return DEFAULT_VAULT_ROOT
    parts = []
    for seg in text.split("/"):
        s = seg.strip()
        if not s or s in {".", ".."}:
            continue
        clean = re.sub(r"[^A-Za-z0-9._-]+", "-", s).strip(".-")
        if clean:
            parts.append(clean)
    return "/".join(parts) if parts else DEFAULT_VAULT_ROOT


def _normalize_relative_doc_path(raw_path, vault_root=None):
    """
    Validate and normalize a document path against traversal attacks.
    Returns (mirror_rel_path, vault_rel_path) or raises ValueError.
    """
    if not isinstance(raw_path, str):
        raise ValueError("Path must be a string.")
    text = raw_path.strip()
    if not text or "\x00" in text or "\\" in text:
        raise ValueError("Invalid document path.")
    if text.startswith("~") or text.startswith("/"):
        raise ValueError("Absolute paths are not permitted.")

    vroot = _sanitize_vault_root(vault_root or _get_vault_root())

    # Strip recognized safe prefixes
    for prefix in ("vault:", "zd://"):
        if text.startswith(prefix):
            text = text[len(prefix):]
    text = text.lstrip("/")

    mirror_prefix = "data/zerodrive_mirror/"
    if text.startswith(mirror_prefix):
        text = text[len(mirror_prefix):]
    elif text.startswith(vroot + "/"):
        text = text[len(vroot) + 1:]

    raw_parts = [p for p in text.split("/") if p != ""]
    if not raw_parts:
        raise ValueError("Empty document path.")

    safe_parts = []
    for part in raw_parts:
        if part in {".", ".."} or ".." in part.split("/") or part.startswith("-"):
            raise ValueError("Path traversal is not allowed.")
        if any(ord(ch) < 32 for ch in part):
            raise ValueError("Control characters are not allowed in path.")
        safe_parts.append(part)

    mirror_rel = "/".join(safe_parts)
    mirror_base = MIRROR_ROOT.resolve()
    candidate = (mirror_base / mirror_rel).resolve()

    # Enforce strict containment inside MIRROR_ROOT
    try:
        candidate.relative_to(mirror_base)
    except ValueError:
        raise ValueError("Path escapes the ZeroDrive mirror root.")

    if candidate == mirror_base:
        raise ValueError("Path must reference a file, not the root directory.")

    vault_rel = f"{vroot}/{mirror_rel}"
    return mirror_rel, vault_rel, candidate


def _atomic_write_text(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_name = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            delete=False,
        ) as stream:
            tmp_name = stream.name
            stream.write(content)
        os.replace(tmp_name, path)
    finally:
        if tmp_name and os.path.exists(tmp_name):
            try:
                os.unlink(tmp_name)
            except OSError:
                pass


# ───────────────────────── ZeroDrive CLI & mount helpers ─────────────────────────


def _find_cli():
    candidates = [
        shutil.which("zd"),
        shutil.which("zerodrive"),
        "/Users/admin/.local/bin/zerodrive",
        "/Users/admin/.local/bin/zd",
        str(Path.home() / ".local" / "bin" / "zerodrive"),
        str(Path.home() / ".local" / "bin" / "zd"),
    ]
    for c in candidates:
        if c and os.path.isfile(c) and os.access(c, os.X_OK):
            return os.path.realpath(c) if Path(c).is_symlink() else c
    return ""


def _run_cli(args, cli_path="", timeout=20):
    binary = cli_path or _find_cli()
    if not binary:
        return False, "", "ZeroDrive CLI (zd / zerodrive) not found.", -1
    cmd = [binary, "--no-color", *args]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return proc.returncode == 0, proc.stdout or "", proc.stderr or "", proc.returncode
    except subprocess.TimeoutExpired:
        return False, "", f"ZeroDrive command timed out after {timeout}s.", -2
    except OSError as exc:
        return False, "", f"Failed to execute ZeroDrive CLI: {exc}", -3


def _inspect_cli_status(cli_path):
    """Parse `zd --no-color status` for Finder mount state and vault prefix."""
    info = {"mounted": False, "mountPath": "", "vaultPrefix": "", "statusOk": False, "rawError": ""}
    if not cli_path:
        return info

    ok, stdout, stderr, _ = _run_cli(["status"], cli_path=cli_path, timeout=8)
    combined = (stdout + "\n" + stderr).strip()
    info["statusOk"] = ok
    if not ok and not stdout:
        info["rawError"] = _scrub_secret(combined[:240])
        return info

    mount_match = re.search(r"Finder Mount:\s*(.+)", stdout)
    if mount_match:
        val = mount_match.group(1).strip().lower()
        info["mounted"] = ("mounted" in val) and ("not mounted" not in val)

    path_match = re.search(r"Mount Path:\s*(.+)", stdout)
    if path_match:
        info["mountPath"] = path_match.group(1).strip()

    prefix_match = re.search(r"Vault Prefix:\s*(.+)", stdout)
    if prefix_match:
        info["vaultPrefix"] = prefix_match.group(1).strip()

    if not info["mountPath"]:
        default_mount = Path.home() / ".zerodrive" / "My Drive"
        if default_mount.exists():
            info["mountPath"] = str(default_mount)

    return info


def _extract_cli_error(stdout, stderr):
    """Detect errors emitted either on stderr or as JSON `{"error": ...}` on stdout."""
    for blob in (stderr, stdout):
        txt = (blob or "").strip()
        if not txt:
            continue
        if txt.startswith("{"):
            try:
                parsed = json.loads(txt)
                if isinstance(parsed, dict) and parsed.get("error"):
                    return _scrub_secret(str(parsed["error"]).strip())
            except json.JSONDecodeError:
                pass
        if "CRITICAL:" in txt or "secret_access_key not found" in txt or "Error:" in txt:
            return _scrub_secret(txt.splitlines()[0][:240])
    return ""


def _probe_cloud_vault(cli_path):
    """Lightweight check to see if ZeroDrive CLI can talk to the cloud vault."""
    if not cli_path:
        return False, "ZeroDrive CLI is not installed."
    ok, stdout, stderr, _ = _run_cli(["ls", "--json"], cli_path=cli_path, timeout=8)
    err = _extract_cli_error(stdout, stderr)
    if err:
        return False, err
    if not ok:
        return False, _scrub_secret((stderr or stdout or "ZeroDrive vault check failed.").strip()[:240])
    return True, ""


def _copy_to_cloud(local_file, vault_rel_path, cli_path=""):
    """Copy a local file into ZeroDrive vault via `zd cp` (or Finder mount fallback)."""
    binary = cli_path or _find_cli()
    if binary:
        ok, stdout, stderr, _ = _run_cli(
            ["cp", str(local_file), f"vault:{vault_rel_path}"],
            cli_path=binary,
            timeout=25,
        )
        err = _extract_cli_error(stdout, stderr)
        if ok and not err:
            return True, ""
        reason = err or _scrub_secret((stderr or stdout or "ZeroDrive cp failed.").strip()[:240])
        return False, reason

    return False, "ZeroDrive CLI is not installed; saved to local mirror only."


def _count_mirror_files(workspace_id=""):
    base = MIRROR_ROOT / _sanitize_segment(workspace_id) if workspace_id else MIRROR_ROOT
    if not base.exists():
        return 0
    total = 0
    for p in base.rglob("*"):
        if p.is_file() and not p.name.startswith("."):
            total += 1
    return total


# ───────────────────────── markdown renderers ─────────────────────────


def _fmt_value(val, indent=0):
    pad = "  " * indent
    if val is None or val == "":
        return f"{pad}_Not specified yet._"
    if isinstance(val, str):
        return "\n".join(f"{pad}{line}" for line in val.strip().splitlines()) or f"{pad}_Not specified yet._"
    if isinstance(val, (int, float, bool)):
        return f"{pad}{val}"
    if isinstance(val, list):
        if not val:
            return f"{pad}_None yet._"
        lines = []
        for item in val:
            if isinstance(item, dict):
                title = (
                    item.get("name")
                    or item.get("title")
                    or item.get("label")
                    or item.get("id")
                    or "Item"
                )
                lines.append(f"{pad}- **{title}**")
                for k, v in item.items():
                    if k in {"name", "title", "label", "id"} or v in (None, "", [], {}):
                        continue
                    key_label = re.sub(r"([a-z])([A-Z])", r"\1 \2", str(k)).replace("_", " ").strip().title()
                    if isinstance(v, (dict, list)):
                        lines.append(f"{pad}  - **{key_label}:**")
                        lines.append(_fmt_value(v, indent=indent + 2))
                    else:
                        lines.append(f"{pad}  - **{key_label}:** {v}")
            else:
                lines.append(f"{pad}- {item}")
        return "\n".join(lines)
    if isinstance(val, dict):
        if not val:
            return f"{pad}_None yet._"
        lines = []
        for k, v in val.items():
            if v in (None, "", [], {}):
                continue
            key_label = re.sub(r"([a-z])([A-Z])", r"\1 \2", str(k)).replace("_", " ").strip().title()
            if isinstance(v, (dict, list)):
                lines.append(f"{pad}- **{key_label}:**")
                lines.append(_fmt_value(v, indent=indent + 1))
            else:
                lines.append(f"{pad}- **{key_label}:** {v}")
        return "\n".join(lines) if lines else f"{pad}_None yet._"
    return f"{pad}{val}"


def _pick(payload, *keys, default=None):
    if not isinstance(payload, dict):
        return default
    for k in keys:
        if k in payload and payload[k] not in (None, ""):
            return payload[k]
    return default


def _render_founder_persona_md(ws_id, ws_name, payload, synced_at):
    founder = _pick(payload, "founderPersona", "founder_persona", "founder", "persona", "brandVoice", "voice")
    lines = [
        f"# Founder Persona — {ws_name}",
        "",
        f"> Workspace: `{ws_id}` | Synced: `{synced_at}`",
        "",
    ]
    if isinstance(founder, dict):
        for k, v in founder.items():
            heading = re.sub(r"([a-z])([A-Z])", r"\1 \2", str(k)).replace("_", " ").strip().title()
            lines.append(f"## {heading}")
            lines.append("")
            lines.append(_fmt_value(v))
            lines.append("")
    elif founder:
        lines.append(_fmt_value(founder))
        lines.append("")
    else:
        # Pull top-level brand/niche fields if structured flat
        flat = {
            k: payload[k]
            for k in ("name", "brand", "niche", "positioning", "tone", "voice", "bio", "story", "ctaStyle", "mission")
            if isinstance(payload, dict) and payload.get(k) not in (None, "", [], {})
        }
        lines.append(_fmt_value(flat) if flat else "_No founder persona details saved yet._")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _render_customer_avatars_md(ws_id, ws_name, payload, synced_at):
    avatars = _pick(payload, "customerAvatars", "customer_avatars", "avatars", "icp", "audience", "targetAudience")
    lines = [
        f"# Customer Avatars — {ws_name}",
        "",
        f"> Workspace: `{ws_id}` | Synced: `{synced_at}`",
        "",
    ]
    if isinstance(avatars, list) and avatars:
        for idx, av in enumerate(avatars, start=1):
            if isinstance(av, dict):
                title = av.get("name") or av.get("title") or av.get("segment") or f"Avatar {idx}"
                lines.append(f"## {idx}. {title}")
                lines.append("")
                rest = {k: v for k, v in av.items() if k not in {"name", "title", "segment"}}
                lines.append(_fmt_value(rest))
                lines.append("")
            else:
                lines.append(f"- {av}")
    elif avatars:
        lines.append(_fmt_value(avatars))
        lines.append("")
    else:
        lines.append("_No customer avatars saved yet._")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _render_products_and_offers_md(ws_id, ws_name, payload, synced_at):
    offers = _pick(payload, "productsAndOffers", "products_and_offers", "offers", "products")
    lines = [
        f"# Products & Offers — {ws_name}",
        "",
        f"> Workspace: `{ws_id}` | Synced: `{synced_at}`",
        "",
    ]
    if isinstance(offers, list) and offers:
        for idx, item in enumerate(offers, start=1):
            if isinstance(item, dict):
                title = item.get("name") or item.get("title") or item.get("offer") or f"Offer {idx}"
                lines.append(f"## {idx}. {title}")
                lines.append("")
                rest = {k: v for k, v in item.items() if k not in {"name", "title", "offer"}}
                lines.append(_fmt_value(rest))
                lines.append("")
            else:
                lines.append(f"- {item}")
    elif offers:
        lines.append(_fmt_value(offers))
        lines.append("")
    else:
        lines.append("_No products or offers saved yet._")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _render_memories_md(ws_id, ws_name, payload, synced_at):
    memories = _pick(payload, "memories", "memory", "notes", "insights", "learnings")
    lines = [
        f"# Workspace Memories — {ws_name}",
        "",
        f"> Workspace: `{ws_id}` | Synced: `{synced_at}`",
        "",
    ]
    if isinstance(memories, list) and memories:
        for item in memories:
            if isinstance(item, dict):
                title = item.get("title") or item.get("topic") or item.get("category") or "Memory"
                body = item.get("content") or item.get("text") or item.get("note") or ""
                created = item.get("createdAt") or item.get("date") or ""
                header = f"## {title}" + (f" ({created})" if created else "")
                lines.append(header)
                lines.append("")
                if body:
                    lines.append(str(body).strip())
                    lines.append("")
                extra = {
                    k: v
                    for k, v in item.items()
                    if k not in {"title", "topic", "category", "content", "text", "note", "createdAt", "date"}
                    and v not in (None, "", [], {})
                }
                if extra:
                    lines.append(_fmt_value(extra))
                    lines.append("")
            else:
                lines.append(f"- {item}")
    elif memories:
        lines.append(_fmt_value(memories))
        lines.append("")
    else:
        lines.append("_No memories recorded yet._")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _render_asset_library_md(ws_id, ws_name, payload, synced_at):
    assets = _pick(payload, "assetLibrary", "asset_library", "assets", "resources", "links", "scripts")
    lines = [
        f"# Asset Library — {ws_name}",
        "",
        f"> Workspace: `{ws_id}` | Synced: `{synced_at}`",
        "",
    ]
    if isinstance(assets, list) and assets:
        for idx, item in enumerate(assets, start=1):
            if isinstance(item, dict):
                title = item.get("title") or item.get("name") or item.get("filename") or f"Asset {idx}"
                lines.append(f"## {idx}. {title}")
                lines.append("")
                rest = {k: v for k, v in item.items() if k not in {"title", "name", "filename"}}
                lines.append(_fmt_value(rest))
                lines.append("")
            else:
                lines.append(f"- {item}")
    elif assets:
        lines.append(_fmt_value(assets))
        lines.append("")
    else:
        lines.append("_No assets saved in library yet._")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


# ───────────────────────── public API ─────────────────────────


def status():
    """Return live ZeroDrive CLI, Finder mount, hosted API, and local mirror status."""
    zd_cfg = _zerodrive_config()
    vault_root = _get_vault_root()
    api_url = _get_api_url()
    api_configured = _is_api_configured()
    last_synced_at = str(zd_cfg.get("lastSyncedAt") or "")

    cli_path = _find_cli()
    cli_available = bool(cli_path)
    cli_info = _inspect_cli_status(cli_path) if cli_available else {
        "mounted": False,
        "mountPath": "",
        "vaultPrefix": "",
    }

    cloud_ok = False
    cloud_error = ""
    if cli_available:
        cloud_ok, cloud_error = _probe_cloud_vault(cli_path)

    mounted = bool(cli_info.get("mounted"))
    connected = bool(cloud_ok or mounted or api_configured)
    file_count = _count_mirror_files()

    if cloud_ok:
        message = f"Connected to ZeroDrive cloud vault ({vault_root})."
    elif mounted:
        message = f"Connected via ZeroDrive Finder mount ({cli_info.get('mountPath')})."
    elif api_configured:
        message = f"Connected via hosted ZeroDrive API ({api_url}). Local mirror active."
    elif cli_available:
        hint = f" ({cloud_error})" if cloud_error else ""
        message = f"ZeroDrive CLI detected, but cloud vault is not authenticated yet{hint}. Local mirror is active."
    else:
        message = "ZeroDrive CLI not installed. Local mirror is active for offline-safe sync."

    return {
        "connected": connected,
        "cliAvailable": cli_available,
        "cliPath": cli_path,
        "vaultRoot": vault_root,
        "apiConfigured": api_configured,
        "lastSyncedAt": last_synced_at,
        "fileCount": file_count,
        "message": _scrub_secret(message),
        "mounted": mounted,
        "mountPath": cli_info.get("mountPath") or "",
        "apiUrl": api_url,
        "mirrorPath": str(MIRROR_ROOT),
    }


def connect(vault_root="OutlierLab", api_url="", api_key=""):
    """Save ZeroDrive configuration (non-secret in config.json, secret key in .env) and return status()."""
    clean_root = _sanitize_vault_root(vault_root or DEFAULT_VAULT_ROOT)
    clean_url = str(api_url or "").strip().rstrip("/")
    clean_key = str(api_key or "").strip()

    patch = {
        "vaultRoot": clean_root,
        "updatedAt": _utc_now(),
    }
    if clean_url:
        patch["apiUrl"] = clean_url
        update_env(ENV_FILE, "ZERODRIVE_API_URL", clean_url)

    _save_zerodrive_config(patch)

    if clean_key:
        update_env(ENV_FILE, "ZERODRIVE_API_KEY", clean_key)

    return status()


def sync_workspace_brain(workspace_id, brain_payload):
    """
    Write structured JSON & human-readable Markdown brain files for a workspace to the
    local mirror AND push them to ZeroDrive (`<vaultRoot>/<workspace_id>/...`) when healthy.
    """
    ws_id = _sanitize_segment(workspace_id, default="default")
    payload = brain_payload if isinstance(brain_payload, dict) else {"raw": brain_payload}
    ws_name = str(
        _pick(payload, "workspaceName", "workspace_name", "name", "brandName", "brand") or ws_id
    ).strip()

    vault_root = _get_vault_root()
    synced_at = _utc_now()
    ws_mirror_dir = MIRROR_ROOT / ws_id
    ws_vault_dir = f"{vault_root}/{ws_id}"

    brain_doc = {
        "workspaceId": ws_id,
        "workspaceName": ws_name,
        "vaultPath": ws_vault_dir,
        "syncedAt": synced_at,
        "brain": payload,
    }

    rendered_files = [
        ("brain.json", json.dumps(brain_doc, indent=2, ensure_ascii=False) + "\n"),
        ("founder-persona.md", _render_founder_persona_md(ws_id, ws_name, payload, synced_at)),
        ("customer-avatars.md", _render_customer_avatars_md(ws_id, ws_name, payload, synced_at)),
        ("products-and-offers.md", _render_products_and_offers_md(ws_id, ws_name, payload, synced_at)),
        ("memories.md", _render_memories_md(ws_id, ws_name, payload, synced_at)),
        ("asset-library.md", _render_asset_library_md(ws_id, ws_name, payload, synced_at)),
    ]

    written = []
    try:
        ws_mirror_dir.mkdir(parents=True, exist_ok=True)
        for fname, text in rendered_files:
            target = ws_mirror_dir / fname
            _atomic_write_text(target, text)
            written.append((fname, target, target.stat().st_size))
    except OSError as exc:
        return {
            "ok": False,
            "syncedToCloud": False,
            "localPath": str(ws_mirror_dir),
            "vaultPath": ws_vault_dir,
            "files": [],
            "warning": f"Failed writing local mirror: {exc}",
        }

    cli_path = _find_cli()
    synced_to_cloud = False
    warning = ""
    cloud_results = {}

    if cli_path:
        all_ok = True
        for idx, (fname, local_file, _) in enumerate(written):
            vpath = f"{ws_vault_dir}/{fname}"
            ok, err = _copy_to_cloud(local_file, vpath, cli_path=cli_path)
            cloud_results[fname] = ok
            if not ok:
                all_ok = False
                warning = _scrub_secret(err or "ZeroDrive cloud copy failed; saved to local mirror.")
                # Short-circuit on first failure (e.g. offline or missing R2 key) so sync stays fast
                if idx == 0:
                    break
        synced_to_cloud = all_ok and len(cloud_results) == len(written)
    else:
        warning = "ZeroDrive CLI not installed; brain saved to local mirror."

    _save_zerodrive_config({"lastSyncedAt": synced_at})

    file_records = [
        {
            "name": fname,
            "path": f"{ws_id}/{fname}",
            "vaultPath": f"{ws_vault_dir}/{fname}",
            "size": size,
            "updatedAt": synced_at,
            "syncedToCloud": bool(cloud_results.get(fname, False)),
        }
        for fname, _, size in written
    ]

    return {
        "ok": True,
        "syncedToCloud": synced_to_cloud,
        "localPath": str(ws_mirror_dir),
        "vaultPath": ws_vault_dir,
        "files": file_records,
        "warning": warning,
    }


def save_document(workspace_id, category, filename, content):
    """
    Save any AI chat output, script, email, presentation, or memory doc to
    `<vaultRoot>/<workspace_id>/<category>/<filename>` (local mirror + ZeroDrive vault).
    """
    ws_id = _sanitize_segment(workspace_id, default="default")
    cat = _sanitize_segment(category, default="documents")
    fname = _sanitize_filename(filename, default="document.md")
    vault_root = _get_vault_root()
    synced_at = _utc_now()

    rel_path = f"{ws_id}/{cat}/{fname}"
    vault_path = f"{vault_root}/{rel_path}"
    local_file = MIRROR_ROOT / ws_id / cat / fname

    # Final containment verification
    try:
        local_file.resolve().relative_to(MIRROR_ROOT.resolve())
    except ValueError:
        return {
            "ok": False,
            "path": "",
            "vaultPath": "",
            "syncedToCloud": False,
            "warning": "Invalid target path.",
        }

    if isinstance(content, (dict, list)):
        body = json.dumps(content, indent=2, ensure_ascii=False) + "\n"
    else:
        body = str(content if content is not None else "")

    try:
        _atomic_write_text(local_file, body)
        size = local_file.stat().st_size
    except OSError as exc:
        return {
            "ok": False,
            "path": rel_path,
            "vaultPath": vault_path,
            "syncedToCloud": False,
            "warning": f"Failed writing local document: {exc}",
        }

    cli_path = _find_cli()
    synced_to_cloud = False
    warning = ""
    if cli_path:
        synced_to_cloud, err = _copy_to_cloud(local_file, vault_path, cli_path=cli_path)
        if not synced_to_cloud:
            warning = _scrub_secret(err or "Saved locally; cloud sync unavailable.")
    else:
        warning = "ZeroDrive CLI not installed; saved to local mirror."

    _save_zerodrive_config({"lastSyncedAt": synced_at})

    return {
        "ok": True,
        "path": rel_path,
        "vaultPath": vault_path,
        "syncedToCloud": synced_to_cloud,
        "localPath": str(local_file),
        "size": size,
        "updatedAt": synced_at,
        "warning": warning,
    }


def list_files(workspace_id=""):
    """List synced ZeroDrive / mirror files for a workspace (or all workspaces if omitted)."""
    ws_id = _sanitize_segment(workspace_id, default="") if str(workspace_id or "").strip() else ""
    vault_root = _get_vault_root()

    entries_by_path = {}
    base_dir = (MIRROR_ROOT / ws_id) if ws_id else MIRROR_ROOT

    if base_dir.exists():
        for fp in sorted(base_dir.rglob("*")):
            if not fp.is_file() or fp.name.startswith("."):
                continue
            try:
                rel = fp.relative_to(MIRROR_ROOT).as_posix()
                stat = fp.stat()
            except (OSError, ValueError):
                continue
            parts = rel.split("/")
            item_ws = parts[0] if parts else ws_id
            item_cat = parts[1] if len(parts) > 2 else "brain"
            updated = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(stat.st_mtime))
            entries_by_path[rel] = {
                "name": fp.name,
                "path": rel,
                "vaultPath": f"{vault_root}/{rel}",
                "workspaceId": item_ws,
                "category": item_cat,
                "size": stat.st_size,
                "updatedAt": updated,
                "source": "mirror",
                "syncedToCloud": False,
            }

    cli_path = _find_cli()
    cloud_checked = False
    warning = ""

    if cli_path:
        vault_target = f"{vault_root}/{ws_id}" if ws_id else vault_root
        ok, stdout, stderr, _ = _run_cli(["ls", "-R", "--json", vault_target], cli_path=cli_path, timeout=12)
        err = _extract_cli_error(stdout, stderr)
        if ok and not err and stdout.strip():
            try:
                cloud_items = json.loads(stdout)
                if isinstance(cloud_items, list):
                    cloud_checked = True
                    for item in cloud_items:
                        if not isinstance(item, dict) or item.get("IsDir"):
                            continue
                        raw_p = str(item.get("Path") or item.get("Name") or "").lstrip("/")
                        if not raw_p:
                            continue
                        rel = f"{ws_id}/{raw_p}" if ws_id else raw_p
                        if rel in entries_by_path:
                            entries_by_path[rel]["source"] = "both"
                            entries_by_path[rel]["syncedToCloud"] = True
                        else:
                            parts = rel.split("/")
                            entries_by_path[rel] = {
                                "name": Path(rel).name,
                                "path": rel,
                                "vaultPath": f"{vault_root}/{rel}",
                                "workspaceId": parts[0] if parts else ws_id,
                                "category": parts[1] if len(parts) > 2 else "brain",
                                "size": int(item.get("Size") or 0),
                                "updatedAt": str(item.get("ModTime") or ""),
                                "source": "cloud",
                                "syncedToCloud": True,
                            }
            except json.JSONDecodeError:
                warning = "Could not parse ZeroDrive cloud listing; showing local mirror."
        elif err and "directory not found" not in err.lower() and "not found" not in err.lower():
            warning = _scrub_secret(err)

    files = sorted(entries_by_path.values(), key=lambda x: x["path"])
    return {
        "ok": True,
        "workspaceId": ws_id,
        "vaultRoot": vault_root,
        "syncedToCloud": cloud_checked,
        "count": len(files),
        "files": files,
        "warning": warning,
    }


def read_document(path):
    """Safely read a document from local mirror or `zd cat` with strict path traversal protection."""
    vault_root = _get_vault_root()
    try:
        mirror_rel, vault_rel, candidate = _normalize_relative_doc_path(path, vault_root=vault_root)
    except ValueError as exc:
        return {
            "ok": False,
            "path": "",
            "vaultPath": "",
            "source": "",
            "content": "",
            "error": str(exc),
        }

    # Prefer local mirror (fast, zero latency, offline-safe)
    if candidate.is_file():
        try:
            # Verify symlink doesn't escape MIRROR_ROOT
            resolved = candidate.resolve(strict=True)
            resolved.relative_to(MIRROR_ROOT.resolve())
            size = resolved.stat().st_size
            if size > MAX_READ_BYTES:
                return {
                    "ok": False,
                    "path": mirror_rel,
                    "vaultPath": vault_rel,
                    "source": "mirror",
                    "content": "",
                    "error": f"File exceeds maximum readable size ({MAX_READ_BYTES} bytes).",
                }
            content = resolved.read_text(encoding="utf-8", errors="replace")
            updated = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(resolved.stat().st_mtime))
            return {
                "ok": True,
                "path": mirror_rel,
                "vaultPath": vault_rel,
                "source": "mirror",
                "content": content,
                "size": size,
                "updatedAt": updated,
            }
        except (OSError, ValueError) as exc:
            return {
                "ok": False,
                "path": mirror_rel,
                "vaultPath": vault_rel,
                "source": "mirror",
                "content": "",
                "error": f"Could not read local document: {exc}",
            }

    # Fallback to ZeroDrive cloud vault via `zd cat`
    cli_path = _find_cli()
    if cli_path:
        ok, stdout, stderr, _ = _run_cli(
            ["cat", "--bytes", f"0-{MAX_READ_BYTES}", vault_rel],
            cli_path=cli_path,
            timeout=15,
        )
        err = _extract_cli_error(stdout, stderr)
        if ok and not err:
            return {
                "ok": True,
                "path": mirror_rel,
                "vaultPath": vault_rel,
                "source": "cloud",
                "content": stdout,
                "size": len(stdout.encode("utf-8")),
                "updatedAt": "",
            }
        return {
            "ok": False,
            "path": mirror_rel,
            "vaultPath": vault_rel,
            "source": "cloud",
            "content": "",
            "error": _scrub_secret(err or (stderr or "Document not found in ZeroDrive vault.").strip()[:240]),
        }

    return {
        "ok": False,
        "path": mirror_rel,
        "vaultPath": vault_rel,
        "source": "",
        "content": "",
        "error": "Document not found in local mirror and ZeroDrive CLI is unavailable.",
    }
