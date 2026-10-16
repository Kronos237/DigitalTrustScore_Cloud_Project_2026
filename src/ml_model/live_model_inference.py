"""Cached live-phishing-v1 inference using the shared URL extractor."""

from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd

from .live_url_features import LIVE_MODEL_FEATURES, LIVE_MODEL_SCHEMA_VERSION, extract_live_url_features
from .model_metadata import load_metadata


class LiveRiskPredictor:
    def __init__(self, model_path: Path, metadata_path: Path):
        self.pipeline = joblib.load(model_path)
        self.metadata = load_metadata(metadata_path)
        if self.metadata.get("feature_schema_version") != LIVE_MODEL_SCHEMA_VERSION:
            raise ValueError("Live model feature schema is incompatible")
        if self.metadata.get("feature_names") != list(LIVE_MODEL_FEATURES):
            raise ValueError("Live model feature ordering is incompatible")

    def transformed_row(self, url: str):
        values = extract_live_url_features(url)
        return pd.DataFrame([[values[name] for name in LIVE_MODEL_FEATURES]], columns=LIVE_MODEL_FEATURES)

    def predict(self, url: str) -> dict:
        row = self.transformed_row(url)
        prediction = int(self.pipeline.predict(row)[0])
        probabilities = self.pipeline.predict_proba(row)[0]
        phishing_probability = float(probabilities[list(self.pipeline.classes_).index(1)])
        return {"status": "observed", "prediction": "phishing" if prediction == 1 else "legitimate", "phishing_probability": phishing_probability, "model_version": self.metadata["model_version"], "schema_version": LIVE_MODEL_SCHEMA_VERSION}


@lru_cache(maxsize=1)
def get_live_predictor(model_path: str, metadata_path: str) -> LiveRiskPredictor:
    return LiveRiskPredictor(Path(model_path), Path(metadata_path))