# Contributing

Changes are welcome: new `hunt-*` classes, sharper detections, corrected claims,
better routing descriptions. Three gates decide whether a change is accepted.

## Rules a skill must satisfy

A skill is a directory `skills/<name>/SKILL.md` with YAML frontmatter:

```yaml
---
name: hunt-example
description: "Example bugs: signal, payload, proof bar. Detail for the long tail."
sources: github, hackerone_public
report_count: 7
---
```

- `name` matches `^[a-z0-9][a-z0-9-]*$`, is at most 64 characters, and equals the
  directory name.
- **`description` is the routing layer.** Hermes shows about the first 60
  characters in the skill index, so the first sentence must name the trigger and
  the action and end before that window closes. Put disambiguation
  ("…, owned by hunt-xss") and provenance after it. Hard cap: 1024 characters.
- `sources:` is required (where the content comes from) and `report_count:` on
  every `hunt-*` skill (`0` is valid for a pattern library or research-derived
  skill).
- Names must be unique across the whole bundle. Two skills sharing a name make
  the bare name ambiguous in Hermes — no slash command, and `skill_view` refuses
  it.
- Keep the body under ~500 lines. Reference material (payload tables, vendor
  matrices, case catalogues) goes in `references/<topic>.md` and is pointed at
  from the body; Hermes reads it with `skill_view(name, "references/…")`.
- No client identifiers, engagement names, real credentials, or other users'
  data. `scripts/lint_skills.py` enforces this against a hashed denylist.

## Gates

```bash
python3 scripts/lint_skills.py        # structure, YAML safety, secrets, identifiers
python3 scripts/hermes_compat.py      # Hermes loader rules, unique names, links
python3 scripts/check_doc_counts.py   # README / docs counts vs disk
python3 -m pytest -q                  # unit + consistency tests
(cd engine && python3 -m pytest -q)   # engine tests run from their own directory
```

All of them must pass. CI runs the first four on every pull request
(`skill-lint.yml`, `hermes-compat.yml`, `doc-count-check.yml`,
`runtime-tests.yml`); `engine/` has its own pytest config because its modules
import each other by bare name.

## Editing an existing skill

- Prefer a targeted patch over a rewrite; the value of the library is the
  accumulated detail.
- If you change a description, check the first 60 characters still read as a
  complete instruction. `python3 scripts/hermes_compat.py` warns otherwise.
- If you add or rename a skill, regenerate the generated artifacts:

```bash
python3 scripts/gen_skill_catalog.py   # docs/skills.md
python3 scripts/gen_skill_index.py     # cbh/data/skill_index.json
```

and add a row to `tests/smoke-test-prompts.md` if the new skill has a distinct
trigger.

## Adding a vulnerability class

1. Check the matrix first (`docs/skills.md`) — the class may be covered by an
   existing skill; extend that one instead of adding an overlapping skill.
2. Write the signal → payload → confirmation-bar → root-cause structure, and
   cite the disclosed reports or research behind it in `sources:`.
3. Cross-link the neighbouring skills by name (the text is how the model learns
   which one owns which case).
4. Run the gates. Commit with a message naming the class and the change.

## Reporting a problem

Open an issue for a wrong claim, broken command, or missing pitfall — a skill
that sends a hunter down a false-positive path is a bug. Do not include target
data, credentials, or client names in an issue.

## License

By contributing you agree that code is licensed under the MIT license
(`LICENSE`) and skill/documentation content under `LICENSE-CONTENT`.
