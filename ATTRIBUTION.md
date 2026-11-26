# Attribution

The skills are written from public security research. Each `SKILL.md` records its
own provenance in frontmatter:

```yaml
sources: github, hackerone_public
report_count: 174
```

`sources` names the kind of material the skill was built from; `report_count`
counts the disclosed reports behind a `hunt-*` skill (`0` for pattern libraries
and research-derived skills). `scripts/lint_skills.py` enforces both fields.

## Research and report material

- Disclosed bug-bounty reports on HackerOne, Bugcrowd, Intigriti, and Immunefi,
  and public write-ups by their authors. Individual findings are cited in the
  skill that uses them; report counts are aggregates, not endorsements.
- Published security research, including PortSwigger research (HTTP desync and
  request smuggling, web cache deception/poisoning, DOM clobbering and DOM
  Invader), OWASP guidance (Top 10, API Security Top 10, LLM Top 10, Agentic
  Applications), and vendor advisories and CVE records (NVD, GitHub Advisories).
- Community references such as HackTricks, PayloadsAllTheThings, SecLists, and
  HowToHunt, which are used as pointers rather than copied wholesale.

## Tooling referenced

The skills name tools their authors do not maintain: ProjectDiscovery
(`subfinder`, `httpx`, `dnsx`, `nuclei`, `katana`), `ffuf`, `gf`, `dalfox`,
`sqlmap`, `arjun`, `trufflehog`, `gitleaks`, `ysoserial`, `phpggc`, Burp Suite
extensions, `interactsh`, Foundry, and others. Each is governed by its own
license and documentation; install and use them under those terms.

## Corrections

If a skill misattributes work, or a citation is wrong, open an issue with the
correct source. Attribution fixes are welcome and take priority over new content.

## No client material

The repository deliberately contains no client names, engagement identifiers, or
target data. `scripts/lint_skills.py` checks a hashed denylist of identifiers
before content can land; see `SECURITY.md` for the evidence-handling rules.
