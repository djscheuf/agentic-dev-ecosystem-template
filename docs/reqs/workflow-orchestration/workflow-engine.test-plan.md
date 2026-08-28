# Workflow Engine — TDD Test Plan

Source: `docs/reqs/workflow-orchestration/streams/workflow-engine.stream.json`

## Architecture note (see `vault/services/cadence.md`)

`cadence-python-client` 0.3.0 (latest on PyPI) does not ship `cadence.testing.TestWorkflowEnvironment`
yet (it exists on the `main` branch but is unreleased). To keep tests fast, deterministic, and free of
a real Cadence server, the orchestration logic is split:

- **`story_analysis_engine.py`** — pure `asyncio` engine with all sequencing/decision logic
  (grade-repair loop, escalation, human-response handling). Takes the four skill-activity callables,
  a `sleep` function, and a signal-wait function as constructor arguments, so it never imports
  `cadence`. Fully unit-testable with fakes.
- **`workflow.py`** — thin `@registry.workflow()` class wiring the engine to real
  `cadence.workflow.execute_activity` / `sleep` / `wait_condition` and the `human_response` signal.
- **`skill_activity.py`** — subprocess wrapper (`devin` CLI) shared by the four Activities, with the
  `subprocess.run`-like runner injected for testing.

## Test cases

### `grade_repair.py` (pure decision function)
1. `evaluate_grade_repair_WhenPassed_ReturnsProceed`
2. `evaluate_grade_repair_WhenFailedBelowMaxAttempts_ReturnsRepair`
3. `evaluate_grade_repair_WhenFailedAtMaxAttempts_ReturnsEscalate`
4. `evaluate_grade_repair_WhenFailedAboveMaxAttempts_ReturnsEscalate` (defensive)

### `skill_activity.py` (subprocess wrapper — AC: repository state changes, idempotency, unicode passthrough)
5. `run_skill_OnSuccess_ReturnsOutputPathFromSentinel`
6. `run_skill_WhenDevinExitsNonZero_RaisesSkillActivityError`
7. `run_skill_WhenSentinelMissing_RaisesSkillActivityError`
8. `run_skill_WhenSentinelTaskMismatched_RaisesSkillActivityError`
9. `run_skill_WhenRetried_RemovesStaleSentinelFirst` (idempotent retry edge case)
10. `run_skill_PassesUnicodeStoryTextUnmodifiedInPrompt` (unicode edge case)

### `story_analysis_engine.py` (StoryAnalysisEngine — integration of the four steps)
11. `run_HappyPath_CompletesWithoutEscalation` (AC: happy path)
12. `run_WhenGradeFailsOnceThenPasses_RepairsOnceAndProceeds` (AC: repair/re-grade cycle)
13. `run_WhenGradeRepairLoopExhausted_EscalatesWithGradeRepairExhaustedReason` (AC: bounded to 3 attempts)
14. `run_WhenActivityFails_EscalatesWithActivityFailureReason` (AC: retries exhausted -> escalate, not silent completion)
15. `run_WhenHumanAccepts_ReturnsHumanResolvedResult`
16. `run_WhenHumanAborts_ReturnsFailedResult`
17. `run_WhenHumanRetries_ResetsAttemptCountAndRepairsWithNotes`
18. `run_WhenEscalationTimesOutOnce_ReEscalatesThenSucceedsOnSecondResponse` (AC/edge: bounded human wait, re-notify)
19. `run_WhenEscalationTimesOutTwice_FailsGracefully` (AC/edge: bounded wait, no signal -> fail gracefully)

## Out of scope for automated tests (documented manually in the runbook instead)

- Real Cadence server interaction (worker polling, replay after crash, domain/task-list scoping,
  Cadence-service-unavailable retries) — these require a live `ubercadence/server` instance; see
  `docs/reqs/workflow-orchestration/local-dev-prerequisites.md` and
  `src/orchestrator/README.md` for the manual verification steps.
- Cadence payload size limits — enforced server-side, not application logic.
