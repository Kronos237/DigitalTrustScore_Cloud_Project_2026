"""Deterministic URL feature extraction for the first project baseline."""

from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True)
class UrlFeatures:
    https: float
    hostname_present: float
    hostname_length_ok: float
    uses_ip_address: float
    suspicious_path: float

    def as_dict(self) -> dict[str, float]:
        return {
            "https": self.https,
            "hostname_present": self.hostname_present,
            "hostname_length_ok": self.hostname_length_ok,
            "uses_ip_address": self.uses_ip_address,
            "suspicious_path": self.suspicious_path,
        }


def normalize_url(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("A URL is required")
    candidate = value if "://" in value else f"https://{value}"
    parsed = urlparse(candidate)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or any(char.isspace() for char in parsed.hostname):
        raise ValueError("Enter a valid HTTP or HTTPS URL")
    return candidate


def extract_features(value: str) -> tuple[str, UrlFeatures]:
    normalized = normalize_url(value)
    parsed = urlparse(normalized)
    hostname = parsed.hostname or ""
    path = parsed.path.lower()
    suspicious_terms = ("login", "verify", "account", "secure", "update")
    looks_like_ip = all(part.isdigit() for part in hostname.split(".")) and hostname.count(".") == 3
    features = UrlFeatures(
        https=float(parsed.scheme == "https"),
        hostname_present=float(bool(hostname)),
        hostname_length_ok=float(4 <= len(hostname) <= 65),
        uses_ip_address=float(looks_like_ip),
        suspicious_path=float(any(term in path for term in suspicious_terms)),
    )
    return normalized, features