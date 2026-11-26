# INSTALLATION (Hermes Agent Skill)

This skill ships in the Hermes-BugHunter bundle. Install the whole bundle from
the repository root:

```bash
bash scripts/install.sh          # -> $HERMES_HOME/skills/hermes-bughunter/
```

The installer resolves the profile, warns about name collisions with other
skills already installed, and verifies that every skill loads. Hermes discovers
it on the next session; keep `SKILL.md` and its `references/` directory
together. Details: `docs/hermes.md`.

---

## Related Skills & Chains

- **`bb-methodology`** — When a hunting session starts and the user is "lost about what to do next." Workflow primitive: this skill is the orchestrator; `bb-methodology` is the 5-phase workflow it routes to. Load `bb-methodology` FIRST, then this skill names the topic-matched hunt-* skills.
- **`hunt-dispatch`** — When PART 0 mode (red team / WAPT) has been confirmed. Workflow primitive: this skill's "what should I do" routing hands off to `hunt-dispatch` for the platform fingerprint + skill-set load.
- **`web2-recon`** + **`offensive-osint`** — When Phase 1 (recon) starts. Workflow primitive: this skill's "Standard Recon Pipeline" section delegates the live execution to `web2-recon` and the operational arsenal (probes / wordlists / regexes) to `offensive-osint`.
- **`triage-validation`** + **`report-writing`** — When a finding completes Phase 4. Workflow primitive: this skill routes to `triage-validation` (7Q gate) → only if all 7 pass, hand off to `report-writing` for the platform-specific body.

---

## Operator Notes (Hermes-BugHunter)

> Engagement-derived additions to the vendored foundation. Wisdom from real
> authorized engagements + Phase 2 verification across this repo's 31+
> skill-area live tests. The upstream methodology covers the WHAT; this
> layer covers the WHEN-IT-ACTUALLY-WORKS and the FAILURE-MODES.

### When to use the orchestrator vs a direct skill

The orchestrator (this skill) is for the "I don't yet know what bug class to hunt for" case. If you've already identified the candidate — "the response reflects my Host header into a JavaScript src URL, that's cache poisoning" — load `hunt-cache-poisoning` directly. The orchestrator's value is the initial routing from a fuzzy intent ("there's a chatbot, what should I test") to a concrete skill set (`hunt-llm-ai` + `hunt-api-misconfig`).

When in doubt: open the orchestrator FIRST on any new target, let it route, then close the orchestrator and work in the loaded skills. Don't keep the orchestrator loaded all session — it occupies context window that could hold actual probe results.

### Common misuse: loading every hunt-* simultaneously

There are 58 hunt-* skills in this repo. Each carries a non-trivial context footprint. The orchestrator's job is to pick 2-3 by topic match, not to dump the entire library. If the user says "hunt this SaaS app", do NOT load every hunt-* skill — pick `web2-recon` + `hunt-idor` + `hunt-api-misconfig` (the SaaS-typical trio) and stop there. Add more only when the recon output suggests a specific additional class (e.g., GraphQL endpoints found → add `hunt-graphql`).

### Integration with hunt-dispatch

This skill routes by **bug class** (topic match). The `hunt-dispatch` skill added in this repo routes by **engagement mode** (red-team vs WAPT, blackbox vs greybox). They compose:

1. User says "hunt example.com"
2. `bb-methodology` PART 0 confirms mode (e.g., bug-bounty blackbox)
3. `hunt-dispatch` loads the platform-specific attack profile
4. This orchestrator (`bug-bounty`) names the topic-matched hunt-* skills inside the chosen profile

Don't bypass either step. Mode determines what counts as a finding; topic determines what techniques apply.

### Engagement scaffolding

The `/hunt` slash-command and the `hunt <target>` shell helper (see this repo's `cmd/` directory) pre-create the engagement scaffold:

- `targets/<target>/scope.md` — declared scope, pasted from the program page
- `targets/<target>/findings/` — one MD per validated finding
- `targets/<target>/evidence/` — HARs, screenshots, redacted curl transcripts
- `targets/<target>/submissions.txt` — log of submitted-report URLs + states
- `targets/<target>/recon/` — outputs from `subfinder | dnsx | httpx | katana`

Use the scaffold from the start. Half-organized engagements lose findings — a probe result from hour 2 that didn't seem important until hour 14 is unrecoverable if it wasn't logged.

### When the orchestrator gets it wrong

Across the bundle's live verification tests in this repo, the orchestrator correctly auto-triggered the matching skill in every test — zero misfires. If on a future target the orchestrator misroutes (loads the wrong hunt-* for the topic), the cause is almost always the `description:` frontmatter field on the target skill: a missing keyword that would have matched the user's intent. Fix forward by editing that skill's frontmatter `description:` field to include the missing trigger word. Don't add another layer of dispatch logic; tighten the description.
- **`bb-local-toolkit`** — When you need to know which local clone has the tool for a given task. Workflow primitive: this skill is general bug-bounty guidance; `bb-local-toolkit` answers the specific "where is jhaddix/SecLists installed on this machine?" question.
