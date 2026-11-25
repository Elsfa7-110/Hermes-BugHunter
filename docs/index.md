---
title: Home
nav_order: 1
---

# DeepSeek BugHunter

**98 Agent Skills** for bug bounty research and authorized external security assessments, designed for Hermes Agent with the model already configured in your Hermes profile.

## Contents

- [Skill catalog](skills.md) — searchable list of every bundled skill.
- [Usage guide](../USAGE.md) — an end-to-end security-research workflow.
- [Hermes Agent guide](hermes.md) — copy and invoke skills in Hermes.
- [Architecture](architecture.md) — workflow phases and component map.
- [Recon manifest](recon-manifest.md) — the recon-to-hunt handoff format.
- [Command-line tools](cbh-cli.md) — optional `cbh` usage.
- [Security policy](../SECURITY.md) — authorized-use and evidence-handling boundaries.

## Quick copy

Linux:

```bash
mkdir -p ~/.hermes/skills
cp -a skills/. ~/.hermes/skills/
```


The repository does not configure the model, provider, credentials, or Hermes profile. Start a new Hermes session after copying the skills.
