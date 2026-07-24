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
    exit 2
  fi
}


# Verify audit JSON structure against schema
verify_audit_structure() {
  local audit_path="$1"
  
  if [[ ! -f "$audit_path" ]]; then
    fail "Audit file not found: $audit_path"
    return
  fi
  
  # Validate JSON is well-formed
  if ! jq empty "$audit_path" 2>/dev/null; then
    fail "Audit file is not valid JSON: $audit_path"
    return
  fi
  
  local audit
  audit=$(jq '.' "$audit_path")
  
  # Check required top-level properties
  local required_props=("run_date" "target_story" "vault_audit" "code_audit")
  for prop in "${required_props[@]}"; do
    if ! jq -e ".$prop" <<< "$audit" &>/dev/null; then
      fail "Audit validation failed: Missing required property '$prop'"
    fi
  done
  
  # Validate vault_audit structure
  if jq -e '.vault_audit' <<< "$audit" &>/dev/null; then
    local vault_audit
    vault_audit=$(jq '.vault_audit' <<< "$audit")
    local vault_props=("decisions" "persona" "target_architecture")
    for prop in "${vault_props[@]}"; do
      if ! jq -e ".$prop" <<< "$vault_audit" &>/dev/null; then
        fail "Audit validation failed: vault_audit.$prop is required"
      fi
    done
    
    # Validate vault_audit arrays have correct structure
    for array_prop in "decisions" "persona" "target_architecture"; do
      if jq -e ".$array_prop" <<< "$vault_audit" &>/dev/null; then
        local array_data
        array_data=$(jq ".$array_prop" <<< "$vault_audit")
        if ! jq -e 'type == "array"' <<< "$array_data" &>/dev/null; then
          fail "Audit validation failed: vault_audit.$array_prop must be an array"
        else
          local item_count
          item_count=$(jq 'length' <<< "$array_data")
          for idx in $(seq 0 $((item_count - 1))); do
            local item
            item=$(jq ".[$idx]" <<< "$array_data")
            if ! jq -e '.path and .why' <<< "$item" &>/dev/null; then
              fail "Audit validation failed: vault_audit.$array_prop[$idx] must have 'path' and 'why' properties"
            fi
          done
        fi
      fi
    done
  fi
  
  # Validate code_audit structure
  if jq -e '.code_audit' <<< "$audit" &>/dev/null; then
    local code_audit
    code_audit=$(jq '.code_audit' <<< "$audit")
    local code_props=("components" "services" "models" "apis" "tests")
    for prop in "${code_props[@]}"; do
      if ! jq -e ".$prop" <<< "$code_audit" &>/dev/null; then
        fail "Audit validation failed: code_audit.$prop is required"
      fi
    done
    
    # Validate code_audit arrays have correct structure
    for array_prop in "components" "services" "models" "apis" "tests"; do
      if jq -e ".$array_prop" <<< "$code_audit" &>/dev/null; then
        local array_data
        array_data=$(jq ".$array_prop" <<< "$code_audit")
        if ! jq -e 'type == "array"' <<< "$array_data" &>/dev/null; then
          fail "Audit validation failed: code_audit.$array_prop must be an array"
        else
          local item_count
          item_count=$(jq 'length' <<< "$array_data")
          for idx in $(seq 0 $((item_count - 1))); do
            local item
            item=$(jq ".[$idx]" <<< "$array_data")
            if ! jq -e '.path and .why' <<< "$item" &>/dev/null; then
              fail "Audit validation failed: code_audit.$array_prop[$idx] must have 'path' and 'why' properties"
            fi
          done
        fi
      fi
    done
  fi
}

# Verify all paths in the audit file exist
verify_audit_paths() {
  local audit_path="$1"
  local repo_root="$2"
  
  if [[ ! -f "$audit_path" ]]; then
    return
  fi
  
  local audit
  audit=$(jq '.' "$audit_path")
  
  # Collect all paths from vault_audit
  if jq -e '.vault_audit' <<< "$audit" &>/dev/null; then
    local vault_audit
    vault_audit=$(jq '.vault_audit' <<< "$audit")
    
    for array_prop in "decisions" "persona" "target_architecture"; do
      if jq -e ".$array_prop" <<< "$vault_audit" &>/dev/null; then
        local array_data
        array_data=$(jq ".$array_prop" <<< "$vault_audit")
        local item_count
        item_count=$(jq 'length' <<< "$array_data")
        
        for idx in $(seq 0 $((item_count - 1))); do
          local item
          item=$(jq ".[$idx]" <<< "$array_data")
          local path
          path=$(jq -r '.path // empty' <<< "$item")
          
          if [[ -n "$path" ]]; then
            local full_path="$repo_root/$path"
            if [[ ! -e "$full_path" ]]; then
              fail "Path does not exist (vault_audit.$array_prop[$idx]): $path"
            fi
          fi
        done
      fi
    done
  fi
  
  # Collect all paths from code_audit
  if jq -e '.code_audit' <<< "$audit" &>/dev/null; then
    local code_audit
    code_audit=$(jq '.code_audit' <<< "$audit")
    
    for array_prop in "components" "services" "models" "apis" "tests"; do
      if jq -e ".$array_prop" <<< "$code_audit" &>/dev/null; then
        local array_data
        array_data=$(jq ".$array_prop" <<< "$code_audit")
        local item_count
        item_count=$(jq 'length' <<< "$array_data")
        
        for idx in $(seq 0 $((item_count - 1))); do
          local item
          item=$(jq ".[$idx]" <<< "$array_data")
          local path
          path=$(jq -r '.path // empty' <<< "$item")
          
          if [[ -n "$path" ]]; then
            local full_path="$repo_root/$path"
            if [[ ! -e "$full_path" ]]; then
              fail "Path does not exist (code_audit.$array_prop[$idx]): $path"
            fi
          fi
        done
      fi
    done
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
  
  # Extract paths from sentinel
  local sentinel
  sentinel=$(jq '.' "$sentinel_path")
  local audit_path
  audit_path=$(jq -r '.verify_params.audit_path // empty' <<< "$sentinel")
  
  if [[ -z "$audit_path" ]]; then
    echo "Sentinel file missing 'verify_params.audit_path'" >&2
    exit 2
  fi
  
  # Run verifications
  verify_audit_structure "$audit_path"
  verify_audit_paths "$audit_path" "$PROJECT_DIR"
  
  # Delete sentinel file after verification
  rm -f "$sentinel_path"

  # Exit if any failures
  exit_if_failed
  
  
  echo -e "${GREEN}Verification passed${NC}" >&2
}

main "$@"
