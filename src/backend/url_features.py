"""Observable URL structure indicators."""

import ipaddress
from urllib.parse import urlparse


def collect(url: str) -> dict:
    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    try:
        has_ip = ipaddress.ip_address(hostname).version in {4, 6}
    except ValueError:
        has_ip = False
    path_and_query = f"{parsed.path}?{parsed.query}"
    return {
        "url_length": len(url),
        "subdomain_count": max(0, len(hostname.split(".")) - 2),
        "uses_https": parsed.scheme == "https",
        "uses_ip_address": has_ip,
        "contains_at_symbol": "@" in url,
        "suspicious_special_characters": sum(url.count(character) for character in ("%", "=", "&", "-")),
        "path_length": len(path_and_query),
    }