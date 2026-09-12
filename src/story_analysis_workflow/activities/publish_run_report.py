from datetime import datetime, timezone
from pathlib import Path

from cadence import activity

from ..reporting import (
    REPORT_FILENAME,
    ActivityAttemptObservation,
    TerminalWorkflowOutcome,
    UsageMetrics,
    build_run_report,
    publish_run_report_to_path,
)
from ..story_analysis_engine import OutcomeOrigin


@activity.defn(name="publish_story_analysis_run_report")
async def publish_story_analysis_run_report(
    story_document: str,
    terminal_result: dict,
    attempt_documents: list[dict],
    _report_root: str,
) -> dict:
    info = activity.info()
    attempts = []
    for document in attempt_documents:
        values = dict(document)
        usage = values.get("usage")
        values["usage"] = UsageMetrics(**usage) if usage is not None else None
        attempts.append(ActivityAttemptObservation(**values))
    report_workflow_id = attempts[0].workflow_id if attempts else info.workflow_id
    report_run_id = attempts[0].run_id if attempts else info.workflow_run_id
    report = build_run_report(
        workflow_id=report_workflow_id,
        run_id=report_run_id,
        story_document=story_document,
        terminal_at=datetime.now(timezone.utc),
        outcome=TerminalWorkflowOutcome(
            final_status=terminal_result["final_status"],
            outcome_origin=OutcomeOrigin(terminal_result["outcome_origin"]),
            final_analysis_path=terminal_result["final_analysis_path"],
            repair_attempt_count=terminal_result["attempt_count"],
        ),
        attempts=attempts,
    )
    destination = Path(story_document).expanduser().resolve().parent / REPORT_FILENAME
    report_path = publish_run_report_to_path(report, destination)
    return {"report_path": str(report_path)}
