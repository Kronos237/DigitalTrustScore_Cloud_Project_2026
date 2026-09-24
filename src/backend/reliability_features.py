"""Reliability observations derived from one bounded HTTP request."""

from .network import FetchResult


def collect(response: FetchResult) -> dict:
    available = response.status is not None
    return {"http_status": response.status, "response_time_ms": response.response_time_ms, "redirect_count": response.redirect_count, "availability": "observed" if available else "unavailable", "error": response.error}