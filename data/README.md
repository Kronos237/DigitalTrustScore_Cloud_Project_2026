# Data

This project does not fabricate or commit third-party datasets or claim benchmark metrics without an actual training run.

## Dataset expected by the training pipeline

- **Name:** UCI Phishing Websites Dataset
- **Source:** UCI Machine Learning Repository, dataset 327, `https://archive.ics.uci.edu/dataset/327/phishing+websites`
- **Download:** obtain the official archive from UCI and place it at `data/raw/phishing+websites.zip`. The archive is expected to contain the UCI ARFF data file, normally named `Training Dataset.arff`.
- **Records after loading:** 2,456 rows. Inspection found 740 exact full-row duplicates, plus 10 conflicting feature vectors covering 34 rows. Training excludes those ambiguous rows and removes remaining feature duplicates before splitting, leaving 1,696 rows.
- **Target:** UCI `Result`, normalized to `label` (`0` legitimate, `1` phishing).
- **Observed class distribution:** raw `0=1,362`, `1=1,094`; after conflict exclusion and feature-vector deduplication `0=890`, `1=806`.
- **Features:** `having_IP_Address`, `URL_Length`, `Shortining_Service`, `having_At_Symbol`, `double_slash_redirecting`, `Prefix_Suffix`, `having_Sub_Domain`, `SSLfinal_State`, `Domain_registeration_length`, `Favicon`, `port`, `HTTPS_token`, `Request_URL`, `URL_of_Anchor`, `Links_in_tags`, `SFH`, `Submitting_to_email`, `Abnormal_URL`, `Redirect`, `on_mouseover`, `RightClick`, `popUpWidnow`, `Iframe`, `age_of_domain`, `DNSRecord`, `web_traffic`, `Page_Rank`, `Google_Index`, `Links_pointing_to_page`, and `Statistical_report`.
- **Preprocessing:** ARFF decoding, numeric conversion, target normalization, duplicate removal before a stratified 80/20 split. Missing values are median-imputed inside each model pipeline.
- **Artifacts:** `models/model_metadata.json`, `models/random_forest.joblib`, and generated plots/comparison CSV under `experiments/`.

Run inspection after downloading:

```text
python -m src.ml_model.data_loader --inspect data/raw/phishing+websites.zip
```

## Supported input

The loader accepts the official ARFF file directly or a processed CSV created by the inspection/processing command. Place licensed source data under `data/raw/` and derived files under `data/processed/`. Keep provenance, license, sample count, preprocessing, and target-label meaning in the accompanying dataset note.

The UCI dataset is used only as a benchmark. Verify UCI usage terms and cite the repository in academic work. Benchmark phishing labels are not universal website trust labels.

## PhiUSIIL benchmark

- **Source:** UCI Machine Learning Repository dataset 967, [PhiUSIIL Phishing URL (Website)](https://archive.ics.uci.edu/dataset/967/phiusiil+phishing+url+dataset), CC BY 4.0.
- **Download:** `https://archive.ics.uci.edu/static/public/967/phiusiil+phishing+url+dataset.zip`
- **Local file:** `data/raw/phiusiiil/phiusiil-phishing-url-dataset.zip`.
- **Raw data:** 235,795 rows and 56 columns, with 50 numeric candidate predictors, 5 text/identifier columns, and `label`.
- **Label:** `1=legitimate`, `0=phishing`.
- **Cleaning:** exclude `FILENAME`, raw `URL`, `Domain`, `TLD`, and `Title`; exclude no conflicting vectors because the audit found none; remove 808 repeated numeric feature vectors before splitting.
- **Prepared data:** 234,987 rows; 100,137 phishing and 134,850 legitimate.
- **Experiment namespace:** `models/phiusiiil/` and `experiments/phiusiiil/`.