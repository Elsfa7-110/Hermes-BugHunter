# Copy the skills into Hermes Agent (Linux)

This bundle is intended for Linux systems running Hermes Agent. It uses the model and provider already selected in your Hermes profile. It does not configure DeepSeek, create API credentials, or edit Hermes configuration.

## Copy the skills

Open a terminal in the extracted repository directory and run:

```bash
mkdir -p "$HOME/.hermes/skills"
cp -a skills/. "$HOME/.hermes/skills/"
```

The `/.` after `skills` is intentional: it copies the contents of `skills/` directly into the Hermes skills directory, preserving every skill folder and its nested references, scripts, templates, and assets.

## Optional Bash copy helper

The included helper performs the same copy operation and nothing else:

```bash
bash scripts/install.sh --dry-run
bash scripts/install.sh
```

By default, existing skill directories are left untouched. Use `--force` only when you intend to replace same-named skills with the versions in this bundle. Review local customizations first.

## Start using the skills

Start a new Hermes session. Each skill in `~/.hermes/skills/` is available on demand and can be invoked by its slash command, for example:

```text
/hunt example.com
/recon example.com
/triage
/validate
/report
```

Always confirm written authorization and scope before active testing.

## What this does not change

The copy operation does not:

- install or update Hermes Agent;
- change the model or provider selected in Hermes;
- request, read, or write a provider API key;
- edit `~/.hermes/config.yaml`, `.env`, or any MCP configuration;
- install external tools such as Burp Suite, `httpx`, `nuclei`, or `katana`.

The optional Python engine and `cbh` CLI have separate documentation and are not required to load or use the skills.
