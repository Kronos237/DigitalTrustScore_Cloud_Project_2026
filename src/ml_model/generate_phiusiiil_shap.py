"""Generate separate PhiUSIIL SHAP artifacts from the saved Random Forest."""

from pathlib import Path

from .phiusiiil_shap import PhiusiilShapExplainer


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    explainer = PhiusiilShapExplainer(root / "models" / "phiusiiil" / "random_forest.joblib", root / "models" / "phiusiiil" / "model_metadata.json", root / "data" / "raw" / "phiusiiil" / "phiusiil-phishing-url-dataset.zip")
    print(explainer.global_importance(root / "experiments" / "phiusiiil"))