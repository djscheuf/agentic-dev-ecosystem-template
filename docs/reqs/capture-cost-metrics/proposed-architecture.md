# Capture Devin Cost Metrics: Proposed Architecture

## Bottom line

Run every non-interactive Devin CLI invocation with `--export <path>`, retain the resulting ATIF trajectory beside the invocation's existing workflow logs, parse its aggregate metrics, and return normalized usage through `HarnessResult`.

Usage collection is observational. A missing, malformed, or partially populated export must not change the Devin invocation's exit code or turn an otherwise successful skill Activity into a failure.

## Status

**Status:** Proposed  
**Date:** 2026-09-04  
**Scope:** Architecture and implementation proposal; no implementation is included.

## Goals

- Capture prompt, completion, cached-token, and monetary-cost metrics reported by Devin CLI.
- Associate each usage record with the workflow, run, Activity, and Devin invocation that produced it.
- Preserve the original ATIF trajectory for audit and future metric extraction.
- Expose normalized usage on the workflow-agnostic `HarnessResult` contract.
- Store structured exports alongside existing workflow-aware logs.
- Preserve existing harness behavior when metrics are unavailable.
- Avoid coupling `common` back to `orchestrator` or to a specific workflow package.

## Non-goals

- Deriving monetary cost from token counts or maintaining a model-pricing table.
- Treating context-window utilization as billed token usage.
- Scraping human-formatted `/usage` or `/session-stats` terminal output.
- Replacing the existing activity and Devin text logs.
- Defining organization-wide billing, quota, or chargeback policy.
- Uploading trajectories or metrics to an external observability service.
- Making successful workflow execution depend on telemetry availability.

## Current state

`common.devin_harness.DevinHarness` runs one non-interactive Devin process and returns only its process result:

```text
devin -p --permission-mode <mode> --model <model> -- <prompt>
```

`common.harness.HarnessResult` contains:

```python
@dataclass(frozen=True)
class HarnessResult:
    exit_code: int
    stdout: str
    stderr: str
```

The current `common.workflow_logger` is workflow-agnostic but only exposes standard Python loggers. It does not retain filesystem paths for the current workflow or Activity, and `get_workflow_log_path()` returns `None`.

The legacy `orchestrator.workflow_logger` already demonstrates the required path-aware pattern. It derives per-execution log directories from Cadence context and tracks paths for Activity, Devin, workflow, and client logs. The workflow-module refactor proposes moving and generalizing that mechanism into `common`.

## Devin CLI metric source

Devin CLI supports:

```text
--export <path>
```

The export is written after each turn in Agent Trajectory Interchange Format (ATIF). ATIF can carry per-step metrics and aggregate `final_metrics`, including:

- `total_prompt_tokens`;
- `total_completion_tokens`;
- `total_cached_tokens`;
- `total_cost_usd`;
- producer-specific fields under `extra`.

Interactive `/usage` and `/session-stats` are useful for manual inspection, but they are not the integration boundary:

- they produce display-oriented output;
- their labels and grouping are server-driven;
- invoking them would require resuming or keeping open the session;
- parsing terminal rendering would be more fragile than parsing ATIF JSON.

The selected source of truth is therefore the exported ATIF document.

## Proposed flow

```text
Skill Activity
    |
    v
common.DevinHarness.run()
    |
    +-- resolve invocation profile
    +-- obtain invocation artifact directory from logging context
    +-- choose devin-trajectory.json export path
    +-- run: devin -p --export <path> ...
    +-- preserve stdout, stderr, and exit code
    +-- parse final_metrics defensively
    |
    v
HarnessResult
    |- exit_code
    |- stdout
    |- stderr
    `- usage
         |- prompt_tokens
         |- completion_tokens
         |- cached_tokens
         |- cost_usd
         `- extra
```

The original trajectory remains on disk for audit. `HarnessResult.usage` is a normalized summary for immediate consumers.

## Artifact layout

Store the export beside the invocation's existing Activity and Devin logs. The exact intermediate directory names remain owned by the generalized workflow logger, but the resulting layout should be equivalent to:

```text
.process/logs/
└── <workflow-id>/
    └── <run-id>/
        └── activities/
            └── <activity-id-or-attempt>/
                ├── activity.log
                ├── devin.log
                └── devin-trajectory.json
```

This provides:

- natural correlation with workflow execution;
- durable inspection after workflow completion;
- isolation between concurrent Activities;
- a place for future structured invocation artifacts;
- no need for a second metrics-specific directory hierarchy.

### Activity retries and multiple invocations

A fixed `devin-trajectory.json` filename is safe only if the logging directory uniquely identifies an Activity attempt and the attempt invokes Devin once.

If either invariant is false, the filename must include a stable invocation discriminator:

```text
devin-trajectory-<invocation-id>.json
```

The implementation must not silently overwrite a prior attempt or concurrent invocation. Prefer a logging context that allocates one artifact directory per Activity attempt. If one Activity intentionally performs multiple harness calls, allocate an invocation sequence or identifier within that directory.

## Common logging contract

