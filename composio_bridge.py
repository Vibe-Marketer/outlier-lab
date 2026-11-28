#!/usr/bin/env python3
"""
Outlier Lab — Complete Composio Integration Bridge.

Talks directly to Composio REST API v3 (`https://backend.composio.dev/api/v3`) using
Python stdlib `urllib.request` with `x-api-key` auth, gracefully falling back to v2
endpoints when a v3 route returns HTTP 404.

Secrets (`COMPOSIO_API_KEY`) are persisted strictly in gitignored `.env` via
`storage.update_env` and are NEVER written to `config.json` or returned in responses.

Pure Python stdlib — zero third-party pip dependencies.
"""

import json
import os
import re
import shutil
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from storage import file_lock, update_env, write_json

ROOT = Path(__file__).resolve().parent
CONFIG_FILE = ROOT / "config.json"
CONFIG_LOCK_FILE = ROOT / ".cache" / "config.lock"
ENV_FILE = ROOT / ".env"

COMPOSIO_V3_BASE = "https://backend.composio.dev/api/v3"
COMPOSIO_V2_BASE = "https://backend.composio.dev/api/v2"
DEFAULT_USER_ID = "aisimple-default"
REQUEST_TIMEOUT = 20

POPULAR_TOOLKITS = [
    {
        "slug": "gmail",
        "name": "Gmail",
        "description": "Read, draft, search, label, and send emails through Google Gmail.",
        "category": "Communication",
        "authSchemes": ["OAUTH2"],
        "aliases": ["email", "google mail"],
        "popular": True,
        "source": "catalog",
    },
    {
        "slug": "notion",
        "name": "Notion",
        "description": "Search workspaces, create and update Notion pages, wikis, and databases.",
        "category": "Productivity",
        "authSchemes": ["OAUTH2"],
        "aliases": ["wiki", "docs", "notes"],
        "popular": True,
        "source": "catalog",
    },
    {
        "slug": "slack",
        "name": "Slack",
        "description": "Post channel messages, read threads, manage channels, and send team alerts.",
        "category": "Communication",
        "authSchemes": ["OAUTH2"],
        "aliases": ["chat", "messaging"],
        "popular": True,
        "source": "catalog",
    },
    {
        "slug": "googledrive",
        "name": "Google Drive",
        "description": "Upload, organize, search, share, and read files across Google Drive.",
        "category": "Storage",
        "authSchemes": ["OAUTH2"],
        "aliases": ["gdrive", "drive", "files"],
        "popular": True,
        "source": "catalog",
    },
    {
        "slug": "youtube",
        "name": "YouTube",
        "description": "Inspect channels, videos, playlists, analytics, and comments on YouTube.",
        "category": "Social & Video",
        "authSchemes": ["OAUTH2"],
        "aliases": ["yt", "video", "shorts"],
        "popular": True,
        "source": "catalog",
    },
    {
        "slug": "instagram",
        "name": "Instagram",
        "description": "Manage Instagram creator media, insights, comments, and publishing.",
        "category": "Social & Video",
        "authSchemes": ["OAUTH2"],
        "aliases": ["ig", "reels", "meta"],
        "popular": True,
        "source": "catalog",
    },
    {
        "slug": "metaads",
        "name": "Meta Ads",
        "description": "Query ad campaigns, ad sets, creatives, and performance metrics in Meta Ads.",
        "category": "Marketing",
        "authSchemes": ["OAUTH2"],
        "aliases": ["facebook ads", "meta", "ads"],
        "popular": True,
        "source": "catalog",
    },
    {
        "slug": "hubspot",
        "name": "HubSpot",
        "description": "Sync CRM contacts, companies, deals, pipelines, and marketing engagement.",
        "category": "CRM",
        "authSchemes": ["OAUTH2"],
        "aliases": ["crm", "leads", "sales"],
        "popular": True,
        "source": "catalog",
    },
    {
        "slug": "airtable",
        "name": "Airtable",
        "description": "Read, create, update, and query structured bases, tables, and content trackers.",
        "category": "Database",
        "authSchemes": ["OAUTH2"],
        "aliases": ["spreadsheet", "content calendar", "base"],
        "popular": True,
        "source": "catalog",
    },
    {
        "slug": "googlecalendar",
        "name": "Google Calendar",
        "description": "List events, check availability, and schedule or update calendar meetings.",
        "category": "Productivity",
        "authSchemes": ["OAUTH2"],
        "aliases": ["gcal", "calendar", "meetings"],
        "popular": True,
        "source": "catalog",
    },
    {
        "slug": "linear",
        "name": "Linear",
        "description": "Create and track issues, projects, cycles, and roadmap items in Linear.",
        "category": "Engineering",
        "authSchemes": ["OAUTH2"],
        "aliases": ["issues", "tasks", "tickets"],
        "popular": True,
        "source": "catalog",
    },
    {
        "slug": "github",
        "name": "GitHub",
        "description": "Inspect repositories, issues, pull requests, commits, and workflow runs.",
        "category": "Engineering",
        "authSchemes": ["OAUTH2"],
        "aliases": ["git", "code", "repos"],
        "popular": True,
        "source": "catalog",
    },
    {
        "slug": "stripe",
        "name": "Stripe",
        "description": "Inspect customers, subscriptions, invoices, payments, and revenue metrics.",
        "category": "Payments",
        "authSchemes": ["API_KEY", "OAUTH2"],
        "aliases": ["billing", "revenue", "payments"],
        "popular": True,
        "source": "catalog",
    },
    {
        "slug": "discord",
        "name": "Discord",
        "description": "Read community channels, post updates, and automate Discord workflows.",
        "category": "Communication",
        "authSchemes": ["OAUTH2"],
        "aliases": ["community", "chat"],
        "popular": True,
        "source": "catalog",
    },
    {
        "slug": "twitter",
        "name": "X",
        "description": "Publish posts and threads, monitor mentions, and inspect analytics on X.",
        "category": "Social & Video",
        "authSchemes": ["OAUTH2"],
        "aliases": ["x", "tweets", "social"],
        "popular": True,
        "source": "catalog",
    },
]


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


