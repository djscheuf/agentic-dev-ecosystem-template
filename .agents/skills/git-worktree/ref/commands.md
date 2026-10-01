# git worktree Commands

Reference for the `git worktree` subcommands, their flags, and output formats.

[Source: https://git-scm.com/docs/git-worktree]

## Synopsis

```
git worktree add [-f] [--detach] [--checkout] [--lock [--reason <string>]]
                 [--orphan] [(-b | -B) <new-branch>] <path> [<commit-ish>]
git worktree list [-v | --porcelain [-z]]
git worktree lock [--reason <string>] <worktree>
git worktree move <worktree> <new-path>
git worktree prune [-n] [-v] [--expire <expire>]
git worktree remove [-f] <worktree>
git worktree repair [<path>…]
git worktree unlock <worktree>
```

## Identifying a worktree

Most subcommands accept `<worktree>` as a path (relative or absolute). If the final path component is unique among all worktrees, you can use just that tail (e.g., `foo` or `bar/foo`).

## add

Create a new linked worktree at `<path>` and check out `<commit-ish>` into it.

### Behavior defaults

- If `<commit-ish>` is omitted and none of `-b`, `-B`, or `--detach` are used, Git creates or checks out a branch named after the basename of `<path>`.
- If that branch does not exist, it is created from `HEAD`.
- If the branch exists but is already checked out elsewhere, the command fails unless `--force` is used.
- If `<commit-ish>` is `-`, it is treated as `@{-1}` (previous branch/commit).
- If `<commit-ish>` is a branch name not found locally, and exactly one remote has a tracking branch with that name (and neither `-b`/`-B`/`--detach` is used), Git behaves as if you ran:
  ```
  git worktree add --track -b <branch> <path> <remote>/<branch>
  ```
- If multiple remotes match and `checkout.defaultRemote` is set, that remote is used for disambiguation.
- If there are no valid local branches (or remote branches with `--guess-remote`), Git may create a new unborn branch named after the path, as if `--orphan` was passed.

### Options

| Flag | Meaning |
|------|---------|
| `-f`, `--force` | Override safeguards: branch already checked out elsewhere; `<path>` already assigned to a missing worktree; adding a missing but locked path requires `-f` twice. |
| `-b <new-branch>` | Create and check out a new branch starting at `<commit-ish>` (default `HEAD`). Fails if the branch exists. |
| `-B <new-branch>` | Same as `-b`, but reset the branch to `<commit-ish>` if it already exists. |
| `-d`, `--detach` | Check out the commit with detached `HEAD`. |
| `--checkout` / `--no-checkout` | Default is `--checkout`. Use `--no-checkout` to create the worktree without populating it, e.g., before configuring sparse-checkout. |
| `--guess-remote` / `--no-guess-remote` | When `<commit-ish>` is omitted, prefer a matching remote-tracking branch over creating a branch from `HEAD`. Can be made default via `worktree.guessRemote`. |
| `--track` / `--no-track` | When creating a new branch from a branch, mark the source as upstream. Default when `<commit-ish>` is a remote-tracking branch. |
| `--lock` | Keep the new worktree locked immediately (avoids a race with `git worktree lock`). |
| `--reason <string>` | Reason stored in the lock file when used with `--lock`. |
| `--orphan` | Create an empty worktree/index associated with a new unborn branch named `<new-branch>`. |
| `-q`, `--quiet` | Suppress feedback messages. |

## list

List worktrees. Main worktree is listed first, then linked worktrees.

Default output columns:

```
/path/to/bare-source            (bare)
/path/to/linked-worktree        abcd1234 [master]
/path/to/other-linked-worktree  1234abc  (detached HEAD)
```

Annotations:

- `locked` — worktree is locked.
- `prunable` — worktree can be pruned because its working tree is missing.

With `-v`/`--verbose`, reasons for `locked`/`prunable` appear indented on the next line.

### Machine-readable output

- `--porcelain` — stable, scriptable format.
- `-z` — terminate records/lines with NUL instead of newline; use with `--porcelain` when paths may contain newlines.

### Porcelain record format

Each worktree is a record; records are separated by a blank line. The first attribute is always `worktree <path>`.

Attributes:

| Attribute | Meaning |
|-----------|---------|
| `worktree <path>` | Path of the worktree. |
| `bare` | This is a bare repository. |
| `HEAD <sha>` | Current HEAD revision. |
| `branch refs/heads/<name>` | Checked-out branch. |
| `detached` | HEAD is detached. |
| `locked` | Locked with no reason. |
| `locked <reason>` | Locked with reason. |
| `prunable <reason>` | Can be pruned; reason follows. |

## lock

Lock a worktree to prevent automatic pruning of its administrative files. Useful for worktrees stored on removable/network storage.

- `--reason <string>` — stores a plain-text reason in the lock file.
- A locked worktree cannot be moved or removed without using `--force` twice.

## unlock

Remove the lock from a worktree, allowing prune/move/remove.

## move

Move a worktree to a new path. Updates internal administrative files.

- Cannot move the main worktree.
- Cannot move worktrees containing submodules.
- `--force` is required twice to move a locked worktree or to overwrite a missing destination path.

## remove

Remove a worktree.

- Only clean worktrees (no modified tracked files, no untracked files) can be removed unless `--force` is used.
- Cannot remove the main worktree.
- `--force` twice is required to remove a locked worktree.

## prune

Remove administrative entries in `$GIT_DIR/worktrees` for worktrees whose working tree directory is missing.

- `-n`, `--dry-run` — report what would be removed without removing it.
- `-v`, `--verbose` — report all removals.
- `--expire <time>` — only prune entries older than the given time.

## repair

Repair stale or corrupted worktree administrative links.

- Run from the main worktree after moving the main/bare repository to reconnect linked worktrees.
- Run from a moved linked worktree to reconnect it to the main repository.
- Pass each moved linked worktree path as an argument to repair multiple moved worktrees from any worktree.
- See `troubleshooting.md` for concrete repair scenarios.
