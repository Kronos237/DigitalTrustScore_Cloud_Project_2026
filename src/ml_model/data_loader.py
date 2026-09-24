"""Load and inspect the official UCI Phishing Websites ARFF dataset."""

import argparse
import io
import json
import zipfile
from pathlib import Path

import pandas as pd
from scipy.io import arff

TARGET = "Result"


def _read_arff(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as archive:
            candidates = [name for name in archive.namelist() if name.lower().endswith(".arff")]
            if not candidates:
                raise ValueError("The UCI archive does not contain an ARFF data file")
            raw = archive.read(candidates[0])
            records, _ = arff.loadarff(io.StringIO(raw.decode("utf-8")))
    else:
        with path.open("rb") as stream:
            records, _ = arff.loadarff(stream)
    frame = pd.DataFrame(records)
    for column in frame.columns:
        if frame[column].dtype == object:
            frame[column] = frame[column].map(lambda value: value.decode("utf-8") if isinstance(value, bytes) else value)
        try:
            frame[column] = pd.to_numeric(frame[column], errors="raise")
        except (TypeError, ValueError):
            pass
    return frame


def load_dataset(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}. Download the official UCI archive into data/raw/phishing+websites.zip.")
    frame = _read_arff(path)
    if TARGET not in frame.columns:
        raise ValueError(f"Expected target column {TARGET!r}; found {list(frame.columns)}")
    frame = frame.rename(columns={TARGET: "label"})
    frame["label"] = pd.to_numeric(frame["label"], errors="raise").map(lambda value: 1 if value > 0 else 0).astype("int8")
    return frame


def inspect_dataset(path: Path) -> dict:
    frame = load_dataset(path)
    feature_frame = frame.drop(columns=["label"])
    return {"dataset": str(path), "rows": int(len(frame)), "columns": int(len(frame.columns)), "features": list(feature_frame.columns), "missing_values": {key: int(value) for key, value in frame.isna().sum().items() if value}, "duplicate_rows": int(frame.duplicated().sum()), "target_distribution": {str(key): int(value) for key, value in frame["label"].value_counts().sort_index().items()}, "feature_types": {key: str(value) for key, value in feature_frame.dtypes.items()}, "unique_values": {key: int(value) for key, value in feature_frame.nunique().items() if value <= 10}, "class_imbalance_ratio": round(float(frame["label"].value_counts().max() / frame["label"].value_counts().min()), 4)}


def prepare_training_dataset(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    feature_columns = [column for column in frame.columns if column != "label"]
    exact_duplicate_rows = int(frame.duplicated().sum())
    feature_duplicate_rows = int(frame.duplicated(subset=feature_columns).sum())
    conflict_mask = frame.groupby(feature_columns, dropna=False)["label"].transform("nunique") > 1
    conflicting_rows = int(conflict_mask.sum())
    conflicting_vectors = int(frame.loc[conflict_mask, feature_columns].drop_duplicates().shape[0])
    without_conflicts = frame.loc[~conflict_mask].copy()
    prepared = without_conflicts.drop_duplicates(subset=feature_columns).reset_index(drop=True)
    audit = {"raw_rows": int(len(frame)), "exact_duplicate_rows_removed": exact_duplicate_rows, "feature_duplicate_rows_removed": feature_duplicate_rows, "duplicate_percentage": round(exact_duplicate_rows / len(frame) * 100, 6), "conflicting_feature_vectors": conflicting_vectors, "rows_in_conflicting_feature_vectors": conflicting_rows, "conflicting_rows_excluded_before_split": conflicting_rows, "feature_duplicate_rows_removed_after_conflict_exclusion": int(len(without_conflicts) - len(prepared)), "prepared_rows": int(len(prepared)), "prepared_class_distribution": {str(key): int(value) for key, value in prepared["label"].value_counts().sort_index().items()}}
    return prepared, audit


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--inspect", dest="dataset", type=Path, required=True)
    arguments = parser.parse_args()
    print(json.dumps(inspect_dataset(arguments.dataset), indent=2))