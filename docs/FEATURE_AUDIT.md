# Live Feature Audit

This audit reflects the current implementation, not proposed functionality.

## Live collector inventory

| Canonical/current feature | Location | Type / unit | Source and availability | Error/timeout behavior | Live score | Existing ML | Live-model suitability |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `https` / `uses_https` | `src/backend/security_features.py`, `url_features.py` | Boolean | Parsed URL; always available after validation | Invalid schemes rejected | Security | None | Suitable |
| `hostname_present` | `src/backend/features.py` | Numeric 0/1 | URL parser | Invalid/missing host rejected | Not directly | None | Suitable |
| `hostname_length_ok` | `src/backend/features.py` | Numeric 0/1; 4-65 chars | Parsed hostname | Deterministic | Not directly | None | Suitable |
| `uses_ip_address` | `src/backend/features.py`, `url_features.py` | Boolean | Host parser | Deterministic; IPv6 handling differs between modules | URL evidence | None | Requires canonicalization |
| `url_length` | `src/backend/url_features.py` | Integer characters | Normalized URL | Deterministic | URL evidence payload | None | Suitable |
| `subdomain_count` | `src/backend/url_features.py` | Integer | Hostname dot count | Heuristic; public suffixes are not resolved | URL evidence payload | None | Suitable with documented heuristic |
| `contains_at_symbol` | `src/backend/url_features.py` | Boolean | Raw normalized URL | Deterministic | URL evidence payload | None | Suitable |
| `suspicious_path` | `src/backend/features.py` | Boolean | Path keyword heuristic: login/verify/account/secure/update | Deterministic; lexical false positives possible | Baseline factors | None | Suitable only as derived indicator |
| `suspicious_special_characters` | `src/backend/url_features.py` | Integer count | URL `%`, `=`, `&`, `-` count | Deterministic; naming is broad | URL evidence payload | None | Requires definition review |
| `path_length` | `src/backend/url_features.py` | Integer characters | Path and query | Deterministic | URL evidence payload | None | Suitable |
| TLS validity | `src/backend/network.py`, `security_features.py` | Boolean/null + status | Python `ssl` verified handshake | Bounded connect; errors become unavailable | Security | None | Suitable with status feature |
| TLS issuer/expiry/days remaining/version | `src/backend/network.py` | Structured string/int | Peer certificate and socket | Unavailable on handshake/certificate errors | Evidence payload | None | Numeric subset suitable |
| Security headers | `src/backend/security_features.py` | `present`/`missing`/`unknown` | HTTP response headers: HSTS, CSP, XFO, XCTO, Referrer, Permissions | Unknown when no HTTP response | Security score/header evidence | None | Suitable as status encoding |
| Security header score | `src/backend/security_features.py` | 0-100 or null | Present header count / six | Unknown if response unavailable | Security | None | Suitable, but not safety proof |
| HTTP status | `src/backend/reliability_features.py` | Integer/null | One bounded HTTP request | HTTP/network errors become unavailable | Reliability | None | Suitable categorical/numeric |
| Response time | `src/backend/network.py` | Milliseconds/null | Monotonic timer around request | Timeout/error returns unavailable timing | Reliability | None | Suitable with censoring policy |
| Redirect count | `src/backend/network.py` | Integer | Currently always 0 because redirects are not followed | Redirects are blocked rather than observed | Reliability payload | None | Not currently reliable; requires safe redirect walker |
| Availability | `src/backend/reliability_features.py` | `observed`/`unavailable` | HTTP status presence | Network errors do not crash analysis | Reliability | None | Suitable status feature |
| Privacy/contact/about/terms/email/phone | `src/backend/transparency_features.py` | `detected`/`not_detected`/`unknown` | Bounded HTML parser text/links | Unknown if body unavailable; no JavaScript | Transparency | None | Suitable, lexical limitations |
| Reputation | `src/backend/reputation_features.py` | Status + null verdicts | Optional VirusTotal domain provider; disabled without key | Timeout/provider/rate-limit errors become status | Neutral unless confirmed malicious | None | Candidate after labelled live data |
| Domain age/RDAP | Not implemented | N/A | No provider | N/A | No | None | Requires provider and terms review |
| DNS records | `src/backend/network.py` | Resolution gate only | `socket.getaddrinfo` | DNS failure blocks fetch | Not scored directly | None | Suitable with explicit DNS status |

## Trust-score use

`src/backend/analyzer.py` currently uses security, reputation, transparency, and reliability category scores. It normalizes available category weights and treats unavailable reputation as neutral `50`; ML is explicitly omitted. Prototype weights are defined in `WEIGHTS` and are not scientifically validated.

## Benchmark-model use

Neither UCI nor PhiUSIIL consumes these live features. UCI expects 30 dataset-specific features with different encodings; PhiUSIIL expects 50 numeric features and has opposite label semantics (`1=legitimate`). Their SHAP explanations remain benchmark-only.

## Overlap and risk findings

- `uses_ip_address` is implemented twice with different details; `live-trust-v1` must consolidate it.
- `https` and `uses_https` duplicate the same concept across payloads.
- `suspicious_special_characters` is a broad count, not a validated maliciousness signal.
- Redirect count is misleadingly present but currently records zero because redirects are deliberately not followed.
- TLS inspection is real but only used for HTTPS and is not a complete certificate-history or CT service.
- Raw HTML is used for transparency evidence but is not included in any numeric model vector.
- Reputation and RDAP/domain age are unavailable, not clean or negative.

## Not implemented / requires new work

Domain registration age, certificate transparency, configured reputation use, safe redirect revalidation, ATT&CK evidence mapping, CVE correlation, labelled live-schema dataset generation, live-compatible model training, and live SHAP are all deferred. Implementing them requires new providers, provenance, privacy review, or a defensible labelled collection process.

## Canonical schema status

`src/backend/live_schema.py` defines `live-trust-v1` and `build_vector()` is called by `src/backend/analyzer.py`. The vector is emitted for auditability and future training, but no model currently consumes it. `src/backend/reputation_features.py` contains an optional VirusTotal domain adapter; it remains disabled without `VIRUSTOTAL_API_KEY` and is not treated as clean by default.

## Live URL model status

The compatible model uses a separate `live-phishing-v1` schema from `src/ml_model/live_url_features.py`, not the broader `live-trust-v1` evidence vector. It consumes 24 URL-only lexical/structural features and uses the same extractor during training and live inference. The saved Random Forest is under `models/live-phishing/`; SHAP is generated from the same transformed row and class-1 phishing output. It does not consume TLS, HTTP, transparency, reputation, or raw HTML features, and its output remains separate from the trust score.