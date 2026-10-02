#!/usr/bin/env bash
# Pre-command verification: gate dangerous commands
# Triggered by PreToolUse/Bash (see .claude/settings.json)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

command=$(get_command)

if [[ -z "$command" ]]; then
  exit 0
fi

# Extension point: gate specific commands (e.g. git push/merge) by exec'ing a
# fuller verification script here. No gating rules defined yet.

exit 0
