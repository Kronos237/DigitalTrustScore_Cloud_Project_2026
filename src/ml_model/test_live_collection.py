import csv
import tempfile
import unittest
from pathlib import Path

from .live_collection import collect_manifest


class LiveCollectionTests(unittest.TestCase):
    def test_manifest_is_provenance_aware_and_network_disabled_by_default(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = root / "manifest.csv"
            output = root / "rows.jsonl"
            with manifest.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=["url", "label", "label_source", "label_confidence", "domain_group", "approved_for_fetch", "source_timestamp"])
                writer.writeheader()
                writer.writerow({"url": "https://example.com", "label": "1", "label_source": "manual_review", "label_confidence": "high", "domain_group": "example.com", "approved_for_fetch": "false", "source_timestamp": "2026-10-15"})
            summary = collect_manifest(manifest, output)
            self.assertEqual(summary["collected"], 0)
            self.assertIn("not_collected_network_disabled", output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()