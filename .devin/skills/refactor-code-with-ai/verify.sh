#!/usr/bin/env bash
# verify.sh - Verify refactor-code-with-ai sentinel structure
# Validates sentinel against schema using jq

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

# Track failures
FAILURES=()

# Add failure message
fail() {
  FAILURES+=("$1")
}

# Exit with error if any failures
exit_if_failed() {
  if [[ ${#FAILURES[@]} -gt 0 ]]; then
    echo -e "${RED}Verification failed:${NC}" >&2
    printf '%s\n' "${FAILURES[@]}" >&2
    exit 2
  fi
}

# Verify sentinel JSON structure
verify_sentinel_structure() {
  local sentinel_path="$1"
  
  if [[ ! -f "$sentinel_path" ]]; then
    fail "Sentinel file not found: $sentinel_path"
    return
  fi
  
  # Validate JSON is well-formed
  if ! jq empty "$sentinel_path" 2>/dev/null; then
    fail "Sentinel file is not valid JSON: $sentinel_path"
    return
  fi
  
  local sentinel
  sentinel=$(jq '.' "$sentinel_path")
  
  # Check required top-level properties
  local required_props=("task" "status" "verify_params")
  for prop in "${required_props[@]}"; do
    if ! jq -e ".$prop" <<< "$sentinel" &>/dev/null; then
      fail "Schema validation failed: Missing required property '$prop'"
    fi
  done
  
  # Validate status is one of the allowed values
  if jq -e '.status' <<< "$sentinel" &>/dev/null; then
    local status
    status=$(jq -r '.status' <<< "$sentinel")
    if [[ ! "$status" =~ ^(pending|in_progress|completed|failed)$ ]]; then
      fail "Schema validation failed: status must be one of 'pending', 'in_progress', 'completed', or 'failed', got '$status'"
    fi
  fi
  
  # Check verify_params structure
  if jq -e '.verify_params' <<< "$sentinel" &>/dev/null; then
    local verify_params
    verify_params=$(jq '.verify_params' <<< "$sentinel")
    
    # Check required verify_params fields
    local required_verify_fields=("refactored_code_files")
    for field in "${required_verify_fields[@]}"; do
      if ! jq -e ".$field" <<< "$verify_params" &>/dev/null || [[ $(jq -r ".$field" <<< "$verify_params") == "null" ]]; then
        fail "Schema validation failed: Missing required verify_params field '$field'"
      fi
    done
    
    # Validate refactored_code_files is an array
    if jq -e '.refactored_code_files' <<< "$verify_params" &>/dev/null; then
      if ! jq -e '.refactored_code_files | type == "array"' <<< "$verify_params" &>/dev/null; then
        fail "Schema validation failed: refactored_code_files must be an array"
      fi
    fi
  fi
}

# Verify refactored code files exist
verify_refactored_code_files() {
  local refactored_code_files="$1"
  
  if [[ -z "$refactored_code_files" ]]; then
    fail "refactored_code_files is empty"
    return
  fi
  
  # Parse array and check each file
  while IFS= read -r file; do
    file=$(echo "$file" | xargs) # trim whitespace
    if [[ -z "$file" ]]; then
      continue
    fi
    
    local full_path="$PROJECT_DIR/$file"
    if [[ ! -f "$full_path" ]]; then
      fail "Refactored code file not found: $file"
    fi
  done < <(jq -r '.[]' <<< "$refactored_code_files")
}

# Run the test (placeholder)
run_test() {
  # TODO: Implement test runner logic based on file type
  # - Detect language/framework from file extension
  # - Run the test suite
  # - Capture and validate that all tests pass
  echo "Placeholder: Would run test suite to verify refactored code" >&2
}

# Main execution
main() {
  local sentinel_path="$1"
  
  if [[ -z "$sentinel_path" ]]; then
    echo "Usage: verify.sh <sentinel_file>" >&2
    exit 2
  fi
  
  if [[ ! -f "$sentinel_path" ]]; then
    echo "Sentinel file not found: $sentinel_path" >&2
    exit 2
  fi
  
  # Extract details from sentinel
  local sentinel
  sentinel=$(jq '.' "$sentinel_path")
  local refactored_code_files
  
  refactored_code_files=$(jq '.verify_params.refactored_code_files // empty' <<< "$sentinel")
  
  if [[ -z "$refactored_code_files" ]]; then
    echo "Sentinel file missing required verify_params fields" >&2
    exit 2
  fi
  
  # Run verifications
  verify_sentinel_structure "$sentinel_path"
  verify_refactored_code_files "$refactored_code_files"
  run_test
  
  # Delete sentinel file after verification
  rm -f "$sentinel_path"

  # Exit if any failures
  exit_if_failed
  
  echo -e "${GREEN}Verification passed${NC}" >&2
}

main "$@"
