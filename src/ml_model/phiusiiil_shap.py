"""SHAP explanations for the independent PhiUSIIL Random Forest benchmark."""

import csv
import json
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import shap

from .model_metadata import load_metadata
from .phiusiiil_loader import feature_columns, load_dataset, prepare_training_dataset
from sklearn.model_selection import train_test_split


class PhiusiilShapExplainer:
    def __init__(self, model_path: Path, metadata_path: Path, dataset_path: Path, sample_size: int = 1000):
        self.pipeline = joblib.load(model_path)
        self.metadata = load_metadata(metadata_path)
        if self.metadata.get("model_name") != "Random Forest":
            raise ValueError("PhiUSIIL SHAP requires the PhiUSIIL Random Forest artifact")
        frame, _ = prepare_training_dataset(load_dataset(dataset_path))
        features = feature_columns(frame)
        x = frame[features]
        y = frame["label"]
        _, self.x_test, _, self.y_test = train_test_split(x, y, test_size=0.2, random_state=42, stratify=y)
        self.feature_names = list(self.metadata["feature_names"])
        sample_count = min(sample_size, len(self.x_test))
        self.x_sample = self.x_test.sample(n=sample_count, random_state=42).sort_index()
        self.y_sample = self.y_test.loc[self.x_sample.index]
        self.transformed = self.pipeline.named_steps["preprocess"].transform(self.x_sample)
        self.model = self.pipeline.named_steps["model"]
        self.explainer = shap.TreeExplainer(self.model)
        self._values = None

    def shap_values(self):
        if self._values is None:
            values = self.explainer.shap_values(self.transformed, check_additivity=True)
            self._values = values[1] if isinstance(values, list) else values[:, :, 1] if values.ndim == 3 else values
        return self._values

    def explain_sample(self, sample_id: str) -> dict:
        if not sample_id.startswith("test-"):
            raise ValueError("PhiUSIIL sample IDs must use test-00000 format")
        index = int(sample_id.removeprefix("test-"))
        if index < 0 or index >= len(self.x_sample):
            raise ValueError(f"Unknown PhiUSIIL sample ID: {sample_id}")
        values = self.shap_values()[index]
        row = self.x_sample.iloc[index]
        transformed_row = self.transformed[index:index + 1]
        prediction = int(self.model.predict(transformed_row)[0])
        legitimate_probability = float(self.pipeline.predict_proba(self.x_sample.iloc[index:index + 1])[0][1])
        base_value = float(self.explainer.expected_value[1] if hasattr(self.explainer.expected_value, "__len__") else self.explainer.expected_value)
        contributions = [{"feature": name, "value": row[name].item() if hasattr(row[name], "item") else row[name], "shap_value": float(value), "direction": "legitimate" if value > 0 else "phishing"} for name, value in zip(self.feature_names, values)]
        toward_legitimate = sorted((item for item in contributions if item["shap_value"] > 0), key=lambda item: item["shap_value"], reverse=True)[:5]
        toward_phishing = sorted((item for item in contributions if item["shap_value"] < 0), key=lambda item: item["shap_value"])[:5]
        label = "legitimate" if prediction == 1 else "phishing"
        return {"sample_id": sample_id, "dataset": self.metadata["dataset_name"], "model": self.metadata["model_name"], "prediction": label, "legitimate_probability": legitimate_probability, "phishing_probability": 1 - legitimate_probability, "base_value_legitimate": base_value, "shap_sum_plus_base": base_value + float(values.sum()), "top_legitimate_features": toward_legitimate, "top_phishing_features": toward_phishing, "all_features": contributions, "actual_label": "legitimate" if int(self.y_sample.iloc[index]) == 1 else "phishing", "scope": "PhiUSIIL benchmark model; separate from UCI and live trust analysis"}

    def global_importance(self, output_dir: Path | None = None) -> dict:
        values = self.shap_values()
        mean_absolute = abs(values).mean(axis=0)
        ranked = [{"rank": index + 1, "feature": self.feature_names[feature_index], "mean_absolute_shap_value": float(mean_absolute[feature_index])} for index, feature_index in enumerate(mean_absolute.argsort()[::-1])]
        result = {"dataset": self.metadata["dataset_name"], "model": self.metadata["model_name"], "model_version": self.metadata["model_version"], "sample_count": int(len(self.x_sample)), "test_rows": int(len(self.x_test)), "feature_count": len(self.feature_names), "importance": ranked, "scope": "PhiUSIIL benchmark test sample; separate from UCI and live trust analysis"}
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
            with (output_dir / "shap_feature_importance.csv").open("w", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=["rank", "feature", "mean_absolute_shap_value"])
                writer.writeheader()
                writer.writerows(ranked)
            plt.figure(figsize=(10, 8))
            shap.summary_plot(values, self.transformed, feature_names=self.feature_names, plot_type="bar", show=False)
            plt.tight_layout()
            plt.savefig(output_dir / "shap_summary_bar.png", dpi=150, bbox_inches="tight")
            plt.close()
            plt.figure(figsize=(10, 8))
            shap.summary_plot(values, self.transformed, feature_names=self.feature_names, show=False)
            plt.tight_layout()
            plt.savefig(output_dir / "shap_summary_beeswarm.png", dpi=150, bbox_inches="tight")
            plt.close()
            (output_dir / "shap_global_importance.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        return result