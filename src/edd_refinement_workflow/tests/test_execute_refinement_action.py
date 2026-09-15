import pytest

from edd_refinement_workflow.activities.execute_refinement_action import (
    ExecuteRefinementActionActivity,
)


def test_execute_refinement_action_rejects_unapproved_expectation_change() -> None:
    harness_calls = []
    activity = ExecuteRefinementActionActivity(
        harness_runner=lambda **kwargs: harness_calls.append(kwargs)
    )
    planning = {
        "action": "propose_evaluation_expectation_change",
        "requires_approval": True,
        "proposal_id": "proposal-1",
        "proposed_diff_hash": "abc123",
        "intended_files": ["evals/required.yaml"],
    }

    with pytest.raises(ValueError, match="missing_approval"):
        activity.run("run-1", planning, None, "/repo")

    assert harness_calls == []


def test_execute_refinement_action_rejects_approval_diff_hash_mismatch() -> None:
    harness_calls = []
    activity = ExecuteRefinementActionActivity(
        harness_runner=lambda **kwargs: harness_calls.append(kwargs)
    )
    planning = {
        "action": "propose_evaluation_expectation_change",
        "requires_approval": True,
        "proposal_id": "proposal-1",
        "proposed_diff_hash": "abc123",
        "intended_files": ["evals/required.yaml"],
    }

    with pytest.raises(ValueError, match="diff_hash_mismatch"):
        activity.run("run-1", planning, "different", "/repo")

    assert harness_calls == []
