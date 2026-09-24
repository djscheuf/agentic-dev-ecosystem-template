# Fix the EDD Refinement Workflow — Requirements & Analysis

## Bottom line

> **Status update (2026-09-23):** the two dummy activities described below have been
> replaced. `edd_plan` (backed by `.devin/skills/edd-plan`) and `edd_do` (backed by
> `.devin/skills/edd-do`) are real `SkillActivity` subclasses, colocated-config,
> wired into `EddRefinementWorkflow` and `module.py`. `plan_refinement.py` and
> `execute_refinement_action.py` are deleted. `iteration_start_baseline` is threaded
> through Plan→Check→Regression-Confirm and is persisted to `progress.json`.
>
> **New decisions made in this revision:**
> - The *guiding document* is **not** a standalone `guide.md`. Instead, the Setup
>   activity initializes a single workflow-level historical document,
>   `refinement.yaml`, under the run's process folder, and embeds the original
>   `edd_input` object inside it. `edd-plan` reads `refinement.yaml` as its primary
>   context.
> - **Sentinels are only required for agentic skill invocations** (`edd-plan`,
>   `edd-do`). Deterministic activities (`initialize_run`, `check_candidate`,
>   regression confirmation, commit, revert) do **not** write sentinels. `check_candidate`
>   may continue to write `check.done.json` for observability, but that is optional.
> - The running historical document is `refinement.yaml`, matching the `edd-plan`
>   skill's existing convention. `plan.md` is no longer used.
> - The approval flow is simplified: any `edd-plan` action other than
>   `propose_evaluation_expectation_change` routes straight to `edd-do`. Only
>   expectation-change proposals require human approval.
> - The progress record uses the `attempts` field everywhere; `attempt_records` is
>   being retired. `iteration_start_baseline` will be added to
>   `ProgressRecordSerializer.for_v5`'s allow-list.
>
> **Status update (2026-09-23, second revision):** the Setup context-document
> writer has shipped — `initialize_run` now runs the baseline evaluation as
> iteration 0 (`iterations/0/check.json`) and initializes
> `.process/edd/<run_id>/refinement.yaml` embedding `edd_input`, baseline metrics,
> and the action taxonomy. `edd_plan` reads `refinement.yaml` + `progress.json`
> and places its sentinel next to the original EDD input file. The
> `attempt_records`→`attempts` rename and the `iteration_start_baseline`
> serializer allow-list entry are done, and approval routing is simplified —
> only `propose_evaluation_expectation_change` proposals gate on human approval;
> everything else routes straight to `edd_do`.
>
> Still open: the first real end-to-end run of the full loop against the
> `grade-story-design` eval suite.
>
> **Status update (2026-09-24):** three more gaps closed — `edd_do` now writes
> per-iteration `iterations/<n>/do.json` (the `ExecutionResult` shape) after
> measuring the diff; `edd_plan`'s token usage is propagated via
> `PlanningResult.usage_metrics` and `check_refinement_limits` re-runs before
> `edd_do`; and deterministic activities append outcome events
> (`accepted`, `regression_confirmed`, `reverted`, `human_handoff`) to the
> current iteration's section of `refinement.yaml` via
> `refinement_log.append_refinement_outcome`.

`edd_refinement_workflow` was a large, fully-**deterministic simulation** of an agentic
refinement loop. Its two steps that were supposed to be agentic — `plan_refinement_action`
and `execute_refinement_action` — never invoked a real skill: planning was a hardcoded
`if failing>0: "repair" elif uncovered: "add_coverage"` rule table, and execution sent a
single ad-hoc prompt string to `DevinHarness` referencing a skill (`execute-refinement-action`)
that did not exist under `.devin/skills/`. Everything *around* those two steps (progress
record, budgets, quality ratchet, regression recovery, commit) is sound, reusable, and
already follows the `SkillActivity` / colocated-config pattern used by `story_analysis_workflow`.

