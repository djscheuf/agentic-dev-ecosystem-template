#!/usr/bin/env bash
# verify.sh - Verify minimal implementation sentinel structure
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
    local required_verify_fields=("failing_test_path" "failing_test_name" "changed_code_files")
    for field in "${required_verify_fields[@]}"; do
      if ! jq -e ".$field" <<< "$verify_params" &>/dev/null || [[ $(jq -r ".$field" <<< "$verify_params") == "null" ]]; then
        fail "Schema validation failed: Missing required verify_params field '$field'"
      fi
    done
    
    # Validate changed_code_files is an array
    if jq -e '.changed_code_files' <<< "$verify_params" &>/dev/null; then
      if ! jq -e '.changed_code_files | type == "array"' <<< "$verify_params" &>/dev/null; then
        fail "Schema validation failed: changed_code_files must be an array"
      fi
    fi
  fi
}

# Verify test cases file exists
verify_test_cases_file() {
  local test_cases_path="$1"
  
  if [[ -z "$test_cases_path" ]]; then
    fail "test_cases_path is empty"
    return
  fi
  
  if [[ ! -f "$test_cases_path" ]]; then
    fail "Test cases file not found: $test_cases_path"
    return
  fi
}

# Verify failing test file exists
verify_failing_test_file() {
  local failing_test_path="$1"
  
  if [[ -z "$failing_test_path" ]]; then
    fail "failing_test_path is empty"
    return
  fi
  
  if [[ ! -f "$failing_test_path" ]]; then
    fail "Failing test file not found: $failing_test_path"
    return
  fi
}


# Run the test (placeholder)
run_test() {
  local failing_test_path="$1"
  local failing_test_name="$2"
  
  # TODO: Implement test runner logic based on file type
  # - Detect language/framework from file extension
  # - Run the specific test
  # - Capture and validate that it passes
  echo "Placeholder: Would run test '$failing_test_name' from '$failing_test_path'" >&2
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
  
  # Extract test details from sentinel
  local sentinel
  sentinel=$(jq '.' "$sentinel_path")
  local test_cases_path
  local failing_test_path
  local failing_test_name
  local changed_code_files
  
  test_cases_path=$(jq -r '.verify_params.test_cases_path // empty' <<< "$sentinel")
  failing_test_path=$(jq -r '.verify_params.failing_test_path // empty' <<< "$sentinel")
  failing_test_name=$(jq -r '.verify_params.failing_test_name // empty' <<< "$sentinel")
  changed_code_files=$(jq '.verify_params.changed_code_files // empty' <<< "$sentinel")
  
  if [[ -z "$test_cases_path" ]] || [[ -z "$failing_test_path" ]] || [[ -z "$failing_test_name" ]] || [[ -z "$changed_code_files" ]]; then
    echo "Sentinel file missing required verify_params fields" >&2
    exit 2
  fi
  
  # Run verifications
  verify_sentinel_structure "$sentinel_path"
  verify_test_cases_file "$test_cases_path"
  verify_failing_test_file "$failing_test_path"
  run_test "$failing_test_path" "$failing_test_name"
  
  # Delete sentinel file after verification
  rm -f "$sentinel_path"

  # Exit if any failures
  exit_if_failed
  
  echo -e "${GREEN}Verification passed${NC}" >&2
}

main "$@"
