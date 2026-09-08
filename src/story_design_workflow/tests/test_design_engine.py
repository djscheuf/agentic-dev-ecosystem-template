import pytest

from story_design_workflow.design_engine import ActivityFailure, StoryDesignEngine


class FakeActivities:
    def __init__(self):
        self.calls = []
        self.audit_result = {"output_path": "docs/current-reality.audit.json"}
        self.design_result = {"output_path": "docs/foo.design.json"}
        self.grade_result = {"output_path": "docs/foo.design-grade.json", "passed": True, "score": 0.95}
        self.audit_exception = None

    async def audit_current_reality(self, analysis_path):
        self.calls.append(("audit_current_reality", analysis_path))
        if self.audit_exception is not None:
            raise self.audit_exception
        return self.audit_result

    async def design_story_implementation(self, analysis_path, audit_path):
        self.calls.append(("design_story_implementation", analysis_path, audit_path))
        return self.design_result

    async def grade_story_design(self, design_path):
        self.calls.append(("grade_story_design", design_path))
        return self.grade_result


def make_engine(activities):
    return StoryDesignEngine(
        execute_audit_current_reality=activities.audit_current_reality,
        execute_design_story_implementation=activities.design_story_implementation,
        execute_grade_story_design=activities.grade_story_design,
    )


@pytest.mark.asyncio
async def test_run_happy_path_completes_when_grade_passes():
    activities = FakeActivities()
    engine = make_engine(activities)

    result = await engine.run("docs/foo.analysis.json")

    assert result.passed is True
    assert result.final_status == "passed"
    assert result.design_path == "docs/foo.design.json"
    assert result.score == 0.95
    assert [c[0] for c in activities.calls] == [
        "audit_current_reality",
        "design_story_implementation",
        "grade_story_design",
    ]


@pytest.mark.asyncio
async def test_run_fails_when_grade_does_not_pass():
    activities = FakeActivities()
    activities.grade_result = {"output_path": "docs/foo.design-grade.json", "passed": False, "score": 0.45}
    engine = make_engine(activities)

    result = await engine.run("docs/foo.analysis.json")

    assert result.passed is False
    assert result.final_status == "failed"
    assert result.design_path == "docs/foo.design.json"
    assert result.score == 0.45


@pytest.mark.asyncio
async def test_run_fails_when_activity_exhausts_retries():
    activities = FakeActivities()
    activities.audit_exception = ActivityFailure("boom")
    engine = make_engine(activities)

    result = await engine.run("docs/foo.analysis.json")

    assert result.passed is False
    assert result.final_status == "failed"
    assert result.design_path is None
    assert [c[0] for c in activities.calls] == ["audit_current_reality"]
