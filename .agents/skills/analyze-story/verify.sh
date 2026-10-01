#!/usr/bin/env bash
# verify.sh - Verify analyze-story skill output against analysis schema

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
  
  local required_props=("raw_request" "story" "target_persona" "capability_breakdown" "acceptance_criteria" "edge_cases" "questions" "dependencies")
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
    local persona_props=("role" "technical_level" "journey")
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
    local dep_props=("technical" "story" "knowledge")
    for prop in "${dep_props[@]}"; do
      if ! jq -e ".$prop" <<< "$dependencies" &>/dev/null; then
        fail "Schema validation failed: dependencies.$prop is required"
      fi
    done
    
    if jq -e '.story' <<< "$dependencies" &>/dev/null; then
      local story_deps
      story_deps=$(jq '.story' <<< "$dependencies")
      local story_dep_props=("blocked_by" "blocks" "related")
      for prop in "${story_dep_props[@]}"; do
        if ! jq -e ".$prop" <<< "$story_deps" &>/dev/null; then
          fail "Schema validation failed: dependencies.story.$prop is required"
        fi
      done
    fi
  fi
  
  if jq -e '.questions' <<< "$analysis" &>/dev/null; then
    if ! jq -e '.questions | type == "array"' <<< "$analysis" &>/dev/null; then
      fail "Schema validation failed: questions must be an array"
    fi
  fi
}

verify_completeness() {
  local analysis_path="$1"
  local analysis
  
  analysis=$(jq '.' "$analysis_path")
  
  local required_fields=("story" "target_persona" "capability_breakdown" "acceptance_criteria")
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
      
      if ! jq -e '.gherkin' <<< "$criterion" &>/dev/null || [[ $(jq -r '.gherkin' <<< "$criterion") == "null" ]]; then
        fail "Acceptance criterion $idx missing 'gherkin' field"
      fi
      
      if ! jq -e '.jtbd' <<< "$criterion" &>/dev/null || [[ $(jq -r '.jtbd' <<< "$criterion") == "null" ]]; then
        fail "Acceptance criterion $idx missing 'jtbd' field"
      fi
      
      if ! jq -e '.persona_served' <<< "$criterion" &>/dev/null || [[ $(jq -r '.persona_served' <<< "$criterion") == "null" ]]; then
        fail "Acceptance criterion $idx missing 'persona_served' field"
      fi
    done
  fi
  
  if jq -e '.edge_cases' <<< "$analysis" &>/dev/null; then
    local edge_cases
    edge_cases=$(jq '.edge_cases' <<< "$analysis")
    
    if ! jq -e 'type == "array"' <<< "$edge_cases" &>/dev/null; then
      fail "Edge cases must be an array"
      return
    fi
    
    local edge_count
    edge_count=$(jq 'length' <<< "$edge_cases")
    
    for idx in $(seq 0 $((edge_count - 1))); do
      local edge_case
      edge_case=$(jq ".[$idx]" <<< "$edge_cases")
      
      if ! jq -e '.criterion' <<< "$edge_case" &>/dev/null || [[ $(jq -r '.criterion' <<< "$edge_case") == "null" ]]; then
        fail "Edge case $idx missing 'criterion' field"
      fi
      
      if ! jq -e '.gherkin' <<< "$edge_case" &>/dev/null || [[ $(jq -r '.gherkin' <<< "$edge_case") == "null" ]]; then
        fail "Edge case $idx missing 'gherkin' field"
      fi
      
      if ! jq -e '.type' <<< "$edge_case" &>/dev/null || [[ $(jq -r '.type' <<< "$edge_case") == "null" ]]; then
        fail "Edge case $idx missing 'type' field"
      fi
      
      if ! jq -e '.jtbd' <<< "$edge_case" &>/dev/null || [[ $(jq -r '.jtbd' <<< "$edge_case") == "null" ]]; then
        fail "Edge case $idx missing 'jtbd' field"
      fi
      
      if ! jq -e '.persona_served' <<< "$edge_case" &>/dev/null || [[ $(jq -r '.persona_served' <<< "$edge_case") == "null" ]]; then
        fail "Edge case $idx missing 'persona_served' field"
      fi
    done
  fi
}

verify_consistency() {
  local analysis_path="$1"
  local analysis
  
  analysis=$(jq '.' "$analysis_path")
  
  if jq -e '.acceptance_criteria and .target_persona' <<< "$analysis" &>/dev/null; then
    local persona_role
    persona_role=$(jq -r '.target_persona.role' <<< "$analysis")
    local criteria_list
    criteria_list=$(jq '.acceptance_criteria' <<< "$analysis")
    
    local target_persona_served=false
    local criteria_count
    criteria_count=$(jq 'length' <<< "$criteria_list")
    
    for idx in $(seq 0 $((criteria_count - 1))); do
      local persona_served
      persona_served=$(jq -r ".[$idx].persona_served // empty" <<< "$criteria_list")
      if [[ -n "$persona_served" ]]; then
        target_persona_served=true
        break
      fi
    done
    
    if [[ "$target_persona_served" == false ]]; then
      fail "At least one acceptance criterion must have persona_served field populated."
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
  
  # Extract story path from sentinel
  local sentinel
  sentinel=$(jq '.' "$sentinel_path")
  local analysis_path
  analysis_path=$(jq -r '.verify_params.analysis_path // empty' <<< "$sentinel")
  
  verify_structure "$analysis_path"
  verify_completeness "$analysis_path"
  verify_consistency "$analysis_path"
  
  exit_if_failed
  
  echo -e "${GREEN}Analysis verification passed${NC}" >&2
}

main "$@"
