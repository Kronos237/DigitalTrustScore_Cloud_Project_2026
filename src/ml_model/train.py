"""Train, compare, evaluate, and persist real UCI benchmark models."""

import argparse
import json
from datetime import date
from pathlib import Path

import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from .data_loader import load_dataset, prepare_training_dataset
from .evaluate import evaluate_model, save_comparison, score_model
from .model_metadata import save_metadata
from .preprocessing import numeric_preprocessor, split_dataset


def train(dataset_path: Path, models_dir: Path, experiments_dir: Path) -> dict:
    raw_frame = load_dataset(dataset_path)
    frame, duplicate_audit = prepare_training_dataset(raw_frame)
    feature_names = [column for column in frame.columns if column != "label"]
    x_train, x_test, y_train, y_test = split_dataset(frame)
    candidates = {
        "Logistic Regression": Pipeline([("preprocess", numeric_preprocessor(scale=True)), ("model", LogisticRegression(max_iter=1000, random_state=42))]),
        "Random Forest": Pipeline([("preprocess", numeric_preprocessor()), ("model", RandomForestClassifier(n_estimators=300, random_state=42, class_weight="balanced", n_jobs=-1))]),
    }
    try:
        from xgboost import XGBClassifier
        candidates["XGBoost"] = Pipeline([("preprocess", numeric_preprocessor()), ("model", XGBClassifier(n_estimators=300, max_depth=6, learning_rate=0.08, subsample=0.9, colsample_bytree=0.9, random_state=42, eval_metric="logloss"))])
    except (ImportError, ValueError):
        pass
    x_fit, x_validation, y_fit, y_validation = train_test_split(x_train, y_train, test_size=0.2, random_state=42, stratify=y_train)
    validation_results = []
    results = []
    trained = {}
    for name, model in candidates.items():
        model.fit(x_fit, y_fit)
        validation_results.append(score_model(model, x_validation, y_validation, name))
        model.fit(x_train, y_train)
        results.append(evaluate_model(model, x_test, y_test, name, experiments_dir, feature_names))
        trained[name] = model
    save_comparison(results, experiments_dir / "model_comparison.csv")
    selected_validation_metrics = max(validation_results, key=lambda result: (result["roc_auc"], result["f1"]))
    selected_name = selected_validation_metrics["model"]
    selected_metrics = next(result for result in results if result["model"] == selected_name)
    models_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = models_dir / "random_forest.joblib" if selected_name == "Random Forest" else models_dir / "selected_model.joblib"
    joblib.dump(trained[selected_name], artifact_path)
    metadata = {"loaded": True, "model_name": selected_name, "model_version": f"benchmark-{date.today().isoformat()}", "dataset_name": "UCI Phishing Websites", "dataset_path": str(dataset_path), "duplicate_audit": duplicate_audit, "feature_count": len(feature_names), "feature_names": feature_names, "target": "label (1=phishing, 0=legitimate)", "training_date": date.today().isoformat(), "random_state": 42, "split": {"test_size": 0.2, "validation_fraction_of_training": 0.2, "stratified": True, "train_rows": int(len(x_train)), "validation_rows": int(len(x_validation)), "test_rows": int(len(x_test))}, "selection_metrics_validation": validation_results, "selected_model_selection_metrics": selected_validation_metrics, "metrics": selected_metrics, "all_model_metrics": results, "artifact": str(artifact_path)}
    save_metadata(metadata, models_dir / "model_metadata.json")
    return metadata


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--models-dir", type=Path, default=Path("models"))
    parser.add_argument("--experiments-dir", type=Path, default=Path("experiments"))
    arguments = parser.parse_args()
    print(json.dumps(train(arguments.dataset, arguments.models_dir, arguments.experiments_dir), indent=2))