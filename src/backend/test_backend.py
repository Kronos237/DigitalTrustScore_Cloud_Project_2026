import unittest

from .features import extract_features
from .model import TrustModel
from .analyzer import analyze


class TrustModelTests(unittest.TestCase):
    def test_secure_url_scores_higher_than_ip_url(self) -> None:
        secure_url, secure_features = extract_features("https://example.com")
        ip_url, ip_features = extract_features("http://192.168.1.1/login")
        self.assertEqual(secure_url, "https://example.com")
        self.assertLess(TrustModel().predict(ip_features).score, TrustModel().predict(secure_features).score)

    def test_invalid_url_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            extract_features("not a url")

    def test_score_is_bounded(self) -> None:
        _, features = extract_features("https://example.com")
        self.assertIn(TrustModel().predict(features).score, range(101))

    def test_private_targets_are_rejected_before_fetch(self) -> None:
        with self.assertRaises(ValueError):
            analyze("http://127.0.0.1")


if __name__ == "__main__":
    unittest.main()