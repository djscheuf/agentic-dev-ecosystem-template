import pytest

from story_design_workflow.design_engine import ActivityFailure, StoryDesignEngine
from story_design_workflow.handoff_validation import GuardrailRule, HandoffValidationResult
from story_design_workflow.source_document_validation import (
    SourceDocumentValidationResult,
    SourceDocumentValidationRule,
)


class FakeActivities:
    def __init__(self):
        self.calls = []
        self.audit_result = {"output_path": "docs/current-reality.audit.json"}
        self.design_result = {"output_path": "docs/foo.design.json"}
        self.grade_result = {"output_path": "docs/foo.design-grade.json", "passed": True, "score": 0.95}
        self.draft_result = {"output_path": "docs/foo.plan.json"}
        self.audit_exception = None
        self.validate_result = SourceDocumentValidationResult(
            True, SourceDocumentValidationRule.VALID
        )
        self.handoff_result = HandoffValidationResult(
            valid=True,
            ambiguity=False,
            rule=GuardrailRule.PASSED,
            artifact_path="",
            schema_path="",
        )

    async def validate_source_document(self, analysis_path):
        self.calls.append(("validate_source_document", analysis_path))
        return self.validate_result

    async def validate_handoff(self, output_path, schema_path):
        self.calls.append(("validate_handoff", output_path, schema_path))
        return self.handoff_result

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

    async def draft_implementation_plan(self, design_path):
        self.calls.append(("draft_implementation_plan", design_path))
        return self.draft_result


def make_engine(activities):
    return StoryDesignEngine(
        validate_source_document=activities.validate_source_document,
        validate_handoff=activities.validate_handoff,
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
        "validate_source_document",
        "audit_current_reality",
        "validate_handoff",
        "design_story_implementation",
        "validate_handoff",
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
    assert [c[0] for c in activities.calls] == [
        "validate_source_document",
        "audit_current_reality",
    ]


@pytest.mark.asyncio
async def test_run_returns_validation_failed_when_source_document_is_invalid():
    activities = FakeActivities()
    activities.validate_result = SourceDocumentValidationResult(
        False, SourceDocumentValidationRule.NON_JSON_EXTENSION
    )
    engine = make_engine(activities)

    result = await engine.run("docs/foo.analysis.md")

    assert result.passed is False
    assert result.final_status == "validation_failed"
    assert result.validation_rule == SourceDocumentValidationRule.NON_JSON_EXTENSION
    assert result.design_path is None
    assert [c[0] for c in activities.calls] == ["validate_source_document"]


@pytest.mark.asyncio
async def test_run_returns_handoff_failed_when_audit_artifact_is_invalid():
    activities = FakeActivities()
    activities.handoff_result = HandoffValidationResult(
        valid=False,
        ambiguity=False,
        rule=GuardrailRule.SCHEMA_VIOLATION,
        artifact_path="docs/current-reality.audit.json",
        schema_path=".devin/skills/audit-current-reality/schema/audit.schema.json",
    )
    engine = make_engine(activities)

    result = await engine.run("docs/foo.analysis.json")

    assert result.passed is False
    assert result.final_status == "handoff_failed"
    assert result.handoff_rule == GuardrailRule.SCHEMA_VIOLATION
    assert [c[0] for c in activities.calls] == [
        "validate_source_document",
        "audit_current_reality",
        "validate_handoff",
    ]


@pytest.mark.asyncio
async def test_run_returns_handoff_failed_when_design_artifact_is_invalid():
    activities = FakeActivities()
    activities.handoff_result = HandoffValidationResult(
        valid=True,
        ambiguity=False,
        rule=GuardrailRule.PASSED,
        artifact_path="docs/current-reality.audit.json",
        schema_path=".devin/skills/audit-current-reality/schema/audit.schema.json",
    )
    design_handoff = HandoffValidationResult(
        valid=False,
        ambiguity=False,
        rule=GuardrailRule.MALFORMED_JSON,
        artifact_path="docs/foo.design.json",
        schema_path=".devin/skills/design-story-implementation/schema/design.schema.json",
    )

    async def validate_handoff(output_path, schema_path):
        activities.calls.append(("validate_handoff", output_path, schema_path))
        if output_path == "docs/foo.design.json":
            return design_handoff
        return activities.handoff_result

    activities.validate_handoff = validate_handoff
    engine = make_engine(activities)

    result = await engine.run("docs/foo.analysis.json")

    assert result.passed is False
    assert result.final_status == "handoff_failed"
    assert result.handoff_rule == GuardrailRule.MALFORMED_JSON
    assert result.design_path == "docs/foo.design.json"
    assert [c[0] for c in activities.calls] == [
        "validate_source_document",
        "audit_current_reality",
        "validate_handoff",
        "design_story_implementation",
        "validate_handoff",
    ]


@pytest.mark.asyncio
async def test_run_plans_when_grade_passes():
    activities = FakeActivities()
    engine = StoryDesignEngine(
        validate_source_document=activities.validate_source_document,
        validate_handoff=activities.validate_handoff,
        execute_audit_current_reality=activities.audit_current_reality,
        execute_design_story_implementation=activities.design_story_implementation,
        execute_grade_story_design=activities.grade_story_design,
        execute_draft_implementation_plan=activities.draft_implementation_plan,
    )

    result = await engine.run("docs/foo.analysis.json")

    assert result.passed is True
    assert result.final_status == "passed"
    assert result.design_path == "docs/foo.design.json"
    assert result.plan_path == "docs/foo.plan.json"
    assert [c[0] for c in activities.calls] == [
        "validate_source_document",
        "audit_current_reality",
        "validate_handoff",
        "design_story_implementation",
        "validate_handoff",
        "grade_story_design",
        "draft_implementation_plan",
    ]
