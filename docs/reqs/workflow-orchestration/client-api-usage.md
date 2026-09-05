# Client API Usage: Story Analysis Workflow

`src/story_analysis_workflow/` is the client-side counterpart to the `StoryAnalysisWorkflow`
implemented in `src/orchestrator/` (see `src/orchestrator/README.md`). It starts runs, sends the
`human_response` Signal, queries `get_status`, and registers the Cadence domain — all without
requiring the `cadence` CLI binary to be installed.

See `docs/reqs/workflow-orchestration/streams/client-api.stream.json` for the implementation plan
this satisfies, and `signal-query-contract.md` / `activity-contracts.md` for the underlying
Signal/Query/Activity contracts.

## Layout

| File | Purpose |
|---|---|
| `config.py` | `CadenceConfig` / `load_config()` — domain, task list, target, timeouts, loaded from `domain-task-list-retry-config.json` (colocated in this module) with env var and explicit-override fallbacks. |
| `starter.py` | `start_story_analysis_workflow()` — starts a `StoryAnalysisWorkflow` execution with a `WorkflowID` derived from the story document's name plus a kickoff-time zettel id. |
| `signals.py` | `send_human_response()` — sends the `human_response` Signal. |
| `queries.py` | `get_status()` — queries the `get_status` Query. |
| `cli.py` | `story-analysis-cli` — `start` / `signal` / `query` / `register-domain` subcommands wrapping the above. |
| `tests/` | Unit tests using a `FakeClient` test double (`tests/fake_client.py`) — no real Cadence server required. |

## Installing and running

From the repo root, inside the Nix dev shell (see `shell.nix` for the `LD_LIBRARY_PATH` fix
`grpcio` needs on NixOS):

```bash
nix-shell --run "python3 -m venv .venv && .venv/bin/pip install -r src/orchestrator/requirements.txt"
```

All commands below assume `PYTHONPATH=src` and a domain already registered (see
`docs/reqs/workflow-orchestration/cadence-local-runbook.md`, or use `register-domain` below).

### Register the domain (first-time use)

```bash
nix-shell --run "PYTHONPATH=src .venv/bin/python -m story_analysis_workflow.cli register-domain --retention-days 1"
```

### Start a run

```bash
nix-shell --run "PYTHONPATH=src .venv/bin/python -m story_analysis_workflow.cli start \
  docs/reqs/workflow-orchestration/story.md"
```

Prints the resolved `workflow_id` and `run_id`. Pass `--workflow-id` to control it explicitly;
otherwise it's derived from the story document's name plus a "zettel id" -- a `YYYYMMDDHHmm`
timestamp (24-hour, local time) taken at kickoff -- e.g. `example_story.md` started at 14:30 on
2026-08-31 becomes `story-analysis-example_story_202608311430`. Each kickoff therefore gets its own
`WorkflowID` (the `RejectDuplicate` reuse policy only guards against two starts for the same story
in the same minute, rather than deduplicating re-runs of the same story like the previous
content-hash id did).

Override the grade-repair loop's bounds with `--max-attempts` / `--escalation-timeout-seconds`.

### Inspect status

```bash
nix-shell --run "PYTHONPATH=src .venv/bin/python -m story_analysis_workflow.cli query <workflow_id>"
```

Prints the `get_status` Query result as JSON: `{step, attempt_count, escalated, escalation_reason,
final_status}` (see `signal-query-contract.md`).

### Respond to a human escalation

```bash
nix-shell --run "PYTHONPATH=src .venv/bin/python -m story_analysis_workflow.cli signal <workflow_id> accept --notes 'Looks good'"
```

`decision` must be one of `retry`, `accept`, or `abort`.

### Overriding domain/task-list/target

Every subcommand accepts `--domain`, `--task-list`, and `--target` before the subcommand name,
e.g. `python -m story_analysis_workflow.cli --domain other-domain query <workflow_id>`. These take
priority over `domain-task-list-retry-config.json` and the `CADENCE_DOMAIN` / `CADENCE_TASK_LIST` /
`CADENCE_TARGET` environment variables.

## Using the `cadence` CLI instead

The official `cadence` CLI (see `.devin/skills/cadence-workflow-orchestration/05-api-and-cli/cli-reference.md`)
works identically against the same domain/task list — the commands in
`docs/reqs/workflow-orchestration/local-dev-prerequisites.md` and `src/orchestrator/README.md`
remain valid. `story_analysis_workflow.cli` exists so a Python-only environment doesn't need the Go
CLI binary installed.

## Testing

```bash
nix-shell --run "PYTHONPATH=src .venv/bin/python -m pytest src/story_analysis_workflow -v"
```

All client-API logic is unit tested against `tests/fake_client.FakeClient`, a test double
recording `start_workflow` / `signal_workflow` / `query_workflow` / `domain_stub.RegisterDomain`
calls — no real Cadence server needed. See `client-api.test-cases.json` for the full test plan.
