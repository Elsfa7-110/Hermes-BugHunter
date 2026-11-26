## 11. Identity Fabric Mapping

An organization's IdP/SSO posture is a high-value target: compromise the identity fabric and you don't need to break into individual apps. Map it methodically.

### 11.1 Subdomain prefix enumeration

Probe these prefixes against the target's root domain (and any sibling brand domains discovered):

```
auth.{domain}
login.{domain}
sso.{domain}
idp.{domain}
iam.{domain}
identity.{domain}
accounts.{domain}
oauth.{domain}
```

Plus generic OIDC discovery on every alive subdomain:
```
{any-host}/.well-known/openid-configuration
```

### 11.2 Microsoft Entra (Azure AD)

- **OIDC metadata + tenant GUID extraction** — fetch `https://login.microsoftonline.com/{tenant-or-domain}/.well-known/openid-configuration`. The `issuer` field returns a URL containing the tenant GUID (8-4-4-4-12 hex format). Tenant GUID + domain = stable tenant fingerprint.
- **getuserrealm.srf** — `https://login.microsoftonline.com/getuserrealm.srf?login=<user>@<domain>` returns NameSpaceType: `Managed` (cloud-native), `Federated` (on-prem ADFS / external IdP), or `Unknown`. Detectability: low.
- **Autodiscover v2** — `https://autodiscover-s.outlook.com/autodiscover/metadata/json/1` POST with email; detects tenant membership.
- **GetCredentialType** (deep-mode user-enum) — `https://login.microsoftonline.com/common/GetCredentialType` POST `{"username": "<email>"}`. Response indicates whether email exists in tenant. Detectability: medium. Cap attempts at 20 per tenant.

### 11.3 Okta

- **Org slug derivation** — derive candidate slugs from subdomains + root domain stem; Okta tenants live at `<slug>.okta.com` (or `<slug>.oktapreview.com`).
- **OIDC fingerprint** — `https://<slug>.okta.com/.well-known/openid-configuration`.
- **/api/v1/authn user-enum** (deep-mode) — POST `{"username": "<email>", "password": "invalid"}`. 400 vs 401 response code indicates user existence. Detectability: medium. Cap at 20 per tenant.

### 11.4 ADFS

- **Passive fingerprint** — GET `https://{domain}/adfs/idpinitiatedsignon.aspx` → 200 indicates ADFS present.
- **Active mex endpoint** (deep-mode) — `https://{domain}/adfs/Services/Trust/mex` returns SOAP metadata.

### 11.5 Google Workspace

- `https://{domain}/.well-known/openid-configuration` — Google-hosted-domain customers expose discovery endpoints with characteristic issuer/JWKS URIs.
- MX records pointing to `*.googlemail.com` / `aspmx.l.google.com` is a strong Google Workspace signal.

### 11.6 Generic OIDC (Keycloak / Auth0 / Ping / OneLogin / Duo)

- Probe every alive subdomain for `/.well-known/openid-configuration`.
- The `issuer` and `authorization_endpoint` fields fingerprint the IdP product.
- `*.auth0.com`, `*.onelogin.com`, `*.pingone.com`, `*.duosecurity.com` patterns are characteristic.

### 11.7 SAML metadata

Probe these paths on every alive webapp:

```
/saml/metadata
/FederationMetadata/2007-06/FederationMetadata.xml
/federationmetadata/2007-06/federationmetadata.xml
/simplesaml/saml2/idp/metadata.php
/auth/saml2/metadata
```

SAML metadata XML contains: `EntityID`, signing certs, `SingleSignOnService` URL, `NameIDFormat`.

### 11.8 AWS account-ID extraction

