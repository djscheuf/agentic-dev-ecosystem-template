# Handle Agentic EDD Refinement Code Review

## Bottom line

Address every blocking comment from the `feat/agentic-edd-refinement` code review and ensure every terminal workflow branch runs through finalization, producing a terminal record, restoring the best accepted state, and releasing the mutation lease.

## Status

- Requirements captured: 2026-09-30
- Source review: `docs/reqs/agentic-edd-refinement/code-review-feat-agentic-edd-refinement.yaml`
- Target branch: `feat/agentic-edd-refinement`
- Related requirements: `docs/reqs/agentic-edd-refinement/bring-to-ready/requirements.md`, `docs/reqs/agentic-edd-refinement/fix-edd-workflow/requirements.md`

## User story

So that the Agentic EDD Refinement capability can merge

As a maintainer

I want every blocking code-review item resolved and every terminal branch finalized

So that the workflow is durable, target-root correct, budget-enforced, and leaves a clean audit trail on every exit.

## Blocking review items

### CR-01: Schedule preflight as a workflow Activity

**Original comment:** The public workflow signature is `run(preflight_result: PreflightResult, request: dict)` and the CLI executes `resolve_and_validate_target_repository` in the client process before calling `start_workflow`. Requirements state the public input must be the input-document path, that the workflow schedules preflight as an Activity, and that no client constructs trusted repository context on the workflow's behalf.

**Impact:** Violates the "Workflow-owned preflight" contract: preflight is not durable, not retried, not replayed, and its result is trusted client-supplied state. A client crash between preflight and start loses the resolution entirely, and any caller can fabricate a `PreflightResult`. Breaks the replay/resume guarantees the rest of the design assumes.

**Requirement:**

1. Change the workflow signature to accept only the input-document path and an optional workflow ID.
2. Schedule a `preflight` Activity inside the workflow that resolves and validates the target repository.
3. The CLI performs only basic schema sanity-checks before contacting Cadence; it must not resolve or validate the target repository.
4. The workflow derives `TargetRepositoryContext`, the normalized request, and all trusted paths from the Activity result.

**Verification:**

- Workflow tests assert the workflow is started with a document path, not a `PreflightResult`.
- Mock-based tests verify the `preflight` Activity is scheduled and its result is consumed.
- The CLI unit test no longer imports or calls repository-resolution helpers.

**Locations:**

- `src/edd_refinement_workflow/cli.py:75-132`
- `src/edd_refinement_workflow/workflow.py:29-67`
- `src/common/preflight.py:30-150`

### CR-02: Renew the run-lifetime mutation lease

**Original comment:** The mutation-lease TTL is set from `limits.eval_timeout_seconds` (default 1200s) at CLI construction and passed through to `initialize_run`. Nothing in the codebase renews or heartbeats the lease (no renew/extend call exists on `MutationLeaseStore` or the policy handler).

**Impact:** A run that waits on human approval (timeout 3600s) or runs more than a couple of 10-20 minute evaluations outlives its lease, after which a second mutating run can acquire the lease and modify the same worktree concurrently. Breaks AC-8 ("lease remains valid until finalization") and the at-most-one-mutating-run invariant.

**Requirement:**

1. Decouple lease TTL from `eval_timeout_seconds`; define a lease TTL appropriate for the whole run lifetime.
2. Add a renew or extend operation to `MutationLeaseStore`.
3. Have the workflow refresh `dead_by` before lease expiry during waits, retries, and between iterations.
4. Confirm that the lease blocks a second mutating run for the same target until the first run finalizes or the lease genuinely expires.

**Verification:**

- Unit tests simulate a run longer than the original TTL and assert the lease remains held after renewal.
- Unit tests verify a second run is rejected while the first lease is valid.
- Integration tests confirm lease release on every terminal branch.

**Locations:**

- `src/edd_refinement_workflow/cli.py:94`
- `src/edd_refinement_workflow/cli.py:124`
- `src/edd_refinement_workflow/activities/initialize_run.py:96-109`
- `src/common/mutation_lease_store.py:30-51`

### CR-03: Enforce the `max_tokens` budget

**Original comment:** `check_refinement_limits` reads `budgets['token_budget']`, `budgets['hard_token_limit']`, and `budgets['regression_stop_threshold']`, but `record['budgets']` is populated from `profile['limits']`, whose keys are `max_iterations`, `max_tokens`, and `eval_timeout_seconds`. The token-budget and regression-threshold checks therefore never fire; only `max_iterations` is enforced.

**Impact:** A run configured with only `max_tokens` has no effective stop condition besides planning voluntarily choosing `stop` — the cumulative token guardrail the feature advertises is silently absent. Agent spend is unbounded in that configuration.

**Requirement:**

1. Align the checked keys with the input contract (`max_tokens`).
2. Keep regression-threshold checking if a threshold is configured, but do not invent keys not present in the input.
3. Normalize limits into canonical budget keys during `initialize_run` if the checker requires different names.
4. Add tests that seed budgets from the real `limits` shape and assert token-budget exhaustion stops the run.

