# Script Standards (scripts/)

## Bash

- `set -euo pipefail` at the top of every script — fail fast and loud instead of continuing past
  an error.
- Quote variable expansions (`"$var"`), especially paths.
- Name scripts by what they do, verb-first, matching the existing convention in this directory:
  `kickoff-*`, `run-*`, `stop-*`, `start-*`.

## Node scripts

- When adding a new npm dependency, check its current setup docs rather than relying on a
  remembered config shape from an older major version.
- Prefer `const`/`let` over `var`; don't let untyped data flow through without a comment on why.

## Forbidden

- Scripts that silently continue after a failed step
- Hardcoded absolute paths — use `$(dirname "$0")` or repo-relative paths
