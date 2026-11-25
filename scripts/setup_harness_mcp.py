#!/usr/bin/env python3
"""Print an MCP server snippet for manual review; never edits Hermes config."""
import argparse
import json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", default="burp", help="MCP server name")
    parser.add_argument("--command", required=True, help="Executable, e.g. java or python3")
    parser.add_argument("--arg", action="append", default=[], help="Argument; repeat for each argument")
    args = parser.parse_args()

    print("Add this snippet manually to your Hermes MCP configuration after reviewing it:")
    print("mcp_servers:")
    print(f"  {args.name}:")
    print(f"    command: {json.dumps(args.command)}")
    if args.arg:
        print("    args: [" + ", ".join(json.dumps(item) for item in args.arg) + "]")
    print("\nNo file was read or modified. Model and credential settings are untouched.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
