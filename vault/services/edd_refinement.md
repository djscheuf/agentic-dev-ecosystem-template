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
- When no `proposed_action` is supplied, `PlanRefinementActivity` auto-selects `repair` if any tests are failing, `add_coverage` when all tests pass but required test-case coverage is incomplete, and stops only when all tests pass with full coverage.
- The stop rationale now explains whether the cause is an exhausted budget, a missing/auto-selected proposal, or an unauthorized action, including the current budget/regression state.
- The workflow finalizer reads the planning result's `rationale` field, so the terminal report shows the actual reason instead of the generic `planning_stopped` default.

- Remaining readiness work includes workflow-owned preflight, start/query CLI support, a kickoff script, and an external-repository Cadence integration test.

## `edd_plan`/`edd_do` skill wiring (2026-09-23)

- The two agentic steps in the loop, previously dummy Python (a hardcoded rule table
  for planning and a raw ad-hoc prompt string for execution — see
  `docs/reqs/agentic-edd-refinement/fix-edd-workflow/requirements.md`), are now real
  skill invocations. `plan_refinement.py` and `activities/execute_refinement_action.py`
  are deleted.
- `activities/edd_plan.py` defines `EddPlanSkillActivity(SkillActivity)` and the Cadence
  activity `edd_plan`, colocated with `edd_plan.config.json`
  (`skill_name: "edd-plan"`, `output_path_key: "plan_path"`, `accept-edits`). It invokes
  `.devin/skills/edd-plan`, pointing it at `.process/edd/<run_id>/progress.json` as the
  anchor input path (so the skill's own sentinel convention nests under
  `.process/edd/<run_id>/.process/`), then reads the `plan.json` the skill wrote to build
  a `PlanningResult`.
