#!/usr/bin/env python3
"""
check_install_report.py — assert on the JSON that hermes_install.py emits.

Used by CI (and handy locally) so the install contract is checked by exit code
instead of by reading the table:

    python3 scripts/hermes_install.py --dest /tmp/s --json > report.json
    python3 scripts/check_install_report.py report.json 98
    python3 scripts/check_install_report.py report.json 98 \\
        --expect-collision hunt-xss:hermes-bughunter/hunt-xss

Exit 0 when every assertion holds, 1 otherwise.
"""
from __future__ import annotations

import argparse
import json
import sys


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("report", help="JSON file written by hermes_install.py --json")
    parser.add_argument("expected", type=int, help="expected number of installed skills")
    parser.add_argument("--expect-collision", action="append", default=[],
                        metavar="NAME:LOAD_NAME",
                        help="assert NAME collides and loads as LOAD_NAME")
    args = parser.parse_args(argv)

    try:
        report = json.load(open(args.report, encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"cannot read report: {exc}", file=sys.stderr)
        return 1
    verification = report.get("verification")
    if not verification:
        print("report has no verification block (was --no-verify used?)", file=sys.stderr)
        return 1

    failures = []
    if verification["total"] != args.expected:
        failures.append(f"installed {verification['total']}, expected {args.expected}")
    if verification["unloadable"]:
        failures.append(f"unloadable skills: {verification['unloadable']}")

    ambiguous = {row["name"]: row["load_name"] for row in verification["ambiguous"]}
    for spec in args.expect_collision:
        name, _, load_name = spec.partition(":")
        if name not in ambiguous:
            failures.append(f"expected {name!r} to be ambiguous, it is not")
        elif ambiguous[name] != load_name:
            failures.append(f"{name!r} loads as {ambiguous[name]!r}, expected {load_name!r}")

    if not args.expect_collision and ambiguous:
        failures.append(f"unexpected collisions: {sorted(ambiguous)}")

    for failure in failures:
        print(f"FAIL {failure}", file=sys.stderr)
    if failures:
        return 1
    print(f"install report OK: {verification['total']} skills, "
          f"{len(verification['unique'])} unique names")
    return 0


if __name__ == "__main__":
    sys.exit(main())
