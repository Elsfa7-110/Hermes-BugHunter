---
title: Hermes Agent
nav_order: 3
description: Load the bundle's Agent Skills in Hermes Agent.
---

# Hermes Agent

The bundle uses the Agent Skills format supported by Hermes Agent. Place each skill directory under `~/.hermes/skills/`; keep the directory's `SKILL.md` and any nested `references/`, `templates/`, `scripts/`, or `assets/` files together.

## Copy on Linux

```bash
mkdir -p ~/.hermes/skills
cp -a skills/. ~/.hermes/skills/
```


## Invoke a skill

Every installed skill is also available as a slash command in Hermes. Examples:

```text
/hunt example.com
/recon example.com
/triage
/validate
/report
```

Skills can also be selected automatically from the user's task based on their descriptions. Open a new conversation after copying the library so the session loads the current set of skills.

## Model and credentials

Hermes continues to use the provider, model, and credentials already selected in the active profile. The skills do not select a model, request credentials, or change any profile settings.

## MCP tools

The optional engagement workflows can use tools that are already connected to Hermes, such as a Burp Suite MCP server. This repository does not install or configure MCP servers as part of the skill-copy operation. Follow the official [Hermes MCP guide](https://hermes-agent.nousresearch.com/docs/guides/use-mcp-with-hermes) for any separate integration you choose to use.

## Official documentation

- [Hermes Agent skills system](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills)
- [Hermes Agent CLI](https://hermes-agent.nousresearch.com/docs/user-guide/cli)
- [Hermes Agent MCP guide](https://hermes-agent.nousresearch.com/docs/guides/use-mcp-with-hermes)