**Verification:**

- A workflow test with `limits.max_tokens` set to a small value stops the run when cumulative token usage exceeds the limit.
- A workflow test with `limits.max_iterations` set still stops at the iteration limit.
- Tests no longer construct budgets using keys that do not exist in the input contract.

**Locations:**

- `src/edd_refinement_workflow/activities/check_refinement_limits.py:4-36`
- `src/edd_refinement_workflow/activities/initialize_run.py:188`
- `src/edd_refinement_workflow/cli.py:106`

### CR-04: Run baseline evaluation with the correct timeout

**Original comment:** `initialize_run` executes the full baseline evaluation inline via `CheckCandidateActivity.run`, but the workflow schedules `initialize_run` with `start_to_close_timeout=timedelta(minutes=5)` while `eval_timeout_seconds` is expected to accommodate 10-20 minute suites.

**Impact:** For any real evaluation suite, the baseline evaluation exceeds the activity timeout: the workflow either fails during initialize or Cadence retries the whole 20-minute eval under a 5-minute ceiling repeatedly. The baseline requirement ("does not begin refinement if the baseline cannot be evaluated") is unreachable for the suite sizes the input contract anticipates.

**Requirement:**

1. Restore `run_baseline_evaluation` as its own Activity invocation in the workflow.
2. The baseline Activity's start-to-close timeout is derived from `eval_timeout_seconds`.
3. `initialize_run` no longer runs the full baseline inline; it prepares the record and lease, then returns.
4. The workflow schedules baseline evaluation after `initialize_run` succeeds and before the first planning cycle.

**Verification:**

- Workflow tests assert that `run_baseline_evaluation` is scheduled separately from `initialize_run`.
- A test configures `eval_timeout_seconds` longer than 300 and verifies the baseline Activity receives that timeout.
- A baseline that exceeds 300 seconds no longer causes an activity timeout in the workflow.

**Locations:**

- `src/edd_refinement_workflow/activities/initialize_run.py:111-122`
- `src/edd_refinement_workflow/activities/initialize_run.py:228-240`
- `src/edd_refinement_workflow/workflow.py:57-67`
- `src/edd_refinement_workflow/activities/run_baseline_evaluation.py:221-229`

### CR-05: Root `edd_plan` and `edd_do` in the target repository

**Original comment:** `EDD_PLAN_ACTIVITY` and `EDD_DO_ACTIVITY` are module-level singletons constructed with `REPO_ROOT` — `Path(__file__).resolve().parents[3]`, i.e. the orchestration repository where the code is installed. Neither `edd_plan` nor `edd_do` passes `SkillActivityInput.target_context`, so `SkillActivity._repo_root` falls back to this install-location root: prompts, sentinel paths, output paths, and the agent harness `cwd` all resolve against the wrong repository for any target that is not the orchestration repo itself.

**Impact:** Directly violates the invariant "Activity implementations must not retain a process-global repository root selected from their installed source location" and AC-15 (external target run). Self-refinement runs mask the defect because target == orchestration repo; against a separate target repo the agent works in the wrong tree entirely.

**Requirement:**

1. Build the `SkillActivity` (or at least its repo root) from the Activity's `repo_root` argument at invocation time.
2. Populate `SkillActivityInput.target_context` from the workflow's resolved `TargetRepositoryContext`.
3. Ensure prompts, sentinels, output paths, and the harness `cwd` resolve against the target repository, not the orchestration install path.
4. Delete or no longer use the module-level singletons if they cannot be re-targeted per invocation.

**Verification:**

- Add a unit/integration test that creates a scratch Git repo as the target, invokes the real skill-activity path, and asserts the orchestration tree is unchanged.
- Assert that `SkillActivity._repo_root` equals the target repository root during `edd_plan` and `edd_do` execution.
- Verify sentinel paths are created under the target repository, not under the orchestration repository.

**Locations:**

- `src/edd_refinement_workflow/activities/harness_instance.py:20-21`
- `src/edd_refinement_workflow/activities/edd_plan.py:62-64`
- `src/edd_refinement_workflow/activities/edd_plan.py:152-165`
- `src/edd_refinement_workflow/activities/edd_do.py:23-25`
- `src/common/skill_activity.py:93-96`

### CR-06: Add automated external-target proof (AC-15)

**Original comment:** No automated test exercises the workflow against a target repository separate from the orchestration repository (AC-15). All workflow tests mock activities; the real `SkillActivity` path is never run against a foreign `repo_root` — which is why the `harness_instance` `REPO_ROOT` defect is invisible to the suite.

**Impact:** The headline guarantee of the feature — every operation runs against the intended target and the orchestration worktree stays untouched — has no automated evidence and currently fails by inspection.

**Requirement:**

