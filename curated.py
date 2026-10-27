"""Offline renderer for independently retained curated research."""
import json
from html import escape
from pathlib import Path
from urllib.parse import urlparse


class CuratedResearchError(ValueError):
    """Raised when the curated research file cannot be safely rendered."""


def _text(value, field):
    if not isinstance(value, str):
        raise CuratedResearchError(f"{field} must be a string")
    return value


def _required_text(value, field):
    value = _text(value, field)
    if not value.strip():
        raise CuratedResearchError(f"{field} must not be empty")
    return value


def _strings(value, field):
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        raise CuratedResearchError(f"{field} must be a list of strings")
    return value


def _safe_url(value):
    """Return an absolute HTTP(S) URL, or None. Never emit executable schemes."""
    if not isinstance(value, str):
        return None
    parsed = urlparse(value)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
        return None
    return value


def load_curated_research(path):
    """Load and validate curated research. A missing optional file is not an error."""
    path = Path(path)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise CuratedResearchError(f"could not read {path.name}: {exc}") from exc
    if not isinstance(data, dict) or data.get("version") != 1:
        raise CuratedResearchError("curated research must be an object with version 1")
    _text(data.get("updatedAt"), "updatedAt")
    for field in ("principles", "caveats"):
        _strings(data.get(field), field)
    items = data.get("items")
    if not isinstance(items, list):
        raise CuratedResearchError("items must be a list")
    ids = set()
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise CuratedResearchError(f"items[{index}] must be an object")
        item_id = _required_text(item.get("id"), f"items[{index}].id")
        if item_id in ids:
            raise CuratedResearchError(f"items[{index}].id duplicates {item_id!r}")
        ids.add(item_id)
        _required_text(item.get("sourceUrl"), f"items[{index}].sourceUrl")
        for field in ("topic", "creator", "sourceCaption", "status", "audienceFit", "sourceTake", "proposedTake", "evidenceLimit"):
            _text(item.get(field), f"items[{index}].{field}")
        _strings(item.get("substance"), f"items[{index}].substance")
        _strings(item.get("scopes"), f"items[{index}].scopes")
        metrics = item.get("metrics")
        if not isinstance(metrics, dict):
            raise CuratedResearchError(f"items[{index}].metrics must be an object")
        for field in ("source", "observedAt", "viewsDisplay", "outlierDisplay", "engagementDisplay", "postedAgeDisplay"):
            _text(metrics.get(field), f"items[{index}].metrics.{field}")
        if "sourceUrl" in metrics and metrics["sourceUrl"] is not None:
            _text(metrics["sourceUrl"], f"items[{index}].metrics.sourceUrl")
    return data


def _list(values):
    return "".join(f"<li>{escape(value)}</li>" for value in values)


def _link(url, label):
    safe_url = _safe_url(url)
    if not safe_url:
        return ""
    return f'<a href="{escape(safe_url, quote=True)}" target="_blank" rel="noopener noreferrer">{escape(label)}</a>'


def _item(item):
    metrics = item["metrics"]
    original_link = _link(item["sourceUrl"], "Open original")
    provider_link = _link(metrics.get("sourceUrl"), f'Source: {metrics["source"]}')
    links = " ".join(link for link in (original_link, provider_link) if link) or "<span>Original/source link unavailable</span>"
    metric_values = [metrics["viewsDisplay"], metrics["outlierDisplay"], metrics["engagementDisplay"], metrics["postedAgeDisplay"]]
    search_text = " ".join([item["topic"], item["creator"], item["status"], item["audienceFit"], item["sourceTake"], item["proposedTake"], *item["substance"]]).lower()
    return f'''<article id="{escape(item["id"], quote=True)}" class="curated-card" data-curated-search="{escape(search_text, quote=True)}">
  <div class="curated-card-top"><span class="curated-status">{escape(item["status"])}</span><span>{escape(item["creator"])}</span></div>
  <h3>{escape(item["topic"])}</h3>
  <p class="curated-fit"><strong>Audience fit:</strong> {escape(item["audienceFit"])}</p>
  <div class="curated-metrics"><span>Source: {escape(metrics["source"])}</span><span>Observed: {escape(metrics["observedAt"])}</span>{"".join(f"<span>{escape(value)}</span>" for value in metric_values)}</div>
  <details class="curated-caption"><summary>Source caption/excerpt</summary><p>{escape(item["sourceCaption"])}</p></details>
  <p><strong>Source takeaway:</strong> {escape(item["sourceTake"])}</p>
  <p><strong>Proposed original angle:</strong> {escape(item["proposedTake"])}</p>
  <div><strong>Concrete substance</strong><ul>{_list(item["substance"])}</ul></div>
  <p class="curated-limit"><strong>Evidence limit:</strong> {escape(item["evidenceLimit"])}</p>
  <p class="curated-scopes">Scopes: {escape(", ".join(item["scopes"])) or "Unscoped"}</p>
  <p class="curated-links">{links}</p>
</article>'''


def render_curated_research(data):
    """Return escaped, self-contained HTML; curated samples never enter feed metrics."""
    if data is None:
        body = '<p class="curated-empty">No curated research file has been supplied yet. Feed baselines remain unchanged.</p>'
        updated = "Not supplied"
        principles = caveats = ""
    else:
        updated = escape(data["updatedAt"])
        principles = f'<div><h3>Principles</h3><ul>{_list(data["principles"])}</ul></div>' if data["principles"] else ""
        caveats = f'<div><h3>Caveats</h3><ul>{_list(data["caveats"])}</ul></div>' if data["caveats"] else ""
        body = "".join(_item(item) for item in data["items"]) or '<p class="curated-empty">No curated items yet. Feed baselines remain unchanged.</p>'
    return f'''<section id="curated-research" class="curated-research" aria-labelledby="curated-heading">
  <details open>
    <summary><span><span class="section-title">Curated research</span><strong id="curated-heading">Independent examples and proposed angles</strong></span><span>Updated {updated}</span></summary>
    <p class="curated-intro">These independently retained samples are source-labelled editorial research. They are not part of the 28-day feed, creator medians, or Outlier ratios.</p>
    <label class="curated-search-label">Find curated research <input id="curated-search" type="search" placeholder="Search topic, creator, or substance"></label>
    <div class="curated-notes">{principles}{caveats}</div>
    <div class="curated-grid" id="curated-grid">{body}</div>
  </details>
</section>'''
