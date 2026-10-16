"""Reproduce live URL model diagnostics without visiting any URLs."""

import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.metrics import average_precision_score, classification_report, confusion_matrix
from sklearn.model_selection import GroupShuffleSplit

from .live_url_features import LIVE_MODEL_FEATURES, extract_live_url_features
from .live_shap import explain_live_url
from .live_url_train import _prepare_dataset
from .phiusiiil_loader import load_dataset
from .model_metadata import load_metadata


LEGITIMATE_REGRESSION_URLS = ("https://example.com", "https://www.google.com", "https://www.wikipedia.org", "https://www.microsoft.com")


def _test_split(frame):
    x = frame[list(LIVE_MODEL_FEATURES)]
    y = frame["phishing_label"]
    groups = frame["domain_group"]
    train_index, test_index = next(GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42).split(x, y, groups))
    return x.iloc[test_index], y.iloc[test_index]


def diagnose(dataset_path: Path, model_path: Path, metadata_path: Path, output_path: Path) -> dict:
    frame, audit = _prepare_dataset(load_dataset(dataset_path))
    x_test, y_test = _test_split(frame)
    model = joblib.load(model_path)
    predictions = model.predict(x_test)
    probabilities = model.predict_proba(x_test)[:, list(model.named_steps["model"].classes_).index(1)]
    fraction_positive, fraction_mean = calibration_curve(y_test, probabilities, n_bins=10, strategy="quantile")
    regression = []
    for url in LEGITIMATE_REGRESSION_URLS:
        row = pd.DataFrame([[extract_live_url_features(url)[name] for name in LIVE_MODEL_FEATURES]], columns=LIVE_MODEL_FEATURES)
        row_probabilities = model.predict_proba(row)[0]
        phishing_index = list(model.named_steps["model"].classes_).index(1)
        shap_result = explain_live_url(url, str(model_path), str(metadata_path))
        regression.append({"url": url, "features": row.iloc[0].to_dict(), "prediction": "phishing" if int(model.predict(row)[0]) == 1 else "legitimate", "phishing_probability": float(row_probabilities[phishing_index]), "top_phishing_features": shap_result["top_phishing_features"], "top_legitimate_features": shap_result["top_legitimate_features"], "shap_sum_plus_base": shap_result["shap_sum_plus_base"]})
    report = {"model_classes": [int(value) for value in model.named_steps["model"].classes_], "label_semantics": "phishing_label=1; legitimate_label=0", "audit": audit, "test_rows": int(len(x_test)), "confusion_matrix_labels": ["legitimate", "phishing"], "confusion_matrix": confusion_matrix(y_test, predictions).tolist(), "classification_report": classification_report(y_test, predictions, target_names=["legitimate", "phishing"], output_dict=True), "average_precision": float(average_precision_score(y_test, probabilities)), "calibration": {"mean_predicted_probability": [float(value) for value in fraction_mean], "fraction_positive": [float(value) for value in fraction_positive]}, "legitimate_regression": regression, "model_limitations": ["Metrics are PhiUSIIL URL-string benchmark results, not arbitrary-web accuracy.", "The dataset's URL distributions and label collection process may be source-specific.", "example.com is a demonstrated false-positive risk for this model."]}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    result = diagnose(root / "data/raw/phiusiiil/phiusiil-phishing-url-dataset.zip", root / "models/live-phishing/random_forest.joblib", root / "models/live-phishing/model_metadata.json", root / "experiments/live-phishing/diagnostics.json")
    print(json.dumps(result, indent=2))