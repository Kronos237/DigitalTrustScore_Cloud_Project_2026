# ML Feature Mapping

## Scope

The benchmark model is a phishing/risk classifier trained on the UCI Phishing Websites dataset. It is not a universal trustworthiness model. Live TrustGuard evidence is collected separately and is never silently substituted into the benchmark vector.

## Benchmark Dataset Features

The UCI archive provides 30 input features and the `Result` target. The exact values and meanings are preserved in the downloaded ARFF file; the loader normalizes the target to `label` (`1` phishing, `0` legitimate) and keeps the original feature names.

| Dataset feature | Meaning | Live correspondence | Transformation | Live status |
| --- | --- | --- | --- | --- |
| `having_IP_Address` | URL host is an IP address | `url.uses_ip_address` | Map boolean to dataset encoding only after validation | Available |
| `URL_Length` | URL length category | `url.url_length` | Dataset categorical bins must be verified against UCI encoding | Partial |
| `Shortining_Service` | URL shortening indicator | None | No safe live provider mapping yet | Unsupported |
| `having_At_Symbol` | `@` in URL | `url.contains_at_symbol` | Map boolean to dataset encoding | Available |
| `double_slash_redirecting` | Redirect marker in URL | `url` and redirect observations | Requires UCI encoding validation | Partial |
| `Prefix_Suffix` | Hyphen in domain | `url` hostname | Requires domain-only transformation | Partial |
| `having_Sub_Domain` | Subdomain structure | `url.subdomain_count` | Requires UCI categorical encoding | Partial |
| `SSLfinal_State` | SSL state category | `security.tls.valid` | Binary live evidence does not cover all UCI categories | Partial |
| `Domain_registeration_length` | Registration duration | None | Requires RDAP and compatible units | Unsupported |
| `Favicon` | Favicon relationship | None | HTML retrieval alone is insufficient | Unsupported |
| `port` | Non-standard port indicator | Parsed URL port | Requires UCI encoding validation | Partial |
| `HTTPS_token` | HTTPS token in domain | Parsed hostname | Requires domain token transform | Partial |
| `Request_URL` | External resource ratio | None | Requires HTML resource analysis and UCI ratio definition | Unsupported |
| `URL_of_Anchor` | Anchor URL ratio | None | Requires HTML analysis and UCI ratio definition | Unsupported |
| `Links_in_tags` | Link tag ratio | None | Requires HTML analysis and UCI ratio definition | Unsupported |
| `SFH` | Form handler state | None | Requires form analysis and UCI encoding | Unsupported |
| `Submitting_to_email` | Form submits to email | None | Requires form analysis | Unsupported |
| `Abnormal_URL` | Domain/URL abnormality | None | No compatible live evidence contract | Unsupported |
| `Redirect` | Redirect count category | `reliability.redirect_count` | Current collector intentionally does not follow redirects | Unsupported |
| `on_mouseover` | Mouseover behavior | None | JavaScript is not executed | Unsupported |
| `RightClick` | Right-click behavior | None | JavaScript is not executed | Unsupported |
| `popUpWidnow` | Popup behavior | None | JavaScript is not executed | Unsupported |
| `Iframe` | Iframe usage | None | HTML parser could be extended, but encoding needs validation | Unsupported |
| `age_of_domain` | Domain age | None | Requires RDAP provider | Unsupported |
| `DNSRecord` | DNS record availability | `network` DNS resolution | Requires UCI encoding validation | Partial |
| `web_traffic` | Traffic rank | None | Requires permitted reputation/traffic source | Unsupported |
| `Page_Rank` | Page rank | None | Historical external signal; no provider configured | Unsupported |
| `Google_Index` | Search index status | None | Requires permitted search source | Unsupported |
| `Links_pointing_to_page` | Inbound links category | None | Requires external source | Unsupported |
| `Statistical_report` | Statistical report flag | None | Dataset-specific feature; no live mapping | Unsupported |

## Live Trust Features

Live analysis separately reports HTTPS, TLS certificate details, security headers, response status/time, URL structure, transparency links, reputation availability, and DNS/SSRF outcomes. These features are used by the broader prototype trust score, not passed to the UCI model unless a validated mapping is implemented and documented.

## Integrity Rule

The API returns `ML prediction unavailable for live feature set` unless a trained model with a compatible feature adapter is installed. A benchmark prediction must never be inferred from an incompatible live feature vector.