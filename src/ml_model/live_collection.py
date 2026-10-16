"""Bounded, provenance-aware collection for a future live-trust-v1 dataset.

This command never invents labels and never fetches a URL unless the manifest
explicitly marks it approved_for_fetch=true and --allow-network is supplied.
"""

import argparse
import csv
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from src.backend.analyzer import analyze
from src.backend.features import normalize_url
from src.backend.live_schema import LIVE_SCHEMA_VERSION

REQUIRED_COLUMNS = ("url", "label", "label_source", "label_confidence", "domain_group", "approved_for_fetch")


def collect_manifest(manifest_path: Path, output_path: Path, allow_network: bool = False) -> dict:
    records = []
    seen_urls: set[str] = set()
    seen_domain_groups: set[str] = set()
    with manifest_path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        missing = [column for column in REQUIRED_COLUMNS if column not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"Manifest is missing columns: {', '.join(missing)}")
        for row_number, row in enumerate(reader, start=2):
            normalized = normalize_url(row["url"])
            parsed = urlparse(normalized)
            label = row["label"].strip()
            if label not in {"0", "1"}:
                raise ValueError(f"Row {row_number} has an invalid label; use 1=legitimate or 0=phishing")
            if not row["label_source"].strip() or not row["label_confidence"].strip() or not row["domain_group"].strip():
                raise ValueError(f"Row {row_number} must include label source, confidence, and domain group")
            record = {"record_id": str(uuid.uuid4()), "url": normalized, "domain_group": row["domain_group"].strip(), "label": int(label), "label_source": row["label_source"].strip(), "label_confidence": row["label_confidence"].strip(), "source_timestamp": row.get("source_timestamp") or None, "collection_timestamp": datetime.now(timezone.utc).isoformat(), "feature_schema_version": LIVE_SCHEMA_VERSION, "collection_status": None, "canonical_features": None, "error": None}
            if normalized in seen_urls:
                record["collection_status"] = "duplicate_url_skipped"
            elif record["domain_group"] in seen_domain_groups:
                record["collection_status"] = "duplicate_domain_group_skipped"
            elif row["approved_for_fetch"].strip().lower() != "true" or not allow_network:
                record["collection_status"] = "not_collected_network_disabled"
            else:
                try:
                    result = analyze(normalized)
                    record["collection_status"] = result["status"]
                    record["canonical_features"] = result["canonical_features"]
                    record["collection_timestamp"] = result["created_at"]
                except (ValueError, OSError, TimeoutError) as error:
                    record["collection_status"] = "collection_error"
                    record["error"] = str(error)
            seen_urls.add(normalized)
            seen_domain_groups.add(record["domain_group"])
            records.append(record)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(json.dumps(record) for record in records) + ("\n" if records else ""), encoding="utf-8")
    return {"manifest": str(manifest_path), "output": str(output_path), "records": len(records), "collected": sum(record["canonical_features"] is not None for record in records), "skipped_or_failed": sum(record["canonical_features"] is None for record in records), "schema_version": LIVE_SCHEMA_VERSION}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path, default=Path("data/live/collected.jsonl"))
    parser.add_argument("--allow-network", action="store_true", help="Allow approved manifest URLs to be fetched")
    arguments = parser.parse_args()
    print(json.dumps(collect_manifest(arguments.manifest, arguments.output, arguments.allow_network), indent=2))