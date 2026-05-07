#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STEP_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_DIR="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

FAILURES=()

fail() {
  FAILURES+=("$1")
}

exit_if_failed() {
  if [[ ${#FAILURES[@]} -gt 0 ]]; then
    echo -e "${RED}Verification failed:${NC}" >&2
    printf '%s\n' "${FAILURES[@]}" >&2
    exit 2
  fi
}

verify_structure() {
  local story_path="$1"
  local schema_path="$STEP_DIR/schema/story-intent.schema.json"
  
  if [[ ! -f "$story_path" ]]; then
    fail "Story file not found: $story_path"
    return
  fi
  
  if ! jq empty "$story_path" 2>/dev/null; then
    fail "Story file is not valid JSON: $story_path"
    return
  fi
  
  if [[ ! -f "$schema_path" ]]; then
    fail "Schema file not found: $schema_path"
    return
  fi
  
  local story
  story=$(jq '.' "$story_path")
  
  local required_props=("raw_request" "title" "story" "target_persona" "capability_breakdown" "acceptance_criteria")
  for prop in "${required_props[@]}"; do
    if ! jq -e ".$prop" <<< "$story" &>/dev/null; then
      fail "Schema validation failed: Missing required property '$prop'"
    fi
  done
  
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
  
  if jq -e '.target_persona' <<< "$story" &>/dev/null; then
    local persona
    persona=$(jq '.target_persona' <<< "$story")
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
  
  if jq -e '.capability_breakdown' <<< "$story" &>/dev/null; then
    local capability
    capability=$(jq '.capability_breakdown' <<< "$story")
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
  
  if jq -e '.acceptance_criteria' <<< "$story" &>/dev/null; then
    if ! jq -e '.acceptance_criteria | type == "array"' <<< "$story" &>/dev/null; then
      fail "Schema validation failed: acceptance_criteria must be an array"
    fi
  fi
}

verify_story_completeness() {
  local story_path="$1"
  local story
  
  story=$(jq '.' "$story_path")
  
  local required_fields=("title" "story" "target_persona" "capability_breakdown" "acceptance_criteria")
  for field in "${required_fields[@]}"; do
    if ! jq -e ".$field" <<< "$story" &>/dev/null || [[ $(jq -r ".$field" <<< "$story") == "null" ]]; then
      fail "Missing required field: '$field'"
    fi
  done
  
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
  
  if jq -e '.acceptance_criteria' <<< "$story" &>/dev/null; then
    local criteria_list
    criteria_list=$(jq '.acceptance_criteria' <<< "$story")
    
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
  local story_path="$1"
  local story
  
  story=$(jq '.' "$story_path")
  
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
}

find_intent_file() {
  local search_dir="${1:-$PROJECT_DIR}"
  
  local intent_files
  intent_files=$(find "$search_dir" -name "*.intent.json" -type f 2>/dev/null | head -n 1)
  
  if [[ -z "$intent_files" ]]; then
    echo "" >&2
    echo "ERROR: No *.intent.json file found in $search_dir" >&2
    echo "The step should have created a file matching *.intent.json" >&2
    return 1
  fi
  
  echo "$intent_files"
}

main() {
  echo "[Verify] Searching for generated intent file..."
  
  local story_path
  if ! story_path=$(find_intent_file); then
    exit 2
  fi
  
  echo "[Verify] Found intent file: $story_path"
  
  verify_structure "$story_path"
  verify_story_completeness "$story_path"
  verify_consistency "$story_path"
  
  exit_if_failed
  
  echo -e "${GREEN}[Verify] ✓ Verification passed${NC}"
}

main "$@"
