---
description: Create, manage, clean up, and troubleshoot Git worktrees for parallel branch checkouts.
---

# git worktree

`git worktree` lets a single repository maintain multiple working trees, each checked out to a different branch or commit. Use it when you need to work on multiple branches at once (e.g., a hotfix alongside a long-running refactor) without stashing or cloning the repository again.

## When to use this skill

- Creating a new linked worktree from a branch, tag, or detached commit.
- Listing, moving, locking, unlocking, or removing existing worktrees.
- Cleaning up stale worktree metadata after manual deletion.
- Repairing broken worktree links after moving repositories or worktrees.
- Configuring per-worktree Git settings.

## Core concepts

- A repository has **one main worktree** (unless it is bare) and zero or more **linked worktrees**.
- All worktrees share the same object database and most refs, but each has its own `HEAD`, `index`, and checked-out files.
- A worktree is identified by its path (relative or absolute); if the path tail is unique, you can refer to it by just the basename.
- Worktree metadata lives under `$GIT_DIR/worktrees/<id>/`.

## Reference Files

- `ref/commands.md` — subcommand syntax, options, and machine-readable `list` output format.
- `ref/configuration.md` — shared vs. per-worktree config and relevant `git-config` variables.
- `ref/troubleshooting.md` — repair scenarios, cleanup, locks, and common gotchas.

## Utility Scripts

- `scripts/create_worktree.sh` — create a linked worktree for a branch at the conventional path `{parent}/worktrees/{repo}_{branch}`. Supports `--dry-run`.
- `scripts/clean_worktree.sh` — remove the worktree for a branch after confirming the branch is merged; optionally delete the branch. Supports `--dry-run` and `--force`.

[Source: https://git-scm.com/docs/git-worktree]