**Recommendation: repair, don't rebuild.** Keep the deterministic scaffolding
(`ProgressRecordStore`, limits, coverage, quality ratchet math, commit, evaluation
harness), and replace the two fake agentic activities with real `SkillActivity` calls
against two new skills (`edd-plan`, `edd-do`), plus a small set of renamed/repaired
deterministic activities that match the loop the user described (setup → plan → do →
check → regression-confirm → commit/revert → loop). A from-scratch rebuild would throw
away ~2,500 lines of already-tested budget/ratchet/regression logic that has nothing
to do with the actual bug.

See also:
- [[vault/services/grade-story-design-eval-refinement.md]] — the manually-run process this workflow should automate.
- [[vault/services/edd_refinement.md]] — current implementation status log.
- [[vault/decisions/ADR-017-agentic-edd-quality-ratchet.md]], [[ADR-019-edd-multi-iteration-loop.md]], [[ADR-021-edd-evaluation-command-contracts.md]].
- `docs/reqs/agentic-edd-refinement/feature-description.md` — original feature spec (still largely valid; this doc corrects the implementation, not the intent).

## Why the current implementation doesn't work

| Component | File | Problem |
|---|---|---|
| Planning | `plan_refinement.py` (`PlanRefinementActivity`) | Pure rule table over `failing`/`uncovered` counts. No skill invocation, no judgment, no reading of the rubric/rubric/fixtures. Cannot decide *what* to change, only which bucket (`repair` / `add_coverage`) to pick. |
| Execution | `execute_refinement_action.py` (`HarnessBackedRefinementRunner`) | Builds one raw prompt string (`"Execute refinement action '{action}'... Only modify these files: {...}"`) and calls `DevinHarness.run` directly. `execute_refinement_action.config.json` declared `skill_name: "execute-refinement-action"`, but no such skill exists in `.devin/skills/`. This bypasses the entire skills-based architecture (ADR-003) that `story_analysis_workflow` follows. |
| Agentic context document | *(missing)* | Setup does not synthesize the `edd_input` object, rubric, test-case catalog, fixture inventory, or prior iteration history into a single document `edd-plan` can read. Every planning/do cycle starts from zero durable context. |
| Loop anchor for regression confirmation | `workflow.py` (`_handle_regression`) | Already fixed: `iteration_start_baseline` is frozen at Plan time, persisted into `progress.json`, and used by Check and Regression Confirmation. |
| Per-iteration artifact trail | *(mostly resolved)* | `check.json` is written for iteration 0 (Setup baseline) and post-Do candidates; `check.done.json` remains as optional observability. `iterations/<n>/plan.json` is written by `edd-plan` and `refinement.yaml` is initialized by Setup. `iterations/<n>/do.json` is not yet produced. |
| Skill naming | n/a | The only real EDD skill that exists is `.devin/skills/edd-decide`, which is a single-shot recommender. It is *not* wired into the workflow — `plan_refinement.py` reimplemented a worse version of its logic in Python instead of invoking it. The new `edd-plan` skill supersedes it. |

Net effect: the workflow runs, produces a syntactically valid terminal report, and never
actually asks a model to look at a failing eval and fix it. The "agentic" workflow is
agentic in name only.

## What already works and should be reused as-is

| Concern | File(s) | Keep? |
|---|---|---|
| Durable run state schema | `progress_record.py`, `ProgressRecordStore` | Yes — schema-versioned, redacts secrets, `.process/edd/<run_id>/progress.json` convention (see `vault/services/edd_refinement.md`). |
| Target repo resolution / preflight | `common/preflight.py`, `TargetRepositoryContext` | Yes — cross-cutting capability, not EDD-specific. |
| Evaluation command + inspect parsing | `run_baseline_evaluation.py`, `coverage.py`, `evaluation_identity.py` | Yes — implements ADR-021's non-zero-exit / raw-list contract correctly. Rename its non-baseline use so it can run as the "Check" step for any candidate, not just iteration 0. |
| Quality ratchet comparison math | `quality_ratchet.py` (`compare_candidate_to_best`, `resolve_comparison_baseline`) | Yes — accept/reject/rerun/escalate rules match ADR-017 exactly; `iteration_start_baseline` fallback is already in place. |
| Budgets & counters | `check_refinement_limits.py`, `update_durable_counters.py` | Yes — iteration/token/regression-threshold gating is correct and reusable unchanged. |
| Regression rerun / recovery | `rerun_degraded_candidate.py`, `regression_recovery.py` | Mostly yes — reusable for the Regression Confirmation step, already retargeted to the iteration-start baseline. |
| Commit on accept | `commit_accepted_candidate.py`, `git_commit_message.py` | Yes — deterministic `git add -A && git commit` with a generated message. No sentinel required. |
| `scripts/inspect-eval.js`, `npm run test {eval}.yaml` | n/a | Yes — unchanged, already the deterministic evaluation contract per ADR-021. |
| `.devin/skills/promptfoo` | n/a | Yes — reference skill `edd-do` should invoke/consult when editing eval YAML. |

