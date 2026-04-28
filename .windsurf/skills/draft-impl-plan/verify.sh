#!/usr/bin/env bash
# verify.sh - Verify implementation plan against schema

set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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
    echo -e "${RED}Implementation plan verification failed:${NC}" >&2
    printf '%s\n' "${FAILURES[@]}" >&2
    exit 2
  fi
}

# Verify impl plan JSON structure against schema
verify_structure() {
  local plan_path="$1"
  
  if [[ ! -f "$plan_path" ]]; then
    fail "Implementation plan file not found: $plan_path"
    return
  fi
  
  # Validate JSON is well-formed
  if ! jq empty "$plan_path" 2>/dev/null; then
    fail "Implementation plan file is not valid JSON: $plan_path"
    return
  fi
  
  local plan
  plan=$(jq '.' "$plan_path")
  
  # Check required top-level properties from schema
  local required_props=("source_story" "story" "acceptance_criteria" "edge_cases" "steps" "testing_strategy" "risks_and_mitigations")
  for prop in "${required_props[@]}"; do
    if ! jq -e ".$prop" <<< "$plan" &>/dev/null; then
      fail "Schema validation failed: Missing required property '$prop'"
    fi
  done
  
  # Validate story object structure
  if jq -e '.story' <<< "$plan" &>/dev/null; then
    local story_obj
    story_obj=$(jq '.story' <<< "$plan")
    local story_props=("so_that" "as_a" "i_want")
    for prop in "${story_props[@]}"; do
      if ! jq -e ".$prop" <<< "$story_obj" &>/dev/null; then
        fail "Schema validation failed: story.$prop is required"
      fi
    done
  fi
  
  # Validate acceptance_criteria is array
  if jq -e '.acceptance_criteria' <<< "$plan" &>/dev/null; then
    if ! jq -e '.acceptance_criteria | type == "array"' <<< "$plan" &>/dev/null; then
      fail "Schema validation failed: acceptance_criteria must be an array"
    fi
  fi
  
  # Validate edge_cases is array
  if jq -e '.edge_cases' <<< "$plan" &>/dev/null; then
    if ! jq -e '.edge_cases | type == "array"' <<< "$plan" &>/dev/null; then
      fail "Schema validation failed: edge_cases must be an array"
    fi
  fi
  
  # Validate steps is array
  if jq -e '.steps' <<< "$plan" &>/dev/null; then
    if ! jq -e '.steps | type == "array"' <<< "$plan" &>/dev/null; then
      fail "Schema validation failed: steps must be an array"
    fi
  fi
  
  # Validate testing_strategy structure
  if jq -e '.testing_strategy' <<< "$plan" &>/dev/null; then
    local testing
    testing=$(jq '.testing_strategy' <<< "$plan")
    local testing_props=("unit_tests" "integration_tests" "e2e_tests")
    for prop in "${testing_props[@]}"; do
      if ! jq -e ".$prop" <<< "$testing" &>/dev/null; then
        fail "Schema validation failed: testing_strategy.$prop is required"
      fi
    done
  fi
  
  # Validate risks_and_mitigations is array
  if jq -e '.risks_and_mitigations' <<< "$plan" &>/dev/null; then
    if ! jq -e '.risks_and_mitigations | type == "array"' <<< "$plan" &>/dev/null; then
      fail "Schema validation failed: risks_and_mitigations must be an array"
    fi
  fi
}

