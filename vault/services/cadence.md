# Cadence

Local Cadence stack runs SQLite persistence in Docker using `docker/docker-compose.yml`.

## Files

- `docker/docker-compose.yml` — `ubercadence/server:master` + `ubercadence/web:latest`
- `docker/cadence-sqlite.yaml` — server config for SQLite
- `docker/cadence-ping.py` — Python client smoke test
- `docs/reqs/workflow-orchestration/streams/cadence-local-runbook.md` — operator runbook

## Commands

```bash
cd docker
docker compose up -d
docker compose exec cadence \
  cadence --ad 127.0.0.1:7833 -t grpc --do story-analysis domain register -rd 1
```

## Gotchas

- `ubercadence/server:master` runs as the `cadence` (uid 1000) user by default. The compose file sets `user: root` so the container can write the SQLite files in the named Docker volume at `/data`.
- `cadence-sql-tool` in the `ubercadence/server` image does not include the SQLite driver (`unknown driver "sqlite3"` error). Use `cadence-server --root /etc/cadence --env docker update-schema` instead; it applies the SQLite schema from the config file.
- `start-cadence.sh` copies `CADENCE_CONFIG_FILE` to `/etc/cadence/config/docker.yaml` and then runs the configured services. Run the `update-schema` command first, then exec `start-cadence.sh`.
- The Python client `cadence-python-client` on Nix/Linux may need `LD_LIBRARY_PATH` pointed at a `libstdc++.so.6` location because the `grpcio` wheel links it. Fixed in `shell.nix` (2026-08-28): add `stdenv.cc.cc.lib` to `buildInputs` and `export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"` in `shellHook`.
- Querying a non-existent `WorkflowID` raises `cadence.error.EntityNotExistsError` with a `StatusCode.NOT_FOUND` gRPC error and the message `GetCurrentExecution failed. Error: sql: no rows in result set`. This is a normal "not found" path, not a database connectivity issue. Client CLIs should catch `EntityNotExistsError` and print a workflow-id-focused message rather than dumping the gRPC traceback.

## Python client SDK gap: no `TestWorkflowEnvironment` on PyPI yet (2026-08-28)

`.devin/skills/cadence-workflow-orchestration/03-python-client/testing.md` documents
`cadence.testing.TestWorkflowEnvironment` as supported, but **the latest PyPI release
(`cadence-python-client` 0.3.0, confirmed against the `v0.3.0` git tag) does not include
the `cadence/testing/` package** — it only exists on the project's unreleased `main`
branch. `import cadence.testing` raises `ModuleNotFoundError` on 0.3.0.

Workaround used in `src/orchestrator/` (see `src/orchestrator/README.md`): keep all
Workflow sequencing/decision logic in a plain-`asyncio` class
(`story_analysis_engine.StoryAnalysisEngine`) that never imports `cadence` and takes
its Activity calls / signal-wait as injected callables. Unit test that class directly
with fakes. The real `@registry.workflow()` class is a thin adapter with no automated
test coverage of its own (manual verification against a real server instead).

Re-check this gap before assuming `TestWorkflowEnvironment` is usable — it may have
shipped in a release newer than 0.3.0 by the time you read this.

## Ports

- `localhost:7833` — gRPC frontend (used by workers and clients)
- `localhost:8088` — Cadence Web UI

## Client API (2026-08-29)

`src/story_analysis_workflow/` is the client-side counterpart to `src/orchestrator/`: starts runs,
sends `human_response`, queries `get_status`, and registers the domain, without needing the
`cadence` CLI binary installed. See `docs/reqs/workflow-orchestration/streams/client-api-usage.md`.

- `config.py` — `CadenceConfig`/`load_config()` centralize domain/task-list/target/timeout config.
  Precedence: explicit function argument > `domain-task-list-retry-config.json` > env var
  (`CADENCE_DOMAIN`/`CADENCE_TASK_LIST`/`CADENCE_TARGET`) > hardcoded default. Both `cli.py` and
  `starter.py` depend on this for consistency.
- `starter.py` — derives a deterministic `WorkflowID` (slug + content hash) from the story
  document when none is given, so re-running the same input is rejected as a duplicate
  (`RejectDuplicate`) rather than silently starting a concurrent run — this is how the "Concurrent
  workflow executions for the same story" edge case is closed for this stream.
- `cli.py` — `story-analysis-cli` (argparse-based) is a from-scratch alternative to the `cadence`
  CLI binary; it takes an injectable `client_factory`/`config` for unit testing entirely against
  `tests/fake_client.FakeClient`, no live server needed. `register-domain` calls
  `client.domain_stub.RegisterDomain` directly rather than shelling out.
- Same `cadence.testing.TestWorkflowEnvironment` gap noted above applies: none of this client code
  needs it (it only talks to `Client`'s async methods, all faked in tests).

## See also

- [Workflow Engine implementation](../../src/orchestrator/README.md) — the Story
  Analysis Workflow example (`StoryAnalysisWorkflow`, its four skill Activities, and
  the pure `StoryAnalysisEngine` decision logic).
- [Client API usage](../../docs/reqs/workflow-orchestration/streams/client-api-usage.md) — starter/
  CLI/Signal/Query usage for `src/story_analysis_workflow/`.
