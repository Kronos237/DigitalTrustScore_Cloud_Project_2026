# Project Decisions

This is the persistent decision log for the Digital Trust Score Framework.

## 2026-10-15: Keep benchmark models separate from live analysis

- **Decision:** UCI and PhiUSIIL remain independent benchmark phishing-risk experiments. Neither is fed live collector features.
- **Reason:** Their feature definitions, encodings, collection processes, and label semantics are incompatible with the live schema.
- **Alternatives considered:** Approximate live values into benchmark columns; rejected because it would create unvalidated predictions.
- **Trade-offs:** Live ML remains unavailable until a labelled dataset is collected through the canonical live collector.
- **Status:** Accepted and implemented.
- **Evidence:** `docs/ML_FEATURE_MAPPING.md`, `docs/ML_VALIDATION.md`, benchmark artifact metadata.

## 2026-10-15: Live score remains evidence-based and ML-independent

- **Decision:** The live trust score combines observed security, neutral-for-unavailable reputation, transparency, and reliability dimensions. ML is displayed separately as unavailable when no compatible model exists.
- **Reason:** Missing evidence must not be treated as malicious evidence, and phishing probability is not equivalent to trustworthiness.
- **Alternatives considered:** Multiply the trust score by benchmark phishing probability; rejected as a schema and construct mismatch.
- **Status:** Implemented.

## 2026-10-15: Canonical live schema is versioned before live ML

- **Decision:** Define `live-trust-v1` from bounded URL, TLS, HTTP, security-header, transparency, DNS, and reputation-status observations. Keep availability/status separate from numeric values.
- **Reason:** Training and inference need one explicit ordering and missing-value policy.
- **Status:** Implemented as a schema contract; no live-compatible model is claimed yet.

## 2026-10-15: OSINT starts with an unavailable provider boundary

- **Decision:** Reputation is represented by a provider interface. A VirusTotal domain adapter is available when `VIRUSTOTAL_API_KEY` is configured; without credentials it returns disabled, and no provider result is fabricated.
- **Reason:** Public reputation APIs have different terms, coverage, rate limits, and privacy implications.
- **Status:** Adapter implemented and mocked-tested; production credentials, rate-limit/cache policy, and external service use remain optional.

## 2026-10-15: Local persistence is portable

- **Decision:** SQLAlchemy repository with SQLite by default and PostgreSQL selected by `DATABASE_URL`.
- **Reason:** The local demo must work without AWS while retaining a production-compatible persistence boundary.
- **Status:** Implemented and tested for restart persistence.

## 2026-10-15: AWS remains deferred

- **Decision:** Do not create or configure EC2, RDS, S3, IAM, Amplify, or CloudWatch in this phase.
- **Reason:** Local behavior, schema contracts, and tests must be stable before cloud deployment.
- **Status:** Accepted; documented in `docs/CLOUD_ARCHITECTURE.md`.

## 2026-10-16: Outcome B for live-compatible ML

- **Decision:** Do not train or integrate a live phishing-risk model yet. Complete and preserve the live schema, OSINT boundary, and provenance-aware collection pipeline instead.
- **Reason:** UCI has no replayable URL records, PhiUSIIL URLs should not be fetched indiscriminately, and a small legitimate-only or feed-absence-labelled sample would not support defensible binary training. No trustworthy live-feature rows currently exist.
- **Alternatives considered:** Map benchmark rows into live features; rejected because it would fabricate unavailable TLS/HTTP/transparency/reputation evidence. Fetch phishing URLs from the benchmark; rejected as unsafe uncontrolled access. Treat absence from a feed as legitimate; rejected as invalid labeling.
- **Trade-offs:** Live ML and live SHAP remain explicitly unavailable, but future collection is reproducible and safe when an approved manifest and label sources are supplied.
- **Status:** Accepted and implemented in `src/ml_model/live_collection.py` and `data/live/README.md`.

## 2026-10-16: VirusTotal verification

- **Decision:** Keep VirusTotal domain lookup optional and backend-only; enable it through `VIRUSTOTAL_API_KEY` loaded from ignored `.env`.
- **Reason:** API terms, rate limits, privacy, and credentials must not become frontend or test dependencies.
- **Result:** One real domain-level lookup for `example.com` returned `no_malicious_finding`; provider tests remain mocked and deterministic.
- **Status:** Adapter implemented, real connectivity verified once, broad collection deferred.

## 2026-10-16: Outcome A for URL-only live ML

- **Decision:** Train and integrate a separate `live-phishing-v1` URL-only model from PhiUSIIL raw URL strings and labels, using the same deterministic extractor for training and live inference.
- **Reason:** The archive contains 235,795 raw URLs and binary labels; URL lexical/structural features can be computed without visiting any URL. This is compatible with safe live inference, unlike the existing dataset-specific numeric features.
- **Method:** Remove duplicate URLs, reject conflicting URL labels, split by domain group, fit preprocessing only on training data, select on validation ROC-AUC/F1, and evaluate the untouched test group.
- **Alternatives considered:** Reuse PhiUSIIL numeric features; rejected because they are not available identically at live inference. Fetch dataset URLs; rejected as unsafe. Use UCI benchmark; rejected due schema mismatch.
- **Trade-offs:** The model has strong benchmark metrics but likely dataset/collection bias; `https://example.com` receives a phishing prediction and must be treated as a warning that external validation is required.
- **Status:** Implemented and tested; not production-grade or scientifically validated for arbitrary websites.
- **Evidence:** `src/ml_model/live_url_features.py`, `src/ml_model/live_url_train.py`, `models/live-phishing/`, `experiments/live-phishing/`, and live model tests.

## 2026-10-16: Keep live ML opt-in pending external validation

- **Decision:** Keep `LIVE_ML_ENABLED=false` by default. The URL-only model remains available as an explicitly opt-in experiment; the broader live trust analysis does not depend on it.
- **Reason:** The model maps classes and features correctly, but `example.com` receives phishing probability `1.0`; nearest training URL-feature vectors are phishing-labelled. This demonstrates source/distribution bias and unacceptable default false-positive risk.
- **Alternatives considered:** Lower the threshold; rejected because it would not repair the feature-distribution problem. Retrain blindly; rejected because the same source bias would remain. Hide the result; rejected because it is important validation evidence.
- **Status:** Implemented. Enable only for controlled research evaluation with `LIVE_ML_ENABLED=true`.