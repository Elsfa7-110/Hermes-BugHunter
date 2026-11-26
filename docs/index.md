---
title: Home
nav_order: 1
---

# Hermes-BugHunter

**98 Agent Skills** for bug bounty research and authorized external security assessments, built for Hermes Agent with the model already configured in your Hermes profile.

## Contents

- [Skill catalog](skills.md) — searchable list of every bundled skill.
- [Usage guide](../USAGE.md) — an end-to-end security-research workflow.
- [Hermes Agent guide](hermes.md) — install, verify, invoke, and troubleshoot.
- [Architecture](architecture.md) — workflow phases and component map.
- [Recon manifest](recon-manifest.md) — the recon-to-hunt handoff format.
- [Command-line tools](cbh-cli.md) — optional `cbh` usage.
- [Contributing](../CONTRIBUTING.md) — authoring rules and the gates.
- [Security policy](../SECURITY.md) — authorized-use and evidence-handling boundaries.

## Quick install

```bash
git clone https://github.com/Elsfa7-110/Hermes-BugHunter.git
cd Hermes-BugHunter
bash scripts/install.sh
```

The installer resolves `$HERMES_HOME` (or `--profile <name>`), copies into `skills/hermes-bughunter/`, warns about name collisions with other bundles in the profile, and verifies that every skill resolves. `--dry-run` previews, `--uninstall` removes.

The repository does not configure the model, provider, credentials, or Hermes profile. Start a new Hermes session after installing.