def _get_api_key():
    return _env_var("COMPOSIO_API_KEY")


def _scrub_secret(text):
    """Guarantee COMPOSIO_API_KEY never appears in returned messages or errors."""
    out = str(text or "")
    key = _get_api_key()
    if key and key in out:
        out = out.replace(key, "[REDACTED]")
    return out


def _load_config():
    if not CONFIG_FILE.exists():
        return {}
    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _composio_config():
    cfg = _load_config().get("composio")
    return cfg if isinstance(cfg, dict) else {}


def _save_composio_config(patch):
    """Atomically store non-secret Composio settings in config.json['composio']."""
    safe_patch = {
        k: v
        for k, v in (patch or {}).items()
        if k.lower() not in {"apikey", "api_key", "key", "token", "secret", "password"}
    }
    with file_lock(CONFIG_LOCK_FILE):
        cfg = _load_config()
        comp = cfg.get("composio")
        if not isinstance(comp, dict):
            comp = {}
        comp.update(safe_patch)
        cfg["composio"] = comp
        write_json(CONFIG_FILE, cfg)
        return dict(comp)


def _get_user_id():
    cfg_uid = str(_composio_config().get("userId") or "").strip()
    if cfg_uid:
        return cfg_uid
    env_uid = _env_var("COMPOSIO_USER_ID")
    if env_uid:
        return env_uid
    return DEFAULT_USER_ID


def _sanitize_slug(raw):
    text = str(raw or "").strip().lower()
    cleaned = re.sub(r"[^a-z0-9_-]+", "", text)
    return cleaned[:80]


def _clamp_limit(limit, default=30, maximum=100):
    try:
        val = int(limit)
    except (TypeError, ValueError):
        return default
    return max(1, min(val, maximum))


# ───────────────────────── HTTP client (v3 + v2 fallback) ─────────────────────────


class ComposioAPIError(RuntimeError):
    def __init__(self, message, status_code=0, details=None):
        super().__init__(_scrub_secret(message))
        self.status_code = status_code
        self.details = details


