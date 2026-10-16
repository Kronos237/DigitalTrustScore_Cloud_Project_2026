"""Canonical live feature schema contract shared by collection and future inference."""

from dataclasses import dataclass

LIVE_SCHEMA_VERSION = "live-trust-v1"


@dataclass(frozen=True)
class LiveFeatureSpec:
    name: str
    unit: str
    description: str
    source_kind: str


LIVE_FEATURES = (
    LiveFeatureSpec("url_length", "characters", "Normalized URL length", "direct_observation"),
    LiveFeatureSpec("hostname_length", "characters", "Hostname length", "direct_observation"),
    LiveFeatureSpec("subdomain_count", "count", "Heuristic subdomain count", "derived_indicator"),
    LiveFeatureSpec("uses_ip_address", "boolean", "IP literal used as hostname", "direct_observation"),
    LiveFeatureSpec("suspicious_pattern_count", "count", "Configured suspicious URL pattern count", "derived_indicator"),
    LiveFeatureSpec("contains_at_symbol", "boolean", "At symbol in normalized URL", "direct_observation"),
    LiveFeatureSpec("https_enabled", "boolean", "HTTPS URL scheme", "direct_observation"),
    LiveFeatureSpec("tls_valid", "boolean/null", "Validated TLS handshake result", "direct_observation"),
    LiveFeatureSpec("tls_days_remaining", "days/null", "Certificate days remaining", "direct_observation"),
    LiveFeatureSpec("http_status", "status/null", "Observed HTTP response status", "direct_observation"),
    LiveFeatureSpec("response_time_ms", "milliseconds/null", "Bounded request duration", "direct_observation"),
    LiveFeatureSpec("redirect_count", "count", "Redirects followed safely; currently zero when redirects are not followed", "direct_observation"),
    LiveFeatureSpec("security_header_score", "0-100/null", "Relevant security headers present", "derived_indicator"),
    LiveFeatureSpec("transparency_detected_count", "count/null", "Detected transparency indicators", "derived_indicator"),
    LiveFeatureSpec("dns_resolution", "boolean/null", "Public DNS resolution gate", "direct_observation"),
    LiveFeatureSpec("reputation_status", "categorical", "External reputation provider status", "external_reputation"),
)


def feature_specs() -> list[dict[str, str]]:
    return [{"name": item.name, "unit": item.unit, "description": item.description, "source_kind": item.source_kind} for item in LIVE_FEATURES]


def build_vector(url_data: dict, security: dict, reliability: dict, transparency: dict, reputation: dict) -> dict:
    transparency_values = [value for value in transparency.values() if value != "unknown"]
    detected_count = sum(value == "detected" for value in transparency_values) if transparency_values else None
    tls = security.get("tls", {})
    return {"url_length": url_data.get("url_length"), "hostname_length": url_data.get("hostname_length"), "subdomain_count": url_data.get("subdomain_count"), "uses_ip_address": url_data.get("uses_ip_address"), "suspicious_pattern_count": url_data.get("suspicious_pattern_count"), "contains_at_symbol": url_data.get("contains_at_symbol"), "https_enabled": security.get("https"), "tls_valid": tls.get("valid"), "tls_days_remaining": tls.get("days_remaining"), "http_status": reliability.get("http_status"), "response_time_ms": reliability.get("response_time_ms"), "redirect_count": reliability.get("redirect_count"), "security_header_score": security.get("header_score"), "transparency_detected_count": detected_count, "dns_resolution": reliability.get("dns_resolution"), "reputation_status": reputation.get("status", "unavailable")}