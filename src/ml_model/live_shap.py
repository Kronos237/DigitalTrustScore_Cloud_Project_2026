"""SHAP explanations for the compatible live-phishing-v1 model."""

from pathlib import Path

import shap

from .live_model_inference import get_live_predictor


def explain_live_url(url: str, model_path: str, metadata_path: str) -> dict:
    predictor = get_live_predictor(model_path, metadata_path)
    row = predictor.transformed_row(url)
    transformed = predictor.pipeline.named_steps["preprocess"].transform(row)
    model = predictor.pipeline.named_steps["model"]
    values = shap.TreeExplainer(model).shap_values(transformed, check_additivity=True)
    class_values = values[1][0] if isinstance(values, list) else values[0, :, 1] if values.ndim == 3 else values[0]
    base_values = shap.TreeExplainer(model).expected_value
    base_value = float(base_values[1] if hasattr(base_values, "__len__") else base_values)
    features = [{"feature": name, "value": float(row.iloc[0][name]), "shap_value": float(value), "direction": "phishing" if value > 0 else "legitimate"} for name, value in zip(predictor.metadata["feature_names"], class_values)]
    toward_phishing = sorted((item for item in features if item["shap_value"] > 0), key=lambda item: item["shap_value"], reverse=True)[:5]
    toward_legitimate = sorted((item for item in features if item["shap_value"] < 0), key=lambda item: item["shap_value"])[:5]
    return {"schema_version": predictor.metadata["feature_schema_version"], "model_version": predictor.metadata["model_version"], "base_value": base_value, "top_phishing_features": toward_phishing, "top_legitimate_features": toward_legitimate, "all_features": features, "shap_sum_plus_base": base_value + float(class_values.sum())}