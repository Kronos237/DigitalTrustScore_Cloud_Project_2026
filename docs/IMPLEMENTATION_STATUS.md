# Implementation Status

Updated 2026-10-15.

## Working

- React/Vite dashboard with real backend API calls.
- Live bounded URL analysis with SSRF/private-target rejection.
- TLS handshake and certificate metadata when available.
- Security-header observations and reliability timing/status.
- HTML transparency heuristics with unknown/unavailable states.
- Versioned `live-trust-v1` canonical feature vector emitted with live analysis.
- Optional VirusTotal domain adapter with disabled-by-default and failure-safe states.
- Provenance-aware live collection CLI requiring explicit labels and fetch approval.
- Evidence-based prototype trust score and persisted analysis history.
- SQLAlchemy repository with local SQLite and PostgreSQL-compatible `DATABASE_URL`.
- UCI and PhiUSIIL benchmark models, validation artifacts, and separate SHAP explainers.
- URL-only `live-phishing-v1` model trained from raw PhiUSIIL URLs with domain-group evaluation; live use is opt-in.
- Live phishing-risk inference and SHAP explanations using the shared URL extractor when explicitly enabled.
- FastAPI adapter, Docker configuration, and local Compose configuration.

## Experimental

- Prototype category weights and thresholds.
- Lexical transparency detection.
- URL suspicious-pattern features.
- Benchmark model results, which are dataset-specific and not live predictions.

## Unavailable or deferred

- Domain age/RDAP and certificate transparency.
- Safe redirect-following observation.
- ATT&CK/CVE correlation.
- S3 artifact provider.
- AWS deployment and CloudWatch/IAM wiring.
- Docker runtime validation on this machine because Docker is not installed.

## Verification

- Python suite: 27 tests passed in the last local run.
- Frontend suite: 2 tests passed.
- Frontend production build: passed.
- FastAPI real analysis and SQLite restart persistence: passed with `https://example.com`.
- Compose YAML parsing: passed.
- Docker build/Compose startup: not run because Docker executable is unavailable.
- VirusTotal live lookup: not run; adapter is disabled without credentials and tested with mocked responses.
- VirusTotal connectivity: one real `example.com` domain lookup returned `no_malicious_finding`; no broad collection was performed.
- Live URL dataset: generated reproducibly from PhiUSIIL URL strings without opening them; labels inherit PhiUSIIL provenance and limitations.
- Live model warning: `https://example.com` is predicted phishing by the URL-only model; external/temporal validation is still required.
- Default live behavior: `LIVE_ML_ENABLED=false`; trust analysis does not present the known false-positive-prone model as a default result.