def _http_call(base_url, method, path, params=None, body=None, api_key="", timeout=REQUEST_TIMEOUT):
    key = (api_key or _get_api_key()).strip()
    if not key:
        raise ComposioAPIError("COMPOSIO_API_KEY is not configured.", status_code=401)

    url = base_url.rstrip("/") + "/" + path.lstrip("/")
    if params:
        clean_params = {k: v for k, v in params.items() if v not in (None, "")}
        if clean_params:
            url += "?" + urllib.parse.urlencode(clean_params, doseq=True)

    data_bytes = None
    headers = {
        "x-api-key": key,
        "Accept": "application/json",
        "User-Agent": "OutlierLab-ComposioBridge/1.0",
    }
    if body is not None:
        data_bytes = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method.upper())
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            if not raw.strip():
                return {}
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return {"raw": raw}
    except urllib.error.HTTPError as exc:
        err_body = ""
        parsed = None
        try:
            err_body = exc.read().decode("utf-8", errors="replace")
            parsed = json.loads(err_body)
        except Exception:
            pass
        detail_msg = ""
        if isinstance(parsed, dict):
            err_obj = parsed.get("error")
            if isinstance(err_obj, dict):
                detail_msg = err_obj.get("message") or err_obj.get("suggested_fix") or ""
            elif isinstance(err_obj, str):
                detail_msg = err_obj
            detail_msg = detail_msg or parsed.get("message") or parsed.get("detail") or ""
        msg = detail_msg or err_body[:240] or f"HTTP {exc.code} {exc.reason}"
        raise ComposioAPIError(_scrub_secret(msg), status_code=exc.code, details=parsed)
    except urllib.error.URLError as exc:
        raise ComposioAPIError(f"Could not reach Composio API: {exc.reason}", status_code=0)
    except TimeoutError:
        raise ComposioAPIError(f"Composio API request timed out after {timeout}s.", status_code=0)


def _request(method, v3_path, params=None, body=None, v2_path=None, v2_params=None, v2_body=None, api_key="", timeout=REQUEST_TIMEOUT):
    """Call Composio v3 API, transparently falling back to v2 if v3 returns 404."""
    try:
        return _http_call(
            COMPOSIO_V3_BASE,
            method,
            v3_path,
            params=params,
            body=body,
            api_key=api_key,
            timeout=timeout,
        )
    except ComposioAPIError as exc:
        if exc.status_code == 404 and v2_path:
            return _http_call(
                COMPOSIO_V2_BASE,
                method,
                v2_path,
                params=v2_params if v2_params is not None else params,
                body=v2_body if v2_body is not None else body,
                api_key=api_key,
                timeout=timeout,
            )
        raise


def _extract_items(payload):
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("items", "data", "results", "toolkits", "tools", "actions", "connectedAccounts"):
            val = payload.get(key)
            if isinstance(val, list):
                return val
    return []


# ───────────────────────── normalizers ─────────────────────────


def _filter_popular_catalog(search="", limit=30):
    q = str(search or "").strip().lower()
    items = []
    for tk in POPULAR_TOOLKITS:
        if q:
            haystack = " ".join(
                [
                    tk["slug"],
                    tk["name"],
                    tk["description"],
                    tk["category"],
                    *tk.get("aliases", []),
                ]
            ).lower()
            if q not in haystack:
                continue
        items.append({k: v for k, v in tk.items() if k != "aliases"})
    return items[:limit]


def _normalize_toolkit(raw):
    if not isinstance(raw, dict):
        return None
    slug = str(raw.get("slug") or raw.get("key") or raw.get("appId") or raw.get("name") or "").strip().lower()
    if not slug:
        return None
    meta = raw.get("meta") if isinstance(raw.get("meta"), dict) else {}
    categories = meta.get("categories") or raw.get("categories") or []
    category = ""
    if isinstance(categories, list) and categories:
        first = categories[0]
        category = first.get("name", "") if isinstance(first, dict) else str(first)
    elif isinstance(raw.get("category"), str):
        category = raw["category"]

    schemes = raw.get("auth_schemes") or raw.get("authSchemes") or raw.get("composio_managed_auth_schemes") or []
    if isinstance(schemes, list):
        schemes = [s.get("mode", str(s)) if isinstance(s, dict) else str(s) for s in schemes]
    else:
        schemes = []

    return {
        "slug": slug,
        "name": str(raw.get("name") or slug.title()),
        "description": str(meta.get("description") or raw.get("description") or "")[:280],
        "category": category or "Integration",
        "logo": str(meta.get("logo") or raw.get("logo") or ""),
        "authSchemes": schemes,
        "toolsCount": int(meta.get("tools_count") or raw.get("tools_count") or 0),
        "source": "composio",
    }


