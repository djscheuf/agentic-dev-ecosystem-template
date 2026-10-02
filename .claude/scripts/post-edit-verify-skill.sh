#!/usr/bin/env bash
# Post-edit verification: run a skill's verify.sh when its completion sentinel
# is written. Triggered by PostToolUse/Edit|Write (see .claude/settings.json)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

file_path=$(get_file_path)

if [[ -z "$file_path" ]]; then
  exit 0
fi

# Accept persistent sentinels from any co-located .process directory
if [[ ! "$file_path" =~ \.process/.*\.done\.json$ ]]; then
  info "Skipping non-sentinel file: $file_path"
  exit 0
fi

# Extract task name from sentinel file
task=$(jq -r '.task // empty' "$file_path" 2>/dev/null)
if [[ -z "$task" ]]; then
  warn "Sentinel file has no 'task' property: $file_path"
  exit 0
fi

# Construct path to verify script
verify_script="$HOOK_PROJECT_DIR/.claude/skills/$task/verify.sh"

if [[ ! -f "$verify_script" ]]; then
  warn "Verify script not found for skill '$task': $verify_script"
  exit 0
fi

info "Running verify for skill: $task"

verify_output=$(bash "$verify_script" "$file_path" 2>&1)
verify_exit_code=$?

if [[ $verify_exit_code -ne 0 ]]; then
  block "Skill verification failed for '$task' (exit code: $verify_exit_code)\n\n$verify_output"
fi

info "Verification passed for skill: $task"
