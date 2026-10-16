# Live Dataset Collection

This directory is reserved for provenance-aware rows collected through the actual live collectors. No training dataset is currently present and no labels are inferred from missing reputation results.

## Manifest

Create a private manifest CSV with these columns:

```text
url,label,label_source,label_confidence,domain_group,approved_for_fetch,source_timestamp
```

Use `label=1` for legitimate and `label=0` for phishing only when the source explicitly supports that label. `approved_for_fetch=true` is a deliberate safety approval, not an inferred property. Keep domain groups so future splits can prevent domain leakage.

Run without network access to validate provenance and produce skipped records:

```text
python -m src.ml_model.live_collection data/live/manifest.csv --output data/live/collected.jsonl
```

To collect real observations, review the manifest and explicitly opt in:

```text
python -m src.ml_model.live_collection data/live/manifest.csv --output data/live/collected.jsonl --allow-network
```

The collector reuses URL validation, SSRF protections, bounded requests, TLS/header/transparency collectors, `live-trust-v1`, and the optional VirusTotal domain adapter. It skips duplicate URLs and domain groups and records collection failures instead of fabricating feature rows.