![Hermes BugHunter](assets/banner.jpeg)

# Hermes BugHunter

**98 Agent Skills** for bug bounty research, web application security testing, external attack-surface assessment, validation, and reporting — built to be loaded by Hermes Agent with whatever model your profile already uses.

The bundle includes **58 `hunt-*` skills**, recon and OSINT references, enterprise-platform assessment playbooks, smart-contract review material, reporting templates, and a deterministic engagement engine.

## What it does

- **Plan and scope:** organize targets, rules of engagement, and authorized assets before testing.
- **Recon:** discover and classify external assets, endpoints, parameters, technologies, and exposed information.
- **Hunt:** load class-specific techniques for IDOR, SSRF, SQL injection, XSS, OAuth, GraphQL, race conditions, cloud misconfiguration, and 50 more classes.
- **Validate:** distinguish reproducible security impact from weak signals and false positives.
- **Capture and report:** preserve reproducible evidence, redact sensitive information, and prepare platform-ready reports.
- **Coordinate:** engagement workflows, hunt memory, and an optional deterministic engine for tracking and prioritizing work.

Skills are plain `SKILL.md` directories. Hermes discovers them, indexes each description, and loads the full body only when the task needs it. Every skill is also a slash command — `/hunt`, `/recon`, `/triage`, `/report` — and skills can chain naturally in conversation.

## Install

Requirements: Hermes Agent, `git`, `python3` (stdlib only — no pip install for the skills themselves).

```bash
git clone https://github.com/Elsfa7-110/Hermes-BugHunter.git
cd Hermes-BugHunter
bash scripts/install.sh            # add --dry-run to preview the copy
```

The installer:

- resolves `$HERMES_HOME` (and `--profile <name>`) instead of assuming `~/.hermes`;
- copies the bundle into `skills/hermes-bughunter/` so the tree is identifiable, upgradeable, and removable (`--uninstall`);
- **checks for name collisions before copying** — if another bundle in the same profile already owns a name such as `hunt-xss` or `recon`, Hermes refuses the bare name and registers no `/command`; the installer reports every collision and the exact path form that still loads;
- verifies after copying that all 98 skills resolve, and fails loudly if any does not.

Start a new Hermes session afterwards so the skill index is rebuilt.

> **Running several bug-bounty bundles?** Give this one its own profile — that is how Hermes keeps skill names unique:
> ```bash
> hermes profile create bughunter
> bash scripts/install.sh --profile bughunter
> hermes profile use bughunter              # sticky default
> # or one-off: HERMES_HOME=~/.hermes/profiles/bughunter hermes
> ```
> A shared profile is fine too: colliding skills still load via `skill_view("hermes-bughunter/hunt-xss")`, they just lose the short slash command.

Preview without changing anything: `bash scripts/install.sh --dry-run`.
Upgrade later: `git pull && bash scripts/install.sh --force`.

## Verify the install

```bash
python3 scripts/hermes_compat.py     # loader rules: names, aliases, frontmatter, links
python3 scripts/hermes_compat.py --json > /tmp/compat.json
```

`hermes_compat.py` mirrors what Hermes actually enforces when it builds the skill index: unique names within a tier, `name` matching the directory, description length, support-directory pruning, and relative links that resolve. It exits non-zero on anything that would make a skill unloadable.

Inside Hermes:

```text
/skills                 # the installed skill list
/skill hunt-idor        # load one skill by name
/hunt app.example.com   # the two-track hunting dispatcher
```

Optional routing check: paste prompts from [`tests/smoke-test-prompts.md`](tests/smoke-test-prompts.md) into a fresh session and confirm the expected skill loads first.

## Main skills and workflows

