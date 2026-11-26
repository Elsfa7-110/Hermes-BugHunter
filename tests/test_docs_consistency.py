"""Regression tests for the doc/index consistency gates.

These cover the two scripts the CI workflows invoke (`check_doc_counts.py` and
`gen_skill_index.py`) plus the mirrored `recon` skill, whose missing directory
made the catalog claim a skill that could not be loaded.
"""
import importlib.util
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(name):
    path = os.path.join(REPO, "scripts", name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None, f"cannot load {path}"
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_doc_counts_gate_passes():
    mod = _load("check_doc_counts")
    assert mod.main() == 0, mod.failures


def test_skill_index_is_in_sync():
    mod = _load("gen_skill_index")
    assert mod.main(["--check"]) == 0


def test_skill_index_covers_every_skill_directory():
    mod = _load("gen_skill_index")
    index = mod.build_index()
    disk = {
        d for d in os.listdir(os.path.join(REPO, "skills"))
        if os.path.isfile(os.path.join(REPO, "skills", d, "SKILL.md"))
    }
    assert set(index["skills"]) == disk
    bundled = json.load(open(os.path.join(REPO, "cbh", "data", "skill_index.json"),
                             encoding="utf-8"))
    assert bundled["skills"] == index["skills"]
    assert bundled["reports"] == index["reports"]


def test_every_command_has_a_mirrored_skill():
    commands = {
        f[:-3] for f in os.listdir(os.path.join(REPO, "commands"))
        if f.endswith(".md")
    }
    skills = {
        d for d in os.listdir(os.path.join(REPO, "skills"))
        if os.path.isfile(os.path.join(REPO, "skills", d, "SKILL.md"))
    }
    assert commands <= skills, f"commands without a skill directory: {sorted(commands - skills)}"


def test_recon_skill_frontmatter():
    path = os.path.join(REPO, "skills", "recon", "SKILL.md")
    text = open(path, encoding="utf-8").read()
    assert text.startswith("---\n")
    head = text.split("---", 2)[1]
    assert "name: recon" in head
    assert "description:" in head
    assert "commands/recon.md" in head


def test_no_skill_directory_is_gitignored():
    """An unanchored `recon/` ignore rule silently dropped skills/recon/."""
    import shutil
    import subprocess

    if shutil.which("git") is None:
        return
    skills = sorted(
        os.path.join("skills", d) for d in os.listdir(os.path.join(REPO, "skills"))
        if os.path.isfile(os.path.join(REPO, "skills", d, "SKILL.md"))
    )
    proc = subprocess.run(["git", "-C", REPO, "check-ignore"] + skills,
                          capture_output=True, text=True)
    if proc.returncode not in (0, 1):      # 1 = nothing ignored; 128 = not a repo
        return
    ignored = [ln for ln in proc.stdout.splitlines() if ln.strip()]
    assert not ignored, f"skill directories excluded by .gitignore: {ignored}"
