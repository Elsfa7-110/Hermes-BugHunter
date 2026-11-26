#!/usr/bin/env python3
"""
hermes_compat.py — verify the bundle against Hermes Agent's skill loader rules.

`lint_skills.py` covers repo hygiene (denylist, secrets, YAML safety). This
script covers the rules Hermes itself enforces when it builds the skill index,
registers slash commands, and resolves `skill_view(name)`:

  STRUCTURE (errors)
    - every skill directory has a SKILL.md that starts with a `---` fence
    - no nested SKILL.md inside a support dir (references/, templates/,
      assets/, scripts/) — Hermes prunes those, so the skill would be invisible
    - no duplicate declared names or duplicate directory names across the
      bundle (same-tier duplicates become AMBIGUOUS: no slash command, and
      skill_view refuses the bare name)
  FRONTMATTER (errors)
    - `name` present, matches ^[a-z0-9][a-z0-9-]*$, <= 64 chars, equals the dir
    - `description` present, single line, <= 1024 chars
    - `platforms:` (if present) only linux/macos/windows
  FRONTMATTER (warnings)
    - description clipped in the index: Hermes shows ~60 chars by default
      (skills.index_desc_limit), so the first sentence must carry the trigger
    - generic openers ("Hunting skill for ...") lose routing signal
  BODY (warnings)
    - > 500 lines: move reference material into references/ (progressive
      disclosure costs one skill_view file_path call instead of every load)
    - UTF-8 BOM (Hermes strips it, other tools choke)
    - literal control characters
  LINKS (warnings)
    - relative markdown links inside a skill dir that do not resolve

Exit 0 clean, 1 on errors. `--json` emits a machine-readable report; the
installer reuses `scan_tree()` / `resolve_catalog()` to prove a destination
tree resolves cleanly before it prints a success message.

Usage:
    python3 scripts/hermes_compat.py                    # check ./skills
    python3 scripts/hermes_compat.py --json
    python3 scripts/hermes_compat.py ~/.hermes/skills/hermes-bughunter
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
MAX_NAME = 64
MAX_DESC = 1024
MAX_BODY_LINES = 500
INDEX_DESC_DEFAULT = 60
SUPPORT_DIRS = frozenset(("references", "templates", "assets", "scripts"))
PLATFORMS = frozenset(("linux", "macos", "windows", "darwin", "win32", "any"))
GENERIC_OPENERS = (
    "hunting skill for",
    "skill for",
    "this skill",
    "a skill that",
)
LINK_TARGET_RE = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
FENCE_RE = re.compile(r"^\s*(```+|~~~+)")
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")


# --------------------------------------------------------------------------
# frontmatter (mirrors agent/skill_utils.parse_frontmatter: YAML, then a
# key:value fallback). PyYAML is optional so the repo stays stdlib-only.
# --------------------------------------------------------------------------
def _yaml_load(text: str):
    try:
        import yaml  # type: ignore
    except Exception:  # pragma: no cover - environment without PyYAML
        return None
    try:
        return yaml.safe_load(text)
    except Exception as exc:  # surface strict-parser rejection to the caller
        raise ValueError(str(exc).splitlines()[0]) from exc


def split_frontmatter(raw: str) -> Tuple[Dict[str, object], str, Optional[str]]:
    """(frontmatter, body, error). Tolerates a leading BOM like Hermes does."""
    text = raw[1:] if raw.startswith("\ufeff") else raw
    if not text.startswith("---"):
        return {}, text, "file must start with a '---' frontmatter fence"
    match = re.search(r"\n---[ \t]*\r?\n", text[3:])
    if not match:
        return {}, text, "frontmatter opened with '---' but never closed"
    block = text[3:match.start() + 3]
    body = text[match.end() + 3:]
    parsed = _yaml_load(block)
    if isinstance(parsed, dict):
        return dict(parsed), body, None
    if parsed is not None:  # YAML parsed but is not a mapping
        return {}, body, "frontmatter is not a YAML mapping"
    fm: Dict[str, object] = {}
    for line in block.splitlines():
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        fm[key.strip()] = _unquote(value.strip())
    return fm, body, None


def _unquote(value: str) -> str:
    """Strip one matching pair of quotes from a scalar, undoing YAML escapes.

    The fallback parser runs when PyYAML is absent (the default install). Without
    this, `description: "..."` would keep its quotes in every length check and in
    the index preview Hermes actually renders.
    """
    if len(value) < 2 or value[0] != value[-1] or value[0] not in "\"'":
        return value
    quote, inner = value[0], value[1:-1]
    if quote == "'":
        return inner.replace("''", "'")
    escapes = {'"': '"', "\\": "\\", "/": "/", "b": "\b", "f": "\f",
               "n": "\n", "r": "\r", "t": "\t", "0": "\0"}
    return re.sub(r"\\(.)", lambda m: escapes.get(m.group(1), m.group(1)), inner)


def _one_line(value: object) -> str:
    if isinstance(value, str):
        return " ".join(value.split())
    return "" if value is None else " ".join(str(value).split())


def _as_list(value: object) -> List[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(v).strip() for v in value if str(v).strip()]
    return [p.strip() for p in str(value).strip("[]").split(",") if p.strip()]


# --------------------------------------------------------------------------
# discovery / resolution (same aliases Hermes uses)
# --------------------------------------------------------------------------
def scan_tree(root: Path) -> List[dict]:
    """Every skill under *root*, with the identity fields Hermes indexes on."""
    entries: List[dict] = []
    root = Path(root).resolve()
    for dirpath, dirnames, filenames in os.walk(str(root), followlinks=True):
        here = Path(dirpath)
        has_skill = "SKILL.md" in filenames
        # Hermes prunes support dirs of a skill root and VCS/cache dirs.
        dirnames[:] = sorted(
            d for d in dirnames
            if d not in EXCLUDED_DIRS and not (has_skill and d in SUPPORT_DIRS)
        )
        if not has_skill:
            continue
        skill_md = here / "SKILL.md"
        try:
            raw = skill_md.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            entries.append({"path": skill_md, "dir": here, "name": here.name,
                            "rel": here.relative_to(root).as_posix(),
                            "raw": "", "fm": {}, "body": "", "error": "not UTF-8"})
            continue
        fm, body, err = split_frontmatter(raw)
        entries.append({
            "path": skill_md,
            "dir": here,
            "name": str(fm.get("name") or here.name).strip()[:MAX_NAME],
            "dir_name": here.name,
            "rel": here.relative_to(root).as_posix(),
            "raw": raw,
            "fm": fm,
            "body": body,
            "error": err,
        })
    return sorted(entries, key=lambda e: e["rel"])


EXCLUDED_DIRS = frozenset((
    ".git", ".github", ".hub", ".archive", ".curator_backups", ".locks",
    ".venv", "venv", "node_modules", "site-packages", "__pycache__",
    ".tox", ".nox", ".pytest_cache", ".mypy_cache", ".ruff_cache",
))


def resolve_catalog(entries: Iterable[dict]) -> List[dict]:
    """Annotate entries with (status, load_name) using Hermes' alias rules.

    Aliases per skill: declared name, directory name, relative path. A bare name
    wins only when exactly one skill claims it; otherwise the relative path is
    the load name, and when that is shared too the skill is unloadable.
    """
    rows = [dict(e) for e in entries]
    owners: Dict[str, List[int]] = {}
    for i, row in enumerate(rows):
        for alias in {row["name"], row["dir_name"], row["rel"]}:
            owners.setdefault(alias, []).append(i)
    for i, row in enumerate(rows):
        name, rel = row["name"], row["rel"]
        if len(owners.get(name, [])) == 1:
            row["status"], row["load_name"] = "unique", name
        elif owners.get(rel, []) == [i]:
            row["status"], row["load_name"] = "ambiguous", rel
        else:
            row["status"], row["load_name"] = "unloadable", None
    return rows


# --------------------------------------------------------------------------
# checks
# --------------------------------------------------------------------------
def _index_preview(desc: str, limit: int) -> str:
    """How the Hermes skill index will show *desc*.

    Hermes clips at a word boundary. Prefer the last complete sentence inside
    the window: that is what the reader of the index actually sees, and a
    sentence that ends inside 60 chars means the trigger survived the clip.
    """
    if len(desc) <= limit:
        return desc
    window = desc[:limit]
    ends = [m.end() for m in re.finditer(r"[.!?](?=\s|$)", window)]
    if ends:
        return window[: ends[-1]]
    head = window[: limit - 3]
    cut = head.rfind(" ")
    return (head[:cut] if cut > 1 else head).rstrip(" ,;:-—&/") + "..."


def check_skill(entry: dict, *, index_limit: int = INDEX_DESC_DEFAULT,
                max_body_lines: int = MAX_BODY_LINES) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    rel = entry["rel"]

    if entry.get("error"):
        errors.append(f"{rel}: {entry['error']}")
    raw, fm, body = entry["raw"], entry["fm"], entry["body"]

    # --- frontmatter identity -------------------------------------------
    name = str(fm.get("name") or "").strip()
    if not name:
        errors.append(f"{rel}: frontmatter missing `name`")
    else:
        if not NAME_RE.match(name):
            errors.append(f"{rel}: name {name!r} must match ^[a-z0-9][a-z0-9-]*$")
        if len(name) > MAX_NAME:
            errors.append(f"{rel}: name {len(name)} chars > {MAX_NAME}")
        if name != entry["dir_name"]:
            warnings.append(
                f"{rel}: name {name!r} != directory {entry['dir_name']!r} — "
                "skill_view resolves both, but they must stay in sync for /commands")

    desc = _one_line(fm.get("description"))
    if not desc:
        errors.append(f"{rel}: frontmatter missing `description`")
    else:
        if len(desc) > MAX_DESC:
            errors.append(f"{rel}: description {len(desc)} chars > {MAX_DESC} (Hermes cap)")
        preview = _index_preview(desc, index_limit)
        if len(desc) > index_limit and preview.endswith("..."):
            warnings.append(
                f"{rel}: index line ends mid-clause at {index_limit} chars "
                f"({preview!r}) — front-load the trigger and the action")
        low = desc.lower()
        if any(low.startswith(opener) for opener in GENERIC_OPENERS):
            warnings.append(
                f"{rel}: description opens with a generic phrase — say what it "
                "finds and on what surface so routing picks it")

    platforms = _as_list(fm.get("platforms"))
    for platform in platforms:
        if platform.lower() not in PLATFORMS:
            warnings.append(f"{rel}: unknown platforms entry {platform!r}")

    # --- body -------------------------------------------------------------
    lines = len(body.splitlines())
    if lines > max_body_lines:
        warnings.append(
            f"{rel}: body {lines} lines > {max_body_lines} — move reference "
            "material to references/ and point at it (progressive disclosure)")
    if raw.startswith("\ufeff"):
        warnings.append(f"{rel}: UTF-8 BOM — Hermes strips it, other tools may not")
    for lineno, line in enumerate(raw.splitlines(), 1):
        bad = [ch for ch in line if ch != "\t" and (ord(ch) < 32 or ord(ch) == 127)]
        if bad:
            warnings.append(
                f"{rel}:{lineno}: literal control character 0x{ord(bad[0]):02x}")
            break

    # --- relative links ---------------------------------------------------
    errors_links = _check_links(entry)
    warnings.extend(errors_links)
    return errors, warnings


def _strip_code(text: str) -> str:
    out, in_fence, fence = [], False, ""
    for line in text.splitlines():
        m = FENCE_RE.match(line)
        if m:
            if not in_fence:
                in_fence, fence = True, m.group(1)[:3]
            elif line.strip().startswith(fence):
                in_fence = False
            out.append("")
            continue
        out.append("" if in_fence else INLINE_CODE_RE.sub("", line))
    return "\n".join(out)


def _check_links(entry: dict) -> List[str]:
    problems: List[str] = []
    text = _strip_code(entry["raw"])
    base = entry["dir"]
    for m in LINK_TARGET_RE.finditer(text):
        target = m.group(1)
        if target.startswith(("http://", "https://", "mailto:", "#", "tel:", "data:")):
            continue
        clean = target.split("#", 1)[0].split("?", 1)[0]
        if not clean:
            continue
        # Only file-looking targets; regex/payload snippets live outside code
        # fences in a few skills and are not links.
        if not re.match(r"^[\w./~-]+\.(md|json|ya?ml|py|sh|txt|toml|jpe?g|png|svg|html)$", clean):
            continue
        resolved = (base / clean).resolve()
        if not resolved.exists():
            problems.append(f"{entry['rel']}: broken relative link -> {clean}")
    return problems


def check_structure(root: Path) -> Tuple[List[str], List[str]]:
    """Tree-level checks: nested SKILL.md, duplicates, unloadable skills."""
    errors: List[str] = []
    warnings: List[str] = []
    root = root.resolve()
    if not root.is_dir():
        return [f"{root}: not a directory"], warnings

    for dirpath, dirnames, filenames in os.walk(str(root)):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]
        here = Path(dirpath)
        if here == root or "SKILL.md" not in filenames:
            continue
        rel_parts = here.relative_to(root).parts
        if any(part in SUPPORT_DIRS for part in rel_parts[:-1]):
            errors.append(
                f"{here.relative_to(root).as_posix()}: SKILL.md inside a support "
                "dir — Hermes prunes it, so it can never load")

    entries = [e for e in scan_tree(root) if not e["rel"].endswith("/references")]
    by_name: Dict[str, List[str]] = {}
    by_dir: Dict[str, List[str]] = {}
    for entry in entries:
        by_name.setdefault(entry["name"], []).append(entry["rel"])
        by_dir.setdefault(entry["dir_name"], []).append(entry["rel"])
    for name, rels in sorted(by_name.items()):
        if len(rels) > 1:
            errors.append(
                f"duplicate skill name {name!r} in {len(rels)} dirs "
                f"({', '.join(rels)}) — Hermes refuses the bare name; rename one")
    for name, rels in sorted(by_dir.items()):
        if len(rels) > 1:
            errors.append(f"duplicate skill dir name {name!r} ({', '.join(rels)})")

    for row in resolve_catalog(entries):
        if row["status"] == "unloadable":
            errors.append(
                f"{row['rel']}: no unique load name — skill_view cannot open it "
                "and it gets no /command")
        elif row["status"] == "ambiguous":
            warnings.append(
                f"{row['rel']}: loads as /skill {row['load_name']} (name is "
                "shared) — rename or install into an isolated namespace")
    return errors, warnings


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check skills against Hermes Agent loader rules.")
    parser.add_argument("roots", nargs="*", help="skill roots (default: ./skills)")
    parser.add_argument("--json", action="store_true", help="machine-readable report")
    parser.add_argument("--index-desc-limit", type=int, default=INDEX_DESC_DEFAULT,
                        help=f"index width Hermes clips descriptions to (default {INDEX_DESC_DEFAULT})")
    parser.add_argument("--max-body-lines", type=int, default=MAX_BODY_LINES)
    parser.add_argument("--strict", action="store_true", help="treat warnings as errors")
    args = parser.parse_args(argv)

    repo = Path(__file__).resolve().parent.parent
    roots = [Path(p) for p in (args.roots or [str(repo / "skills")])]

    report = {"roots": [], "errors": [], "warnings": [], "skills": []}
    for root in roots:
        struct_errors, struct_warnings = check_structure(root)
        report["errors"].extend(struct_errors)
        report["warnings"].extend(struct_warnings)
        for entry in scan_tree(root):
            errs, warns = check_skill(entry, index_limit=args.index_desc_limit,
                                      max_body_lines=args.max_body_lines)
            report["errors"].extend(errs)
            report["warnings"].extend(warns)
            report["skills"].append({
                "rel": entry["rel"], "name": entry["name"],
                "lines": len(entry["body"].splitlines()),
                "description_chars": len(_one_line(entry["fm"].get("description"))),
                "errors": len(errs), "warnings": len(warns),
            })
        report["roots"].append(str(root))

    if args.strict:
        report["errors"].extend(report.pop("warnings"))
        report["warnings"] = []

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        for message in report["errors"]:
            print(f"ERROR {message}")
        for message in report["warnings"]:
            print(f"WARN  {message}")
        print(f"\nChecked {len(report['skills'])} skill(s) in "
              f"{len(roots)} root(s): {len(report['errors'])} error(s), "
              f"{len(report['warnings'])} warning(s).")
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