## What must be replaced / finished

- ✅ `plan_refinement.py`'s rule table → replaced by `edd-plan` skill invocation via `SkillActivity` (`activities/edd_plan.py`). Budget/regression stop gate stays deterministic in `EddPlanRunner`.
- ✅ `execute_refinement_action.py`'s raw-prompt runner → replaced by `edd-do` skill invocation via `SkillActivity` (`activities/edd_do.py`). Approval gating stays deterministic.
- ✅ The single-baseline anchor for regression comparison → `iteration_start_baseline` is frozen by `edd-plan`, persisted to `progress.json`, and consumed by `check_candidate` and regression handling.
- ✅ The **context document** → a run-level `refinement.yaml` initialized by `initialize_run`, embedding the `edd_input` object, iteration-0 baseline metrics, the action taxonomy, and an empty `iterations:` list appended to by each cycle.
- ◐ The **per-iteration artifact trail** → `check.json` exists for iteration 0 (Setup baseline) and post-Do checks. `iterations/<n>/plan.json` is written by `edd-plan`. `iterations/<n>/do.json` (change record from `edd-do`) is not yet written/verified.
- ✅ **Sentinel policy** → only `edd-plan` and `edd-do` require sentinels. `check_candidate` still writes `check.done.json` for observability (optional, allowed).
- ✅ **Approval flow simplification** → `workflow.py` routes to `edd_do` directly; only `planning.requires_approval` (set for `propose_evaluation_expectation_change`) triggers the approval gate.
- ✅ **Progress-record schema cleanup** → `attempt_records` renamed to `attempts` in `initialize_run.py`, `update_durable_counters.py`, tests, and the serializer; `iteration_start_baseline` added to `ProgressRecordSerializer.for_v5`.

## Target loop

```
                 ┌─────────────────────────────────────────────────────────┐
                 │                                                         │
                 ▼                                                         │
   [Setup] ──▶ [EDD Plan] ──▶ [EDD Do] ──▶ [Check] ──┬─▶ [Commit] ─────────┘  (accept)
   (once)       (agentic)     (agentic)   (determ.)  │
                                                      ├─▶ [Regression Confirm] ──▶ [Revert] ──▶ loop to Plan (confirmed regression)
                                                      │                              │
                                                      │                              └─▶ [Human Handoff] (not reproduced / inconclusive)
                                                      │
                                                      └─▶ loop to Plan directly (reject: no qualifying value, nothing to commit or revert)

   Limit check ("check_refinement_limits") runs before every EDD Plan call, before every
   EDD Do call (after Plan's token spend is accounted), and after every EDD Do / Check /
   Regression-Confirm call. A stop decision routes straight to Finalize regardless of
   where in the loop it is raised.
```

Activity name ↔ loop position ↔ type, at a glance:

