import json

from edd_refinement_workflow.finalize_run import FinalizeRunActivity
from edd_refinement_workflow.progress_record import ProgressRecordStore


def test_finalize_run_with_terminal_outcome_publishes_once_and_releases_lease(tmp_path) -> None:
    store = ProgressRecordStore(tmp_path)
    store.create_or_resume(
        "run-1",
        {
            "schema_version": 4,
            "run_id": "run-1",
            "starting_revision": "baseline-commit",
            "baseline_metrics": {"passing": 5, "total": 6},
            "best_accepted_state": {
                "candidate_id": "candidate-1",
                "commit": "best-commit",
                "metrics": {"passing": 6, "total": 7},
            },
            "candidate_history": [{"candidate_id": "candidate-2", "status": "rejected"}],
            "approval_request": {"status": "pending", "proposal_id": "proposal-1"},
            "flaky_evidence": [{"candidate_id": "candidate-3"}],
            "target_repository": str(tmp_path),
        },
    )
    restored = []
    released = []
    activity = FinalizeRunActivity(
        store,
        restore=lambda commit: restored.append(commit),
        release_lease=lambda run_id: released.append(run_id),
        now=lambda: "2026-09-15T15:00:00Z",
    )

    first = activity.run("run-1", "budget_exhausted")
    second = activity.run("run-1", "budget_exhausted")

    assert first == second
    assert restored == ["best-commit"]
    assert released == ["run-1"]
    assert first["terminal_reason"] == "budget_exhausted"
    assert first["accepted_commit"] == "best-commit"
    assert first["passing_delta"] == 1
    assert first["pending_human_items"] == [{"status": "pending", "proposal_id": "proposal-1"}]
    assert first["flaky_evidence"] == [{"candidate_id": "candidate-3"}]
    report_path = tmp_path / first["report_path"]
    assert json.loads(report_path.read_text()) == first
