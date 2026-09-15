from collections.abc import Callable
from datetime import UTC, datetime

from ..progress_record import ProgressRecordSerializer


class HumanHandoffActivity:
    def __init__(self, store, notify: Callable[[dict], bool]) -> None:
        self.store = store
        self.notify = notify

    def run(self, run_id: str, reason: str, evidence: dict, maximum_attempts: int = 1) -> dict:
        notified = False
        attempts = 0
        while attempts < maximum_attempts and not notified:
            attempts += 1
            notified = self.notify(evidence)
        result = {"handoff_reason": reason, "evidence_summary": evidence, "notified": notified, "retry_count": attempts - 1}
        record = self.store.create_or_resume(run_id, {})
        record["human_handoff_records"] = record.get("human_handoff_records", []) + [result]
        self.store.save(run_id, record)
        return result


class RecordRevertedProposalContextActivity:
    def __init__(self, store, now: Callable[[], str] | None = None) -> None:
        self.store = store
        self.now = now or (lambda: datetime.now(UTC).isoformat())

    def run(self, run_id: str, context: dict) -> dict:
        record = self.store.create_or_resume(run_id, {})
        redacted = ProgressRecordSerializer(1, {"schema_version", "context"}).serialize({"schema_version": 1, "context": context})["context"]
        result = redacted | {"reverted_at": self.now()}
        record["reverted_proposals"] = record.get("reverted_proposals", []) + [result]
        self.store.save(run_id, record)
        return result


class RevertRepositoryToBestActivity:
    def __init__(self, lease_held: Callable[[str, str], bool], reset: Callable[[str, str], None], is_clean: Callable[[str], bool]) -> None:
        self.lease_held = lease_held
        self.reset = reset
        self.is_clean = is_clean

    def run(self, run_id: str, repo_root: str, best_state: dict) -> dict:
        if not self.lease_held(repo_root, run_id):
            raise RuntimeError("mutation lease is not held")
        commit = best_state["commit"]
        self.reset(repo_root, commit)
        clean = self.is_clean(repo_root)
        if not clean:
            raise RuntimeError("repository is not clean after restore")
        return {"restored_commit": commit, "repo_clean": clean}


def classify_regression_evidence(original: dict, confirmation: dict, best_state: dict) -> dict:
    best = best_state["metrics"]
    if confirmation.get("status") in {"error", "timeout", "infrastructure_error"}:
        classification = "suspected_flakiness"
    elif confirmation.get("measurement_context") != best.get("measurement_context"):
        classification = "suspected_flakiness"
    elif "passing" not in confirmation:
        classification = "inconclusive"
    elif confirmation["passing"] < best["passing"]:
        classification = "confirmed_regression"
    else:
        classification = "unstable_result"
    return {"classification": classification, "reason": f"confirmation classified as {classification}"}


def verify_recovery_metrics(recovery: dict, best: dict) -> dict:
    fields = ["passing", "failing", "total", "required_coverage", "percentage"]
    mismatched = [field for field in fields if (abs(recovery.get(field, 0) - best.get(field, 0)) > 1e-6 if field == "percentage" else recovery.get(field) != best.get(field))]
    matched = [field for field in fields if field not in mismatched]
    recovered = not mismatched
    return {"recovered": recovered, "matched_fields": matched, "mismatched_fields": mismatched, "reason": "recovery metrics match" if recovered else "recovery metrics differ"}
