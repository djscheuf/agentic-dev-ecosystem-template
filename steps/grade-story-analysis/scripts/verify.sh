#!/usr/bin/env bash
# verify.sh - Verify grade-story-analysis step output against analysis-grade schema
# Interface: verify.sh <saga_state_dir> <enrichment_dict_path>

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STEP_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_DIR="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
SCHEMA_PATH="$STEP_DIR/schema/analysis-grade.schema.json"

RED='\033[0;31m'
YELLOW='\033[1;33m'
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
  local grade_path="$1"
  
  if [[ ! -f "$grade_path" ]]; then
    fail "Grade file not found: $grade_path"
    return
  fi
  
  if ! jq empty "$grade_path" 2>/dev/null; then
    fail "Grade file is not valid JSON: $grade_path"
    return
  fi
  
  local grade
  grade=$(jq '.' "$grade_path")
  
  local required_dims=("business_value" "scope" "acceptance_criteria" "story_format" "dependencies")
  for dim in "${required_dims[@]}"; do
    if ! jq -e ".$dim" <<< "$grade" &>/dev/null; then
      fail "Schema validation failed: Missing required dimension '$dim'"
    fi
  done
  
  for dim in "${required_dims[@]}"; do
    if jq -e ".$dim" <<< "$grade" &>/dev/null; then
      local dim_obj
      dim_obj=$(jq ".$dim" <<< "$grade")
      
      if ! jq -e '.score' <<< "$dim_obj" &>/dev/null; then
        fail "Dimension '$dim' missing required field 'score'"
      fi
      
      if ! jq -e '.reason' <<< "$dim_obj" &>/dev/null; then
        fail "Dimension '$dim' missing required field 'reason'"
      fi
      
      if ! jq -e '.recommendation' <<< "$dim_obj" &>/dev/null; then
        fail "Dimension '$dim' missing required field 'recommendation'"
      fi
    fi
  done
}

verify_score_validity() {
  local grade_path="$1"
  local grade
  
  grade=$(jq '.' "$grade_path")
  
  local dims=("business_value" "scope" "acceptance_criteria" "story_format" "dependencies")
  for dim in "${dims[@]}"; do
    local score
    score=$(jq ".$dim.score" <<< "$grade")
    
    if ! [[ "$score" =~ ^[0-3]$ ]]; then
      fail "Dimension '$dim' has invalid score '$score'. Must be 0-3."
    fi
  done
}

calculate_and_verify_score() {
  local grade_path="$1"
  local grade
  
  grade=$(jq '.' "$grade_path")
  
  local weight_business_value=0.25
  local weight_scope=0.20
  local weight_acceptance_criteria=0.25
  local weight_story_format=0.15
  local weight_dependencies=0.10
  
  local bv_score=$(jq '.business_value.score' <<< "$grade")
  local scope_score=$(jq '.scope.score' <<< "$grade")
  local ac_score=$(jq '.acceptance_criteria.score' <<< "$grade")
  local sf_score=$(jq '.story_format.score' <<< "$grade")
  local dep_score=$(jq '.dependencies.score' <<< "$grade")
  
  local weighted_score
  weighted_score=$(awk -v bv="$bv_score" -v scope="$scope_score" -v ac="$ac_score" -v sf="$sf_score" -v dep="$dep_score" \
    -v w_bv="$weight_business_value" -v w_scope="$weight_scope" -v w_ac="$weight_acceptance_criteria" \
    -v w_sf="$weight_story_format" -v w_dep="$weight_dependencies" \
    'BEGIN { printf "%.2f", bv * w_bv + scope * w_scope + ac * w_ac + sf * w_sf + dep * w_dep }')
  
  local normalized_score
  normalized_score=$(awk -v ws="$weighted_score" 'BEGIN { printf "%.2f", (ws / 3) * 100 }')
  
  echo "[Verify] Overall Score: $normalized_score / 100" >&2
  
  if awk -v score="$normalized_score" 'BEGIN { exit !(score < 80) }'; then
    fail "Story analysis score is below threshold: $normalized_score < 80"
  fi
}

report_low_scores() {
  local grade_path="$1"
  local grade
  
  grade=$(jq '.' "$grade_path")
  
  local dims=("business_value" "scope" "acceptance_criteria" "story_format" "dependencies")
  local has_warnings=false
  
  for dim in "${dims[@]}"; do
    local score
    score=$(jq ".$dim.score" <<< "$grade")
    
    if [[ "$score" != "null" ]] && [[ $score -le 2 ]]; then
      if [[ "$has_warnings" == false ]]; then
        echo -e "${YELLOW}[Verify] Warnings:${NC}" >&2
        has_warnings=true
      fi
      
      local reason
      reason=$(jq -r ".$dim.reason" <<< "$grade")
      local recommendation
      recommendation=$(jq -r ".$dim.recommendation" <<< "$grade")
      
      echo -e "${YELLOW}  • $dim (score: $score)${NC}" >&2
      echo "    Reason: $reason" >&2
      echo "    Recommendation: $recommendation" >&2
    fi
  done
}

find_grade_file() {
  local working_dir="${1:-}"
  
  echo "[Verify] Searching for *.analysis-grade.json in uncommitted git changes..." >&2
  
  local grade_files=()
  while IFS= read -r file; do
    if [[ "$file" == *.analysis-grade.json ]]; then
      grade_files+=("$file")
    fi
  done < <(git diff --name-only HEAD 2>/dev/null; git ls-files --others --exclude-standard 2>/dev/null)
  
  if [[ ${#grade_files[@]} -eq 0 ]]; then
    echo "" >&2
    echo "ERROR: No *.analysis-grade.json files found in uncommitted git changes" >&2
    return 1
  fi
  
  if [[ ${#grade_files[@]} -gt 1 ]]; then
    echo "" >&2
    echo "ERROR: Multiple *.analysis-grade.json files found in uncommitted changes:" >&2
    for file in "${grade_files[@]}"; do
      echo "  - $file" >&2
    done
    echo "Please commit or remove all but one grade file" >&2
    return 1
  fi
  
  local grade_path="${grade_files[0]}"
  
  if [[ ! "$grade_path" = /* ]]; then
    grade_path="$PROJECT_DIR/$grade_path"
  fi
  
  if [[ ! -f "$grade_path" ]]; then
    echo "" >&2
    echo "ERROR: Grade file not found at path: $grade_path" >&2
    return 1
  fi
  
  echo "$grade_path"
  return 0
}

main() {
  local saga_state_dir="${1:-}"
  local enrichment_dict_path="${2:-}"
  
  local grade_path
  if ! grade_path=$(find_grade_file); then
    exit 2
  fi
  
  echo "[Verify] Found grade file: $grade_path" >&2
  
  verify_structure "$grade_path"
  verify_score_validity "$grade_path"
  
  report_low_scores "$grade_path"
  
  calculate_and_verify_score "$grade_path"
  
  exit_if_failed
  
  echo -e "${GREEN}[Verify] ✓ Verification passed${NC}" >&2
  
  local analysis_path
  analysis_path=$(jq -r '.analysis_file_path // empty' "$grade_path")
  
  if [[ -n "$analysis_path" ]]; then
    echo "$grade_path|$analysis_path"
  else
    echo "$grade_path"
  fi
}

main "$@"
