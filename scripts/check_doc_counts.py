#!/usr/bin/env python3
"""Check that the generated documentation reports the actual skill totals."""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
DOCS = ROOT / "docs" / "skills.md"
README = ROOT / "README.md"


def count_skills():
    dirs = [p for p in SKILLS.iterdir() if p.is_dir() and (p / "SKILL.md").is_file()]
    return len(dirs), sum(p.name.startswith("hunt-") for p in dirs)


def main():
    total, hunt = count_skills()
    errors = []
    readme = README.read_text(encoding="utf-8")
    catalog = DOCS.read_text(encoding="utf-8")
    if f"**{total} Agent Skills**" not in readme:
        errors.append("README.md does not show the actual Agent Skills count")
    if f"**{hunt} `hunt-*` skills**" not in readme:
        errors.append("README.md does not show the actual hunt-* count")
    m = re.search(r"All \*\*(\d+) skills\*\*", catalog)
    if not m or int(m.group(1)) != total:
        errors.append("docs/skills.md total is missing or stale; regenerate the catalog")
    sections = [int(n) for n in re.findall(r"^## .+\((\d+)\)\s*$", catalog, re.M)]
    if sum(sections) != total:
        errors.append(f"docs/skills.md section totals sum to {sum(sections)}, expected {total}")
    if errors:
        for item in errors:
            print(f"ERROR: {item}", file=sys.stderr)
        return 1
    print(f"PASS: {total} skills ({hunt} hunt-*); README and catalog counts are consistent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
