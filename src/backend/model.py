"""Interpretable baseline model used until a labelled dataset is available."""

from dataclasses import dataclass

from .features import UrlFeatures


@dataclass(frozen=True)
class TrustPrediction:
    score: int
    label: str
    factors: list[dict[str, str | float]]
    model_version: str = "baseline-v1"


class TrustModel:
    """A transparent weighted baseline, with every contribution exposed."""

    weights = {
        "https": 35.0,
        "hostname_present": 20.0,
        "hostname_length_ok": 15.0,
        "uses_ip_address": -20.0,
        "suspicious_path": -10.0,
    }

    def predict(self, features: UrlFeatures) -> TrustPrediction:
        contributions = {
            name: self.weights[name] * value
            for name, value in features.as_dict().items()
        }
        score = round(max(0.0, min(100.0, 30.0 + sum(contributions.values()))))
        factors = [
            {
                "feature": name,
                "impact": round(impact, 2),
                "direction": "positive" if impact >= 0 else "negative",
            }
            for name, impact in sorted(contributions.items(), key=lambda item: abs(item[1]), reverse=True)
            if impact != 0
        ]
        label = "high" if score >= 75 else "moderate" if score >= 50 else "low"
        return TrustPrediction(score=score, label=label, factors=factors)