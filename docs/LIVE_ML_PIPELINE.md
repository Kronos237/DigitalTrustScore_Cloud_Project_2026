# Live ML Pipeline

The project now has a separate `live-phishing-v1` URL-only model. It does not reuse the numeric PhiUSIIL features, does not visit dataset URLs, and does not replace the UCI/PhiUSIIL benchmark experiments. It is an Outcome A implementation with explicit generalization limitations.

## Canonical schema target

The proposed `live-trust-v1` schema will use bounded numeric observations for URL structure, TLS status, security headers, HTTP reliability, transparency indicators, DNS status, and reputation status. Every field must carry an availability/status policy where absence is not silently encoded as malicious or safe.

## Required future pipeline

```text
labelled URLs -> live collectors -> live-trust-v1 rows
               -> provenance-aware cleaning -> domain/time-aware split
               -> preprocessing fitted on training only
               -> Logistic Regression vs Random Forest
               -> untouched test metrics -> saved model/schema metadata
               -> compatible live inference -> local SHAP
```

The live response uses the saved URL-only model only when its schema metadata and artifact are compatible and `LIVE_ML_ENABLED=true`. It is disabled by default because the legitimate-site regression exposed a severe source/distribution false-positive risk. Its phishing-risk probability and SHAP explanation are separate from the rule-based Digital Trust Score.

## Actual live-compatible experiment

- Dataset source: PhiUSIIL raw `URL` strings and `label` from UCI dataset 967.
- Raw rows: `235,795`.
- Invalid URL rows: `0`.
- Duplicate URLs removed: `425`.
- Conflicting URL labels: `0`.
- Prepared rows: `235,370`.
- Phishing rows: `134,850` (`PhiUSIIL label=0`).
- Legitimate rows: `100,520` (`PhiUSIIL label=1`).
- Unique domains: `220,077`.
- Features: `24` deterministic URL-only features in `live_url_features.py`.
- Split: domain-group outer split, 187,856 train, 37,683 validation, 47,514 test.
- Random states: outer `42`, validation `43`.

Random Forest was selected on validation ROC-AUC/F1. Final held-out test metrics:

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
| --- | ---: | ---: | ---: | ---: | ---: |
| Logistic Regression | 0.993854 | 0.999555 | 0.986190 | 0.992827 | 0.996567 |
| Random Forest | 0.995707 | 0.997841 | 0.992192 | 0.995008 | 0.997537 |

Artifacts are under `models/live-phishing/` and `experiments/live-phishing/`.

These metrics are benchmark results only. The URL-only model predicts `https://example.com` as phishing with probability `1.0`, demonstrating that high held-out performance does not establish live-world validity. The nearest 100 training feature vectors to `example.com` are all phishing-labelled, so this is a distribution/source bias failure rather than a class-index bug. The model is disabled by default and must be externally and temporally validated before any safety or production claim.

## Label and data policy

A future dataset must retain stable record ID, canonical feature values, label, label source, confidence/verification state, source timestamp, collection timestamp, schema version, collection status, and domain-group identifier. URLs absent from a malicious feed must not automatically become legitimate examples.

`src/ml_model/live_collection.py` implements the bounded collection boundary. It accepts only manifests with explicit labels, provenance, domain groups, and `approved_for_fetch=true`; network collection additionally requires `--allow-network`. It skips duplicate URLs/domain groups and writes JSONL records with collection status and errors. No manifest or live training rows currently exist.

## Current commands

Benchmark reproduction remains separate:

```text
python -m src.ml_model.train data/raw/phishing+websites.zip --models-dir models --experiments-dir experiments
python -m src.ml_model.phiusiiil_train data/raw/phiusiiil/phiusiil-phishing-url-dataset.zip --models-dir models/phiusiiil --experiments-dir experiments/phiusiiil
```

Future pilot collection:

```text
python -m src.ml_model.live_collection data/live/manifest.csv --output data/live/collected.jsonl
python -m src.ml_model.live_collection data/live/manifest.csv --output data/live/collected.jsonl --allow-network
```

The current model does not require opening the dataset URLs because the dataset already contains raw URL strings. Future collection remains available for external label sources and drift evaluation.

## Diagnostic reproduction

```text
python -m src.ml_model.live_url_diagnostics
```

This writes `experiments/live-phishing/diagnostics.json` with class mapping, confusion matrix, classification report, average precision, calibration bins, four legitimate-site predictions, exact feature vectors, and SHAP contributor directions. It does not visit any URL.