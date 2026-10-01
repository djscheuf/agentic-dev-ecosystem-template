#!/usr/bin/env bash
# Pre-read hook: prevent reading files that may contain secrets.
# Triggered by PreToolUse/read. Blocks env files and redirects to .envrc.example
# so the agent can discover available variables without seeing secret values.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

file_path=$(get_file_path) || true

if [[ -z "$file_path" ]]; then
  exit 0
fi

filename=$(basename "$file_path")

# Safe reference files are allowed.
case "$filename" in
  .envrc.example|.env.example)
    exit 0
    ;;
esac

# Block env files that may contain secrets.
case "$filename" in
  .env|.envrc|.env.local|.envrc.local|.env.*.local|.envrc.*.local|.env.*|.envrc.*)
    block "Blocked read of '${filename}': it may contain secrets. Read '.envrc.example' to see what environment variables are available without their secret values."
    ;;
esac

exit 0
