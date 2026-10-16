"""Provider-isolated reputation enrichment with an explicit unavailable state."""

import json
from datetime import datetime, timezone
from time import monotonic
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from .config import REPUTATION_TIMEOUT_SECONDS, VIRUSTOTAL_API_KEY


class ReputationProvider:
    def check(self, hostname: str) -> dict:
        return {"status": "unavailable", "message": "Reputation information unavailable", "source": None, "phishing": None, "malware": None}


class VirusTotalProvider(ReputationProvider):
    """Optional domain-level VirusTotal adapter; disabled without an API key."""

    endpoint = "https://www.virustotal.com/api/v3/domains/{}"

    def __init__(self, api_key: str = VIRUSTOTAL_API_KEY):
        self.api_key = api_key

    def check(self, hostname: str) -> dict:
        if not self.api_key:
            return {"status": "disabled", "message": "VirusTotal reputation lookup disabled; API key not configured", "source": "VirusTotal", "queried_at": None, "phishing": None, "malware": None}
        started = monotonic()
        request = Request(self.endpoint.format(quote(hostname, safe="")), headers={"x-apikey": self.api_key, "Accept": "application/json", "User-Agent": "TrustGuard-Research-Prototype/1.0"})
        try:
            with urlopen(request, timeout=REPUTATION_TIMEOUT_SECONDS) as response:
                payload = json.loads(response.read(200000).decode("utf-8"))
            stats = payload.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
            malicious = int(stats.get("malicious", 0))
            suspicious = int(stats.get("suspicious", 0))
            return {"status": "malicious" if malicious else "no_malicious_finding", "message": "VirusTotal reported malicious engines" if malicious else "No malicious engine finding in the available report", "source": "VirusTotal", "queried_at": datetime.now(timezone.utc).isoformat(), "elapsed_ms": round((monotonic() - started) * 1000, 2), "malicious_engines": malicious, "suspicious_engines": suspicious, "phishing": malicious > 0, "malware": malicious > 0}
        except HTTPError as error:
            status = "rate_limited" if error.code == 429 else "provider_error"
            return {"status": status, "message": "VirusTotal reputation lookup failed", "source": "VirusTotal", "http_status": error.code, "phishing": None, "malware": None}
        except (URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError) as error:
            return {"status": "provider_error", "message": "VirusTotal reputation lookup unavailable", "source": "VirusTotal", "error": str(error), "phishing": None, "malware": None}


def collect(hostname: str) -> dict:
    return VirusTotalProvider().check(hostname)