- **S3 bucket region header** — HEAD on a known target bucket returns `x-amz-bucket-region`; correlate with bucket-name entropy to infer account.
- **ARN regex in JSON / HTML responses** — search for `arn:aws:[a-z0-9-]+:[a-z0-9-]*:([0-9]{12}):` (the 12-digit AWS account ID is the capture group).
- **`AccountId` property in JS / API responses** — common in IAM-related error messages and CloudFormation outputs.
- **OAuth client_id leaks** — Google OAuth: `<digits>-<chars>.apps.googleusercontent.com`; MSAL: GUID in `clientId` property.

### 11.9 Output

Each discovered IdP becomes a `Service` asset with `attrs.product`, `attrs.tenant_id`, `attrs.discovery_endpoint`. Then in Stage 4, correlate with breach data: every compromised user under a discovered tenant becomes an SSO_EXPOSURE finding (CRITICAL — see §22.3).

### 11.10 Microsoft 365 Deep Surface

Beyond plain Entra fingerprinting, M365 exposes a wider attack surface that's worth enumerating in depth.

**Teams Federation:**

- `https://login.microsoftonline.com/<target-domain>/.well-known/openid-configuration` confirms tenant.
- Teams federation status: `https://teams.microsoft.com/api/mt/<region>/beta/users/<email>/externalsearchv3` (requires authenticated request from a federated tenant; useful for confirming whether external Teams chat is allowed).
- **External chat enabled** = soft-attack surface (vishing, smishing, "from-IT" pretexts via Teams chat).
- **Open Federation** (any tenant can chat) is the default; check whether the target restricted it.

**SharePoint subdomains:**

- `<target-stem>.sharepoint.com` — main tenant SharePoint.
- `<target-stem>-my.sharepoint.com` — OneDrive-for-Business URLs (per-user personal sites).
- `<target-stem>-admin.sharepoint.com` — SharePoint admin center (auth-required, but presence confirms tenancy).
- Where `<target-stem>` is derived from the company name (often the part before `.com`).

**OneDrive personal site enumeration:**

- Per-user OneDrive URL: `https://<target-stem>-my.sharepoint.com/personal/<user_email_with_underscore>/Documents/`.
- Replace `@` with `_` and `.` with `_` in the email (e.g., `alice@acme.com` → `alice_acme_com`).
- Authenticated probe; useful for confirming whether the OneDrive personal site has been provisioned (which itself is a presence indicator).

**M365 OAuth client_id discovery:**

- Many internal apps register OAuth client_ids in Entra. Search JS bundles, mobile-app strings, and API responses for `client_id=<GUID>` patterns.
- Microsoft's well-known first-party client_ids (for Office, Graph, etc.) are documented; finding non-Microsoft GUIDs reveals custom internal apps.
- The endpoint `https://login.microsoftonline.com/<tenant>/v2.0/.well-known/openid-configuration` lists supported endpoints; some tenants leave `device_authorization_endpoint` enabled (device-code phishing target).

**Power Platform / Power Apps:**

- `https://make.powerapps.com/environments` (auth-required); environment IDs sometimes leak in URLs.
- `*.crm.dynamics.com` (Dynamics 365 / Power Apps default URLs).
- `*.azurewebsites.net` for App Service deployments.

**M365 OAuth misconfig findings to look for:**

- `device_authorization_endpoint` enabled on `common` tenant (device-code phishing target) → **MEDIUM** (operational risk; not directly exploitable but enables attack).
- Custom OAuth app with `Public client` flow enabled and broad scopes (offline_access, Mail.Read, Files.Read.All) → **HIGH** if app is approved for the tenant.
- Multi-tenant OAuth app published by the target (others can consent) → check whether scopes include sensitive Graph permissions.

**Detectability:** all M365 endpoint probes log to Entra sign-in logs / audit logs (medium-low for fetch-only; medium for any auth attempt).

---

## 12. API & Auth-Map Methodology

Modern targets expose REST, GraphQL, and undocumented internal APIs. The OSINT goal is to enumerate them, classify them, and rank by attack interest.

### 12.1 Discovery paths

