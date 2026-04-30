#!/usr/bin/env bash
# verify.sh - Verify workstream plans against schema

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
    echo -e "${RED}Workstream verification failed:${NC}" >&2
    printf '%s\n' "${FAILURES[@]}" >&2
    exit 2
  fi
}

# Validate a single workstream against schema
verify_workstream() {
  local ws_path="$1"
  
  if [[ ! -f "$ws_path" ]]; then
    fail "Workstream file not found at $ws_path"
    return
  fi
  
  if ! jq empty "$ws_path" 2>/dev/null; then
    fail "Workstream file is not valid JSON: $ws_path"
    return
  fi
  
  local ws
  ws=$(jq '.' "$ws_path")
  
  # Check required top-level properties
  if ! jq -e '.source_story' <<< "$ws" &>/dev/null || [[ $(jq -r '.source_story' <<< "$ws") == "null" ]]; then
    fail "Workstream at $ws_path: Missing required field 'source_story'"
  else
    local source_story_path
    source_story_path=$(jq -r '.source_story' <<< "$ws")
    if [[ ! -f "$source_story_path" ]]; then
      fail "Workstream at $ws_path: source_story file does not exist: $source_story_path"
    fi
  fi
  
  if ! jq -e '.overall_design' <<< "$ws" &>/dev/null || [[ $(jq -r '.overall_design' <<< "$ws") == "null" ]]; then
    fail "Workstream at $ws_path: Missing required field 'overall_design'"
  else
    local design_path
    design_path=$(jq -r '.overall_design' <<< "$ws")
    if [[ ! -f "$design_path" ]]; then
      fail "Workstream at $ws_path: overall_design file does not exist: $design_path"
    fi
  fi
  
  if ! jq -e '.story' <<< "$ws" &>/dev/null; then
    fail "Workstream at $ws_path: Missing required field 'story'"
    return
  fi
  
  # Validate story object
  local story
  story=$(jq '.story' <<< "$ws")
  
  if ! jq -e '.so_that' <<< "$story" &>/dev/null || [[ $(jq -r '.so_that' <<< "$story") == "null" ]]; then
    fail "Workstream at $ws_path: story.so_that is required"
  fi
  
  if ! jq -e '.as_a' <<< "$story" &>/dev/null || [[ $(jq -r '.as_a' <<< "$story") == "null" ]]; then
    fail "Workstream at $ws_path: story.as_a is required"
  fi
  
  if ! jq -e '.i_want' <<< "$story" &>/dev/null || [[ $(jq -r '.i_want' <<< "$story") == "null" ]]; then
    fail "Workstream at $ws_path: story.i_want is required"
  fi
  
  # Validate related_acceptance_criteria
  if jq -e '.related_acceptance_criteria' <<< "$ws" &>/dev/null; then
    local criteria
    criteria=$(jq '.related_acceptance_criteria' <<< "$ws")
    
    if ! jq -e 'type == "array"' <<< "$criteria" &>/dev/null; then
      fail "Workstream at $ws_path: related_acceptance_criteria must be an array"
    else
      local criteria_count
      criteria_count=$(jq 'length' <<< "$criteria")
      for idx in $(seq 0 $((criteria_count - 1))); do
        local criterion
        criterion=$(jq ".[$idx]" <<< "$criteria")
        
        if ! jq -e '.criterion' <<< "$criterion" &>/dev/null || [[ $(jq -r '.criterion' <<< "$criterion") == "null" ]]; then
          fail "Workstream at $ws_path: related_acceptance_criteria[$idx] missing 'criterion' field"
        fi
        
        if ! jq -e '.status' <<< "$criterion" &>/dev/null || [[ $(jq -r '.status' <<< "$criterion") == "null" ]]; then
          fail "Workstream at $ws_path: related_acceptance_criteria[$idx] missing 'status' field"
        else
          local status
          status=$(jq -r '.status' <<< "$criterion")
          if ! [[ "$status" =~ ^(pending|in_progress|completed)$ ]]; then
            fail "Workstream at $ws_path: related_acceptance_criteria[$idx] has invalid status '$status'"
          fi
        fi
      done
    fi
  fi
  
  # Validate related_edge_cases
  if jq -e '.related_edge_cases' <<< "$ws" &>/dev/null; then
    local edge_cases
    edge_cases=$(jq '.related_edge_cases' <<< "$ws")
    
    if ! jq -e 'type == "array"' <<< "$edge_cases" &>/dev/null; then
      fail "Workstream at $ws_path: related_edge_cases must be an array"
    else
      local edge_count
      edge_count=$(jq 'length' <<< "$edge_cases")
      for idx in $(seq 0 $((edge_count - 1))); do
        local edge_case
        edge_case=$(jq ".[$idx]" <<< "$edge_cases")
        
        if ! jq -e '.criterion' <<< "$edge_case" &>/dev/null || [[ $(jq -r '.criterion' <<< "$edge_case") == "null" ]]; then
          fail "Workstream at $ws_path: related_edge_cases[$idx] missing 'criterion' field"
        fi
        
        if ! jq -e '.status' <<< "$edge_case" &>/dev/null || [[ $(jq -r '.status' <<< "$edge_case") == "null" ]]; then
          fail "Workstream at $ws_path: related_edge_cases[$idx] missing 'status' field"
        else
          local status
          status=$(jq -r '.status' <<< "$edge_case")
          if ! [[ "$status" =~ ^(pending|in_progress|completed)$ ]]; then
            fail "Workstream at $ws_path: related_edge_cases[$idx] has invalid status '$status'"
          fi
        fi
      done
    fi
  fi
  
  # Validate steps
  if jq -e '.steps' <<< "$ws" &>/dev/null; then
    local steps
    steps=$(jq '.steps' <<< "$ws")
    
    if ! jq -e 'type == "array"' <<< "$steps" &>/dev/null; then
      fail "Workstream at $ws_path: steps must be an array"
    else
      local steps_count
      steps_count=$(jq 'length' <<< "$steps")
      for idx in $(seq 0 $((steps_count - 1))); do
        local step
        step=$(jq ".[$idx]" <<< "$steps")
        
        if ! jq -e '.description' <<< "$step" &>/dev/null || [[ $(jq -r '.description' <<< "$step") == "null" ]]; then
          fail "Workstream at $ws_path: steps[$idx] missing 'description' field"
        fi
        
        if ! jq -e '.status' <<< "$step" &>/dev/null || [[ $(jq -r '.status' <<< "$step") == "null" ]]; then
          fail "Workstream at $ws_path: steps[$idx] missing 'status' field"
        else
          local status
          status=$(jq -r '.status' <<< "$step")
          if ! [[ "$status" =~ ^(pending|in_progress|completed)$ ]]; then
            fail "Workstream at $ws_path: steps[$idx] has invalid status '$status'"
          fi
        fi
      done
    fi
  fi
  
  # Validate relevant_context if present
  if jq -e '.relevant_context' <<< "$ws" &>/dev/null; then
    local context
    context=$(jq '.relevant_context' <<< "$ws")
    
    if jq -e '.documentation' <<< "$context" &>/dev/null; then
      if ! jq -e '.documentation | type == "array"' <<< "$context" &>/dev/null; then
        fail "Workstream at $ws_path: relevant_context.documentation must be an array"
      fi
    fi
    
    if jq -e '.code' <<< "$context" &>/dev/null; then
      if ! jq -e '.code | type == "array"' <<< "$context" &>/dev/null; then
        fail "Workstream at $ws_path: relevant_context.code must be an array"
      fi
    fi
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
  
  # Validate sentinel file structure
  if ! jq empty "$sentinel_path" 2>/dev/null; then
    echo "Sentinel file is not valid JSON: $sentinel_path" >&2
    exit 2
  fi
  
  local sentinel
  sentinel=$(jq '.' "$sentinel_path")
  
  local workstream_paths_array
  workstream_paths_array=$(jq '.workstream_paths' <<< "$sentinel")
  
  if [[ -z "$workstream_paths_array" ]] || [[ "$workstream_paths_array" == "null" ]]; then
    echo "Sentinel file missing 'workstream_paths' array" >&2
    exit 2
  fi
  
  echo -e "${YELLOW}Verifying workstream plans...${NC}" >&2
  
  # Verify each workstream from sentinel paths
  local ws_count
  ws_count=$(jq '.workstream_paths | length' <<< "$sentinel")
  
  for idx in $(seq 0 $((ws_count - 1))); do
    local ws_path
    ws_path=$(jq -r ".workstream_paths[$idx]" <<< "$sentinel")
    
    verify_workstream "$ws_path"
  done
  
  # Delete sentinel file after verification
  rm -f "$sentinel_path"

  # Exit if any failures
  exit_if_failed
  
  echo -e "${GREEN}Verification passed${NC}" >&2
}

main "$@"
