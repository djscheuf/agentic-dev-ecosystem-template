# Stage 4 Certification Gap Analysis — Story Analysis Workflow

- **Branch:** `feat/workflow-orchestration`
- **Generated:** 2026-09-08
- **Scope reviewed:** `src/story_analysis_workflow/`, `.process/logs/`, `docs/edd/`, `docs/reqs/workflow-orchestration/`
- **Method:** Comparison against the five Stage 4 certification artifacts shown in the certification framework screenshot.

## Executive Summary

The branch builds a durable, well-instrumented Cadence workflow for the SDLC story-analysis process. It satisfies many of the **workflow definition** and **audit trail** prerequisites but is still missing evidence for **Stage 3 agent quality**, **adversarial guardrails**, **active punch-out testing**, and a consolidated **end-to-end success rate**. Token data in `devin-trajectory.json` is considered sufficient for the current certification needs; the missing piece is a consolidated `{workflow}.report.json` that makes that data easy to consume.

| Criterion | Verdict |
|---|---|
| 1. Workflow Definition | Partially Met |
| 2. Guardrails | Partially Met |
| 3. Punch-Out Evidence | Partially Met (most concerning) |
| 4. End-to-End Success Rate | Not Met (runs exist but are not consolidated/visible) |
| 5. Audit Trail | Sufficient (missing only a consolidated report) |

---

## 1. Workflow Definition

### Evidence

- `src/story_analysis_workflow/workflow.py:50-142` registers and runs the `StoryAnalysisWorkflow`, wiring four activities (`extract_story_intent`, `analyze_story`, `grade_story_analysis`, `repair_story_analysis`) through a Cadence workflow.
- `src/story_analysis_workflow/story_analysis_engine.py:143-214` contains the pure orchestration logic: sequential activity execution, a bounded grade/repair loop, and deterministic branching.
- `src/story_analysis_workflow/module.py:9-37` documents the activity-to-workflow registration.
- `docs/reqs/workflow-orchestration/implement-story-analysis-workflow-example.design.json` provides a step-by-step design with handoff contracts for all nine workflow steps.
- `docs/reqs/workflow-orchestration/activity-contracts.md` defines the uniform `SkillActivityInput`/`SkillActivityOutput` contract and per-skill data shapes.
- `docs/reqs/workflow-orchestration/story.md` lists the workflow acceptance criteria, including retry loops and human-in-the-loop escalation.

### Gaps

- **No Stage 3 certification evidence at 95%+.** The EDD CSVs in `docs/edd/` show per-skill pass rates, but several are below the 95% bar and none are framed as a Stage 3 certification:
  - `analyze-story.results.csv` — pass rates include 76.92%, 82.05%, 106.67%, 79.49%
  - `grade-story-analysis.results.csv` — pass rates include 88.89%, 91.67%, 83.33%, 90.63%
  - `extract-story-intent.results.csv` — some runs at 92.86% and 50%
- **No evidence that the agents no longer need regular manual correction.** The workflow design still routes to a human `accept/retry/abort` decision after failures and after exhausting the repair loop, which is a form of human correction.
- **Unused escalation path.** `src/story_analysis_workflow/escalation.py:12` defines `ACTIVITY_FLAGGED_AMBIGUITY`, but `src/story_analysis_workflow/story_analysis_engine.py` only escalates on `ACTIVITY_FAILURE_EXHAUSTED_RETRIES` and `GRADE_REPAIR_EXHAUSTED`. The mid-step ambiguity branch exists in the design docs but is not wired into the engine.

### Remediation

1. Add a `docs/edd/stage-3-certification.md` or similar artifact that links the latest eval runs and demonstrates each of the four agents passing its Stage 3 bar (95%+) on real work.
2. Instrument and report the rate of manual corrections/escalations to show the agents no longer require regular human fixes.
3. Either implement the `ACTIVITY_FLAGGED_AMBIGUITY` escalation path in the engine or remove it and update the design to match the code.

---

## 2. Guardrails

### Evidence

- `src/common/skill_activity.py:93-153` validates the skill sentinel file and `verify_params` before returning a `SkillActivityOutput`.
- `src/story_analysis_workflow/activities/grade_story_analysis.py:37-38` runs `score_analysis_grade()` on the grader output and adds a deterministic `passed` boolean to the activity result.
- `src/story_analysis_workflow/grade_repair.py:25-30` provides a deterministic `evaluate_grade_repair()` state machine.
- `src/story_analysis_workflow/grade_scoring.py:19-24` enforces an 80% fixed-floor pass threshold across five dimensions.

### Sentinel behavior

