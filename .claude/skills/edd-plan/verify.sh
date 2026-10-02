#!/usr/bin/env bash
# verify.sh - Verify edd-plan skill completion against its sentinel.
#
# Checks:
#   1. The plan path recorded in the sentinel exists and is valid JSON.
#   2. The plan document conforms to schema/plan.schema.json.
#   3. The refinement document recorded in the sentinel exists.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLAN_SCHEMA_PATH="$SCRIPT_DIR/schema/plan.schema.json"
VALIDATE_JSON_SCHEMA_SCRIPT="$SCRIPT_DIR/../validate-json-schema/scripts/validate-json-schema.sh"

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

FAILURES=()

fail() {
    FAILURES+=("$1")
}

exit_if_failed() {
    if [[ ${#FAILURES[@]} -gt 0 ]]; then
        echo -e "${RED}edd-plan verification failed:${NC}" >&2
        printf '%s\n' "${FAILURES[@]}" >&2
        exit 2
    fi
}

usage() {
    echo "Usage: verify.sh <sentinel_file>" >&2
    exit 2
}

main() {
    local sentinel_path="${1:-}"

    if [[ -z "$sentinel_path" ]]; then
        usage
    fi

    if [[ ! -f "$sentinel_path" ]]; then
        fail "Sentinel file not found: $sentinel_path"
        exit_if_failed
    fi

    # Extract verify_params from the sentinel.
    local plan_path refinement_path
    plan_path=$(jq -r '.verify_params.plan_path // empty' "$sentinel_path")
    refinement_path=$(jq -r '.verify_params.refinement_path // empty' "$sentinel_path")

    # Locate the git repository root; all paths in the sentinel are relative
    # to the repository root.
    local repo_root
    repo_root=$(git rev-parse --show-toplevel 2>/dev/null || true)
    if [[ -z "$repo_root" ]]; then
        fail "Cannot locate git repository root"
        exit_if_failed
    fi

    # --- Check 1: plan document exists and is valid JSON. ---
    local plan_abs=""
    if [[ -z "$plan_path" ]]; then
        fail "verify_params.plan_path is missing from sentinel"
    else
        plan_abs="$repo_root/$plan_path"
        if [[ ! -f "$plan_abs" ]]; then
            fail "Plan document not found: $plan_path"
            plan_abs=""
        elif ! jq empty "$plan_abs" 2>/dev/null; then
            fail "Plan document is not valid JSON: $plan_path"
            plan_abs=""
        fi
    fi

    # --- Check 2: plan document conforms to schema/plan.schema.json. ---
    if [[ -n "$plan_abs" ]]; then
        if [[ ! -f "$PLAN_SCHEMA_PATH" ]]; then
            fail "Plan schema not found: $PLAN_SCHEMA_PATH"
        elif [[ ! -x "$VALIDATE_JSON_SCHEMA_SCRIPT" && ! -f "$VALIDATE_JSON_SCHEMA_SCRIPT" ]]; then
            fail "validate-json-schema.sh script not found: $VALIDATE_JSON_SCHEMA_SCRIPT"
        else
            local schema_output
            if ! schema_output=$(bash "$VALIDATE_JSON_SCHEMA_SCRIPT" "$PLAN_SCHEMA_PATH" "$plan_abs" 2>&1); then
                fail "Plan document does not conform to plan.schema.json: $schema_output"
            fi
        fi
    fi

    # --- Check 3: refinement document exists. ---
    if [[ -z "$refinement_path" ]]; then
        fail "verify_params.refinement_path is missing from sentinel"
    else
        local refinement_abs="$repo_root/$refinement_path"
        if [[ ! -f "$refinement_abs" ]]; then
            fail "Refinement document not found: $refinement_path"
        fi
    fi

    exit_if_failed
    echo -e "${GREEN}edd-plan verification passed${NC}" >&2
}

main "$@"
