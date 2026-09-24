"""End-to-end evidence collection and prototype trust-score engine."""

import uuid
from urllib.parse import urlparse

from . import reputation_features, reliability_features, security_features, transparency_features, url_features
from .config import MODEL_VERSION
from .features import normalize_url
from .network import fetch_public_url, is_restricted_hostname
from .storage import utc_now

WEIGHTS = {"security": 0.30, "reputation": 0.25, "transparency": 0.20, "reliability": 0.15, "ml_component": 0.10}


def _status_score(value: str, positive: str = "detected") -> float | None:
    if value == positive:
        return 100.0
    if value in {"not_detected", "missing"}:
        return 0.0
    return None


def _average(values: list[float | None], neutral: float = 50.0) -> float:
    usable = [value for value in values if value is not None]
    return round(sum(usable) / len(usable), 2) if usable else neutral


def _risk_level(score: int) -> str:
    if score >= 80:
        return "low_observed_risk"
    if score >= 60:
        return "moderate_observed_risk"
    if score >= 40:
        return "elevated_observed_risk"
    return "high_observed_risk"


def analyze(value: str) -> dict:
    normalized = normalize_url(value)
    parsed = urlparse(normalized)
    if is_restricted_hostname(parsed.hostname or ""):
        raise ValueError("Private, loopback, and cloud metadata targets are not allowed")
    response = fetch_public_url(normalized)
    security = security_features.collect(parsed.hostname or "", response, parsed.scheme)
    transparency = transparency_features.collect(response.body, response.status is not None and bool(response.body))
    reputation = reputation_features.collect(parsed.hostname or "")
    reliability = reliability_features.collect(response)
    url_data = url_features.collect(normalized)
    security_score = _average([100.0 if security["https"] else 0.0, 100.0 if security["tls"].get("valid") is True else 0.0 if security["tls"].get("valid") is False else None, security["header_score"]])
    transparency_score = _average([_status_score(value) for value in transparency.values()])
    reliability_score = _average([100.0 if reliability["availability"] == "observed" else None, max(0.0, 100.0 - reliability["response_time_ms"] / 10) if reliability["response_time_ms"] is not None else None])
    reputation_score = 50.0 if reputation["status"] == "unavailable" else 0.0
    category_scores = {"security": security_score, "reputation": reputation_score, "transparency": transparency_score, "reliability": reliability_score}
    available_weights = {name: weight for name, weight in WEIGHTS.items() if name != "ml_component"}
    trust_score = round(sum(category_scores[name] * weight for name, weight in available_weights.items()) / sum(available_weights.values()))
    factors = [
        {"feature": "HTTPS", "impact": 0.18 if security["https"] else -0.18, "direction": "positive" if security["https"] else "negative", "source": "observed"},
        {"feature": "Security headers", "impact": round((security["header_score"] or 0) / 500, 3) if security["header_score"] is not None else 0.0, "direction": "positive" if security["header_score"] else "unknown", "source": "observed" if security["header_score"] is not None else "unavailable"},
        {"feature": "Transparency evidence", "impact": round((transparency_score - 50) / 500, 3), "direction": "positive" if transparency_score >= 50 else "negative", "source": "observed" if response.body else "unavailable"},
    ]
    return {"id": str(uuid.uuid4()), "url": normalized, "created_at": utc_now(), "status": "complete" if response.status is not None else "partial", "trust_score": trust_score, "risk_level": _risk_level(trust_score), "model_version": MODEL_VERSION, "prototype_thresholds": True, "ml_prediction": {"status": "unavailable", "probability": None, "message": "ML prediction unavailable for live feature set"}, "category_scores": category_scores, "features": {"url": url_data, "security": security, "reputation": reputation, "transparency": transparency, "reliability": reliability}, "explanation": {"positive": [factor for factor in factors if factor["direction"] == "positive"], "negative": [factor for factor in factors if factor["direction"] == "negative"], "unavailable": [factor for factor in factors if factor["source"] == "unavailable"], "method": "Transparent prototype contributions; SHAP is unavailable until a compatible trained model is supplied."}, "factors": factors, "weights": WEIGHTS}