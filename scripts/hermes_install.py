#!/usr/bin/env python3
"""
hermes_install.py — install this bundle into a Hermes skills directory safely.

Why a dedicated installer instead of `cp -a skills/. ~/.hermes/skills/`:

  * Hermes resolves skills by name inside ONE tier. Copying 98 generic names
    (hunt-xss, recon, triage …) straight into a profile that already has another
    bug-bounty bundle makes both copies AMBIGUOUS: skill_view refuses the bare
    name and no `/command` is registered. This installer detects that before it
    copies anything and tells you the exact load name you will get.
  * Hermes reads `$HERMES_HOME/skills` (profiles included), not a hard-coded
    `~/.hermes/skills`. The destination resolves the same way Hermes does.
  * Progressive disclosure means a skill is only useful if the model can load
    it. The post-install verification walks the destination with Hermes' own
    alias rules and fails loudly if any installed skill cannot be opened.

Layout: skills land in `<dest>/hermes-bughunter/<skill>/` by default, so the
tree is identifiable, upgradeable, and removable in one step. `--flat` copies
them directly into `<dest>` (only sensible in a profile with no other
bug-bounty bundle).

Usage:
    python3 scripts/hermes_install.py                 # install
    python3 scripts/hermes_install.py --dry-run
    python3 scripts/hermes_install.py --profile bbh   # profiles/bbh/skills
    python3 scripts/hermes_install.py --force         # replace changed copies
    python3 scripts/hermes_install.py --uninstall
    python3 scripts/hermes_install.py --json
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

REPO = Path(__file__).resolve().parent.parent
SOURCE = REPO / "skills"
DEFAULT_NAMESPACE = "hermes-bughunter"
MANIFEST_NAME = ".hermes-install.json"


def _load_compat():
    """Load the sibling validator by path.

    Importing it through ``sys.path`` would leak ``scripts/`` onto the path of
    every process that imports this module (unittest discovery then resolves
    other top-level names to scripts/ instead of tests/).
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "hermes_compat", Path(__file__).with_name("hermes_compat.py"))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_compat = _load_compat()
resolve_catalog = _compat.resolve_catalog
scan_tree = _compat.scan_tree


def hermes_home() -> Path:
    """$HERMES_HOME when set (profiles), else ~/.hermes — Hermes' own rule."""
    env = os.environ.get("HERMES_HOME")
    return Path(env).expanduser() if env else Path.home() / ".hermes"


def resolve_dest(args) -> Path:
    if args.dest:
        return Path(args.dest).expanduser().resolve()
    home = hermes_home()
    if args.profile:
        return (home / "profiles" / args.profile / "skills").resolve()
    return (home / "skills").resolve()


def source_skills() -> List[Path]:
    return sorted(p for p in SOURCE.iterdir()
                  if p.is_dir() and (p / "SKILL.md").is_file())


def other_name_owners(dest: Path, targets: List[Path]) -> Dict[str, List[str]]:
    """Declared/dir names already present in *dest* outside our target dirs."""
    target_set = {t.resolve() for t in targets}
    source_root = SOURCE.resolve()
    owners: Dict[str, List[str]] = {}
    if not dest.is_dir():
        return owners
    for entry in scan_tree(dest):
        path = entry["path"].resolve()
        if entry["dir"].resolve() in target_set or path.is_relative_to(source_root):
            continue  # our own copy, or the checkout these skills are copied FROM
        for alias in {entry["name"], entry["dir_name"]}:
            owners.setdefault(alias, []).append(str(entry["path"]))
    return owners


def plan(args) -> Tuple[Path, List[Tuple[Path, Path]]]:
    dest = resolve_dest(args)
    namespace = "" if args.flat else args.namespace
    base = dest / namespace if namespace else dest
    pairs = [(skill, base / skill.name) for skill in source_skills()]
    return dest, pairs


def preflight(dest: Path, pairs: List[Tuple[Path, Path]], namespace: str) -> dict:
    """Report name collisions and unsafe overwrites before touching disk."""
    targets = [target for _src, target in pairs]
    owners = other_name_owners(dest, targets)
    conflicts = {
        src.name: owners[src.name]
        for src, _target in pairs if owners.get(src.name)
    }
    overwrites = []
    for src, target in pairs:
        if not (target.exists() or target.is_symlink()):
            continue
        existing = target / "SKILL.md"
        if existing.is_file():
            try:
                same = existing.read_text(encoding="utf-8") == (src / "SKILL.md").read_text(encoding="utf-8")
            except OSError:
                same = False
            overwrites.append({"skill": src.name, "same_content": same})
        else:
            overwrites.append({"skill": src.name, "same_content": False, "not_a_skill": True})
    return {"conflicts": conflicts, "overwrites": overwrites, "namespace": namespace}


