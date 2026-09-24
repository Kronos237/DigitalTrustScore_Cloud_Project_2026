# TrustGuard: Digital Trust Score Framework

Digital Trust Score Framework for Cloud Applications using Explainable Artificial Intelligence and Trust Analytics.

## Purpose

TrustGuard produces an analytical estimate of a website's digital trust profile from observable evidence. It does not certify a website and does not guarantee safety. The current prototype distinguishes observed evidence, missing evidence, unavailable providers, and prototype scoring thresholds.

## Current Workflow

```text
URL -> validation and SSRF checks -> bounded public fetch -> TLS/header/URL/transparency evidence
    -> category scores -> prototype trust score -> explanation -> SQLite history -> dashboard
```

The local application uses a FastAPI backend with a stdlib HTTP fallback. SQLAlchemy selects SQLite locally or PostgreSQL through `DATABASE_URL`. The Random Forest/XAI pipelines, Docker Compose file, and environment template are also included for the next deployment stage.

## Implemented Features

- Real URL parsing, public-hostname protection, bounded HTTP retrieval, TLS inspection, response headers, response timing, and HTML transparency signals.
- Security, reputation-availability, transparency, and reliability category scores.
- Configurable prototype weights, risk categories, evidence provenance, and an explicit unavailable ML state.
- Persistent local analysis history using SQLite, with analysis, feature, explanation, history, health, model-info, and statistics endpoints.
- TrustGuard dashboard with category bars, technical evidence, security headers, explanations, history, loading/error states, and safety disclaimer.
- Reproducible scikit-learn Random Forest training entry point that requires a real compatible CSV and writes actual metrics and metadata.
- SHAP global and local explanations for the persisted benchmark Random Forest, kept separate from live trust analysis.
- Independent PhiUSIIL benchmark experiment with its own audit, models, metrics, and SHAP artifacts.
- SQLAlchemy repository persistence with local SQLite and PostgreSQL-compatible configuration.

## Local Setup

The zero-install path requires Python 3.10+:

```text
python -m src.backend.api
```

Open `http://127.0.0.1:8000` and use a safe public URL such as `https://example.com`.

## React Dashboard

The primary frontend is the Vite React dashboard under `src/frontend`. Run it alongside the backend:

```text
cd src/frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`. Vite proxies `/api` requests to the Python backend at port `8000`. The dashboard uses the real live analysis, history, model registry, and benchmark SHAP endpoints. Build and test it with `npm run build` and `npm test`.

For the production-shaped API adapter:

```text
python -m pip install -r requirements.txt
uvicorn src.backend.fastapi_app:app --host 127.0.0.1 --port 8000
```

Initialize a fresh local database without deleting existing rows:

```text
.venv\Scripts\python.exe -m src.database.init_db
```

Set `DATABASE_URL=sqlite:///results/trustguard.db` for local SQLite. Docker Compose requires `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD` in `.env` and switches the backend to PostgreSQL.

Optional local services:

```text
copy .env.example .env
# Set POSTGRES_PASSWORD in .env before starting Compose
docker compose up --build
```

Compose runs FastAPI on port `8000` and PostgreSQL on the private Compose network. Docker must be installed locally; no AWS resources are required.

Copy `.env.example` to `.env` and set values appropriate to the environment. Never commit `.env`, credentials, API keys, or passwords.

## API

- `POST /api/analyze` with `{ "url": "https://example.com" }`
- `GET /api/analysis/{id}`
- `GET /api/history`
- `GET /api/features/{id}`
- `GET /api/explanation/{id}`
- `GET /api/statistics`
- `GET /api/model/info`
- `GET /api/health`
- `GET /api/ml/feature-importance`
- `GET /api/ml/explanation/{sample_id}` (for example, `test-00000`)

`POST /api/score` remains as a compatibility alias for the original MVP.

## ML and XAI Status

The live analyzer does not claim a trained phishing model or fabricate SHAP values. `src/ml_model/train.py` trains a real Random Forest when a licensed dataset matching `feature_schema.py` is supplied:

```text
python -m src.ml_model.train data/external/your_dataset.csv --output-dir results/model
```

The current validated run used 1,696 unambiguous feature vectors after excluding conflicting labels and selected Random Forest over Logistic Regression by validation ROC-AUC then F1. Its validation report is [ML_VALIDATION.md](docs/ML_VALIDATION.md); actual metrics are stored in `models/model_metadata.json` and `experiments/model_comparison.csv`. SHAP explains this benchmark model on its UCI test set, not the complete Digital Trust Score. Benchmark phishing labels are not equivalent to universal website trustworthiness, so the live API deliberately reports `ML prediction unavailable for live feature set` until a validated adapter exists.

The independent PhiUSIIL experiment is documented in the PhiUSIIL section of [ML_VALIDATION.md](docs/ML_VALIDATION.md). Its artifacts live under `models/phiusiiil/` and `experiments/phiusiiil/`; it is not mixed with the frozen UCI benchmark or live analysis.

## Architecture Direction

The intended cloud topology is frontend hosting through AWS Amplify, FastAPI on EC2, PostgreSQL on private RDS, S3 for datasets/model artifacts/reports, IAM roles for access, and CloudWatch for logs and metrics. The current local storage abstraction is SQLite; PostgreSQL and S3 adapters require environment configuration and credentials and are not silently faked.

## Testing

```text
python -m unittest src.backend.test_backend -v
python -m compileall -q src/backend src/ml_model
```

The test suite covers URL validation, score bounds, relative baseline behavior, and private-target rejection. Live-site analysis is environment-dependent and should use safe public sites only.

## Limitations and Research Integrity

Public reputation and domain-age data are currently unavailable rather than guessed. Websites can block automated retrieval, change over time, or expose incomplete signals. Public phishing datasets contain sampling and concept-drift bias and may not generalize to cloud-application trust. Prototype category weights and thresholds are not scientifically validated. No result is a safety guarantee.

## Project References

See [architecture/Future_Architecture.md](architecture/Future_Architecture.md), [dataset/Dataset_Strategy.md](dataset/Dataset_Strategy.md), [data/README.md](data/README.md), and [src/aws/README.md](src/aws/README.md) for implementation and deployment boundaries.
See [docs/CLOUD_ARCHITECTURE.md](docs/CLOUD_ARCHITECTURE.md) for the production topology and local-versus-cloud storage plan.