from edd_refinement_workflow.approval import ApprovalService
from edd_refinement_workflow.progress_record import ProgressRecordStore


def test_approval_service_persists_first_decision_and_history(tmp_path) -> None:
    store = ProgressRecordStore(tmp_path)
    record = {"schema_version": 2, "run_id": "run-1", "approval_history": []}
    store.create_or_resume("run-1", record)
    service = ApprovalService(store)

    request = service.request(
        record,
        proposal_id="proposal-1",
        proposed_diff_hash="abc123",
        timeout_seconds=60,
        requested_at="2026-09-14T12:00:00Z",
    )
    decided = service.record_decision(
        record,
        proposal_id="proposal-1",
        decision="approve",
        decided_at="2026-09-14T12:01:00Z",
        notes="approved",
    )

    assert request["approval_request_id"] == "approval-proposal-1"
    assert decided["decision"] == "approve"
    assert decided["status"] == "decided"
    assert record["approval_history"] == [decided]
    assert store.create_or_resume("run-1", {})["approval_request"] == decided
