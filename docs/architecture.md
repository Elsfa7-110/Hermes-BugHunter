# Architecture

The bundle organizes security research into six connected phases. The workflow is flexible: a researcher can start at any phase, but scope and authorization remain mandatory.

1. **Scope** — identify allowed assets, exclusions, restrictions, and test accounts.
2. **Recon** — discover in-scope services, technologies, endpoints, and parameters.
3. **Hunt** — select relevant vulnerability-class and platform skills.
4. **Validate** — establish reproducible security impact and eliminate false positives.
5. **Capture** — record the minimum evidence needed while redacting sensitive data.
6. **Report** — prepare a clear, reproducible, responsible disclosure or client report.

The library currently contains **98 skills**, including **58 `hunt-*` skills**. [`docs/skills.md`](skills.md) is generated from the skill frontmatter.

## Runtime and data flow

Hermes Agent loads skill directories from `$HERMES_HOME/skills/` (or `~/.hermes/skills/`). Each skill contains a `SKILL.md` plus any supporting reference documents, templates, helper scripts, or assets. Hermes indexes one line per skill and loads the body on demand; installed skills are also slash commands.

The optional Python engagement engine handles deterministic scope checks, recon orchestration, ranking, and state persistence. When active hunting is explicitly enabled, it calls the Hermes CLI using the model selected in the current Hermes profile. It does not configure the provider or credentials.

## Progressive disclosure

A skill is a small routing document with deep references behind it:

- `SKILL.md` — what the skill covers, the decision rules, the confirmation bar, and a
  "Where the detail lives" table when the material is long.
- `references/*.md` — payload corpora, vendor matrices, per-platform templates, and
  case catalogues. Loaded one file at a time with
  `skill_view("<skill>", "references/<file>")`.

This keeps the cost of selecting a skill to roughly its index line, and the cost of
using it to the one chapter the task actually needs. `scripts/hermes_compat.py`
warns when a body grows past the point where splitting is worth it.

## Data flow overview

```text
Authorized scope
      │
      ▼
Reconnaissance ──► Asset and endpoint map ──► Skill selection
                                              │
                                              ▼
                                      Controlled testing
                                              │
                                              ▼
                                   Evidence and validation
                                              │
                                              ▼
                                         Reporting
```

## Components

| Component | Responsibility |
|---|---|
| `skills/` | knowledge, procedures, and task-specific workflow skills |
| `bundles/` | Hermes skill-bundle YAML for one-command multi-skill loading |
| `commands/` | human-readable workflow source files retained with the bundle |
| `engine/` | deterministic scope-aware engagement orchestration |
| `cbh/` | deterministic classification, recon, and report helpers |
| `mcp/` | optional HackerOne MCP server |
| `scripts/` | installer, Hermes compatibility gate, engagement scaffold, generators |
| `tests/` | unit tests, doc-consistency checks, routing smoke prompts |

See [`engine/README.md`](../engine/README.md) for runtime details and [`hermes.md`](hermes.md) for skill loading.
