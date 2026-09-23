# Fix the EDD Refinement Workflow — Requirements & Analysis

## Bottom line

> **Status update (2026-09-23):** the two dummy activities described below have been
> replaced. `edd_plan` (backed by the new `.devin/skills/edd-plan` skill) and `edd_do`
> (backed by the new `.devin/skills/edd-do` skill) are real `SkillActivity` subclasses,
> colocated-config, wired into `EddRefinementWorkflow` and `module.py` exactly like
> `analyze_story.py`/`analyze_story.config.json`. `plan_refinement.py` and
> `execute_refinement_action.py` are deleted. See
> [[vault/services/edd_refinement.md]] ("`edd_plan`/`edd_do` skill wiring" section) for
> what shipped and what is still open (`iteration_start_baseline` threading, the
> `guide.md`/`check_candidate` generalization, and the commit/revert policy decision
> remain future work — see "Suggested delivery order" below).

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
away ~2,500 lines of already-tested budget/ratchet/regression logic that has nothing to
do with the actual bug.

See also:
- [[vault/services/grade-story-design-eval-refinement.md]] — the manually-run process this workflow should automate.
- [[vault/services/edd_refinement.md]] — current implementation status log.
- [[vault/decisions/ADR-017-agentic-edd-quality-ratchet.md]], [[ADR-019-edd-multi-iteration-loop.md]], [[ADR-021-edd-evaluation-command-contracts.md]].
- `docs/reqs/agentic-edd-refinement/feature-description.md` — original feature spec (still largely valid; this doc corrects the implementation, not the intent).

## Why the current implementation doesn't work

| Component | File | Problem |
|---|---|---|
| Planning | `plan_refinement.py` (`PlanRefinementActivity`) | Pure rule table over `failing`/`uncovered` counts. No skill invocation, no judgment, no reading of the guide/rubric/fixtures. Cannot decide *what* to change, only which bucket (`repair` / `add_coverage`) to pick. |
| Execution | `execute_refinement_action.py` (`HarnessBackedRefinementRunner`) | Builds one raw prompt string (`"Execute refinement action '{action}'... Only modify these files: {...}"`) and calls `DevinHarness.run` directly. `execute_refinement_action.config.json` declares `skill_name: "execute-refinement-action"`, but no such skill exists in `.devin/skills/`. This bypasses the entire skills-based architecture (ADR-003) that `story_analysis_workflow` follows. |
| Guiding document | *(missing)* | Nothing in Setup/Initialize synthesizes the rubric, existing test-case catalog, fixture inventory, or prior iteration history into a document an agent can act on. Every planning/do cycle starts from zero context. |
| Loop anchor for regression confirmation | `workflow.py` (`_handle_regression`) | Compares candidate to `best_accepted_state` only. The user's requirement — "are the last two results both worse than the baseline **the plan started with**" — needs the per-iteration starting baseline, which is never captured as a discrete artifact today. |
| Process artifacts | *(none)* | `run_baseline_evaluation` writes into the Cadence-durable `ProgressRecord`, but nothing is written as plain JSON/YAML under a target-repo `.process/` folder the way `ADR-004`/`ADR-004` sentinel conventions and `story_analysis_workflow` artifacts do. There is no per-iteration plan/do/check file trail. |
| Skill naming | n/a | The only real EDD skill that exists is `.devin/skills/edd-decide`, which is a single-shot recommender ("Improve the prompt" / "Extend the test suite" / ...). It is *not* wired into the workflow at all — `plan_refinement.py` reimplements a worse version of its logic in Python instead of invoking it. |

Net effect: the workflow runs, produces a syntactically valid terminal report, and never
actually asks a model to look at a failing eval and fix it. The "agentic" workflow is
agentic in name only.

## What already works and should be reused as-is