- **Swagger / OpenAPI** — probe a 28-path wordlist (companion skill §16.1) on every alive webapp. Parse YAML/JSON; extract every endpoint (method + path).
- **GraphQL** — probe a 13-path wordlist (companion skill §16.2). POST a standard introspection query. If schema returns, you have full type/query/mutation/subscription enumeration.
- **GraphQL when introspection is disabled** — fall back to field-suggestion enumeration (companion skill §22.9).
- **Postman** — query Postman's public universal-search endpoint with the target name; walk each matching workspace; extract requests, headers, pre-request scripts, test scripts, env vars.
- **JS-extracted endpoints** — every endpoint extracted from JavaScript bundles feeds into the same classifier.
- **Mobile-extracted endpoints** — every endpoint from APK static analysis feeds in via sidecar (`mobile_endpoints.json`).

### 12.2 Classification

For each endpoint, capture:

```
url, method, source[], auth_required, auth_type, auth_location,
rate_limited, cors_policy, sensitive_path_keywords[], schema_leaks,
verb_tampering_possible, interest_score (0..100), interest_reasons[]
```

How to determine each field:
- Send `OPTIONS` → `Allow` header reveals supported methods (verb tampering check).
- Send `GET` without auth → 200 = `auth_required=false`; 401/403 = `auth_required=true`.
- Capture response headers for `WWW-Authenticate` (auth_type), `RateLimit-*` / `X-RateLimit-*`.
- Send a request with `Origin: https://attacker.example` → response `Access-Control-Allow-Origin` reflected = `cors_policy=reflected`.
- Trigger an error → check response for stack traces, ORM hints.

### 12.3 Interest score (0–100)

See companion skill §20 for the full rubric. **Score ≥ 70 → HIGH/CRITICAL finding** with `attack_path_hint` in evidence.

### 12.4 Attack-path hints

When emitting a HIGH/CRITICAL finding, include a one-sentence attack-path hint in the evidence so the operator knows where to start exploiting. Templates in companion skill §39.

---

## 13. JavaScript Deep Analysis

For every alive webapp, scrape its JS — it's where modern frontends leak.

### 13.1 Script discovery

- Parse HTML for `<script src="...">` and `<link rel="modulepreload" href="...">`.
- Probe a guess-path list (companion skill §16.9) for common bundlers.

### 13.2 Sourcemap detection (HIGH info disclosure)

- Inline reference: regex `//[#@]\s*sourceMappingURL=` at end of bundle.
- Sibling fetch: try `<bundle>.map` next to every discovered JS.
- If accessible: parse the sourcemap's `sources[]` (leaks repo structure) and `sourcesContent[]` (full original source code embedded). Run the secret catalog over `sourcesContent[]`.
- Severity: HIGH `INFO_DISCLOSURE`.

### 13.3 Secret scanning

Run the 29+-pattern catalog (companion skill §17) over every JS body and every parsed `sourcesContent[]` blob. Each hit = `SECRET_LEAK` finding with the catalog's per-pattern severity.

### 13.4 Endpoint extraction

Three regex tiers (companion skill §16.10). Each unique endpoint becomes a `wayback_endpoint` asset and feeds into the API classifier in §12.

### 13.5 Internal-host leakage detection

Three patterns (companion skill §16.11): RFC1918, internal DNS suffixes, K8s service DNS. Each match = MEDIUM `INFO_DISCLOSURE`.

### 13.6 GraphQL introspection probe

When an extracted endpoint ends in `/graphql` or `/graphiql`, POST the standard introspection query. If schema returns → HIGH `MISCONFIG`. Then enumerate mutations and subscriptions for high-value targets.

### 13.7 Next.js manifest parsing

`_buildManifest.js` and `_ssgManifest.js` enumerate every Next.js page route — exposes the application's full route structure.

### 13.8 Budget guidelines

