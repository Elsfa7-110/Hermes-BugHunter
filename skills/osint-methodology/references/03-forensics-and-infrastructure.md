## 19. Chronolocation and Time Analysis

### 19.1 Shadow Analysis

Tools: SunCalc, ShadeMap, Bellingcat Shadow-Finder, NOAA Solar Calculator.

### 19.2 Astronomical Calculations

Stellarium, SkyMap, MoonCalc to simulate sky at different times/locations.

### 19.3 Satellite Imagery Time

Google Earth Pro (historical imagery slider), Sentinel Hub EO Browser (Sentinel + Landsat with timelapse). Record coordinates in WKT; hash cached tilesets.

---

## 20. Threat Actor Investigation

### 20.1 Actor-Centric Workflow

- **Scoping** — actor hypothesis (APT28/29, Turla, Sandworm; APT10/41, Mustang Panda, Volt Typhoon). Seed reports from CERTs/vendors.
- **Indicator harvesting** — IOCs (domains, IPs, hashes, JA3/JA4, user-agents). Validate with passive DNS, CT logs, sandbox submissions.
- **Infrastructure mapping** — pivot from CT logs (SANs, issuer, serials), shared hosting, NS reuse, registrar accounts, HTML fingerprints. Enrich with ASN/WHOIS history, RPKI/ROA, geolocation.
- **Artifact profiling** — PE/ELF metadata (PDB paths, compile timestamps, Rich headers, code-signing). Cluster with SSDEEP/TLSH; YARA matches.
- **Social / procurement pivots** — developer handles, code snippets, academic theses, job posts, procurement records.
- **Falsification + reporting** — weigh each linkage; document alternatives; map TTPs to MITRE ATT&CK; cite sources with sections/pages.

### 20.2 Attribution Discipline

- Separate capability from intent and sponsorship.
- Rule of three: 3 weak OR 1 strong + 1 weak.
- Prefer durable pivots (registrar accounts, code-signing certs, build path idioms) over ephemeral (resolving IPs).
- Mark uncertainty levels; distinguish correlation from control.

### 20.3 Russia-Specific Pivots

- **Corporate / people** — EGRUL/EGRIP (captcha-gated), Rusprofile, Kontur.Focus, zakupki.gov.ru, hh.ru.
- **Infrastructure** — RU WHOIS via `whois.tcinet.ru`; Telegram for channels/admins/cross-posts.
- **Media** — VKontakte, Odnoklassniki, Rutube; search in Russian and transliterations.

### 20.4 China-Specific Pivots

- **Corporate / people** — gsxt.gov.cn (national enterprise credit); Tianyancha / Qichacha; ICP filings on beian.miit.gov.cn → USCC linkage.
- **Infrastructure** — CNNIC WHOIS; common domestic clouds (Aliyun, Tencent, Huawei).
- **Media** — Weibo, WeChat (via weixin.sogou.com), Zhihu, Bilibili, Douyin, Xiaohongshu; Chinese + Pinyin.

### 20.5 Infrastructure & Internet Measurement

- IP→ASN (HE BGP Toolkit, RIPEstat, BGPView).
- CT logs (crt.sh) for cert reuse and issuance cadence; pivot on subjects/issuers/serials.
- URLScan for HTML fingerprints, favicons (mmh3), script hashes.
- DNS over time (SecurityTrails PDNS, DNSDB) for subdomain churn and staging domains.

---

## 21. People & Social Media Investigation

### 21.1 Username Enumeration

WhatsMyName, NameCheckup, Sherlock, Maigret.

### 21.2 Profile Picture & Face Search

PimEyes, Exposing.ai, Azure Face API (compliance).

### 21.3 Social Graph & Content Analysis

Maltego, snscrape, SocialBlade. Bluesky / Mastodon: instance explorers + handle resolvers.

---

## 22. Breach × Identity Correlation

This is the highest-ROI single technique for external red teams. Execute it on every engagement.

### 22.1 Source stack

| Source | Tier | Notes |
|---|---|---|
| **Hudson Rock Cavalier** | FREE | Infostealer-log corpus; very high signal for corp SSO. |
| **Have I Been Pwned** | Free + paid | Domain-wide existence + Pwned Passwords (k-anonymity). |
| **DeHashed** | Paid | Searchable per-record API. |
| **IntelX** | Free + paid | Aggregator; phonebook search. |
| **Local breach corpus** | Operator-supplied | Whatever's on disk. |