def _normalize_connection(raw, fallback_user_id=""):
    if not isinstance(raw, dict):
        return None
    toolkit = raw.get("toolkit") if isinstance(raw.get("toolkit"), dict) else {}
    auth_cfg = raw.get("auth_config") if isinstance(raw.get("auth_config"), dict) else {}
    slug = str(
        toolkit.get("slug")
        or raw.get("toolkit_slug")
        or raw.get("appName")
        or raw.get("appUniqueId")
        or ""
    ).strip().lower()
    return {
        "id": str(raw.get("id") or raw.get("nanoid") or ""),
        "toolkitSlug": slug,
        "toolkitName": str(toolkit.get("name") or raw.get("appName") or slug.title()),
        "status": str(raw.get("status") or "UNKNOWN").upper(),
        "userId": str(raw.get("user_id") or raw.get("entityId") or fallback_user_id),
        "authConfigId": str(auth_cfg.get("id") or raw.get("auth_config_id") or raw.get("integrationId") or ""),
        "createdAt": str(raw.get("created_at") or raw.get("createdAt") or ""),
        "updatedAt": str(raw.get("updated_at") or raw.get("updatedAt") or ""),
    }


def _normalize_tool(raw, default_toolkit=""):
    if not isinstance(raw, dict):
        return None
    slug = str(raw.get("slug") or raw.get("name") or raw.get("enum") or "").strip()
    if not slug:
        return None
    toolkit = raw.get("toolkit") if isinstance(raw.get("toolkit"), dict) else {}
    tk_slug = str(
        toolkit.get("slug")
        or raw.get("toolkit_slug")
        or raw.get("appName")
        or default_toolkit
        or ""
    ).strip().lower()
    params = raw.get("input_parameters") or raw.get("parameters") or {}
    return {
        "slug": slug,
        "name": str(raw.get("displayName") or raw.get("display_name") or raw.get("name") or slug),
        "description": str(raw.get("description") or "")[:400],
        "toolkitSlug": tk_slug,
        "version": str(raw.get("version") or ""),
        "inputParameters": params if isinstance(params, dict) else {},
    }


def _find_or_create_auth_config(toolkit_slug):
    """Resolve an auth_config_id for a toolkit in Composio v3 (reusing existing or creating managed)."""
    existing = _request(
        "GET",
        "/auth_configs",
        params={"toolkit_slug": toolkit_slug, "limit": 10},
    )
    for item in _extract_items(existing):
        if not isinstance(item, dict):
            continue
        cfg_id = item.get("id")
        if cfg_id and str(item.get("status") or "ENABLED").upper() != "DISABLED":
            return str(cfg_id)

    created = _request(
        "POST",
        "/auth_configs",
        body={
            "toolkit": {"slug": toolkit_slug},
            "auth_config": {"type": "use_composio_managed_auth"},
        },
    )
    if isinstance(created, dict):
        if created.get("id"):
            return str(created["id"])
        nested = created.get("auth_config")
        if isinstance(nested, dict) and nested.get("id"):
            return str(nested["id"])
    raise ComposioAPIError(f"Could not resolve or create an auth config for '{toolkit_slug}'.")


# ───────────────────────── public API ─────────────────────────


def status():
    """Return Composio configuration status, active userId, CLI availability, and popular toolkits."""
    return {
        "configured": bool(_get_api_key()),
        "userId": _get_user_id(),
        "cliAvailable": bool(shutil.which("composio")),
        "popularToolkits": _filter_popular_catalog(limit=len(POPULAR_TOOLKITS)),
    }


