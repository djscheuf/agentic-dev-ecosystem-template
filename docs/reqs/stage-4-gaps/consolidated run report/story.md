# Produce a Consolidated Story Analysis Run Report

## Story

So that certification evidence and workflow reliability can be reviewed without reconstructing runs from scattered logs
As a Story Analysis Workflow certification owner
I want each terminal workflow run summarized in one structured report and included in an auditable success-rate aggregate

## Entry Outcome

A terminal workflow run has correlated workflow, activity, attempt, and available usage data ready for consolidation.

## Scope

### In Scope

- Write one schema-versioned `{workflow}.report.json` for each terminal workflow run.
- Include run metadata: `workflow_id`, `run_id`, `story_document`, `final_status`, `attempt_count`, and terminal outcome origin.
- Include one ordered record for every executed activity attempt.
- Include step name, activity type, attempt, model, permission mode, duration, output path, and available prompt, completion, and cached token totals.
- Include `cost_usd` when supplied by the supported usage source; otherwise represent cost as unavailable without estimating it.
- Preserve and reference raw ATIF evidence rather than replacing it.
- Distinguish automated failure, human accept, human abort, and other human-resolved outcomes.
- Avoid treating a partial or malformed report as complete evidence.
- Aggregate visible reports into end-to-end status counts and success-rate metrics without counting retries as independent workflow runs.
- Publish the aggregation formula, numerator, denominator, sample window, and manual-intervention count alongside the result.

### Out of Scope

- Changing the Devin billing contract or introducing a model price table.
- Parsing subagent-level usage from ATIF.
- Log retention or deletion policy.
- Building a graphical dashboard.
- Startup or between-step guardrails.
- Ambiguity punch-out and signal authorization.
- Per-agent Stage 3 quality remediation or certification evidence.

## Acceptance Criteria

- Given a workflow reaches a terminal state, when completion processing finishes, then exactly one schema-valid report exists for its `workflow_id` and `run_id`.
- Given a run contains retries, when the report is read, then every activity attempt appears once in execution order and retry attempts are not collapsed or double-counted.
- Given usage metrics are available in ATIF, when the report is written, then prompt, completion, and cached token totals match the source data and the raw ATIF artifact remains available.
- Given `cost_usd` is absent from ATIF, when the report is written, then cost is explicitly unavailable and no estimated value is invented.
- Given the run ends through automated failure, human accept, or human abort, when the report is read, then the final status and outcome origin distinguish those paths.
- Given report generation is interrupted, when evidence is inspected, then no truncated report is accepted as complete and rerunning completion for the same run produces one valid result.
- Given concurrent workflows and activity retries, when their reports are generated, then records remain isolated by workflow, run, activity, and attempt.
- Given a set of visible reports, when aggregation runs, then it publishes status counts, the defined success formula, numerator, denominator, sample window, and manual-intervention count, with each observation traceable to one report.
- Given retries occur within a run, when the success rate is calculated, then the run contributes at most one observation to the denominator.
- Automated tests cover passed, repaired, human-accepted, human-aborted, and automated-failure reports, missing usage fields, partial writes, retries, and concurrent runs.

## Metric Decision Required Before Implementation

The certification owner must select and document the authoritative primary success formula and target threshold. At minimum, the aggregate must report fully automated passes separately from human-resolved runs so the result does not hide manual intervention.

## Dependencies

- Existing attempt-scoped workflow logging and artifact paths.
- Existing `HarnessUsage` and raw Devin ATIF export support.
- Stable workflow terminal statuses and explicit terminal outcome origins.
- A report JSON Schema and deterministic report location.
- Certification-owner decision on sample window, representative workload, primary success formula, and threshold.

## Exit Outcome

Every terminal run is independently auditable from one report, and a collection of reports yields a reproducible end-to-end success metric without fabricated cost data.
