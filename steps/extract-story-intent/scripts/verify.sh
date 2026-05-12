#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STEP_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_DIR="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

source "$SCRIPT_DIR/common.sh"

find_intent_file() {
  local saga_state_path="${1:-}"
  
  # Try to find *.intent.json from uncommitted git changes
  echo "[Verify] Searching for *.intent.json in uncommitted git changes..." >&2
  
  local intent_files=()
  while IFS= read -r file; do
    if [[ "$file" == *.intent.json ]]; then
      intent_files+=("$file")
    fi
  done < <(git diff --name-only HEAD 2>/dev/null; git ls-files --others --exclude-standard 2>/dev/null)
  
  if [[ ${#intent_files[@]} -eq 0 ]]; then
    echo "" >&2
    echo "ERROR: No *.intent.json files found in uncommitted git changes" >&2
    return 1
  fi
  
  if [[ ${#intent_files[@]} -gt 1 ]]; then
    echo "" >&2
    echo "ERROR: Multiple *.intent.json files found in uncommitted changes:" >&2
    for file in "${intent_files[@]}"; do
      echo "  - $file" >&2
    done
    echo "Please commit or remove all but one intent file" >&2
    return 1
  fi
  
  local intent_path="${intent_files[0]}"
  
  # Convert to absolute path if relative
  if [[ ! "$intent_path" = /* ]]; then
    intent_path="$PROJECT_DIR/$intent_path"
  fi
  
  if [[ ! -f "$intent_path" ]]; then
    echo "" >&2
    echo "ERROR: Intent file not found at path: $intent_path" >&2
    return 1
  fi
  
  echo "$intent_path"
  return 0
}

main() {
  local saga_state_path="${1:-}"
  
  local intent_path
  if ! intent_path=$(find_intent_file "$saga_state_path"); then
    exit 2
  fi
  
  echo "[Verify] Found intent file: $intent_path" >&2
  
  local schema_path="$STEP_DIR/schema/story-intent.schema.json"
  
  verify_structure "$intent_path" "$schema_path"
  verify_story_completeness "$intent_path"
  verify_consistency "$intent_path"
  
  if [[ ${#FAILURES[@]} -gt 0 ]]; then
    if [[ -n "$saga_state_path" ]]; then
      local sentinel_file="$saga_state_path/extract-story-intent.done.json"
      if [[ -f "$sentinel_file" ]]; then
        rm "$sentinel_file"
      fi
    fi
    exit_if_failed
  fi
  
  echo -e "${GREEN}[Verify] ✓ Verification passed${NC}" >&2
  echo "$intent_path"
}

main "$@"