`DevinHarness` must not derive paths by editing an `activity.log` or `devin.log` filename. The generalized common logger should expose the containing artifact directory explicitly:

```python
def get_activity_artifact_dir() -> Path | None:
    """Return the current Activity attempt's artifact directory, if available."""
```

The path-aware implementation belongs in `common.workflow_logger` because:

- `common.devin_harness` must not import `orchestrator`;
- workflow packages must not own generic logging mechanics;
- the orchestrator remains responsible for establishing execution context;
- any harness implementation can reuse the artifact directory.

The existing workflow logger migration should preserve the path information currently held by the legacy logger's context bundle and generalize its naming away from Story Analysis.

### Calls outside an Activity context

The harness may also run in tests, diagnostics, or other callers without a workflow-aware Activity context. In that case it should:

1. allocate a temporary directory;
2. request an ATIF export there;
3. parse usage before the temporary directory is removed;
4. return the normalized usage;
5. omit a durable trajectory path.

This keeps usage behavior consistent without forcing every harness caller to initialize workflow logging.

## Harness result contract

Add a workflow-agnostic usage type:

```python
from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class HarnessUsage:
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    cached_tokens: int | None = None
    cost_usd: float | None = None
    extra: Mapping[str, object] | None = None


@dataclass(frozen=True)
class HarnessResult:
    exit_code: int
    stdout: str
    stderr: str
    usage: HarnessUsage | None = None
```

The optional default preserves source compatibility with existing harness implementations, fake harnesses, and tests that construct `HarnessResult` with three fields.

### Field semantics

| Field | Meaning |
|---|---|
| `prompt_tokens` | Aggregate input tokens reported by the trajectory. |
| `completion_tokens` | Aggregate generated tokens reported by the trajectory. |
| `cached_tokens` | Aggregate cached subset of prompt tokens, when reported. |
| `cost_usd` | Monetary cost only when the producer explicitly reports USD. |
| `extra` | Additional aggregate metrics that are safe and useful to retain without renaming. |

Credits and ACUs must not be stored as `cost_usd`. If Devin exports them, retain them under their source names in `extra` until the contract explicitly adds typed fields.

Do not compute `total_tokens` unless a consumer needs it. Cached tokens are generally a subset of prompt tokens, so adding all three values would double-count cached input.

## Devin harness integration

For an invocation with a durable Activity artifact directory:

```python
artifact_dir = get_activity_artifact_dir()
export_path = artifact_dir / "devin-trajectory.json"

command = [
    "devin",
    "-p",
    "--export",
    str(export_path),
    "--permission-mode",
    profile.permission_mode,
    "--model",
    profile.model,
    "--",
    prompt,
]
```

The harness then parses the export after the subprocess exits:

```python
usage = read_atif_usage(export_path)
return HarnessResult(
    exit_code=result.returncode,
    stdout=result.stdout,
    stderr=result.stderr,
    usage=usage,
)
```

The export path should be absolute. This avoids ambiguity because the Devin subprocess runs with the repository root or another caller-supplied directory as its working directory.

## ATIF parsing

Parsing should be isolated in a small function or module rather than embedded in subprocess control flow:

```python
def read_atif_usage(path: Path) -> HarnessUsage | None:
    try:
        trajectory = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None

    metrics = trajectory.get("final_metrics")
    if not isinstance(metrics, dict):
        return None

    return HarnessUsage(
        prompt_tokens=optional_int(metrics.get("total_prompt_tokens")),
        completion_tokens=optional_int(metrics.get("total_completion_tokens")),
        cached_tokens=optional_int(metrics.get("total_cached_tokens")),
        cost_usd=optional_float(metrics.get("total_cost_usd")),
        extra=optional_mapping(metrics.get("extra")),
    )
```

The parser must:

- reject booleans as integers;
- accept an integer USD value and normalize it to `float`;
- tolerate absent aggregate fields;
- tolerate unknown top-level and metric fields;
- avoid logging trajectory contents;
- return `None` for an absent, unreadable, malformed, or structurally invalid export.

A valid but partially populated `final_metrics` may produce a `HarnessUsage` with some fields set to `None`.

## Failure semantics

Usage collection must be best-effort and must preserve the subprocess result.

| Devin result | Export result | Harness behavior |
|---|---|---|
| Success | Valid metrics | Return success with populated usage. |
| Success | Missing or malformed export | Return success with `usage=None`. |
| Failure | Valid metrics | Return Devin failure with populated usage. |
| Failure | Missing or malformed export | Return Devin failure with `usage=None`. |
| Process launch raises `OSError` | No export | Preserve existing `devin_launch_failed` behavior. |

A malformed export should produce a sanitized diagnostic in the Activity log, such as an error category and export path. It must not include raw trajectory content, prompts, credentials, or subprocess output.

## Audit and security

ATIF trajectories can contain conversation text, tool calls, file paths, and other sensitive operational context. They require the same or stronger controls as existing Devin logs.

The implementation must:

- keep trajectories under the configured workflow log root;
- avoid writing trajectories into source-controlled requirement or output directories;
- never copy trajectory contents into Activity logs;
- ensure workflow identifiers are sanitized before becoming path components;
- follow the existing log retention and access policy;
- document that a trajectory is richer and potentially more sensitive than aggregate usage.

If only aggregate metrics are allowed to persist in a deployment, add a configuration option that parses the temporary ATIF export and then removes it. Durable export remains the recommended default for this repository because workflow actions are intended to be auditable and traceable.

## Aggregation boundary

`HarnessResult` carries metrics for one harness invocation. It does not aggregate an entire workflow by itself.

Workflow-level aggregation should occur above the harness boundary by summing completed invocation results or by reading retained trajectories. Aggregation must account for:

- Activity retries;
- multiple Devin invocations in one Activity;
- failed invocations that still incurred usage;
- subagent usage already included or referenced by the exported trajectory;
- missing metrics;
- potentially different models across billed turns.

A workflow report should distinguish `unknown` from zero. Missing usage is not evidence that no tokens or cost were consumed.

## Configuration

The first implementation does not require a new Devin profile setting: ATIF export should be enabled for every `DevinHarness` invocation so usage is consistently available.

If operational needs require configurability later, add a common harness option with explicit semantics, for example:

```json
{
  "devin": {
    "capture_usage": true,
    "retain_trajectory": true
  }
}
```

Do not add configuration until there is a concrete need to disable capture or retention. Defaults should preserve observability.

## Testing strategy

### Harness result tests

- Existing three-argument `HarnessResult` construction remains valid.
- `HarnessUsage` is immutable.
- Missing metrics are represented as `None`, not zero.

### ATIF parser tests

- Complete `final_metrics` populates all normalized fields.
- Partial `final_metrics` populates only available fields.
- Unknown fields are tolerated.
- Producer-specific `extra` is retained.
- Missing file returns `None`.
- Invalid JSON returns `None`.
- Non-object document returns `None`.
- Non-object `final_metrics` returns `None`.
- Boolean token values are rejected.
- Numeric USD values are normalized consistently.

### Devin harness tests

- `--export` and an absolute export path are passed to Devin.
- The existing model and permission arguments remain unchanged.
- A fake runner can write an ATIF document to the supplied export path.
- Parsed usage is returned with stdout, stderr, and exit code.
- A missing or malformed export does not change a successful exit code.
- Usage can be returned for a nonzero Devin exit.
- An Activity artifact directory is preferred when context exists.
- A temporary path is used when no Activity context exists.
- Durable exports are not removed by fallback cleanup.

### Workflow logger tests

- The current Activity artifact directory is available inside its context.
- The accessor returns `None` outside the context.
- Workflow, run, Activity, and attempt path components are sanitized.
- Concurrent Activity contexts produce distinct directories.
- Retry attempts cannot overwrite one another's trajectories.

### Integration characterization

Run one authenticated, low-cost Devin CLI invocation against the installed CLI and inspect the resulting ATIF document. Confirm:

- the export is produced in `--print` mode;
- the actual `schema_version`;
- which `final_metrics` fields Devin populates;
- whether credits or ACUs appear in `extra`;
- whether subagent usage is included in aggregate metrics or represented separately;
- whether a failed turn still writes an export.

The implementation should be based on this characterization rather than assuming every optional ATIF field is populated.

## Implementation sequence

1. Characterize an actual Devin `--print --export` document using a minimal invocation.
2. Complete the path-aware logger migration into `common.workflow_logger`.
3. Add `get_activity_artifact_dir()` and tests for context and attempt isolation.
4. Add the backward-compatible `HarnessUsage` and `HarnessResult.usage` contracts.
5. Add the defensive ATIF usage parser with unit tests.
6. Add export-path selection with durable and temporary modes.
7. Update `common.devin_harness.DevinHarness.run()` to pass `--export` and return parsed usage.
8. Add workflow-level reporting or persistence only after invocation-level capture is verified.

## Acceptance criteria

- Every `common.DevinHarness` invocation requests an ATIF export.
- An invocation inside an Activity logging context retains its trajectory beside that Activity's logs.
- An invocation outside an Activity context still captures usage through a temporary export.
- `HarnessResult` exposes optional normalized prompt, completion, cached-token, and USD-cost metrics.
- Existing harness implementations remain compatible without supplying usage.
- Missing or malformed telemetry never changes the Devin subprocess exit result.
- Concurrent Activities and retries do not overwrite one another's trajectories.
- Raw trajectory data is not copied into normal Activity logs.
- Tests cover parsing, path selection, compatibility, failure semantics, and isolation.

## Open questions

1. Does the installed Devin CLI populate standard ATIF `final_metrics`, or place some billing dimensions under `extra`?
2. Does the export include usage from subagents in aggregate totals?
3. Does the Activity logging layout already isolate Cadence retry attempts after the logger migration is complete?
4. Can one generic skill Activity call the harness more than once per attempt?
5. Should retained trajectories follow a configurable retention period distinct from text logs?
6. Which workflow result or reporting surface should expose aggregate cost after invocation-level metrics are available?
