from pathlib import Path

from edd_refinement_workflow.progress_record import ProgressRecordStore


def test_progress_record_store_create_or_resume_is_idempotent(tmp_path) -> None:
    store = ProgressRecordStore(tmp_path)
    record = {"schema_version": 1, "run_id": "run-1"}

    created = store.create_or_resume("run-1", record)
    assert created == record

    progress_path = tmp_path / ".process" / "edd" / "run-1" / "progress.json"
    assert progress_path.exists()
    assert progress_path.read_text()

    resumed = store.create_or_resume(
        "run-1", {"schema_version": 999, "run_id": "run-1"}
    )
    assert resumed == record
    assert progress_path.read_text() == progress_path.read_text()
