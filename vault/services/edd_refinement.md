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

## Regression recovery (2026-09-15)

- ProgressRecord schema version 5 initializes regression evidence, reverted proposal, recovery result, and human handoff collections.
- Dedicated recovery Activities classify confirmation evidence, restore the accepted revision, verify exact recovery metrics, persist redacted reverted-proposal context, and record notification attempts.
- Confirmed regressions increment and check the stop threshold before restore; non-confirmed evidence routes to human review.
- The workflow exposes `get_regression_status` with classification, recovery, reverted-proposal, and handoff state for presentation clients.

## Durable refinement limits (2026-09-15)

- New runs persist configured iteration, token, hard-token, and regression budgets with zeroed logical-iteration, cumulative-token, pending-evidence, and attempt state.
- `check_refinement_limits` returns stable iteration, token, hard-limit, regression-threshold, and pending-evidence scheduling decisions while preserving the best accepted state.
- `update_durable_counters` records every Activity attempt and its token usage, including retries, while only non-retries advance the logical iteration count; missing usage is recorded as zero with an explicit marker.
- The workflow checks configured limits before its first agentic step and finalizes immediately when blocked.
- Structured regression-threshold handoff reports include the best accepted state, durable counter summary, and the three latest regression attempts.
- The limit, counter, and structured handoff Activities are registered in the EDD refinement worker module.

## Limit completion coverage (2026-09-15)

- Regression evidence flags are durable and clear only after resolution.
- The third confirmed regression routes directly to structured handoff publication without another restore or evaluation.
- Counter updates on a shared Activity instance are serialized so concurrent completions do not corrupt or lose attempt state.

## Workflow-wide limit enforcement (2026-09-15)

- Candidate evaluation propagates provider usage, retry identity, and logical iteration context into its durable metric result when the provider reports them.
- The workflow accounts execution and evaluation results, then reruns the centralized limit gate before scheduling subsequent autonomous work.
- A post-Activity limit stop finalizes with the preserved best accepted state and does not schedule the next step.

## Bring-to-ready contract (2026-09-15)

- Readiness requirements are captured in `docs/reqs/agentic-edd-refinement/bring-to-ready/requirements.md`.
- The public JSON input anchors repository discovery at `skill_folder`; relative paths resolve from the input document parent, and progress is written under `<input-parent>/.process/edd/<run-id>/`.
- The target repository supplies `eval_config`, argv-based `test_command` and `inspect_command`, structured required test cases, and a configurable metadata property for coverage IDs. Provider identity is derived and validated from the evaluation configuration rather than duplicated in the input.

## Multi-iteration workflow loop (2026-09-15)

- `EddRefinementWorkflow.run` now loops over `plan_refinement_action`, `execute_refinement_action`, `validate_candidate`, and `evaluate_candidate`.
- `check_refinement_limits` runs before each planning cycle; a stop decision immediately finalizes the run.
- Durable counters are updated after `execute_refinement_action` and `evaluate_candidate`, and the returned progress record is reused by the workflow and the next `plan_refinement_action`.
- `compare_candidate_to_best` compares against the baseline when no `best_accepted_state` exists, and against the accepted best on subsequent cycles.
- Accepted candidates are committed through `commit_accepted_candidate` and the updated best state is written back into the in-memory progress record, so the next planning cycle sees the latest accepted commit.
- See [[decisions/ADR-019-edd-multi-iteration-loop.md]] for the rationale.

## Planning budget derivation and action proposal (2026-09-22)

- `PlanRefinementActivity` derives the remaining iteration budget from `budgets.max_iterations - logical_iteration_count` when an explicit `budgets.remaining_iterations` is not present.
- The workflow stops after the baseline unless the input document or an external caller provides a `proposed_action` (e.g. `add_coverage` or `propose_evaluation_expectation_change`); the stop rationale now explains whether the cause is an exhausted budget, a missing proposal, or an unauthorized action.
- The workflow finalizer reads the planning result's `rationale` field, so the terminal report shows the actual reason instead of the generic `planning_stopped` default.

- Remaining readiness work includes workflow-owned preflight, start/query CLI support, a kickoff script, and an external-repository Cadence integration test.
