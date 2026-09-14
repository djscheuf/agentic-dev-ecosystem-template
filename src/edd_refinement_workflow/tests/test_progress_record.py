from pathlib import Path

import pytest
from edd_refinement_workflow.progress_record import (
    ProgressRecordSerializer,
    ProgressRecordStore,
    SchemaVersionMismatch,
)


def test_serializer_enforces_schema_version_and_field_allow_list() -> None:
    serializer = ProgressRecordSerializer(
        schema_version=1, allowed_fields={"schema_version", "run_id"}
    )
    serialized = serializer.serialize(
        {"schema_version": 1, "run_id": "run-1", "secret_token": "shhh"}
    )
    assert serialized == {"schema_version": 1, "run_id": "run-1"}

    with pytest.raises(SchemaVersionMismatch):
        serializer.serialize({"schema_version": 2, "run_id": "run-1"})


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
