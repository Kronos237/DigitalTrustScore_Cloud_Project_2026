"""Reputation provider boundary. Unavailable is distinct from a clean result."""


class ReputationProvider:
    def check(self, hostname: str) -> dict:
        return {"status": "unavailable", "message": "Reputation information unavailable", "source": None, "phishing": None, "malware": None}


def collect(hostname: str) -> dict:
    return ReputationProvider().check(hostname)