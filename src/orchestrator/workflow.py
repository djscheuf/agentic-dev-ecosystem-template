"""The Story Analysis Cadence Workflow.

Thin glue: wires `StoryAnalysisEngine` (all the sequencing/decision logic, unit
tested in `tests/test_story_analysis_engine.py`) to real Cadence primitives --
`execute_activity` for the four SDLC skill Activities, `sleep`/`wait_condition`
for the bounded human-escalation wait (the Python client has no `Selector`;
see `.devin/skills/cadence-workflow-orchestration/03-python-client/feature-gaps.md`),
and a `human_response` Signal + `get_status` Query for the human-in-the-loop
acceptance criteria.

See `docs/reqs/workflow-orchestration/implement-story-analysis-workflow-example.design.json`
for the full step-by-step design this implements.
"""

import asyncio
import dataclasses
from datetime import timedelta
from typing import Any, Optional

from cadence import Registry, workflow
from cadence.error import ActivityFailure as CadenceActivityFailure
from cadence.workflow import RetryPolicy, execute_activity, sleep, wait_condition

from .activities.analyze_story import analyze_story
from .activities.extract_story_intent import extract_story_intent
from .activities.grade_story_analysis import grade_story_analysis
from .activities.repair_story_analysis import repair_story_analysis
from .escalation import HumanResponse, parse_human_response
from .grade_repair import DEFAULT_MAX_ATTEMPTS
from .story_analysis_engine import ActivityFailure, DEFAULT_ESCALATION_TIMEOUT, StoryAnalysisEngine

registry = Registry()
registry.register_activity(extract_story_intent)
registry.register_activity(analyze_story)
registry.register_activity(grade_story_analysis)
registry.register_activity(repair_story_analysis)

# Cadence-managed retries per Activity attempt, distinct from the workflow's own
# grade-repair attempt_count (see instrumentation_events.InvokeSkillActivity).
ACTIVITY_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=5),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(minutes=5),
    maximum_attempts=3,
)
ACTIVITY_START_TO_CLOSE_TIMEOUT = timedelta(minutes=30)


@registry.workflow(name="StoryAnalysisWorkflow")
class StoryAnalysisWorkflow:
    def __init__(self) -> None:
        self._pending_human_response: Optional[HumanResponse] = None
        self._engine: Optional[StoryAnalysisEngine] = None

    async def _execute_skill_activity(self, name: str, *args: Any) -> dict:
        try:
            return await execute_activity(
                name,
                dict,
                *args,
                start_to_close_timeout=ACTIVITY_START_TO_CLOSE_TIMEOUT,
                retry_policy=ACTIVITY_RETRY_POLICY,
            )
        except CadenceActivityFailure as exc:
            raise ActivityFailure(str(exc)) from exc

    async def _extract_story_intent(self, story_document: str) -> dict:
        return await self._execute_skill_activity("extract_story_intent", [story_document], "")

    async def _analyze_story(self, intent_path: str) -> dict:
        return await self._execute_skill_activity("analyze_story", intent_path)

    async def _grade_story_analysis(self, analysis_path: str) -> dict:
        return await self._execute_skill_activity("grade_story_analysis", analysis_path)

    async def _repair_story_analysis(self, analysis_path: str, grade_path: str, notes: str = "") -> dict:
        return await self._execute_skill_activity("repair_story_analysis", analysis_path, grade_path, notes)

    async def _await_human_response(self, timeout: timedelta) -> Optional[HumanResponse]:
        """Bounded wait for the `human_response` Signal.

        The Python client has no Go-style `Selector`, so we race a
        `wait_condition` against a `sleep` timer on the same deterministic
        workflow event loop.
        """
        self._pending_human_response = None
        wait_task = asyncio.ensure_future(wait_condition(lambda: self._pending_human_response is not None))
        timer_task = asyncio.ensure_future(sleep(timeout))
        done, pending = await asyncio.wait({wait_task, timer_task}, return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            task.cancel()

        if wait_task in done:
            return self._pending_human_response
        return None

    @workflow.run
    async def run(self, story_document: str, config: Optional[dict] = None) -> dict:
        config = config or {}
        engine = StoryAnalysisEngine(
            execute_extract_story_intent=self._extract_story_intent,
            execute_analyze_story=self._analyze_story,
            execute_grade_story_analysis=self._grade_story_analysis,
            execute_repair_story_analysis=self._repair_story_analysis,
            await_human_response=self._await_human_response,
            max_attempts=config.get("max_attempts", DEFAULT_MAX_ATTEMPTS),
            escalation_timeout=timedelta(seconds=config["escalation_timeout_seconds"])
            if "escalation_timeout_seconds" in config
            else DEFAULT_ESCALATION_TIMEOUT,
        )
        self._engine = engine
        result = await engine.run(story_document)
        return dataclasses.asdict(result)

    @workflow.signal
    def human_response(self, decision: str, notes: str = "") -> None:
        self._pending_human_response = parse_human_response(decision, notes)

    @workflow.query
    def get_status(self) -> dict:
        engine = self._engine
        if engine is None:
            return {"status": "running", "attempt_count": 0, "escalated": False, "escalation_reason": None}
        return {
            "status": engine.status,
            "attempt_count": engine.attempt_count,
            "escalated": engine.escalated,
            "escalation_reason": engine.escalation_reason.value if engine.escalation_reason else None,
        }
