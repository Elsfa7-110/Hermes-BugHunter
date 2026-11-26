"""Validate bundles/*.yaml without a YAML dependency.

Hermes loads bundles from `$HERMES_HOME/skill-bundles/`: `name`, `description`,
`skills: [...]`, optional `instruction`. A bundle that names a missing skill is
silently partially loaded, so the members are checked here.
"""
import os
import re
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUNDLES = os.path.join(REPO, "bundles")
SKILLS = os.path.join(REPO, "skills")

from typing import Any, Dict

ITEM_RE = re.compile(r"^\s+-\s+(?P<name>[a-z0-9-]+)\s*$")


def parse_bundle(path):
    """Minimal parse of the subset the repo uses: scalar keys + a skills list."""
    data: Dict[str, Any] = {"skills": []}
    with open(path, encoding="utf-8") as fh:
        in_skills = False
        for line in fh:
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            key = re.match(r"^(?P<key>[a-z_]+):\s*(?P<value>.*)$", line)
            if key and not line.startswith((" ", "\t")):
                in_skills = key.group("key") == "skills"
                if not in_skills:
                    data[key.group("key")] = key.group("value").strip().strip('"\'')
                continue
            if in_skills:
                item = ITEM_RE.match(line)
                if item:
                    data["skills"].append(item.group("name"))
    return data


class BundleTests(unittest.TestCase):
    def test_bundle_files_exist(self):
        found = [f for f in os.listdir(BUNDLES) if f.endswith((".yaml", ".yml"))]
        self.assertGreaterEqual(len(found), 4)

    def test_every_bundle_is_well_formed_and_names_real_skills(self):
        available = {d for d in os.listdir(SKILLS)
                     if os.path.isfile(os.path.join(SKILLS, d, "SKILL.md"))}
        for filename in sorted(os.listdir(BUNDLES)):
            if not filename.endswith((".yaml", ".yml")):
                continue
            data = parse_bundle(os.path.join(BUNDLES, filename))
            with self.subTest(bundle=filename):
                self.assertTrue(data.get("name"), f"{filename}: missing name")
                self.assertTrue(data.get("description"), f"{filename}: missing description")
                self.assertTrue(data["skills"], f"{filename}: no skills")
                missing = sorted(set(data["skills"]) - available)
                self.assertFalse(missing, f"{filename}: unknown skills {missing}")

    def test_bundle_names_are_unique(self):
        names = []
        for filename in sorted(os.listdir(BUNDLES)):
            if filename.endswith((".yaml", ".yml")):
                names.append(parse_bundle(os.path.join(BUNDLES, filename)).get("name"))
        self.assertEqual(len(names), len(set(names)))


class MarketplaceManifestTests(unittest.TestCase):
    """skills.sh.json drives the Marketplace/CLI grouping; a stale entry hides a skill."""

    def setUp(self):
        import json
        with open(os.path.join(REPO, "skills.sh.json"), encoding="utf-8") as fh:
            self.manifest = json.load(fh)
        self.available = {d for d in os.listdir(SKILLS)
                          if os.path.isfile(os.path.join(SKILLS, d, "SKILL.md"))}

    def test_schema_and_paths(self):
        self.assertTrue(self.manifest["$schema"].endswith("skills.sh.schema.json"))
        self.assertEqual(self.manifest["paths"], ["./skills"])

    def test_every_grouped_skill_exists(self):
        grouped = [name for group in self.manifest["groupings"] for name in group["skills"]]
        missing = sorted(set(grouped) - self.available)
        self.assertFalse(missing, f"skills.sh.json names missing skills: {missing}")

    def test_no_skill_is_grouped_twice(self):
        grouped = [name for group in self.manifest["groupings"] for name in group["skills"]]
        dupes = sorted({n for n in grouped if grouped.count(n) > 1})
        self.assertFalse(dupes, f"skills.sh.json groups these twice: {dupes}")

    def test_groupings_cover_the_bundle(self):
        grouped = {name for group in self.manifest["groupings"] for name in group["skills"]}
        self.assertEqual(grouped, self.available)


if __name__ == "__main__":
    unittest.main()
