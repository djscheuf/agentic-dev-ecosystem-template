import pytest

from story_analysis_workflow.escalation import EscalationReason, HumanDecision, HumanResponse
from story_analysis_workflow.story_analysis_engine import ActivityFailure, StoryAnalysisEngine


class FakeActivities:
    """Records calls and lets each test script canned results/failures per call."""

    def __init__(self):
        self.calls = []
        self.extract_result = {"output_path": "docs/foo.intent.json"}
        self.analyze_result = {"output_path": "docs/foo.analysis.json"}
        # Queue of grade results consumed one-per-call; last one repeats if exhausted.
        self.grade_results = [{"output_path": "docs/foo.analysis-grade.json", "passed": True}]
        self.repair_result = {"output_path": "docs/foo.analysis.json"}
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
async def test_run_happy_path_completes_without_escalation():
    activities = FakeActivities()
    activities.grade_results = [{"output_path": "g.json", "passed": True}]
    engine = make_engine(activities)

    result = await engine.run("story text")

    assert result.passed is True
    assert result.escalated is False
    assert result.final_status == "passed"
    assert result.attempt_count == 0
    assert [c[0] for c in activities.calls] == [
        "extract_story_intent",
        "analyze_story",
        "grade_story_analysis",
    ]


@pytest.mark.asyncio
async def test_run_when_grade_fails_once_then_passes_repairs_once_and_proceeds():
    activities = FakeActivities()
    activities.grade_results = [
        {"output_path": "g1.json", "passed": False},
        {"output_path": "g2.json", "passed": True},
    ]
    engine = make_engine(activities)

    result = await engine.run("story text")

    assert result.passed is True
    assert result.attempt_count == 1
    assert [c[0] for c in activities.calls] == [
        "extract_story_intent",
        "analyze_story",
        "grade_story_analysis",
        "repair_story_analysis",
        "grade_story_analysis",
    ]


@pytest.mark.asyncio
async def test_run_when_grade_repair_loop_exhausted_escalates_with_grade_repair_exhausted_reason():
    activities = FakeActivities()
    activities.grade_results = [{"output_path": "g.json", "passed": False}]
    engine = make_engine(activities, human_responses=[HumanResponse(HumanDecision.ABORT)], max_attempts=3)

    result = await engine.run("story text")

    assert result.escalated is True
    assert engine.escalation_reason == EscalationReason.GRADE_REPAIR_EXHAUSTED
    assert result.attempt_count == 3
    assert result.final_status == "failed"


@pytest.mark.asyncio
async def test_run_when_activity_fails_escalates_with_activity_failure_reason():
    activities = FakeActivities()
    activities.extract_exception = ActivityFailure("boom")
    engine = make_engine(activities, human_responses=[HumanResponse(HumanDecision.ABORT)])

    result = await engine.run("story text")

    assert result.escalated is True
    assert engine.escalation_reason == EscalationReason.ACTIVITY_FAILURE_EXHAUSTED_RETRIES
    assert result.final_status == "failed"


@pytest.mark.asyncio
async def test_run_when_human_accepts_returns_human_resolved_result():
    activities = FakeActivities()
    activities.grade_results = [{"output_path": "g.json", "passed": False}]
    engine = make_engine(activities, human_responses=[HumanResponse(HumanDecision.ACCEPT, notes="good enough")])

    result = await engine.run("story text")

    assert result.escalated is True
    assert result.final_status == "human_resolved"
    assert result.passed is False


@pytest.mark.asyncio
async def test_run_when_human_aborts_returns_failed_result():
    activities = FakeActivities()
    activities.grade_results = [{"output_path": "g.json", "passed": False}]
    engine = make_engine(activities, human_responses=[HumanResponse(HumanDecision.ABORT)])

    result = await engine.run("story text")

    assert result.final_status == "failed"
    assert result.escalated is True


@pytest.mark.asyncio
async def test_run_when_human_retries_resets_attempt_count_and_repairs_with_notes():
    activities = FakeActivities()
    # Every grade call fails until the loop is exhausted (3 attempts), then the
    # human retries once with notes, after which the next grade passes.
    activities.grade_results = [
        {"output_path": "g0.json", "passed": False},
        {"output_path": "g1.json", "passed": False},
        {"output_path": "g2.json", "passed": False},
        {"output_path": "g3.json", "passed": False},
        {"output_path": "g4.json", "passed": True},
    ]
    engine = make_engine(
        activities,
        human_responses=[HumanResponse(HumanDecision.RETRY, notes="focus on edge cases")],
        max_attempts=3,
    )

    result = await engine.run("story text")

    assert result.passed is True
    assert result.escalated is True
    assert result.final_status == "passed"
    # The repair call made in response to the human's retry decision carries their notes.
    retry_repair_calls = [c for c in activities.calls if c[0] == "repair_story_analysis"]
    assert retry_repair_calls[-1][3] == "focus on edge cases"


@pytest.mark.asyncio
async def test_run_when_escalation_times_out_once_re_escalates_then_succeeds_on_second_response():
    activities = FakeActivities()
    activities.grade_results = [{"output_path": "g.json", "passed": False}]
    engine = make_engine(
        activities,
        # First wait times out (None), second wait gets the human's decision.
        human_responses=[None, HumanResponse(HumanDecision.ACCEPT)],
        max_attempts=3,
    )

    result = await engine.run("story text")

    assert result.final_status == "human_resolved"
    assert result.escalated is True


@pytest.mark.asyncio
async def test_run_when_escalation_times_out_twice_fails_gracefully():
    activities = FakeActivities()
    activities.grade_results = [{"output_path": "g.json", "passed": False}]
    engine = make_engine(activities, human_responses=[None, None], max_attempts=3)

    result = await engine.run("story text")

    assert result.final_status == "failed"
    assert result.escalated is True
