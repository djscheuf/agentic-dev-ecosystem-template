#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat <<'EOF'
Usage: create_worktree.sh [OPTIONS] <branch> [<base-commit>]

Create a Git linked worktree for an existing or new branch under a conventional
location next to the main repository.

If the current repository is at /path/to/repo, the new worktree is created at:
  /path/to/worktrees/repo_<branch>

The intermediate "worktrees" directory is created if it does not exist.

Arguments:
  branch        Name of the branch to check out in the new worktree.
  base-commit   Commit, branch, or tag from which to create <branch> when it does
                not already exist. Defaults to HEAD.

Options:
  -n, --dry-run  Print the commands that would run without executing them.
  -h, --help     Show this help message and exit.

Examples:
  create_worktree.sh feature-x
  create_worktree.sh -n feature-x origin/main
EOF
}

die() { echo "Error: $*" >&2; exit 1; }

DRY_RUN=0
BRANCH=""
BASE_COMMIT=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        -n|--dry-run) DRY_RUN=1; shift ;;
        -h|--help) usage; exit 0 ;;
        --) shift; break ;;
        -*) die "Unknown option: $1" ;;
        *)
            if [[ -z "$BRANCH" ]]; then
                BRANCH="$1"
            elif [[ -z "$BASE_COMMIT" ]]; then
                BASE_COMMIT="$1"
            else
                die "Unexpected argument: $1"
            fi
            shift
            ;;
    esac
done

if [[ -z "$BRANCH" ]]; then
    usage >&2
    exit 1
fi

BASE_COMMIT="${BASE_COMMIT:-HEAD}"

# Resolve the main worktree path so the new worktree is placed next to it
# regardless of which worktree the script is invoked from.
main_path=$(git worktree list --porcelain | awk '/^worktree / {print $2; exit}')
[[ -n "$main_path" ]] || die "Could not determine the main worktree path."

parent_dir=$(dirname "$main_path")
repo_name=$(basename "$main_path")
worktree_dir="${parent_dir}/worktrees/${repo_name}_${BRANCH}"

mkdir -p "$(dirname "$worktree_dir")"

if git show-ref --verify --quiet "refs/heads/${BRANCH}"; then
    if [[ "$DRY_RUN" -eq 1 ]]; then
        echo "Would create worktree directory: ${worktree_dir}"
        echo "Would run: git worktree add ${worktree_dir@Q} ${BRANCH@Q}"
        exit 0
    fi
    echo "Branch '${BRANCH}' exists; checking it out in ${worktree_dir}"
    git worktree add "$worktree_dir" "$BRANCH"
else
    if [[ "$DRY_RUN" -eq 1 ]]; then
        echo "Would create worktree directory: ${worktree_dir}"
        echo "Would run: git worktree add -b ${BRANCH@Q} ${worktree_dir@Q} ${BASE_COMMIT@Q}"
        exit 0
    fi
    echo "Creating branch '${BRANCH}' from ${BASE_COMMIT} and worktree ${worktree_dir}"
    git worktree add -b "$BRANCH" "$worktree_dir" "$BASE_COMMIT"
fi

echo "Worktree ready at ${worktree_dir}"
