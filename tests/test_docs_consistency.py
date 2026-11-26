"""Regression tests for the doc/index consistency gates.

These cover the two scripts the CI workflows invoke (`check_doc_counts.py` and
`gen_skill_index.py`) plus the mirrored `recon` skill, whose missing directory
made the catalog claim a skill that could not be loaded.

Written as unittest.TestCase so runtime-tests.yml's
`python -m unittest discover -s tests` picks them up (pytest runs them too).
"""
import importlib.util
import json
import os
import shutil
import subprocess
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(name):
    path = os.path.join(REPO, "scripts", name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None, f"cannot load {path}"
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _skill_dirs():
    base = os.path.join(REPO, "skills")
    return sorted(d for d in os.listdir(base)
                  if os.path.isfile(os.path.join(base, d, "SKILL.md")))


class DocsConsistencyTests(unittest.TestCase):
    def test_doc_counts_gate_passes(self):
        mod = _load("check_doc_counts")
        self.assertEqual(mod.main(), 0, mod.failures)

    def test_skill_index_is_in_sync(self):
        mod = _load("gen_skill_index")
        self.assertEqual(mod.main(["--check"]), 0)

    def test_skill_index_covers_every_skill_directory(self):
        index = _load("gen_skill_index").build_index()
        self.assertEqual(set(index["skills"]), set(_skill_dirs()))
        with open(os.path.join(REPO, "cbh", "data", "skill_index.json"),
                  encoding="utf-8") as fh:
            bundled = json.load(fh)
        self.assertEqual(bundled["skills"], index["skills"])
        self.assertEqual(bundled["reports"], index["reports"])

    def test_every_command_has_a_mirrored_skill(self):
        commands = {f[:-3] for f in os.listdir(os.path.join(REPO, "commands"))
                    if f.endswith(".md")}
        missing = commands - set(_skill_dirs())
        self.assertFalse(missing, f"commands without a skill directory: {sorted(missing)}")

    def test_recon_skill_frontmatter(self):
        with open(os.path.join(REPO, "skills", "recon", "SKILL.md"),
                  encoding="utf-8") as fh:
            text = fh.read()
        self.assertTrue(text.startswith("---\n"))
        head = text.split("---", 2)[1]
        self.assertIn("name: recon", head)
        self.assertIn("description:", head)
        self.assertIn("commands/recon.md", head)

    def test_no_skill_directory_is_gitignored(self):
        """An unanchored `recon/` ignore rule silently dropped skills/recon/."""
        if shutil.which("git") is None:
            self.skipTest("git not installed")
        skills = [os.path.join("skills", d) for d in _skill_dirs()]
        proc = subprocess.run(["git", "-C", REPO, "check-ignore"] + skills,
                              capture_output=True, text=True)
        if proc.returncode not in (0, 1):      # 1 = nothing ignored; 128 = not a repo
            self.skipTest(f"git check-ignore unavailable (rc={proc.returncode})")
        ignored = [ln for ln in proc.stdout.splitlines() if ln.strip()]
        self.assertFalse(ignored, f"skill directories excluded by .gitignore: {ignored}")


if __name__ == "__main__":
    unittest.main()
