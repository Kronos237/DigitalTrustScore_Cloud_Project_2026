# Machine Learning Model

This folder will contain:

- Dataset preprocessing
- Model training
- Prediction
- Explainability

Implementation will begin after the literature survey and dataset finalization.

The current backend contains a transparent prototype scoring engine so the end-to-end workflow can be tested before dataset selection. It is not a trained machine-learning claim. `train.py` provides the real Random Forest training path once a licensed CSV matching `feature_schema.py` is available:

```text
python -m src.ml_model.data_loader --inspect data/raw/phishing+websites.zip
python -m src.ml_model.train data/raw/phishing+websites.zip --models-dir models --experiments-dir experiments
```

The current actual run selected Random Forest over Logistic Regression using validation ROC-AUC then F1. Its metrics are stored in `models/model_metadata.json` and `experiments/model_comparison.csv`; no placeholder metrics are used. SHAP explains this persisted benchmark artifact on the corrected UCI test set:

```text
python -m src.ml_model.generate_shap_artifacts
```

It does not map live TrustGuard features into the benchmark model and does not explain the complete Digital Trust Score.
