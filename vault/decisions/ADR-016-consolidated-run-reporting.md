# ADR-016: Consolidated Story Analysis Run Reporting

**Status:** Proposed
**Date:** 2026-09-08
**Author:** Project team

## Bottom line

Produce one atomic, schema-versioned report per terminal Story Analysis workflow execution and derive explicit-window success aggregates from visible reports.

## Context

Certification owners currently reconstruct a run from workflow logs, Activity-attempt artifacts, ATIF exports, and terminal results. Retries, human resolution, missing cost, and interrupted writes make that reconstruction difficult to audit consistently.

The detailed design is in `docs/reqs/stage-4-gaps/consolidated run report/produce-consolidated-story-analysis-run-report.design.json`.

## Decision

- Keep report models, writing, and aggregation in `story_analysis_workflow`; keep generic attempt telemetry and artifact layout in `common` per [[ADR-013-three-layer-workflow-module-architecture]].
- Store `story-analysis.report.json` in the existing sanitized workflow/run artifact directory established by [[ADR-011-workflow-logging]].
- Validate complete documents and publish reports and aggregates by atomic same-filesystem replacement. The final filename is the completeness marker and repeated completion is idempotent by `workflow_id` plus `run_id`.
- Preserve every Activity retry as an ordered attempt observation inside one run report. Aggregation counts each workflow execution once.
- Represent usage availability explicitly. Never estimate missing cost, consistent with [[ADR-015-devin-cost-metric-scope]].
- Define `automated_pass_rate_v1` as automated or repaired passes divided by all included terminal runs. Human accept and abort are separately visible and both count as manual intervention. Empty samples publish a null rate.
- Aggregate only schema-compatible final reports beneath an explicit local root and within an explicit UTC sample window. Incompatible schemas are excluded with reason counts, not silently migrated.
- Do not publish a certification threshold verdict until product ownership defines the threshold.

## Consequences

### Positive

- One report provides traceable evidence for each terminal run.
- Atomic publication prevents truncated reports from appearing complete.
- Formula operands, exclusions, and report references make aggregate results reproducible.
- Retry attempts remain visible without inflating run-level reliability metrics.

### Negative

- Workflow completion now depends on successful report validation and filesystem publication.
- Filesystem discovery remains bounded by local artifact visibility and existing retention behavior.
- Attempt metadata must be carried from the Activity boundary instead of reconstructed later.

### Neutral / Follow-up

- Retention remains outside this feature.
- Startup rejection and unmodeled cancellation need separate explicit evidence contracts before inclusion.
- Schema migration and certification thresholds require later decisions.

## Alternatives Considered

- **Reconstruct reports from text logs after completion** — rejected because typed attempt facts and terminal origins are lost or ambiguous.
- **Store report state in a new database** — rejected because current evidence is filesystem-based and the story does not require a new service.
- **Estimate cost from token counts** — rejected because estimates are not authoritative ATIF evidence.
- **Count Activity attempts in the success denominator** — rejected because end-to-end reliability is measured per workflow execution.

## Implementation status — 2026-09-08

The initial unit-level reporting domain is implemented in `story_analysis_workflow.reporting`:

- terminal engine results distinguish automated pass, repaired pass, timeout, human accept, and human abort origins;
- run-report construction orders attempt observations and totals independently available usage fields;
- report publication uses sanitized run paths and atomic replacement;
- aggregation filters an explicit UTC window, rejects incompatible or malformed reports, deduplicates workflow/run identity, and publishes auditable operands;
- report and aggregate publication share the same atomic JSON writer.

Workflow Activity plumbing, Cadence completion publication, CLI exposure, and standalone JSON Schema files remain follow-up integration work.

## Integration status — 2026-09-08

The workflow now publishes through a registered Cadence Activity after reaching a modeled terminal outcome. Successful publication adds `report_path` to the workflow result and status query; publication failure prevents reported completion. If no root is supplied, the Activity uses the configured workflow artifact/log root.

Skill Activity successes carry structured attempt identity, invocation profile, artifact references, duration, and independently available ATIF usage into the workflow ledger. V1 report and aggregate JSON Schemas validate documents before atomic publication. The CLI exposes explicit-root, explicit-UTC-window aggregation.

Capturing observations from every Cadence-managed failed retry remains follow-up work because failed Activity return values are not delivered to workflow code; it requires a durable attempt-side evidence handoff rather than reconstructing facts from text logs.

## Republish identity invariant — 2026-09-08

A report reconstructed from existing attempt observations uses their shared `workflow_id` and `run_id`, not the identity of the Activity currently performing publication. This permits an idempotent republish from a helper workflow while preserving the original execution identity. Mixed observation identities still fail report construction, so republishing cannot combine evidence from different runs.