def configure(api_key, user_id=""):
    """
    Save COMPOSIO_API_KEY to gitignored `.env` (if non-empty) and user_id to `config.json['composio']`,
    verify credentials against Composio API, and return summary status without leaking the key.
    """
    clean_key = str(api_key or "").strip()
    clean_uid = str(user_id or "").strip()

    if clean_key:
        update_env(ENV_FILE, "COMPOSIO_API_KEY", clean_key)

    effective_uid = clean_uid or _get_user_id()
    _save_composio_config({"userId": effective_uid, "updatedAt": _utc_now()})

    active_key = clean_key or _get_api_key()
    if not active_key:
        return {
            "ok": False,
            "configured": False,
            "userId": effective_uid,
            "connectedCount": 0,
            "message": "No Composio API key provided or saved in .env.",
        }

    # Verify against Composio API (try connected_accounts first so we also get connectedCount)
    try:
        res = _request(
            "GET",
            "/connected_accounts",
            params={"user_ids": effective_uid, "limit": 50},
            v2_path="/connectedAccounts",
            v2_params={"user_uuid": effective_uid},
            api_key=active_key,
            timeout=15,
        )
        items = _extract_items(res)
        active_conns = [
            c for c in items
            if isinstance(c, dict) and str(c.get("status") or "").upper() in {"ACTIVE", "CONNECTED", ""}
        ]
        count = len(active_conns)
        return {
            "ok": True,
            "configured": True,
            "userId": effective_uid,
            "connectedCount": count,
            "message": f"Composio connected for user '{effective_uid}' ({count} active connection{'s' if count != 1 else ''}).",
        }
    except ComposioAPIError as exc:
        if exc.status_code in {401, 403}:
            msg = "Composio rejected the API key (unauthorized). Double-check COMPOSIO_API_KEY."
        else:
            msg = f"Saved credentials, but Composio verification failed: {exc}"
        return {
            "ok": False,
            "configured": True,
            "userId": effective_uid,
            "connectedCount": 0,
            "message": _scrub_secret(msg),
        }


def list_toolkits(search="", limit=30):
    """
    Return live toolkits from Composio when configured, or curated popular catalog
    when unconfigured (or if the Composio API is temporarily unreachable).
    """
    lim = _clamp_limit(limit, default=30, maximum=100)
    query = str(search or "").strip()

    if not _get_api_key():
        catalog = _filter_popular_catalog(search=query, limit=lim)
        return {
            "ok": True,
            "configured": False,
            "source": "catalog",
            "count": len(catalog),
            "toolkits": catalog,
            "warning": "",
        }

    try:
        params = {"limit": lim}
        if query:
            params["search"] = query
        res = _request(
            "GET",
            "/toolkits",
            params=params,
            v2_path="/apps",
            v2_params={"limit": lim},
        )
        raw_items = _extract_items(res)
        toolkits = []
        for item in raw_items:
            norm = _normalize_toolkit(item)
            if not norm:
                continue
            if query:
                hay = f"{norm['slug']} {norm['name']} {norm['description']} {norm['category']}".lower()
                if query.lower() not in hay:
                    continue
            toolkits.append(norm)
            if len(toolkits) >= lim:
                break

        return {
            "ok": True,
            "configured": True,
            "source": "composio",
            "count": len(toolkits),
            "toolkits": toolkits,
            "warning": "",
        }
    except ComposioAPIError as exc:
        fallback = _filter_popular_catalog(search=query, limit=lim)
        return {
            "ok": True,
            "configured": True,
            "source": "catalog",
            "count": len(fallback),
            "toolkits": fallback,
            "warning": _scrub_secret(f"Live Composio toolkit lookup failed ({exc}); showing curated catalog."),
        }


def list_connections():
    """List active connected Composio accounts for the configured user."""
    user_id = _get_user_id()
    if not _get_api_key():
        return {
            "ok": True,
            "configured": False,
            "userId": user_id,
            "count": 0,
            "connections": [],
            "message": "Configure COMPOSIO_API_KEY to view connected accounts.",
        }

    try:
        res = _request(
            "GET",
            "/connected_accounts",
            params={"user_ids": user_id, "limit": 100},
            v2_path="/connectedAccounts",
            v2_params={"user_uuid": user_id},
        )
        connections = []
        for item in _extract_items(res):
            norm = _normalize_connection(item, fallback_user_id=user_id)
            if norm and norm["id"]:
                connections.append(norm)

        return {
            "ok": True,
            "configured": True,
            "userId": user_id,
            "count": len(connections),
            "connections": connections,
            "message": "",
        }
    except ComposioAPIError as exc:
        return {
            "ok": False,
            "configured": True,
            "userId": user_id,
            "count": 0,
            "connections": [],
            "message": _scrub_secret(str(exc)),
        }


