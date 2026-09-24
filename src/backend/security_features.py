"""Security observations from the response and TLS handshake."""

from .network import FetchResult, inspect_tls

SECURITY_HEADERS = ("Strict-Transport-Security", "Content-Security-Policy", "X-Frame-Options", "X-Content-Type-Options", "Referrer-Policy", "Permissions-Policy")


def collect(hostname: str, response: FetchResult, scheme: str) -> dict:
    headers = {key.lower(): value for key, value in response.headers.items()}
    header_status = {header: ("present" if header.lower() in headers else "missing") if response.status is not None else "unknown" for header in SECURITY_HEADERS}
    tls = inspect_tls(hostname) if scheme == "https" else {"status": "not_applicable", "valid": None}
    observed = [value for value in header_status.values() if value == "present"]
    header_score = round(len(observed) / len(SECURITY_HEADERS) * 100) if response.status is not None else None
    return {"https": scheme == "https", "tls": tls, "headers": header_status, "header_score": header_score}