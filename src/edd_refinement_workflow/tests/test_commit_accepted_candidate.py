import pytest
from edd_refinement_workflow.activities.commit_accepted_candidate import (
    CommitAcceptedCandidateActivity,
    commit_accepted_candidate_activity,
)
from edd_refinement_workflow.progress_record import ProgressRecordStore


def test_commit_accepted_candidate_with_accepted_metrics_updates_best_state(tmp_path) -> None:
    store = ProgressRecordStore(tmp_path)
    metric = {
        "candidate_id": "candidate-1",
        "passing": 6,
        "total": 7,
        "required_coverage": {"required-1": 1},
    }
    store.create_or_resume(
        "run-1",
        {
            "candidate": {"candidate_id": "candidate-1", "diff_hash": "abc123"},
            "candidate_history": [],
            "consecutive_confirmed_regressions": 2,
        },
    )
    commits = []
    activity = CommitAcceptedCandidateActivity(
        store,
        commit=lambda message: commits.append(message) or "commit-123",
        now=lambda: "2026-09-15T16:00:00Z",
    )

    result = activity.run("run-1", metric)

    assert commits == ["Accept EDD candidate candidate-1"]
    assert result == {
        "candidate_id": "candidate-1",
        "commit": "commit-123",
        "metrics": metric,
        "accepted_at": "2026-09-15T16:00:00Z",
    }
    record = store.create_or_resume("run-1", {})
    assert record["best_accepted_state"] == result
    assert record["consecutive_confirmed_regressions"] == 0
    assert record["candidate_history"][-1]["status"] == "accepted"


@pytest.mark.asyncio
async def test_commit_accepted_candidate_activity_uses_target_git_repository_updates_state(tmp_path, monkeypatch) -> None:
    store = ProgressRecordStore(tmp_path)
    store.create_or_resume("run-1", {"candidate_history": [], "consecutive_confirmed_regressions": 1})
    calls = []
    monkeypatch.setattr("edd_refinement_workflow.activities.commit_accepted_candidate._commit_repository", lambda root, message: calls.append((root, message)) or "commit-1")
    metric = {"candidate_id": "candidate-1", "passing": 6}

    result = await commit_accepted_candidate_activity("run-1", metric, str(tmp_path))

    assert calls == [(str(tmp_path), "Accept EDD candidate candidate-1")]
    assert result["commit"] == "commit-1"
    assert store.create_or_resume("run-1", {})["best_accepted_state"]["commit"] == "commit-1"
