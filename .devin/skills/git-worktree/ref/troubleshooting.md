# git worktree Troubleshooting

Common repair, cleanup, and day-to-day gotchas when working with linked worktrees.

[Source: https://git-scm.com/docs/git-worktree]

## Manual deletion of a worktree directory

If you delete a linked worktree directory without `git worktree remove`, its administrative files under `$GIT_DIR/worktrees/<id>` remain stale. Clean them up with:

```
git worktree prune
```

Or let `gc` remove them automatically based on `gc.worktreePruneExpire`.

To preview what would be removed:

```
git worktree prune -n
```

## Moving worktrees

### Moving a linked worktree manually

Prefer the supported command:

```
git worktree move <worktree> <new-path>
```

Limitations:

- Cannot move the main worktree.
- Cannot move worktrees that contain submodules.
- A locked worktree requires `--force` twice to move.

### Moving the main worktree or bare repository

If you move the main worktree (or bare repo), linked worktrees lose their connection. From the main worktree run:

```
git worktree repair
```

This reestablishes the connection from every linked worktree back to the main worktree.

### Reconnecting a moved linked worktree

If you moved a linked worktree without `git worktree move`, run from inside that moved worktree:

```
git worktree repair
```

### Multiple moved linked worktrees

From any worktree, pass each moved linked worktree’s new path as an argument:

```
git worktree repair <new-path-1> <new-path-2>
```

### Both main and linked worktrees moved

From the main worktree, pass the new paths of all linked worktrees:

```
git worktree repair <linked-new-path-1> <linked-new-path-2>
```

This repairs both directions of the links.

## Locking for portable or network storage

If a worktree lives on a removable drive or network share, lock it before the storage is unmounted so Git does not prune its administrative files:

```
git worktree lock --reason "mounted on external SSD" /path/to/worktree
```

Unlock when it is permanently available:

```
git worktree unlock /path/to/worktree
```

A locked worktree cannot be moved or removed without using `--force` twice.

## Refs that are not shared across worktrees

Most refs under `refs/` are shared, but these are per-worktree:

- `HEAD`
- `refs/bisect/*`
- `refs/worktree/*`
- `refs/rewritten/*`

Access another worktree’s per-worktree refs with:

```
main-worktree/<ref>
worktrees/<id>/<ref>
```

Examples:

```
git rev-parse main-worktree/HEAD
git rev-parse worktrees/foo/HEAD
```

Avoid directly reading paths inside `$GIT_DIR`; use `git rev-parse --git-path <path>`.

## Internal layout basics

Each linked worktree has a private administrative directory:

```
$GIT_DIR/worktrees/<id>/
```

`<id>` is usually the basename of the worktree path, with a numeric suffix if needed for uniqueness.

Inside the linked worktree, `.git` is a file (not a directory) containing the path to that administrative directory. `$GIT_DIR` points at the administrative directory, while `$GIT_COMMON_DIR` points back at the main repository’s `$GIT_DIR`.

If you must fix a manual move by hand, update `$GIT_DIR/worktrees/<id>/gitdir` to point at the worktree’s new location, then run `git worktree repair`.

## Submodules and multiple checkouts

Git worktree support for submodules is incomplete. It is NOT recommended to maintain multiple checkouts of a superproject when submodules are involved.

## Common error patterns

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Worktree path still listed after deleting directory | Stale `$GIT_DIR/worktrees/<id>` entry | `git worktree prune` |
| `git worktree remove` refuses to delete | Unclean tree or submodules | `git worktree remove -f <path>` (twice if locked) |
| Cannot move a worktree | It contains submodules or is locked | Use `-f` twice if appropriate; otherwise move manually and run `git worktree repair` |
| Branch already checked out | The branch is checked out in another worktree | Use a different branch or `git worktree add -f <path> <branch>` |
| Linked worktree cannot find the main repository | Main worktree or bare repo was moved | Run `git worktree repair` from the main worktree |

## Safe cleanup checklist

Before removing a worktree:

1. Commit or stash any changes.
2. Remove untracked files if you do not need them.
3. Run `git worktree remove <path>` (or `git worktree remove -f <path>` if unclean).
4. If you already deleted the directory, run `git worktree prune -n` first, then `git worktree prune`.
