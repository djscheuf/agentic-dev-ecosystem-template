import pytest
import yaml

from edd_refinement_workflow.progress_record import ProgressRecordStore
from edd_refinement_workflow.refinement_log import append_refinement_outcome


def _write_refinement(repo_root, run_id="run-1", iterations=None):
    path = repo_root / ".process" / "edd" / run_id / "refinement.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    document = {
        "schema_version": 1,
        "run_id": run_id,
        "iterations": iterations if iterations is not None else [{"iteration": 1}],
    }
    path.write_text(yaml.safe_dump(document, sort_keys=False))
    return path


def _read(path):
    return yaml.safe_load(path.read_text())


def test_append_refinement_outcome_adds_to_current_iteration_section(tmp_path) -> None:
    path = _write_refinement(
        tmp_path,
        iterations=[{"iteration": 1, "outcomes": [{"event": "planned"}]}, {"iteration": 2}],
    )

    append_refinement_outcome(tmp_path, "run-1", {"event": "accepted", "commit": "abc"})

    document = _read(path)
    assert document["iterations"][0]["outcomes"] == [{"event": "planned"}]
    assert document["iterations"][1]["outcomes"] == [{"event": "accepted", "commit": "abc"}]


def test_append_refinement_outcome_is_noop_without_context_document(tmp_path) -> None:
    append_refinement_outcome(tmp_path, "run-1", {"event": "accepted"})

    assert not (tmp_path / ".process" / "edd" / "run-1" / "refinement.yaml").exists()


@pytest.mark.asyncio
async def test_record_confirmed_regression_appends_outcome_to_refinement_yaml(tmp_path) -> None:
    from edd_refinement_workflow.activities.regression_recovery import (
        record_confirmed_regression_activity,
    )

    path = _write_refinement(tmp_path)
    ProgressRecordStore(tmp_path).create_or_resume("run-1", {})

    result = await record_confirmed_regression_activity(
        "run-1", "candidate-1", {"passing": 4}, {"passing": 4}, 3, str(tmp_path)
    )

    assert result["consecutive_confirmed_regressions"] == 1
    outcomes = _read(path)["iterations"][0]["outcomes"]
    assert outcomes == [
        {
            "event": "regression_confirmed",
            "candidate_id": "candidate-1",
            "consecutive_confirmed_regressions": 1,
        }
    ]


@pytest.mark.asyncio
async def test_commit_accepted_candidate_appends_outcome_to_refinement_yaml(
    tmp_path, monkeypatch
) -> None:
    from edd_refinement_workflow.activities.commit_accepted_candidate import (
        commit_accepted_candidate_activity,
    )

    path = _write_refinement(tmp_path)
    ProgressRecordStore(tmp_path).create_or_resume("run-1", {})
    monkeypatch.setattr(
        "edd_refinement_workflow.activities.commit_accepted_candidate._commit_repository",
        lambda root, message: "commit-1",
    )

    result = await commit_accepted_candidate_activity(
        "run-1", {"candidate_id": "candidate-1", "passing": 6}, str(tmp_path)
    )

    assert result["commit"] == "commit-1"
    outcomes = _read(path)["iterations"][0]["outcomes"]
    assert outcomes == [
        {"event": "accepted", "candidate_id": "candidate-1", "commit": "commit-1"}
    ]


@pytest.mark.asyncio
async def test_record_reverted_proposal_appends_outcome_to_refinement_yaml(tmp_path) -> None:
    from edd_refinement_workflow.activities.regression_recovery import (
        record_reverted_proposal_context_activity,
    )

    path = _write_refinement(tmp_path)
    ProgressRecordStore(tmp_path).create_or_resume("run-1", {})

    await record_reverted_proposal_context_activity(
        "run-1",
        {
            "candidate_id": "candidate-1",
            "recovery_result": {"recovered": True},
        },
        str(tmp_path),
    )

    outcomes = _read(path)["iterations"][0]["outcomes"]
    assert outcomes == [
        {"event": "reverted", "candidate_id": "candidate-1", "recovered": True}
    ]


@pytest.mark.asyncio
async def test_human_handoff_appends_outcome_to_refinement_yaml(tmp_path) -> None:
    from edd_refinement_workflow.activities.regression_recovery import (
        human_handoff_activity,
    )

    path = _write_refinement(tmp_path)
    ProgressRecordStore(tmp_path).create_or_resume("run-1", {})

    await human_handoff_activity(
        "run-1", "unstable_result", {"confirmation": {}}, str(tmp_path)
    )

    outcomes = _read(path)["iterations"][0]["outcomes"]
    assert outcomes == [{"event": "human_handoff", "reason": "unstable_result"}]
