# OSINT Integration

## Current state

The live analyzer has a `ReputationProvider` boundary in `src/backend/reputation_features.py`. A domain-level VirusTotal adapter is implemented but disabled unless `VIRUSTOTAL_API_KEY` is configured. Without credentials it returns `disabled`, not clean.

## Local setup

Create the ignored local environment file from the placeholder:

```powershell
Copy-Item .env.example .env
```

Open `.env` and set only this backend variable:

```text
VIRUSTOTAL_API_KEY=your_key_here
```

Start the backend after editing `.env`:

```powershell
.venv\Scripts\python.exe -m uvicorn src.backend.fastapi_app:app --host 127.0.0.1 --port 8000
```

For Compose, the backend receives `VIRUSTOTAL_API_KEY` from the local `.env` through `docker-compose.yml`; the key is not copied into the image, frontend bundle, URL, response body, or logs. Do not add a `VITE_` variable for this key.

Without the key, no external VirusTotal request is made and the analysis reports `disabled`.

## Provider policy

VirusTotal is the first implemented adapter. PhishTank or URLhaus remain future alternatives only after access terms, API limits, privacy implications, and domain/URL query behavior are reviewed. Provider credentials must come from environment variables or a cloud secret manager, never source code or browser code.

Each adapter must record provider name, query timestamp, status, verdict, error category, and cache behavior. Malicious match, clean/no-result, provider failure, disabled credentials, and rate limiting must remain distinct states. Timeouts and provider errors must not fail the complete analysis.

The system must avoid sending unnecessary URL paths/query strings to third parties and must not upload private user URLs without explicit documented consent. Tests should mock provider HTTP responses and never require live credentials. Verify the secret is ignored with `git check-ignore -v .env`; only `.env.example` belongs in version control.

## Deferred threat knowledge

MITRE ATT&CK may later provide a taxonomy mapping for supported evidence, but it is not a reputation feed and must not label a site without evidence. CVE records are vulnerability identifiers and will remain deferred unless a product/version can be identified defensibly.