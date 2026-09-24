import unittest
from pathlib import Path

import joblib

from .phiusiiil_loader import audit_dataset, feature_columns, load_dataset, prepare_training_dataset
from .phiusiiil_shap import PhiusiilShapExplainer
from .preprocessing import numeric_preprocessor
from sklearn.model_selection import train_test_split


ROOT = Path(__file__).resolve().parents[2]
DATASET = ROOT / "data" / "raw" / "phiusiiil" / "phiusiil-phishing-url-dataset.zip"
MODEL = ROOT / "models" / "phiusiiil" / "random_forest.joblib"
METADATA = ROOT / "models" / "phiusiiil" / "model_metadata.json"


@unittest.skipUnless(DATASET.exists() and MODEL.exists() and METADATA.exists(), "PhiUSIIL dataset and artifacts are required")
class PhiusiilTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = load_dataset(DATASET)
        cls.frame, cls.cleaning = prepare_training_dataset(cls.raw)

    def test_schema_and_audit(self):
        audit = audit_dataset(self.raw)
        self.assertEqual((audit["rows"], audit["columns"]), (235795, 56))
        self.assertEqual(audit["duplicate_feature_vectors"], 808)
        self.assertEqual(audit["conflicting_feature_vectors"], 0)
        self.assertEqual(audit["missing_values"], {})
        self.assertNotIn("FILENAME", audit["feature_columns"])
        self.assertNotIn("URL", audit["feature_columns"])
        self.assertEqual(audit["target_definition"], "1=legitimate, 0=phishing")

    def test_cleaning_and_split_are_reproducible(self):
        features = feature_columns(self.frame)
        self.assertEqual(len(features), 50)
        self.assertEqual(len(self.frame), 234987)
        self.assertEqual(self.frame.duplicated(subset=features).sum(), 0)
        x_train, x_test, y_train, y_test = train_test_split(self.frame[features], self.frame.label, test_size=0.2, random_state=42, stratify=self.frame.label)
        self.assertEqual((len(x_train), len(x_test)), (187989, 46998))
        self.assertEqual(numeric_preprocessor().fit_transform(x_train).shape, (187989, 50))
        self.assertEqual(y_train.value_counts().sum(), 187989)
        self.assertEqual(y_test.value_counts().sum(), 46998)

    def test_saved_random_forest_reloads_and_predicts(self):
        model = joblib.load(MODEL)
        features = feature_columns(self.frame)
        transformed = model.named_steps["preprocess"].transform(self.frame[features].iloc[:3])
        self.assertEqual(model.named_steps["model"].predict(transformed).shape, (3,))

    def test_saved_shap_explainer_has_real_dimensions_and_additivity(self):
        explainer = PhiusiilShapExplainer(MODEL, METADATA, DATASET, sample_size=20)
        self.assertEqual(explainer.shap_values().shape, (20, 50))
        result = explainer.explain_sample("test-00000")
        self.assertAlmostEqual(result["shap_sum_plus_base"], result["legitimate_probability"], places=10)
        self.assertEqual(len(result["all_features"]), 50)
        self.assertEqual(result["scope"], "PhiUSIIL benchmark model; separate from UCI and live trust analysis")


if __name__ == "__main__":
    unittest.main()