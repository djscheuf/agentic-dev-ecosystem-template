# ADR-009: Colocate `story_analysis_workflow` config with its module

**Date:** 2026-08-31
**Status:** Accepted

## Decision

`src/story_analysis_workflow/config.py`'s `DEFAULT_CONFIG_PATH` now points at
`domain-task-list-retry-config.json` colocated inside the `story_analysis_workflow` package
directory, instead of a path under `docs/`. The JSON file itself was moved from
`docs/reqs/workflow-orchestration/domain-task-list-retry-config.json` to
`src/story_analysis_workflow/domain-task-list-retry-config.json`.

## Rationale

- **The old default path was broken.** `DEFAULT_CONFIG_PATH` was
  `docs/reqs/workflow-orchestration/streams/domain-task-list-retry-config.json`, but the file
  actually lived one directory up, at `docs/reqs/workflow-orchestration/domain-task-list-retry-config.json`
  (outside `streams/`). The path never resolved, so `load_config()` always silently fell back to
  hardcoded/env-var defaults — the on-disk JSON (including `activity_defaults` and `retry_policy`
  values) was never actually read by client code. This ADR closes that gap in addition to moving
  the file.
- **`docs/` should hold requirements/specs, not runtime config.** A module's runtime default
  config is an implementation detail of that module, not a requirement artifact. Mixing the two
  made the dependency direction backwards: code depended on a path inside `docs/`.
- **Precedent in this repo.** `src/orchestrator/devin_harness.py` already colocates its default
  config file (`devin_harness.config.json`) next to the module that reads it, via
  `Path(__file__).resolve().parent / "devin_harness.config.json"`. `config.py` now follows the
  same pattern.

## Implementation

- `config.py`: replaced `REPO_ROOT`-relative `DEFAULT_CONFIG_PATH` with
  `Path(__file__).resolve().parent / "domain-task-list-retry-config.json"`.
- Moved the JSON file via `git mv` into `src/story_analysis_workflow/`.
- No packaging manifest changes needed — this repo has no `pyproject.toml`/`setup.py`; modules run
  directly via `PYTHONPATH=src`, so the colocated JSON is picked up as a plain file on disk.
- Updated `docs/reqs/workflow-orchestration/client-api-usage.md` and
  `vault/services/cadence.md` to reflect the new location.
- Left the historical `docs/reqs/workflow-orchestration/streams/foundations.stream.json` artifact
  list untouched — it's a record of what a past stream produced, not a live reference.

## Trade-offs

**Advantage:** `config.py` is now self-contained (code + its default config in one directory);
the default path is verified to exist and actually loads.

**Disadvantage:** None significant — callers only referenced the file by name/via `load_config()`,
never by hardcoded path.

## Related Decisions

- None yet cross-reference this; see [Cadence service notes](../services/cadence.md#client-api-2026-08-29)
  for how `config.py` is used by `cli.py`/`starter.py`.
