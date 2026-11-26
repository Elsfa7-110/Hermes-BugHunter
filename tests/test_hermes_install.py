"""Tests for scripts/hermes_install.py — the Hermes-facing install path.

Everything runs against a temporary destination; nothing here touches the
real profile, and the bundle source is read-only.
"""
import contextlib
import importlib.util
import io
import json
import os
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def _load(name):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    assert spec is not None and spec.loader is not None, f"cannot load scripts/{name}.py"
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


installer = _load("hermes_install")


def run(*args):
    """Run the installer, returning (exit_code, stdout)."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = installer.main(list(args))
    return rc, buf.getvalue()


def fake_other_bundle(dest: Path, name: str) -> Path:
    skill = dest / "other-bundle" / name
    skill.mkdir(parents=True, exist_ok=True)
    (skill / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: another bundle's copy\n---\n\nbody\n",
        encoding="utf-8")
    return skill


class InstallTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dest = Path(self._tmp.name) / "skills"
        self.dest.mkdir(parents=True)

    def tearDown(self):
        self._tmp.cleanup()

    def test_clean_install_gives_every_skill_a_command(self):
        rc, out = run("--dest", str(self.dest), "--json")
        self.assertEqual(rc, 0)
        report = json.loads(out)
        self.assertEqual(report["verification"]["total"], 98)
        self.assertEqual(len(report["verification"]["unique"]), 98)
        self.assertEqual(report["verification"]["unloadable"], [])
        self.assertTrue((self.dest / "hermes-bughunter" / "hunt-xss" / "SKILL.md").is_file())
        self.assertTrue((self.dest / "hermes-bughunter" / ".hermes-install.json").is_file())

    def test_install_is_idempotent(self):
        run("--dest", str(self.dest))
        rc, out = run("--dest", str(self.dest), "--json")
        self.assertEqual(rc, 0)
        actions = {row["action"] for row in json.loads(out)["copied"]}
        self.assertEqual(actions, {"unchanged"})

    def test_collision_is_reported_and_stays_loadable_by_path(self):
        fake_other_bundle(self.dest, "hunt-xss")
        rc, out = run("--dest", str(self.dest), "--json")
        self.assertEqual(rc, 0)
        report = json.loads(out)
        self.assertIn("hunt-xss", report["preflight"]["conflicts"])
        ambiguous = {row["name"]: row["load_name"] for row in report["verification"]["ambiguous"]}
        self.assertEqual(ambiguous["hunt-xss"], "hermes-bughunter/hunt-xss")
        # our copy is still 98 entries; the other bundle's copy is not counted as ours
        self.assertEqual(report["verification"]["total"], 98)

    def test_dry_run_changes_nothing(self):
        rc, _out = run("--dest", str(self.dest), "--dry-run")
        self.assertEqual(rc, 0)
        self.assertEqual(list(self.dest.iterdir()), [])

    def test_changed_copy_is_skipped_without_force(self):
        run("--dest", str(self.dest))
        target = self.dest / "hermes-bughunter" / "hunt-xss" / "SKILL.md"
        target.write_text("---\nname: hunt-xss\ndescription: local edit\n---\n", encoding="utf-8")
        rc, out = run("--dest", str(self.dest), "--json")
        self.assertEqual(rc, 0)
        actions = {row["skill"]: row["action"] for row in json.loads(out)["copied"]}
        self.assertEqual(actions["hunt-xss"], "skipped-existing")
        self.assertIn("local edit", target.read_text(encoding="utf-8"))

    def test_force_replaces_changed_copy(self):
        run("--dest", str(self.dest))
        target = self.dest / "hermes-bughunter" / "hunt-xss" / "SKILL.md"
        target.write_text("---\nname: hunt-xss\ndescription: local edit\n---\n", encoding="utf-8")
        run("--dest", str(self.dest), "--force")
        self.assertNotIn("local edit", target.read_text(encoding="utf-8"))

    def test_flat_layout_installs_into_the_root(self):
        rc, _out = run("--dest", str(self.dest), "--flat")
        self.assertEqual(rc, 0)
        self.assertTrue((self.dest / "hunt-xss" / "SKILL.md").is_file())
        self.assertFalse((self.dest / "hermes-bughunter").exists())

    def test_uninstall_removes_only_the_namespaced_tree(self):
        fake_other_bundle(self.dest, "hunt-xss")
        run("--dest", str(self.dest))
        rc, _out = run("--dest", str(self.dest), "--uninstall")
        self.assertEqual(rc, 0)
        self.assertFalse((self.dest / "hermes-bughunter").exists())
        self.assertTrue((self.dest / "other-bundle" / "hunt-xss" / "SKILL.md").is_file())

    def test_uninstall_refuses_a_tree_it_did_not_install(self):
        tree = self.dest / "hermes-bughunter"
        tree.mkdir()
        rc, out = run("--dest", str(self.dest), "--uninstall")
        self.assertEqual(rc, 1)
        self.assertIn("refusing", out)
        self.assertTrue(tree.exists())

    def test_bundles_flag_copies_into_hermes_home(self):
        home = Path(self._tmp.name) / "hermes-home"
        old = os.environ.get("HERMES_HOME")
        os.environ["HERMES_HOME"] = str(home)
        try:
            rc, out = run("--dest", str(self.dest), "--bundles", "--json")
        finally:
            if old is None:
                os.environ.pop("HERMES_HOME", None)
            else:
                os.environ["HERMES_HOME"] = old
        self.assertEqual(rc, 0)
        names = json.loads(out)["bundles"]
        self.assertGreaterEqual(len(names), 4)
        for name in names:
            self.assertTrue((home / "skill-bundles" / f"{name}.yaml").is_file(), name)

    def test_profile_flag_targets_a_profile_skills_dir(self):
        home = Path(self._tmp.name) / "hermes-home"
        old = os.environ.get("HERMES_HOME")
        os.environ["HERMES_HOME"] = str(home)
        try:
            args = type("A", (), {"dest": None, "profile": "bbh"})()
            self.assertEqual(installer.resolve_dest(args),
                             (home / "profiles" / "bbh" / "skills").resolve())
            rc, out = run("--profile", "bbh", "--dry-run", "--json")
        finally:
            if old is None:
                os.environ.pop("HERMES_HOME", None)
            else:
                os.environ["HERMES_HOME"] = old
        self.assertEqual(rc, 0)
        self.assertIn("profiles/bbh/skills", json.loads(out)["destination"])


if __name__ == "__main__":
    unittest.main()
