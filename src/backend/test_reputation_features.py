import json
import unittest
from unittest.mock import patch

from . import reputation_features
from .reputation_features import VirusTotalProvider


class _Response:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, _limit):
        return json.dumps({"data": {"attributes": {"last_analysis_stats": {"malicious": 2, "suspicious": 1}}}}).encode()


class ReputationProviderTests(unittest.TestCase):
    def test_missing_key_is_disabled_not_clean(self):
        result = VirusTotalProvider("").check("example.com")
        self.assertEqual(result["status"], "disabled")
        self.assertIsNone(result["phishing"])

    def test_malicious_verdict_is_provider_result(self):
        with patch.object(reputation_features, "urlopen", return_value=_Response()) as mocked_urlopen:
            result = VirusTotalProvider("test-key").check("example.com")
            self.assertEqual(result["status"], "malicious")
            self.assertEqual(result["malicious_engines"], 2)
            mocked_urlopen.assert_called_once()


if __name__ == "__main__":
    unittest.main()