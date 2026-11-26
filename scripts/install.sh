#!/usr/bin/env bash
# Install the Hermes-BugHunter skills into a Hermes skills directory.
#
# Thin wrapper around scripts/hermes_install.py, which does the real work:
# resolves $HERMES_HOME / named profiles, copies into a namespaced tree,
# detects name collisions with skills already installed in that profile, and
# verifies that every installed skill resolves under Hermes' alias rules.
#
# Usage:
#   bash scripts/install.sh                  # install into $HERMES_HOME/skills
#   bash scripts/install.sh --profile bbh    # install into a named profile
#   bash scripts/install.sh --force          # replace changed skill dirs
#   bash scripts/install.sh --dry-run
#   bash scripts/install.sh --uninstall
cp -r /root/Hermes-BugHunter /root/.hermes/skills
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

command -v python3 >/dev/null 2>&1 || {
  echo "python3 is required (the installer is stdlib-only Python)" >&2
  exit 1
}

exec python3 "$SCRIPT_DIR/hermes_install.py" "$@"
