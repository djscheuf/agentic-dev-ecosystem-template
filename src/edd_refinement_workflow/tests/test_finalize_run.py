import json

import pytest
from edd_refinement_workflow.finalize_run import FinalizeRunActivity, finalize_run_activity
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


def test_finalize_run_without_accepted_state_resets_to_starting_revision(
    tmp_path,
) -> None:
    store = ProgressRecordStore(tmp_path)
    store.create_or_resume(
        "run-1",
        {
            "schema_version": 5,
            "run_id": "run-1",
            "starting_revision": "start-commit",
            "baseline_metrics": {"passing": 5, "total": 6},
            "best_accepted_state": None,
            "scope_violations": [
                {"check": "plan", "paths": ["outside/hack.py"]}
            ],
        },
    )
    restored = []
    released = []
    activity = FinalizeRunActivity(
        store,
        restore=lambda commit: restored.append(commit),
        release_lease=lambda run_id: released.append(run_id),
    )

    result = activity.run("run-1", "out_of_scope_modification")

    assert restored == ["start-commit"]
    assert released == ["run-1"]
    assert result["terminal_reason"] == "out_of_scope_modification"
    assert result["scope_violations"] == [
        {"check": "plan", "paths": ["outside/hack.py"]}
    ]
    assert result["final_commit"] == "start-commit"
    report = json.loads((tmp_path / result["report_path"]).read_text())
    assert report["scope_violations"] == result["scope_violations"]


def test_finalize_run_still_reports_and_releases_lease_when_reset_fails(
    tmp_path,
) -> None:
    store = ProgressRecordStore(tmp_path)
    store.create_or_resume(
        "run-1",
        {
            "schema_version": 5,
            "run_id": "run-1",
            "starting_revision": "start-commit",
            "baseline_metrics": {"passing": 5, "total": 6},
            "best_accepted_state": None,
        },
    )
    released = []

    def failing_restore(commit: str) -> None:
        raise RuntimeError("git reset failed")

    activity = FinalizeRunActivity(
        store,
        restore=failing_restore,
        release_lease=lambda run_id: released.append(run_id),
    )

    result = activity.run("run-1", "out_of_scope_modification")

    assert released == ["run-1"]
    assert result["terminal_reason"] == "out_of_scope_modification"
    assert result["restore_succeeded"] is False
    assert (tmp_path / result["report_path"]).exists()


@pytest.mark.asyncio
async def test_finalize_run_activity_uses_target_dependencies_publishes_terminal_result(tmp_path, monkeypatch) -> None:
    store = ProgressRecordStore(tmp_path)
    store.create_or_resume("run-1", {"starting_revision": "start", "best_accepted_state": {"candidate_id": "candidate-1", "commit": "best", "metrics": {"passing": 2}}, "baseline_metrics": {"passing": 1}})
    restored = []
    released = []
    monkeypatch.setattr("edd_refinement_workflow.finalize_run._restore_repository", lambda root, commit: restored.append((root, commit)))
    monkeypatch.setattr("edd_refinement_workflow.finalize_run._release_lease", lambda root, run_id: released.append((root, run_id)))

    result = await finalize_run_activity("run-1", "completed", str(tmp_path))

    assert result["accepted_commit"] == "best"
    assert restored == [(str(tmp_path), "best")]
    assert released == [(str(tmp_path), "run-1")]