| # | Activity name | Loop position | Type | Runs |
|---|---|---|---|---|
| 0 | `initialize_edd_run` (Setup) | before the loop, once | deterministic | once per run |
| 1 | `check_refinement_limits` | top of every loop cycle | deterministic | every cycle |
| 2 | `edd_plan` | loop step 1 | **agentic** (skill: `edd-plan`) | every cycle |
| 3 | `edd_do` | loop step 2 | **agentic** (skill: `edd-do`) | every cycle (unless Plan says `stop`) |
| 4 | `check_candidate` (Check) | loop step 3 | deterministic | every cycle after Do |
| 5 | `check_refinement_limits` | before Do (after Plan's usage is accounted), after Do, after Check | deterministic | every cycle |
| 6 | `confirm_regression` (Regression Confirmation) | loop step 4, conditional | deterministic | only when Check flags apparent regression |
| 7 | `revert_last_change` (Revert) | loop step 5, conditional | deterministic | only on confirmed regression |
| 8 | `commit_accepted_candidate` (Commit) | loop step 5, conditional | deterministic | only on accept |
| 9 | `finalize_run` | terminal | deterministic | once, on any stop condition |

## Per-activity requirements

### 0. Setup (`initialize_edd_run`) — deterministic, no sentinel

**Inputs**
- `EddRefinementInput` (existing `input.py` contract: `skill_folder`, `eval_config`, `test_command`, `inspect_command`, `test_cases`, `coverage_metadata_property`, `modification_scope`, `limits`).
- Target skill's prompt/`SKILL.md`, its `_tests/` fixtures, and rubric text.

**Requirements**
- Reuse `TargetRepositoryContext` preflight (ADR-018) unchanged; refuse to start on a dirty worktree or missing skill/eval-suite (feature-description.md preconditions 1–15 remain in force).
- Create/resume the `ProgressRecord` at `<input-parent>/.process/edd/<run_id>/progress.json` via `ProgressRecordStore` (unchanged).
- Run the **baseline** evaluation once, using the same mechanics as `check_candidate`, and persist it as **iteration 0**'s check result at `.process/edd/<run_id>/iterations/0/check.json`.
- Initialize the workflow's historical context document at `.process/edd/<run_id>/refinement.yaml`. It must embed, without judgment:
  - the original `edd_input` object (as `edd_input`),
  - the baseline metrics and per-test-case coverage map (reuse `CoverageCalculator`),
  - the authorized modification scope and action taxonomy.
- Leave an empty `iterations:` list in `refinement.yaml`; each subsequent Plan/Do/Check cycle appends a section to it.
- No `setup.done.json` sentinel is required.

**Outputs:** `progress_record` (schema v5+), `iterations/0/check.json`, `refinement.yaml`.

### 1. EDD Plan (`edd_plan`) — agentic, new skill `edd-plan`

Replaces `plan_refinement.py`'s rule table. Evolves `.devin/skills/edd-decide` rather than discarding it — same recommendation taxonomy (Improve Prompt / Extend Test Suite / Modify Evaluation Criteria / Stop), but iteration-aware and file-scoped.

**Inputs**
- `refinement.yaml` from Setup or the current run (first iteration or subsequent iterations).
- The two most recent `check.json` results (for pattern detection, matching `edd-decide`'s existing instruction to "review the two most recent evaluation runs").
- The previous iteration's `plan.json` and the "changes made" notes in `refinement.yaml` (what was tried, what changed, whether it was accepted/reverted) — this is the mechanism that lets the agent avoid repeating a just-reverted change (ADR-017's "failed-attempt memory").
- Remaining iteration/token budget (from `check_refinement_limits`), read via `progress.json` or embedded in `refinement.yaml`.
- Authorized action taxonomy and modification scope (from the embedded `edd_input`), unchanged from `feature-description.md`.

**Behavior / implicit rules**
- Prioritize, in order: (1) get all currently-failing evaluations to pass, (2) extend coverage for uncovered required test cases, (3) only consider "modify evaluation criteria" when a prompt fix has been tried and failed against a criterion that looks defective — mirrors `edd-decide`'s existing stubbornness rule and the vault's classification-of-failure guidance.
- Must record, for this iteration, the **starting baseline** it is trying to beat — either `best_accepted_state.metrics` or the original baseline if none exists yet. This value must be included verbatim in the plan output so Check/Regression-Confirm can compare against the same target the plan believed it was improving on.
- Produces exactly one proposed action per the closed taxonomy in `feature-description.md` (`add_coverage`, `repair`, `refine_skill`, `refine_supporting_docs`, `propose_evaluation_expectation_change`, `stop`), with a specific, actionable description ("what to change and why"), not just a bucket name.
- `propose_evaluation_expectation_change` must set `requires_approval: true`. All other actions route directly to `edd-do`.

**Outputs**
- `.process/edd/<run_id>/iterations/<n>/plan.json` (structured: action, rationale, evidence, intended_files, expected_effect, iteration-start baseline reference, requires_approval, stop_recommendation) — schema mirrors the existing `PlanningResult` dataclass fields and follows `.devin/skills/edd-plan/schema/plan.schema.json`.
- Append-only update to `.process/edd/<run_id>/refinement.yaml`: one new section per iteration summarizing number, selected action, rationale, evidence, intended files, expected effect, and a placeholder for the "changes made" notes that `edd-do` will fill in.
- Sentinel `<input-parent>/.process/edd-plan.done.json`, where `<input-parent>` is the directory containing the original EDD input document. The sentinel follows `@/schema/sentinel.schema.json` and lists `plan_path`, `refinement_path`, `iteration_number`, and `action` in `verify_params`.

### 2. EDD Do (`edd_do`) — agentic, new skill `edd-do`

Replaces `execute_refinement_action.py`'s raw-prompt runner. Follows the `analyze_story.py`/`.config.json` `SkillActivity` pattern exactly: colocated `edd_do.config.json` with `skill_name: "edd-do"`, `harness.devin.permission_mode: "accept-edits"`.

**Inputs**
- The current iteration's `plan.json` (single source of truth for what to change and the authorized file scope).
- Direct filesystem access to the target skill folder and its `_tests/` eval suite (per `feature-description.md`'s Authorized Refinement Actions taxonomy: skill prompt, supporting docs, evaluation YAML/fixtures/helper JS).

**Behavior / implicit rules**
- Must only touch files inside `intended_files` / the run's authorized `modification_scope`; anything else is a scope violation (existing `validate_candidate.py` logic already checks this and should be kept).
- Loads the `promptfoo` skill's guidance when editing eval YAML/assertions (existing skill, no new work needed — `edd-do`'s `SKILL.md` should explicitly tell the agent to consult it).
- Never modifies evaluation *expectations* (i.e., what score/pass a fixture "should" get) unless `plan.json.action == propose_evaluation_expectation_change` **and** approval has already been recorded — mirrors the existing approval-gate code in `workflow.py`.
- If `plan.json.requires_approval` is true, the deterministic wrapper must verify that an approved diff hash is supplied and matches before invoking the skill.

**Outputs**
- Modified skill/eval files (the actual diff).
- `.process/edd/<run_id>/iterations/<n>/do.json`: changed files, diff hash, usage metrics, duration — same shape as today's `ExecutionResult` dataclass so `validate_candidate`/`evaluate_candidate` need no changes. (If the skill itself writes this, the deterministic wrapper verifies it; otherwise the wrapper writes it after measuring the diff.)
- "Changes made" subsection appended to the current iteration's section in `.process/edd/<run_id>/refinement.yaml`: files touched, one line per file describing the change, how the actual change differs from the plan if it does, and why.
- Sentinel `<plan-parent>/.process/edd-do.done.json`, where `<plan-parent>` is the directory containing the iteration's `plan.json`. The sentinel lists `plan_path`, `iteration_number`, `action`, and `changed_files` in `verify_params`.

### 3. Check (`check_candidate`) — deterministic, optional sentinel

Generalizes `run_baseline_evaluation.py` so the same code path runs for the baseline (iteration 0) and every candidate thereafter.

**Inputs:** the repaired evaluation command contract from `EddRefinementInput` (`test_command`, `inspect_command`), the iteration's `do.json` (for context only).

**Requirements**
- Run `npm run test {eval}.yaml` (`check=False`, non-zero exit is a normal signal per ADR-021), then `node scripts/inspect-eval.js --all --json`, and compute `passing/failing/total/percentage` + `required_coverage` exactly as `run_baseline_evaluation.py`/`CoverageCalculator` already do — **no behavior change needed here**, just a rename/generalization so it isn't baseline-only.
- Compare the result against **both** (a) `best_accepted_state` (or original baseline) via `compare_candidate_to_best`, and (b) the iteration-start baseline recorded in `plan.json` / `progress.json`, per the user's regression-confirmation requirement.
- Persist `.process/edd/<run_id>/iterations/<n>/check.json` (or `.yaml` — either is acceptable; JSON matches the rest of the progress record and avoids a second parser) containing the raw metrics, the comparison decision (`accept` / `reject` / `rerun` / `escalate`), and which baseline it was compared against.
- May write `.process/check.done.json` naming the files checked and the determination reached — this is optional because Check is deterministic.
- On `accept` → route to Commit. On `reject` (no qualifying value, nothing worth keeping or reverting since Do's edits added no measured value but also didn't regress) → loop directly back to Plan. On `rerun` (apparent regression) → route to Regression Confirmation. On `escalate` (measurement context changed) → human handoff, no autonomous decision.

### 4. Regression Confirmation (`confirm_regression`) — deterministic, no sentinel

Directly implements the user's spec: "loop through the check again and see... are the last two results both worse than the baseline that the plan started with."

**Inputs:** the current (degraded) `check.json`, the iteration-start baseline reference from `plan.json`/`progress.json`, the unchanged candidate state (no new Do runs).

**Requirements**
- Re-run Check (same deterministic evaluation command, same candidate state, no code changes in between) exactly once — reuse `rerun_degraded_candidate.py`'s existing rerun mechanics.
- Classify using **the iteration-start baseline**, not only `best_accepted_state`:
  - Both the original and the rerun are worse than the iteration-start baseline → **confirmed regression** → Revert.
  - The rerun returns to or exceeds the iteration-start baseline → **not reproduced** → human handoff, no commit/revert.
  - The rerun errors/times out → **inconclusive** → human handoff.
- Record the classification in the progress record and append it to the current iteration's section in `refinement.yaml`. No sentinel is required.

### 5. Revert (`revert_last_change`) — deterministic, no sentinel

**Requirements**
- Programmatic only — no agent invocation. Uses `git reset --hard <last_accepted_commit>` against `best_accepted_state.commit` (the git-history approach decided in Open Question 1).
- Must not depend on or restore `.process/` contents — those are gitignored (`*.process`, `*.done.json` in `.gitignore`) and must never enter Git history, matching the user's explicit requirement ("sentinel and process documents should not be included in git history").
- After reverting, re-run Check once against the restored state to verify recovery (reuse `verify_recovery_metrics` concept) before handing control back to Plan. Failure to recover routes to human handoff rather than looping.
- Record the revert and verification result in the progress record and in `refinement.yaml`. No sentinel is required.

### 6. Commit (`commit_accepted_candidate`) — deterministic, no sentinel

**Requirements**
- Triggered only by Check's `accept` decision.
- Deterministic: reuse `commit_accepted_candidate.py`/`GitCommitMessageBuilder` unchanged — `git add -A && git commit -m <templated message>`, record `best_accepted_state`, reset the consecutive-regression counter.
- The `git-commit` skill is **not** used; commit message generation remains deterministic in this iteration.
- Record the accepted commit in the progress record and in the current iteration's `refinement.yaml` section. No sentinel is required.

### 7. Loop control: iteration & token limits — deterministic

- Reuse `check_refinement_limits.py` and `update_durable_counters.py` verbatim. Keep the existing check-before-Plan / update-after-Do / update-after-Check placement from `workflow.py`.
- **Both agentic steps are individually pre-checked.** `check_refinement_limits` already runs before `edd_plan` at the top of every loop cycle — that placement stays unchanged. The new requirement is a second check **before `edd_do`**: `edd_plan`'s token usage must be folded into `cumulative_token_usage` via `update_durable_counters` immediately after the plan step (today it is only accounted after `edd_do`), and `check_refinement_limits` re-run against the updated totals. If the plan step spent the last of the allowed token budget, the loop must stop there — a stop decision routes straight to `finalize_run`, exactly like any other limit stop — rather than invoking `edd_do`.
- Confirmed regression count (3-strikes stop) is already implemented; port it into the new `edd_plan` deterministic wrapper (the Cadence Activity around the `edd-plan` skill call), not into the skill itself — budget arithmetic must stay deterministic and untestable-by-the-model.

## New skills to write

| Skill | Purpose | Notes |
|---|---|---|
| `edd-plan` ✅ written, wired | Review `refinement.yaml` (which embeds the `edd_input` object), iteration history, and latest `check.json` results; select one authorized action; produce a scoped, specific incremental plan. | Lives at `.devin/skills/edd-plan/SKILL.md`; wired via `src/edd_refinement_workflow/activities/edd_plan.py`/`edd_plan.config.json`. It now reads `refinement.yaml` as its primary context document and writes `plan.json` plus an append-only `refinement.yaml` section. |
| `edd-do` ✅ written, wired | Load the target skill's prompt/tests, apply the plan's described change within the authorized scope, update `refinement.yaml` with what actually changed. | Lives at `.devin/skills/edd-do/SKILL.md`; wired via `src/edd_refinement_workflow/activities/edd_do.py`/`edd_do.config.json`, following the `analyze-story` skill's shape. References the `promptfoo` skill for eval-suite edits. |

No new skill is required for Check, Regression Confirmation, Revert, or the loop-limit
gate — those are all deterministic per the vault's own classification table in
`grade-story-design-eval-refinement.md`.

## Existing skills/activities usable without change

- `.devin/skills/promptfoo` — referenced by `edd-do` for eval-suite mechanics.
- `scripts/inspect-eval.js`, `npm run test {eval}.yaml` — the Check step's evaluation contract (ADR-021).
- `common/preflight.py`, `TargetRepositoryContext` — Setup's repo resolution.
- `common/skill_activity.py` (`SkillActivity`) — the base class `edd_plan`/`edd_do` Activities must subclass, exactly as `AnalyzeStorySkillActivity` does.
- `progress_record.py`, `coverage.py`, `evaluation_identity.py`, `quality_ratchet.py`, `check_refinement_limits.py`, `update_durable_counters.py`, `commit_accepted_candidate.py`, `git_commit_message.py`, `rerun_degraded_candidate.py`, `regression_recovery.py` — all reusable per the table in "What already works" above.

## Sentinel & process-file conventions (per ADR-004 and revised policy)

- Only **agentic skill invocations** (`edd-plan`, `edd-do`) are required to write sentinels.
- Deterministic activities (`initialize_run`, `check_candidate`, regression confirmation, commit, revert) do **not** write sentinels. `check_candidate` may optionally continue writing `check.done.json` for observability.
- `edd-plan`'s sentinel is written to `<input-parent>/.process/edd-plan.done.json`, where `<input-parent>` is the directory containing the original EDD input document.
- `edd-do`'s sentinel is written to `<plan-parent>/.process/edd-do.done.json`, where `<plan-parent>` is the directory containing the current iteration's `plan.json`.
- Per-iteration artifacts live under `.process/edd/<run_id>/iterations/<n>/{plan,do,check}.json`; the append-only human-readable plan narrative lives at `.process/edd/<run_id>/refinement.yaml`. This mirrors the existing `.process/edd/<run_id>/progress.json` convention already documented in `vault/services/edd_refinement.md`.
- Sentinels and process documents are gitignored (`*.process`, `*.done.json`) and must never enter Git history.

## Data threaded around the loop (progress record additions)

- The `ProgressRecord` schema needs one durable addition to close the regression-baseline
  gap: each iteration's plan must persist `iteration_start_baseline` (a reference to either
  `best_accepted_state.metrics` or the original baseline metrics, frozen at Plan time), so
  Check and Regression Confirmation compare against the same target the plan believed it
  was improving on. It must also be added to `ProgressRecordSerializer.for_v5`'s allow-list
  so any round-trip path does not silently drop it.
