# Contributing

Contributions should improve the accuracy, clarity, safety, and maintainability of the Hermes Agent skill bundle and its optional tooling.

## Useful contributions

- focused vulnerability-class or framework skills;
- improvements to scope handling, recon accuracy, evidence hygiene, and report quality;
- current, source-backed CVE or platform references;
- tests that reproduce a regression or validate an existing behavior;
- improvements to the Hermes engine adapter, `cbh`, or skill-copy scripts;
- documentation corrections and examples that use controlled or explicitly authorized targets.

## Skill quality standards

Each new skill should include a `SKILL.md` with valid YAML frontmatter containing:

- `name`: lowercase letters, digits, and hyphens;
- `description`: a concise statement of purpose and the situations that should trigger the skill.

Keep the skill focused. Put lengthy reference material, templates, and helper scripts in subdirectories such as `references/`, `templates/`, and `scripts/`. Cross-reference related skills where useful. Avoid unsupported claims, unverified exploitability statements, and copied target-specific data.

## Testing changes

Run the following checks when relevant:

```bash
python3 scripts/lint_skills.py
python3 scripts/gen_skill_index.py
python3 scripts/check_doc_counts.py
python3 -m unittest discover -s engine -p 'test_*.py'
python3 eval/test_harness.py
```

For shell changes, also run `bash -n` on the modified scripts. For the Hermes adapter, use mocked CLI output in automated tests; a real target assessment is not a substitute for unit tests.

## Data hygiene

Do not commit real client identifiers, credentials, access tokens, personal data, private program information, or unredacted engagement evidence. Use synthetic hostnames and test data in examples. Never include private scope documents or customer records.

## Licensing

Preserve existing copyright and license notices. Contributions must be compatible with the repository's MIT code license and CC BY 4.0 content license as applicable. Cite and attribute third-party material where the relevant license requires it.
