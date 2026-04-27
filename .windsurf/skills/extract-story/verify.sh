#!/usr/bin/env bash
# verify/verify.sh - Verify extracted user story JSON
# Replaces verify.py with pure shell + jq

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
    exit 1
  fi
}

# Verify story JSON structure against schema
verify_structure() {
  local story_path="$1"
  local schema_path="$SCRIPT_DIR/schema/user-story.schema.json"
  
  if [[ ! -f "$story_path" ]]; then
    fail "Story file not found: $story_path"
    return
  fi
  
  # Validate JSON is well-formed
  if ! jq empty "$story_path" 2>/dev/null; then
    fail "Story file is not valid JSON: $story_path"
    return
  fi
  
  # Validate against schema structure
  if [[ ! -f "$schema_path" ]]; then
    fail "Schema file not found: $schema_path"
    return
  fi
  
  local story
  story=$(jq '.' "$story_path")
  
  # Check required top-level properties from schema
  local required_props=("raw_request" "title" "story" "target_persona" "capability_breakdown" "acceptance_criteria" "edge_cases" "dependencies" "complexity" "open_questions" "recommendation")
  for prop in "${required_props[@]}"; do
    if ! jq -e ".$prop" <<< "$story" &>/dev/null; then
      fail "Schema validation failed: Missing required property '$prop'"
    fi
  done
  
  # Validate story object structure
  if jq -e '.story' <<< "$story" &>/dev/null; then
    local story_obj
    story_obj=$(jq '.story' <<< "$story")
    local story_props=("so_that" "as_a" "i_want")
    for prop in "${story_props[@]}"; do
      if ! jq -e ".$prop" <<< "$story_obj" &>/dev/null; then
        fail "Schema validation failed: story.$prop is required"
      fi
    done
  fi
  
  # Validate target_persona structure
  if jq -e '.target_persona' <<< "$story" &>/dev/null; then
    local persona
    persona=$(jq '.target_persona' <<< "$story")
    local persona_props=("name" "role" "technical_level" "journey")
    for prop in "${persona_props[@]}"; do
      if ! jq -e ".$prop" <<< "$persona" &>/dev/null; then
        fail "Schema validation failed: target_persona.$prop is required"
      fi
    done
    
    # Validate journey structure
    if jq -e '.journey' <<< "$persona" &>/dev/null; then
      local journey
      journey=$(jq '.journey' <<< "$persona")
      local journey_props=("before" "during" "after")
      for prop in "${journey_props[@]}"; do
        if ! jq -e ".$prop" <<< "$journey" &>/dev/null; then
          fail "Schema validation failed: target_persona.journey.$prop is required"
        fi
      done
    fi
  fi
  
  # Validate capability_breakdown structure
  if jq -e '.capability_breakdown' <<< "$story" &>/dev/null; then
    local capability
    capability=$(jq '.capability_breakdown' <<< "$story")
    local capability_props=("core_action" "inputs" "outputs" "state_changes" "affected_components")
    for prop in "${capability_props[@]}"; do
      if ! jq -e ".$prop" <<< "$capability" &>/dev/null; then
        fail "Schema validation failed: capability_breakdown.$prop is required"
      fi
    done
    
    # Validate affected_components structure
    if jq -e '.affected_components' <<< "$capability" &>/dev/null; then
      local affected
      affected=$(jq '.affected_components' <<< "$capability")
      local component_props=("ui" "api" "database" "external_services")
      for prop in "${component_props[@]}"; do
        if ! jq -e ".$prop" <<< "$affected" &>/dev/null; then
          fail "Schema validation failed: capability_breakdown.affected_components.$prop is required"
        fi
      done
    fi
  fi
  
  # Validate acceptance_criteria is array
  if jq -e '.acceptance_criteria' <<< "$story" &>/dev/null; then
    if ! jq -e '.acceptance_criteria | type == "array"' <<< "$story" &>/dev/null; then
      fail "Schema validation failed: acceptance_criteria must be an array"
    fi
  fi
  
  # Validate dependencies structure
  if jq -e '.dependencies' <<< "$story" &>/dev/null; then
    local dependencies
    dependencies=$(jq '.dependencies' <<< "$story")
    local dep_props=("blocked_by" "blocks" "technical")
    for prop in "${dep_props[@]}"; do
      if ! jq -e ".$prop" <<< "$dependencies" &>/dev/null; then
        fail "Schema validation failed: dependencies.$prop is required"
      fi
    done
  fi
  
  # Validate complexity structure
  if jq -e '.complexity' <<< "$story" &>/dev/null; then
    local complexity
    complexity=$(jq '.complexity' <<< "$story")
    local complexity_props=("story_points" "risk_level" "uncertainty")
    for prop in "${complexity_props[@]}"; do
      if ! jq -e ".$prop" <<< "$complexity" &>/dev/null; then
        fail "Schema validation failed: complexity.$prop is required"
      fi
    done
  fi
}

