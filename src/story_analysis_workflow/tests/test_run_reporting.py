import json
from dataclasses import asdict
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from jsonschema import ValidationError, validate

from story_analysis_workflow.reporting import (
    AGGREGATE_SCHEMA_PATH,
    REPORT_SCHEMA_PATH,
    ActivityAttemptObservation,
    TerminalWorkflowOutcome,
    UsageMetrics,
    aggregate_run_reports,
    build_run_report,
    publish_run_aggregate,
    publish_run_report,
)
from story_analysis_workflow.activities.publish_run_report import publish_story_analysis_run_report
from story_analysis_workflow.story_analysis_engine import OutcomeOrigin
from story_analysis_workflow.workflow import StoryAnalysisWorkflow


def test_build_run_report_with_retries_preserves_ordered_attempts_and_usage():
    attempts = [
        ActivityAttemptObservation(
            workflow_id="workflow-1",
            run_id="run-1",
            sequence=2,
            step_name="grade",
            activity_type="grade_story_analysis",
            activity_id="grade-1",
            attempt=2,
            started_at="2026-09-08T12:00:02Z",
            duration_ms=20,
            outcome="success",
            model="model-b",
            permission_mode="safe",
            output_path="grade.json",
            activity_log_path="activity-2.log",
            devin_log_path="devin-2.log",
            atif_path="attempt-2/trajectory.json",
            usage=UsageMetrics(prompt_tokens=7, completion_tokens=3, cached_tokens=0),
        ),
        ActivityAttemptObservation(
            workflow_id="workflow-1",
            run_id="run-1",
            sequence=1,
            step_name="grade",
            activity_type="grade_story_analysis",
            activity_id="grade-1",
            attempt=1,
            started_at="2026-09-08T12:00:00Z",
            duration_ms=10,
            outcome="failed",
            model="model-a",
            permission_mode="safe",
            output_path="",
            activity_log_path="activity-1.log",
            devin_log_path="devin-1.log",
            atif_path="attempt-1/trajectory.json",
            usage=UsageMetrics(prompt_tokens=5, completion_tokens=None, cached_tokens=2),
        ),
    ]
    outcome = TerminalWorkflowOutcome(
        final_status="passed",
        outcome_origin=OutcomeOrigin.REPAIRED_PASS,
        final_analysis_path="analysis.json",
        repair_attempt_count=1,
    )

    report = build_run_report(
        workflow_id="workflow-1",
        run_id="run-1",
        story_document="story.md",
        terminal_at=datetime(2026, 9, 8, 12, 1, tzinfo=timezone.utc),
        outcome=outcome,
        attempts=attempts,
    )

    assert [attempt.attempt for attempt in report.attempts] == [1, 2]
    assert report.usage.prompt_tokens.value == 12
    assert report.usage.prompt_tokens.available is True
    assert report.usage.completion_tokens.value == 3
    assert report.usage.cached_tokens.value == 2
    assert report.usage.cost_usd.value is None
    assert report.usage.cost_usd.available is False
    assert [attempt.atif_path for attempt in report.attempts] == [
        "attempt-1/trajectory.json",
        "attempt-2/trajectory.json",
    ]


def test_publish_run_report_accepts_cadence_first_attempt_zero(tmp_path):
    attempt = ActivityAttemptObservation(
        workflow_id="workflow-1",
        run_id="run-1",
        sequence=1,
        step_name="extract-story-intent",
        activity_type="extract_story_intent",
        activity_id="activity-1",
        attempt=0,
        started_at="2026-09-08T12:00:00Z",
        duration_ms=10,
        outcome="success",
        model="SWE-1.7",
        permission_mode="accept-edits",
        output_path="intent.json",
        activity_log_path="activity.log",
        devin_log_path="devin.log",
    )
    report = build_run_report(
        workflow_id="workflow-1",
        run_id="run-1",
        story_document="story.md",
        terminal_at=datetime(2026, 9, 8, tzinfo=timezone.utc),
        outcome=TerminalWorkflowOutcome(
            "passed", OutcomeOrigin.AUTOMATED_PASS, "analysis.json", 0
        ),
        attempts=[attempt],
    )

    report_path = publish_run_report(report, tmp_path)

    assert json.loads(report_path.read_text())["attempts"][0]["attempt"] == 0