def copy_skills(pairs: List[Tuple[Path, Path]], force: bool, dry_run: bool) -> List[dict]:
    results = []
    for src, target in pairs:
        action = "copy"
        if target.exists():
            if not force:
                same = (target / "SKILL.md").is_file() and (
                    target / "SKILL.md").read_text(encoding="utf-8") == (src / "SKILL.md").read_text(encoding="utf-8")
                if same:
                    results.append({"skill": src.name, "action": "unchanged"})
                    continue
                results.append({"skill": src.name, "action": "skipped-existing",
                                "hint": "re-run with --force to replace"})
                continue
            action = "replace"
        if not dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(src, target)
        results.append({"skill": src.name, "action": action})
    return results


def write_manifest(dest: Path, namespace: str, pairs: List[Tuple[Path, Path]],
                   dry_run: bool) -> Optional[Path]:
    if not namespace:
        return None  # flat installs are not owned trees; never claim them
    manifest = dest / namespace / MANIFEST_NAME
    payload = {
        "bundle": "Hermes-BugHunter",
        "version": read_version(),
        "installed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "namespace": namespace,
        "skills": [src.name for src, _t in pairs],
    }
    if not dry_run:
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return manifest


def read_version() -> str:
    try:
        for line in (REPO / "pyproject.toml").read_text(encoding="utf-8").splitlines():
            if line.startswith("version"):
                return line.split("=", 1)[1].strip().strip('"')
    except OSError:
        pass
    return "unknown"


def verify(dest: Path, installed: List[str], namespace: str = "") -> dict:
    """Resolve every skill in *dest* the way Hermes does; report ours.

    *namespace* scopes the report to the tree this installer owns, so a
    colliding skill from another bundle is not counted as one of ours.
    """
    entries = scan_tree(dest) if dest.is_dir() else []
    rows = resolve_catalog(entries)
    prefix = f"{namespace}/" if namespace else ""
    mine = [r for r in rows
            if (r["rel"].startswith(prefix) if prefix else r["dir_name"] in installed)]
    if prefix:
        mine = [r for r in mine if r["dir_name"] in installed]
    unique = [r for r in mine if r["status"] == "unique"]
    ambiguous = [r for r in mine if r["status"] == "ambiguous"]
    unloadable = [r for r in mine if r["status"] == "unloadable"]
    return {
        "total": len(mine),
        "unique": [{"name": r["name"], "command": "/" + r["name"], "path": r["rel"]} for r in unique],
        "ambiguous": [{"name": r["name"], "load_name": r["load_name"], "path": r["rel"]} for r in ambiguous],
        "unloadable": [{"name": r["name"], "path": r["rel"]} for r in unloadable],
    }


def bundle_home(args) -> Path:
    home = hermes_home()
    if args.profile:
        return home / "profiles" / args.profile / "skill-bundles"
    return home / "skill-bundles"


def install_bundles(args, dry_run: bool) -> List[str]:
    """Copy bundles/*.yaml into the profile's skill-bundles directory."""
    source = REPO / "bundles"
    if not source.is_dir():
        return []
    dest = bundle_home(args)
    names = []
    for path in sorted(source.glob("*.y*ml")):
        names.append(path.stem)
        if not dry_run:
            dest.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest / path.name)
    return names


def uninstall(dest: Path, namespace: str) -> int:
    tree = dest / namespace
    manifest = tree / MANIFEST_NAME
    if not manifest.is_file():
        print(f"refusing to remove {tree}: no {MANIFEST_NAME} (not installed by this script)")
        return 1
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    for name in payload.get("skills", []):
        if "/" in name or name in ("", ".", ".."):
            print(f"refusing to remove {tree}: manifest contains unsafe name {name!r}")
            return 1
    shutil.rmtree(tree)
    print(f"removed {tree} ({len(payload.get('skills', []))} skills)")
    return 0


