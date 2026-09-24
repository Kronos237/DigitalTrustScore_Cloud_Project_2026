"""Small, defensive network helpers for public website observation."""

import ipaddress
import socket
import ssl
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .config import MAX_RESPONSE_BYTES, REQUEST_TIMEOUT_SECONDS


@dataclass
class FetchResult:
    status: int | None
    headers: dict[str, str]
    body: str
    response_time_ms: float | None
    redirect_count: int
    error: str | None


def is_public_hostname(hostname: str) -> bool:
    if hostname.lower() in {"localhost", "metadata.google.internal", "instance-data.ec2.internal"}:
        return False
    try:
        addresses = {info[4][0] for info in socket.getaddrinfo(hostname, None)}
    except socket.gaierror:
        return False
    return bool(addresses) and all(_is_public_ip(address) for address in addresses)


def _is_public_ip(value: str) -> bool:
    address = ipaddress.ip_address(value)
    return not (address.is_private or address.is_loopback or address.is_link_local or address.is_reserved or address.is_multicast)


def is_restricted_hostname(hostname: str) -> bool:
    if hostname.lower() in {"localhost", "metadata.google.internal", "instance-data.ec2.internal"}:
        return True
    try:
        return not _is_public_ip(hostname)
    except ValueError:
        return False


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, file, code, msg, headers, new):
        return None


def fetch_public_url(url: str) -> FetchResult:
    from time import monotonic
    from urllib.parse import urlparse

    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    if not hostname or not is_public_hostname(hostname):
        return FetchResult(None, {}, "", None, 0, "The target is not a public hostname")
    request = Request(url, headers={"User-Agent": "TrustGuard-Research-Prototype/1.0", "Accept": "text/html"})
    started = monotonic()
    try:
        opener = build_opener(_NoRedirect())
        with opener.open(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            body = response.read(MAX_RESPONSE_BYTES + 1)
            if len(body) > MAX_RESPONSE_BYTES:
                return FetchResult(None, {}, "", None, 0, "Response exceeded the configured size limit")
            return FetchResult(response.status, dict(response.headers.items()), body.decode("utf-8", "replace"), round((monotonic() - started) * 1000, 2), 0, None)
    except HTTPError as error:
        return FetchResult(error.code, dict(error.headers.items()), "", round((monotonic() - started) * 1000, 2), 0, "Website returned an HTTP error")
    except (URLError, TimeoutError, OSError) as error:
        return FetchResult(None, {}, "", round((monotonic() - started) * 1000, 2), 0, str(error.reason if isinstance(error, URLError) else error))


def inspect_tls(hostname: str, port: int = 443) -> dict:
    context = ssl.create_default_context()
    try:
        with socket.create_connection((hostname, port), timeout=REQUEST_TIMEOUT_SECONDS) as raw_socket:
            with context.wrap_socket(raw_socket, server_hostname=hostname) as tls_socket:
                certificate = tls_socket.getpeercert()
                expires = datetime.strptime(certificate["notAfter"], "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
                return {"status": "observed", "valid": True, "issuer": dict(x[0] for x in certificate.get("issuer", [])), "expires": expires.isoformat(), "days_remaining": max(0, (expires - datetime.now(timezone.utc)).days), "tls_version": tls_socket.version()}
    except (OSError, ssl.SSLError, KeyError, ValueError) as error:
        return {"status": "unavailable", "valid": None, "error": str(error)}