If a skill fails to write its sentinel file, the class-based `SkillActivity.execute` at `src/common/skill_activity.py:128-132` falls back to the `expected_output_path(skill_input)` and logs a warning. It does **not** raise an error and it does **not** check that the output file actually exists. The standalone `run_skill` helper at `src/common/skill_activity.py:179-185` does raise `SkillActivityError` on a missing sentinel, but the Story Analysis activities use the class-based form. The workflow then uses the returned `output_path` as the input for the next activity without any explicit `file-exists` check between steps.

### Gaps

- **Guardrails live inside activities, not between steps.** Sentinel verification, `score_analysis_grade`, and the 80% threshold are all embedded in `SkillActivity.execute` or in the `grade_story_analysis` activity. There is no separate workflow node or guardrail activity that runs *between* steps.
- **No `file-exists` guard between steps.** The engine does not verify that the file at the previous activity's `output_path` exists before scheduling the next activity.
- **No adversarial review agent.** The `grade_story_analysis` step is a normal SDLC grader, not an independent adversarial reviewer that challenges the prior step's output. The certification asks for guardrails that explicitly challenge prior outputs, which is different from the existing grade/repair loop.
- **No startup guardrail.** The workflow does not validate that `story_document` is a Markdown document before the first activity runs.
- **No post-grader artifact guardrail.** After `grade_story_analysis` passes, the workflow does not verify that the expected intent, analysis, and analysis-grade artifacts all exist in the parent directory of the original story.

### Remediation

1. Add a startup guardrail activity (or workflow decision) before `extract_story_intent` that asserts the input is a Markdown file and fails fast if it is not.
2. Add an explicit `file_exists` guard between every pair of successive activities (or a single `validate_artifact` activity) that confirms the prior step's output file exists and matches the expected schema before the next step runs.
3. Add a post-grader guardrail activity that confirms the three expected artifacts (`{stem}.intent.json`, `{stem}.analysis.json`, `{stem}.analysis-grade.json`) exist in the input story's parent directory.
4. Keep the existing in-activity sentinel checks, but document the new between-step guardrails in the design so they are visible as separate workflow nodes.
5. If guardrail failures are ambiguous, route them to the `ACTIVITY_FLAGGED_AMBIGUITY` human-escalation path.

---

## 3. Punch-Out Evidence

### Evidence

- `src/story_analysis_workflow/escalation.py:16-19` defines the explicit `HumanDecision` vocabulary: `retry`, `accept`, `abort`.
- `src/story_analysis_workflow/story_analysis_engine.py:92-116` opens a bounded `await_human_response` wait and re-escalates once on timeout.
- `src/story_analysis_workflow/workflow.py:123-125` exposes the `human_response` Signal.
- `src/story_analysis_workflow/signals.py:8-21` provides `send_human_response` and validates the decision before calling the client.
- `src/story_analysis_workflow/tests/test_story_analysis_engine.py:99-205` and `tests/unit/test_workflow_state.py:57-133` unit-test escalation, timeout, retry, accept, and abort paths.

### Gaps

- **No active bypass testing.** The only "invalid decision" test is `tests/unit/test_signal_query.py:34-41`, which validates `send_human_response` client-side before any network call. There is no test that sends an invalid `human_response` to a live workflow and asserts the workflow ignores/blocks it.
- **No mid-step punch-out.** As noted in the Workflow Definition section, the `ACTIVITY_FLAGGED_AMBIGUITY` reason is defined but never used, so there is no human-escalation point in the middle of an activity step.
- **No distinction between "fail workflow" and "punch to human" beyond final status.** The engine produces `final_status` values of `passed`, `human_resolved`, and `failed`, but the failure case does not explicitly log whether the failure was an automated guardrail failure or a human `abort`.
- **No recorded escalation runs in `.process/logs/`.** The logged runs are happy path. A punch-out point that has not been exercised in a real or recorded run does not qualify.

### Remediation

1. Add an integration/e2e test that attempts to bypass the human-escalation wait (e.g., by sending an invalid `human_response` decision or by skipping the Signal entirely) and asserts the workflow remains in an `awaiting_signal` state or fails safely.
2. Implement and test the `ACTIVITY_FLAGGED_AMBIGUITY` escalation path so a step can explicitly "punch out" to a human mid-execution.
3. Add explicit audit log entries for each human decision, clearly distinguishing automated `failed` from human-initiated `abort`/`accept`.
4. Record at least one manual run of the escalation path and commit the resulting `.process/logs/` tree as evidence.

---

## 4. End-to-End Success Rate

### Evidence

