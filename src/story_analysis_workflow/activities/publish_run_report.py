from datetime import datetime, timezone
from pathlib import Path

from cadence import activity

from ..reporting import (
    ActivityAttemptObservation,
    TerminalWorkflowOutcome,
    UsageMetrics,
    build_run_report,
    publish_run_report,
)
from ..story_analysis_engine import OutcomeOrigin


@activity.defn(name="publish_story_analysis_run_report")
async def publish_story_analysis_run_report(
    story_document: str,
    terminal_result: dict,
    attempt_documents: list[dict],
    report_root: str,
) -> dict:
    info = activity.info()
    attempts = []
    for document in attempt_documents:
        values = dict(document)
        usage = values.get("usage")
        values["usage"] = UsageMetrics(**usage) if usage is not None else None
        attempts.append(ActivityAttemptObservation(**values))
    report = build_run_report(
        workflow_id=info.workflow_id,
        run_id=info.workflow_run_id,
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
    report_path = publish_run_report(report, Path(report_root))
    return {"report_path": str(report_path)}
