#!/usr/bin/env bash
# Post-cascade verification: TDD cycle completion gate
# Triggered after Cascade responses to detect cycle completion

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

# Read cascade response to detect cycle completion
response_text=$(get_field '.response' 2>/dev/null || echo "")

# Check if this is a TDD cycle completion point
if echo "$response_text" | grep -qiE "(decide next action|choose one:|continue to next test|all tests implemented)"; then
  
  # Check if code changes were made
  changed_files=$(get_changed_files)
  if [[ -z "$changed_files" ]]; then
    exit 0
  fi
  
  # Check if changes are code (not just docs)
  if ! echo "$changed_files" | grep -qE '\.(ts|tsx|cs|csproj)$'; then
    exit 0
  fi
  
  info "TDD Cycle Complete: Running verification before handoff..."
  exec "$SCRIPT_DIR/verify-all.sh" --mode=stop
fi

exit 0
