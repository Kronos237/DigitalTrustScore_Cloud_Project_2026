"""Generate real global SHAP artifacts from the persisted benchmark model."""

from pathlib import Path

from .shap_explainer import BenchmarkShapExplainer


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    explainer = BenchmarkShapExplainer(root / "models" / "random_forest.joblib", root / "models" / "model_metadata.json", root / "data" / "raw" / "phishing+websites.zip")
    print(explainer.global_importance(root / "experiments"))