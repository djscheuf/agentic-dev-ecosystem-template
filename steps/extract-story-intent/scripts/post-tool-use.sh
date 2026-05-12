#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STEP_DIR="$(dirname "$SCRIPT_DIR")"

source "$SCRIPT_DIR/common.sh"

HOOK_DATA=$(cat)

TOOL_NAME=$(echo "$HOOK_DATA" | jq -r '.tool_name // empty' 2>/dev/null || echo "")

if [[ "$TOOL_NAME" != "write_to_file" && "$TOOL_NAME" != "edit" && "$TOOL_NAME" != "multi_edit" ]]; then
  exit 0
fi

FILE_PATH=""
if [[ "$TOOL_NAME" == "write_to_file" ]]; then
  FILE_PATH=$(echo "$HOOK_DATA" | jq -r '.tool_input.TargetFile // empty' 2>/dev/null || echo "")
elif [[ "$TOOL_NAME" == "edit" || "$TOOL_NAME" == "multi_edit" ]]; then
  FILE_PATH=$(echo "$HOOK_DATA" | jq -r '.tool_input.file_path // empty' 2>/dev/null || echo "")
fi

if [[ -z "$FILE_PATH" ]]; then
  exit 0
fi

if [[ ! "$FILE_PATH" =~ \.intent\.json$ ]]; then
  exit 0
fi

echo -e "${YELLOW}[Post-Tool-Use] Detected write to .intent.json file: $FILE_PATH${NC}" >&2
echo "[Post-Tool-Use] Running validation checks..." >&2

SCHEMA_PATH="$STEP_DIR/schema/story-intent.schema.json"

verify_structure "$FILE_PATH" "$SCHEMA_PATH"
verify_story_completeness "$FILE_PATH"
verify_consistency "$FILE_PATH"

if [[ ${#FAILURES[@]} -gt 0 ]]; then
  echo -e "${RED}[Post-Tool-Use] ✗ Validation failed for $FILE_PATH${NC}" >&2
  echo -e "${RED}Issues found:${NC}" >&2
  printf '%s\n' "${FAILURES[@]}" >&2
  echo "" >&2
  echo "Please fix the above issues in the intent file." >&2
  exit 1
fi

echo -e "${GREEN}[Post-Tool-Use] ✓ Validation passed for $FILE_PATH${NC}" >&2
exit 0
