class DiffIntegrityError(Exception):
    pass


class ApprovalService:
    def __init__(self, store) -> None:
        self.store = store

    def request(
        self,
        record: dict,
        proposal_id: str,
        proposed_diff_hash: str,
        timeout_seconds: int,
        requested_at: str,
    ) -> dict:
        approval_request = {
            "approval_request_id": f"approval-{proposal_id}",
            "run_id": record["run_id"],
            "proposal_id": proposal_id,
            "proposed_diff_hash": proposed_diff_hash,
            "requested_at": requested_at,
            "timeout_seconds": timeout_seconds,
            "status": "pending",
            "decision": None,
            "decided_at": None,
            "notes": "",
        }
        record["approval_request"] = approval_request
        record.setdefault("approval_history", [])
        self.store.save(record["run_id"], record)
        return approval_request

    def record_decision(
        self,
        record: dict,
        proposal_id: str,
        decision: str,
        decided_at: str,
        notes: str = "",
    ) -> dict:
        approval_request = record["approval_request"]
        if approval_request["proposal_id"] != proposal_id:
            raise ValueError("approval decision does not match pending proposal")
        if approval_request["status"] != "pending":
            raise ValueError("approval request has already been decided")
        if decision not in {"approve", "reject", "timeout"}:
            raise ValueError("invalid approval decision")
        approval_request.update(
            status="decided",
            decision=decision,
            decided_at=decided_at,
            notes=notes,
        )
        record.setdefault("approval_history", []).append(dict(approval_request))
        self.store.save(record["run_id"], record)
        return approval_request

    def record_applied_change(
        self, record: dict, applied_diff_hash: str, applied_at: str
    ) -> dict:
        approval_request = record["approval_request"]
        if approval_request.get("decision") != "approve":
            raise DiffIntegrityError("evaluation change has not been approved")
        if approval_request["proposed_diff_hash"] != applied_diff_hash:
            raise DiffIntegrityError("applied diff does not match approved diff")
        applied_change = {
            "approval_request_id": approval_request["approval_request_id"],
            "proposal_id": approval_request["proposal_id"],
            "applied_diff_hash": applied_diff_hash,
            "applied_at": applied_at,
            "approval_context": "human_approved_evaluation_change",
        }
        record.setdefault("human_approved_evaluation_changes", []).append(applied_change)
        self.store.save(record["run_id"], record)
        return applied_change
