#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat <<'EOF'
Usage: clean_worktree.sh [OPTIONS] <branch>

Remove the Git linked worktree associated with <branch> after confirming the
branch has been merged. Optionally delete the local branch as well.

The script expects the worktree to live at the conventional location created by
create_worktree.sh:
  <parent>/worktrees/<repo>_<branch>

If the worktree directory is already missing, its stale administrative entry is
pruned instead.

Options:
  -f, --force          Skip the merge check and force removal.
  -d, --delete-branch  Also delete the local branch after removing the worktree.
  -n, --dry-run        Print the operations that would run without executing them.
  -h, --help           Show this help message and exit.

Examples:
  clean_worktree.sh feature-x
  clean_worktree.sh -d feature-x
  clean_worktree.sh -n -d feature-x
EOF
}

die() { echo "Error: $*" >&2; exit 1; }

DRY_RUN=0
FORCE=0
DELETE_BRANCH=0
BRANCH=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        -n|--dry-run) DRY_RUN=1; shift ;;
        -f|--force) FORCE=1; shift ;;
        -d|--delete-branch) DELETE_BRANCH=1; shift ;;
        -h|--help) usage; exit 0 ;;
        --) shift; break ;;
        -*) die "Unknown option: $1" ;;
        *)
            if [[ -z "$BRANCH" ]]; then
                BRANCH="$1"
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

# Verify the branch exists locally.
git show-ref --verify --quiet "refs/heads/${BRANCH}" || die "Local branch '${BRANCH}' does not exist."

# Determine what "merged" means. Prefer the remote's default branch; fall back to HEAD.
merge_target="HEAD"
if git rev-parse --verify --quiet refs/remotes/origin/HEAD >/dev/null 2>&1; then
    merge_target=$(git rev-parse --abbrev-ref refs/remotes/origin/HEAD)
fi

if [[ "$FORCE" -eq 0 ]]; then
    if git --no-pager branch --merged "$merge_target" --format='%(refname:short)' | grep -qx "$BRANCH"; then
        echo "Branch '${BRANCH}' is merged into ${merge_target}."
    else
        die "Branch '${BRANCH}' is not merged into ${merge_target}. Use --force to override, or merge the branch first."
    fi
else
    echo "Skipping merge check for branch '${BRANCH}' (--force)."
fi

# Locate the worktree record for this branch from 'git worktree list --porcelain'.
worktree_path=""
locked=0
{
    read -r _ wt_path
    in_record=1
    while IFS= read -r line; do
        if [[ -z "$line" ]]; then
            in_record=1
            continue
        fi
        if [[ "$in_record" -eq 1 ]]; then
            wt_path=${line#worktree }
            locked=0
            in_record=0
            continue
        fi
        case "$line" in
            branch\ refs/heads/${BRANCH})
                worktree_path="$wt_path"
                ;;
            locked*)
                locked=1
                ;;
        esac
    done
} < <(git worktree list --porcelain)

# If Git doesn't list a worktree for the branch, check the conventional path so
# we can still remove a stale or manually created directory.
main_path=$(git worktree list --porcelain | awk '/^worktree / {print $2; exit}')
parent_dir=$(dirname "$main_path")
repo_name=$(basename "$main_path")
conventional_path="${parent_dir}/worktrees/${repo_name}_${BRANCH}"

if [[ -n "$worktree_path" ]]; then
    target_path="$worktree_path"
else
    target_path="$conventional_path"
fi

remove_flags=""
if [[ "$FORCE" -eq 1 ]]; then
    remove_flags="-f"
    if [[ "$locked" -eq 1 ]]; then
        remove_flags="-ff"
    fi
fi

run_cmd() {
    echo "+ $*"
    "$@"
}

if [[ -n "$worktree_path" ]]; then
    if [[ -e "$target_path" ]]; then
        if [[ "$DRY_RUN" -eq 1 ]]; then
            echo "Would remove worktree at ${target_path} (git worktree remove ${remove_flags} ${target_path@Q})"
        else
            if [[ -n "$remove_flags" ]]; then
                git worktree remove "$remove_flags" "$target_path"
            else
                git worktree remove "$target_path"
            fi
        fi
    else
        if [[ "$DRY_RUN" -eq 1 ]]; then
            echo "Would prune stale worktree entry for branch '${BRANCH}' (git worktree prune)"
        else
            echo "Worktree directory ${target_path} is missing; pruning stale entry."
            git worktree prune
        fi
    fi
else
    if [[ -d "$target_path" ]]; then
        if [[ "$DRY_RUN" -eq 1 ]]; then
            echo "Would remove unregistered worktree directory ${target_path}"
        else
            die "Found a directory at ${target_path} but it is not registered as a Git worktree. Remove it manually if appropriate."
        fi
    else
        die "No worktree found for branch '${BRANCH}'."
    fi
fi

# Optionally delete the branch.
if [[ "$DELETE_BRANCH" -eq 1 ]]; then
    if [[ "$DRY_RUN" -eq 1 ]]; then
        echo "Would delete local branch '${BRANCH}'"
    else
        if [[ "$FORCE" -eq 1 ]]; then
            git branch -D "$BRANCH"
        else
            git branch -d "$BRANCH"
        fi
    fi
fi

# Clean up the intermediate worktrees directory if it is now empty.
worktrees_parent="${parent_dir}/worktrees"
if [[ -d "$worktrees_parent" ]] && [[ -z "$(ls -A "$worktrees_parent" 2>/dev/null || true)" ]]; then
    if [[ "$DRY_RUN" -eq 1 ]]; then
        echo "Would remove empty directory ${worktrees_parent}"
    else
        rmdir "$worktrees_parent"
    fi
fi

if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "Dry run complete; no changes made."
else
    echo "Cleanup complete for branch '${BRANCH}'."
fi
