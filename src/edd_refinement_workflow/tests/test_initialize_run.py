from typing import Any

from common.preflight import PreflightResult, TargetRepositoryContext
from edd_refinement_workflow.activities.initialize_run import InitializeRunActivity
from edd_refinement_workflow.progress_record import ProgressRecordFactory, ProgressRecordStore


def test_initialize_run_creates_record_and_emits_event(tmp_path) -> None:
    events = []

    def on_event(name: str, **data: Any) -> None:
        events.append((name, data))

    factory = ProgressRecordFactory(ProgressRecordStore(tmp_path))
    activity = InitializeRunActivity(factory, on_event=on_event)

    preflight = PreflightResult(
        status="success",
        target_context=TargetRepositoryContext(
            repo_root=tmp_path,
            anchor_path="",
            explicit_root=None,
            branch="main",
            starting_revision="abcdef123456",
        ),
    )

    record = activity.run("wf-1", preflight)

    assert record["run_id"] == "wf-1-abcdef1"
    assert record["workflow_run_id"] == "wf-1"
    assert record["starting_revision"] == "abcdef123456"
    assert record["token_usage"] == 0
    assert record["consecutive_confirmed_regressions"] == 0
    assert record["iteration_history"] == []
    assert (
        tmp_path / ".process" / "edd" / record["run_id"] / "progress.json"
    ).exists()
    assert any(name == "InitializeRun" for name, _ in events)
