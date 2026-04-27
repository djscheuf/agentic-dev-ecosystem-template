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
bash "$verify_script" "$file_path"