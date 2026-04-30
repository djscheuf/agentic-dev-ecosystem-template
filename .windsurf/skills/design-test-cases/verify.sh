#!/usr/bin/env bash
# verify.sh - Verify test cases JSON structure
# Validates test cases against schema using jq

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

# Verify test cases JSON structure against schema
verify_structure() {
  local test_cases_path="$1"
  
  if [[ ! -f "$test_cases_path" ]]; then
    fail "Test cases file not found: $test_cases_path"
    return
  fi
  
  # Validate JSON is well-formed
  if ! jq empty "$test_cases_path" 2>/dev/null; then
    fail "Test cases file is not valid JSON: $test_cases_path"
    return
  fi
  
  local test_cases
  test_cases=$(jq '.' "$test_cases_path")
  
  # Check required top-level properties
  local required_props=("target_story" "source_workstream" "priority_groups")
  for prop in "${required_props[@]}"; do
    if ! jq -e ".$prop" <<< "$test_cases" &>/dev/null; then
      fail "Schema validation failed: Missing required property '$prop'"
    fi
  done
  
  # Validate priority_groups is array
  if jq -e '.priority_groups' <<< "$test_cases" &>/dev/null; then
    if ! jq -e '.priority_groups | type == "array"' <<< "$test_cases" &>/dev/null; then
      fail "Schema validation failed: priority_groups must be an array"
    fi
  fi
}

# Verify test cases completeness
verify_test_cases_completeness() {
  local test_cases_path="$1"
  local test_cases
  
  test_cases=$(jq '.' "$test_cases_path")
  
  # Check top-level required fields
  local required_fields=("target_story" "source_workstream" "priority_groups")
  for field in "${required_fields[@]}"; do
    if ! jq -e ".$field" <<< "$test_cases" &>/dev/null || [[ $(jq -r ".$field" <<< "$test_cases") == "null" ]]; then
      fail "Missing required field: '$field'"
    fi
  done
  
  # Check priority_groups structure
  if jq -e '.priority_groups' <<< "$test_cases" &>/dev/null; then
    local priority_groups
    priority_groups=$(jq '.priority_groups' <<< "$test_cases")
    
    # Check if it's an array
    if ! jq -e 'type == "array"' <<< "$priority_groups" &>/dev/null; then
      fail "priority_groups must be an array"
      return
    fi
    
    # Check if array is non-empty
    local group_count
    group_count=$(jq 'length' <<< "$priority_groups")
    if [[ $group_count -eq 0 ]]; then
      fail "priority_groups must be a non-empty list"
      return
    fi
    
    # Check each priority group
    for idx in $(seq 0 $((group_count - 1))); do
      local group
      group=$(jq ".[$idx]" <<< "$priority_groups")
      
      if ! jq -e '.description' <<< "$group" &>/dev/null || [[ $(jq -r '.description' <<< "$group") == "null" ]]; then
        fail "Priority group $idx missing 'description' field"
      fi
      
      if ! jq -e '.tests' <<< "$group" &>/dev/null; then
        fail "Priority group $idx missing 'tests' field"
      else
        local tests
        tests=$(jq '.tests' <<< "$group")
        
        # Check if tests is an array
        if ! jq -e 'type == "array"' <<< "$tests" &>/dev/null; then
          fail "Priority group $idx tests must be an array"
          continue
        fi
        
        # Check each test
        local test_count
        test_count=$(jq 'length' <<< "$tests")
        for test_idx in $(seq 0 $((test_count - 1))); do
          local test
          test=$(jq ".[$test_idx]" <<< "$tests")
          
          if ! jq -e '.id' <<< "$test" &>/dev/null; then
            fail "Priority group $idx test $test_idx missing 'id' field"
          fi
          
          if ! jq -e '.name' <<< "$test" &>/dev/null || [[ $(jq -r '.name' <<< "$test") == "null" ]]; then
            fail "Priority group $idx test $test_idx missing 'name' field"
          fi
          
          if ! jq -e '.status' <<< "$test" &>/dev/null || [[ $(jq -r '.status' <<< "$test") == "null" ]]; then
            fail "Priority group $idx test $test_idx missing 'status' field"
          else
            local status
            status=$(jq -r '.status' <<< "$test")
            if [[ "$status" != "pending" ]]; then
              fail "Priority group $idx test $test_idx has invalid status '$status'. Must be 'pending'"
            fi
          fi
          
          if ! jq -e '.description' <<< "$test" &>/dev/null || [[ $(jq -r '.description' <<< "$test") == "null" ]]; then
            fail "Priority group $idx test $test_idx missing 'description' field"
          fi
          
          if ! jq -e '.arrange' <<< "$test" &>/dev/null || [[ $(jq -r '.arrange' <<< "$test") == "null" ]]; then
            fail "Priority group $idx test $test_idx missing 'arrange' field"
          fi
          
          if ! jq -e '.act' <<< "$test" &>/dev/null || [[ $(jq -r '.act' <<< "$test") == "null" ]]; then
            fail "Priority group $idx test $test_idx missing 'act' field"
          fi
          
          if ! jq -e '.assert' <<< "$test" &>/dev/null || [[ $(jq -r '.assert' <<< "$test") == "null" ]]; then
            fail "Priority group $idx test $test_idx missing 'assert' field"
          fi
        done
      fi
    done
  fi
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
  
  # Extract test cases path from sentinel
  local sentinel
  sentinel=$(jq '.' "$sentinel_path")
  local test_cases_path
  test_cases_path=$(jq -r '.verify_params.test_cases_path // empty' <<< "$sentinel")
  
  if [[ -z "$test_cases_path" ]]; then
    echo "Sentinel file missing 'verify_params.test_cases_path'" >&2
    exit 2
  fi
  
  # Run verifications
  verify_structure "$test_cases_path"
  verify_test_cases_completeness "$test_cases_path"
  
  # Delete sentinel file after verification
  rm -f "$sentinel_path"

  # Exit if any failures
  exit_if_failed
  
  echo -e "${GREEN}Verification passed${NC}" >&2
}

main "$@"
