#!/usr/bin/env bash
# Copy this bundle's Agent Skills into Hermes. Does not edit Hermes config or credentials.
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
SOURCE="$REPO_DIR/skills"
DEST="${HERMES_SKILLS_DIR:-$HOME/.hermes/skills}"
FORCE=0
DRY_RUN=0

usage() {
  cat <<'EOF'
Usage: bash scripts/install.sh [--force] [--dry-run] [--dest PATH]

Copies only the skills/ directory into ~/.hermes/skills/.
No model selection, API key, provider, MCP, or config.yaml changes are made.

Options:
  --force       Replace destination skills with the bundled versions
  --dry-run     Show what would be copied
  --dest PATH   Use a custom skills directory (default: ~/.hermes/skills)
  --help        Show this help
EOF
}
while (($#)); do
  case "$1" in
    --force) FORCE=1 ;;
    --dry-run) DRY_RUN=1 ;;
    --dest) shift; [[ $# -gt 0 ]] || { echo 'Missing path after --dest' >&2; exit 2; }; DEST="$1" ;;
    --help|-h) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
  shift
done
[[ -d "$SOURCE" ]] || { echo "Skills directory not found: $SOURCE" >&2; exit 1; }
mkdir -p "$DEST"
count=0; skipped=0
for item in "$SOURCE"/*; do
  [[ -d "$item" ]] || continue
  name="$(basename "$item")"
  target="$DEST/$name"
  if [[ -e "$target" && "$FORCE" -ne 1 ]]; then
    echo "SKIP existing: $name (use --force to replace)"
    skipped=$((skipped + 1))
    continue
  fi
  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "COPY $item -> $target"
  else
    rm -rf -- "$target"
    cp -a -- "$item" "$target"
    echo "COPIED $name"
  fi
  count=$((count + 1))
done
echo "Skills copied: $count; existing skipped: $skipped; destination: $DEST"
