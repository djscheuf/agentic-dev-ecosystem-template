"""Unit tests for ``StoryAnalysisEngine`` state and status transitions."""

import pytest

from orchestrator.escalation import EscalationReason, HumanDecision, HumanResponse
from orchestrator.story_analysis_engine import ActivityFailure, StoryAnalysisEngine


class FakeActivities:
    def __init__(self):
        self.calls = []
        self.extract_result = {"output_path": ".process/intent.json"}
        self.analyze_result = {"output_path": ".process/analysis.json"}
        self.grade_results = [{"output_path": ".process/grade.json", "passed": True}]
        self.repair_result = {"output_path": ".process/analysis.json"}
        self.extract_exception = None

    async def extract_story_intent(self, story_document):
        self.calls.append(("extract_story_intent", story_document))
        if self.extract_exception is not None:
            raise self.extract_exception
        return self.extract_result

    async def analyze_story(self, intent_path):
        self.calls.append(("analyze_story", intent_path))
        return self.analyze_result

    async def grade_story_analysis(self, analysis_path):
        self.calls.append(("grade_story_analysis", analysis_path))
        if len(self.grade_results) > 1:
            return self.grade_results.pop(0)
        return self.grade_results[0]

    async def repair_story_analysis(self, analysis_path, grade_path, notes=""):
        self.calls.append(("repair_story_analysis", analysis_path, grade_path, notes))
        return self.repair_result


def make_engine(activities, *, human_responses=None, max_attempts=3):
    human_responses = list(human_responses or [])

    async def await_human_response(timeout):
        if human_responses:
            return human_responses.pop(0)
        return None

    return StoryAnalysisEngine(
        execute_extract_story_intent=activities.extract_story_intent,
        execute_analyze_story=activities.analyze_story,
        execute_grade_story_analysis=activities.grade_story_analysis,
        execute_repair_story_analysis=activities.repair_story_analysis,
        await_human_response=await_human_response,
        max_attempts=max_attempts,
    )


@pytest.mark.asyncio
async def test_engine_status_tracks_escalation_reason_on_activity_failure():
    activities = FakeActivities()
    activities.extract_exception = ActivityFailure("boom")
    engine = make_engine(activities, human_responses=[HumanResponse(HumanDecision.ABORT)])

    await engine.run("story text")

    assert engine.status == "failed"
    assert engine.escalated is True
    assert engine.escalation_reason == EscalationReason.ACTIVITY_FAILURE_EXHAUSTED_RETRIES


@pytest.mark.asyncio
async def test_engine_attempt_count_caps_at_max_before_escalation():
    activities = FakeActivities()
    activities.grade_results = [{"output_path": ".process/grade.json", "passed": False}]
    engine = make_engine(
        activities,
        human_responses=[HumanResponse(HumanDecision.ABORT)],
        max_attempts=3,
    )

    result = await engine.run("story text")

    assert result.attempt_count == 3
    assert result.escalated is True
    assert result.final_status == "failed"


@pytest.mark.asyncio
async def test_engine_attempt_count_resets_after_human_retry():
    activities = FakeActivities()
    # Three failing grades exhaust the loop, then human retries with a final pass.
    activities.grade_results = [
        {"output_path": ".process/grade.json", "passed": False},
        {"output_path": ".process/grade.json", "passed": False},
        {"output_path": ".process/grade.json", "passed": False},
        {"output_path": ".process/grade.json", "passed": False},
        {"output_path": ".process/grade.json", "passed": True},
    ]
    engine = make_engine(
        activities,
        human_responses=[HumanResponse(HumanDecision.RETRY, notes="try again")],
        max_attempts=3,
    )

    result = await engine.run("story text")

    assert result.passed is True
    assert result.escalated is True
    assert result.attempt_count == 0


@pytest.mark.asyncio
async def test_engine_status_is_awaiting_signal_during_escalation():
    activities = FakeActivities()
    activities.grade_results = [{"output_path": ".process/grade.json", "passed": False}]

    captured_status = []

    async def await_human_response(timeout):
        captured_status.append(engine.status)
        return None

    engine = StoryAnalysisEngine(
        execute_extract_story_intent=activities.extract_story_intent,
        execute_analyze_story=activities.analyze_story,
        execute_grade_story_analysis=activities.grade_story_analysis,
        execute_repair_story_analysis=activities.repair_story_analysis,
        await_human_response=await_human_response,
        max_attempts=3,
    )

    await engine.run("story text")

    assert captured_status == ["awaiting_signal", "awaiting_signal"]