def initiate_connection(toolkit_slug, redirect_url=""):
    """Initiate a 1-click Composio OAuth Connect Link for a toolkit."""
    slug = _sanitize_slug(toolkit_slug)
    user_id = _get_user_id()
    callback = str(redirect_url or "").strip()

    if not slug:
        return {
            "ok": False,
            "toolkitSlug": "",
            "userId": user_id,
            "connectedAccountId": "",
            "redirectUrl": "",
            "connectionStatus": "FAILED",
            "message": "Provide a valid toolkit_slug (e.g. 'gmail', 'notion', 'slack').",
        }

    if not _get_api_key():
        return {
            "ok": False,
            "toolkitSlug": slug,
            "userId": user_id,
            "connectedAccountId": "",
            "redirectUrl": "",
            "connectionStatus": "UNCONFIGURED",
            "message": "Configure COMPOSIO_API_KEY before connecting toolkits.",
        }

    if callback and not callback.startswith(("http://", "https://")):
        return {
            "ok": False,
            "toolkitSlug": slug,
            "userId": user_id,
            "connectedAccountId": "",
            "redirectUrl": "",
            "connectionStatus": "FAILED",
            "message": "redirect_url must be an http:// or https:// URL.",
        }

    # Try Composio v3 Connect Link flow first
    try:
        auth_config_id = _find_or_create_auth_config(slug)
        link_body = {
            "auth_config_id": auth_config_id,
            "user_id": user_id,
        }
        if callback:
            link_body["callback_url"] = callback

        try:
            res = _http_call(
                COMPOSIO_V3_BASE,
                "POST",
                "/connected_accounts/link",
                body=link_body,
            )
        except ComposioAPIError as link_exc:
            if link_exc.status_code != 404:
                raise
            # Fallback to v3 direct connected_accounts initiation
            direct_body = {
                "auth_config": {"id": auth_config_id},
                "connection": {"user_id": user_id},
            }
            if callback:
                direct_body["connection"]["callback_url"] = callback
            res = _http_call(
                COMPOSIO_V3_BASE,
                "POST",
                "/connected_accounts",
                body=direct_body,
            )

        redirect = str(
            res.get("redirect_url")
            or res.get("redirectUrl")
            or res.get("redirectUri")
            or ""
        )
        conn_id = str(res.get("connected_account_id") or res.get("id") or "")
        conn_status = str(res.get("status") or res.get("connectionStatus") or ("INITIATED" if redirect else "ACTIVE")).upper()

        return {
            "ok": True,
            "toolkitSlug": slug,
            "userId": user_id,
            "connectedAccountId": conn_id,
            "redirectUrl": redirect,
            "connectionStatus": conn_status,
            "expiresAt": str(res.get("expires_at") or ""),
            "message": "Open redirectUrl to complete OAuth connection." if redirect else "Connection initiated.",
        }
    except ComposioAPIError as v3_exc:
        # Graceful fallback to v2 initiation when v3 endpoints return 404
        if v3_exc.status_code == 404:
            try:
                v2_body = {"appName": slug, "entityId": user_id}
                if callback:
                    v2_body["redirectUri"] = callback
                res = _http_call(
                    COMPOSIO_V2_BASE,
                    "POST",
                    "/connectedAccounts",
                    body=v2_body,
                )
                redirect = str(res.get("redirectUrl") or res.get("redirectUri") or "")
                conn_id = str(res.get("connectedAccountId") or res.get("id") or "")
                conn_status = str(res.get("connectionStatus") or res.get("status") or "INITIATED").upper()
                return {
                    "ok": True,
                    "toolkitSlug": slug,
                    "userId": user_id,
                    "connectedAccountId": conn_id,
                    "redirectUrl": redirect,
                    "connectionStatus": conn_status,
                    "expiresAt": "",
                    "message": "Open redirectUrl to complete OAuth connection." if redirect else "Connection initiated.",
                }
            except ComposioAPIError as v2_exc:
                v3_exc = v2_exc

        return {
            "ok": False,
            "toolkitSlug": slug,
            "userId": user_id,
            "connectedAccountId": "",
            "redirectUrl": "",
            "connectionStatus": "FAILED",
            "message": _scrub_secret(str(v3_exc)),
        }


