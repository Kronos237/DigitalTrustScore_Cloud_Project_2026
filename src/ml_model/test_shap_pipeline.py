import http.client
import json
import threading
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

try:
    import shap
except ImportError:
    shap = None

from .shap_explainer import BenchmarkShapExplainer


ROOT = Path(__file__).resolve().parents[2]
MODEL = ROOT / "models" / "random_forest.joblib"
METADATA = ROOT / "models" / "model_metadata.json"
DATASET = ROOT / "data" / "raw" / "phishing+websites.zip"


@unittest.skipUnless(shap is not None and MODEL.exists() and METADATA.exists() and DATASET.exists(), "SHAP and trained benchmark artifacts are required")
class ShapPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.explainer = BenchmarkShapExplainer(MODEL, METADATA, DATASET)

    def test_shap_dimensions_match_corrected_test_set(self):
        values = self.explainer.test_shap_values()
        self.assertEqual(values.shape, (340, 30))
        self.assertTrue((abs(values).sum(axis=1) > 0).all())

    def test_local_explanation_is_deterministic_and_additive(self):
        first = self.explainer.explain_sample("test-00000")
        second = self.explainer.explain_sample("test-00000")
        self.assertEqual(first, second)
        self.assertAlmostEqual(first["shap_sum_plus_base"], first["probability"], places=10)
        self.assertEqual(first["model"], "Random Forest")
        self.assertEqual(first["dataset"], "UCI Phishing Websites")
        self.assertTrue(first["all_features"])

    def test_global_importance_is_real_and_ranked(self):
        with TemporaryDirectory() as temporary:
            result = self.explainer.global_importance(Path(temporary))
            self.assertEqual(result["sample_count"], 340)
            self.assertEqual(len(result["importance"]), 30)
            self.assertEqual([item["rank"] for item in result["importance"]], list(range(1, 31)))
            self.assertGreater(result["importance"][0]["mean_absolute_shap_value"], 0)
            self.assertTrue((Path(temporary) / "shap_summary_bar.png").exists())
            self.assertTrue((Path(temporary) / "shap_summary_beeswarm.png").exists())

    def test_stdlib_api_returns_real_local_explanation(self):
        from src.backend.api import RequestHandler

        server = __import__("http.server", fromlist=["ThreadingHTTPServer"]).ThreadingHTTPServer(("127.0.0.1", 0), RequestHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=30)
            connection.request("GET", "/api/ml/explanation/test-00000")
            response = connection.getresponse()
            body = json.loads(response.read())
            connection.close()
            self.assertEqual(response.status, 200)
            self.assertEqual(body["scope"], "benchmark UCI phishing-risk model; not the live Digital Trust Score")
            self.assertEqual(len(body["all_features"]), 30)
            self.assertNotEqual(body["base_value"], 0)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()