- Cap webapps analyzed per engagement: 40 default, 120 with `--deep`.
- Cap JS files per webapp: 40 default, 80 with `--deep`.
- Cap individual JS file size: 2 MiB.
- Per-file timeout: 10 seconds.

---

## 14. Mobile Attack Surface

Mobile apps are often the weakest link.

### 14.1 App discovery

- **Android** — google-play-scraper. Search by company name, brand keywords, root domain stem.
- **iOS** — iTunes Search API.

### 14.2 Ownership confidence (0–100)

See companion skill §21. Threshold: **≥70** for deep analysis.

### 14.3 APK acquisition + static analysis

- Download via APKPure HTML scrape.
- Extract via `zipfile` + optional `androguard`.
- Pull: `AndroidManifest.xml`, resource strings, asset files, native `.so` files, `classes*.dex` (string-extract).

### 14.4 Secret scanning

Run the catalog over manifest, resources, asset files, dex string-extract output.

### 14.5 Backend hostname extraction

Every discovered hostname becomes a `subdomain` asset. Write sidecar `mobile_endpoints.json` for the API discovery module to consume.

### 14.6 Manifest misconfig findings

| Manifest attribute | Severity |
|---|---|
| `android:debuggable="true"` | CRITICAL |
| `android:allowBackup="true"` (without whitelist) | MEDIUM |
| `android:usesCleartextTraffic="true"` | MEDIUM |
| Exported activity/service/receiver without `android:permission` | MEDIUM |
| Sensitive deep-link handler | HIGH |
| WebView with `setJavaScriptEnabled(true)` + `addJavascriptInterface(...)` | HIGH |
| Certificate pinning absent | LOW |

### 14.7 Firebase canonical probe

For every Firebase project ID extracted:
- **Realtime DB** — GET `https://{project-id}.firebaseio.com/.json`. Returns JSON tree → CRITICAL `OPEN_FIREBASE_RTDB`.
- **Firestore** — `https://{project-id}.firebaseapp.com/`.
- **Storage** — corresponding GCS bucket.
- **Remote Config** — only readable with extracted API key + app ID.

### 14.8 iOS path

- Discovery only via iTunes Search API.
- ITMS link extraction: `https://apps.apple.com/<region>/app/<slug>/id<bundle-id>`.
- Privacy nutrition labels (App Store Connect): publicly published; useful for understanding what data the app touches.
- Don't recommend auto-download (DMCA / DRM considerations).

---

## 15. Cloud Attack Surface

### 15.1 Bucket permutation

Build candidate bucket names from: target's root domain, subdomain stems, optional brand/company name. Filter generic stems unless combined with target-identifying tokens. Apply 6 prefixes × 15 suffixes (companion skill §16.8 has the lists).

### 15.2 Provider URL templates

S3, GCS, Azure Blob templates — see companion skill §16.8.

### 15.3 Probe technique

- HEAD first. Status code 200/301 = exists; 403 = exists, private; 404 = skip.
- If exists, GET on bucket root. Listable XML/JSON listing → **CRITICAL**.

### 15.4 Severity mapping

| Outcome | Severity |
|---|---|
| Bucket listable | CRITICAL |
| Bucket exists, objects readable by direct URL but not listable | HIGH |
| Bucket exists, ACL private | INFO |

### 15.5 Adjacent cloud signals

Extract AWS account-ID from S3 region/error responses. GCP project ID from GCS error responses. Azure tenant ID from blob URL patterns.

---

## 16. Cryptocurrency Investigation

### 16.1 Transaction Analysis

- Track flows between wallets; identify clusters of related addresses; monitor large transfers.

Tools: Cielo (multi-chain), TRM (graphs), Arkham (multichain + entity labels), MetaSleuth (visual), Range (CCTP), Socketscan (EVM bridge), Pulsy (bridge aggregator), Chainalysis Horizon 2.0 (paid), Elliptic Lens.

### 16.2 Layer 2 / Rollup Analysis

