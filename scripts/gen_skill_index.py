#!/usr/bin/env python3
"""
gen_skill_index.py — regenerate cbh/data/skill_index.json from the working tree.

A pip-installed copy has no skills/ directory, so `cbh classify` reads the bundled
index for skill descriptions and the disclosed-reports list. The index drifts as
soon as a SKILL.md description or a hunt-*.md report changes, so this script both
writes it and verifies it in CI:

    python3 scripts/gen_skill_index.py            # rewrite the bundled index
    python3 scripts/gen_skill_index.py --check    # exit 1 if it is stale

Parsing matches cbh/cli.py:load_skill_descriptions() exactly (same regex, same
2000-char cap) so generating and reading the index can never disagree. Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS_DIR = os.path.join(REPO, "skills")
REPORTS_DIR = os.path.join(REPO, "docs", "disclosed-reports")
OUT = os.path.join(REPO, "cbh", "data", "skill_index.json")

# Keep in lockstep with cbh/cli.py:load_skill_descriptions().
_DESC_RE = re.compile(r"^description:\s*(.+?)(?=\n[a-z_]+:|^---|\Z)", re.M | re.S)


def parse_description(path: str) -> str | None:
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return None
    m = _DESC_RE.search(text)
    if not m:
        return None
    return m.group(1).strip().strip('"').strip("'").strip()[:2000]


def build_index() -> dict:
    skills: dict[str, str] = {}
    if os.path.isdir(SKILLS_DIR):
        for name in sorted(os.listdir(SKILLS_DIR)):
            skill_md = os.path.join(SKILLS_DIR, name, "SKILL.md")
            if not os.path.isfile(skill_md):
                continue
            desc = parse_description(skill_md)
            if desc:
                skills[name] = desc
    reports = sorted(
        p for p in os.listdir(REPORTS_DIR)
        if p.startswith("hunt-") and p.endswith(".md")
    ) if os.path.isdir(REPORTS_DIR) else []
    return {"reports": reports, "skills": skills}


def dump(index: dict) -> str:
    return json.dumps(index, indent=1, sort_keys=True) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="gen_skill_index.py",
        description="Generate or verify cbh/data/skill_index.json.")
    ap.add_argument("--check", action="store_true",
                    help="do not write; exit 1 if the bundled index is stale")
    args = ap.parse_args(argv)

    if not os.path.isdir(SKILLS_DIR):
        print(f"[error] no skills/ directory at {SKILLS_DIR}", file=sys.stderr)
        return 1

    want = build_index()
    if not want["skills"]:
        print("[error] parsed zero skill descriptions — refusing to write an empty index",
              file=sys.stderr)
        return 1
    rendered = dump(want)

    if not args.check:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        with open(OUT, "w", encoding="utf-8") as fh:
            fh.write(rendered)
        print(f"Wrote {OUT} — {len(want['skills'])} skill(s), {len(want['reports'])} report(s).")
        return 0

    try:
        with open(OUT, encoding="utf-8") as fh:
            current = json.load(fh)
    except (OSError, json.JSONDecodeError) as err:
        print(f"[error] cannot read {OUT}: {err}", file=sys.stderr)
        return 1
    if current == want:
        print(f"skill index OK — {len(want['skills'])} skill(s), {len(want['reports'])} report(s).")
        return 0

    problems = []
    old_skills = current.get("skills", {})
    old_reports = current.get("reports", [])
    for name in sorted(set(want["skills"]) - set(old_skills)):
        problems.append(f"missing from index: {name}")
    for name in sorted(set(old_skills) - set(want["skills"])):
        problems.append(f"index lists a skill that is not on disk: {name}")
    for name in sorted(set(want["skills"]) & set(old_skills)):
        if want["skills"][name] != old_skills[name]:
            problems.append(f"description changed: {name}")
    for name in sorted(set(want["reports"]) - set(old_reports)):
        problems.append(f"missing report entry: {name}")
    for name in sorted(set(old_reports) - set(want["reports"])):
        problems.append(f"stale report entry: {name}")
    print("skill index is STALE — run: python3 scripts/gen_skill_index.py",
          file=sys.stderr)
    for line in problems:
        print(f"  - {line}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
