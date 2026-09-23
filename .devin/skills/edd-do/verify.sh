#!/usr/bin/env bash
# verify.sh - Verify edd-do skill completion against its sentinel.
#
# Checks:
#   1. The plan path recorded in the sentinel exists and is valid JSON.
#   2. The running refinement.yaml under the same edd/<run_id> exists and
#      documents the iteration number recorded in the sentinel.
#   3. The working tree contains changes ONLY for the files listed in the
#      sentinel's changed_files array (no extra modified/untracked files,
#      no missing expected changes).

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

FAILURES=()

fail() {
    FAILURES+=("$1")
}

exit_if_failed() {
    if [[ ${#FAILURES[@]} -gt 0 ]]; then
        echo -e "${RED}edd-do verification failed:${NC}" >&2
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
    local plan_path iteration_number action
    plan_path=$(jq -r '.verify_params.plan_path // empty' "$sentinel_path")
    iteration_number=$(jq -r '.verify_params.iteration_number // empty' "$sentinel_path")
    action=$(jq -r '.verify_params.action // empty' "$sentinel_path")

    # Locate the git repository root; all paths in the sentinel are relative
    # to the repository root.
    local repo_root
    repo_root=$(git rev-parse --show-toplevel 2>/dev/null || true)
    if [[ -z "$repo_root" ]]; then
        fail "Cannot locate git repository root"
        exit_if_failed
    fi

    # --- Check 1: plan path exists and is valid JSON. ---
    if [[ -z "$plan_path" ]]; then
        fail "verify_params.plan_path is missing from sentinel"
    else
        local plan_abs="$repo_root/$plan_path"
        if [[ ! -f "$plan_abs" ]]; then
            fail "Plan path does not exist: $plan_path"
        elif ! jq empty "$plan_abs" 2>/dev/null; then
            fail "Plan file is not valid JSON: $plan_path"
        else
            # Light consistency check: the plan's action matches the sentinel.
            local plan_action
            plan_action=$(jq -r '.action // empty' "$plan_abs")
            if [[ -n "$action" && -n "$plan_action" && "$action" != "$plan_action" ]]; then
                fail "Sentinel action '$action' does not match plan action '$plan_action'"
            fi
        fi
    fi

    # --- Check 2: refinement.yaml exists and documents iteration n. ---
    if [[ -n "$plan_path" ]]; then
        # plan_path is .process/edd/<run_id>/iterations/<n>/plan.json
        # Strip three levels to reach the run directory.
        local run_dir refinement_path
        run_dir=$(dirname "$(dirname "$(dirname "$plan_path")")")
        refinement_path="$run_dir/refinement.yaml"
        local refinement_abs="$repo_root/$refinement_path"

        if [[ ! -f "$refinement_abs" ]]; then
            fail "Refinement document not found: $refinement_path"
        elif [[ -z "$iteration_number" ]]; then
            fail "verify_params.iteration_number is missing; cannot verify refinement.yaml section"
        else
            # Look for an iteration marker in either YAML-key or heading form,
            # e.g. "iteration: 3", "## Iteration 3", "iteration = 3".
            local pattern
            pattern='\biteration\b[[:space:]]*[:=-]?[[:space:]]*\b'"${iteration_number}"'\b'
            if ! grep -qiE "$pattern" "$refinement_abs"; then
                fail "Refinement document $refinement_path does not appear to document iteration $iteration_number"
            fi
        fi
    fi

    # --- Check 3: working tree changes match changed_files exactly. ---
    local -a expected_files=()
    while IFS= read -r f; do
        [[ -n "$f" ]] && expected_files+=("$f")
    done < <(jq -r '.verify_params.changed_files[]?' "$sentinel_path" 2>/dev/null || true)

    local -a actual_files=()
    while IFS= read -r line; do
        [[ -z "$line" ]] && continue

        # git status --porcelain format: "XY PATH" or "XY OLD -> NEW".
        local status_code="${line:0:2}"
        local rest="${line:3}"
        local file_entry=""

        case "$status_code" in
            R?|?R)
                # Renamed: use the new path (after " -> ").
                file_entry=$(printf '%s' "$rest" | sed 's/.* -> //')
                ;;
            *)
                file_entry="$rest"
                ;;
        esac

        # Process artifacts live under .process/ and are gitignored.
        # They are not part of the candidate change set.
        if [[ "$file_entry" == .process/* || "$file_entry" == .process ]]; then
            continue
        fi

        actual_files+=("$file_entry")
    done < <(git -C "$repo_root" status --porcelain)

    # Compare actual vs expected.
    local -a extra=() missing=()

    for a in "${actual_files[@]}"; do
        local found=false
        for e in "${expected_files[@]}"; do
            if [[ "$a" == "$e" ]]; then
                found=true
                break
            fi
        done
        if [[ "$found" == false ]]; then
            extra+=("$a")
        fi
    done

    for e in "${expected_files[@]}"; do
        local found=false
        for a in "${actual_files[@]}"; do
            if [[ "$a" == "$e" ]]; then
                found=true
                break
            fi
        done
        if [[ "$found" == false ]]; then
            missing+=("$e")
        fi
    done

    if [[ ${#extra[@]} -gt 0 ]]; then
        for f in "${extra[@]}"; do
            fail "Unexpected working-tree change not listed in changed_files: $f"
        done
    fi

    if [[ ${#missing[@]} -gt 0 ]]; then
        for f in "${missing[@]}"; do
            fail "File listed in changed_files is not modified in working tree: $f"
        done
    fi

    exit_if_failed
    echo -e "${GREEN}edd-do verification passed${NC}" >&2
}

main "$@"
