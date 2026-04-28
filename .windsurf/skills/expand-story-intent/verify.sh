#!/usr/bin/env bash
# verify.sh - Verify expand-story-intent skill output against analysis schema

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCHEMA_PATH="$SCRIPT_DIR/schema/analysis.schema.json"

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

FAILURES=()

fail() {
  FAILURES+=("$1")
}

exit_if_failed() {
  if [[ ${#FAILURES[@]} -gt 0 ]]; then
    echo -e "${RED}Analysis verification failed:${NC}" >&2
    printf '%s\n' "${FAILURES[@]}" >&2
    exit 2
  fi
}

verify_structure() {
  local analysis_path="$1"
  
  if [[ ! -f "$analysis_path" ]]; then
    fail "Analysis file not found: $analysis_path"
    return
  fi
  
  if ! jq empty "$analysis_path" 2>/dev/null; then
    fail "Analysis file is not valid JSON: $analysis_path"
    return
  fi
  
  if [[ ! -f "$SCHEMA_PATH" ]]; then
    fail "Schema file not found: $SCHEMA_PATH"
    return
  fi
  
  local analysis
  analysis=$(jq '.' "$analysis_path")
  
  local required_props=("raw_request" "title" "story" "target_persona" "capability_breakdown" "acceptance_criteria" "edge_cases" "dependencies" "complexity" "open_questions" "recommendation")
  for prop in "${required_props[@]}"; do
    if ! jq -e ".$prop" <<< "$analysis" &>/dev/null; then
      fail "Schema validation failed: Missing required property '$prop'"
    fi
  done
  
  if jq -e '.story' <<< "$analysis" &>/dev/null; then
    local story_obj
    story_obj=$(jq '.story' <<< "$analysis")
    local story_props=("so_that" "as_a" "i_want")
    for prop in "${story_props[@]}"; do
      if ! jq -e ".$prop" <<< "$story_obj" &>/dev/null; then
        fail "Schema validation failed: story.$prop is required"
      fi
    done
  fi
  
  if jq -e '.target_persona' <<< "$analysis" &>/dev/null; then
    local persona
    persona=$(jq '.target_persona' <<< "$analysis")
    local persona_props=("name" "role" "technical_level" "journey")
    for prop in "${persona_props[@]}"; do
      if ! jq -e ".$prop" <<< "$persona" &>/dev/null; then
        fail "Schema validation failed: target_persona.$prop is required"
      fi
    done
    
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
  
  if jq -e '.capability_breakdown' <<< "$analysis" &>/dev/null; then
    local capability
    capability=$(jq '.capability_breakdown' <<< "$analysis")
    local capability_props=("core_action" "inputs" "outputs" "state_changes" "affected_components")
    for prop in "${capability_props[@]}"; do
      if ! jq -e ".$prop" <<< "$capability" &>/dev/null; then
        fail "Schema validation failed: capability_breakdown.$prop is required"
      fi
    done
    
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
  
  if jq -e '.acceptance_criteria' <<< "$analysis" &>/dev/null; then
    if ! jq -e '.acceptance_criteria | type == "array"' <<< "$analysis" &>/dev/null; then
      fail "Schema validation failed: acceptance_criteria must be an array"
    fi
  fi
  
  if jq -e '.dependencies' <<< "$analysis" &>/dev/null; then
    local dependencies
    dependencies=$(jq '.dependencies' <<< "$analysis")
    local dep_props=("blocked_by" "blocks" "technical")
    for prop in "${dep_props[@]}"; do
      if ! jq -e ".$prop" <<< "$dependencies" &>/dev/null; then
        fail "Schema validation failed: dependencies.$prop is required"
      fi
    done
  fi
  
  if jq -e '.complexity' <<< "$analysis" &>/dev/null; then
    local complexity
    complexity=$(jq '.complexity' <<< "$analysis")
    local complexity_props=("story_points" "risk_level" "uncertainty")
    for prop in "${complexity_props[@]}"; do
      if ! jq -e ".$prop" <<< "$complexity" &>/dev/null; then
        fail "Schema validation failed: complexity.$prop is required"
      fi
    done
  fi
}

verify_completeness() {
  local analysis_path="$1"
  local analysis
  
  analysis=$(jq '.' "$analysis_path")
  
  local required_fields=("title" "story" "target_persona" "capability_breakdown" "acceptance_criteria")
  for field in "${required_fields[@]}"; do
    if ! jq -e ".$field" <<< "$analysis" &>/dev/null || [[ $(jq -r ".$field" <<< "$analysis") == "null" ]]; then
      fail "Missing required field: '$field'"
    fi
  done
  
  if jq -e '.story' <<< "$analysis" &>/dev/null; then
    local story_obj
    story_obj=$(jq '.story' <<< "$analysis")
    local story_fields=("as_a" "i_want" "so_that")
    for field in "${story_fields[@]}"; do
      if ! jq -e ".$field" <<< "$story_obj" &>/dev/null || [[ $(jq -r ".$field" <<< "$story_obj") == "null" ]]; then
        fail "Story missing required field: '$field'"
      fi
    done
  fi
  
  if jq -e '.target_persona' <<< "$analysis" &>/dev/null; then
    local persona
    persona=$(jq '.target_persona' <<< "$analysis")
    if ! jq -e '.name' <<< "$persona" &>/dev/null || [[ $(jq -r '.name' <<< "$persona") == "null" ]]; then
      fail "Target persona missing 'name'"
    fi
    if ! jq -e '.role' <<< "$persona" &>/dev/null || [[ $(jq -r '.role' <<< "$persona") == "null" ]]; then
      fail "Target persona missing 'role'"
    fi
  fi
  
  if jq -e '.acceptance_criteria' <<< "$analysis" &>/dev/null; then
    local criteria_list
    criteria_list=$(jq '.acceptance_criteria' <<< "$analysis")
    
    if ! jq -e 'type == "array"' <<< "$criteria_list" &>/dev/null; then
      fail "Acceptance criteria must be an array"
      return
    fi
    
    local criteria_count
    criteria_count=$(jq 'length' <<< "$criteria_list")
    if [[ $criteria_count -eq 0 ]]; then
      fail "Acceptance criteria must be a non-empty list"
      return
    fi
    
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

verify_consistency() {
  local analysis_path="$1"
  local analysis
  
  analysis=$(jq '.' "$analysis_path")
  
  if jq -e '.acceptance_criteria and .target_persona' <<< "$analysis" &>/dev/null; then
    local persona_name
    persona_name=$(jq -r '.target_persona.name' <<< "$analysis")
    local criteria_list
    criteria_list=$(jq '.acceptance_criteria' <<< "$analysis")
    
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
  
  if jq -e '.complexity' <<< "$analysis" &>/dev/null; then
    local complexity
    complexity=$(jq '.complexity' <<< "$analysis")
    
    if jq -e '.risk_level' <<< "$complexity" &>/dev/null; then
      local risk
      risk=$(jq -r '.risk_level' <<< "$complexity")
      if ! [[ "$risk" =~ ^(Low|Medium|High)$ ]]; then
        fail "Risk level '$risk' is invalid. Must be one of: Low, Medium, High"
      fi
    fi
    
    if jq -e '.story_points' <<< "$complexity" &>/dev/null; then
      local points
      points=$(jq '.story_points' <<< "$complexity")
      
      if ! jq -e 'type == "number" and . > 0' <<< "$points" &>/dev/null; then
        fail "Story points must be a positive number, got: $points"
      else
        if ! [[ "$points" =~ ^(1|2|3|5|8|13|21)$ ]]; then
          fail "Story points '$points' is not a valid Fibonacci value. Accepted values: 1, 2, 3, 5, 8, 13, 21"
        fi
      fi
    fi
  fi
}

main() {
  local analysis_path="$1"
  
  if [[ -z "$analysis_path" ]]; then
    echo "Usage: verify.sh <analysis_file>" >&2
    exit 2
  fi
  
  verify_structure "$analysis_path"
  verify_completeness "$analysis_path"
  verify_consistency "$analysis_path"
  
  exit_if_failed
  
  echo -e "${GREEN}Analysis verification passed${NC}" >&2
}

main "$@"