- `activities/edd_do.py` defines `EddDoSkillActivity(SkillActivity)` and the Cadence
  activity `edd_do`, colocated with `edd_do.config.json` (same shape, `skill_name:
  "edd-do"`). It invokes `.devin/skills/edd-do` pointed at the current iteration's
  `plan_path` (from `edd_plan`'s output), then measures `git diff`/`git diff --name-only`
  itself to produce the `ExecutionResult` — the skill only edits files, it does not
  report the diff hash.
- Both activities keep their **deterministic** guardrails outside the skill, per
  ADR-017: `EddPlanRunner` still short-circuits to `action: "stop"` on
  iteration/token-budget exhaustion or 3 consecutive confirmed regressions *without*
  invoking the skill; `EddDoRunner` still fails closed on `missing_approval` /
  `diff_hash_mismatch` before invoking the skill.
- Cadence activity names changed: `plan_refinement_action` → `edd_plan`,
  `execute_refinement_action` → `edd_do`. `workflow.py`'s `execute_activity` calls,
  `module.py`'s `ACTIVITY_TYPES`/`ACTIVITIES`, and every test that mocked those names
  (`tests/test_workflow.py`, `tests/test_module.py`) were updated. The old
  `execute_refinement_action.config.json` (which declared a `skill_name` that was never
  actually used, since the old runner built its own prompt) was removed with it.
- **Still open** (see requirements.md "What must be replaced" / "Suggested delivery
  order"): the `guide.md` Setup writer, the `check_candidate` generalization,
  and per-iteration `check.json`/`regression-confirm.json` artifacts are unwritten;
  `edd-decide` was left in place, unreferenced, rather than folded into `edd-plan`.

## `iteration_start_baseline` threading (2026-09-23)

- `edd-plan`'s `plan.json` freezes an `iteration_start_baseline` metrics snapshot at
  Plan time (either the current `best_accepted_state.metrics` or the original
  baseline). `EddPlanRunner` surfaces it verbatim on `PlanningResult`, so it rides
  along in `workflow.py`'s `planning` dict for the rest of that loop iteration.
- `quality_ratchet.resolve_comparison_baseline(planning, best_state, baseline)` is the
  single place that decides what a candidate is judged against: it prefers
  `planning["iteration_start_baseline"]` and only falls back to
  `best_state["metrics"]`/`baseline` when Plan didn't record one (legacy/mocked
  callers). `workflow.py` calls it once per iteration and reuses the result
  (`comparison_baseline`) for `compare_candidate_to_best`, the `rerun_degraded_candidate`
  call, and the reference state passed to regression handling.
- **Why this matters:** without it, a candidate produced this iteration was being
  compared against `best_accepted_state`, which can race ahead of what `edd-plan`
  actually saw when it decided what to try. A candidate that's an improvement over
  what the plan started from but a regression against a *newer* accepted state (or
  vice versa) would be misclassified. Freezing the comparison target at Plan time and
  reusing it through Check/Regression-Confirm fixes that.
- `rerun_degraded_candidate_activity` gained an optional 4th positional arg,
  `iteration_start_baseline`; `RerunDegradedCandidateActivity.run` prefers it over
  reading `best_accepted_state` from the store, falling back to the old behavior when
  omitted (so out-of-workflow callers/tests keep working unchanged).
- `workflow.py`'s regression path builds `regression_reference_state = {**best_state,
  "metrics": comparison_baseline}` (or just `{"metrics": comparison_baseline}` when
  there's no accepted state yet) before calling `_handle_regression`. This keeps
  `best_state["commit"]` intact for `revert_repository_to_best` (which needs an actual
  git commit to reset to — a different concern, still gated on Open Question 1) while
  overriding only the `metrics` used for classification/verification.
- **Deliberately not done:** `iteration_start_baseline` is *not* persisted into
  `.process/edd/<run_id>/progress.json`. It's threaded as a plain function argument
  through the workflow's existing in-memory `planning` value, which is sufficient
  because everything that needs it runs within the same Cadence workflow iteration
  that produced it. If a future activity needs it independent of the live workflow
  (e.g. reading `progress.json` directly, out of process), add it to
  `ProgressRecordSerializer`'s allow-list then — don't do it preemptively.

## `check_candidate` and persisted iteration baseline (2026-09-23)

> **Supersedes the "Deliberately not done" bullet above:** the user decided the
> baseline *should* live in `progress.json`; see below.

- `activities/check_candidate.py` (`CheckCandidateActivity`, Cadence name
  `check_candidate`) is the deterministic Check step. It delegates the
  run/inspect/metrics mechanics to `EvaluateCandidateActivity` (ADR-021 contract
  unchanged), resolves the comparison baseline **from the persisted progress
  record** — `iteration_start_baseline` → `best_accepted_state.metrics` →
  `baseline_metrics` — and returns `{metrics, determination, comparison,
  compared_against, baseline}`.
- It writes `.process/edd/<run_id>/iterations/<n>/check.json` and the
  `.process/check.done.json` sentinel (task, files, determination). Iteration
  number comes from `logical_iteration_count`, falling back to
  `len(candidate_metrics) + 1`.
- `workflow.py` now calls `check_candidate` where it used to call
  `evaluate_candidate` in the main loop, and routes on the returned
  `comparison`/`determination`/`baseline` instead of computing
  `compare_candidate_to_best` itself (in-workflow comparison remains only as a
  fallback for bare-metric/mocked responses). `evaluate_candidate` is still
  registered and still used inside `_handle_regression` for the post-revert
  recovery evaluation.
- `EddPlanRunner` now persists `plan.json`'s `iteration_start_baseline` into
  `progress.json` right after a successful Plan (user decision: write it to the
  progress record, load it from file where needed). It is still *not* in
  `ProgressRecordSerializer.for_v5`'s allow-list — fine today since that
  serializer isn't on the save path, but it will be silently dropped if a
  round-trip path ever uses it.
- **Commit/revert policy decided (2026-09-23):** git-history approach. Accepted
  candidates are committed via `commit_accepted_candidate`; Revert restores with
  `git reset --hard <best_accepted_state.commit>` (existing
  `revert_repository_to_best` semantics), not `git checkout -- <files>`.

## Setup context document and baseline unification (2026-09-23)

- `initialize_run` is now the single Setup step. It runs the baseline evaluation as
  iteration 0 via `CheckCandidateActivity`, writes
  `.process/edd/<run_id>/iterations/0/check.json`, and stores the metrics as
  `baseline_metrics` in the progress record.
- `initialize_run` also writes the workflow-level historical document
  `refinement.yaml` under `.process/edd/<run_id>/`. It embeds the original
  `edd_input` object, the baseline metrics, the closed action taxonomy, and an
  empty `iterations:` list that each Plan/Do/Check cycle will append to.
- `workflow.py` no longer calls `run_baseline_evaluation` as a separate activity;
  it reads `baseline_metrics` from the progress record populated during Setup.
- `cli.py` threads the original input path, its parent directory, and the parsed
  `edd_input` object into the workflow request so that Setup and `edd-plan` know
  where to write artifacts and sentinels.
- `activities/edd_plan.py` now invokes the `edd-plan` skill with
  `refinement.yaml` as its primary context document plus `progress.json` for
  runtime state. An `input_parent` override lets the completion sentinel land in
  the `.process` directory next to the original EDD input file, per the revised
  sentinel convention.
- `ProgressRecordSerializer.for_v5` allow-list updated: `iteration_start_baseline`
  added, `attempt_records` renamed to `attempts`.
- `activities/check_candidate.py` iteration numbering fixed so
  `logical_iteration_count == 0` produces `iterations/0/check.json` instead of
  falling through to 1.

Still open: simplify workflow approval routing (route directly to `edd-do`
unless the action is `propose_evaluation_expectation_change`), ensure `edd-do`
records `do.json` and appends "changes made" to `refinement.yaml`, remove
sentinel expectations from deterministic activities, and run end-to-end
validation against the `grade-story-design` eval suite.

## Artifact trail, limits, and outcome logging (2026-09-24)

- `EddDoRunner` writes `iterations/<n>/do.json` (the `ExecutionResult` shape:
  changed files, diff hash, usage metrics, duration) next to `plan.json` after
  measuring the diff, on both success and harness-failure paths.
- `PlanningResult.usage_metrics` propagates the edd-plan skill's token spend;
  `workflow.py` folds it into `cumulative_token_usage` and re-runs
  `check_refinement_limits` immediately after Plan, so a budget-exhausting plan
  routes to `finalize_run` without invoking `edd_do`.
- `refinement_log.append_refinement_outcome` is the shared append point for
  deterministic outcomes: `record_confirmed_regression`,
  `record_reverted_proposal_context`, `human_handoff`, and
  `commit_accepted_candidate` each append an `outcomes` event to the current
  iteration's section of `refinement.yaml`. It is a no-op when the run has no
  refinement.yaml.
- `record_reverted_proposal_context` also appends the reverted candidate to
  `candidate_history` with status `reverted` — every candidate now has a final
  state (`accepted` / `rejected` / `reverted`).

Still open: end-to-end validation of the full loop against the
`grade-story-design` eval suite.
