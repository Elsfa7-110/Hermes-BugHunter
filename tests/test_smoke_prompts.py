"""Keep tests/smoke-test-prompts.md honest.

The file is the manual routing check for a fresh install: every row names the
skill a prompt should load first. If a skill is renamed or removed, this test
fails before a user discovers it by pasting the prompt into Hermes.
"""
import os
import re
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROMPTS = os.path.join(REPO, "tests", "smoke-test-prompts.md")
SKILLS_DIR = os.path.join(REPO, "skills")

ROW_RE = re.compile(r"^\|\s*`?(?P<prompt>[^|`]+?)`?\s*\|\s*`(?P<skill>[a-z0-9-]+)`\s*\|\s*$")


def rows():
    with open(PROMPTS, encoding="utf-8") as fh:
        for line in fh:
            match = ROW_RE.match(line.strip())
            if match:
                yield match.group("prompt").strip(), match.group("skill")


class SmokePromptTests(unittest.TestCase):
    def test_every_named_skill_exists(self):
        available = {d for d in os.listdir(SKILLS_DIR)
                     if os.path.isfile(os.path.join(SKILLS_DIR, d, "SKILL.md"))}
        missing = sorted({skill for _prompt, skill in rows()} - available)
        self.assertFalse(missing, f"smoke prompts name skills that do not exist: {missing}")

    def test_covers_the_workflow_skills(self):
        named = {skill for _prompt, skill in rows()}
        for required in ("hunt", "scope", "triage", "report", "recon"):
            self.assertIn(required, named)

    def test_has_enough_coverage(self):
        self.assertGreaterEqual(len(list(rows())), 40)


if __name__ == "__main__":
    unittest.main()
