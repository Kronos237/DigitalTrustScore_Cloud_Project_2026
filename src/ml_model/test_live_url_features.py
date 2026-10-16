import unittest

from .live_url_features import LIVE_MODEL_FEATURES, LIVE_MODEL_SCHEMA_VERSION, extract_live_url_features, ordered_feature_row


class LiveUrlFeatureTests(unittest.TestCase):
    def test_feature_order_and_schema_are_stable(self):
        values = extract_live_url_features("https://example.com/a/b?q=1&x=2#top")
        self.assertEqual(LIVE_MODEL_SCHEMA_VERSION, "live-phishing-v1")
        self.assertEqual(tuple(values), LIVE_MODEL_FEATURES)
        self.assertEqual(len(ordered_feature_row("https://example.com")), len(LIVE_MODEL_FEATURES))

    def test_malformed_url_is_rejected(self):
        for value in ("", "not a url", "ftp://example.com", "https://bad:port"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    extract_live_url_features(value)

    def test_ipv4_ipv6_ports_and_https(self):
        ipv4 = extract_live_url_features("http://192.0.2.1:8080/path")
        ipv6 = extract_live_url_features("https://[2001:db8::1]/path")
        self.assertEqual((ipv4["hostname_is_ipv4"], ipv4["hostname_is_ipv6"], ipv4["port_present"], ipv4["nonstandard_port"]), (1.0, 0.0, 1.0, 1.0))
        self.assertEqual((ipv6["hostname_is_ipv4"], ipv6["hostname_is_ipv6"], ipv6["https_enabled"]), (0.0, 1.0, 1.0))

    def test_unicode_punycode_query_fragment_and_path(self):
        values = extract_live_url_features("https://xn--bcher-kva.example/a/b?q=1&x=2#fragment")
        self.assertEqual(values["hostname_uses_punycode"], 1.0)
        self.assertEqual(values["path_depth"], 2.0)
        self.assertEqual(values["query_parameter_count"], 2.0)
        self.assertEqual(values["fragment_present"], 1.0)


if __name__ == "__main__":
    unittest.main()