"""Runtime configuration loaded from environment variables."""

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
try:
	from dotenv import load_dotenv
except ImportError:  # pragma: no cover - requirements.txt includes python-dotenv
	load_dotenv = None

if load_dotenv is not None:
	load_dotenv(PROJECT_ROOT / ".env")

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{(PROJECT_ROOT / 'results' / 'trustguard.db').as_posix()}")
MODEL_VERSION = os.getenv("MODEL_VERSION", "prototype-v2")
MODEL_METADATA_PATH = Path(os.getenv("MODEL_METADATA_PATH", str(PROJECT_ROOT / "models" / "model_metadata.json")))
LIVE_MODEL_ARTIFACT_PATH = Path(os.getenv("LIVE_MODEL_ARTIFACT_PATH", str(PROJECT_ROOT / "models" / "live-phishing" / "random_forest.joblib")))
LIVE_MODEL_METADATA_PATH = Path(os.getenv("LIVE_MODEL_METADATA_PATH", str(PROJECT_ROOT / "models" / "live-phishing" / "model_metadata.json")))
MODEL_ARTIFACT_PATH = Path(os.getenv("MODEL_ARTIFACT_PATH", str(PROJECT_ROOT / "models" / "random_forest.joblib")))
DATASET_PATH = Path(os.getenv("DATASET_PATH", str(PROJECT_ROOT / "data" / "raw" / "phishing+websites.zip")))
EXPERIMENTS_PATH = Path(os.getenv("EXPERIMENTS_PATH", str(PROJECT_ROOT / "experiments")))
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"
REQUEST_TIMEOUT_SECONDS = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "8"))
MAX_RESPONSE_BYTES = int(os.getenv("MAX_RESPONSE_BYTES", "1000000"))
FRONTEND_API_URL = os.getenv("FRONTEND_API_URL", "")
CORS_ORIGINS = tuple(origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://127.0.0.1:5173,http://localhost:5173").split(",") if origin.strip())
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
LIVE_ML_ENABLED = os.getenv("LIVE_ML_ENABLED", "false").lower() == "true"
VIRUSTOTAL_API_KEY = os.getenv("VIRUSTOTAL_API_KEY", "")
REPUTATION_TIMEOUT_SECONDS = float(os.getenv("REPUTATION_TIMEOUT_SECONDS", "5"))