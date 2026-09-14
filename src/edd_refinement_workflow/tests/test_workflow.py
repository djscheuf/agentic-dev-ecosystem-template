import pytest
from common.preflight import PreflightResult, TargetRepositoryContext
from edd_refinement_workflow.workflow import EddRefinementWorkflow


@pytest.mark.asyncio
async def test_workflow_sequences_activities_in_order(tmp_path, monkeypatch) -> None:
    preflight = PreflightResult(
        status="success",
        target_context=TargetRepositoryContext(
            repo_root=tmp_path,
            anchor_path="",
            explicit_root=None,
            branch="main",
            starting_revision="abc123456",
        ),
    )
    request = {
        "workflow_run_id": "wf-1",
        "profile": {"command": ["x"], "provider": "p", "timeout": 1},
    }

    calls = []

    async def mock_execute(name: str, result_type, *args, **kwargs) -> dict:
        calls.append(name)
        if name == "initialize_run":
            return {"run_id": "wf-1-abc1234"}
        if name == "run_baseline_evaluation":
            return {"passing": 5}
        if name == "plan_refinement_action":
            return {"action": "stop"}
        return {}

    monkeypatch.setattr(
        "edd_refinement_workflow.workflow.execute_activity", mock_execute
    )

    result = await EddRefinementWorkflow().run(preflight, request)

    assert calls == [
        "initialize_run",
        "run_baseline_evaluation",
        "plan_refinement_action",
    ]
    assert result["record"]["run_id"] == "wf-1-abc1234"
    assert result["baseline"]["passing"] == 5
    assert result["planning"]["action"] == "stop"
