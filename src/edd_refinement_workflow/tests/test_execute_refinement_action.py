import pytest

from edd_refinement_workflow.candidate_results import ExecutionResult, UsageMetrics
from edd_refinement_workflow.activities.execute_refinement_action import (
    ExecuteRefinementActionActivity,
    execute_refinement_action_activity,
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


def test_execute_refinement_action_returns_harness_usage_and_changed_files() -> None:
    activity = ExecuteRefinementActionActivity(
        harness_runner=lambda **kwargs: {
            "status": "success",
            "observation": {
                "usage": {
                    "prompt_tokens": 120,
                    "completion_tokens": 30,
                    "cost_usd": 0.02,
                },
                "atif_path": ".process/edd/run-1/devin-trajectory.json",
                "duration_ms": 250,
            },
            "changed_files": ["src/skill.py"],
            "diff_hash": "abc123",
        }
    )

    result = activity.run(
        "run-1",
        {"action": "repair", "intended_files": ["src/skill.py"]},
        None,
        "/repo",
    )

    assert isinstance(result, ExecutionResult)
    assert result.usage_metrics.total_tokens == 150
    assert result.changed_files == ["src/skill.py"]
    assert result.atif_path == ".process/edd/run-1/devin-trajectory.json"


@pytest.mark.asyncio
async def test_execute_refinement_action_entrypoint_runs_configured_activity(
    monkeypatch,
) -> None:
    expected = ExecutionResult(
        status="success",
        usage_metrics=UsageMetrics(1, 1, 2, 0.01),
        changed_files=["src/skill.py"],
        diff_hash="abc123",
        failure_reason=None,
        atif_path=None,
        duration_ms=1,
    )

    class FakeActivity:
        def run(self, *args):
            return expected

    monkeypatch.setattr(
        "edd_refinement_workflow.activities.execute_refinement_action.EXECUTION_ACTIVITY",
        FakeActivity(),
    )

    result = await execute_refinement_action_activity(
        "run-1", {"action": "repair"}, None, "/repo"
    )

    assert result["diff_hash"] == "abc123"


def test_execute_refinement_action_emits_success_event() -> None:
    events = []
    activity = ExecuteRefinementActionActivity(
        harness_runner=lambda **kwargs: {
            "status": "success",
            "observation": {
                "usage": {
                    "prompt_tokens": 1,
                    "completion_tokens": 1,
                    "cost_usd": 0.01,
                },
                "atif_path": None,
                "duration_ms": 2,
            },
            "changed_files": ["src/skill.py"],
            "diff_hash": "abc123",
        },
        on_event=lambda name, **data: events.append((name, data)),
    )

    activity.run("run-1", {"action": "repair"}, None, "/repo")

    assert events == [
        (
            "RefinementActivitySucceeded",
            {"run_id": "run-1", "duration_ms": 2, "changed_files_count": 1},
        )
    ]


def test_execute_refinement_action_reports_harness_failure_without_candidate() -> None:
    def fail(**kwargs):
        raise RuntimeError("harness_failure:1")

    events = []
    activity = ExecuteRefinementActionActivity(
        harness_runner=fail,
        on_event=lambda name, **data: events.append((name, data)),
    )

    result = activity.run("run-1", {"action": "repair"}, None, "/repo")

    assert result.status == "failed"
    assert result.changed_files == []
    assert result.failure_reason == "harness_failure:1"
    assert events[0][0] == "RefinementActivityFailed"