def test_build_run_report_validates_metadata_and_attempt_identity():
    outcome = TerminalWorkflowOutcome(
        final_status="failed",
        outcome_origin=OutcomeOrigin.AUTOMATED_FAILURE,
        final_analysis_path=None,
        repair_attempt_count=0,
    )
    report = build_run_report(
        workflow_id="workflow-1",
        run_id="run-1",
        story_document="story.md",
        terminal_at=datetime(2026, 9, 8, tzinfo=timezone.utc),
        outcome=outcome,
        attempts=[],
    )
    mismatched_attempt = ActivityAttemptObservation(
        workflow_id="workflow-2",
        run_id="run-1",
        sequence=1,
        step_name="extract",
        activity_type="extract_story_intent",
        activity_id="extract-1",
        attempt=1,
        started_at="2026-09-08T00:00:00Z",
        duration_ms=1,
        outcome="failed",
        model="model-a",
        permission_mode="safe",
        output_path="",
        activity_log_path="activity.log",
        devin_log_path="devin.log",
    )

    assert report.attempts == ()
    with pytest.raises(ValueError, match="workflow_id is required"):
        build_run_report(
            workflow_id="",
            run_id="run-1",
            story_document="story.md",
            terminal_at=datetime(2026, 9, 8, tzinfo=timezone.utc),
            outcome=outcome,
            attempts=[],
        )
    with pytest.raises(ValueError, match="attempt identity does not match report"):
        build_run_report(
            workflow_id="workflow-1",
            run_id="run-1",
            story_document="story.md",
            terminal_at=datetime(2026, 9, 8, tzinfo=timezone.utc),
            outcome=outcome,
            attempts=[mismatched_attempt],
        )


def test_publish_run_report_repeated_or_interrupted_is_atomic_and_idempotent(tmp_path):
    report = build_run_report(
        workflow_id="../workflow/文",
        run_id=".run/../id",
        story_document="story.md",
        terminal_at=datetime(2026, 9, 8, tzinfo=timezone.utc),
        outcome=TerminalWorkflowOutcome(
            final_status="passed",
            outcome_origin=OutcomeOrigin.AUTOMATED_PASS,
            final_analysis_path="analysis.json",
            repair_attempt_count=0,
        ),
        attempts=[],
    )

    first_path = publish_run_report(report, tmp_path)
    second_path = publish_run_report(report, tmp_path)

    assert first_path == second_path
    assert first_path.name == "story-analysis.report.json"
    assert first_path.resolve().is_relative_to(tmp_path.resolve())
    assert json.loads(first_path.read_text())["schema_version"] == "1.0"
    assert list(tmp_path.rglob("story-analysis.report.json")) == [first_path]

    interrupted_root = tmp_path / "interrupted"

    def interrupt(_source, _destination):
        raise OSError("replace interrupted")

    with pytest.raises(OSError, match="replace interrupted"):
        publish_run_report(report, interrupted_root, replace_file=interrupt)

    assert list(interrupted_root.rglob("story-analysis.report.json")) == []
    assert list(interrupted_root.rglob("*.tmp")) == []


