# DeepSeek BugHunter — Usage Guide

This guide explains how to use the 98 Hermes Agent skills as a structured security-research workflow. The skill library is installed in `~/.hermes/skills/`; Hermes uses the model and tools already configured in your profile.

## 1. Start with scope

Before testing, identify the exact program or engagement, the allowed hosts, excluded hosts, accepted vulnerability classes, rate limits, test-account requirements, and prohibited actions. Use `/scope` to inspect or record scope. A wildcard such as `*.example.com` must not be treated as permission to test unrelated third-party services discovered during reconnaissance.

Recommended opening prompt:

```text
I am assessing example.com under an authorized program. First establish the
scope, exclusions, allowed test methods, and rate limits. Do not send requests
until the target list is confirmed.
```

## 2. Reconnaissance

Use `/recon example.com` for a recon workflow, or ask Hermes to enumerate and classify the assets and endpoints already authorized by the program. Relevant skills include:

- `offensive-osint` — external discovery, identity-fabric mapping, exposed services, public data, and secret triage.
- `osint-methodology` — an organized recon process and attack-surface map.
- `web2-recon` — web host discovery, URL collection, and application mapping.
- `recon-scope-triage` — ownership and scope filtering for candidate assets.

Keep passive discovery separate from active probing. Do not test newly discovered hosts until ownership and program scope are confirmed.

## 3. Choose a vulnerability class

The `hunt-*` library contains class-specific techniques. Examples:

| Signal or feature | Skills to consider |
|---|---|
| Object IDs, user IDs, tenant IDs | `hunt-idor`, `hunt-business-logic`, `hunt-api-misconfig` |
| Redirect parameters and callback URLs | `hunt-open-redirect`, `hunt-oauth` |
| URL fetchers, importers, webhook previews | `hunt-ssrf` |
| Search fields and dynamic filters | `hunt-sqli`, `hunt-nosqli`, `hunt-xss` |
| GraphQL endpoints | `hunt-graphql`, `hunt-fintech-graphql` |
| JWT and session tokens | `hunt-jwt-crypto`, `hunt-session`, `hunt-auth-bypass` |
| File uploads and document processing | `hunt-file-upload`, `hunt-xxe`, `hunt-deserialization` |
| CI/CD and cloud configuration | `hunt-cicd`, `hunt-cloud-misconfig`, `hunt-k8s` |
| LLM-powered application features | `hunt-llm-ai`, `hunt-rag-vector` |

You can invoke a skill directly, or describe the observation and let Hermes select the relevant skill from its description. Example:

```text
The API accepts /api/orders/<built-in function id>. I have two test accounts. Help me check
whether an authenticated user can read another account's order, using only
in-scope test accounts and read-only requests.
```

## 4. Use the workflow commands

The command workflows are available as Hermes skills:

| Command | Purpose |
|---|---|
| `/hunt` | Dispatch a target assessment into the appropriate testing workflow. |
| `/autopilot` | Organize a full engagement sequence with review checkpoints. |
| `/recon` | Start asset and application reconnaissance. |
| `/surface` | Prioritize discovered endpoints and potential attack paths. |
| `/chain` | Explore whether independently confirmed findings can be combined. |
| `/intel` | Gather relevant public advisories and disclosed-report context. |
| `/token-scan` | Review token and smart-contract risk indicators. |
| `/triage` | Run a quick 7-question finding gate. |
| `/validate` | Perform the deeper validation workflow. |
| `/report` | Draft a submission or assessment report. |
| `/remember`, `/pickup`, `/memory-gc` | Save, restore, or clean up engagement notes. |
| `/scope` | Inspect or record authorized scope and exclusions. |

## 5. Validate before reporting

Run `/triage` or `/validate` before writing a report. A strong finding should have:

1. An exact in-scope asset and reproducible request sequence.
2. A clear precondition and attacker capability.
3. A response or observable behavior demonstrating the security impact.
4. A realistic impact explanation, not just a suspicious status code or theoretical possibility.
5. No reliance on touching an out-of-scope system or another user's data beyond the minimum permitted proof.

If safe proof requires a prohibited or state-changing action, stop and document the limitation rather than carrying it out.

## 6. Capture evidence and write the report

Use `evidence-hygiene` before capturing screenshots, exporting HAR files, or sharing logs. Redact session cookies, authorization headers, API keys, private tokens, and unnecessary personal information. Keep enough request and response context for a reviewer to reproduce the issue with authorized test accounts.

Use `report-writing` for the core report structure and `bugcrowd-reporting` for Bugcrowd-specific VRT mapping and severity reasoning. Do not auto-submit: review the report and submit it through the program's official channel yourself.

## 7. Optional command-line tools

The `cbh` utility provides deterministic recon classification, scope import, and report helpers. The Python engagement engine provides map-first recon and opt-in hunt/validate phases. Neither is needed for Hermes to load the skills.

- [`cbh` CLI guide](docs/cbh-cli.md)
- [Engagement engine guide](engine/README.md)
- [Architecture overview](docs/architecture.md)

## Operational discipline

Only test systems you own or are explicitly authorized to assess. Honor program scope, safe-harbor conditions, rate limits, and stop-work instructions. Never use the skills to disrupt services, harvest credentials, access unrelated accounts, persist in systems, or extract data beyond the minimum required proof.
