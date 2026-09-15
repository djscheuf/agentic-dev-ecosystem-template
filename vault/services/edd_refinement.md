# EDD Refinement ProgressRecord

The `edd_refinement_workflow` persists durable, schema-versioned run state in the target repository under `.process/edd/<run_id>/progress.json`.

- `ProgressRecordStore` provides idempotent `create_or_resume`.
- `ProgressRecordSerializer` enforces the schema version, an explicit field allow-list, and redacts environment variables and credential-bearing paths before writing.
- `ProgressRecordFactory` derives a stable `run_id` from the Cadence workflow run id and the starting Git revision, and refuses duplicate creation.
- `InitializeRunActivity` verifies a successful `PreflightResult`, creates or resumes the progress record, and emits `InitializeRun` or `ResumeRun` events.
- `RunBaselineEvaluationActivity` invokes a pinned evaluation profile through a pluggable harness and records each attempt in the progress record.
- `BaselineResultParser` extracts and validates pass/fail/coverage metrics and failures from structured output.
- `BaselineResultArtifactWriter` writes the baseline result to a repository-relative artifact file.
- `PlanRefinementActivity` produces a `PlanningResult`, choosing `stop` when budgets or the regression limit is exhausted, validating proposed actions against the taxonomy and required-test-case mapping, and flagging `propose_evaluation_expectation_change` for human approval.
- `EddRefinementWorkflow` and `WorkflowModuleSpec` register the workflow and the three Cadence Activities with the orchestrator.
- `EddRefinementWorkflow.run` sequences `initialize_run`, `run_baseline_evaluation`, and `plan_refinement_action`, carrying the `TargetRepositoryContext` and run id through each step.

See [[decisions/ADR-017-agentic-edd-quality-ratchet.md]] and [[decisions/ADR-018-target-repository-context.md]] for background.

## Evaluation expectation approvals (2026-09-14)

- `ProgressRecord` schema version 2 persists the pending approval request and decision history.
- `EddRefinementWorkflow` gates evaluation expectation changes on the first valid matching Cadence signal and treats timeout as no approval.
- Approval decisions bind a stable proposal id to an exact diff hash; only matching approved hashes receive the `human_approved_evaluation_change` context.
- Client helpers send `approve_evaluation_change` and query `get_approval_status`.

## Approval completion details (2026-09-14)

- Replaying approval creation with the same pending proposal returns the original request and preserves its timeout start; conflicting or missing proposal context fails closed.
- Empty evaluation diffs bypass the approval gate, while late decisions after timeout cannot replace the recorded result.
- `python -m edd_refinement_workflow.approval_cli` provides `approve`, `reject`, and `status` commands with workflow, run, and proposal identifiers.
- The `plan_refinement_action` Cadence entrypoint accepts and returns proposal identifiers and diff hashes instead of raising its former placeholder error.

## Scoped candidate execution and validation (2026-09-15)

- `execute_refinement_action` runs the selected action through `DevinHarness` with an explicitly colocated `accept-edits` configuration and returns usage, ATIF path, changed files, and a canonical diff hash.
- Expectation-changing actions fail closed unless the approved hash matches the planned hash.
- `validate_candidate` rejects empty scope, no-op and out-of-scope diffs, malformed metrics, hash mismatches, and required-test weakening or ambiguous modifications.
- Candidate validation results use stable run-and-diff identifiers and append to `candidate_history` under a per-activity persistence lock.
- `EddRefinementWorkflow` resumes persisted candidates without rerunning the harness and exposes `get_candidate_status`.

## Candidate evaluation and quality comparison (2026-09-15)

- ProgressRecord schema version 4 stores the deterministic evaluation configuration, candidate metric attempts, and best accepted state.
- Scope-valid candidates are evaluated with the baseline command, configuration, pinned provider version, timeout, measurement context, and target repository root.
- Malformed metrics are rejected, while runner failures are recorded as infrastructure errors that are unusable for acceptance.
- `compare_candidate_to_best` accepts absolute passing gains without coverage loss, accepts newly required coverage at a stable passing count, requests a rerun for apparent degradation, and keeps different measurement contexts incomparable.
- `FinalizeRunActivity` atomically publishes an idempotent terminal report, restores the best accepted commit through an injected repository operation, and releases the mutation lease through an injected lease operation.
- Cadence wiring for quality decisions and finalization, accepted-candidate commits, concrete regression reruns, and timeout-attempt persistence remain implementation work.

## Ratchet orchestration contracts (2026-09-15)

> **Stale as of 2026-09-15:** The final bullet in the preceding section predates the orchestration-contract slice below.

- Timeout attempts persist as non-acceptance evidence without changing `iteration_history`.
- No-value candidates are rejected deterministically; accepted comparisons route to `commit_accepted_candidate` and update durable best state while resetting the confirmed-regression counter.
- Unchanged confirmation reruns persist separately in `confirmation_evaluations`.
- The workflow module registers candidate commit, degraded rerun, and finalization Activity contracts.
- Concrete deployed Cadence entrypoints, retry-policy configuration, confirmed-regression classification, terminal workflow routing, and frontend status/report views remain implementation work.

## Retry and terminal routing (2026-09-15)

> **Stale as of 2026-09-15:** Retry-policy configuration and terminal workflow routing in the preceding remaining-work list are now implemented.

- Candidate evaluation scheduling converts the configured maximum attempts and initial interval into the Cadence Activity retry policy.
- Apparent degradation routes to `rerun_degraded_candidate` with the unchanged candidate identifier and target repository context.
- A terminal planning decision routes through `finalize_run` before the workflow returns its terminal result.
- Concrete deployed Activity entrypoint dependencies, confirmed-regression classification after rerun, and frontend status/report views remain implementation work.

## Concrete ratchet Activities (2026-09-15)

> **Stale as of 2026-09-15:** Concrete Activity dependencies and confirmed-regression classification in the preceding remaining-work list are now implemented.

- `evaluate_candidate` executes the persisted deterministic command in the target repository and parses structured JSON output.
- `commit_accepted_candidate` stages and commits the target repository, then records the resulting revision as best accepted state.
- `rerun_degraded_candidate` uses the same evaluation command and classifies repeated passing-count degradation as a confirmed regression while incrementing the consecutive counter.
- `finalize_run` restores the accepted revision, attempts lease release, and publishes the idempotent terminal result through repository-scoped dependencies.
- Frontend status and terminal-report views remain implementation work.