| Area | Examples |
|---|---|
| Methodology | `bb-methodology`, `bug-bounty`, `redteam-mindset` |
| Recon and OSINT | `offensive-osint`, `osint-methodology`, `web2-recon`, `recon-scope-triage` |
| Vulnerability classes | 58 `hunt-*` skills covering web, API, cloud, and AI surface |
| Enterprise assessments | `m365-entra-attack`, `okta-attack`, `enterprise-vpn-attack`, `vmware-vcenter-attack`, `cloud-iam-deep` |
| Mobile and supply chain | `apk-redteam-pipeline`, `ios-redteam-pipeline`, `supply-chain-attack-recon` |
| Smart contracts | `web3-audit`, `meme-coin-audit` |
| Validation and reporting | `triage-validation`, `evidence-hygiene`, `report-writing`, `bugcrowd-reporting` |
| Engagement workflows | `autopilot`, `hunt`, `recon`, `scope`, `surface`, `chain`, `intel`, `pickup`, `remember`, `memory-gc`, `token-scan`, `triage`, `validate`, `report` |

Full catalog: [`docs/skills.md`](docs/skills.md). Recommended order of work: [`USAGE.md`](USAGE.md). Hermes specifics: [`docs/hermes.md`](docs/hermes.md).

## Optional skill bundles

Hermes can load several skills under one command. Install them with the bundle flag, or copy the YAML yourself:

```bash
bash scripts/install.sh --bundles          # -> $HERMES_HOME/skill-bundles/
# or: cp bundles/*.yaml ~/.hermes/skill-bundles/
```

Then `/bughunt-start`, `/bughunt-report`, `/bughunt-web`, and `/redteam-engagement` each load their member skills in one turn.

## Optional deterministic tools

The repository also ships a Python CLI (`cbh`) and a deterministic engagement engine under `engine/`. Neither is required to load or use the skills. See [`docs/cbh-cli.md`](docs/cbh-cli.md) and [`engine/README.md`](engine/README.md).

```bash
pip install -e .            # exposes the `cbh` command
cbh --help
```

The engine delegates reasoning to the active Hermes CLI profile and uses its currently selected model and credentials. It does not configure providers or change model settings.

## Authorized-use boundary

Use these skills only for systems you own, explicitly authorized bug-bounty targets, contracted assessments, or controlled labs and CTFs. Confirm the exact scope and rules of engagement before sending traffic. Respect exclusions, rate limits, data-handling requirements, and stop conditions. Do not use the material for unauthorized access, disruption, credential abuse, persistence, or data extraction.

See [`SECURITY.md`](SECURITY.md) for the security policy and safe-use boundaries.

## Project files

- `skills/` — all 98 skill directories, with `references/`, `templates/`, and helper material.
- `commands/` — source workflow descriptions; their Hermes-facing forms are included as skills.
- `bundles/` — Hermes skill-bundle YAML for one-command multi-skill loading.
- `engine/` — scope-aware engagement orchestration and validation.
- `cbh/` — deterministic command-line utilities.
- `mcp/` — optional HackerOne MCP server.
- `scripts/` — installer, Hermes compatibility gate, engagement scaffolding, and index generators.
- `tests/` — unit tests, doc-consistency checks, and routing smoke prompts.
- `eval/` — local-lab evaluation harnesses and fixtures.
- `docs/` — methodology, architecture, skill catalog, and technical references.

## Development

```bash
python3 scripts/lint_skills.py        # structure, YAML safety, secrets, identifiers
python3 scripts/hermes_compat.py      # Hermes loader rules
python3 scripts/check_doc_counts.py   # README/docs counts vs disk
python3 -m pytest -q                  # unit + consistency tests
```

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the skill-authoring rules (including the 60-character index line that Hermes shows for every skill).

## Licensing

Code is covered by the MIT license in [`LICENSE`](LICENSE). Skill and documentation content is covered by [`LICENSE-CONTENT`](LICENSE-CONTENT); required attribution and change notes are collected in [`ATTRIBUTION.md`](ATTRIBUTION.md), with a third-party notice in [`NOTICE`](NOTICE).
