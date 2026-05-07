#!/usr/bin/env bash
# Post-edit verification: fast lint checks after code edits
# Triggered by Windsurf after file edits

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

# Get edited file from hook stdin
file_path=$(get_file_path)

if [[ -z "$file_path" ]]; then
  exit 0
fi

# Skip non-sentinel files (must be in .process directory and end with .done.json)
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
verify_script="$HOOK_PROJECT_DIR/.windsurf/skills/$task/verify.sh"

# Check if verify script exists
if [[ ! -f "$verify_script" ]]; then
  warn "Verify script not found for skill '$task': $verify_script"
  exit 0
fi

# Run the verify script with sentinel file path
info "Running verify for skill: $task"

# Capture both output and exit code
verify_output=$(bash "$verify_script" "$file_path" 2>&1)
verify_exit_code=$?

# If verification failed, block with detailed error
if [[ $verify_exit_code -ne 0 ]]; then
  block "Skill verification failed for '$task' (exit code: $verify_exit_code)\n\n$verify_output"
fi

# Log success
info "Verification passed for skill: $task"