| Concern | File(s) | Keep? |
|---|---|---|
| Durable run state schema | `progress_record.py`, `ProgressRecordStore` | Yes — schema-versioned, redacts secrets, `.process/edd/<run_id>/progress.json` convention (see `vault/services/edd_refinement.md`). |
| Target repo resolution / preflight | `common/preflight.py`, `TargetRepositoryContext` | Yes — cross-cutting capability, not EDD-specific. |
| Evaluation command + inspect parsing | `run_baseline_evaluation.py`, `coverage.py`, `evaluation_identity.py` | Yes — implements ADR-021's non-zero-exit / raw-list contract correctly. Rename its non-baseline use so it can run as the "Check" step for any candidate, not just iteration 0. |
| Quality ratchet comparison math | `quality_ratchet.py` (`compare_candidate_to_best`) | Yes — accept/reject/rerun/escalate rules match ADR-017 exactly. |
| Budgets & counters | `check_refinement_limits.py`, `update_durable_counters.py` | Yes — iteration/token/regression-threshold gating is correct and reusable unchanged. |
| Regression rerun / recovery | `rerun_degraded_candidate.py`, `regression_recovery.py` | Mostly yes — reusable for the Regression Confirmation step, but needs to compare against the **iteration-start baseline** captured by Plan, not only `best_accepted_state` (see gap above). |
| Commit on accept | `commit_accepted_candidate.py`, `git_commit_message.py` | Yes — deterministic `git add -A && git commit` with a generated message. Candidate for wrapping with the `git-commit` skill for message quality (see Commit activity below). |
| `scripts/inspect-eval.js`, `npm run test {eval}.yaml` | n/a | Yes — unchanged, already the deterministic evaluation contract per ADR-021. |
| `.devin/skills/edd-decide` | n/a | Partially — its review logic (compare last two runs, classify failure patterns, choose among Improve Prompt / Extend Suite / Modify Criteria / Stop) is the right shape for **EDD Plan**, but it needs to become iteration-aware (reads Setup's guide doc + prior plan/do/check artifacts, not just "the log") and produce a structured, scoped plan rather than free text. |
| `.devin/skills/promptfoo` | n/a | Yes — reference skill `edd-do` should invoke/consult when editing eval YAML. |
| `.devin/skills/git-commit` | n/a | Yes — conventions for the Commit activity. |

## What must be replaced

- ✅ `plan_refinement.py`'s `_select_action` rule table → replaced by a real `edd-plan` skill invocation via `SkillActivity` (`src/edd_refinement_workflow/activities/edd_plan.py`, Cadence activity name `edd_plan`). The deterministic budget/regression-count stop gate was ported into `EddPlanRunner`, not into the skill.
- ✅ `execute_refinement_action.py`'s raw-prompt `HarnessBackedRefinementRunner` → replaced by a real `edd-do` skill invocation via `SkillActivity` (`src/edd_refinement_workflow/activities/edd_do.py`, Cadence activity name `edd_do`), following the exact `analyze_story.py` / `analyze_story.config.json` pattern (colocated config, `skill_name`, `output_path_key`, `accept-edits` permission). Approval gating (`missing_approval` / `diff_hash_mismatch`) stayed deterministic in `EddDoRunner`.
- ⬜ The single-baseline anchor for regression comparison → still needs an explicit "iteration start baseline" captured at Plan time and threaded through Do/Check/Regression-Confirm. `edd-plan`'s `plan.json` already emits `iteration_start_baseline` and `edd_plan_action` surfaces it in `PlanningResult`, but nothing downstream (Check/Regression-Confirm) consumes it yet.
- ⬜ The complete absence of `.process/edd/<run_id>/iterations/<n>/{plan,do,check}.*` artifacts and sentinels → `edd-plan`/`edd-do` write `plan.json`/sentinels per their `SKILL.md`s; the `check`/`regression-confirm` writers and the Setup `guide.md` writer are still outstanding.

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

   Limit check ("check_refinement_limits") runs before every EDD Plan call and after
   every EDD Do / Check / Regression-Confirm call. A stop decision routes straight to Finalize
   regardless of where in the loop it is raised.
```

Activity name ↔ loop position ↔ type, at a glance:

| # | Activity name | Loop position | Type | Runs |
|---|---|---|---|---|
| 0 | `initialize_edd_run` (Setup) | before the loop, once | deterministic | once per run |
| 1 | `check_refinement_limits` | top of every loop cycle | deterministic | every cycle |
| 2 | `edd_plan` | loop step 1 | **agentic** (skill: `edd-plan`) | every cycle |
| 3 | `edd_do` | loop step 2 | **agentic** (skill: `edd-do`) | every cycle (unless Plan says `stop`) |
| 4 | `check_candidate` (Check) | loop step 3 | deterministic | every cycle after Do |
| 5 | `check_refinement_limits` | after Do, after Check | deterministic | every cycle |
| 6 | `confirm_regression` (Regression Confirmation) | loop step 4, conditional | deterministic | only when Check flags apparent regression |
| 7 | `revert_last_change` (Revert) | loop step 5, conditional | deterministic | only on confirmed regression |
| 8 | `commit_accepted_candidate` (Commit) | loop step 5, conditional | deterministic + optional skill (`git-commit`) | only on accept |
| 9 | `finalize_run` | terminal | deterministic | once, on any stop condition |

## Per-activity requirements

### 0. Setup (`initialize_edd_run`) — deterministic

**Inputs**
- `EddRefinementInput` (existing `input.py` contract: `skill_folder`, `eval_config`, `test_command`, `inspect_command`, `test_cases`, `coverage_metadata_property`, `modification_scope`, `limits`).
- Target skill's prompt/`SKILL.md`, its `_tests/` fixtures, and rubric text.

**Requirements**
- Reuse `TargetRepositoryContext` preflight (ADR-018) unchanged; refuse to start on a dirty worktree or missing skill/eval-suite (feature-description.md preconditions 1–15 remain in force).
- Create/resume the `ProgressRecord` at `.process/edd/<run_id>/progress.json` via `ProgressRecordStore` (unchanged).
- Run the **baseline** evaluation once via the existing deterministic `run_baseline_evaluation` / `Check` logic (see below) and persist it as `iteration 0`'s check result.
- **New:** deterministically assemble a **guide document** at `.process/edd/<run_id>/guide.md` (or `.json`) that concatenates, without judgment:
  - the eval config path and required test-case catalog,
  - the target skill's rubric/prompt text,
  - the baseline metrics and per-test-case coverage map (reuse `CoverageCalculator`),
  - the authorized modification scope and action taxonomy.
  - This is pure aggregation (file reads + the existing `CoverageCalculator`), matching the vault's classification of "coverage mapping" as agentic only in its *interpretation*, not its *extraction*. Interpretation is deferred to `edd-plan`.
- Write a sentinel `.process/setup.done.json` naming the run id and the guide document path.

**Outputs:** `progress_record` (schema v1+), `iteration_0` baseline check artifact, `guide.md`, `.process/setup.done.json`.

### 1. EDD Plan (`edd_plan`) — agentic, new skill `edd-plan`

Replaces `plan_refinement.py`'s rule table. Evolves `.devin/skills/edd-decide` rather than discarding it — same recommendation taxonomy (Improve Prompt / Extend Test Suite / Modify Evaluation Criteria / Stop), but iteration-aware and file-scoped.

**Inputs**
- `guide.md` from Setup (first iteration) or the running plan document + latest `check.json` (subsequent iterations).
- The two most recent `check` results (for pattern detection, matching `edd-decide`'s existing instruction to "review the two most recent evaluation runs").
- The previous iteration's `plan.md`/`plan.json` and `do.json` (what was tried, what changed, whether it was accepted/reverted) — this is the mechanism that lets the agent avoid repeating a just-reverted change (ADR-017's "failed-attempt memory").
- Remaining iteration/token budget (from `check_refinement_limits`).
- Authorized action taxonomy and modification scope (from Setup/EddRefinementInput), unchanged from `feature-description.md`.

**Behavior / implicit rules**
- Prioritize, in order: (1) get all currently-failing evaluations to pass, (2) extend coverage for uncovered required test cases, (3) only consider "modify evaluation criteria" when a prompt fix has been tried and failed against a criterion that looks defective — mirrors `edd-decide`'s existing stubbornness rule and the vault's classification-of-failure guidance.
- Must record, for this iteration, the **starting baseline** it is trying to beat — either `best_accepted_state` or the original baseline if none exists yet. This value must be included verbatim in the plan output so Check/Regression-Confirm can compare against the same target the plan believed it was improving on (closes the gap identified above).
- Produces exactly one proposed action per the closed taxonomy in `feature-description.md` (`add_coverage`, `repair`, `refine_skill`, `refine_supporting_docs`, `propose_evaluation_expectation_change`, `stop`), with a specific, actionable description ("what to change and why"), not just a bucket name.
- `propose_evaluation_expectation_change` still requires human approval before Do executes it (unchanged approval gate).

**Outputs**
- `.process/edd/<run_id>/iterations/<n>/plan.json` (structured: action, rationale, evidence, intended files, expected effect, iteration-start baseline reference, requires_approval, stop_recommendation) — schema mirrors the existing `PlanningResult` dataclass fields so downstream Cadence code doesn't need a rewrite.
- Append-only `.process/edd/<run_id>/plan.md` — a single running document, one section per iteration, human-readable audit trail (this is the "incremental plan" / "plan document" the user described).
- Sentinel `.process/edd_plan.done.json` listing `plan.json` and `plan.md` as changed/created files.

### 2. EDD Do (`edd_do`) — agentic, new skill `edd-do`

Replaces `execute_refinement_action.py`'s raw-prompt runner. Follows the `analyze_story.py`/`.config.json` `SkillActivity` pattern exactly: colocated `edd_do.config.json` with `skill_name: "edd-do"`, `harness.devin.permission_mode: "accept-edits"`.

**Inputs**
- The current iteration's `plan.json` (single source of truth for what to change and the authorized file scope).
- Direct filesystem access to the target skill folder and its `_tests/` eval suite (per `feature-description.md`'s Authorized Refinement Actions taxonomy: skill prompt, supporting docs, evaluation YAML/fixtures/helper JS).

**Behavior / implicit rules**
- Must only touch files inside `intended_files` / the run's authorized `modification_scope`; anything else is a scope violation (existing `validate_candidate.py` logic already checks this and should be kept).
- Loads the `promptfoo` skill's guidance when editing eval YAML/assertions (existing skill, no new work needed — `edd-do`'s `SKILL.md` should explicitly tell the agent to consult it).
- Never modifies evaluation *expectations* (i.e., what score/pass a fixture "should" get) unless `plan.json.action == propose_evaluation_expectation_change` **and** approval has already been recorded — mirrors the existing approval-gate code in `workflow.py`.

**Outputs**
- Modified skill/eval files (the actual diff).
- `.process/edd/<run_id>/iterations/<n>/do.json`: changed files, diff hash, usage metrics, duration — same shape as today's `ExecutionResult` dataclass so `validate_candidate`/`evaluate_candidate` need no changes.
- Appends a "changes made" section to `.process/edd/<run_id>/plan.md` describing what was actually done vs. what was planned (per the user's requirement that Do "update the plan upon completion with a description of the changes that were made").
- Sentinel `.process/edd_do.done.json` listing every changed file.

### 3. Check (`check_candidate`) — deterministic

Generalizes `run_baseline_evaluation.py` so the same code path runs for the baseline (iteration 0) and every candidate thereafter.

**Inputs:** the repaired evaluation command contract from `EddRefinementInput` (`test_command`, `inspect_command`), the iteration's `do.json` (for context only).

**Requirements**
- Run `npm run test {eval}.yaml` (`check=False`, non-zero exit is a normal signal per ADR-021), then `node scripts/inspect-eval.js --all --json`, and compute `passing/failing/total/percentage` + `required_coverage` exactly as `run_baseline_evaluation.py`/`CoverageCalculator` already do — **no behavior change needed here**, just a rename/generalization so it isn't baseline-only.
- Compare the result against **both** (a) `best_accepted_state` (or original baseline) via `compare_candidate_to_best`, and (b) the iteration-start baseline recorded in `plan.json`, per the user's regression-confirmation requirement.
- Persist `.process/edd/<run_id>/iterations/<n>/check.json` (or `.yaml` — either is acceptable; JSON matches the rest of the progress record and avoids a second parser) containing the raw metrics, the comparison decision (`accept` / `reject` / `rerun` / `escalate`), and which baseline it was compared against.
- Sentinel `.process/check.done.json` naming the files checked (`check.json`) and the determination (`accept`/`reject`/`rerun`/`escalate`) — this is the "check Sentinel file that indicates what was checked, what the determination was" the user asked for.
- On `accept` → route to Commit. On `reject` (no qualifying value, nothing worth keeping or reverting since Do's edits added no measured value but also didn't regress) → loop directly back to Plan. On `rerun` (apparent regression) → route to Regression Confirmation. On `escalate` (measurement context changed) → human handoff, no autonomous decision.

### 4. Regression Confirmation (`confirm_regression`) — deterministic

Directly implements the user's spec: "loop through the check again and see... are the last two results both worse than the baseline that the plan started with."

**Inputs:** the current (degraded) `check.json`, the iteration-start baseline reference from `plan.json`, the unchanged candidate state (no new Do runs).

**Requirements**
- Re-run Check (same deterministic evaluation command, same candidate state, no code changes in between) exactly once — reuse `rerun_degraded_candidate.py`'s existing rerun mechanics.
- Classify using **the iteration-start baseline**, not only `best_accepted_state`:
  - Both the original and the rerun are worse than the iteration-start baseline → **confirmed regression** → Revert.
  - The rerun returns to or exceeds the iteration-start baseline → **not reproduced** → human handoff, no commit/revert (existing `classify_regression_evidence` semantics, retarget the comparison baseline).
  - The rerun errors/times out → **inconclusive** → human handoff.
- Persist `.process/edd/<run_id>/iterations/<n>/regression-confirm.json` and sentinel `.process/regression_confirm.done.json` with the classification.

### 5. Revert (`revert_last_change`) — deterministic

**Requirements**
- Programmatic only — no agent invocation. Uses `git` directly against the run's own commit history: `git reset --hard <last_accepted_commit>` (or `git checkout -- <changed_files>` if the run's commit policy is "commit every iteration, revert via history" vs. "never commit until accepted" — this is a design decision the implementation must pin down explicitly; see Open Questions).
- Must not depend on or restore `.process/` contents — those are gitignored (`*.process`, `*.done.json` in `.gitignore`) and must never enter Git history, matching the user's explicit requirement ("sentinel and process documents should not be included in git history").
- After reverting, re-run Check once against the restored state to verify recovery (reuse `verify_recovery_metrics` concept) before handing control back to Plan. Failure to recover routes to human handoff rather than looping.
- Sentinel `.process/revert.done.json` naming what was reverted and the verification result.

### 6. Commit (`commit_accepted_candidate`) — deterministic (+ optional skill)

**Requirements**
- Triggered only by Check's `accept` decision.
- Deterministic default: reuse `commit_accepted_candidate.py`/`GitCommitMessageBuilder` unchanged — `git add -A && git commit -m <templated message>`, record `best_accepted_state`, reset the consecutive-regression counter.
- Optional upgrade (recommended, matches user's "probably be a skill-based activity"): route message drafting through the `git-commit` skill so the commit subject/body follow the repo's observed Karma-style conventions (`type(scope): subject`) instead of the current hardcoded `feat(edd refinement): accept candidate {id}` template. If adopted, this becomes a thin `SkillActivity` that reads `plan.md`'s "changes made" section and produces a conventional message, then performs the same deterministic `git add -A && git commit` as today.
- Sentinel `.process/commit.done.json` naming the commit hash and files committed.

### 7. Loop control: iteration & token limits — deterministic, unchanged

- Reuse `check_refinement_limits.py` and `update_durable_counters.py` verbatim. No functional gap was found here; keep the existing check-before-Plan / update-after-Do / update-after-Check placement from `workflow.py`.
- Confirmed regression count (3-strikes stop) is already implemented in `plan_refinement.py`/`_budget_exhausted`; port it into the new `edd_plan` deterministic wrapper (the Cadence Activity around the `edd-plan` skill call), not into the skill itself — budget arithmetic must stay deterministic and untestable-by-the-model.

## New skills to write

| Skill | Purpose | Notes |
|---|---|---|
| `edd-plan` ✅ written, wired | Review guide doc + iteration history + latest check results; select one authorized action; produce a scoped, specific incremental plan. | Lives at `.devin/skills/edd-plan/SKILL.md`; wired via `src/edd_refinement_workflow/activities/edd_plan.py`/`edd_plan.config.json`. `edd-decide` was left in place, unreferenced, rather than renamed — that consolidation is still open (see Open Question 2). |
| `edd-do` ✅ written, wired | Load the target skill's prompt/tests, apply the plan's described change within the authorized scope, update the plan document with what actually changed. | Lives at `.devin/skills/edd-do/SKILL.md`; wired via `src/edd_refinement_workflow/activities/edd_do.py`/`edd_do.config.json`, following the `analyze-story` skill's shape (single responsibility, defines its own output contract, writes a sentinel). References the `promptfoo` skill for eval-suite edits. |

No new skill is required for Check, Regression Confirmation, Revert, or the loop-limit
gate — those are all deterministic per the vault's own classification table in
`grade-story-design-eval-refinement.md`. Commit may optionally use the existing
`git-commit` skill (no new skill needed, just a new Activity that invokes it).

## Existing skills/activities usable without change

- `.devin/skills/promptfoo` — referenced by `edd-do` for eval-suite mechanics.
- `.devin/skills/git-commit` — referenced by the optional skill-based Commit activity.
- `scripts/inspect-eval.js`, `npm run test {eval}.yaml` — the Check step's evaluation contract (ADR-021).
- `common/preflight.py`, `TargetRepositoryContext` — Setup's repo resolution.
- `common/skill_activity.py` (`SkillActivity`) — the base class `edd_plan`/`edd_do` Activities must subclass, exactly as `AnalyzeStorySkillActivity` does.
- `progress_record.py`, `coverage.py`, `evaluation_identity.py`, `quality_ratchet.py`, `check_refinement_limits.py`, `update_durable_counters.py`, `commit_accepted_candidate.py`, `git_commit_message.py`, `rerun_degraded_candidate.py`, `regression_recovery.py` — all reusable per the table in "What already works" above, with the one targeted change of threading the iteration-start baseline through regression comparison.

## Sentinel & process-file conventions to follow (per ADR-004 and existing practice)

- Sentinels live at `<input_parent>/.process/<activity-name>.done.json` and are gitignored (`*.process`, `*.done.json` already in `.gitignore`).
- Every agentic step (`edd_plan`, `edd_do`) and every gating deterministic step (`check_candidate`, `confirm_regression`, `revert_last_change`, `commit_accepted_candidate`, `initialize_edd_run`) writes its own sentinel naming: task name, files changed/created, and (for Check/Regression/Commit) the determination reached.
- Per-iteration artifacts live under `.process/edd/<run_id>/iterations/<n>/{plan,do,check,regression-confirm}.json`; the append-only human-readable plan narrative lives at `.process/edd/<run_id>/plan.md`. This mirrors the existing `.process/edd/<run_id>/progress.json` convention already documented in `vault/services/edd_refinement.md`.

## Data threaded around the loop (progress record additions)

The existing `ProgressRecord` schema needs one addition to close the regression-baseline
gap: each iteration's plan must persist `iteration_start_baseline` (a reference to either
`best_accepted_state.metrics` or the original baseline metrics, frozen at Plan time), so
Check and Regression Confirmation compare against the same target the plan believed it
was improving on — not a possibly-changed `best_accepted_state` if a race or manual edit
occurred mid-iteration. Everything else in the current schema (budgets, counters,
`candidate_history`, `best_accepted_state`, regression evidence, approvals) is sufficient
as-is.

## Open questions / decisions needed before implementation

1. **Commit policy per iteration.** Does Do's change land as an uncommitted working-tree diff that Check evaluates in place (today's behavior), with Commit being the *first* commit for that change — or does the workflow commit provisionally after every Do and rely on `git reset --hard`/`git revert` for Revert? This determines whether Revert is `git checkout -- <files>` (uncommitted) or `git reset --hard <prior-commit>` (committed-then-reverted). The user's phrasing ("take in the git history to revert") suggests the latter; recommend confirming and documenting explicitly, since it changes both Commit and Revert's implementation.
2. **Should `edd-decide` be renamed to `edd-plan` or kept as an internal step `edd-plan` calls?** Affects skill directory layout and any existing references to `edd-decide`.
3. **Commit message: deterministic template vs. `git-commit` skill.** Recommend the skill-based version per the user's own suggestion, but it adds one more agentic hop per accepted iteration; confirm the added cost/latency is acceptable.
4. **Where does the "guide document" belong physically** — target-repo `.process/edd/<run_id>/guide.md` (ephemeral, gitignored) vs. a durable doc under the target skill's own folder? Recommend ephemeral/gitignored, consistent with all other process artifacts, since it's regenerated from source-of-truth files (skill prompt, rubric, test cases) at Setup time.
5. **Regression-confirmation loop bound.** The user asked to "loop through the check again" — confirm this is exactly one extra rerun (matching ADR-017's existing "rerun once before confirming" rule) and not an open-ended retry loop.

## Suggested delivery order

1. Add `iteration_start_baseline` to the progress record and thread it through `quality_ratchet.py` / `rerun_degraded_candidate.py` (small, deterministic, unblocks everything else).
2. ✅ **Done (2026-09-23).** Write `edd-plan` and `edd-do` skills; wire them as `SkillActivity` subclasses replacing `plan_refinement.py`/`execute_refinement_action.py`, following `analyze_story.py` exactly. Cadence activity names are `edd_plan`/`edd_do` (renamed from `plan_refinement_action`/`execute_refinement_action`) — `workflow.py`, `module.py`, and their tests were updated to match; `iteration_start_baseline` is threaded from `edd-plan`'s `plan.json` into `PlanningResult`, but not yet consumed downstream (still step 1/3's job).
3. Generalize `run_baseline_evaluation.py` into a `check_candidate` activity usable for both baseline and post-Do candidates; add the `check.json`/sentinel writers.
4. Add the Setup guide-document writer.
5. Confirm and implement the commit/revert policy decision (Open Question 1), then wire Commit and Revert activities with sentinels.
6. Re-verify the existing budget/limit/regression-threshold tests still pass unchanged against the new activity boundaries.
7. Run the full loop against the `grade-story-design` eval suite (the same target used in the manual walkthrough documented in `vault/services/grade-story-design-eval-refinement.md`) as the first real end-to-end validation.