def test_aggregate_run_reports_with_mixed_candidates_publishes_auditable_operands(tmp_path):
    window_start = datetime(2026, 9, 8, tzinfo=timezone.utc)
    window_end = datetime(2026, 9, 9, tzinfo=timezone.utc)
    origins = [
        OutcomeOrigin.AUTOMATED_PASS,
        OutcomeOrigin.REPAIRED_PASS,
        OutcomeOrigin.HUMAN_ACCEPT,
        OutcomeOrigin.HUMAN_ABORT,
        OutcomeOrigin.AUTOMATED_FAILURE,
    ]
    paths = []
    for index, origin in enumerate(origins):
        status = "passed" if index < 2 else "human_resolved" if index < 4 else "failed"
        report = build_run_report(
            workflow_id=f"workflow-{index}",
            run_id=f"run-{index}",
            story_document="story.md",
            terminal_at=window_start,
            outcome=TerminalWorkflowOutcome(status, origin, "analysis.json", 0),
            attempts=[],
        )
        paths.append(publish_run_report(report, tmp_path))

    duplicate_path = tmp_path / "duplicate" / "story-analysis.report.json"
    duplicate_path.parent.mkdir()
    duplicate_path.write_text(paths[0].read_text())
    malformed_path = tmp_path / "malformed" / "story-analysis.report.json"
    malformed_path.parent.mkdir()
    malformed_path.write_text("{")
    incompatible_path = tmp_path / "incompatible" / "story-analysis.report.json"
    incompatible_path.parent.mkdir()
    incompatible = json.loads(paths[1].read_text())
    incompatible["schema_version"] = "2.0"
    incompatible_path.write_text(json.dumps(incompatible))
    outside_report = build_run_report(
        workflow_id="outside",
        run_id="outside",
        story_document="story.md",
        terminal_at=window_end,
        outcome=TerminalWorkflowOutcome(
            "passed", OutcomeOrigin.AUTOMATED_PASS, "analysis.json", 0
        ),
        attempts=[],
    )
    publish_run_report(outside_report, tmp_path)

    aggregate = aggregate_run_reports(tmp_path, window_start, window_end)

    assert aggregate.formula_id == "automated_pass_rate_v1"
    assert aggregate.numerator == 2
    assert aggregate.denominator == 5
    assert aggregate.success_rate == 0.4
    assert aggregate.manual_intervention_count == 2
    assert aggregate.outcome_origin_counts == {
        origin.value: 1 for origin in origins
    }
    assert len(aggregate.observations) == 5
    assert aggregate.exclusion_counts == {
        "duplicate": 1,
        "incompatible_schema": 1,
        "malformed": 1,
        "out_of_window": 1,
    }


def test_aggregate_run_reports_with_empty_sample_returns_null_rate(tmp_path):
    window_start = datetime(2026, 9, 8, tzinfo=timezone.utc)
    window_end = datetime(2026, 9, 9, tzinfo=timezone.utc)

    aggregate = aggregate_run_reports(tmp_path, window_start, window_end)
    output_path = publish_run_aggregate(aggregate, tmp_path)

    assert aggregate.numerator == 0
    assert aggregate.denominator == 0
    assert aggregate.success_rate is None
    assert aggregate.status_counts == {}
    assert aggregate.outcome_origin_counts == {}
    assert aggregate.observations == ()
    assert json.loads(output_path.read_text())["success_rate"] is None


@pytest.mark.asyncio
async def test_publish_run_report_activity_with_terminal_result_writes_run_scoped_report(
    monkeypatch, tmp_path
):
    from story_analysis_workflow.activities import publish_run_report as activity_module

    monkeypatch.setattr(
        activity_module.activity,
        "info",
        lambda: SimpleNamespace(workflow_id="workflow-1", workflow_run_id="run-1"),
    )
    terminal_result = {
        "final_analysis_path": "analysis.json",
        "passed": True,
        "attempt_count": 0,
        "escalated": False,
        "final_status": "passed",
        "validation_rule": None,
        "outcome_origin": "automated_pass",
    }

    result = await publish_story_analysis_run_report(
        "story.md", terminal_result, [], str(tmp_path)
    )

    report_path = tmp_path / "workflow-1" / "run-1" / "story-analysis.report.json"
    assert result == {"report_path": str(report_path)}
    assert json.loads(report_path.read_text())["workflow_id"] == "workflow-1"


@pytest.mark.asyncio
async def test_publish_activity_preserves_original_identity_when_rerun_from_another_workflow(
    monkeypatch, tmp_path
):
    from story_analysis_workflow.activities import publish_run_report as activity_module

    monkeypatch.setattr(
        activity_module.activity,
        "info",
        lambda: SimpleNamespace(
            workflow_id="republish-helper", workflow_run_id="helper-run"
        ),
    )
    attempt = {
        "workflow_id": "original-workflow",
        "run_id": "original-run",
        "sequence": 1,
        "step_name": "extract-story-intent",
        "activity_type": "extract_story_intent",
        "activity_id": "activity-1",
        "attempt": 0,
        "started_at": "2026-09-08T12:00:00Z",
        "duration_ms": 10,
        "outcome": "success",
        "model": "SWE-1.7",
        "permission_mode": "accept-edits",
        "output_path": "intent.json",
        "activity_log_path": "activity.log",
        "devin_log_path": "devin.log",
        "atif_path": None,
        "usage": None,
    }
    terminal_result = {
        "final_analysis_path": "analysis.json",
        "attempt_count": 0,
        "final_status": "passed",
        "outcome_origin": "automated_pass",
    }

    result = await publish_story_analysis_run_report(
        "story.md", terminal_result, [attempt], str(tmp_path)
    )

    expected = (
        tmp_path
        / "original-workflow"
        / "original-run"
        / "story-analysis.report.json"
    )
    assert result == {"report_path": str(expected)}
    assert json.loads(expected.read_text())["run_id"] == "original-run"


