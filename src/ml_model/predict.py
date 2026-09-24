"""Load a trained benchmark model without confusing it with live trust signals."""

from pathlib import Path

import joblib
import pandas as pd

from .model_metadata import load_metadata


class BenchmarkPredictor:
    def __init__(self, model_path: Path, metadata_path: Path | None = None):
        self.pipeline = joblib.load(model_path)
        self.metadata = load_metadata(metadata_path) if metadata_path else None

    def predict(self, features: dict[str, float]) -> dict:
        expected = self.metadata["feature_names"] if self.metadata else list(self.pipeline.feature_names_in_)
        if any(name not in features for name in expected):
            return {"status": "unavailable", "probability": None, "message": "ML prediction unavailable for live feature set"}
        values = pd.DataFrame([{name: features[name] for name in expected}])
        probability = float(self.pipeline.predict_proba(values)[0][1])
        return {"status": "observed", "probability": probability, "label": str(self.pipeline.predict(values)[0]), "model_version": self.metadata.get("model_version") if self.metadata else None}