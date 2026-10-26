"""Saved niche lists and creator selection shared by the admin and refresh job."""
import re
import urllib.parse

DEFAULT_SCOPES = [
    {"id": "ai-dtc", "name": "AI × DTC ecommerce", "description": "AI workflows, creative production, and product discovery for ecommerce."},
    {"id": "dtc-agencies", "name": "DTC agencies / creative", "description": "Paid social, creative testing, and agency delivery."},
    {"id": "dtc-ecommerce", "name": "DTC ecommerce", "description": "Brand growth, acquisition, retention, and conversion."},
    {"id": "ai", "name": "AI broadly", "description": "AI tools, useful workflows, and industry developments."},
]
ALL = "__all__"


def scopes_for(config):
    return config.get("scopes", DEFAULT_SCOPES)


def validate_scope(config, scope):
    if not isinstance(scope, str) or (scope != ALL and scope not in {s["id"] for s in scopes_for(config)}):
        raise ValueError("Unknown niche list.")
    return scope


def validate_memberships(config, scopes):
    allowed = {s["id"] for s in scopes_for(config)}
    if not isinstance(scopes, list) or any(not isinstance(s, str) or s not in allowed for s in scopes):
        raise ValueError("Choose valid niche lists.")
    return list(dict.fromkeys(scopes))


def valid_handle(handle):
    return isinstance(handle, str) and bool(re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9._]{0,29}", handle))


def parse_handles(value):
    values = re.split(r"[\s,;]+", value.strip()) if isinstance(value, str) else value
    if not isinstance(values, list):
        raise ValueError("Paste Instagram handles separated by spaces, commas, or new lines.")
    handles = []
    for item in values:
        if not isinstance(item, str):
            raise ValueError("Each Instagram handle must be text.")
        handle = item.strip().strip("\"'“”‘’").lstrip("@").lower()
        if not handle:
            continue
        if handle.startswith(("https://", "http://")):
            url = urllib.parse.urlparse(handle)
            if url.hostname not in {"instagram.com", "www.instagram.com"}:
                raise ValueError("Use Instagram profile links or exact handles.")
            handle = url.path.strip("/")
        if not valid_handle(handle):
            raise ValueError(f"Invalid Instagram handle: {item[:50]}")
        if handle not in handles:
            handles.append(handle)
    if not handles or len(handles) > 25:
        raise ValueError("Add between 1 and 25 unique Instagram handles at a time.")
    return handles


def select_creators(config, scope=ALL, tracked_only=True):
    """A shared creator is scraped once, even when it belongs to several lists."""
    validate_scope(config, scope)
    unique = {}
    for creator in config.get("creators", []):
        if not valid_handle(creator.get("handle")):
            continue
        handle = creator["handle"].lower()
        if tracked_only and not creator.get("trackingEnabled", True):
            continue
        if scope != ALL and scope not in creator.get("scopes", []):
            continue
        if handle not in unique:
            unique[handle] = {**creator, "handle": handle}
    return list(unique.values())
