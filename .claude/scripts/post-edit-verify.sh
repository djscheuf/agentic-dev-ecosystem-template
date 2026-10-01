#!/usr/bin/env bash
# Post-edit verification: fast lint checks after code edits
# Triggered by PostToolUse/Edit|Write (see .claude/settings.json)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

file_path=$(get_file_path)

if [[ -z "$file_path" ]]; then
  exit 0
fi

# Skip non-code files
if [[ "$file_path" =~ \.(md|txt|json|yml|yaml|gitignore)$ ]]; then
  exit 0
fi

# Extension point: route to a linter for this repo's languages (e.g. ruff for
# src/**/*.py) by exec'ing a fuller verification script here. No linter wired
# up yet.

exit 0
