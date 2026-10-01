from pathlib import Path

import pytest
from edd_refinement_workflow.progress_record import (
    ProgressRecordAlreadyExists,
    ProgressRecordFactory,
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


def test_serializer_redacts_environment_variables_and_credential_paths() -> None:
    serializer = ProgressRecordSerializer(
        schema_version=1,
        allowed_fields={"schema_version", "run_id", "payload"},
    )
    record = {
        "schema_version": 1,
        "run_id": "run-1",
        "payload": {
            "aws_path": "/home/user/.aws/credentials",
            "token": "${GITHUB_TOKEN}",
            "normal": "some-value",
        },
    }

    serialized = serializer.serialize(record)

    assert serialized["payload"]["aws_path"] == "[REDACTED]"
    assert serialized["payload"]["token"] == "[REDACTED]"
    assert serialized["payload"]["normal"] == "some-value"


def test_serializer_schema_version_two_preserves_approval_state() -> None:
    serializer = ProgressRecordSerializer(
        schema_version=2,
        allowed_fields={"schema_version", "run_id", "approval_request", "approval_history"},
    )
    approval_request = {
        "approval_request_id": "approval-1",
        "proposal_id": "proposal-1",
        "proposed_diff_hash": "abc123",
        "status": "pending",
    }
    record = {
        "schema_version": 2,
        "run_id": "run-1",
        "approval_request": approval_request,
        "approval_history": [],
    }

    serialized = serializer.serialize(record)
    restored = serializer.deserialize(serialized)

    assert restored == record


def test_progress_record_v5_with_limit_state_serializes_and_redacts() -> None:
    record = {
        "schema_version": 5,
        "run_id": "run-1",
        "budgets": {"max_iterations": 3, "token_budget": 100},
        "logical_iteration_count": 1,
        "cumulative_token_usage": 25,
        "consecutive_confirmed_regressions": 0,
        "pending_evidence_flags": ["inconclusive"],
        "attempts": [
            {
                "attempt_id": "attempt-1",
                "total_tokens": 25,
                "artifact_path": "/home/user/private/token-cache.json",
            }
        ],
        "human_handoff_records": [],
    }

    restored = ProgressRecordSerializer.for_v5().deserialize(
        ProgressRecordSerializer.for_v5().serialize(record)
    )

    assert restored == record | {
        "attempts": [
            {
                "attempt_id": "attempt-1",
                "total_tokens": 25,
                "artifact_path": "[REDACTED]",
            }
        ]
    }


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


def test_for_v5_roundtrip_preserves_modification_scope_and_violations() -> None:
    serializer = ProgressRecordSerializer.for_v5()
    record = {
        "schema_version": 5,
        "run_id": "run-1",
        "modification_scope": ["skill/", "docs/guide.md"],
        "scope_violations": [
            {
                "check": "plan",
                "paths": ["outside/hack.py"],
                "action": "refine_skill",
                "rationale": "oops",
                "evidence": {},
            }
        ],
        "unlisted_field": "dropped",
    }

    serialized = serializer.serialize(record)
    assert serialized["modification_scope"] == ["skill/", "docs/guide.md"]
    assert serialized["scope_violations"] == record["scope_violations"]
    assert "unlisted_field" not in serialized
    assert serializer.deserialize(serialized) == serialized


def test_factory_derives_run_id_and_refuses_duplicate_creation(tmp_path) -> None:
    store = ProgressRecordStore(tmp_path)
    factory = ProgressRecordFactory(store)

    run_id = factory.derive_run_id("workflow-1", "abcdef123456")
    assert run_id == "workflow-1-abcdef1"

    record = {"schema_version": 1, "run_id": run_id}
    created = factory.create_or_resume(run_id, record)
    assert created == record

    with pytest.raises(ProgressRecordAlreadyExists):
        factory.create(run_id, record)

    resumed = factory.create_or_resume(run_id, {"schema_version": 999, "run_id": run_id})
    assert resumed == record