- The progress record field for durable attempt bookkeeping is renamed from `attempt_records`
  to `attempts`. `initialize_run.py`, `update_durable_counters.py`, tests, and the
  serializer must all use `attempts`.
- `candidate_history` records every candidate, the plan that produced it, and its final
  state (`accepted`, `rejected`, `reverted`). The `commit` field is included only when the
  candidate was accepted and committed; otherwise it is omitted.
- The durable historical narrative lives in `refinement.yaml`, which is regenerated/extended
  by each activity rather than being a single value carried in the Cadence workflow state.

## Open questions / decisions (all closed)

1. **Commit policy per iteration.** ✅ **Decided (2026-09-23):** the git-history approach. Accepted candidates are committed (`commit_accepted_candidate` remains the commit point), and Revert restores via `git reset --hard <last_accepted_commit>` — i.e., the existing `revert_repository_to_best` semantics against `best_accepted_state.commit`.
2. **Should `edd-decide` be renamed to `edd-plan` or kept as an internal step `edd-plan` calls?** ✅ **Decided:** `edd-plan` is the canonical skill. `edd-decide` remains in the repo but is unreferenced; deleting or folding it is future cleanup.
3. **Commit message: deterministic template vs. `git-commit` skill.** ✅ **Decided:** keep the deterministic `commit_accepted_candidate.py`/`GitCommitMessageBuilder` path for now. The skill-based version is deferred.
4. **Where does the agentic context document belong?** ✅ **Decided:** a run-level `refinement.yaml` under `.process/edd/<run_id>/`, initialized by Setup and embedding the `edd_input` object. It is gitignored and regenerated from source-of-truth files.
5. **Regression-confirmation loop bound.** ✅ **Decided:** exactly one extra rerun, matching ADR-017's existing "rerun once before confirming" rule, implemented by `rerun_degraded_candidate.py`.

