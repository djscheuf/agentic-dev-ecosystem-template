# Local Development Prerequisites for the Story Analysis Workflow

This document covers the zero-dependency local setup used to run the Story Analysis Workflow example with the Cadence Python client SDK and an embedded SQLite persistence store.

## Required tooling

| Tool | Version / source | Purpose |
|---|---|---|
| `git` | any | Clone the `cadence` server source. |
| Go toolchain | 1.20+ | Build Cadence binaries (`make bins`). |
| `make` | any | Run Cadence build and schema targets. |
| `jq` | any | The skill `verify.sh` scripts use `jq` for JSON validation. |
| Python | 3.10+ | Run the Cadence Python client and the workflow Worker. |
| `pip` | any | Install `cadence-python-client`. |
| `devin` CLI | installed, on `PATH`, and authenticated (`devin auth status`) | The Activity wrapper shells out to `devin` to run the agentic SDLC skills. |
| `cadence` CLI | built from the Cadence repo, or use the `ubercadence/cli` Docker image | Register the domain, start/signal/query workflows for inspection. |

## Cadence server (embedded SQLite)

```bash
git clone https://github.com/cadence-workflow/cadence.git
cd cadence
make bins
make install-schema-sqlite
./cadence-server --zone sqlite start
```

- Frontend gRPC: `localhost:7833`
- Web UI: `http://localhost:8088`
- The SQLite store is deleted when the process stops unless you mount a persistent data directory.

## Python SDK

```bash
pip install cadence-python-client
```

The workflow, activity, and worker code for this example is written against the `cadence` Python client (`cadence.client`, `cadence.worker`, `cadence.workflow`, `cadence.activity`).

## Domain registration

The `story-analysis` domain must exist before any Workflow is started:

```bash
cadence --do story-analysis domain register -rd 1
```

Verify it:

```bash
cadence --do story-analysis domain describe
```

First-time runs will fail with an `EntityNotExists` error until the domain is registered.

## Running the Worker

1. Set `CADENCE_TARGET` to `localhost:7833`, `DOMAIN` to `story-analysis`, and `TASK_LIST` to `story-analysis`.
2. Run the Worker process that registers the `StoryAnalysisWorkflow` and the four skill Activities.
3. Keep the Worker running while you start workflows from another terminal.

```bash
python src/workflow/story_analysis_worker.py
```

The Worker must be running before a Workflow is started, otherwise the `start_to_close`/`schedule_to_start` timeouts will expire.

## Starting the workflow from the CLI

```bash
cadence --domain story-analysis workflow start \
  --et 3600 \
  --tl story-analysis \
  --workflow_type StoryAnalysisWorkflow \
  --input '{"story_document":"docs/reqs/workflow-orchestration/story.md","config":{"domain":"story-analysis","task_list":"story-analysis"}}' \
  --workflow_id "story-analysis-<story-name>"
```

Use `RejectDuplicate` for the workflow ID reuse policy to avoid accidental duplicate starts.

## Human escalation

When the Workflow waits on a `human_response` Signal, inspect it with:

```bash
cadence --domain story-analysis workflow query \
  --workflow_id "story-analysis-<story-name>" \
  --query_type get_status
```

Send a decision with:

```bash
cadence --domain story-analysis workflow signal \
  --workflow_id "story-analysis-<story-name>" \
  --signal_name human_response \
  --input '{"decision":"accept","notes":"Looks good"}'
```

## `devin` CLI authentication

Every skill Activity shells out to `devin` (`src/orchestrator/devin_harness.py`), so
the Worker's host user must be authenticated *before* starting the engine:

```bash
devin auth status
```

If a browser-based `devin auth login` leaves you flapping between "already logged
in" and "not logged in" (common with session-bridged enterprise/Windsurf tokens —
see `vault/services/orchestrator-harness.md`), use a real, independently-issued
token instead:

```bash
devin auth logout
devin auth login --force-manual-token-flow
```

`scripts/start-workflow-engine.sh` preflights this and fails fast with a pointer
to this fix rather than letting it surface later as a buried `SkillActivityError`
in `scripts/.run/worker.log`.

## Constraints and gotchas

- **No production persistence:** The embedded SQLite server is for local development only. It is not a substitute for Cassandra, MySQL, or PostgreSQL in production.
- **Payload size:** Keep Workflow and Signal payloads small. Pass file paths rather than large story text directly. Cadence Activity/Workflow input limits are roughly 2 MB.
- **Python SDK gaps:** `GetVersion`/SideEffect, async Activity completion, and sessions are not available in the Python SDK. Push non-deterministic data into Activities and avoid hot-patching running Workflow code.
- **Determinism:** Do not use `time.time()`, `datetime.now()`, `random`, or `uuid` inside Workflow code. Use `workflow.sleep()` for delays and `execute_activity` for anything non-deterministic.
- **Idempotency:** Cadence may retry an Activity after a Worker crash. The underlying SDLC skills are already file/JSON based; running the same Activity twice with the same inputs writes the same output paths, which is idempotent as long as prompts are deterministic.
- **First-time use:** If `cadence --do story-analysis domain describe` returns an error, the domain has not been registered.
