# Fix Dead Duplicates and Remaining Refactor Gaps

## Bottom line

`common` now owns the live harness, skill-activity, and workflow-logging implementations.
The old `orchestrator` versions are dead duplicates. This document lists the files to
remove and the small behavior/coverage gaps to close before the refactor is complete.

## Dead duplicates to remove

### Core modules

- `src/orchestrator/harness.py` — old `Harness` protocol; `common/harness.py` is the live
  contract (`HarnessUsage`, `config` param).
- `src/orchestrator/devin_harness.py` — old `DevinHarness`; `common/devin_harness.py` is
  live (ATIF `--export`, stdout/stderr capture, `HarnessUsage`).
- `src/orchestrator/skill_activity.py` — old skill-activity wrapper; `common/skill_activity.py`
  is live.
- `src/orchestrator/workflow_logger.py` — old logger; `common/workflow_logger.py` is live.
- `src/orchestrator/invocation_context.py` — identical to `common/invocation_context.py`.
- `src/orchestrator/skill_activity_config.py` — identical to `common/skill_activity_config.py`.

### Config files

- `src/orchestrator/devin_harness.config.json` — only consumed by the dead
  `orchestrator/devin_harness.py`.
- `src/orchestrator/workflow_logging.config.json` — only consumed by the dead
  `orchestrator/workflow_logger.py`.

### Tests

- `src/orchestrator/tests/test_devin_harness.py`
- `src/orchestrator/tests/test_skill_activity.py`
- `src/orchestrator/tests/test_workflow_logger.py`

These test the dead `orchestrator` modules; any behavior still worth keeping should be
ported to `common/tests` first.

### Stale documentation

- `src/orchestrator/README.md` — references removed paths (`orchestrator/activities/`,
  `orchestrator/story_analysis_engine.py`, etc.).
- `vault/services/orchestrator-harness.md` — references `src/orchestrator/activities/*.py`
  which no longer exist; the activities live in `src/story_analysis_workflow/activities/`.

## Behavior gaps to close in `common`

1. **Global Devin config file**

   `orchestrator/devin_harness.config.json` supported `defaults` and per-skill `skills`
   overrides. `common/devin_harness.py` only accepts a per-call `config` mapping from the
   Activity's `.config.json`. Either port the file-based override behavior to `common` or
   ensure every Activity `.config.json` carries the needed `harness.devin` settings.

2. **Prompt output-directory instruction**

   `orchestrator/skill_activity.py` `_build_prompt` instructed the harness to write the
   output file in the same directory as the first input path. `common/skill_activity.py`
   `build_prompt` omits this line. If the instruction matters for `devin` behavior, add it
   to `common`.

3. **Extensibility hooks and `run_skill` helper**

   `orchestrator/skill_activity.py` provided `modify_*` hooks and a `run_skill()` helper.
   `common/skill_activity.py` has neither. They are not used by `story_analysis_workflow`
   today, but any external callers depending on them will break.

4. **Config file wiring for `common` logging**

   `common/workflow_logger.py` looks for `src/common/workflow_logging.config.json`, which
   does not exist, so it falls back to hardcoded defaults. The existing
   `src/orchestrator/workflow_logging.config.json` is ignored. Move or copy the config
   file to `src/common/workflow_logging.config.json` so `WorkflowLoggerConfig.load()`
   uses it.

5. **Worker logging setup API**

   `common` provides `worker_log_context`/`get_worker_logger` (LoggerAdapter).
   `orchestrator/workflow_logger.py` provided `setup_worker_logging()` and a plain
   `get_worker_logger()`. `orchestrator/worker.py` and `orchestrator/runtime.py` currently
   use `common`, so `setup_worker_logging` is unused. Decide whether it is still needed;
   if so, port it to `common` and call it from `orchestrator/worker.py`.

## Test coverage gaps in `common`

- `common/tests/test_workflow_logger.py` does not exercise `workflow_log_context`,
  `client_log_context`, `get_workflow_log_path`, or `get_client_log_path`.
- `common/tests/test_devin_harness.py` does not assert that `stdout`/`stderr` are
  captured to `devin.log`.
- `common/tests/test_skill_activity.py` does not assert `activity_log_path`/
  `devin_log_path` in `SkillActivityOutput` or the creation of `activity.log`/
  `devin.log`.

## Verification

- `nix-shell --run ".venv/bin/python -m pytest src/common/tests src/orchestrator/tests src/story_analysis_workflow/tests"` passes (184 tests as of this writing).
- A live workflow run now produces the expected log tree under
  `.process/logs/<workflow_id>/<run_id>/` with `workflow.log`, `client.log`, and
  `activities/<activity_type>_<activity_id>_<attempt>/{activity.log,devin.log,devin-trajectory.json}`.
