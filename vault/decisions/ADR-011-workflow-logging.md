# ADR-011: Workflow-Aware File Logging for the Story Analysis Orchestrator

**Date:** 2026-09-02
**Status:** Accepted

## Decision

Add a `src/orchestrator/workflow_logger.py` module and an orchestrator-level
`workflow_logging.config.json` that creates plain-text log files scoped to the
current Cadence workflow, run, and activity.

- **One file per activity.** Each activity invocation writes to its own
  `activity.log`.
- **Separate devin log.** `DevinHarness` writes the `devin` CLI stdout/stderr to
  a sibling `devin.log`. The `activity.log` records the path to `devin.log`.
- **Workflow log.** `StoryAnalysisWorkflow`/`StoryAnalysisEngine` write
  workflow-level events (grade/repair decisions, escalations, terminal status)
  to a `workflow.log` per run.
- **Client log.** `story-analysis-cli` and `run-single-activity` write start,
  signal, and query events to a `client.log` per run.
- **Worker log preserved.** `scripts/.run/worker.log` remains the capture point
  for worker startup, shutdown, and crashes.
- **Configurable levels.** The config file sets per-category levels
  (`worker`, `workflow`, `client`, `activity`, `devin`).

## Rationale

- `DevinHarness` previously captured `stdout`/`stderr` only on non-zero exit,
  and discarded it on success. Intermittent failures during end-to-end runs
  were hard to diagnose because the harness output was lost.
- A single `scripts/.run/worker.log` mixes output from many concurrent workflow
  executions. Per-execution files let an operator trace one workflow without
  parsing interleaved records.
- `cadence.activity.info()` provides `workflow_id`, `workflow_run_id`,
  `activity_type`, `activity_id`, and `attempt`. Using these as directory
  components gives a natural, correlation-friendly layout.
- `asyncio.to_thread()` copies `ContextVar`s, so a context-manager-based logger
  works inside the activity thread pool without changing the `Harness` Protocol
  or every test double.

## Consequences

- **Positive:** Full traceability of devin output, activity life cycle, workflow
  decisions, and client commands; tunable verbosity; tests can redirect logs
  via `STORY_ANALYSIS_LOG_ROOT`.
- **Negative:** Additional disk writes per workflow execution; log directories
  must be ignored by git (covered by `.process/.gitignore` `*.log`).
- **Neutral:** The `Harness` Protocol does not change; `DevinHarness` simply
  calls `get_activity_logger()`/`get_devin_logger()` when a context is active.

## Implementation

- `src/orchestrator/workflow_logger.py` — `WorkflowLoggerConfig`,
  `activity_log_context()`, `workflow_log_context()`, `client_log_context()`,
  `get_*_logger()` / `get_*_log_path()` helpers, `setup_worker_logging()`,
  `get_worker_logger()`.
- `src/orchestrator/workflow_logging.config.json` — default log root and levels.
- `src/orchestrator/devin_harness.py` — logs command, exit code, duration to
  `activity.log`; writes devin stdout/stderr to `devin.log`.
- `src/orchestrator/skill_activity.py` — enters `activity_log_context()` and
  returns `activity_log_path` / `devin_log_path` in `SkillActivityOutput`.
- `src/orchestrator/story_analysis_engine.py` — accepts an injected logger and
  logs grade/repair/escalation events.
- `src/orchestrator/workflow.py` — enters `workflow_log_context()` and passes the
  workflow logger to the engine; `get_status` query includes
  `workflow_log_path` when available.
- `src/orchestrator/worker.py` — calls `setup_worker_logging()` and logs worker
  startup.
- `src/story_analysis_workflow/starter.py`, `cli.py`, `run_single_activity.py`
  — wrap client operations in `client_log_context()`.
- `tests/` — `conftest.py` files redirect logs to `tmp_path` during tests;
  `test_workflow_logger.py` covers config, context managers, sanitization, and
  worker setup.

## See also

- [Workflow Logging design doc](../../../docs/reqs/workflow-logging/design.md)
- [Orchestrator harness notes](../services/orchestrator-harness.md)