@pytest.mark.asyncio
async def test_story_analysis_workflow_on_terminal_result_publishes_before_completion():
    workflow = StoryAnalysisWorkflow()

    async def validate(_story_document):
        from story_analysis_workflow.source_document_validation import (
            SourceDocumentValidationResult,
            SourceDocumentValidationRule,
        )

        return SourceDocumentValidationResult(True, SourceDocumentValidationRule.VALID)

    async def output(*_args):
        return {"output_path": "artifact.json"}

    async def grade(*_args):
        return {"output_path": "grade.json", "passed": True}

    publication_calls = []

    async def publish(story_document, terminal_result, attempts, report_root):
        publication_calls.append((story_document, terminal_result, attempts, report_root))
        return {"report_path": "/reports/workflow-1/run-1/story-analysis.report.json"}

    workflow._validate_source_document = validate
    workflow._extract_story_intent = output
    workflow._analyze_story = output
    workflow._grade_story_analysis = grade
    workflow._execute_reporting_activity = publish

    result = await workflow.run("story.md", {"report_root": "/reports"})

    assert publication_calls[0][0] == "story.md"
    assert publication_calls[0][1]["outcome_origin"] == OutcomeOrigin.AUTOMATED_PASS
    assert publication_calls[0][2] == []
    assert publication_calls[0][3] == "/reports"
    assert result["report_path"] == "/reports/workflow-1/run-1/story-analysis.report.json"
    assert workflow.get_status()["report_path"] == result["report_path"]


@pytest.mark.asyncio
async def test_story_analysis_workflow_when_publication_fails_does_not_claim_reported_completion():
    workflow = StoryAnalysisWorkflow()

    async def validate(_story_document):
        from story_analysis_workflow.source_document_validation import (
            SourceDocumentValidationResult,
            SourceDocumentValidationRule,
        )

        return SourceDocumentValidationResult(True, SourceDocumentValidationRule.VALID)

    async def output(*_args):
        return {"output_path": "artifact.json"}

    async def grade(*_args):
        return {"output_path": "grade.json", "passed": True}

    async def fail_publication(*_args):
        raise OSError("publication failed")

    workflow._validate_source_document = validate
    workflow._extract_story_intent = output
    workflow._analyze_story = output
    workflow._grade_story_analysis = grade
    workflow._execute_reporting_activity = fail_publication

    with pytest.raises(OSError, match="publication failed"):
        await workflow.run("story.md", {"report_root": "/reports"})

    assert workflow.get_status()["report_path"] is None


def test_report_schemas_validate_complete_documents_and_reject_invalid_values(tmp_path):
    window_start = datetime(2026, 9, 8, tzinfo=timezone.utc)
    window_end = datetime(2026, 9, 9, tzinfo=timezone.utc)
    report = build_run_report(
        workflow_id="workflow-1",
        run_id="run-1",
        story_document="story.md",
        terminal_at=window_start,
        outcome=TerminalWorkflowOutcome(
            "passed", OutcomeOrigin.AUTOMATED_PASS, "analysis.json", 0
        ),
        attempts=[],
    )
    report_document = json.loads(json.dumps(asdict(report)))
    aggregate_document = json.loads(json.dumps(asdict(
        aggregate_run_reports(tmp_path, window_start, window_end)
    )))
    report_schema = json.loads(REPORT_SCHEMA_PATH.read_text())
    aggregate_schema = json.loads(AGGREGATE_SCHEMA_PATH.read_text())

    validate(report_document, report_schema)
    validate(aggregate_document, aggregate_schema)

    report_document["outcome_origin"] = "unknown"
    with pytest.raises(ValidationError):
        validate(report_document, report_schema)

    aggregate_document["denominator"] = -1
    with pytest.raises(ValidationError):
        validate(aggregate_document, aggregate_schema)
