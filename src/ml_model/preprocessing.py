"""Leakage-safe split and preprocessing for UCI benchmark features."""

import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def split_dataset(frame: pd.DataFrame, target: str = "label"):
    features = frame.drop(columns=[target])
    labels = frame[target]
    return train_test_split(features, labels, test_size=0.2, random_state=42, stratify=labels)


def numeric_preprocessor(scale: bool = False) -> Pipeline:
    steps = [("imputer", SimpleImputer(strategy="median"))]
    if scale:
        steps.append(("scaler", StandardScaler()))
    return Pipeline(steps)