- **zkSync Era / Polygon zkEVM** — ZK proofs hide L2 details; only L1 bridge events visible.
- **Arbitrum / Optimism** — batched/compressed; L2 state from L1 calldata.
- **StarkNet** — Cairo VM; different address derivation.
- **Base / Blast / Scroll** — OP Stack or ZK.
- **Privacy protocols on L2** — Aztec (programmable privacy), Railgun (shielded pools), Privacy Pools (Tornado Cash successor).

**Methodology:** start with L1 bridge events; use L2 explorers for in-rollup activity; for privacy protocols focus on timing analysis and clustering.

### 16.3 Cautions

- Bridges introduce mint/burn semantics; avoid 1:1 flow assumptions.
- MEV/aggregator paths create false "direct" trails.
- L2 finality: optimistic rollups have 7-day challenge periods.

### 16.4 Wallet / Exchange / NFT Profiling

Same patterns: age + activity + connections + balance over time + linked accounts. NFTs add ownership history + metadata + connected wallets.

---

## 17. Image Analysis

### 17.1 Reverse Image Search

- Google Images / Lens (Lens may require auth — use sock-puppet incognito).
- Yandex Images (strongest for RU/East-European content).
- Bing Image Match, TinEye, Copyseeker, Perplexity Pro.
- Browser extensions: RevEye, Search by Image (multi-engine).
- Picarta for AI geolocation.

### 17.2 Metadata (EXIF)

ExifTool, Jeffrey's Image Metadata Viewer, EXIF Viewer Pro.

### 17.3 Image Forensics

Forensically, FotoForensics, Bellingcat Photo Checker, Sensity AI, Exposing.ai, Adobe Content Credentials Verify, c2patool. Techniques: ELA, metadata, clone detection, noise analysis.

### 17.4 Geolocation Workflow

- **Foreground** — signs, license plates, clothing, vegetation, weather.
- **Background** — landmarks, unique buildings, mountains, water, infrastructure.
- **Map markings** — flora/fauna, seasonal indicators.
- **Trial and error** — Google Street View, Bing Streetside, Yandex Panorama.
- **Overpass Turbo** for OpenStreetMap queries.
- **Mountain ID** — PeakVisor, Peakfinder, PeakLens AR.
- **OCR** — Google or Yandex OCR.
- **Video transcripts** — YouTube captions improve keyword search.

### 17.5 Specialized

- **Fire identification** — NASA FIRMS, Sentinel Hub, Global Forest Watch, Copernicus EFFIS.
- **Plane tracking** — Apollo Hunter, FlightRadar, ADS-B Exchange.

---

## 18. Video Analysis

### 18.1 Context extraction

Signs/banners, architecture, road markings, license plates, clothing, cross-platform snippet search.

### 18.2 Metadata

YouTube Data Viewer (Amnesty), ExifTool on downloaded files.

### 18.3 Platform-specific

- **TikTok / Instagram** — APIs change often; prefer platform exports; sample 1–4h cadence.
- **Bluesky AT Protocol** — DID resolution via `bsky.social/xrpc/com.atproto.identity.resolveHandle`; identity doc via `plc.directory/<did>`; firehose at Firesky; SkyView for graphs. Archive early — handle migration / post deletion.
- **Mastodon / Fediverse** — instance matters (jurisdiction, logging); WebFinger for discovery; FediSearch cross-instance; instance enumeration via Fediverse Observer; ActivityPub objects are JSON-LD.
- **Threads** — IG-API-similar limitations.

### 18.4 Auditory clues

Languages, dialects, background noises (train horns, prayer calls, wildlife). Tools: Audacity, Sonic Visualiser, SoundCMD. Spectrograms for unique patterns; Shazam/SoundHound for music.

### 18.5 Frame extraction

FFmpeg, VLC. Stitch panoramas; stabilize panning footage (FFmpeg `deshake` or Blender VSE). Prefer original uploads over re-encodes.

---
