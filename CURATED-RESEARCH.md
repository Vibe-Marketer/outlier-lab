# Curated research

`data/curated_research.json` is an optional, independently retained editorial-research source. It is rendered into the collapsible **Curated research** section near the top of `index.html` and is deliberately separate from the rolling 28-day feed.

## Contract

The file must be JSON matching this shape:

```json
{
  "version": 1,
  "updatedAt": "2026-10-27",
  "principles": ["string"],
  "caveats": ["string"],
  "items": [{
    "id": "stable-unique-anchor",
    "topic": "string",
    "creator": "string",
    "sourceUrl": "https://direct-original.example/post",
    "sourceCaption": "exact source caption or excerpt",
    "metrics": {
      "source": "provider name",
      "sourceUrl": "https://optional-provider.example/research",
      "observedAt": "string",
      "viewsDisplay": "string",
      "outlierDisplay": "string",
      "engagementDisplay": "string",
      "postedAgeDisplay": "string"
    },
    "status": "string",
    "audienceFit": "string",
    "sourceTake": "what the source supports",
    "proposedTake": "proposed original angle, not a measured result",
    "substance": ["concrete detail"],
    "evidenceLimit": "what is not known",
    "scopes": ["optional organizational labels"]
  }]
}
```

`id` and `sourceUrl` are required non-empty strings; item IDs must be unique. `metrics.sourceUrl` is optional and, when supplied, renders a separate provider link. `sourceCaption` is plain exact source text in its own collapsed **Source caption/excerpt** disclosure, never a link label. Each item’s stable ID becomes its article anchor and `topic` is rendered as the item `h3`.

## Boundaries and safety

- Curated items are never loaded into reel rows, feed totals, creator medians, outlier ratios, or 28-day refresh logic.
- Display metrics remain source-labelled strings. They are not normalized, calculated, or blended with Outlier metrics.
- The renderer escapes all text. It renders original/provider links only for absolute `https://` or `http://` URLs; other schemes are shown as unavailable rather than emitted.
- A missing file leaves an explicit empty section so the top link remains valid. Present but malformed data stops the build with a clear `CuratedResearchError`, rather than silently removing prior research.

Run the offline contract tests with:

```sh
python3 -m unittest tests/test_curated.py
```

## Ongoing input / output workflow

Use this project as the canonical home, not a parallel spreadsheet.

1. Discover specific high-performing content from the latest 7–21 days. Keep original URL, creator, publication date, observed metrics, baseline definition and observation time. Recent news alone is not validation.
2. Check audience fit separately. Require corroboration before calling a topic an emerging trend; compare repeated observations at comparable post ages to measure acceleration.
3. Search existing ids and source URLs before adding. Use Instagram shortcode as identity. Preserve earlier dated observations rather than silently overwrite history.
4. Preserve what the source already says. Retrieve daily-work evidence to propose Andrew’s new distinction, example or method; distinguish actual work from a demo still needed.
5. Store in data/curated_research.json. Keep provider scores separate from feed medians. Curated entries survive normal rolling-feed refreshes.
6. Retrieve using Curated research search or #ig-SHORTCODE anchors. Open the original before script development; proposals are not proven outcomes or globally verified novel ideas.
7. Validate with python3 -m unittest tests/test_curated.py, rebuild using build.py, inspect the BB preview, review the diff, then publish only the authorized update through GitHub/Vercel. Editorial import must not trigger paid scrape, transcription or schedule changes.

Initial import: three new public-source candidates plus one annotation of an existing reel. Existing 410-reel feed and 104 outliers unchanged. No recurring ingestion or cross-app synchronization was activated.