### 22.2 Domain-level severity

| Stat | Severity |
|---|---|
| ≥10 employees compromised | CRITICAL |
| 1–9 employees compromised | HIGH |
| ≥1 end-user (non-employee) compromised | MEDIUM |
| Domain seen in breach with 0 named accounts | INFO |

### 22.3 SSO_EXPOSURE correlation

After Stage 3 has run identity-fabric mapping AND breach lookups have completed: for every discovered IdP tenant, intersect with breach corpus on the tenant's domain. Non-empty intersection → `SSO_EXPOSURE` finding, severity **CRITICAL**. Evidence: tenant ID + product + employee count + per-account source attribution.

### 22.4 Operational handling of stealer logs

- Treat as PII; encrypt at rest.
- SHA-256 every artifact; record source URL + acquisition timestamp.
- Never paste plaintext passwords into cloud LLMs.
- Document chain of custody.
- For client reports: redact passwords by default; offer the operator a separate encrypted credential bundle for raw data.

---

## 23. Infrastructure OSINT

### 23.1 IP & Domain Discovery

Shodan, Censys, Onyphe, DNSDB.

### 23.2 Certificate & Passive DNS

crt.sh, SecurityTrails.

### 23.3 Malware & Artifact Analysis Workflow

- **Static triage** — SHA-256, strings, import tables, PDB path, Rich header. Don't rely solely on AV labels.
- **Dynamic / sandbox** — ANY.RUN, Hybrid Analysis, CAPE, Tria.ge.
- **Clustering** — SSDEEP/TLSH, YARA matches.
- **Reporting** — STIX 2.1 IOCs; ATT&CK technique IDs; reproduction steps.

### 23.4 Telegram / WeChat Investigation

- **Telegram** — public analytics (TGStat, Telemetr, Combot); export channels with Telegram Desktop; preserve message IDs, UTC timestamps, media hashes.
- **WeChat** — Sogou Weixin search; archive articles (PNG + WARC); capture `__biz` IDs. Expect link rot.

---

## 24. Automation & Case Management

### 24.1 Tools

Hunchly, Kasm Workspaces, ArchiveBox, SingleFileZ.

### 24.2 Cross-Module Coordination Patterns

When multiple OSINT tools (or modules) run, late-arriving outputs need to feed into earlier-running consumers. Three patterns:

1. **Sidecar JSON drops** — module writes `<scan>/mobile_endpoints.json` or `<scan>/secrets_sidecar.json`; later modules read on start. No blocking.
2. **Asset-graph upserts** — shared graph store; new assets trigger downstream modules via event bus.
3. **Late-binding queues** — long-running enumeration emits assets continuously; enrichment workers pull.

In ad-hoc engagement: `tmpdir + JSON sidecars + one-line manifest` makes operations composable.

### 24.3 Multi-Engine Corpus Run Methodology

Running a large dork corpus across multiple engines:

- **Pluggable engines** — wrap each engine (DDG, Bing, Brave, SerpAPI, Yandex, Baidu) behind a common interface. Default DDG (keyless); fall back to others when keys available.
- **Per-engine rate-limiting** — each engine has its own quota and ban posture. Use a token bucket per engine.
- **Result classification** — URL-signature → title-hint → snippet-regex pipeline. Output: `(severity, category, confidence)`.
- **Dedup by URL** — different engines surface duplicates.
- **Confidence rule** — snippet-only = TENTATIVE.
- **Persistence** — corpus DB so re-runs across engagements deduplicate.

### 24.4 Evidence Preservation for Offensive Engagements

- Per-engagement / per-scan SQLite store.
- JSONL run log with `run_id`, every event one line, UTC timestamps, tool versions.
- SHA-256 every downloaded artifact.
- PNG screenshots.
- Raw HTTP requests/responses, capped at 2 KiB body per side.
- Evidence served read-only from operator's machine.
- Reproduction package: `run_id` + tool versions + JSONL log + asset/findings DB.

---

## 25. Synthetic Media Verification

Sensity AI, Hive Moderation, Reality Defender, Adobe Content Credentials Verify, CarNet (AI car-model identification for geolocation aid).

---

## 26. Anti-Patterns & Common Failure Modes

