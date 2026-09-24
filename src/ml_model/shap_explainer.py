"""SHAP explanations for the persisted benchmark Random Forest only."""

import csv
import json
from pathlib import Path

import joblib
import matplotlib
import pandas as pd
import shap

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .data_loader import load_dataset, prepare_training_dataset
from .model_metadata import load_metadata
from .preprocessing import split_dataset


class BenchmarkShapExplainer:
    """Explain test-set predictions from the exact persisted benchmark artifact."""

    def __init__(self, model_path: Path, metadata_path: Path, dataset_path: Path):
        self.model_path = model_path
        self.metadata_path = metadata_path
        self.dataset_path = dataset_path
        self.pipeline = joblib.load(model_path)
        self.metadata = load_metadata(metadata_path)
        if self.metadata.get("model_name") != "Random Forest":
            raise ValueError("SHAP explainer requires the persisted Random Forest artifact")
        frame, _ = prepare_training_dataset(load_dataset(dataset_path))
        _, self.x_test, _, self.y_test = split_dataset(frame)
        self.feature_names = list(self.metadata["feature_names"])
        self.preprocessor = self.pipeline.named_steps["preprocess"]
        self.model = self.pipeline.named_steps["model"]
        self.transformed_test = self.preprocessor.transform(self.x_test)
        self.explainer = shap.TreeExplainer(self.model)
        self._test_shap_values = None

    def _class_one_values(self, values):
        if isinstance(values, list):
            return values[1]
        if values.ndim == 3:
            return values[:, :, 1]
        return values

    def test_shap_values(self):
        if self._test_shap_values is None:
            self._test_shap_values = self._class_one_values(self.explainer.shap_values(self.transformed_test, check_additivity=True))
        return self._test_shap_values

    def _sample_index(self, sample_id: str) -> int:
        if not sample_id.startswith("test-"):
            raise ValueError("Sample IDs must use the benchmark test-00000 format")
        try:
            index = int(sample_id.removeprefix("test-"))
        except ValueError as error:
            raise ValueError("Invalid benchmark sample ID") from error
        if index < 0 or index >= len(self.x_test):
            raise ValueError(f"Unknown benchmark sample ID: {sample_id}")
        return index

    def explain_sample(self, sample_id: str) -> dict:
        index = self._sample_index(sample_id)
        values = self.test_shap_values()[index]
        row = self.x_test.iloc[index]
        transformed_row = self.transformed_test[index:index + 1]
        prediction = int(self.model.predict(transformed_row)[0])
        probability = float(self.pipeline.predict_proba(self.x_test.iloc[index:index + 1])[0][1])
        base_value = float(self.explainer.expected_value[1] if hasattr(self.explainer.expected_value, "__len__") else self.explainer.expected_value)
        contributions = [{"feature": name, "value": row[name].item() if hasattr(row[name], "item") else row[name], "shap_value": float(value), "direction": "phishing" if value > 0 else "legitimate"} for name, value in zip(self.feature_names, values)]
        positive = sorted((item for item in contributions if item["shap_value"] > 0), key=lambda item: item["shap_value"], reverse=True)
        negative = sorted((item for item in contributions if item["shap_value"] < 0), key=lambda item: item["shap_value"])
        label = "phishing" if prediction == 1 else "legitimate"
        top_positive = positive[:5]
        top_negative = negative[:5]
        explanation = f"The benchmark Random Forest predicts {label} with phishing probability {probability:.4f}. The base value for the phishing class is {base_value:.4f}. "
        if top_positive:
            explanation += "The strongest features increasing phishing risk are " + ", ".join(item["feature"] for item in top_positive) + ". "
        if top_negative:
            explanation += "The strongest features decreasing phishing risk are " + ", ".join(item["feature"] for item in top_negative) + "."
        return {"sample_id": sample_id, "dataset": self.metadata["dataset_name"], "model": self.metadata["model_name"], "model_version": self.metadata["model_version"], "prediction": label, "probability": probability, "base_value": base_value, "shap_sum_plus_base": base_value + float(values.sum()), "top_positive_features": top_positive, "top_negative_features": top_negative, "all_features": contributions, "actual_label": "phishing" if int(self.y_test.iloc[index]) == 1 else "legitimate", "explanation": explanation, "scope": "benchmark UCI phishing-risk model; not the live Digital Trust Score"}

    def global_importance(self, experiments_dir: Path | None = None) -> dict:
        values = self.test_shap_values()
        mean_absolute = abs(values).mean(axis=0)
        ranked = [{"rank": index + 1, "feature": self.feature_names[feature_index], "mean_absolute_shap_value": float(mean_absolute[feature_index])} for index, feature_index in enumerate(mean_absolute.argsort()[::-1])]
        result = {"dataset": self.metadata["dataset_name"], "model": self.metadata["model_name"], "model_version": self.metadata["model_version"], "sample_count": int(len(self.x_test)), "feature_count": len(self.feature_names), "importance": ranked, "scope": "benchmark test-set explanations; not live trust features"}
        if experiments_dir:
            experiments_dir.mkdir(parents=True, exist_ok=True)
            with (experiments_dir / "shap_feature_importance.csv").open("w", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=["rank", "feature", "mean_absolute_shap_value"])
                writer.writeheader()
                writer.writerows(ranked)
            plt.figure(figsize=(10, 8))
            shap.summary_plot(values, self.transformed_test, feature_names=self.feature_names, plot_type="bar", show=False)
            plt.tight_layout()
            plt.savefig(experiments_dir / "shap_summary_bar.png", dpi=150, bbox_inches="tight")
            plt.close()
            plt.figure(figsize=(10, 8))
            shap.summary_plot(values, self.transformed_test, feature_names=self.feature_names, show=False)
            plt.tight_layout()
            plt.savefig(experiments_dir / "shap_summary_beeswarm.png", dpi=150, bbox_inches="tight")
            plt.close()
            (experiments_dir / "shap_global_importance.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        return result