---
name: edd-plan
description: Reviews the current EDD refinement run state (refinement.yaml context document, evaluation history, and prior plan/do/check outcomes) for a target skill's evaluation, and selects the next single authorized refinement action. Use at the start of every EDD refinement iteration, before edd-do.
---

## Steps:

### 1. Read the Run's Process Directory
- Read the EDD run folder provided as input, e.g. `.process/edd/<run_id>/`.
- Read `progress.json` for remaining iteration/token budgets, `best_accepted_state`, `consecutive_confirmed_regressions`, and `candidate_history`.
- Read the running `refinement.yaml` document. It embeds the original `edd_input` object, which supplies the target skill's rubric/prompt text, the required-test-case catalog, the baseline metrics, the per-test-case coverage map, and the authorized modification scope.
- Also read the highest-numbered `iterations/<n>/{plan,do,check}.json` files for the current iteration state.

### 2. Review the Latest Evaluation Evidence
- Read the two most recent `check.json` results (or the single baseline result if this is the first iteration).
- Identify common failure patterns: are failures concentrated in one rubric dimension, one fixture, or one assertion helper?
- Cross-reference the required-test-case coverage map in the latest `check.json` against the target skill's `_tests/*.tests.yaml` and required-test-case catalog to find any required case with no covering assertion.

### 3. Review Prior Plan/Do/Check History
- Read every prior iteration's `plan.json`, `do.json`, and its outcome (`accepted` / `rejected` / `reverted`) from `candidate_history` and `refinement.yaml`.
- Do not propose an action that repeats a change already confirmed as a regression and reverted, unless the new plan explicitly states what will be different this time and why it is expected to avoid the prior failure.

### 4. Select the Next Action
Choose exactly one action from this closed taxonomy:

- **`refine_skill`** — modify the target skill's `SKILL.md` / prompt / instructions.
- **`repair`** — fix a defect in a scripted assertion, fixture, or evaluation helper (a fixture bug or helper bug, not a real model gap).
- **`add_coverage`** — add a missing required test case, or extend deterministic assertions, without weakening any existing expectation.
- **`refine_supporting_docs`** — modify an authorized reference, example, template, or other document the target skill depends on.
- **`propose_evaluation_expectation_change`** — change what an evaluation expects (an LLM rubric, an expected/floor score). This action requires explicit human approval before `edd-do` may apply it; never select it as a first attempt at a failure.
- **`stop`** — no defensible action remains, the objective is already met, or a budget/regression limit blocks another safe attempt.

Apply this priority order, mirroring the manually-run refinement process:
1. If any evaluation is currently failing, prefer `repair` when the failure traces to a fixture/assertion/helper defect, or `refine_skill` when the failure is a genuine model gap against a rubric the evaluation correctly represents. Fix fixture contradictions before ever relaxing an assertion.
2. If all evaluations pass but required test cases remain uncovered, choose `add_coverage`.
3. Only propose `propose_evaluation_expectation_change` when a prompt or fixture fix has already been attempted against the same failure in a prior iteration and did not resolve it, and the evaluation itself looks defective (ambiguous rubric wording, an incorrect expected score, brittle phrasing matching).
4. Choose `stop` when every required test case passes and is covered, when the remaining iteration/token budget cannot support another safe attempt, or when three consecutive proposals have already been confirmed regressions.

Record the exact metric snapshot this iteration is trying to beat as `iteration_start_baseline` (the current `best_accepted_state.metrics` if one exists, otherwise the original baseline). This value is frozen for the whole iteration and must not be re-derived later even if `best_accepted_state` changes.

### 5. Describe the Change with Enough Detail to Guide Implementation
- Write a specific description of what to change and why
- Name specific files, fixtures, assertion blocks, or prompt sections whenever they are known from the evidence, as `intended_files`. This list must be a subset of the run's overall authorized `modification_scope`.
- State the expected, falsifiable effect (e.g. "required test case TC-14 moves from uncovered to covered" or "the `layer-responsibilities` assertion for the admin-tactic fixture stops failing without changing its `score_floor`").

### 6. Create the Plan JSON File
- Create `.process/edd/<run_id>/iterations/<n>/plan.json`, where `<n>` is one greater than the highest existing iteration number under `.process/edd/<run_id>/iterations/`, or `1` if none exist.
  - if unable to write, send the plan JSON in chat instead.
- The JSON MUST follow `/schema/plan.schema.json`.

### 7. Append to the Running Refinement Document
- Append a new, dated section to `.process/edd/<run_id>/refinement.yaml` (create it if it doesn't exist yet) summarizing this iteration's number, selected action, rationale, evidence, intended files, and expected effect.
- This document is append-only: never rewrite, reorder, or delete a prior iteration's section. It is the audit trail!

### 8. Write the Sentinel File
- create `<input_parent>/.process/` when needed and write `{skill-name}.done.json` there; use the repository-root `.process/` only when no input path is supplied. The sentinel must not be removed after verification.
- the sentinel file will follow @/schema/sentinel.schema.json.
- set the task field to "{skill-name}".
- the verify_params of the sentinel file will follow @/schema/verify-params.schema.json.
- set the verify_params as follows:
    - set "plan_path" to the path of `iterations/<n>/plan.json`, relative to repo root.
    - set "refinement_path" to the path of `refinement.yaml`, relative to repo root.
    - set "iteration_number" to `<n>`.
    - set "action" to the selected action.