A non-exhaustive list of mistakes that come up often.

- **Single-source attribution.** Three weak OR one strong + one weak.
- **Trusting vendor labels as ground truth.** Treat labels as hypotheses.
- **Assuming favicon-hash = ownership.** Shared infra, shared CMS templates, shared CDN.
- **Asserting 1:1 bridge flows.** Bridges mint and burn; aggregators rebalance.
- **Treating snippet-only Google dorks as confirmed.** TENTATIVE until you visit.
- **Pasting real PII / creds into cloud LLMs.** Local models for sensitive analysis.
- **Mirror-imaging the threat actor.** They don't think like you.
- **Attribution by IP geolocation.** IPs lie; VPNs and residential proxies exist.
- **Ignoring the 7-day optimistic-rollup challenge window.** L2 finality is delayed.
- **Ignoring CT-log lag.** New certs take minutes-to-hours to surface; absence ≠ doesn't exist.
- **Counting Wayback snapshots as "the site at time T."** Best-effort; many requests fail.
- **Trusting `whoami` from a discovered API.** Could be a honeypot.
- **Letting the asset graph carry untyped strings.** Every discovery is an asset.
- **Skipping the scope check.** Ask once when in doubt.
- **Forgetting UTC.** Local time creates correlation bugs.
- **Continuing to probe after a WAF block.** See §6.4 — back off.
- **Skipping confidence-upgrade documentation.** TENTATIVE assets need a path to CONFIRMED.
- **Treating exec-summary writing as an afterthought.** See §31 — plan deliverables at engagement start, not at the end.

---

## 27. WAF / CDN Bypass & Origin Discovery

Web targets are increasingly behind Cloudflare / Akamai / Fastly / AWS CloudFront. The CDN itself is hard to attack; the **origin server** is often softly defended. Six techniques to find it.

### 27.1 DNS history pivot

The target's domain may have pointed directly at the origin IP **before** the CDN was deployed. Query historical passive DNS:

- **SecurityTrails** — `https://api.securitytrails.com/v1/history/<domain>/dns/a` (paid; the most complete).
- **RiskIQ PassiveTotal** — passive DNS lookups; freemium.
- **DNSDB** (Farsight) — paid; long history.
- **Validin.com** — newer, has free tier.
- **Censys host search** — historical IP-cert mapping.

What to look for: an IP that resolved 1–5 years ago and is **not** in the current CDN's published IP ranges (Cloudflare / Akamai / etc.). Cross-check the IP's current banner — if it serves the same site without the CDN, you've got the origin.

### 27.2 Certificate SAN pivot

Certificates often get re-issued with the same SAN list across origin and CDN. Search CT logs:

- crt.sh `?q=%.<target.com>&exclude=expired` — find certs with the target's domain in SAN.
- Cross-reference issued certs against current CDN-fronted cert. The "extra" cert (not the CDN one) often points to origin via its CN/SAN.
- Tools like `cero` (`go install github.com/glebarez/cero@latest`) crawl IPs and pull certs; correlate IPs whose certs include the target's hostname.

### 27.3 Favicon hash + JARM origin clustering

