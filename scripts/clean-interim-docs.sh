#!/usr/bin/env bash
# Clean up interim documentation artifacts (sentinels, audits, grades, plans).
#
# Usage: scripts/clean-interim-docs.sh [--delete] [--ending <ending>] [<directory>]
#
# Defaults to a dry run. Excludes .git, .devin, .venv, node_modules, .pytest_cache,
# and __pycache__. When no --ending is given, the default set of interim endings
# is used.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

DEFAULT_ENDINGS=(
  ".done.json"
  ".audit.json"
  ".analysis-grade.json"
  ".design-grade.json"
  ".plan.json"
  ".plan.test-cases.json"
)

DELETE=0
ENDINGS=()
TARGET_DIR="$REPO_ROOT"
TARGET_DIR_SET=""

usage() {
  cat <<EOF
Usage: ${BASH_SOURCE[0]} [options] [<directory>]

Options:
  --delete              Actually remove the matched files (default is dry-run).
  -e, --ending <end>    Filter to a specific file ending. Can be given multiple times.
  -h, --help            Show this help.

Examples:
  # List all default interim artifacts
  scripts/clean-interim-docs.sh

  # List only .audit.json files
  scripts/clean-interim-docs.sh --ending .audit.json

  # Remove all .done.json sentinels
  scripts/clean-interim-docs.sh --delete --ending .done.json
EOF
}

log() { printf '[clean-interim-docs] %s\n' "$1"; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --delete)
      DELETE=1
      shift
      ;;
    -e|--ending)
      if [[ $# -lt 2 ]]; then
        log "ERROR: $1 requires an argument"
        exit 1
      fi
      ENDINGS+=("$2")
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    -*)
      log "ERROR: unknown option: $1"
      usage >&2
      exit 1
      ;;
    *)
      if [[ -n "$TARGET_DIR_SET" ]]; then
        log "ERROR: only one directory argument is allowed"
        exit 1
      fi
      TARGET_DIR="$1"
      TARGET_DIR_SET=1
      shift
      ;;
  esac
done

if [[ ${#ENDINGS[@]} -eq 0 ]]; then
  ENDINGS=("${DEFAULT_ENDINGS[@]}")
fi

find_args=()
first=1
for ending in "${ENDINGS[@]}"; do
  if [[ $first -eq 1 ]]; then
    find_args+=(-name "*${ending}")
    first=0
  else
    find_args+=(-o -name "*${ending}")
  fi
done

mapfile -d '' -t matches < <(
  find "$TARGET_DIR" -type f \( "${find_args[@]}" \) \
    ! -path "*/.git/*" \
    ! -path "*/.devin/*" \
    ! -path "*/.venv/*" \
    ! -path "*/node_modules/*" \
    ! -path "*/.pytest_cache/*" \
    ! -path "*/__pycache__/*" \
    -print0 2>/dev/null | sort -z
)

if [[ ${#matches[@]} -eq 0 ]]; then
  log "No matching interim files found."
  exit 0
fi

if [[ $DELETE -eq 1 ]]; then
  for f in "${matches[@]}"; do
    rm -f "$f"
    log "Removed: $f"
  done
else
  log "Dry run: the following ${#matches[@]} file(s) would be removed:"
  for f in "${matches[@]}"; do
    printf '  %s\n' "$f"
  done
fi
