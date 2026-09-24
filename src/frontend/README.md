# TrustGuard Frontend

This directory contains the React/Vite dashboard. It calls the existing Python API; it does not embed analysis results or secrets.

Planned capabilities:

- Input form for website or application URL
- Trust score display
- Explainability summary
- Result history and visual indicators

## Run locally

Start the backend from the repository root:

```text
.venv\Scripts\python.exe -m src.backend.api
```

In a second terminal:

```text
cd src/frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`. Vite proxies `/api` requests to the backend at `http://127.0.0.1:8000`.

Build and test:

```text
npm run build
npm test
```

The benchmark page uses the real `/api/ml/feature-importance` and `/api/ml/explanation/{sample_id}` endpoints. It labels those results separately from live trust analysis.
