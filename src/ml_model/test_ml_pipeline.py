import tempfile
import unittest
from pathlib import Path

import joblib

from .data_loader import load_dataset, prepare_training_dataset
from .model_metadata import load_metadata
from .predict import BenchmarkPredictor
from .preprocessing import numeric_preprocessor, split_dataset
from .train import train


DATASET = Path("data/raw/phishing+websites.zip")


@unittest.skipUnless(DATASET.exists(), "Download the official UCI dataset before running benchmark tests")
class MlPipelineTests(unittest.TestCase):
    def test_dataset_loads_with_expected_target_and_features(self):
        frame = load_dataset(DATASET)
        self.assertEqual(len(frame.columns), 31)
        self.assertIn("label", frame.columns)
        self.assertEqual(len(frame), 2456)

    def test_duplicate_conflicts_are_removed_before_split(self):
        frame, audit = prepare_training_dataset(load_dataset(DATASET))
        self.assertEqual(audit["exact_duplicate_rows_removed"], 740)
        self.assertEqual(audit["conflicting_feature_vectors"], 10)
        self.assertEqual(audit["rows_in_conflicting_feature_vectors"], 34)
        self.assertEqual(audit["prepared_rows"], 1696)
        self.assertEqual(frame.duplicated(subset=[column for column in frame.columns if column != "label"]).sum(), 0)

    def test_preprocessing_split_is_stratified_and_reproducible(self):
        frame, _ = prepare_training_dataset(load_dataset(DATASET))
        first = split_dataset(frame)
        second = split_dataset(frame)
        self.assertEqual(first[0].shape, (1356, 30))
        self.assertEqual(first[0].equals(second[0]), True)
        self.assertEqual(numeric_preprocessor().fit_transform(first[0]).shape, first[0].shape)

    def test_training_saves_reloadable_model_and_metadata(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            metadata = train(DATASET, root / "models", root / "experiments")
            model = joblib.load(root / "models" / "random_forest.joblib")
            saved = load_metadata(root / "models" / "model_metadata.json")
            self.assertEqual(metadata["model_name"], "Random Forest")
            self.assertEqual(saved["feature_count"], 30)
            predictor = BenchmarkPredictor(root / "models" / "random_forest.joblib", root / "models" / "model_metadata.json")
            features = {name: 1 for name in saved["feature_names"]}
            self.assertIn(predictor.predict(features)["label"], {"0", "1"})
            self.assertTrue(hasattr(model, "predict"))


if __name__ == "__main__":
    unittest.main()