"""Compatibility façade preserving the existing AnalysisStore API."""

from datetime import datetime, timezone

from src.database.repository import AnalysisRepository


class AnalysisStore(AnalysisRepository):
    """Repository-backed store used by both HTTP adapters."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()