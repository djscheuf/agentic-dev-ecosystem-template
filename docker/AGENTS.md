# Docker Standards (docker/)

## Core Principles

- Build minimal, secure images; one process per container; containers stay stateless/ephemeral.
- Never store secrets in images or compose files — use runtime env vars or a secrets manager.

## Image & Config Versions

- Pin explicit image tags (not `:latest` or a moving branch tag like `:master`) so builds are
  reproducible; bump them deliberately.
  - `docker-compose.yml` currently pins `cadence` to `ubercadence/server:master` and `cadence-web`
    to `ubercadence/web:latest` — both float. Pin to a specific released tag the next time either
    service is bumped.
- Before bumping a service version (Cadence, SQLite, etc.), check its current compose/config docs
  — config shape and required env vars change between major versions.
- If a version is deliberately pinned below current stable (known compatibility issue), say why
  in the commit/PR.

## Health Checks

- Every long-running service in compose should define a `healthcheck`, and anything that depends
  on it should use `depends_on: condition: service_healthy` (already done for `cadence-web` →
  `cadence`).
  - `cadence-web` itself has no healthcheck — add one if another service ever needs to depend on it.

## `cadence-ping.py`

Keep it dependency-light — it's a health-check script, not application code. Don't pull in the
same patterns/dependencies used in `src/`.

## Forbidden

- Secrets in images or compose files (`ENV API_KEY=...`, a committed `.env`)
- `:latest` or a branch-name tag (`:master`) for any image
- Skipping a healthcheck on a service other things depend on
