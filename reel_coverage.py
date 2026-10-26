"""Separate requested coverage, authored Reels, and collaborations."""
from collections import defaultdict
from datetime import datetime, timezone
from urllib.parse import urlparse


def summarize_coverage(handles, items, limit, fetched_at=None):
    grouped = defaultdict(list)
    for item in items:
        handle = urlparse(item.get("inputUrl") or "").path.strip("/").split("/")[0].lower()
        if handle not in handles:
            handle = (item.get("ownerUsername") or "").lower()
        if handle in handles:
            grouped[handle].append(item)
    result = {}
    for handle in handles:
        rows = grouped[handle]
        authored = {r["shortCode"] for r in rows if r.get("shortCode") and (r.get("ownerUsername") or "").lower() == handle}
        collaborations = {r["shortCode"] for r in rows if r.get("shortCode") and (r.get("ownerUsername") or "").lower() != handle
                          and any(c.get("username", "").lower() == handle for c in (r.get("coauthorProducers") or []))}
        result[handle] = {"requestedAt": fetched_at or datetime.now(timezone.utc).isoformat(),
                          "limit": limit, "authoredReels": len(authored), "collaborations": len(collaborations),
                          "status": "loaded" if authored else "collaborations_only" if collaborations else "no_reels_returned",
                          "errors": sorted({r["error"] for r in rows if r.get("error")}),
                          "rowsReturned": len(rows)}
    return result
