import json
import tempfile
import unittest
from pathlib import Path

from curated import CuratedResearchError, load_curated_research, render_curated_research


def sample():
    return {"version": 1, "updatedAt": "2026-10-27", "principles": ["Keep <evidence> separate"], "caveats": ["No measured outcome"], "items": [{"id": "source-item", "topic": "Hooks <tested>", "creator": "A <B>", "sourceUrl": "https://example.com/original", "sourceCaption": "Exact <source> excerpt", "metrics": {"source": "Example provider", "sourceUrl": "https://provider.example/research", "observedAt": "2026-10-27", "viewsDisplay": "10K views", "outlierDisplay": "2x reported", "engagementDisplay": "100 comments", "postedAgeDisplay": "3 days"}, "status": "Proposed", "audienceFit": "Good", "sourceTake": "Observed <claim>", "proposedTake": "Test & learn", "substance": ["Use a concrete opening"], "evidenceLimit": "No conversion data", "scopes": ["ai"]}]}


class CuratedResearchTests(unittest.TestCase):
    def test_missing_file_renders_explicit_empty_section(self):
        self.assertIsNone(load_curated_research(Path("/tmp/no-curated-research-file.json")))
        self.assertIn('id="curated-research"', render_curated_research(None))

    def test_escapes_text_links_and_searchable_takeaways(self):
        data = sample()
        html = render_curated_research(data)
        self.assertIn('id="source-item"', html)
        self.assertIn("<h3>Hooks &lt;tested&gt;</h3>", html)
        self.assertIn("<summary>Source caption/excerpt</summary><p>Exact &lt;source&gt; excerpt</p>", html)
        self.assertIn('href="https://example.com/original"', html)
        self.assertIn('href="https://provider.example/research"', html)
        self.assertIn("test &amp; learn", html.lower())
        data["items"][0]["sourceUrl"] = "javascript:alert(1)"
        data["items"][0]["metrics"]["sourceUrl"] = "javascript:alert(2)"
        html = render_curated_research(data)
        self.assertNotIn("javascript:", html)
        self.assertIn("link unavailable", html)

    def test_malformed_present_file_fails_instead_of_erasing(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "curated_research.json"
            path.write_text("{not json")
            with self.assertRaises(CuratedResearchError):
                load_curated_research(path)
            bad = sample()
            bad["items"].append(sample()["items"][0].copy())
            path.write_text(json.dumps(bad))
            with self.assertRaisesRegex(CuratedResearchError, "duplicates"):
                load_curated_research(path)
            bad = sample()
            bad["items"][0]["sourceUrl"] = " "
            path.write_text(json.dumps(bad))
            with self.assertRaisesRegex(CuratedResearchError, "sourceUrl must not be empty"):
                load_curated_research(path)


if __name__ == "__main__":
    unittest.main()
