#!/usr/bin/env bash
# Pre-command verification: gate dangerous commands
# Triggered by Windsurf before running commands

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

# Get command from hook stdin
command=$(get_command)

if [[ -z "$command" ]]; then
  exit 0
fi

# Only gate git push and merge commands
if [[ "$command" =~ ^git\ (push|merge) ]]; then
  info "Git push/merge detected, running full verification..."
  exec "$SCRIPT_DIR/verify-all.sh" --mode=full
fi

exit 0