## Suggested delivery order

1. ✅ **Done.** Thread `iteration_start_baseline` through Plan→Check→Regression and persist it.
2. ✅ **Done.** Wire `edd-plan` and `edd-do` as real `SkillActivity` invocations.
3. ✅ **Done.** Update `requirements.md` (this document) to record the new context-document, sentinel, approval-flow, and record-schema decisions.
4. ✅ **Done.** `ProgressRecordSerializer.for_v5` allows `iteration_start_baseline`; `attempt_records` renamed to `attempts` in `initialize_run.py`, `update_durable_counters.py`, tests, and serializer.
5. ✅ **Done.** `initialize_run` creates `refinement.yaml` (embedded `edd_input`, baseline metrics, action taxonomy, empty `iterations` list) and runs the baseline as iteration 0 via `check_candidate`, writing `iterations/0/check.json` and storing `baseline_metrics` in the progress record.
6. ✅ **Done.** `edd_plan` is invoked with `input_path` (sentinel placed at `<input-parent>/.process/edd-plan.done.json`) and reads `refinement.yaml` + `progress.json` for context.
7. ✅ **Done.** `edd-do`'s SKILL.md appends a "changes made" section to `refinement.yaml`; `EddDoRunner` writes `iterations/<n>/do.json` (the `ExecutionResult` shape) next to the iteration's `plan.json` after measuring the diff, on both success and harness-failure paths.
7a. ✅ **Done.** Token-limit pre-check before `edd_do`: `PlanningResult` now carries `usage_metrics` (populated from the skill run's usage observation), and `workflow.py` folds it into `cumulative_token_usage` via `update_durable_counters` then re-runs `check_refinement_limits` immediately after `edd_plan`. A budget-exhausting plan routes to `finalize_run` without invoking `edd_do`.
8. ✅ **Done.** `workflow.py` routes to `edd_do` directly unless `planning.requires_approval`; expectation-change proposals await approval and verify the executed diff hash before proceeding.
9. ✅ **Done.** Sentinels are required only for `edd-plan` and `edd-do`; `check_candidate`'s `check.done.json` is retained as optional observability.
10. **Pending.** Re-verify the existing budget/limit/regression-threshold tests still pass unchanged against the new activity boundaries, then run the full loop against the `grade-story-design` eval suite as the first real end-to-end validation.
