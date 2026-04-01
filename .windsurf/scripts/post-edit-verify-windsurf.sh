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

# Skip non-code files
if [[ "$file_path" =~ \.(md|txt|json|yml|yaml|gitignore)$ ]]; then
  exit 0
fi

# Route to appropriate verifier
if [[ "$file_path" =~ \.(ts|tsx)$ ]]; then
  pkg=$(affected_ui_packages "$file_path")
  if [[ -n "$pkg" ]]; then
    exec "$SCRIPT_DIR/verify-typescript.sh" --check=lint --scope="$pkg"
  fi
elif [[ "$file_path" =~ \.(cs|csproj)$ ]]; then
  project=$(affected_dotnet_projects "$file_path")
  if [[ -n "$project" ]]; then
    exec "$SCRIPT_DIR/verify-dotnet.sh" --check=lint --scope="$project"
  fi
fi

exit 0
