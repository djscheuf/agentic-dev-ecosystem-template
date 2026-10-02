#!/usr/bin/env bash
# verify.test.sh - Tests for edd-do/verify.sh
#
# Creates throwaway git repositories, installs fake EDD process artifacts,
# and asserts that verify.sh accepts the valid cases and rejects the invalid ones.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERIFY_SCRIPT="$SCRIPT_DIR/verify.sh"
ORIGINAL_DIR="$(pwd)"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS=0
FAIL=0

# Ensure we always return to the original working directory on exit.
cleanup() {
    cd "$ORIGINAL_DIR" || true
}
trap cleanup EXIT

# Create a temp repo, cd into it, and return the temp path via a variable.
mk_temp_repo() {
    local tmp
    tmp=$(mktemp -d)
    cd "$tmp"
    git init -q
    CURRENT_TMP=$tmp
}

# Common fixture layout used by every test.
write_process_artifacts() {
    mkdir -p .process/edd/run-1/iterations/3
    cat > .process/edd/run-1/iterations/3/plan.json <<'EOF'
{"action":"repair","intended_files":["skill/SKILL.md"],"rationale":"fix fixture","expected_effect":"test passes"}
EOF
    cat > .process/edd/run-1/refinement.yaml <<'EOF'
## Iteration 3
action: repair
EOF
    cat > .process/edd-do.done.json <<'EOF'
{"task":"edd-do","status":"completed","verify_params":{"plan_path":".process/edd/run-1/iterations/3/plan.json","iteration_number":"3","action":"repair","changed_files":["skill/SKILL.md"]}}
EOF
}

# Create a tracked, committed skill file so git can report real modifications.
write_tracked_skill_file() {
    mkdir -p skill
    echo "original skill content" > skill/SKILL.md
    git add skill/SKILL.md
    git commit -q -m "baseline skill"
}

run_case() {
    local name="$1"
    local expected_rc="$2"
    shift 2

    # Every case runs in its own temp repo, cd'd here in the current shell.
    mk_temp_repo
    write_process_artifacts
    write_tracked_skill_file

    # Apply per-test setup commands passed as args.
    "$@"

    set +e
    bash "$VERIFY_SCRIPT" .process/edd-do.done.json >/dev/null 2>&1
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
pass_case "valid change matches changed_files" bash -c 'echo modified > skill/SKILL.md'

# --- Negative cases ---------------------------------------------------------
fail_case "missing plan file" rm .process/edd/run-1/iterations/3/plan.json

fail_case "missing refinement.yaml" rm .process/edd/run-1/refinement.yaml

fail_case "iteration not documented in refinement.yaml" bash -c 'cat > .process/edd/run-1/refinement.yaml <<EOF
## Iteration 2
action: repair
EOF'

fail_case "extra unexpected working-tree change" bash -c 'echo modified > skill/SKILL.md && echo surprise > extra.txt'

fail_case "expected change was reverted before verification" git -C . checkout -- skill/SKILL.md

# --- Summary ----------------------------------------------------------------
echo ""
if [[ $FAIL -eq 0 ]]; then
    echo -e "${GREEN}All $PASS tests passed.${NC}"
else
    echo -e "${RED}$FAIL test(s) failed, $PASS passed.${NC}"
    exit 1
fi
