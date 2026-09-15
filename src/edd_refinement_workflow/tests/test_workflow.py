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


@pytest.mark.asyncio
async def test_workflow_requires_explicit_approval_and_records_timeout(
    tmp_path, monkeypatch
) -> None:
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
        "proposed_action": "propose_evaluation_expectation_change",
        "proposal_id": "proposal-1",
        "proposed_diff_hash": "abc123",
        "approval_timeout_seconds": 60,
    }
    calls = []

    async def mock_execute(name: str, result_type, *args, **kwargs) -> dict:
        calls.append(name)
        if name == "initialize_run":
            return {"run_id": "run-1"}
        if name == "run_baseline_evaluation":
            return {"passing": 5}
        if name == "plan_refinement_action":
            return {
                "action": "propose_evaluation_expectation_change",
                "requires_approval": True,
                "proposal_id": "proposal-1",
                "proposed_diff_hash": "abc123",
            }
        if name == "request_human_approval":
            return {"proposal_id": "proposal-1", "status": "pending"}
        return {"proposal_id": "proposal-1", "status": "decided", "decision": "timeout"}

    workflow = EddRefinementWorkflow()
    monkeypatch.setattr("edd_refinement_workflow.workflow.execute_activity", mock_execute)
    monkeypatch.setattr(workflow, "_await_approval", lambda timeout: _result("timeout"))

    result = await workflow.run(preflight, request)

    assert calls[-2:] == ["request_human_approval", "record_human_approval_decision"]
    assert result["approval"]["decision"] == "timeout"
    assert result["approved"] is False
    assert result["next_state"] == "planning"


def test_workflow_ignores_decisions_after_approval_is_decided() -> None:
    workflow = EddRefinementWorkflow()
    workflow._approval_request = {
        "proposal_id": "proposal-1",
        "status": "decided",
        "decision": "timeout",
    }

    workflow.approve_evaluation_change("approve", "proposal-1")

    assert workflow._pending_approval_decision is None
    assert workflow.get_approval_status()["decision"] == "timeout"


@pytest.mark.asyncio
async def test_workflow_records_only_the_exact_approved_diff(tmp_path, monkeypatch) -> None:
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
        "proposed_action": "propose_evaluation_expectation_change",
        "proposal_id": "proposal-1",
        "proposed_diff_hash": "abc123",
        "executed_diff_hash": "abc123",
    }
    calls = []

    async def mock_execute(name: str, result_type, *args, **kwargs) -> dict:
        calls.append(name)
        if name == "initialize_run":
            return {"run_id": "run-1"}
        if name == "run_baseline_evaluation":
            return {"passing": 5}
        if name == "plan_refinement_action":
            return {
                "action": "propose_evaluation_expectation_change",
                "requires_approval": True,
                "proposal_id": "proposal-1",
                "proposed_diff_hash": "abc123",
            }
        if name == "request_human_approval":
            return {"proposal_id": "proposal-1", "status": "pending"}
        if name == "record_human_approval_decision":
            return {"proposal_id": "proposal-1", "decision": "approve"}
        return {"applied_diff_hash": "abc123", "approval_context": "human_approved_evaluation_change"}

    workflow = EddRefinementWorkflow()
    monkeypatch.setattr("edd_refinement_workflow.workflow.execute_activity", mock_execute)
    monkeypatch.setattr(workflow, "_await_approval", lambda timeout: _result("approve"))

    result = await workflow.run(preflight, request)

    assert calls[-1] == "record_human_approved_evaluation_change"
    assert result["applied_change"]["applied_diff_hash"] == "abc123"


async def _result(value):
    return value
