"""Independent PhiUSIIL model comparison and artifact generation."""

import argparse
import json
from datetime import date
from pathlib import Path

import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from .evaluate import evaluate_model, save_comparison, score_model
from .model_metadata import save_metadata
from .phiusiiil_loader import audit_dataset, feature_columns, load_dataset, prepare_training_dataset
from .preprocessing import numeric_preprocessor


def train(dataset_path: Path, models_dir: Path, experiments_dir: Path) -> dict:
    raw = load_dataset(dataset_path)
    raw_audit = audit_dataset(raw)
    frame, cleaning_audit = prepare_training_dataset(raw)
    features = feature_columns(frame)
    x = frame[features]
    y = frame["label"]
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42, stratify=y)
    candidates = {
        "Logistic Regression": Pipeline([("preprocess", numeric_preprocessor(scale=True)), ("model", LogisticRegression(max_iter=1000, random_state=42))]),
        "Random Forest": Pipeline([("preprocess", numeric_preprocessor()), ("model", RandomForestClassifier(n_estimators=300, random_state=42, class_weight="balanced", n_jobs=-1))]),
    }
    x_fit, x_validation, y_fit, y_validation = train_test_split(x_train, y_train, test_size=0.2, random_state=42, stratify=y_train)
    validation_metrics = []
    test_metrics = []
    trained = {}
    for name, candidate in candidates.items():
        candidate.fit(x_fit, y_fit)
        validation_metrics.append(score_model(candidate, x_validation, y_validation, name))
        candidate.fit(x_train, y_train)
        test_metrics.append(evaluate_model(candidate, x_test, y_test, name, experiments_dir, features))
        trained[name] = candidate
    selected_validation = max(validation_metrics, key=lambda result: (result["roc_auc"], result["f1"]))
    selected_name = selected_validation["model"]
    selected_test = next(result for result in test_metrics if result["model"] == selected_name)
    models_dir.mkdir(parents=True, exist_ok=True)
    artifact = models_dir / "random_forest.joblib" if selected_name == "Random Forest" else models_dir / "selected_model.joblib"
    joblib.dump(trained[selected_name], artifact)
    metadata = {"loaded": True, "experiment": "phiusiiil", "model_name": selected_name, "model_version": f"phiusiiil-{date.today().isoformat()}", "dataset_name": "PhiUSIIL Phishing URL Dataset", "dataset_source": "UCI Machine Learning Repository dataset 967", "dataset_path": str(dataset_path), "raw_audit": raw_audit, "cleaning_audit": cleaning_audit, "feature_names": features, "feature_count": len(features), "target": "label (1=legitimate, 0=phishing)", "random_state": 42, "split": {"test_size": 0.2, "validation_fraction_of_training": 0.2, "stratified": True, "train_rows": int(len(x_train)), "validation_rows": int(len(x_validation)), "test_rows": int(len(x_test))}, "selection_metrics_validation": validation_metrics, "selected_model_selection_metrics": selected_validation, "metrics": selected_test, "all_model_metrics": test_metrics, "artifact": str(artifact)}
    save_metadata(metadata, models_dir / "model_metadata.json")
    save_comparison(test_metrics, experiments_dir / "model_comparison.csv")
    return metadata


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", type=Path, default=Path("data/raw/phiusiiil/phiusiil-phishing-url-dataset.zip"), nargs="?")
    parser.add_argument("--models-dir", type=Path, default=Path("models/phiusiiil"))
    parser.add_argument("--experiments-dir", type=Path, default=Path("experiments/phiusiiil"))
    arguments = parser.parse_args()
    print(json.dumps(train(arguments.dataset, arguments.models_dir, arguments.experiments_dir), indent=2))