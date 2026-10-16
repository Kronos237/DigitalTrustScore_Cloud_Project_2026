"""Deterministic URL-only features shared by training and live inference."""

import ipaddress
import re
from urllib.parse import parse_qsl, urlsplit

LIVE_MODEL_SCHEMA_VERSION = "live-phishing-v1"
LIVE_MODEL_FEATURES = (
    "url_length", "hostname_length", "hostname_dot_count", "subdomain_count", "hostname_label_count",
    "path_depth", "query_parameter_count", "fragment_present", "https_enabled", "hostname_is_ipv4",
    "hostname_is_ipv6", "hostname_uses_punycode", "at_symbol_present", "port_present", "nonstandard_port",
    "percent_encoded_count", "digit_count", "letter_count", "special_character_count", "hyphen_count",
    "underscore_count", "equals_count", "ampersand_count", "suspicious_token_count",
)

SUSPICIOUS_TOKENS = ("login", "signin", "verify", "account", "secure", "update", "password", "bank", "wallet")


def normalize_model_url(value: str) -> str:
    candidate = value.strip()
    if not candidate:
        raise ValueError("URL is empty")
    if "://" not in candidate:
        candidate = f"https://{candidate}"
    parsed = urlsplit(candidate)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("URL must have an HTTP(S) scheme and hostname")
    if any(char.isspace() for char in parsed.hostname):
        raise ValueError("Hostname contains whitespace")
    try:
        _ = parsed.port
    except ValueError as error:
        raise ValueError("URL contains an invalid port") from error
    return candidate


def _ip_kind(hostname: str) -> tuple[bool, bool]:
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        return False, False
    return address.version == 4, address.version == 6


def extract_live_url_features(value: str) -> dict[str, float]:
    normalized = normalize_model_url(value)
    parsed = urlsplit(normalized)
    hostname = parsed.hostname or ""
    hostname_lower = hostname.lower()
    ipv4, ipv6 = _ip_kind(hostname)
    labels = hostname.split(".") if hostname else []
    path_parts = [part for part in parsed.path.split("/") if part]
    query_pairs = parse_qsl(parsed.query, keep_blank_values=True)
    url_lower = normalized.lower()
    punctuation = sum(not character.isalnum() for character in normalized)
    try:
        port = parsed.port
    except ValueError as error:
        raise ValueError("URL contains an invalid port") from error
    return {
        "url_length": float(len(normalized)),
        "hostname_length": float(len(hostname)),
        "hostname_dot_count": float(hostname.count(".")),
        "subdomain_count": float(max(0, len(labels) - 2)),
        "hostname_label_count": float(len(labels)),
        "path_depth": float(len(path_parts)),
        "query_parameter_count": float(len(query_pairs)),
        "fragment_present": float(bool(parsed.fragment)),
        "https_enabled": float(parsed.scheme == "https"),
        "hostname_is_ipv4": float(ipv4),
        "hostname_is_ipv6": float(ipv6),
        "hostname_uses_punycode": float(any(label.lower().startswith("xn--") for label in labels) or hostname.encode("idna").decode("ascii").lower() != hostname_lower),
        "at_symbol_present": float("@" in normalized),
        "port_present": float(port is not None),
        "nonstandard_port": float(port is not None and port not in ({"http": 80, "https": 443}.get(parsed.scheme, 0),)),
        "percent_encoded_count": float(len(re.findall(r"%[0-9a-fA-F]{2}", normalized))),
        "digit_count": float(sum(character.isdigit() for character in normalized)),
        "letter_count": float(sum(character.isalpha() for character in normalized)),
        "special_character_count": float(punctuation),
        "hyphen_count": float(normalized.count("-")),
        "underscore_count": float(normalized.count("_")),
        "equals_count": float(normalized.count("=")),
        "ampersand_count": float(normalized.count("&")),
        "suspicious_token_count": float(sum(url_lower.count(token) for token in SUSPICIOUS_TOKENS)),
    }


def ordered_feature_row(value: str) -> list[float]:
    features = extract_live_url_features(value)
    return [features[name] for name in LIVE_MODEL_FEATURES]