- `tests/e2e/test_audit_trail.py:19-80` demonstrates one end-to-end happy-path run that completes successfully.
- `.process/logs/` contains two completed `StoryAnalysisWorkflow` executions in the working tree; additional runs are reported to have been performed outside the committed evidence.
- `docs/edd/*.results.csv` provides per-skill eval pass rates over time.

### Gaps

- **No consolidated end-to-end success rate report.** The EDD CSVs are per-skill; they do not measure the full workflow from start to finish.
- **Success data not visible/auditable.** If other runs exist, they are not present in the repository or logs under review, so they cannot be evaluated by an examiner.
- **No definition of "success" for the whole workflow.** The workflow can close as `passed`, `human_resolved`, or `failed`. The certification wants a single end-to-end number (e.g., "X% of runs reach a non-failed terminal state without human retry"), which is not reported.

### Remediation

1. Define the end-to-end success metric explicitly (e.g., percentage of runs with `final_status != "failed"` over a representative sample).
2. Run a small benchmark across happy path, one repair, exhausted repair + human abort, and exhausted repair + human accept, and record start-to-finish outcomes.
3. Generate a `{workflow}.report.json` at workflow completion that records the final status, number of attempts, and a per-step outcome summary so success can be aggregated across runs.
4. Commit or otherwise make the additional historical runs available to the examiner, or run a fresh representative sample and store the resulting `.process/logs/` and reports.

---

## 5. Audit Trail

### Evidence

- `src/common/workflow_logger.py:183-286` creates per-run workflow and activity log files under `.process/logs/{workflow_id}/{run_id}/`.
- `.process/logs/.../workflow.log` records step names, grade decisions, `attempt_count`, `escalated`, and `final_status`.
- `.process/logs/.../activity.log` records `RunSkill`, `StartDevinInvocation` (including `model` and `permission_mode`), and `CompleteDevinInvocation` with `duration_ms`.
- `.process/logs/.../devin-trajectory.json` contains per-activity `final_metrics` with `total_prompt_tokens`, `total_completion_tokens`, and `total_cached_tokens`.
- `src/common/harness.py:9-14` and `src/common/atif_usage.py:34-38` define a `HarnessUsage` dataclass that can carry `prompt_tokens`, `completion_tokens`, `cached_tokens`, and `cost_usd`.
- `tests/e2e/test_audit_trail.py:59-71` asserts that the Cadence event history contains the four skill activities and that the workflow returns a `passed` result.

### Gaps

- **No consolidated `{workflow}.report.json`.** The per-activity `devin-trajectory.json` files contain token data, but there is no single roll-up document that summarizes, for a given workflow run, the steps, retries, model, and token costs in one place.
- **Token/cost data is not in the structured text logs.** `activity.log` only records `usage_available=True` and `duration_ms`; a reviewer must open each `devin-trajectory.json` to read token counts.
- **Cost is missing from the observed ATIF export.** The `devin-trajectory.json` files contain token counts but no `total_cost_usd` key. `read_atif_usage_result()` cannot populate `HarnessUsage.cost_usd` unless the CLI adds that field or a price-table fallback is added.

### Remediation

1. Write a `{workflow}.report.json` at workflow completion that includes:
   - run metadata (`workflow_id`, `run_id`, `story_document`, `final_status`, `attempt_count`)
   - per-step summary (`step`, `activity_type`, `model`, `permission_mode`, `prompt_tokens`, `completion_tokens`, `cached_tokens`, `cost_usd`, `duration_ms`, `output_path`)
2. Add a `SkillActivityOutput` field for `usage` and log it to `activity.log` and `workflow.log` so the structured logs carry the same data as `devin-trajectory.json`.
3. If cost is required in the report and not provided by ATIF, add a per-model cost table or ask the harness to emit `total_cost_usd`.

---

## Overall Verdict

The `feat/workflow-orchestration` branch is **not yet Stage 4 certified**. The workflow definition and audit-trail scaffolding are the strongest areas. The biggest blockers are:

1. Missing Stage 3 95%+ certification evidence for the agents.
2. Missing active punch-out/bypass testing and the unused `ACTIVITY_FLAGGED_AMBIGUITY` path.
3. Missing end-to-end success rate report; additional runs are not visible to an examiner.
4. Missing a consolidated `{workflow}.report.json` and structured log token/cost roll-up.
5. Guardrails are embedded in activities rather than positioned as explicit between-step orchestration nodes, and there is no `file-exists` guard between steps, no startup Markdown guardrail, and no post-grader artifact verification.

The branch does contain groundwork for several of these (especially the `HarnessUsage`/`read_atif_usage_result` plumbing and the `human_response` Signal design), but the evidence, tests, and guardrail activities needed for certification are not complete.