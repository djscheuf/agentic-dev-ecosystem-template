#!/usr/bin/env bash
# verify.sh - Verify analyze-story step output against analysis schema
# Interface: verify.sh <saga_state_dir> <enrichment_dict_path>

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STEP_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_DIR="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
SCHEMA_PATH="$STEP_DIR/schema/analysis.schema.json"

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
  local analysis_path="$1"
  
  if [[ ! -f "$analysis_path" ]]; then
    fail "Analysis file not found in $(dirname "$analysis_path")"
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
  
  # recommendation is optional
  if jq -e '.recommendation' <<< "$analysis" &>/dev/null; then
    local rec
    rec=$(jq -r '.recommendation' <<< "$analysis")
    if [[ -z "$rec" || "$rec" == "null" ]]; then
      fail "Schema validation failed: recommendation field is present but empty"
    fi
  fi
  
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
      fail "Target persona '$persona_name' is not served by any acceptance criterion"
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

find_analysis_file() {
  local working_dir="${1:-}"
  
  # Try to find *.analysis.json from uncommitted git changes
  echo "[Verify] Searching for *.analysis.json in uncommitted git changes..." >&2
  
  local analysis_files=()
  while IFS= read -r file; do
    if [[ "$file" == *.analysis.json ]]; then
      analysis_files+=("$file")
    fi
  done < <(git diff --name-only HEAD 2>/dev/null; git ls-files --others --exclude-standard 2>/dev/null)
  
  if [[ ${#analysis_files[@]} -eq 0 ]]; then
    echo "" >&2
    echo "ERROR: No *.analysis.json files found in uncommitted git changes" >&2
    return 1
  fi
  
  if [[ ${#analysis_files[@]} -gt 1 ]]; then
    echo "" >&2
    echo "ERROR: Multiple *.analysis.json files found in uncommitted changes:" >&2
    for file in "${analysis_files[@]}"; do
      echo "  - $file" >&2
    done
    echo "Please commit or remove all but one analysis file" >&2
    return 1
  fi
  
  local analysis_path="${analysis_files[0]}"
  
  # Convert to absolute path if relative
  if [[ ! "$analysis_path" = /* ]]; then
    analysis_path="$PROJECT_DIR/$analysis_path"
  fi
  
  if [[ ! -f "$analysis_path" ]]; then
    echo "" >&2
    echo "ERROR: Analysis file not found at path: $analysis_path" >&2
    return 1
  fi
  
  echo "$analysis_path"
  return 0
}

main() {
  local saga_state_dir="${1:-}"
  local enrichment_dict_path="${2:-}"
  
  local analysis_path
  if ! analysis_path=$(find_analysis_file); then
    exit 2
  fi
  
  echo "[Verify] Found analysis file: $analysis_path" >&2
  
  verify_structure "$analysis_path"
  verify_completeness "$analysis_path"
  verify_consistency "$analysis_path"
  
  exit_if_failed
  
  echo -e "${GREEN}[Verify] ✓ Verification passed${NC}" >&2
  echo "$analysis_path"
}

main "$@"
