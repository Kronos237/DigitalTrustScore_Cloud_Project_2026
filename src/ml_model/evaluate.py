"""Actual classification metrics and experiment plots."""

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import ConfusionMatrixDisplay, accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score, RocCurveDisplay


def score_model(model, x_test, y_test, name: str) -> dict:
    predictions = model.predict(x_test)
    probabilities = model.predict_proba(x_test)[:, 1]
    return {"model": name, "accuracy": float(accuracy_score(y_test, predictions)), "precision": float(precision_score(y_test, predictions, zero_division=0)), "recall": float(recall_score(y_test, predictions, zero_division=0)), "f1": float(f1_score(y_test, predictions, zero_division=0)), "roc_auc": float(roc_auc_score(y_test, probabilities))}


def evaluate_model(model, x_test, y_test, name: str, experiments_dir: Path, feature_names: list[str]) -> dict:
    metrics = score_model(model, x_test, y_test, name)
    predictions = model.predict(x_test)
    probabilities = model.predict_proba(x_test)[:, 1]
    experiments_dir.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots()
    ConfusionMatrixDisplay(confusion_matrix(y_test, predictions), display_labels=["legitimate", "phishing"]).plot(ax=axis, colorbar=False)
    figure.tight_layout()
    figure.savefig(experiments_dir / f"confusion_matrix_{name.lower().replace(' ', '_')}.png", dpi=150)
    plt.close(figure)
    figure, axis = plt.subplots()
    RocCurveDisplay.from_predictions(y_test, probabilities, name=name, ax=axis)
    figure.tight_layout()
    figure.savefig(experiments_dir / f"roc_curve_{name.lower().replace(' ', '_')}.png", dpi=150)
    plt.close(figure)
    if hasattr(model[-1], "feature_importances_"):
        values = model[-1].feature_importances_
        order = np.argsort(values)[::-1]
        figure, axis = plt.subplots(figsize=(10, 6))
        axis.barh([feature_names[index] for index in order[::-1]], values[order[::-1]])
        axis.set_title(f"Feature importance: {name}")
        figure.tight_layout()
        figure.savefig(experiments_dir / "feature_importance.png", dpi=150)
        plt.close(figure)
    return metrics


def save_comparison(metrics: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(metrics[0]))
        writer.writeheader()
        writer.writerows(metrics)