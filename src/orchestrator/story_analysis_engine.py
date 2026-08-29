"""Pure `asyncio` engine for the Story Analysis Workflow.

Contains all of the sequencing/decision logic described in
`docs/reqs/workflow-orchestration/implement-story-analysis-workflow-example.design.json`
(steps 2-9): run the four SDLC skill Activities, loop on the grade/repair cycle
(bounded to `max_attempts`), and escalate to a human via a Signal-or-Timer wait
whenever the loop is exhausted or an Activity fails.

This module never imports `cadence` so it can be unit tested directly with plain
async fakes (see `tests/test_story_analysis_engine.py`) -- as of
`cadence-python-client` 0.3.0 there is no released `TestWorkflowEnvironment` yet
(see `docs/reqs/workflow-orchestration/workflow-engine.test-plan.md`). The real
`@registry.workflow()` class in `workflow.py` wires this engine to Cadence's
`execute_activity` / `sleep` / `wait_condition` primitives.
"""

from dataclasses import dataclass
from datetime import timedelta
from typing import Awaitable, Callable, Optional

from .escalation import EscalationReason, HumanDecision, HumanResponse
from .grade_repair import DEFAULT_MAX_ATTEMPTS, GradeRepairDecision, GradeRepairState, evaluate_grade_repair

DEFAULT_ESCALATION_TIMEOUT = timedelta(hours=4)


class ActivityFailure(RuntimeError):
    """Raised when a skill Activity exhausts its RetryPolicy."""


@dataclass(frozen=True)
class WorkflowResult:
    final_analysis_path: Optional[str]
    passed: bool
    attempt_count: int
    escalated: bool
    final_status: str  # "passed" | "human_resolved" | "failed"


AwaitHumanResponse = Callable[[timedelta], Awaitable[Optional[HumanResponse]]]


class StoryAnalysisEngine:
    def __init__(
        self,
        *,
        execute_extract_story_intent: Callable[[str], Awaitable[dict]],
        execute_analyze_story: Callable[[str], Awaitable[dict]],
        execute_grade_story_analysis: Callable[[str], Awaitable[dict]],
        execute_repair_story_analysis: Callable[..., Awaitable[dict]],
        await_human_response: AwaitHumanResponse,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
        escalation_timeout: timedelta = DEFAULT_ESCALATION_TIMEOUT,
    ) -> None:
        self._execute_extract_story_intent = execute_extract_story_intent
        self._execute_analyze_story = execute_analyze_story
        self._execute_grade_story_analysis = execute_grade_story_analysis
        self._execute_repair_story_analysis = execute_repair_story_analysis
        self._await_human_response = await_human_response
        self.max_attempts = max_attempts
        self.escalation_timeout = escalation_timeout

        self.status = "running"
        self.attempt_count = 0
        self.escalated = False
        self.escalation_reason: Optional[EscalationReason] = None

    def _terminal(self, analysis_path: Optional[str], final_status: str) -> WorkflowResult:
        self.status = final_status
        return WorkflowResult(
            final_analysis_path=analysis_path,
            passed=final_status == "passed",
            attempt_count=self.attempt_count,
            escalated=self.escalated,
            final_status=final_status,
        )

    async def _escalate(self, reason: EscalationReason) -> Optional[HumanResponse]:
        """Open a bounded wait for the `human_response` Signal.

        Re-escalates (re-notifies) once if the first wait times out. If the
        second wait also times out, returns None so the caller can fail
        gracefully instead of blocking forever.
        """
        self.escalated = True
        self.escalation_reason = reason
        self.status = "awaiting_signal"

        response = await self._await_human_response(self.escalation_timeout)
        if response is not None:
            return response

        # Timed out once: re-escalate (re-notify) and wait again.
        response = await self._await_human_response(self.escalation_timeout)
        return response

    async def _run_activity_with_escalation(
        self, fn: Callable[..., Awaitable[dict]], *args
    ) -> tuple[Optional[dict], Optional[WorkflowResult]]:
        """Run a skill Activity, escalating on failure.

        Returns `(activity_result, None)` on success, or `(None, terminal_result)`
        if the failure could not be resolved (human aborted/accepted or the
        escalation itself timed out) and the workflow must stop.
        """
        while True:
            try:
                return await fn(*args), None
            except ActivityFailure:
                response = await self._escalate(EscalationReason.ACTIVITY_FAILURE_EXHAUSTED_RETRIES)
                if response is None or response.decision != HumanDecision.RETRY:
                    is_abort = response is None or response.decision == HumanDecision.ABORT
                    final_status = "failed" if is_abort else "human_resolved"
                    return None, self._terminal(None, final_status)
                # decision == RETRY: loop and retry the same activity call.

    async def run(self, story_document: str) -> WorkflowResult:
        intent, failure_result = await self._run_activity_with_escalation(
            self._execute_extract_story_intent, story_document
        )
        if failure_result is not None:
            return failure_result

        analysis, failure_result = await self._run_activity_with_escalation(
            self._execute_analyze_story, intent["output_path"]
        )
        if failure_result is not None:
            return failure_result

        analysis_path = analysis["output_path"]
        notes = ""

        while True:
            grade, failure_result = await self._run_activity_with_escalation(
                self._execute_grade_story_analysis, analysis_path
            )
            if failure_result is not None:
                return failure_result

            decision = evaluate_grade_repair(
                grade["passed"], GradeRepairState(self.attempt_count, self.max_attempts)
            )

            if decision == GradeRepairDecision.PROCEED:
                return self._terminal(analysis_path, "passed")

            if decision == GradeRepairDecision.REPAIR:
                self.attempt_count += 1
                repaired, failure_result = await self._run_activity_with_escalation(
                    self._execute_repair_story_analysis, analysis_path, grade["output_path"], notes
                )
                if failure_result is not None:
                    return failure_result
                analysis_path = repaired["output_path"]
                notes = ""
                continue

            # ESCALATE: the grade-repair loop is exhausted.
            response = await self._escalate(EscalationReason.GRADE_REPAIR_EXHAUSTED)

            if response is None or response.decision == HumanDecision.ABORT:
                self.status = "failed"
                return self._terminal(analysis_path, "failed")

            if response.decision == HumanDecision.ACCEPT:
                return self._terminal(analysis_path, "human_resolved")

            # RETRY: immediately repair using the human's guidance, then give
            # the loop a fresh attempt budget for the re-graded result.
            repaired, failure_result = await self._run_activity_with_escalation(
                self._execute_repair_story_analysis, analysis_path, grade["output_path"], response.notes
            )
            if failure_result is not None:
                return failure_result
            analysis_path = repaired["output_path"]
            self.attempt_count = 0
            notes = ""
