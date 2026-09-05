# ADR-015: Devin Cost Metric Capture Scope

**Status:** Accepted
**Date:** 2026-09-04
**Author:** Project team

## Bottom line

Export raw ATIF for every Devin harness invocation and normalize only standard aggregate metrics. For now, treat ATIF totals as inclusive of subagent usage.

## Context

Devin CLI may emit an additional billing dimension whose stable normalized contract is not yet known. Cost capture must proceed without losing that information or blocking on exact subagent semantics.

The existing Activity logging layout isolates Cadence attempts, and each Skill Activity calls the harness once per attempt. The PathAware logger and affected Devin/harness integrations still need to complete their migration into `common` as part of this story.

## Decision

- Always request and retain the raw ATIF export.
- Normalize only supported standard aggregate metrics on `HarnessResult.usage`.
- Preserve additional billing dimensions in raw ATIF rather than adding them to the normalized contract in this story.
- Assume exported aggregate totals include subagent usage; do not parse subagent-level usage.
- Use the existing Cadence attempt-scoped logging layout; one Skill Activity harness call produces one export per attempt.
- Include the PathAware workflow logger migration to `common`, plus Devin/harness migration where necessary, in this story.
- Exclude log retention; another service owns it.
- Defer cost fields on Skill Activity results and workflow-level aggregation. A future workflow aggregate is the sum of Activity aggregates across the workflow call.
- Use the existing local Cadence stack and worker runtimes for verification.

## Consequences

### Positive

- Cost capture can proceed despite possible additional billing dimensions.
- Raw ATIF preserves data needed for future billing-contract changes.
- The normalized result remains small and stable.
- Existing retry-attempt isolation avoids a new invocation discriminator.

### Negative

- Subagent inclusion is an explicit assumption until Devin export behavior is characterized.
- Consumers cannot access additional billing dimensions through `HarnessResult.usage` yet.

### Neutral / Follow-up

- Add cost reporting to Skill Activity result objects later.
- Add workflow-level aggregation after Activity-level reporting exists.
- Revisit normalized billing fields if Devin establishes a stable additional dimension.

## Alternatives Considered

- **Block on complete Devin billing semantics** — rejected because raw ATIF preserves unknown dimensions safely.
- **Normalize every field under `final_metrics`** — rejected because it would make the result contract depend on unstable or vendor-specific dimensions.
- **Implement retention here** — rejected because retention belongs to another service.

## Logging infrastructure status (2026-09-04)

- `common.workflow_logger.activity_log_context` creates `activity.log` and `devin.log` in a sanitized workflow/run/Activity/attempt directory.
- `get_activity_artifact_dir()` exposes that directory only while the Activity context is active and returns `None` without one.
- Activity IDs and retry attempts select distinct directories, so their artifacts do not overwrite one another.
- The NixOS unit entry point passes 190 tests after the logging infrastructure increment.
