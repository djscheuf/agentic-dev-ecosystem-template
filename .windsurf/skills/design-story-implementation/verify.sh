#!/usr/bin/env bash
# verify/verify.sh - Verify design JSON against design schema
# Validates that the design file identified in sentinel matches design.schema.json

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
    exit 2
  fi
}

# Verify design JSON structure against schema
verify_design_structure() {
  local design_path="$1"
  
  if [[ ! -f "$design_path" ]]; then
    fail "Design file not found: $design_path"
    return
  fi
  
  # Validate JSON is well-formed
  if ! jq empty "$design_path" 2>/dev/null; then
    fail "Design file is not valid JSON: $design_path"
    return
  fi
  
  local design
  design=$(jq '.' "$design_path")
  
  # Check required top-level properties
  local required_props=("story_path" "audit_path" "workflow_sequence" "layer_responsibilities" "contracts" "architectural_decisions" "questions_addressed")
  for prop in "${required_props[@]}"; do
    if ! jq -e ".$prop" <<< "$design" &>/dev/null; then
      fail "Design validation failed: Missing required property '$prop'"
    fi
  done
  
  # Validate story_path and audit_path are strings
  if jq -e '.story_path' <<< "$design" &>/dev/null; then
    if ! jq -e '.story_path | type == "string"' <<< "$design" &>/dev/null; then
      fail "Design validation failed: story_path must be a string"
    fi
  fi
  
  if jq -e '.audit_path' <<< "$design" &>/dev/null; then
    if ! jq -e '.audit_path | type == "string"' <<< "$design" &>/dev/null; then
      fail "Design validation failed: audit_path must be a string"
    fi
  fi
  
  # Validate workflow_sequence is an array
  if jq -e '.workflow_sequence' <<< "$design" &>/dev/null; then
    if ! jq -e '.workflow_sequence | type == "array"' <<< "$design" &>/dev/null; then
      fail "Design validation failed: workflow_sequence must be an array"
    else
      local seq_count
      seq_count=$(jq '.workflow_sequence | length' <<< "$design")
      for idx in $(seq 0 $((seq_count - 1))); do
        local step
        step=$(jq ".workflow_sequence[$idx]" <<< "$design")
        if ! jq -e '.step and .description and .layers_involved and .handshake_points' <<< "$step" &>/dev/null; then
          fail "Design validation failed: workflow_sequence[$idx] must have 'step', 'description', 'layers_involved', and 'handshake_points'"
        fi
        if ! jq -e '.step | type == "number"' <<< "$step" &>/dev/null; then
          fail "Design validation failed: workflow_sequence[$idx].step must be a number"
        fi
        if ! jq -e '.layers_involved | type == "array"' <<< "$step" &>/dev/null; then
          fail "Design validation failed: workflow_sequence[$idx].layers_involved must be an array"
        fi
        if ! jq -e '.handshake_points | type == "array"' <<< "$step" &>/dev/null; then
          fail "Design validation failed: workflow_sequence[$idx].handshake_points must be an array"
        fi
      done
    fi
  fi
  
  # Validate layer_responsibilities is an array
  if jq -e '.layer_responsibilities' <<< "$design" &>/dev/null; then
    if ! jq -e '.layer_responsibilities | type == "array"' <<< "$design" &>/dev/null; then
      fail "Design validation failed: layer_responsibilities must be an array"
    else
      local layer_count
      layer_count=$(jq '.layer_responsibilities | length' <<< "$design")
      for idx in $(seq 0 $((layer_count - 1))); do
        local layer
        layer=$(jq ".layer_responsibilities[$idx]" <<< "$design")
        if ! jq -e '.layer and .new_responsibilities' <<< "$layer" &>/dev/null; then
          fail "Design validation failed: layer_responsibilities[$idx] must have 'layer' and 'new_responsibilities'"
        fi
        if ! jq -e '.new_responsibilities | type == "array"' <<< "$layer" &>/dev/null; then
          fail "Design validation failed: layer_responsibilities[$idx].new_responsibilities must be an array"
        fi
      done
    fi
  fi
  
  # Validate contracts is an array
  if jq -e '.contracts' <<< "$design" &>/dev/null; then
    if ! jq -e '.contracts | type == "array"' <<< "$design" &>/dev/null; then
      fail "Design validation failed: contracts must be an array"
    else
      local contract_count
      contract_count=$(jq '.contracts | length' <<< "$design")
      for idx in $(seq 0 $((contract_count - 1))); do
        local contract
        contract=$(jq ".contracts[$idx]" <<< "$design")
        if ! jq -e '.contract_type and .name and .description and .changes' <<< "$contract" &>/dev/null; then
          fail "Design validation failed: contracts[$idx] must have 'contract_type', 'name', 'description', and 'changes'"
        fi
        if ! jq -e '.changes | type == "object"' <<< "$contract" &>/dev/null; then
          fail "Design validation failed: contracts[$idx].changes must be an object"
        fi
      done
    fi
  fi
  
  # Validate architectural_decisions is an array
  if jq -e '.architectural_decisions' <<< "$design" &>/dev/null; then
    if ! jq -e '.architectural_decisions | type == "array"' <<< "$design" &>/dev/null; then
      fail "Design validation failed: architectural_decisions must be an array"
    else
      local decision_count
      decision_count=$(jq '.architectural_decisions | length' <<< "$design")
      for idx in $(seq 0 $((decision_count - 1))); do
        local decision
        decision=$(jq ".architectural_decisions[$idx]" <<< "$design")
        if ! jq -e '.decision and .justification and .basis and .impact' <<< "$decision" &>/dev/null; then
          fail "Design validation failed: architectural_decisions[$idx] must have 'decision', 'justification', 'basis', and 'impact'"
        fi
      done
    fi
  fi
  
  # Validate questions_addressed is an array
  if jq -e '.questions_addressed' <<< "$design" &>/dev/null; then
    if ! jq -e '.questions_addressed | type == "array"' <<< "$design" &>/dev/null; then
      fail "Design validation failed: questions_addressed must be an array"
    else
      local question_count
      question_count=$(jq '.questions_addressed | length' <<< "$design")
      for idx in $(seq 0 $((question_count - 1))); do
        local question
        question=$(jq ".questions_addressed[$idx]" <<< "$design")
        if ! jq -e '.question and .answer and .justification and .basis' <<< "$question" &>/dev/null; then
          fail "Design validation failed: questions_addressed[$idx] must have 'question', 'answer', 'justification', and 'basis'"
        fi
      done
    fi
  fi
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
  
  # Extract design_path from sentinel
  local sentinel
  sentinel=$(jq '.' "$sentinel_path")
  local design_path
  design_path=$(jq -r '.verify_params.design_path // empty' <<< "$sentinel")
  
  if [[ -z "$design_path" ]]; then
    echo "Sentinel file missing 'verify_params.design_path'" >&2
    exit 2
  fi
  
  # Run verifications
  verify_design_structure "$design_path"
  
  # Delete sentinel file after verification
  rm -f "$sentinel_path"

  # Exit if any failures
  exit_if_failed
  
  echo -e "${GREEN}Verification passed${NC}" >&2
}

main "$@"
