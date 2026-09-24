# Backend

Backend implementation is developed in Python. `fastapi_app.py` is the production-shaped server; the standard-library server remains a local fallback. Analysis history is accessed through the SQLAlchemy repository and selected with `DATABASE_URL`.

Planned modules:

- API
- Feature Extraction
- Trust Prediction
- Explainable AI

This folder will later contain the application logic that connects the UI, dataset pipeline, and model outputs.

Run from the repository root with `.venv\Scripts\python.exe -m src.backend.api` for the fallback server. For the deployment-shaped server, run `uvicorn src.backend.fastapi_app:app --host 0.0.0.0 --port 8000`. Initialize persistence with `.venv\Scripts\python.exe -m src.database.init_db`.