If the target has a unique favicon, the origin server still serves it (CDNs proxy but don't strip the favicon). Compute the favicon's mmh3 hash and search:

- Shodan: `http.favicon.hash:<mmh3-hash>`.
- Censys: `services.http.response.favicons.hashes:<mmh3-hash>`.

Returned IPs that are **not** in CDN ranges are origin candidates.

JARM (TLS handshake hash) works similarly: compute the target's JARM via `jarm`, search Shodan `ssl.jarm:<jarm-hash>`. Origin servers usually have a different JARM than CDNs.

### 27.4 Direct IP probe with Host header

If you have an origin candidate IP from steps 27.1–27.3:

```bash
curl -sk -H "Host: target.example.com" https://<candidate-IP>/
```

If the response matches the public site (same title, same body fingerprint) — you've found the origin. CDN-only IPs return generic CDN error pages or 403 to wrong Host.

### 27.5 mail.* / ftp.* / cpanel.* exception

Targets often forget to put auxiliary subdomains behind the CDN:

- `mail.<target>` — often points at the actual mail server, sometimes co-located with web origin.
- `ftp.<target>`, `sftp.<target>` — likewise.
- `cpanel.<target>`, `whm.<target>`, `webmail.<target>` — shared hosting controls; same IP as web origin.
- `direct.<target>`, `origin.<target>`, `direct-connect.<target>`, `noproxy.<target>` — ironic admin labels.
- `dev.<target>`, `staging.<target>` — dev environments often skip CDN.

Probe each. If any resolves to a non-CDN IP, that IP often hosts the prod origin too.

### 27.6 Error page / misconfig leakage

When the CDN throws an error (request triggers WAF, origin is down, configuration mismatch), it sometimes leaks the origin IP in the error body:

- Cloudflare 5xx error pages historically included a `cf-ray` and sometimes the underlying upstream details.
- 502/504 from CDN tells you the origin exists but is unreachable from the CDN — useful confirmation it's not just NXDOMAIN.
- `X-Cache: MISS from <origin-host>` headers.
- HTTP response with origin headers leaking through (`X-Powered-By`, `Server`, `X-Backend-Server`).

### 27.7 Email-header bounce trick (for email-server origin)

Send an email to a non-existent address at the target. The bounce often reveals origin mail server IPs in the `Received:` headers — these mail servers are sometimes on the same IP / netblock as the web origin. (Use a sock-puppet email; never your real engagement persona.)

### 27.8 Confidence rules

- Origin IP found via DNS history: **TENTATIVE** until corroborated by direct probe.
- Origin IP corroborated by Host-header probe matching content: **FIRM**.
- Origin IP corroborated by Host-header probe + cert SAN match + favicon match: **CONFIRMED**.

When unsure, document the hypothesis in the asset attrs — don't claim origin discovery without ≥2 corroborating signals.

---

## 28. Vulnerability Prioritization (CVE / EPSS / KEV)

A Nuclei scan can return 100+ CVEs against a target. You can't validate all of them. Prioritize by exploitability.

### 28.1 Data sources (companion skill §29.2 has the URLs)

- **NVD** (National Vulnerability Database) — base CVE catalog, CVSS scores.
- **EPSS** (Exploit Prediction Scoring System) — probability of exploit in the next 30 days, scale 0.0–1.0.
- **CISA KEV** (Known Exploited Vulnerabilities) — vulnerabilities proven exploited in the wild; includes federal-agency due-by dates.
- **ExploitDB** — POC code presence.
- **Metasploit module catalog** — automation availability.
- **InTheWild.io** — community-curated "actively exploited" tracker.
- **OpenCVE** — timeline + watchlist + alerts.
- **Trickest CVE → POC mapping** — community-maintained mapping of CVEs to public POCs.

### 28.2 Prioritization rubric

For each CVE in your list, score:

| Signal | Weight |
|---|---|
| Listed in CISA KEV | **+50** (proven exploited; treat as immediate) |
| EPSS score ≥ 0.7 | **+30** |
| EPSS score 0.3–0.69 | **+15** |
| Public Metasploit module exists | **+25** |
| Public POC on ExploitDB / GitHub | **+15** |
| Vendor-issued advisory + patch | **+10** (means the vuln is real and patchable; not always exploitable) |
| Auth-required vs unauth-required | unauth +20, post-auth +0 |
| Network-vector (network) vs adjacent / local | network +15, adjacent +5, local +0 |
| CVSS v3 base ≥ 9.0 | **+15** |

**Total score → priority tier:**

| Score | Tier | Action |
|---|---|---|
| ≥ 100 | P0 | Immediate validation; surface in engagement summary now. |
| 70–99 | P1 | Validate this engagement; include in technical report. |
| 40–69 | P2 | Mention in technical report; validate if time permits. |
| < 40 | P3 | List in appendix; no validation expected. |

### 28.3 Validation discipline

- **Validate** = run a single read-only proof (e.g., a version banner check, a static-page fetch that confirms the vulnerable component) **without** triggering exploitation.
- **Do NOT** run the actual exploit unless the rules of engagement explicitly permit. Many bug bounty programs forbid PoC execution against production.
- For client engagements: deliver the prioritized list with reproduction commands but defer actual exploitation to a follow-on assessment if needed.

### 28.4 Handle CVE-less findings

Many real-world findings (sourcemap exposure, open GraphQL introspection, public bucket) don't have a CVE. Score them by their independent interest score (companion skill §20 for endpoints; §40 for severity-mapping examples). Don't gate on CVE availability.

---
