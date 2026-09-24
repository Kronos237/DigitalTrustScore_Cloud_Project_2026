"""Loader, audit, and leakage-safe preparation for the PhiUSIIL benchmark."""

import argparse
import io
import json
import zipfile
from pathlib import Path

import pandas as pd

TARGET = "label"
IDENTIFIER_COLUMNS = ("FILENAME",)
TEXT_COLUMNS = ("URL", "Domain", "TLD", "Title")


def load_dataset(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"PhiUSIIL dataset not found: {path}")
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as archive:
            candidates = [name for name in archive.namelist() if name.lower().endswith(".csv")]
            if not candidates:
                raise ValueError("PhiUSIIL archive does not contain a CSV file")
            frame = pd.read_csv(io.BytesIO(archive.read(candidates[0])))
    else:
        frame = pd.read_csv(path)
    if TARGET not in frame.columns:
        raise ValueError(f"PhiUSIIL target column {TARGET!r} is missing")
    frame[TARGET] = pd.to_numeric(frame[TARGET], errors="raise").astype("int8")
    if not set(frame[TARGET].unique()).issubset({0, 1}):
        raise ValueError("PhiUSIIL label must contain only 0 and 1")
    return frame


def feature_columns(frame: pd.DataFrame) -> list[str]:
    excluded = set(IDENTIFIER_COLUMNS + TEXT_COLUMNS + (TARGET,))
    return [column for column in frame.select_dtypes(include="number").columns if column not in excluded]


def audit_dataset(frame: pd.DataFrame) -> dict:
    features = feature_columns(frame)
    conflict_mask = frame.groupby(features, dropna=False)[TARGET].transform("nunique") > 1
    return {"rows": int(len(frame)), "columns": int(len(frame.columns)), "column_names": list(frame.columns), "feature_columns": features, "excluded_columns": {"target": [TARGET], "identifiers": list(IDENTIFIER_COLUMNS), "text_or_high_cardinality": list(TEXT_COLUMNS)}, "target_definition": "1=legitimate, 0=phishing", "class_distribution": {str(key): int(value) for key, value in frame[TARGET].value_counts().sort_index().items()}, "missing_values": {key: int(value) for key, value in frame.isna().sum().items() if value}, "duplicate_full_rows": int(frame.duplicated().sum()), "duplicate_feature_vectors": int(frame.duplicated(subset=features).sum()), "conflicting_feature_vectors": int(frame.loc[conflict_mask, features].drop_duplicates().shape[0]), "rows_in_conflicting_feature_vectors": int(conflict_mask.sum()), "data_types": {key: str(value) for key, value in frame.dtypes.items()}, "unique_counts": {key: int(frame[key].nunique(dropna=False)) for key in frame.columns}, "obvious_leakage_columns": ["label"], "identifier_columns": list(IDENTIFIER_COLUMNS), "text_or_url_columns": list(TEXT_COLUMNS)}


def prepare_training_dataset(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    features = feature_columns(frame)
    conflict_mask = frame.groupby(features, dropna=False)[TARGET].transform("nunique") > 1
    without_conflicts = frame.loc[~conflict_mask].copy()
    prepared = without_conflicts.drop_duplicates(subset=features).reset_index(drop=True)
    audit = {"raw_rows": int(len(frame)), "conflicting_feature_vectors": int(frame.loc[conflict_mask, features].drop_duplicates().shape[0]), "conflicting_rows_excluded": int(conflict_mask.sum()), "duplicate_feature_rows_removed": int(len(without_conflicts) - len(prepared)), "prepared_rows": int(len(prepared)), "prepared_class_distribution": {str(key): int(value) for key, value in prepared[TARGET].value_counts().sort_index().items()}}
    return prepared[features + [TARGET]], audit


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--output", type=Path, default=Path("data/processed/phiusiiil_dataset_audit.json"))
    arguments = parser.parse_args()
    report = audit_dataset(load_dataset(arguments.dataset))
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))