# Verify required fields and nested structure
verify_plan_completeness() {
  local plan_path="$1"
  local plan
  
  plan=$(jq '.' "$plan_path")
  
  # Check top-level required fields
  local required_fields=("source_story" "story" "acceptance_criteria" "edge_cases" "steps" "testing_strategy" "risks_and_mitigations")
  for field in "${required_fields[@]}"; do
    if ! jq -e ".$field" <<< "$plan" &>/dev/null || [[ $(jq -r ".$field" <<< "$plan") == "null" ]]; then
      fail "Missing required field: '$field'"
    fi
  done
  
  # Check story object fields
  if jq -e '.story' <<< "$plan" &>/dev/null; then
    local story_obj
    story_obj=$(jq '.story' <<< "$plan")
    local story_fields=("as_a" "i_want" "so_that")
    for field in "${story_fields[@]}"; do
      if ! jq -e ".$field" <<< "$story_obj" &>/dev/null || [[ $(jq -r ".$field" <<< "$story_obj") == "null" ]]; then
        fail "Story missing required field: '$field'"
      fi
    done
  fi
  
  # Check acceptance_criteria
  if jq -e '.acceptance_criteria' <<< "$plan" &>/dev/null; then
    local criteria_list
    criteria_list=$(jq '.acceptance_criteria' <<< "$plan")
    
    # Check if it's an array
    if ! jq -e 'type == "array"' <<< "$criteria_list" &>/dev/null; then
      fail "Acceptance criteria must be an array"
      return
    fi
    
    # Check if array is non-empty
    local criteria_count
    criteria_count=$(jq 'length' <<< "$criteria_list")
    if [[ $criteria_count -eq 0 ]]; then
      fail "Acceptance criteria must be a non-empty list"
      return
    fi
    
    # Check each criterion
    for idx in $(seq 0 $((criteria_count - 1))); do
      local criterion
      criterion=$(jq ".[$idx]" <<< "$criteria_list")
      
      if ! jq -e '.criterion' <<< "$criterion" &>/dev/null || [[ $(jq -r '.criterion' <<< "$criterion") == "null" ]]; then
        fail "Acceptance criterion $idx missing 'criterion' field"
      fi
      
      if ! jq -e '.status' <<< "$criterion" &>/dev/null || [[ $(jq -r '.status' <<< "$criterion") == "null" ]]; then
        fail "Acceptance criterion $idx missing 'status' field"
      else
        local status
        status=$(jq -r '.status' <<< "$criterion")
        if ! [[ "$status" =~ ^(pending|in_progress|completed)$ ]]; then
          fail "Acceptance criterion $idx has invalid status '$status'. Must be one of: pending, in_progress, completed"
        fi
      fi
    done
  fi
  
  # Check edge_cases
  if jq -e '.edge_cases' <<< "$plan" &>/dev/null; then
    local edge_list
    edge_list=$(jq '.edge_cases' <<< "$plan")
    
    # Check if it's an array
    if ! jq -e 'type == "array"' <<< "$edge_list" &>/dev/null; then
      fail "Edge cases must be an array"
      return
    fi
    
    # Check each edge case
    local edge_count
    edge_count=$(jq 'length' <<< "$edge_list")
    for idx in $(seq 0 $((edge_count - 1))); do
      local edge_case
      edge_case=$(jq ".[$idx]" <<< "$edge_list")
      
      if ! jq -e '.criterion' <<< "$edge_case" &>/dev/null || [[ $(jq -r '.criterion' <<< "$edge_case") == "null" ]]; then
        fail "Edge case $idx missing 'criterion' field"
      fi
      
      if ! jq -e '.status' <<< "$edge_case" &>/dev/null || [[ $(jq -r '.status' <<< "$edge_case") == "null" ]]; then
        fail "Edge case $idx missing 'status' field"
      else
        local status
        status=$(jq -r '.status' <<< "$edge_case")
        if ! [[ "$status" =~ ^(pending|in_progress|completed)$ ]]; then
          fail "Edge case $idx has invalid status '$status'. Must be one of: pending, in_progress, completed"
        fi
      fi
    done
  fi
  
  # Check steps
  if jq -e '.steps' <<< "$plan" &>/dev/null; then
    local steps_list
    steps_list=$(jq '.steps' <<< "$plan")
    
    # Check if it's an array
    if ! jq -e 'type == "array"' <<< "$steps_list" &>/dev/null; then
      fail "Steps must be an array"
      return
    fi
    
    # Check if array is non-empty
    local steps_count
    steps_count=$(jq 'length' <<< "$steps_list")
    if [[ $steps_count -eq 0 ]]; then
      fail "Steps must be a non-empty list"
      return
    fi
    
    # Check each step
    for idx in $(seq 0 $((steps_count - 1))); do
      local step
      step=$(jq ".[$idx]" <<< "$steps_list")
      
      if ! jq -e '.description' <<< "$step" &>/dev/null || [[ $(jq -r '.description' <<< "$step") == "null" ]]; then
        fail "Step $idx missing 'description' field"
      fi
      
      if ! jq -e '.status' <<< "$step" &>/dev/null || [[ $(jq -r '.status' <<< "$step") == "null" ]]; then
        fail "Step $idx missing 'status' field"
      else
        local status
        status=$(jq -r '.status' <<< "$step")
        if ! [[ "$status" =~ ^(pending|in_progress|completed)$ ]]; then
          fail "Step $idx has invalid status '$status'. Must be one of: pending, in_progress, completed"
        fi
      fi
    done
  fi
  
  # Check testing_strategy
  if jq -e '.testing_strategy' <<< "$plan" &>/dev/null; then
    local testing
    testing=$(jq '.testing_strategy' <<< "$plan")
    
    # Check unit_tests is array
    if jq -e '.unit_tests' <<< "$testing" &>/dev/null; then
      if ! jq -e '.unit_tests | type == "array"' <<< "$testing" &>/dev/null; then
        fail "testing_strategy.unit_tests must be an array"
      fi
    fi
    
    # Check integration_tests is array
    if jq -e '.integration_tests' <<< "$testing" &>/dev/null; then
      if ! jq -e '.integration_tests | type == "array"' <<< "$testing" &>/dev/null; then
        fail "testing_strategy.integration_tests must be an array"
      fi
    fi
    
    # Check e2e_tests is array
    if jq -e '.e2e_tests' <<< "$testing" &>/dev/null; then
      if ! jq -e '.e2e_tests | type == "array"' <<< "$testing" &>/dev/null; then
        fail "testing_strategy.e2e_tests must be an array"
      fi
    fi
  fi
  
  # Check risks_and_mitigations
  if jq -e '.risks_and_mitigations' <<< "$plan" &>/dev/null; then
    local risks_list
    risks_list=$(jq '.risks_and_mitigations' <<< "$plan")
    
    # Check if it's an array
    if ! jq -e 'type == "array"' <<< "$risks_list" &>/dev/null; then
      fail "Risks and mitigations must be an array"
      return
    fi
    
    # Check each risk
    local risks_count
    risks_count=$(jq 'length' <<< "$risks_list")
    for idx in $(seq 0 $((risks_count - 1))); do
      local risk
      risk=$(jq ".[$idx]" <<< "$risks_list")
      
      if ! jq -e '.risk' <<< "$risk" &>/dev/null || [[ $(jq -r '.risk' <<< "$risk") == "null" ]]; then
        fail "Risk $idx missing 'risk' field"
      fi
      
      if ! jq -e '.mitigation' <<< "$risk" &>/dev/null || [[ $(jq -r '.mitigation' <<< "$risk") == "null" ]]; then
        fail "Risk $idx missing 'mitigation' field"
      fi
    done
  fi
}

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
  
  local plan_path
  plan_path=$(jq -r '.verify_params.impl_plan_path // empty' "$sentinel_path")
  
  if [[ -z "$plan_path" ]]; then
    echo "Sentinel file missing 'verify_params.impl_plan_path'" >&2
    exit 2
  fi
  
  echo -e "${YELLOW}Verifying implementation plan...${NC}" >&2
  
  # Run verifications
  verify_structure "$plan_path"
  verify_plan_completeness "$plan_path"
  
  # Delete sentinel file after verification
  rm -f "$sentinel_path"

  # Exit if any failures
  exit_if_failed
  
  
  echo -e "${GREEN}Verification passed${NC}" >&2
}

main "$@"
