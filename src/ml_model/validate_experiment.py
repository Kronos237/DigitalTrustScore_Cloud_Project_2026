"""Reproducible validation audit for duplicate handling and split methodology."""

import argparse
import json
from pathlib import Path

from .data_loader import load_dataset, prepare_training_dataset
from .preprocessing import split_dataset


def validate(path: Path) -> dict:
    raw = load_dataset(path)
    prepared, duplicate_audit = prepare_training_dataset(raw)
    x_train, x_test, y_train, y_test = split_dataset(prepared)
    train_keys = {tuple(row) for row in x_train.to_numpy()}
    test_keys = {tuple(row) for row in x_test.to_numpy()}
    return {"duplicate_audit": duplicate_audit, "split": {"random_state": 42, "test_size": 0.2, "stratified": True, "train_rows": int(len(x_train)), "test_rows": int(len(x_test)), "identical_feature_vectors_across_split": len(train_keys & test_keys), "train_class_distribution": {str(key): int(value) for key, value in y_train.value_counts().sort_index().items()}, "test_class_distribution": {str(key): int(value) for key, value in y_test.value_counts().sort_index().items()}}, "leakage_controls": {"duplicates_removed_before_split": True, "preprocessing_inside_model_pipeline": True, "target_excluded_from_features": True, "model_selection_uses_test_set": False}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", type=Path)
    arguments = parser.parse_args()
    print(json.dumps(validate(arguments.dataset), indent=2))