from datetime import datetime, timezone

from story_analysis_workflow.reporting import (
    ActivityAttemptObservation,
    TerminalWorkflowOutcome,
    UsageMetrics,
    build_run_report,
)
from story_analysis_workflow.story_analysis_engine import OutcomeOrigin


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