def list_tools(toolkit_slug="", search="", limit=25):
    """Search available Composio actions/tools for a toolkit or query."""
    slug = _sanitize_slug(toolkit_slug) if toolkit_slug else ""
    query = str(search or "").strip()
    lim = _clamp_limit(limit, default=25, maximum=100)

    if not _get_api_key():
        return {
            "ok": False,
            "configured": False,
            "toolkitSlug": slug,
            "count": 0,
            "tools": [],
            "message": "Configure COMPOSIO_API_KEY to list available Composio tools.",
        }

    v3_params = {"limit": lim}
    if slug:
        v3_params["toolkit_slug"] = slug
    if query:
        v3_params["search"] = query

    v2_params = {"limit": lim}
    if slug:
        v2_params["apps"] = slug
    if query:
        v2_params["useCase"] = query

    try:
        res = _request(
            "GET",
            "/tools",
            params=v3_params,
            v2_path="/actions",
            v2_params=v2_params,
        )
        tools = []
        for item in _extract_items(res):
            norm = _normalize_tool(item, default_toolkit=slug)
            if norm:
                tools.append(norm)
            if len(tools) >= lim:
                break

        return {
            "ok": True,
            "configured": True,
            "toolkitSlug": slug,
            "count": len(tools),
            "tools": tools,
            "message": "",
        }
    except ComposioAPIError as exc:
        return {
            "ok": False,
            "configured": True,
            "toolkitSlug": slug,
            "count": 0,
            "tools": [],
            "message": _scrub_secret(str(exc)),
        }


def execute_tool(tool_slug, arguments, connected_account_id=""):
    """Execute a Composio tool action and return a structured JSON result."""
    slug = str(tool_slug or "").strip()
    user_id = _get_user_id()
    conn_id = str(connected_account_id or "").strip()

    if not slug or not re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", slug):
        return {
            "ok": False,
            "toolSlug": slug,
            "connectedAccountId": conn_id,
            "successful": False,
            "data": None,
            "error": "Provide a valid tool_slug (e.g. 'GMAIL_FETCH_EMAILS').",
            "logId": "",
        }

    if not _get_api_key():
        return {
            "ok": False,
            "toolSlug": slug,
            "connectedAccountId": conn_id,
            "successful": False,
            "data": None,
            "error": "Configure COMPOSIO_API_KEY before executing tools.",
            "logId": "",
        }

    if arguments is None:
        args_dict = {}
    elif isinstance(arguments, dict):
        args_dict = arguments
    else:
        return {
            "ok": False,
            "toolSlug": slug,
            "connectedAccountId": conn_id,
            "successful": False,
            "data": None,
            "error": "arguments must be a JSON object (dict).",
            "logId": "",
        }

    encoded_slug = urllib.parse.quote(slug, safe="")
    v3_body = {
        "user_id": user_id,
        "arguments": args_dict,
    }
    if conn_id:
        v3_body["connected_account_id"] = conn_id

    v2_body = {
        "entityId": user_id,
        "input": args_dict,
    }
    if conn_id:
        v2_body["connectedAccountId"] = conn_id

    try:
        res = _request(
            "POST",
            f"/tools/execute/{encoded_slug}",
            body=v3_body,
            v2_path=f"/actions/{encoded_slug}/execute",
            v2_body=v2_body,
            timeout=60,
        )
        if not isinstance(res, dict):
            res = {"data": res}

        successful = bool(res.get("successful", res.get("successfull", True)))
        err_val = res.get("error")
        err_msg = _scrub_secret(err_val) if err_val else ""

        return {
            "ok": successful and not err_msg,
            "toolSlug": slug,
            "connectedAccountId": conn_id,
            "successful": successful,
            "data": res.get("data", res),
            "error": err_msg,
            "logId": str(res.get("log_id") or res.get("logId") or ""),
        }
    except ComposioAPIError as exc:
        return {
            "ok": False,
            "toolSlug": slug,
            "connectedAccountId": conn_id,
            "successful": False,
            "data": None,
            "error": _scrub_secret(str(exc)),
            "logId": "",
        }
