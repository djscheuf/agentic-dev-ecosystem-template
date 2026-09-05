# Workflow Logging Design

## Bottom line

Every workflow execution produces a set of plain-text log files on disk. The
files are scoped to the Cadence workflow/run and activity, so a failure in the
`devin` CLI, an activity, or the workflow engine can be traced without digging
through a single monolithic worker log.

## Goals

- Capture `devin` subprocess output even when the harness exits successfully.
- Trace the entire workflow execution (worker start, workflow decisions, activity
  invocations, client commands).
- Keep logs on disk in a structure that maps directly to workflow identity.
- Make log levels tunable per log category.
- Avoid contaminating the worker's existing `scripts/.run/worker.log` with
  per-execution detail.

## Log files

Logs are written under the configured `log_root` (default:
`REPO_ROOT/.process/logs`).

| Scope | File path | Level | Contents |
|---|---|---|---|
| Worker | `scripts/.run/worker.log` (via start script redirect) | `INFO` | Worker startup/shutdown/crashes. |
| Workflow | `<log_root>/<workflow_id>/<run_id>/workflow.log` | `INFO` | Workflow start, grade/repair decisions, escalations, terminal status. |
| Activity | `<log_root>/<workflow_id>/<run_id>/activities/<activity_type>_<activity_id>_<attempt>/activity.log` | `DEBUG` | Prompt, harness start/end, sentinel status, path to devin log. |
| Devin | `<log_root>/<workflow_id>/<run_id>/activities/<activity_type>_<activity_id>_<attempt>/devin.log` | `DEBUG` | Full `devin` CLI stdout/stderr. |
| Client | `<log_root>/<workflow_id>/<run_id>/client.log` | `INFO` | Start, signal, query events. |

All path components are sanitized so workflow/run/activity identifiers cannot
escape the log directory.

## Configuration

`src/orchestrator/workflow_logging.config.json` controls the log root and level
per category:

```json
{
  "log_root": ".process/logs",
  "levels": {
    "worker": "INFO",
    "workflow": "INFO",
    "client": "INFO",
    "activity": "DEBUG",
    "devin": "DEBUG"
  }
}
```

- `log_root` may be absolute or relative to the repo root.
- Levels follow Python `logging` names (`DEBUG`, `INFO`, `WARNING`, `ERROR`).
- `STORY_ANALYSIS_LOG_ROOT` env var overrides `log_root` for tests and ad-hoc
  redirection.

## How components log

### Worker

`orchestrator/worker.py` calls `setup_worker_logging()` on startup and logs
through `get_worker_logger()`. The existing `scripts/start-workflow-engine.sh`
redirects stdout/stderr to `scripts/.run/worker.log`, so worker log records
continue to land there.

### Workflow

`StoryAnalysisWorkflow.run()` enters a `workflow_log_context()` and passes the
workflow logger to `StoryAnalysisEngine`. Engine grade/repair/escalation decisions
are logged at `INFO`.

### Activity

`run_skill()` enters an `activity_log_context()`. Inside that context:

- `get_activity_logger()` writes to `activity.log`.
- `get_devin_logger()` writes to `devin.log`.
- `DevinHarness.run()` logs the command, exit code, and duration to the activity
  log and writes the `devin` stdout/stderr to the devin log.
- `activity.log` ends with a line pointing at the corresponding `devin.log`
  path.

`SkillActivityOutput` now carries `activity_log_path` and `devin_log_path` so the
result of an activity can be correlated with its trace.

### Client

`story-analysis-cli` and `run-single-activity` wrap their work in a
`client_log_context(workflow_id, run_id)`. Each start/signal/query writes to
`client.log` under the run directory.

## Code example

```python
from orchestrator.workflow_logger import activity_log_context, get_activity_logger

with activity_log_context():
    get_activity_logger().debug("about to call a slow tool")
```

Outside of a logging context the getters return silent fallback loggers, so unit
tests that do not set a context do not create files or emit warnings.

## Threading and context propagation

The module uses Python `contextvars.ContextVar` to hold the current log bundle.
`activity_log_context()` derives the activity directory from
`cadence.activity.info()` (or an explicit override for tests). Because
`asyncio.to_thread()` copies the caller's context into the worker thread,
`run_skill()` and `DevinHarness` see the same loggers without the activity
functions having to pass a logger through every signature.

## Future work

- Convert plain-text logs to JSON Lines for programmatic replay.
- Add a workflow query that returns the full set of log paths for a run.
- Stream `devin` output in real time with `subprocess.Popen` instead of
  writing it after `subprocess.run` returns.
