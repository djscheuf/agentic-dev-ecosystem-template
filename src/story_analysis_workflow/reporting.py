import json
import os
import re
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable

from .story_analysis_engine import OutcomeOrigin

REPORT_SCHEMA_VERSION = "1.0"
REPORT_FILENAME = "story-analysis.report.json"
_SAFE_COMPONENT_RE = re.compile(r"[^A-Za-z0-9_-]+")


@dataclass(frozen=True)
class UsageMetrics:
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    cached_tokens: int | None = None
    cost_usd: float | None = None


@dataclass(frozen=True)
class UsageValue:
    available: bool
    value: int | float | None


@dataclass(frozen=True)
class UsageTotals:
    prompt_tokens: UsageValue
    completion_tokens: UsageValue
    cached_tokens: UsageValue
    cost_usd: UsageValue


@dataclass(frozen=True)
class ActivityAttemptObservation:
    workflow_id: str
    run_id: str
    sequence: int
    step_name: str
    activity_type: str
    activity_id: str
    attempt: int
    started_at: str
    duration_ms: int
    outcome: str
    model: str
    permission_mode: str
    output_path: str
    activity_log_path: str
    devin_log_path: str
    atif_path: str | None = None
    usage: UsageMetrics | None = None


@dataclass(frozen=True)
class TerminalWorkflowOutcome:
    final_status: str
    outcome_origin: OutcomeOrigin
    final_analysis_path: str | None
    repair_attempt_count: int


@dataclass(frozen=True)
class StoryAnalysisRunReportV1:
    schema_version: str
    generated_at: str
    workflow_id: str
    run_id: str
    story_document: str
    terminal_at: str
    final_status: str
    outcome_origin: OutcomeOrigin
    final_analysis_path: str | None
    repair_attempt_count: int
    attempts: tuple[ActivityAttemptObservation, ...]
    usage: UsageTotals


def _total(attempts: tuple[ActivityAttemptObservation, ...], field: str) -> UsageValue:
    values = [
        getattr(attempt.usage, field)
        for attempt in attempts
        if attempt.usage is not None and getattr(attempt.usage, field) is not None
    ]
    return UsageValue(available=bool(values), value=sum(values) if values else None)


def build_run_report(
    *,
    workflow_id: str,
    run_id: str,
    story_document: str,
    terminal_at: datetime,
    outcome: TerminalWorkflowOutcome,
    attempts: Iterable[ActivityAttemptObservation],
    generated_at: datetime | None = None,
) -> StoryAnalysisRunReportV1:
    required = {
        "workflow_id": workflow_id,
        "run_id": run_id,
        "story_document": story_document,
    }
    for name, value in required.items():
        if not value:
            raise ValueError(f"{name} is required")
    ordered_attempts = tuple(sorted(attempts, key=lambda item: item.sequence))
    if any(
        attempt.workflow_id != workflow_id or attempt.run_id != run_id
        for attempt in ordered_attempts
    ):
        raise ValueError("attempt identity does not match report")
    generated_at = generated_at or datetime.now(timezone.utc)
    return StoryAnalysisRunReportV1(
        schema_version=REPORT_SCHEMA_VERSION,
        generated_at=generated_at.isoformat().replace("+00:00", "Z"),
        workflow_id=workflow_id,
        run_id=run_id,
        story_document=story_document,
        terminal_at=terminal_at.isoformat().replace("+00:00", "Z"),
        final_status=outcome.final_status,
        outcome_origin=outcome.outcome_origin,
        final_analysis_path=outcome.final_analysis_path,
        repair_attempt_count=outcome.repair_attempt_count,
        attempts=ordered_attempts,
        usage=UsageTotals(
            prompt_tokens=_total(ordered_attempts, "prompt_tokens"),
            completion_tokens=_total(ordered_attempts, "completion_tokens"),
            cached_tokens=_total(ordered_attempts, "cached_tokens"),
            cost_usd=_total(ordered_attempts, "cost_usd"),
        ),
    )


def _safe_component(value: str) -> str:
    return _SAFE_COMPONENT_RE.sub("_", value).strip("_") or "unknown"


def publish_run_report(
    report: StoryAnalysisRunReportV1,
    report_root: Path,
    *,
    replace_file: Callable[[str, str], None] = os.replace,
) -> Path:
    destination = (
        report_root
        / _safe_component(report.workflow_id)
        / _safe_component(report.run_id)
        / REPORT_FILENAME
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=destination.parent,
            prefix=f".{REPORT_FILENAME}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            json.dump(asdict(report), temporary, indent=2)
            temporary.write("\n")
            temporary.flush()
            os.fsync(temporary.fileno())
        replace_file(str(temporary_path), str(destination))
    except BaseException:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise
    return destination
