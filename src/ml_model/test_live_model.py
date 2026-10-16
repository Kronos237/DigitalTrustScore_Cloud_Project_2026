import unittest
from pathlib import Path

from .live_model_inference import LiveRiskPredictor
from .live_shap import explain_live_url


ROOT = Path(__file__).resolve().parents[2]
MODEL = ROOT / "models" / "live-phishing" / "random_forest.joblib"
METADATA = ROOT / "models" / "live-phishing" / "model_metadata.json"


@unittest.skipUnless(MODEL.exists() and METADATA.exists(), "Train the live URL model before running inference tests")
class LiveModelTests(unittest.TestCase):
    def test_live_prediction_uses_versioned_schema(self):
        predictor = LiveRiskPredictor(MODEL, METADATA)
        result = predictor.predict("https://example.com")
        self.assertEqual(list(predictor.pipeline.named_steps["model"].classes_), [0, 1])
        self.assertEqual(result["status"], "observed")
        self.assertEqual(result["schema_version"], "live-phishing-v1")
        self.assertIn(result["prediction"], {"phishing", "legitimate"})
        self.assertGreaterEqual(result["phishing_probability"], 0)
        self.assertLessEqual(result["phishing_probability"], 1)

    def test_probability_is_selected_by_phishing_class_label(self):
        predictor = LiveRiskPredictor(MODEL, METADATA)
        row = predictor.transformed_row("https://www.google.com")
        probabilities = predictor.pipeline.predict_proba(row)[0]
        phishing_index = list(predictor.pipeline.named_steps["model"].classes_).index(1)
        self.assertAlmostEqual(predictor.predict("https://www.google.com")["phishing_probability"], float(probabilities[phishing_index]))

    def test_live_shap_matches_prediction_probability(self):
        result = explain_live_url("https://example.com", str(MODEL), str(METADATA))
        predictor = LiveRiskPredictor(MODEL, METADATA)
        prediction = predictor.predict("https://example.com")
        self.assertEqual(len(result["all_features"]), 24)
        self.assertAlmostEqual(result["shap_sum_plus_base"], prediction["phishing_probability"], places=8)
        self.assertTrue(result["top_phishing_features"] or result["top_legitimate_features"])


if __name__ == "__main__":
    unittest.main()