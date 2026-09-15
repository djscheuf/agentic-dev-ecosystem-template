import json
from collections.abc import Callable
from datetime import UTC, datetime

from cadence import activity


class FinalizeRunActivity:
    def __init__(
        self,
        store,
        restore: Callable[[str], None],
        release_lease: Callable[[str], None],
        now: Callable[[], str] | None = None,
    ) -> None:
        self.store = store
        self.restore = restore
        self.release_lease = release_lease
        self.now = now or (lambda: datetime.now(UTC).isoformat())

    def run(self, run_id: str, terminal_reason: str) -> dict:
        record = self.store.create_or_resume(run_id, {})
        if record.get("terminal_result") is not None:
            return record["terminal_result"]

        best = record.get("best_accepted_state")
        accepted_commit = best["commit"] if best else None
        baseline = record.get("baseline_metrics", {})
        final_metrics = best.get("metrics", {}) if best else baseline
        if accepted_commit is not None:
            self.restore(accepted_commit)
        self.release_lease(run_id)

        report_path = f".process/edd/{run_id}/terminal.json"
        result = {
            "schema_version": 1,
            "run_id": run_id,
            "terminal_reason": terminal_reason,
            "baseline_metrics": baseline,
            "final_metrics": final_metrics,
            "passing_delta": final_metrics.get("passing", 0) - baseline.get("passing", 0),
            "accepted_candidate_id": best.get("candidate_id") if best else None,
            "accepted_commit": accepted_commit,
            "rejected_or_reverted_summaries": record.get("candidate_history", []),
            "pending_human_items": [record["approval_request"]]
            if record.get("approval_request", {}).get("status") == "pending"
            else [],
            "flaky_evidence": record.get("flaky_evidence", []),
            "target_repository": record.get("target_repository"),
            "final_commit": accepted_commit or record.get("starting_revision"),
            "lease_released_at": self.now(),
            "report_path": report_path,
        }
        path = self.store.target_root / report_path
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = path.with_suffix(".tmp")
        temporary_path.write_text(json.dumps(result, indent=2, sort_keys=True))
        temporary_path.replace(path)
        record["terminal_result"] = result
        record["lease_released"] = True
        record["terminal_report_path"] = report_path
        self.store.save(run_id, record)
        return result


@activity.defn(name="finalize_run")
async def finalize_run_activity(
    run_id: str, terminal_reason: str, repo_root: str
) -> dict:
    raise NotImplementedError
