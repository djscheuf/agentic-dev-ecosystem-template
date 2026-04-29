#!/usr/bin/env bash
# verify.sh - Verify design grade
# Validates that design meets quality threshold and reports low-scoring dimensions

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
  local required_dims=("design_reasoning" "workflow_changes" "interface_contracts" "layer_responsibilities" "instrumentation")
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
  
  local dims=("design_reasoning" "workflow_changes" "interface_contracts" "layer_responsibilities" "instrumentation")
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
  
  # Dimension weights (must sum to 1.0)
  local weight_design_reasoning=0.25
  local weight_layer_responsibilities=0.25
  local weight_workflow_changes=0.20
  local weight_interface_contracts=0.20
  local weight_instrumentation=0.10
  
  # Extract scores
  local dr_score=$(jq '.design_reasoning.score' <<< "$grade")
  local wc_score=$(jq '.workflow_changes.score' <<< "$grade")
  local ic_score=$(jq '.interface_contracts.score' <<< "$grade")
  local lr_score=$(jq '.layer_responsibilities.score' <<< "$grade")
  local inst_score=$(jq '.instrumentation.score' <<< "$grade")
  
  # Calculate weighted score
  # Weighted Score = (DR × 0.25) + (LR × 0.25) + (WC × 0.20) + (IC × 0.20) + (Inst × 0.10)
  local weighted_score
  weighted_score=$(awk -v dr="$dr_score" -v lr="$lr_score" -v wc="$wc_score" -v ic="$ic_score" -v inst="$inst_score" \
    -v w_dr="$weight_design_reasoning" -v w_lr="$weight_layer_responsibilities" -v w_wc="$weight_workflow_changes" \
    -v w_ic="$weight_interface_contracts" -v w_inst="$weight_instrumentation" \
    'BEGIN { printf "%.2f", dr * w_dr + lr * w_lr + wc * w_wc + ic * w_ic + inst * w_inst }')
  
  # Normalize to 0-100 scale
  # Normalized Score = (Weighted Score / 3) × 100
  local normalized_score
  normalized_score=$(awk -v ws="$weighted_score" 'BEGIN { printf "%.2f", (ws / 3) * 100 }')
  
  echo "Overall Score: $normalized_score / 100"
  
  # Check if score is below 80
  if awk -v score="$normalized_score" 'BEGIN { exit !(score < 80) }'; then
    fail "Design score is below threshold: $normalized_score < 80"
  fi
}

# Report warnings for low-scoring dimensions
report_low_scores() {
  local grade_path="$1"
  local grade
  
  grade=$(jq '.' "$grade_path")
  
  local dims=("design_reasoning" "workflow_changes" "interface_contracts" "layer_responsibilities" "instrumentation")
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
  grade_path=$(jq -r '.verify_params.design_grade_path // empty' <<< "$sentinel")
  
  if [[ -z "$grade_path" ]]; then
    echo "Sentinel file missing 'verify_params.design_grade_path'" >&2
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
