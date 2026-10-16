"""Train a URL-only phishing model using the same extractor as live inference."""

import argparse
import json
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline

from .evaluate import evaluate_model, save_comparison, score_model
from .live_url_features import LIVE_MODEL_FEATURES, LIVE_MODEL_SCHEMA_VERSION, extract_live_url_features
from .model_metadata import save_metadata
from .phiusiiil_loader import load_dataset
from .preprocessing import numeric_preprocessor


def _prepare_dataset(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    if "URL" not in frame or "label" not in frame:
        raise ValueError("PhiUSIIL must contain raw URL and label columns")
    rows = []
    invalid = 0
    for index, row in frame[["URL", "label"]].iterrows():
        try:
            features = extract_live_url_features(row["URL"])
            raw_url = row["URL"]
            domain = (urlsplit(raw_url if "://" in raw_url else f"https://{raw_url}").hostname or "").lower()
            rows.append({"source_index": int(index), "url": raw_url, "domain_group": domain, "label": int(row["label"]), **features})
        except (ValueError, UnicodeError):
            invalid += 1
    prepared = pd.DataFrame(rows)
    prepared["phishing_label"] = (prepared["label"] == 0).astype("int8")
    feature_columns = list(LIVE_MODEL_FEATURES)
    url_conflicts = prepared.groupby("url")["phishing_label"].nunique() > 1
    conflict_urls = set(url_conflicts[url_conflicts].index)
    without_conflicts = prepared[~prepared["url"].isin(conflict_urls)].copy()
    deduped = without_conflicts.drop_duplicates(subset=["url"]).reset_index(drop=True)
    audit = {"raw_rows": int(len(frame)), "invalid_url_rows": invalid, "duplicate_urls": int(prepared.duplicated("url").sum()), "conflicting_urls": len(conflict_urls), "conflicting_rows_removed": int(prepared["url"].isin(conflict_urls).sum()), "duplicate_rows_removed": int(len(without_conflicts) - len(deduped)), "prepared_rows": int(len(deduped)), "class_distribution": {str(key): int(value) for key, value in deduped["phishing_label"].value_counts().sort_index().items()}, "unique_domains": int(deduped["domain_group"].nunique()), "feature_schema_version": LIVE_MODEL_SCHEMA_VERSION, "features": feature_columns, "label_mapping": "PhiUSIIL label 0 -> phishing_label 1; PhiUSIIL label 1 -> phishing_label 0"}
    return deduped, audit


def _group_split(features, labels, groups, test_size, random_state):
    splitter = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=random_state)
    train_index, test_index = next(splitter.split(features, labels, groups))
    return features.iloc[train_index], features.iloc[test_index], labels.iloc[train_index], labels.iloc[test_index], groups.iloc[train_index], groups.iloc[test_index]


def train(dataset_path: Path, models_dir: Path, experiments_dir: Path) -> dict:
    raw = load_dataset(dataset_path)
    frame, audit = _prepare_dataset(raw)
    x = frame[list(LIVE_MODEL_FEATURES)]
    y = frame["phishing_label"]
    groups = frame["domain_group"]
    x_train, x_test, y_train, y_test, groups_train, groups_test = _group_split(x, y, groups, 0.2, 42)
    x_fit, x_validation, y_fit, y_validation, groups_fit, groups_validation = _group_split(x_train, y_train, groups_train, 0.2, 43)
    if set(y_train.unique()) != {0, 1} or set(y_validation.unique()) != {0, 1} or set(y_test.unique()) != {0, 1}:
        raise ValueError("Domain-group split does not preserve both classes; collect more diverse labelled domains")
    if set(groups_train) & set(groups_test) or set(groups_fit) & set(groups_validation):
        raise AssertionError("Domain leakage detected across split")
    candidates = {"Logistic Regression": Pipeline([("preprocess", numeric_preprocessor(scale=True)), ("model", LogisticRegression(max_iter=1000, random_state=42))]), "Random Forest": Pipeline([("preprocess", numeric_preprocessor()), ("model", RandomForestClassifier(n_estimators=300, random_state=42, class_weight="balanced", n_jobs=-1))])}
    validation_metrics, test_metrics, trained = [], [], {}
    for name, candidate in candidates.items():
        candidate.fit(x_fit, y_fit)
        validation_metrics.append(score_model(candidate, x_validation, y_validation, name))
        candidate.fit(x_train, y_train)
        test_metrics.append(evaluate_model(candidate, x_test, y_test, name, experiments_dir, list(LIVE_MODEL_FEATURES)))
        trained[name] = candidate
    selected_validation = max(validation_metrics, key=lambda result: (result["roc_auc"], result["f1"]))
    selected_name = selected_validation["model"]
    selected_test = next(result for result in test_metrics if result["model"] == selected_name)
    models_dir.mkdir(parents=True, exist_ok=True)
    artifact = models_dir / "random_forest.joblib" if selected_name == "Random Forest" else models_dir / "selected_model.joblib"
    joblib.dump(trained[selected_name], artifact)
    metadata = {"loaded": True, "experiment": "live-url-phishing", "model_name": selected_name, "model_version": f"live-phishing-{date.today().isoformat()}", "dataset_name": "PhiUSIIL URL strings with URL-only recomputation", "dataset_path": str(dataset_path), "feature_schema_version": LIVE_MODEL_SCHEMA_VERSION, "feature_names": list(LIVE_MODEL_FEATURES), "feature_count": len(LIVE_MODEL_FEATURES), "label_mapping": audit["label_mapping"], "audit": audit, "split": {"strategy": "domain_group", "test_fraction": 0.2, "validation_fraction_of_training": 0.2, "train_rows": int(len(x_train)), "validation_rows": int(len(x_validation)), "test_rows": int(len(x_test)), "train_domains": int(groups_train.nunique()), "validation_domains": int(groups_validation.nunique()), "test_domains": int(groups_test.nunique()), "random_state_outer": 42, "random_state_validation": 43}, "selection_metrics_validation": validation_metrics, "selected_model_selection_metrics": selected_validation, "metrics": selected_test, "all_model_metrics": test_metrics, "artifact": str(artifact)}
    save_metadata(metadata, models_dir / "model_metadata.json")
    save_comparison(test_metrics, experiments_dir / "model_comparison.csv")
    (experiments_dir / "live_url_confusion_matrix.json").write_text(json.dumps(confusion_matrix(y_test, trained[selected_name].predict(x_test)).tolist()), encoding="utf-8")
    return metadata


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", type=Path, default=Path("data/raw/phiusiiil/phiusiil-phishing-url-dataset.zip"), nargs="?")
    parser.add_argument("--models-dir", type=Path, default=Path("models/live-phishing"))
    parser.add_argument("--experiments-dir", type=Path, default=Path("experiments/live-phishing"))
    arguments = parser.parse_args()
    print(json.dumps(train(arguments.dataset, arguments.models_dir, arguments.experiments_dir), indent=2))