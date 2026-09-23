#!/usr/bin/env bash
# verify.test.sh - Tests for edd-plan/verify.sh
#
# Creates throwaway git repositories, installs fake EDD process artifacts,
# and asserts that verify.sh accepts the valid case and rejects the invalid
# ones. Every test runs in its own temp repo, which is removed afterward.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERIFY_SCRIPT="$SCRIPT_DIR/verify.sh"
ORIGINAL_DIR="$(pwd)"

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

PASS=0
FAIL=0

# Ensure we always return to the original working directory on exit, even if
# a test case or the script itself errors out early.
cleanup() {
    cd "$ORIGINAL_DIR" || true
}
trap cleanup EXIT

# Create a temp repo, cd into it, and record the temp path for later removal.
mk_temp_repo() {
    local tmp
    tmp=$(mktemp -d)
    cd "$tmp"
    git init -q
    CURRENT_TMP=$tmp
}

VALID_PLAN_JSON='{
  "iteration_number": 3,
  "action": "repair",
  "rationale": "fix fixture",
  "intended_files": ["skill/SKILL.md"],
  "expected_effect": "test passes",
  "iteration_start_baseline": {
    "source": "baseline",
    "passing": 1,
    "failing": 1,
    "total": 2
  },
  "requires_approval": false,
  "stop_recommendation": false
}'

# Common fixture layout used by every test: a valid plan, a valid refinement
# document, and a sentinel that points at both.
write_process_artifacts() {
    mkdir -p .process/edd/run-1/iterations/3
    printf '%s' "$VALID_PLAN_JSON" > .process/edd/run-1/iterations/3/plan.json
    cat > .process/edd/run-1/refinement.yaml <<'EOF'
## Iteration 3
action: repair
EOF
    cat > .process/edd-plan.done.json <<'EOF'
{"task":"edd-plan","status":"completed","verify_params":{"plan_path":".process/edd/run-1/iterations/3/plan.json","refinement_path":".process/edd/run-1/refinement.yaml","iteration_number":3,"action":"repair"}}
EOF
}

run_case() {
    local name="$1"
    local expected_rc="$2"
    shift 2

    # Every case runs in its own temp repo, cd'd here in the current shell.
    mk_temp_repo
    write_process_artifacts

    # Apply per-test setup commands passed as args.
    "$@"

    set +e
    bash "$VERIFY_SCRIPT" .process/edd-plan.done.json >/dev/null 2>&1
    local actual_rc=$?
    set -e

    rm -rf "$CURRENT_TMP"
    cd "$ORIGINAL_DIR"

    if [[ $actual_rc -eq $expected_rc ]]; then
        echo -e "${GREEN}PASS${NC} $name (rc=$actual_rc)"
        PASS=$((PASS + 1))
    else
        echo -e "${RED}FAIL${NC} $name: expected rc=$expected_rc, got rc=$actual_rc"
        FAIL=$((FAIL + 1))
    fi
}

pass_case() {
    run_case "$1" 0 "${@:2}"
}

fail_case() {
    run_case "$1" 2 "${@:2}"
}

# --- Positive case ----------------------------------------------------------
pass_case "valid plan and refinement document" true

# --- Negative cases ----------------------------------------------------------
fail_case "missing plan document" rm .process/edd/run-1/iterations/3/plan.json

fail_case "plan document is not valid JSON" bash -c 'echo "{not json" > .process/edd/run-1/iterations/3/plan.json'

fail_case "plan document missing a required schema field" bash -c \
    'jq "del(.expected_effect)" .process/edd/run-1/iterations/3/plan.json > tmp.json && mv tmp.json .process/edd/run-1/iterations/3/plan.json'

fail_case "plan document action is outside the taxonomy" bash -c \
    'jq ".action = \"bogus_action\"" .process/edd/run-1/iterations/3/plan.json > tmp.json && mv tmp.json .process/edd/run-1/iterations/3/plan.json'

fail_case "missing refinement document" rm .process/edd/run-1/refinement.yaml

fail_case "sentinel missing plan_path" bash -c \
    'jq "del(.verify_params.plan_path)" .process/edd-plan.done.json > tmp.json && mv tmp.json .process/edd-plan.done.json'

fail_case "sentinel missing refinement_path" bash -c \
    'jq "del(.verify_params.refinement_path)" .process/edd-plan.done.json > tmp.json && mv tmp.json .process/edd-plan.done.json'

fail_case "sentinel file not found" rm .process/edd-plan.done.json

# --- Summary ----------------------------------------------------------------
echo ""
if [[ $FAIL -eq 0 ]]; then
    echo -e "${GREEN}All $PASS tests passed.${NC}"
else
    echo -e "${RED}$FAIL test(s) failed, $PASS passed.${NC}"
    exit 1
fi
