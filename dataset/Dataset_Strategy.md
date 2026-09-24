# Dataset Strategy

## Goal

Define a dataset that supports trust-score prediction and explainable analysis for cloud applications.

## Baseline

The first executable version deliberately does not claim to be trained on a finished dataset. It uses five observable URL features: HTTPS usage, hostname presence, hostname length, IP-address usage, and suspicious path terms. The weighted baseline is versioned as `baseline-v1` and exposes each contribution so it can be compared with a future labelled model.

## Next Dataset Decision

Create a CSV with one row per reviewed URL, the five baseline features, a documented human-review label, and the review source. Before replacing the baseline, record the sampling method, label policy, train/test split, class balance, and evaluation metrics.