1. Add an end-to-end or integration test that initializes a scratch git repo as the target.
2. Run the skill-activity path (or at minimum verify `cwd`/sentinel/output resolution).
3. Assert the orchestration tree is unchanged after the run.
4. Configure `scratch_globs` for `.process/` so run artifacts do not pollute the target commit.

**Verification:**

- The new test passes and fails if the activity resolves paths against the orchestration repo.
- The test exercises at least one planning or execution iteration against the scratch target.

**Locations:**

- `src/edd_refinement_workflow/tests/test_workflow.py`
- `src/edd_refinement_workflow/activities/harness_instance.py:20`

## Finalize-run requirement

### CR-07: Finalize on every terminal branch

**Original comment:** Several normal terminal branches return from `_run` without calling `finalize_run`: approval rejected, execution failed, candidate rejected by `validate_candidate`, regression handoff (`pending_human_review`), and the `budgets not in record` early return. Only the exception path and the explicit stop/budget branches finalize. Even while early bail-out is accepted, route every exit through a shared finalization step (try/finally or `_finalize` helper) so the terminal record, restore, and lease release happen on every branch.

**Impact:** The run ends with no `terminal.json`, no restore-to-best, and the lease held until TTL expiry, leaving the worktree dirty with the rejected/failed candidate's changes. Audit completeness (AC-14's terminal record) is not met.

**Requirement:**

1. Wrap the workflow body so every terminal branch invokes `finalize_run`.
2. Use a try/finally or `_finalize` helper so exceptions also finalize where the artifact location is writable.
3. `finalize_run` must:
   - restore or confirm the target repository at the best accepted state;
   - publish a `terminal.json` record beside the input document;
   - include baseline and final metrics, coverage, attempts, accepted commits, rejected or reverted proposals, token usage, pending human evidence, and terminal reason;
   - identify the target repository and final accepted revision;
   - release the mutation lease or record release failure;
   - return a serializable workflow result.
4. Ensure the lease is released even when `finalize_run` itself raises by recording the failure in the terminal record rather than aborting.

**Verification:**

- For each terminal branch (approval rejected, execution failed, validation rejected, regression handoff, budget stop, iteration limit, success, exception) assert that `finalize_run` is called exactly once and produces `terminal.json`.
- Assert the lease store reports no active lease after each terminal branch.
- Assert the worktree is restored to the best accepted state (or original baseline if no candidate was accepted).

**Locations:**

- `src/edd_refinement_workflow/workflow.py:190-194`
- `src/edd_refinement_workflow/workflow.py:230-250`
- `src/edd_refinement_workflow/workflow.py:368-384`
- `src/edd_refinement_workflow/finalize_run.py:39-74`

## Acceptance criteria

1. Given the EDD CLI starts the workflow, when the workflow runs, then preflight is scheduled as a durable Activity inside the workflow, not executed in the CLI.
2. Given a run waits for approval or runs multiple long evaluations, when time passes, then the mutation lease is renewed and a second mutating run cannot acquire it.
3. Given a run configured with only `limits.max_tokens`, when cumulative token usage exceeds the limit, then the workflow stops before scheduling another planning cycle.
4. Given a baseline evaluation that takes longer than five minutes, when the workflow runs, then the baseline Activity uses `eval_timeout_seconds` and does not time out.
5. Given an external target repository, when `edd_plan` and `edd_do` run, then all paths and the harness `cwd` resolve inside the target repository.
6. Given the automated test suite, when it runs, then at least one test proves an external target run and asserts the orchestration tree is unchanged.
7. Given any terminal outcome (success, rejection, failure, handoff, budget stop), when the workflow completes, then a `terminal.json` is produced, the lease is released or release failure is recorded, and the worktree is restored to the best accepted state.

## Verification

1. Update existing unit tests for `cli.py`, `workflow.py`, and affected activities to reflect the new signatures and wiring.
2. Add targeted tests for CR-02, CR-03, CR-04, and CR-07.
3. Add the AC-15 external-target integration test described in CR-06.
4. Run the full EDD refinement test suite under `nix-shell` and confirm all tests pass.
5. Run `run_unit_tests.sh` and any lint/typecheck commands required by the repository.
6. Perform a real end-to-end run against a non-orchestration target repository and inspect `terminal.json`, the lease state, and the target worktree.

## Suggested run command

When implementation is complete, run the following to verify the fixes:

```bash
nix-shell --run "python -m pytest src/edd_refinement_workflow/tests/ -v"
```

For the external-target proof, also run:

```bash
nix-shell --run "scripts/kickoff-edd-refinement.sh docs/reqs/agentic-edd-refinement/edd_input.example.json"
```

against a target repository that is not the orchestration repository, and verify that:

- `terminal.json` is created under the input document's `.process/edd/<run-id>/` directory;
- the orchestration repository worktree remains clean;
- the target repository's `.process/` artifacts are excluded from any commit;
- the mutation lease is released after the run completes.
