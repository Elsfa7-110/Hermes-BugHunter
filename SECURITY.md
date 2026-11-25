# Security Policy

## Intended use

This repository contains security-research methodology, vulnerability-class guidance, payload examples, recon references, validation checklists, reporting templates, and optional local tooling. Use it only for:

- assets you own;
- bug-bounty assets explicitly listed in an active program scope;
- contracted assessments with written authorization and rules of engagement;
- controlled labs, CTFs, and deliberately vulnerable applications.

Confirm the exact target and permitted methods before sending traffic. Discovery of a hostname, IP address, cloud resource, third-party integration, or vendor endpoint does not by itself make that system in scope.

## Safety boundaries

The skills and tools are not intended for unauthorized access, service disruption, mass exploitation, credential stuffing, fraud, persistence, malware deployment, or extraction of unrelated users' data. Avoid destructive or state-changing actions unless they are expressly authorized and necessary. Respect rate limits and stop conditions. When a finding cannot be demonstrated safely within scope, document the limitation instead of escalating activity.

## Evidence handling

Treat requests, responses, browser captures, HAR files, screenshots, and logs as sensitive. Redact session cookies, bearer tokens, API keys, passwords, private customer data, and unrelated personal information before storage or submission. Keep only the minimum evidence needed to demonstrate impact.

## Supply-chain review

Skills and helper scripts are executable instructions or code. Review them before use, especially scripts that access the network, invoke local tools, or modify files. The included lint checks validate structure and selected secret/identifier patterns; they are not a malware or prompt-injection detector and do not guarantee safety.

The copy helpers only copy the repository's `skills/` directory into `~/.hermes/skills/`. They do not configure models, providers, API keys, or Hermes MCP servers.

## Reporting a repository issue

For a vulnerability in this repository itself, use the repository's private security-reporting channel if one is configured by its maintainer. Do not place exploit details, credentials, or sensitive target data in a public issue.

## Responsible-use expectations

By using this material, you are responsible for ensuring that every target and action is authorized, respecting program rules and applicable law, minimizing impact on users and services, protecting captured data, and disclosing findings through the target's approved process.

## License and liability

The code and content are provided under the licenses identified in `LICENSE`, `LICENSE-CONTENT`, and `NOTICE`, without warranty. Users are responsible for their own testing decisions and compliance with all applicable rules and laws.