# Verify required fields and nested structure
verify_story_completeness() {
  local story_path="$1"
  local story
  
  story=$(jq '.' "$story_path")
  
  # Check top-level required fields
  local required_fields=("title" "story" "target_persona" "capability_breakdown" "acceptance_criteria")
  for field in "${required_fields[@]}"; do
    if ! jq -e ".$field" <<< "$story" &>/dev/null || [[ $(jq -r ".$field" <<< "$story") == "null" ]]; then
      fail "Missing required field: '$field'"
    fi
  done
  
  # Check story object fields
  if jq -e '.story' <<< "$story" &>/dev/null; then
    local story_obj
    story_obj=$(jq '.story' <<< "$story")
    local story_fields=("as_a" "i_want" "so_that")
    for field in "${story_fields[@]}"; do
      if ! jq -e ".$field" <<< "$story_obj" &>/dev/null || [[ $(jq -r ".$field" <<< "$story_obj") == "null" ]]; then
        fail "Story missing required field: '$field'"
      fi
    done
  fi
  
  # Check target_persona fields
  if jq -e '.target_persona' <<< "$story" &>/dev/null; then
    local persona
    persona=$(jq '.target_persona' <<< "$story")
    if ! jq -e '.name' <<< "$persona" &>/dev/null || [[ $(jq -r '.name' <<< "$persona") == "null" ]]; then
      fail "Target persona missing 'name'"
    fi
    if ! jq -e '.role' <<< "$persona" &>/dev/null || [[ $(jq -r '.role' <<< "$persona") == "null" ]]; then
      fail "Target persona missing 'role'"
    fi
  fi
  
  # Check acceptance_criteria
  if jq -e '.acceptance_criteria' <<< "$story" &>/dev/null; then
    local criteria_list
    criteria_list=$(jq '.acceptance_criteria' <<< "$story")
    
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
      
      if ! jq -e '.type' <<< "$criterion" &>/dev/null || [[ $(jq -r '.type' <<< "$criterion") == "null" ]]; then
        fail "Acceptance criterion $idx missing 'type' field"
      else
        local ctype
        ctype=$(jq -r '.type' <<< "$criterion")
        if ! [[ "$ctype" =~ ^(Functional|Non-functional|Happy\ path|Error\ handling|Edge\ Case)$ ]]; then
          fail "Acceptance criterion $idx has invalid type '$ctype'. Must be one of: Functional, Non-functional, Happy path, Error handling, Edge Case"
        fi
      fi
    done
  fi
}

# Verify consistency across fields
verify_consistency() {
  local story_path="$1"
  local story
  
  story=$(jq '.' "$story_path")
  
  # Check persona is served by at least one criterion
  if jq -e '.acceptance_criteria and .target_persona' <<< "$story" &>/dev/null; then
    local persona_name
    persona_name=$(jq -r '.target_persona.name' <<< "$story")
    local criteria_list
    criteria_list=$(jq '.acceptance_criteria' <<< "$story")
    
    local target_persona_served=false
    local criteria_count
    criteria_count=$(jq 'length' <<< "$criteria_list")
    
    for idx in $(seq 0 $((criteria_count - 1))); do
      local persona_served
      persona_served=$(jq -r ".[$idx].persona_served // empty" <<< "$criteria_list")
      if [[ "$persona_served" == "$persona_name" ]]; then
        target_persona_served=true
        break
      fi
    done
    
    if [[ "$target_persona_served" == false ]]; then
      fail "Target persona '$persona_name' is not served by any acceptance criterion. At least one criterion must have persona_served matching the target persona."
    fi
  fi
  
  # Check complexity fields if present
  if jq -e '.complexity' <<< "$story" &>/dev/null; then
    local complexity
    complexity=$(jq '.complexity' <<< "$story")
    
    # Check risk_level
    if jq -e '.risk_level' <<< "$complexity" &>/dev/null; then
      local risk
      risk=$(jq -r '.risk_level' <<< "$complexity")
      if ! [[ "$risk" =~ ^(Low|Medium|High)$ ]]; then
        fail "Risk level '$risk' is invalid. Must be one of: Low, Medium, High"
      fi
    fi
    
    # Check story_points
    if jq -e '.story_points' <<< "$complexity" &>/dev/null; then
      local points
      points=$(jq '.story_points' <<< "$complexity")
      
      # Check if it's a positive number
      if ! jq -e 'type == "number" and . > 0' <<< "$points" &>/dev/null; then
        fail "Story points must be a positive number, got: $points"
      else
        # Check if it's a valid Fibonacci number
        if ! [[ "$points" =~ ^(1|2|3|5|8|13|21)$ ]]; then
          fail "Story points '$points' is not a valid Fibonacci value. Accepted values: 1, 2, 3, 5, 8, 13, 21"
        fi
      fi
    fi
  fi
}

# Main execution
main() {
  local sentinel_path="$1"
  
  if [[ -z "$sentinel_path" ]]; then
    echo "Usage: verify.sh <sentinel_file>" >&2
    exit 1
  fi
  
  if [[ ! -f "$sentinel_path" ]]; then
    echo "Sentinel file not found: $sentinel_path" >&2
    exit 1
  fi
  
  # Extract story path from sentinel
  local sentinel
  sentinel=$(jq '.' "$sentinel_path")
  local story_path
  story_path=$(jq -r '.verify_params.extracted_story_path // empty' <<< "$sentinel")
  
  if [[ -z "$story_path" ]]; then
    echo "Sentinel file missing 'verify_params.extracted_story_path'" >&2
    exit 1
  fi
  
  # Run verifications
  verify_structure "$story_path"
  verify_story_completeness "$story_path"
  verify_consistency "$story_path"
  
  # Exit if any failures
  exit_if_failed
  
  # Delete sentinel file on success
  rm -f "$sentinel_path"
  
  echo -e "${GREEN}Verification passed${NC}" >&2
}

main "$@"
