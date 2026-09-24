# Benchmark Experiment Validation

Validation was run against the downloaded UCI Phishing Websites archive on 2026-09-24. The report below is generated from the current dataset and training code; it is not a claim about arbitrary modern websites.

## Duplicate Analysis

- Raw rows: `2,456`.
- Exact duplicate rows removed by `DataFrame.duplicated()` across all 30 features and the normalized label: `740` (`30.130293%` of raw rows).
- Duplicate feature-vector rows: `750` when the label is excluded.
- Conflicting feature vectors: `10` unique feature vectors appear with both labels, covering `34` rows.
- Because those labels are ambiguous, all 34 rows belonging to conflicting vectors are excluded before deduplication.
- Of the remaining rows, `726` repeated feature-vector rows are removed, leaving `1,696` unambiguous unique feature vectors.
- Prepared class distribution: `890` legitimate (`0`) and `806` phishing (`1`).

Therefore, the original statement “740 duplicates” was accurate only for exact full-row duplicates. It was insufficient for leakage validation because identical features with conflicting labels also existed.

## Leakage Check

The corrected pipeline now:

1. Loads and normalizes the target.
2. Finds feature-vector groups with conflicting labels and excludes those rows.
3. Removes duplicate rows by all benchmark features.
4. Splits the prepared data with `test_size=0.2`, `random_state=42`, and stratification.
5. Fits imputation and scaling only inside each model's scikit-learn `Pipeline` on training data.
6. Excludes `label` from the feature matrix.
7. Selects the model using ROC-AUC then F1 on a validation split carved from the training partition (`272` rows), refits that selected model on all `1,356` training rows, and evaluates the untouched test split once. The test set is not used for model selection.

The resulting split contains `1,356` training rows and `340` test rows. The independent audit found `0` identical feature vectors shared across train and test.

No target-derived column enters preprocessing or model input. There is no fitted preprocessing object created before the split.

## Baseline Methodology

Logistic Regression and Random Forest use the same prepared rows, same outer stratified split, same seed, and same target. The outer split is `1,356` training rows and `340` test rows; model selection uses a stratified `80/20` split inside the training rows. Logistic Regression uses median imputation followed by standardization. Random Forest uses median imputation without scaling. Both transformations are fitted within their respective pipelines.

## Corrected Metrics

These are actual held-out test metrics from the corrected run:

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
| --- | ---: | ---: | ---: | ---: | ---: |
| Logistic Regression | 0.952941 | 0.945122 | 0.956790 | 0.950920 | 0.988660 |
| Random Forest | 0.979412 | 0.958580 | 1.000000 | 0.978852 | 0.996862 |

Random Forest was retained because it had the highest validation ROC-AUC (`0.986827`) and F1 (`0.958175`) under the declared selection rule. The final test metrics below were not used for that choice. Complete values and confusion/ROC plots are stored in `models/model_metadata.json`, `experiments/model_comparison.csv`, and `experiments/`.

## Metric Interpretation

- **Accuracy:** fraction of all test records classified correctly.
- **Precision:** among records predicted as phishing, fraction that were phishing in the benchmark labels.
- **Recall:** among benchmark phishing records, fraction detected by the model.
- **F1:** harmonic mean of precision and recall; it balances the two when both matter.
- **ROC-AUC:** ranking discrimination across classification thresholds; `0.5` is roughly random ranking and `1.0` is perfect separation on this test set.

These values describe this deduplicated UCI benchmark split only. They are not real-world accuracy estimates for arbitrary current websites, cloud applications, or future phishing campaigns.

## Generalization Limits

UCI is a historical benchmark with dataset-specific feature definitions and collection conditions. Websites, hosting patterns, certificate practices, and phishing techniques evolve. Live TrustGuard indicators such as TLS details, headers, response timing, transparency pages, and reputation availability are not identical to the UCI features. The benchmark model is therefore not used to make live website predictions. The API explicitly returns `ML prediction unavailable for live feature set` until a validated feature adapter is developed and evaluated.

The benchmark also has potential sampling bias, duplicate-derived dependence, label ambiguity, concept drift, and a single held-out split. A future study should use a locked external test set or cross-validation, temporal evaluation, calibration analysis, and a documented mapping from live evidence to benchmark features.

## SHAP Explainability

SHAP is applied to the actual persisted `models/random_forest.joblib` artifact after its fitted preprocessing step. Explanations use the corrected 340-row benchmark test set and all 30 UCI feature names. The class-1 SHAP output explains the model's phishing probability.

Global outputs are mean absolute SHAP values ranked across the test set. Generated artifacts are `experiments/shap_summary_bar.png`, `experiments/shap_summary_beeswarm.png`, `experiments/shap_global_importance.json`, and `experiments/shap_feature_importance.csv`.

For local explanations, the API returns the base value, phishing probability, every feature's SHAP value, top features increasing phishing output, and top features decreasing phishing output. Real sample `test-00000` was predicted `legitimate` with phishing probability `0.0066667`, base value `0.5002483`, and reconstructed base-plus-SHAP value `0.0066667`. Its strongest legitimate-direction features were `SSLfinal_State`, `URL_of_Anchor`, `Prefix_Suffix`, `web_traffic`, and `age_of_domain`.

The endpoints are `GET /api/ml/feature-importance` and `GET /api/ml/explanation/test-00000`. These explain only the benchmark UCI phishing-risk model. They do not explain the broader Digital Trust Score and do not accept live website collector features. SHAP values are model-specific associations, not causal evidence or safety certification.

## Reproduce

```text
python -m src.ml_model.validate_experiment data/raw/phishing+websites.zip
python -m src.ml_model.train data/raw/phishing+websites.zip --models-dir models --experiments-dir experiments
python -m unittest discover -s src -p 'test_*.py' -v
```

