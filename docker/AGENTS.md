# Docker Standards (docker/)

## Image & Config Versions

- Pin explicit image tags (not `:latest`) so builds are reproducible; bump them deliberately.
- Before bumping a service version (Cadence, SQLite, etc.), check its current compose/config docs
  — config shape and required env vars change between major versions.
- If a version is deliberately pinned below current stable (known compatibility issue), say why
  in the commit/PR.

## `cadence-ping.py`

Keep it dependency-light — it's a health-check script, not application code. Don't pull in the
same patterns/dependencies used in `src/`.
