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


def test_candidate_status_query_returns_current_candidate() -> None:
    workflow = EddRefinementWorkflow()
    workflow._candidate = {
        "candidate_id": "candidate-1",
        "status": "rejected",
        "changed_files": ["README.md"],
        "rejection_reason": "out_of_scope",
    }

    assert workflow.get_candidate_status() == workflow._candidate


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

    assert "record_human_approved_evaluation_change" in calls
    assert calls[-2:] == ["execute_refinement_action", "validate_candidate"]
    assert result["applied_change"]["applied_diff_hash"] == "abc123"


@pytest.mark.asyncio
async def test_workflow_with_valid_candidate_invokes_candidate_evaluation(
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
    calls = []

    async def mock_execute(name: str, result_type, *args, **kwargs) -> dict:
        calls.append(name)
        if name == "initialize_run":
            return {"run_id": "run-1"}
        if name == "run_baseline_evaluation":
            return {"passing": 5}
        if name == "plan_refinement_action":
            return {"action": "repair", "intended_files": ["src/skill.py"]}
        if name == "execute_refinement_action":
            return {"status": "success", "changed_files": ["src/skill.py"]}
        if name == "validate_candidate":
            return {"candidate_id": "candidate-1", "status": "scope_valid"}
        return {"candidate_id": "candidate-1", "status": "success", "passing": 6}

    monkeypatch.setattr(
        "edd_refinement_workflow.workflow.execute_activity", mock_execute
    )

    result = await EddRefinementWorkflow().run(
        preflight,
        {
            "workflow_run_id": "wf-1",
            "profile": {"command": ["x"], "provider": "p", "timeout": 1},
            "proposed_action": "repair",
        },
    )

    assert calls[-3:] == [
        "execute_refinement_action",
        "validate_candidate",
        "evaluate_candidate",
    ]
    assert result["candidate"]["status"] == "scope_valid"
    assert result["candidate_evaluation"]["passing"] == 6


@pytest.mark.asyncio
async def test_workflow_resumes_persisted_candidate_without_rerunning_harness(
    tmp_path, monkeypatch
) -> None:
    candidate = {"candidate_id": "candidate-1", "status": "scope_valid"}
    calls = []

    async def mock_execute(name: str, result_type, *args, **kwargs) -> dict:
        calls.append(name)
        return {"run_id": "run-1", "candidate": candidate}

    monkeypatch.setattr(
        "edd_refinement_workflow.workflow.execute_activity", mock_execute
    )
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

    result = await EddRefinementWorkflow().run(
        preflight,
        {
            "workflow_run_id": "wf-1",
            "profile": {"command": ["x"], "provider": "p", "timeout": 1},
        },
    )

    assert calls == ["initialize_run"]
    assert result["candidate"] == candidate


@pytest.mark.asyncio
async def test_workflow_creates_no_candidate_when_execution_fails(
    tmp_path, monkeypatch
) -> None:
    calls = []

    async def mock_execute(name: str, result_type, *args, **kwargs) -> dict:
        calls.append(name)
        if name == "initialize_run":
            return {"run_id": "run-1"}
        if name == "run_baseline_evaluation":
            return {"passing": 5}
        if name == "plan_refinement_action":
            return {"action": "repair", "intended_files": ["src/skill.py"]}
        return {"status": "failed", "failure_reason": "harness_failure:1"}

    monkeypatch.setattr(
        "edd_refinement_workflow.workflow.execute_activity", mock_execute
    )
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

    result = await EddRefinementWorkflow().run(
        preflight,
        {
            "workflow_run_id": "wf-1",
            "profile": {"command": ["x"], "provider": "p", "timeout": 1},
        },
    )

    assert calls[-1] == "execute_refinement_action"
    assert "candidate" not in result


@pytest.mark.asyncio
async def test_workflow_with_accepted_comparison_commits_candidate(tmp_path, monkeypatch) -> None:
    calls = []

    async def mock_execute(name: str, result_type, *args, **kwargs) -> dict:
        calls.append((name, args))
        if name == "initialize_run":
            return {"run_id": "run-1", "best_accepted_state": {"metrics": {"passing": 5, "required_coverage": {"required-1": 1}, "measurement_context": "baseline"}}}
        if name == "run_baseline_evaluation":
            return {"passing": 5}
        if name == "plan_refinement_action":
            return {"action": "repair", "intended_files": ["src/skill.py"]}
        if name == "execute_refinement_action":
            return {"status": "success", "changed_files": ["src/skill.py"]}
        if name == "validate_candidate":
            return {"candidate_id": "candidate-1", "status": "scope_valid"}
        if name == "evaluate_candidate":
            return {"candidate_id": "candidate-1", "passing": 6, "required_coverage": {"required-1": 1}, "measurement_context": "baseline"}
        return {"candidate_id": "candidate-1", "commit": "commit-1"}

    monkeypatch.setattr("edd_refinement_workflow.workflow.execute_activity", mock_execute)
    monkeypatch.setattr("edd_refinement_workflow.workflow.compare_candidate_to_best", lambda candidate, best: {"decision": "accept"})
    preflight = PreflightResult(status="success", target_context=TargetRepositoryContext(repo_root=tmp_path, anchor_path="", explicit_root=None, branch="main", starting_revision="abc123456"))

    result = await EddRefinementWorkflow().run(preflight, {"workflow_run_id": "wf-1", "profile": {"command": ["x"], "provider": "p", "timeout": 1}})

    assert [name for name, _ in calls][-2:] == ["evaluate_candidate", "commit_accepted_candidate"]
    assert result["comparison"]["decision"] == "accept"
    assert result["best_accepted_state"]["commit"] == "commit-1"


async def _result(value):
    return value
