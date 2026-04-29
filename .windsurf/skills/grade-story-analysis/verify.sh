#!/usr/bin/env bash
# verify.sh - Verify story analysis grade
# Validates that story meets quality threshold and reports low-scoring dimensions

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

# Color output
RED='\033[0;31m'
YELLOW='\033[1;33m'
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

# Verify grade file structure
verify_structure() {
  local grade_path="$1"
  
  if [[ ! -f "$grade_path" ]]; then
    fail "Grade file not found: $grade_path"
    return
  fi
  
  # Validate JSON is well-formed
  if ! jq empty "$grade_path" 2>/dev/null; then
    fail "Grade file is not valid JSON: $grade_path"
    return
  fi
  
  local grade
  grade=$(jq '.' "$grade_path")
  
  # Check required dimensions
  local required_dims=("business_value" "scope" "acceptance_criteria" "story_format" "dependencies")
  for dim in "${required_dims[@]}"; do
    if ! jq -e ".$dim" <<< "$grade" &>/dev/null; then
      fail "Schema validation failed: Missing required dimension '$dim'"
    fi
  done
  
  # Validate each dimension has required fields
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

# Verify score values are valid
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

# Calculate weighted score and check threshold
calculate_and_verify_score() {
  local grade_path="$1"
  local grade
  
  grade=$(jq '.' "$grade_path")
  
  # Extract scores
  local bv_score=$(jq '.business_value.score' <<< "$grade")
  local scope_score=$(jq '.scope.score' <<< "$grade")
  local ac_score=$(jq '.acceptance_criteria.score' <<< "$grade")
  local sf_score=$(jq '.story_format.score' <<< "$grade")
  local dep_score=$(jq '.dependencies.score' <<< "$grade")
  
  # Calculate weighted score
  # Weighted Score = (BV × 0.25) + (Scope × 0.20) + (AC × 0.25) + (SF × 0.15) + (Dep × 0.10)
  local weighted_score
  weighted_score=$(awk -v bv="$bv_score" -v scope="$scope_score" -v ac="$ac_score" -v sf="$sf_score" -v dep="$dep_score" \
    'BEGIN { printf "%.2f", bv * 0.25 + scope * 0.20 + ac * 0.25 + sf * 0.15 + dep * 0.10 }')
  
  # Normalize to 0-100 scale
  # Normalized Score = (Weighted Score / 3) × 100
  local normalized_score
  normalized_score=$(awk -v ws="$weighted_score" 'BEGIN { printf "%.2f", (ws / 3) * 100 }')
  
  echo "Overall Score: $normalized_score / 100"
  
  # Check if score is below 80
  if awk -v score="$normalized_score" 'BEGIN { exit !(score < 80) }'; then
    fail "Story analysis score is below threshold: $normalized_score < 80"
  fi
}

# Report warnings for low-scoring dimensions
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
        echo -e "${YELLOW}Warnings:${NC}" >&2
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
  
  # Extract grade path from sentinel
  local sentinel
  sentinel=$(jq '.' "$sentinel_path")
  local grade_path
  grade_path=$(jq -r '.verify_params.analysis_grade_path // empty' <<< "$sentinel")
  
  if [[ -z "$grade_path" ]]; then
    echo "Sentinel file missing 'verify_params.analysis_grade_path'" >&2
    exit 2
  fi
  
  # Run verifications
  verify_structure "$grade_path"
  verify_score_validity "$grade_path"
  
  # Report warnings before checking threshold
  report_low_scores "$grade_path"
  
  # Calculate score and check threshold
  calculate_and_verify_score "$grade_path"
  
  # Delete sentinel file after verification
  rm -f "$sentinel_path"
  
  # Exit if any failures
  exit_if_failed
  
  echo -e "${GREEN}Verification passed${NC}" >&2
}

main "$@"