def print_report(dest: Path, namespace: str, pre: dict, copied: List[dict],
                 result: Optional[dict], dry_run: bool) -> int:
    verb = "would install" if dry_run else "installed"
    changed = [c for c in copied if c["action"] in ("copy", "replace")]
    unchanged = [c for c in copied if c["action"] == "unchanged"]
    skipped = [c for c in copied if c["action"] == "skipped-existing"]

    print(f"source     : {SOURCE}")
    print(f"destination: {dest / namespace if namespace else dest}")
    print(f"{verb}  : {len(changed)} skill(s); unchanged {len(unchanged)}; skipped {len(skipped)}")

    if skipped:
        print("\nskipped (destination differs; --force replaces):")
        for row in skipped[:10]:
            print(f"  - {row['skill']}")
        if len(skipped) > 10:
            print(f"  … and {len(skipped) - 10} more")

    conflicts = pre.get("conflicts") or {}
    if conflicts:
        print(f"\nNAME COLLISIONS with skills already in this profile: {len(conflicts)}")
        for name in sorted(conflicts)[:15]:
            print(f"  - {name}: also at {conflicts[name][0]}")
        if len(conflicts) > 15:
            print(f"  … and {len(conflicts) - 15} more")
        print("  Hermes keeps only unique names as /commands. These skills load by path:")
        if namespace:
            example = f"{namespace}/{sorted(conflicts)[0]}"
            print(f'    skill_view("{example}")')
        else:
            print("    (flat install: the bare names are shared, so rename or use --namespace)")
        print("  To get short /commands back, install into a profile that has only this bundle:")
        print("    hermes profile create bughunter")
        print(f"    python3 {Path(__file__).resolve()} --profile bughunter")
        print("    hermes profile use bughunter      # or: HERMES_HOME=~/.hermes/profiles/bughunter hermes")

    if result is None:
        return 0
    print(f"\nverification: {result['total']} skill(s) in the destination tree")
    print(f"  unique names (get a /command) : {len(result['unique'])}")
    print(f"  path-loadable (name shared)   : {len(result['ambiguous'])}")
    print(f"  unloadable                    : {len(result['unloadable'])}")
    if result["unloadable"]:
        for row in result["unloadable"][:10]:
            print(f"  ERROR cannot load {row['path']}")
        return 1
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Install the Hermes-BugHunter skills into a Hermes profile.")
    parser.add_argument("--dest", help="skills directory (default: $HERMES_HOME/skills)")
    parser.add_argument("--profile", help="install into $HERMES_HOME/profiles/<name>/skills")
    parser.add_argument("--namespace", default=DEFAULT_NAMESPACE,
                        help=f"subdirectory under the skills dir (default: {DEFAULT_NAMESPACE})")
    parser.add_argument("--flat", action="store_true",
                        help="copy skill dirs directly into the skills dir (clean profiles only)")
    parser.add_argument("--force", action="store_true", help="replace existing skill dirs")
    parser.add_argument("--bundles", action="store_true",
                        help="also copy bundles/*.yaml into $HERMES_HOME/skill-bundles")
    parser.add_argument("--dry-run", action="store_true", help="show the plan, change nothing")
    parser.add_argument("--no-verify", action="store_true", help="skip post-install resolution check")
    parser.add_argument("--uninstall", action="store_true", help="remove the namespaced tree")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args(argv)

    if not SOURCE.is_dir():
        print(f"source skills directory not found: {SOURCE}", file=sys.stderr)
        return 2

    dest, pairs = plan(args)
    namespace = "" if args.flat else args.namespace

    if args.uninstall:
        if not namespace:
            print("--uninstall needs a namespaced layout (drop --flat)", file=sys.stderr)
            return 2
        return uninstall(dest, namespace)

    pre = preflight(dest, pairs, namespace)
    copied = copy_skills(pairs, force=args.force, dry_run=args.dry_run)
    write_manifest(dest, namespace, pairs, args.dry_run)
    bundles = install_bundles(args, args.dry_run) if args.bundles else []
    result = None
    if not args.dry_run and not args.no_verify:
        result = verify(dest, [src.name for src, _t in pairs], namespace)

    if args.json:
        print(json.dumps({"destination": str(dest / namespace if namespace else dest),
                          "preflight": pre,
                          "bundles": bundles,
                          "copied": [{k: v for k, v in row.items()} for row in copied],
                          "verification": result}, indent=2))
    else:
        rc = print_report(dest, namespace, pre, copied, result, args.dry_run)
        if rc:
            return rc
        if bundles:
            print(f"\nbundles    : {len(bundles)} copied to {bundle_home(args)}")
            print("  " + ", ".join("/" + name for name in bundles))
    if result and result["unloadable"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
