#!/usr/bin/env bash
# verify.sh - Orchestrate verification of expand-story-intent skill outputs
# Verifies both extracted user story and implementation plan against their schemas

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

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
  
  local story_path
  story_path=$(jq -r '.verify_params.extracted_story_path // empty' <<< "$sentinel")
  
  local plan_path
  plan_path=$(jq -r '.verify_params.impl_plan_path // empty' <<< "$sentinel")
  
  if [[ -z "$story_path" ]]; then
    echo "Sentinel file missing 'verify_params.extracted_story_path'" >&2
    exit 2
  fi
  
  if [[ -z "$plan_path" ]]; then
    echo "Sentinel file missing 'verify_params.impl_plan_path'" >&2
    exit 2
  fi
  
  # Run user story verification
  echo -e "${YELLOW}Verifying extracted user story...${NC}" >&2
  if ! "$SCRIPT_DIR/scripts/verify-user-story.sh" "$story_path"; then
    exit 2
  fi
  
  # Run implementation plan verification
  echo -e "${YELLOW}Verifying implementation plan...${NC}" >&2
  if ! "$SCRIPT_DIR/scripts/verify-impl-plan.sh" "$plan_path"; then
    exit 2
  fi
  
  # Delete sentinel file on success
  rm -f "$sentinel_path"
  
  echo -e "${GREEN}All verifications passed${NC}" >&2
}

main "$@"
