# Smoke-test prompts

Routing checks for a fresh install: paste a prompt into Hermes and confirm the
skill named on the right is the first one loaded. They are written the way a
researcher actually talks — no skill name in the prompt — so a pass proves the
description alone carried the signal.

Run the whole file after installing or renaming a skill. `pytest` also parses
it (`tests/test_smoke_prompts.py`) to prove every skill it names exists.

## Engagement workflow

| Prompt | Expected first skill |
|---|---|
| `/hunt app.example.com` | `hunt` |
| `I'm about to start a bug bounty on a new target and I don't know where to begin` | `bb-methodology` |
| `show me the ranked attack surface for example.com` | `surface` |
| `is api.example.com in scope for this program?` | `scope` |
| `pick up where I left off on example.com` | `pickup` |
| `what CVEs and disclosed reports exist for example.com?` | `intel` |
| `chain this open redirect into something bigger` | `chain` |
| `run the autonomous loop against example.com, paranoid mode` | `autopilot` |

## Recon

| Prompt | Expected first skill |
|---|---|
| `/recon example.com` | `recon` |
| `enumerate subdomains and crawl everything live for example.com` | `web2-recon` |
| `these ASM results look like they belong to another company with the same name` | `recon-scope-triage` |
| `give me dorks, probes and regexes for finding leaked secrets` | `offensive-osint` |
| `plan an OSINT workstream for an external red team` | `osint-methodology` |
| `this JS bundle must call a hidden backend API somewhere` | `hunt-spa-api` |
| `I found a .js.map file — what can I get from it?` | `hunt-source-leak` |

## Vulnerability classes

| Prompt | Expected first skill |
|---|---|
| `the id parameter lets me read another user's invoice` | `hunt-idor` |
| `the image URL parameter fetches internal addresses` | `hunt-ssrf` |
| `my name shows up unescaped in the profile page` | `hunt-xss` |
| `my HTML renders but the script tag doesn't execute` | `hunt-html-injection` |
| `quote in the search box changes the SQL error` | `hunt-sqli` |
| `login has no rate limit and the OTP is 6 digits` | `hunt-brute-force` |
| `can I skip the 2FA step by going straight to /dashboard?` | `hunt-mfa-bypass` |
| `password reset email uses the Host header` | `hunt-host-header` |
| `the redirect_uri accepts any domain` | `hunt-oauth` |
| `GraphQL endpoint answers introspection` | `hunt-graphql` |
| `uploading a .svg to the avatar endpoint` | `hunt-file-upload` |
| `the coupon can be applied twice at once` | `hunt-race-condition` |
| `export endpoint returns an Excel file — can I inject a formula?` | `hunt-business-logic` |
| `the S3 bucket behind the CDN is world-readable` | `hunt-cloud-misconfig` |
| `this AWS key came out of the bundle — what does it grant?` | `cloud-iam-deep` |
| `the chatbot reads uploaded PDFs and follows instructions inside them` | `hunt-llm-ai` |
| `the WebSocket handshake has no Origin check` | `hunt-websocket` |
| `the cache serves my reflected payload to other users` | `hunt-cache-poison` |
| `the Spring Boot app exposes /actuator/heapdump` | `hunt-springboot` |
| `this is an on-prem SharePoint farm` | `hunt-sharepoint` |
| `I have an Android APK in scope` | `apk-redteam-pipeline` |
| `there's a Solidity contract in scope` | `web3-audit` |

## Validation and reporting

| Prompt | Expected first skill |
|---|---|
| `is this finding worth submitting?` | `triage` |
| `validate this before I write it up` | `validate` |
| `run the 7-question gate on this IDOR` | `triage-validation` |
| `write the HackerOne report for this finding` | `report-writing` |
| `/report` | `report` |
| `the triager says it's OOS because of rate limiting` | `bugcrowd-reporting` |
| `I need to blur the victim's session cookie in my screenshot` | `evidence-hygiene` |

## Red team

| Prompt | Expected first skill |
|---|---|
| `we're doing an external red team, not a bug bounty` | `redteam-mindset` |
| `the client patched the SQLi while I was testing` | `mid-engagement-ir-detection` |
| `format the final findings into the client's report template` | `redteam-report-template` |
| `the perimeter has a Cisco ASA` | `enterprise-vpn-attack` |
| `I found Okta at tenant.okta.com` | `okta-attack` |
| `spray these credentials against Entra ID without locking accounts` | `m365-entra-attack` |
| `the vCenter login page is internet-facing` | `vmware-vcenter-attack` |
| `external recon for package-namespace squatting` | `supply-chain-attack-recon` |

## Chaining and persistence

| Prompt | Expected first skill |
|---|---|
| `remember that the /v2/graphql endpoint needs an API key` | `remember` |
| `the autopilot ledger files are getting big` | `memory-gc` |
| `scan this token contract for rug-pull vectors` | `token-scan` |