## PhiUSIIL Independent Experiment

### Source and audit

PhiUSIIL was obtained from the authoritative [UCI Machine Learning Repository dataset 967](https://archive.ics.uci.edu/dataset/967/phiusiil+phishing+url+dataset), licensed CC BY 4.0. The local archive is `data/raw/phiusiiil/phiusiil-phishing-url-dataset.zip`. UCI defines label `1` as legitimate and `0` as phishing.

The raw dataset contains 235,795 rows and 56 columns. It has no missing values, no exact full-row duplicates, 808 repeated numeric feature vectors (`0.3427%` of rows), and zero conflicting labels among those vectors. The prepared dataset contains 234,987 unique feature vectors: 100,137 phishing and 134,850 legitimate. The generated audit JSON is `data/processed/phiusiiil_dataset_audit.json`.

The 50 numeric predictors used were:

```text
URLLength, DomainLength, IsDomainIP, URLSimilarityIndex, CharContinuationRate,
TLDLegitimateProb, URLCharProb, TLDLength, NoOfSubDomain, HasObfuscation,
NoOfObfuscatedChar, ObfuscationRatio, NoOfLettersInURL, LetterRatioInURL,
NoOfDegitsInURL, DegitRatioInURL, NoOfEqualsInURL, NoOfQMarkInURL,
NoOfAmpersandInURL, NoOfOtherSpecialCharsInURL, SpacialCharRatioInURL, IsHTTPS,
LineOfCode, LargestLineLength, HasTitle, DomainTitleMatchScore, URLTitleMatchScore,
HasFavicon, Robots, IsResponsive, NoOfURLRedirect, NoOfSelfRedirect, HasDescription,
NoOfPopup, NoOfiFrame, HasExternalFormSubmit, HasSocialNet, HasSubmitButton,
HasHiddenFields, HasPasswordField, Bank, Pay, Crypto, HasCopyrightInfo, NoOfImage,
NoOfCSS, NoOfJS, NoOfSelfRef, NoOfEmptyRef, NoOfExternalRef
```

Excluded columns were `FILENAME` because UCI identifies it as ignorable, `URL`, `Domain`, `TLD`, and `Title` because they are raw/high-cardinality text fields not encoded in this controlled experiment, and `label` because it is the target. No other column was removed as direct target leakage. The very strong source-derived predictors, especially `URLSimilarityIndex`, remain a limitation and are discussed below.

### Methodology

The experiment has its own loader, trainer, model metadata, and artifact directories. It removes ambiguous feature vectors before splitting, deduplicates the remaining numeric feature vectors, uses a stratified 80/20 outer split with `random_state=42`, creates a stratified 20% validation partition from training data for model selection, fits preprocessing only within each model pipeline, refits the selected model on all training rows, and evaluates the untouched test set once.

The resulting sizes are 187,989 training rows, 37,598 validation rows, and 46,998 test rows. Artifacts are isolated under `models/phiusiiil/` and `experiments/phiusiiil/`; the UCI root artifacts are not overwritten.

### Model comparison and metrics

Random Forest was selected on validation ROC-AUC then F1:

| Model | Test Accuracy | Test Precision | Test Recall | Test F1 | Test ROC-AUC |
| --- | ---: | ---: | ---: | ---: | ---: |
| Logistic Regression | 0.999915 | 0.999852 | 1.000000 | 0.999926 | 1.000000 |
| Random Forest | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 |

The saved Random Forest confusion matrix, with rows `[actual 0 phishing, actual 1 legitimate]` and columns `[predicted 0, predicted 1]`, is `[[20028, 0], [0, 26970]]`. Separate Logistic Regression and Random Forest confusion-matrix and ROC-curve plots were generated under `experiments/phiusiiil/`.

The perfect test values are actual outputs, but they should not be interpreted as real-world performance. A univariate audit found `URLSimilarityIndex` alone had ROC-AUC approximately `0.9961`; `LineOfCode` and `NoOfExternalRef` were also extremely separable. The raw data has 15,709 repeated Domain values and 54 domains shared across both labels, so a random row split may not represent domain- or time-held-out performance. These signals may reflect PhiUSIIL's collection and feature-construction process, so the result requires external and temporal validation before any deployment claim.

### PhiUSIIL SHAP

PhiUSIIL SHAP is independent of UCI SHAP. It explains the saved PhiUSIIL Random Forest's class-1 probability, where class 1 means legitimate. Global SHAP uses a deterministic 1,000-row sample from the 46,998-row test partition and all 50 used features. Artifacts are `experiments/phiusiiil/shap_feature_importance.csv`, `shap_global_importance.json`, `shap_summary_bar.png`, and `shap_summary_beeswarm.png`.

The leading mean absolute SHAP features were `URLSimilarityIndex` (`0.175293`), `LineOfCode` (`0.059490`), `NoOfExternalRef` (`0.048865`), `NoOfSelfRef` (`0.043819`), and `NoOfImage` (`0.037851`). Local explanations use `test-00000`-style IDs and preserve legitimate/phishing direction semantics. These explanations describe PhiUSIIL benchmark behavior only, not the live TrustGuard score.

### UCI comparison and cross-dataset validation

Cross-dataset prediction was not performed. UCI has 30 categorical/integer features with different names, encodings, and meanings; PhiUSIIL has 50 numeric predictors derived from URL and webpage content. There is no demonstrated one-to-one compatible feature schema. Comparing raw metric values across the datasets would confound dataset composition, collection process, feature definitions, and label semantics. A scientifically valid cross-dataset study requires a documented common feature subset, compatible transformations, and an external evaluation design; this experiment does not silently invent that mapping.

PhiUSIIL is therefore a second independent benchmark, not evidence that the UCI model generalizes to live websites or that either benchmark proves universal trustworthiness.