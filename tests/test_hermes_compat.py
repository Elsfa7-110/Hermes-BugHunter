"""Tests for the Hermes compatibility gate (scripts/hermes_compat.py).

These cover the rules that decide whether Hermes can index a skill, expose it
as a slash command, and load it by bare name — the failure modes a `cp -a` of
the bundle into a shared profile actually produces.
"""
import importlib.util
import os
import tempfile
import textwrap
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def _load(name):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    assert spec is not None and spec.loader is not None, f"cannot load scripts/{name}.py"
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


compat = _load("hermes_compat")


def write_skill(root: Path, rel: str, name: str = "", description: str = "Hunt things.",
                body: str = "Body.\n") -> Path:
    skill_dir = root / rel
    skill_dir.mkdir(parents=True, exist_ok=True)
    fm = f"---\nname: {name or Path(rel).name}\ndescription: {description}\n---\n\n"
    (skill_dir / "SKILL.md").write_text(fm + body, encoding="utf-8")
    return skill_dir


class FrontmatterTests(unittest.TestCase):
    def test_parses_quoted_and_block_scalars(self):
        raw = "---\nname: demo\ndescription: \"A: colon works\"\n---\nbody\n"
        fm, body, err = compat.split_frontmatter(raw)
        self.assertIsNone(err)
        self.assertEqual(fm["name"], "demo")
        self.assertIn("body", body)

    def test_bom_is_tolerated(self):
        raw = "\ufeff---\nname: demo\ndescription: x\n---\n"
        fm, _body, err = compat.split_frontmatter(raw)
        self.assertIsNone(err)
        self.assertEqual(fm["name"], "demo")

    def test_missing_fence_is_an_error(self):
        _fm, _body, err = compat.split_frontmatter("# no frontmatter\n")
        self.assertIn("frontmatter", err)

    def test_unclosed_fence_is_an_error(self):
        _fm, _body, err = compat.split_frontmatter("---\nname: demo\n")
        self.assertIn("never closed", err)

    def test_quoted_scalars_are_unquoted_without_pyyaml(self):
        """The fallback parser must not leave YAML quotes on the value."""
        raw = '---\nname: demo\ndescription: "A \\"quoted\\" value: with colon"\n---\n'
        fm, _body, err = compat.split_frontmatter(raw)
        self.assertIsNone(err)
        self.assertEqual(fm["description"], 'A "quoted" value: with colon')


class StructureTests(unittest.TestCase):
    def test_duplicate_names_are_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_skill(root, "one/recon", name="recon")
            write_skill(root, "two/recon-copy", name="recon")
            errors, _warnings = compat.check_structure(root)
            self.assertTrue(any("duplicate skill name" in e for e in errors), errors)

    def test_nested_skill_in_support_dir_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = write_skill(root, "demo")
            nested = skill / "references" / "inner"
            nested.mkdir(parents=True)
            (nested / "SKILL.md").write_text("---\nname: inner\ndescription: x\n---\n")
            errors, _warnings = compat.check_structure(root)
            self.assertTrue(any("support dir" in e for e in errors), errors)

    def test_unique_tree_has_no_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_skill(root, "alpha")
            write_skill(root, "beta")
            errors, _warnings = compat.check_structure(root)
            self.assertEqual(errors, [])


class ResolveTests(unittest.TestCase):
    def test_single_owner_is_unique(self):
        rows = compat.resolve_catalog([
            {"name": "hunt-xss", "dir_name": "hunt-xss", "rel": "hunt-xss", "path": "x"},
        ])
        self.assertEqual(rows[0]["status"], "unique")
        self.assertEqual(rows[0]["load_name"], "hunt-xss")

    def test_same_name_different_paths_loads_by_path(self):
        rows = compat.resolve_catalog([
            {"name": "hunt-xss", "dir_name": "hunt-xss", "rel": "a/hunt-xss", "path": "a"},
            {"name": "hunt-xss", "dir_name": "hunt-xss", "rel": "b/hunt-xss", "path": "b"},
        ])
        self.assertEqual([r["status"] for r in rows], ["ambiguous", "ambiguous"])
        self.assertEqual([r["load_name"] for r in rows], ["a/hunt-xss", "b/hunt-xss"])

    def test_shared_name_and_path_is_unloadable(self):
        # Two roots mounted at the same relative path: Hermes cannot tell them apart.
        rows = compat.resolve_catalog([
            {"name": "hunt-xss", "dir_name": "hunt-xss", "rel": "skills/hunt-xss", "path": "one"},
            {"name": "hunt-xss", "dir_name": "hunt-xss", "rel": "skills/hunt-xss", "path": "two"},
        ])
        self.assertEqual([r["status"] for r in rows], ["unloadable", "unloadable"])
        self.assertTrue(all(r["load_name"] is None for r in rows))


class SkillCheckTests(unittest.TestCase):
    def _entry(self, **kwargs):
        write = kwargs.pop("description", "Hunt things.")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = write_skill(root, "demo", description=write, **kwargs)
            entry = compat.scan_tree(root)[0]
        return entry

    def test_good_skill_has_no_findings(self):
        errors, warnings = compat.check_skill(self._entry())
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_missing_description_is_an_error(self):
        errors, _ = compat.check_skill(self._entry(description=""))
        self.assertTrue(any("description" in e for e in errors), errors)

    def test_name_must_match_directory(self):
        _errors, warnings = compat.check_skill(self._entry(name="renamed"))
        self.assertTrue(any("!= directory" in w for w in warnings), warnings)

    def test_over_index_width_warns(self):
        long_desc = "Hunt xss " + "and reflect payloads into markup " * 3
        _errors, warnings = compat.check_skill(self._entry(description=long_desc),
                                               index_limit=60)
        self.assertTrue(any("index line" in w for w in warnings), warnings)

    def test_broken_relative_link_warns(self):
        errors, warnings = compat.check_skill(
            self._entry(body="See [docs](references/missing.md).\n"))
        self.assertEqual(errors, [])
        self.assertTrue(any("broken relative link" in w for w in warnings), warnings)

    def test_payload_lookalikes_are_not_links(self):
        body = "Payload: [x](javascript:alert(1)) and `[y](nope.md)`.\n"
        _errors, warnings = compat.check_skill(self._entry(body=body))
        self.assertFalse(any("broken relative link" in w for w in warnings), warnings)


class RepoBundleTests(unittest.TestCase):
    """The shipped bundle must pass its own gate."""

    def test_repo_tree_resolves_without_errors(self):
        errors, _warnings = compat.check_structure(REPO / "skills")
        self.assertEqual(errors, [])

    def test_every_skill_is_loadable(self):
        rows = compat.resolve_catalog(compat.scan_tree(REPO / "skills"))
        self.assertEqual(len(rows), 98)
        self.assertFalse([r["rel"] for r in rows if r["status"] == "unloadable"])

    def test_every_description_survives_the_index_clip(self):
        for entry in compat.scan_tree(REPO / "skills"):
            _errors, warnings = compat.check_skill(entry, index_limit=60)
            self.assertFalse(
                [w for w in warnings if "index line" in w],
                f"{entry['rel']}: description clipped mid-clause at 60 chars")


if __name__ == "__main__":
    unittest.main()
