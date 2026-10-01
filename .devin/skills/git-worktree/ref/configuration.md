# git worktree Configuration

How repository configuration behaves across worktrees and how to set worktree-specific options.

[Source: https://git-scm.com/docs/git-worktree]

## Default behavior

By default, all worktrees share the same repository `config` file. Per-worktree files such as `HEAD`, `index`, and the worktree’s `gitdir` link are separate, but configuration is common.

When `extensions.worktreeConfig` is disabled:

- `core.bare` and `core.worktree` in the common `config` file apply only to the main worktree.

## Enabling worktree-specific configuration

Enable per-worktree config files:

```
git config extensions.worktreeConfig true
```

Effects:

- A separate config file is read from the path returned by `git rev-parse --git-path config.worktree` (inside the linked worktree’s administrative directory under `$GIT_DIR/worktrees/<id>/`).
- That file is read **after** `.git/config`.
- Use `git config --worktree` to read/write values in the worktree-specific config file.
- Older Git versions cannot access repositories with `extensions.worktreeConfig` enabled.

## Values that should not be shared

When using per-worktree config, move these out of the shared `config` file into the worktree-specific config:

- `core.worktree` — must never be shared.
- `core.bare=true` — should not be shared.
- `core.sparseCheckout` — should not be shared unless sparse checkout is used in every worktree.

## git-config variables

### `worktree.guessRemote`

Type: boolean

When `true`, `git worktree add <path>` (without an explicit `<commit-ish>` and without `-b`/`-B`/`--detach`) tries to find a remote-tracking branch whose name uniquely matches the basename of `<path>`.

- If a unique match exists, it is checked out and set as upstream for the new local branch.
- If multiple remotes match, the command fails.
- If no match exists, falls back to creating a new branch from `HEAD`.

### `worktree.useRelativePaths`

Type: boolean  
Default: `false`

- `true`: link worktrees using relative paths.
- `false`: link worktrees using absolute paths.

Setting this to `true` enables `extensions.relativeWorktrees` and is incompatible with older Git versions.

Use relative paths when the repository and its worktrees may be moved together (e.g., portable drives, shared environments).

## Overriding config from the command line

- `git worktree add --relative-paths` / `--no-relative-paths` overrides `worktree.useRelativePaths`.
- `git worktree add --guess-remote` / `--no-guess-remote` overrides `worktree.guessRemote` for that invocation.

## Related config variables

- `gc.worktreePruneExpire` — how long stale worktree administrative files are kept before automatic pruning.
- `checkout.defaultRemote` — disambiguates which remote to use when multiple remotes have a branch of the same name during `git worktree add <path> <branch>`.
