---
title: Hermes Agent
nav_order: 3
description: Install, verify, and invoke the bundle in Hermes Agent.
---

# Hermes Agent

The bundle uses the Agent Skills format Hermes reads: one directory per skill with a `SKILL.md` (YAML frontmatter + markdown body) and optional `references/`, `templates/`, `assets/`, and `scripts/` next to it.

Hermes discovers skills by walking the skills directory, so nesting is allowed and encouraged — the installer puts everything under `skills/hermes-bughunter/`, which also becomes the category label in the skill list.

## Install

```bash
git clone https://github.com/Elsfa7-110/Hermes-BugHunter.git
cd Hermes-BugHunter
bash scripts/install.sh                 # -> $HERMES_HOME/skills/hermes-bughunter/
bash scripts/install.sh --dry-run       # show the plan, change nothing
bash scripts/install.sh --profile bbh   # -> $HERMES_HOME/profiles/bbh/skills/hermes-bughunter/
bash scripts/install.sh --force         # after `git pull`, replace changed skills
bash scripts/install.sh --uninstall     # remove the namespaced tree
```

`$HERMES_HOME` is used when set; otherwise `~/.hermes`. Nothing is written outside the destination skills directory, and no model, provider, credential, or MCP setting is touched.

Open a new Hermes session after installing — the skill index is built per session.

## Why not `cp -a skills/. ~/.hermes/skills/`?

You can, and it works in a profile that has no other security bundle. It breaks in a profile that does, and the failure is quiet:

- Hermes resolves a skill by **declared name, directory name, or relative path**, in one tier.
- If two skills claim `hunt-xss`, the bare name is *ambiguous*: `skill_view("hunt-xss")` refuses it and no `/hunt-xss` command is registered. The relative path (`hermes-bughunter/hunt-xss`) still works.
- If two skills share both name **and** relative path (two roots mounted the same way), the skill is unloadable and the system prompt lists it with a rename note.

The installer detects this before copying and prints, per collision, the form that still loads. `scripts/hermes_compat.py` enforces the same rules in CI.

### Cleanest fix: a dedicated profile

```bash
hermes profile create bughunter
bash scripts/install.sh --profile bughunter
hermes profile use bughunter
```

Profile skills live in `$HERMES_HOME/profiles/bughunter/skills/`; that profile sees only this bundle, so all 98 skills keep their short names and slash commands. Switch back with `hermes profile use default`.

## Invoke a skill

```text
/hunt app.example.com          # two-track dispatcher
/recon app.example.com         # deterministic recon pipeline
/scope api.example.com         # deny-wins scope check before any traffic
/triage                       # 7-Question Gate on the current finding
/report                       # submission-ready report
```

Every skill is also reachable as an explicit load, which is what the model does when a description matches the task:

```text
/skill hunt-idor
/skill hermes-bughunter/hunt-idor     # path form, when the bare name is shared
```

Skills are loaded on demand: the index costs one line each, and the body is read only when the skill is selected. Skills whose body exceeds ~500 lines keep reference material in `references/`, which Hermes reads with `skill_view(name, file_path)` — one extra call instead of every load.

## Descriptions are the routing layer

Hermes shows roughly the first 60 characters of each description in the skill index (`skills.index_desc_limit`, default 60). The bundle is written so that the trigger and the action fit in that window:

```yaml
description: "SSRF: metadata, DNS rebinding, gopher, PDF render. Built from 15 public reports, ..."
```

If you add a skill or edit a description, keep the first sentence self-contained and under 60 characters; `scripts/hermes_compat.py` warns when the index line ends mid-clause.

## Skill bundles

Hermes loads several skills under one command from YAML in `$HERMES_HOME/skill-bundles/`:

```yaml
name: bughunt-start
description: Start a new target: methodology, scope, recon, surface.
skills: [bb-methodology, scope, recon, surface]
instruction: Run the phases in order; stop if scope fails.
```

```bash
bash scripts/install.sh --bundles            # copies bundles/*.yaml too
# or by hand:
cp bundles/*.yaml "$HERMES_HOME/skill-bundles/"
```

Then `/bughunt-start example.com`. A bundle is an alias, not an install step — if a member skill is missing or ambiguous, it is skipped.

## Verify the install

```bash
# Repo-side gate: frontmatter, unique names, alias resolution, links
python3 scripts/hermes_compat.py

# Post-install resolution check (part of the installer, also standalone)
python3 scripts/hermes_install.py --dest "$HERMES_HOME/skills" --dry-run
```

In-session checks:

```text
/skills                 # installed skills and their categories
/skill hunt-xss         # loads one skill
```

Routing check: `tests/smoke-test-prompts.md` lists prompts and the skill each should load first. Paste a few into a fresh session after installing or renaming anything.

## Model and credentials

Hermes continues to use the provider, model, and credentials already selected in the active profile. The skills do not select a model, request credentials, or change any profile settings.

## MCP tools

Optional workflows can use tools already connected to Hermes, such as a Burp Suite MCP server. This repository does not install or configure MCP servers as part of the skill-copy step. Follow the official [Hermes MCP guide](https://hermes-agent.nousresearch.com/docs/guides/use-mcp-with-hermes) for any separate integration.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `/hunt-xss` is not a command | another bundle owns that name | load `skill_view("hermes-bughunter/hunt-xss")`, or use a dedicated profile |
| Skill missing from `/skills` | installed outside `$HERMES_HOME/skills`, or in a support dir (`references/`) | re-run the installer; keep `SKILL.md` at the skill root |
| Description looks cut off in the index | description longer than `skills.index_desc_limit` | front-load the trigger; raise the limit in `config.yaml` if you prefer |
| Old version still loads | session index was built before the copy | start a new session |
| `hermes_compat.py` reports duplicate names | the bundle was edited, or two roots were merged | rename one skill; the gate names both paths |

## Official documentation

- [Hermes Agent skills system](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills)
- [Hermes Agent CLI](https://hermes-agent.nousresearch.com/docs/user-guide/cli)
- [Hermes Agent MCP guide](https://hermes-agent.nousresearch.com/docs/guides/use-mcp-with-hermes)
