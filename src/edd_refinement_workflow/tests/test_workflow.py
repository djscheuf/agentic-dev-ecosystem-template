from datetime import timedelta

import pytest
from common.preflight import PreflightResult, TargetRepositoryContext
from edd_refinement_workflow.workflow import EddRefinementWorkflow


@pytest.mark.asyncio
async def test_workflow_with_stop_plan_finalizes_run(tmp_path, monkeypatch) -> None:
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
        if name == "edd_plan":
            return {"action": "stop", "reason": "budget_exhausted"}
        if name == "finalize_run":
            return {"terminal_reason": "budget_exhausted", "report_path": "terminal.json"}
        return {}

    monkeypatch.setattr(
        "edd_refinement_workflow.workflow.execute_activity", mock_execute
    )

    result = await EddRefinementWorkflow().run(preflight, request)

    assert calls == [
        "initialize_run",
        "run_baseline_evaluation",
        "edd_plan",
        "finalize_run",
    ]
    assert result["record"]["run_id"] == "wf-1-abc1234"
    assert result["baseline"]["passing"] == 5
    assert result["planning"]["action"] == "stop"
    assert result["terminal_result"]["terminal_reason"] == "budget_exhausted"


@pytest.mark.asyncio
async def test_workflow_before_agentic_step_uses_limit_gate_and_finalizes_when_blocked(
    tmp_path, monkeypatch
) -> None:
    calls = []

    async def mock_execute(name: str, result_type, *args, **kwargs) -> dict:
        calls.append(name)
        if name == "initialize_run":
            return {
                "run_id": "run-1",
                "budgets": {"max_iterations": 0},
                "best_accepted_state": {"commit": "best-1"},
            }
        if name == "check_refinement_limits":
            return {
                "schedule_next_step": False,
                "stop_reason": "iteration_budget",
                "best_accepted_state": {"commit": "best-1"},
            }
        if name == "finalize_run":
            return {"terminal_reason": "iteration_budget"}
        raise AssertionError(f"unexpected activity: {name}")

    monkeypatch.setattr("edd_refinement_workflow.workflow.execute_activity", mock_execute)
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

    assert calls == ["initialize_run", "check_refinement_limits", "finalize_run"]
    assert result["limit_decision"]["best_accepted_state"] == {"commit": "best-1"}


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
        if name == "edd_plan":
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


def test_regression_status_query_exposes_recovery_and_handoff_context() -> None:
    workflow = EddRefinementWorkflow()
    workflow._regression_status = {"classification": "unstable_result", "next_state": "pending_human_review", "human_handoff": {"notified": True}}

    assert workflow.get_regression_status() == workflow._regression_status


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
        if name == "edd_plan":
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
    assert calls[-2:] == ["edd_do", "validate_candidate"]
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
        if name == "edd_plan":
            return {"action": "repair", "intended_files": ["src/skill.py"]}
        if name == "edd_do":
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
        "edd_do",
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
        if name == "edd_plan":
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

    assert calls[-1] == "edd_do"
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
        if name == "edd_plan":
            return {"action": "repair", "intended_files": ["src/skill.py"]}
        if name == "edd_do":
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


@pytest.mark.asyncio
async def test_workflow_with_degraded_comparison_reruns_candidate(tmp_path, monkeypatch) -> None:
    calls = []

    async def mock_execute(name: str, result_type, *args, **kwargs) -> dict:
        calls.append((name, args))
        responses = {
            "initialize_run": {"run_id": "run-1", "best_accepted_state": {"metrics": {"passing": 5, "required_coverage": {}, "measurement_context": "baseline"}}},
            "run_baseline_evaluation": {"passing": 5},
            "edd_plan": {"action": "repair"},
            "edd_do": {"status": "success"},
            "validate_candidate": {"candidate_id": "candidate-1", "status": "scope_valid"},
            "evaluate_candidate": {"candidate_id": "candidate-1", "passing": 4, "required_coverage": {}, "measurement_context": "baseline"},
            "rerun_degraded_candidate": {"candidate_id": "candidate-1", "is_confirmation_rerun": True},
            "classify_regression_evidence": {"classification": "unstable_result"},
            "human_handoff": {"notified": True},
        }
        return responses[name]

    monkeypatch.setattr("edd_refinement_workflow.workflow.execute_activity", mock_execute)
    monkeypatch.setattr("edd_refinement_workflow.workflow.compare_candidate_to_best", lambda candidate, best: {"decision": "rerun"})
    preflight = PreflightResult(status="success", target_context=TargetRepositoryContext(repo_root=tmp_path, anchor_path="", explicit_root=None, branch="main", starting_revision="abc123456"))

    result = await EddRefinementWorkflow().run(preflight, {"workflow_run_id": "wf-1", "profile": {"command": ["x"], "provider": "p", "timeout": 1}})

    assert [name for name, _ in calls][-4:] == ["evaluate_candidate", "rerun_degraded_candidate", "classify_regression_evidence", "human_handoff"]
    assert calls[-3][1][1] == "candidate-1"
    assert result["confirmation_rerun"]["is_confirmation_rerun"] is True
    assert result["regression_recovery"]["next_state"] == "pending_human_review"
    assert calls[-1][1][-1] == str(tmp_path)


@pytest.mark.asyncio
async def test_workflow_when_evaluating_candidate_applies_retry_policy(tmp_path, monkeypatch) -> None:
    options = {}

    async def mock_execute(name: str, result_type, *args, **kwargs) -> dict:
        if name == "evaluate_candidate":
            options.update(kwargs)
        responses = {
            "initialize_run": {"run_id": "run-1"},
            "run_baseline_evaluation": {"passing": 5},
            "edd_plan": {"action": "repair"},
            "edd_do": {"status": "success"},
            "validate_candidate": {"candidate_id": "candidate-1", "status": "scope_valid"},
            "evaluate_candidate": {"candidate_id": "candidate-1", "status": "success"},
        }
        return responses[name]

    monkeypatch.setattr("edd_refinement_workflow.workflow.execute_activity", mock_execute)
    preflight = PreflightResult(status="success", target_context=TargetRepositoryContext(repo_root=tmp_path, anchor_path="", explicit_root=None, branch="main", starting_revision="abc123456"))

    await EddRefinementWorkflow().run(preflight, {"workflow_run_id": "wf-1", "profile": {"command": ["x"], "provider": "p", "timeout": 30, "retry_policy": {"maximum_attempts": 3, "initial_interval_seconds": 2}}})

    assert options["start_to_close_timeout"] == timedelta(seconds=30)
    assert options["retry_policy"] == {
        "maximum_attempts": 3,
        "initial_interval": timedelta(seconds=2),
    }


@pytest.mark.asyncio
async def test_confirmed_regression_restores_and_verifies_before_continuing(monkeypatch) -> None:
    calls = []

    async def mock_execute(name: str, result_type, *args, **kwargs) -> dict:
        calls.append(name)
        return {
            "classify_regression_evidence": {"classification": "confirmed_regression"},
            "record_confirmed_regression": {"consecutive_confirmed_regressions": 1, "threshold_reached": False},
            "revert_repository_to_best": {"repo_clean": True},
            "evaluate_candidate": {"passing": 5},
            "verify_recovery_metrics": {"recovered": True},
            "record_reverted_proposal_context": {"candidate_id": "candidate-1"},
        }[name]

    monkeypatch.setattr("edd_refinement_workflow.workflow.execute_activity", mock_execute)
    result = await EddRefinementWorkflow()._handle_regression(
        "run-1", "candidate-1", {"passing": 4}, {"result": {"passing": 4}},
        {"commit": "best-1", "metrics": {"passing": 5}}, "/repo", 3,
    )

    assert calls == ["classify_regression_evidence", "record_confirmed_regression", "revert_repository_to_best", "evaluate_candidate", "verify_recovery_metrics", "record_reverted_proposal_context"]
    assert result["next_state"] == "planning"


@pytest.mark.asyncio
async def test_workflow_at_third_confirmed_regression_publishes_structured_handoff(monkeypatch) -> None:
    calls = []

    async def mock_execute(name, result_type, *args, **kwargs):
        calls.append(name)
        return {
            "classify_regression_evidence": {"classification": "confirmed_regression"},
            "record_confirmed_regression": {"consecutive_confirmed_regressions": 3, "threshold_reached": True},
            "publish_human_handoff": {"stop_reason": "regression_threshold", "attempts": [{}, {}, {}]},
        }[name]

    monkeypatch.setattr("edd_refinement_workflow.workflow.execute_activity", mock_execute)
    result = await EddRefinementWorkflow()._handle_regression(
        "run-1", "candidate-3", {"passing": 4}, {"passing": 4},
        {"commit": "best", "metrics": {"passing": 5}}, "/repo", 3,
    )

    assert calls == ["classify_regression_evidence", "record_confirmed_regression", "publish_human_handoff"]
    assert result["human_handoff"]["stop_reason"] == "regression_threshold"


@pytest.mark.asyncio
async def test_workflow_after_token_consuming_steps_accounts_usage_and_regates(monkeypatch) -> None:
    calls = []

    async def mock_execute(name, result_type, *args, **kwargs):
        calls.append((name, args))
        if name == "update_durable_counters":
            return {"budgets": {"token_budget": 10}, "cumulative_token_usage": 10}
        return {"schedule_next_step": False, "stop_reason": "token_budget"}

    monkeypatch.setattr("edd_refinement_workflow.workflow.execute_activity", mock_execute)
    record, limit_decision = await EddRefinementWorkflow()._account_and_check_limits(
        {"run_id": "run-1"}, {"usage_metrics": {"total_tokens": 10}}, "execute", "/repo"
    )

    assert [name for name, _ in calls] == ["update_durable_counters", "check_refinement_limits"]
    assert limit_decision["schedule_next_step"] is False


@pytest.mark.asyncio
async def test_workflow_across_execution_and_evaluation_accounts_and_gates_each_step(tmp_path, monkeypatch) -> None:
    calls = []
    responses = {
        "initialize_run": {"run_id": "run-1", "budgets": {"token_budget": 100}},
        "check_refinement_limits": {"schedule_next_step": True, "stop_reason": "none"},
        "run_baseline_evaluation": {"passing": 1},
        "edd_plan": {"action": "repair"},
        "edd_do": {"status": "success", "usage_metrics": {"total_tokens": 5}},
        "validate_candidate": {"status": "scope_valid", "candidate_id": "candidate-1"},
        "evaluate_candidate": {"status": "success", "passing": 2, "usage_metrics": {"total_tokens": 6}},
        "finalize_run": {"terminal_reason": "token_budget"},
    }

    async def mock_execute(name, result_type, *args, **kwargs):
        return responses[name]

    workflow = EddRefinementWorkflow()
    async def account(record, result, step, repo_root):
        calls.append(step)
        return record, {"schedule_next_step": step != "evaluation", "stop_reason": "token_budget" if step == "evaluation" else "none"}

    monkeypatch.setattr("edd_refinement_workflow.workflow.execute_activity", mock_execute)
    monkeypatch.setattr(workflow, "_account_and_check_limits", account)
    preflight = PreflightResult(status="success", target_context=TargetRepositoryContext(repo_root=tmp_path, anchor_path="", explicit_root=None, branch="main", starting_revision="abc"))

    result = await workflow.run(preflight, {"workflow_run_id": "wf", "profile": {"command": ["x"], "provider": "p", "timeout": 1}})

    assert calls == ["execution", "evaluation"]
    assert result["terminal_result"]["terminal_reason"] == "token_budget"


@pytest.mark.asyncio
async def test_workflow_runs_multiple_iterations_until_limit_stops(tmp_path, monkeypatch) -> None:
    plan_calls = []
    execute_calls = []
    evaluate_calls = []
    limit_calls = []

    async def mock_execute(name, result_type, *args, **kwargs):
        if name == "initialize_run":
            return {
                "run_id": "run-1",
                "budgets": {"token_budget": 100},
                "candidate_history": [],
            }
        if name == "check_refinement_limits":
            limit_calls.append(name)
            return {
                "schedule_next_step": len(limit_calls) < 4,
                "stop_reason": "token_budget" if len(limit_calls) >= 4 else "none",
            }
        if name == "run_baseline_evaluation":
            return {"passing": 5, "required_coverage": {}, "measurement_context": "baseline"}
        if name == "edd_plan":
            plan_calls.append(args)
            return {"action": "repair"}
        if name == "edd_do":
            execute_calls.append(args)
            return {"status": "success", "usage_metrics": {"total_tokens": 1}}
        if name == "validate_candidate":
            execute_id = len(execute_calls)
            return {"status": "scope_valid", "candidate_id": f"candidate-{execute_id}"}
        if name == "evaluate_candidate":
            candidate_id = args[1]
            n = int(candidate_id.split("-")[1])
            evaluate_calls.append(candidate_id)
            return {
                "status": "success",
                "candidate_id": candidate_id,
                "passing": 5 + n,
                "required_coverage": {},
                "measurement_context": "baseline",
                "usage_metrics": {"total_tokens": 1},
            }
        if name == "commit_accepted_candidate":
            candidate_evaluation = args[1]
            return {
                "candidate_id": candidate_evaluation["candidate_id"],
                "commit": f"commit-{candidate_evaluation['candidate_id']}",
                "metrics": candidate_evaluation,
            }
        if name == "finalize_run":
            return {"terminal_reason": "token_budget"}
        return {}

    workflow = EddRefinementWorkflow()

    async def account(record, result, step, repo_root):
        return record, {"schedule_next_step": True, "stop_reason": "none"}

    monkeypatch.setattr("edd_refinement_workflow.workflow.execute_activity", mock_execute)
    monkeypatch.setattr(workflow, "_account_and_check_limits", account)
    preflight = PreflightResult(
        status="success",
        target_context=TargetRepositoryContext(
            repo_root=tmp_path,
            anchor_path="",
            explicit_root=None,
            branch="main",
            starting_revision="abc",
        ),
    )

    result = await workflow.run(
        preflight,
        {
            "workflow_run_id": "wf",
            "profile": {"command": ["x"], "provider": "p", "timeout": 1},
        },
    )

    assert len(plan_calls) == 2
    assert len(execute_calls) == 2
    assert len(evaluate_calls) == 2
    assert result["terminal_result"]["terminal_reason"] == "token_budget"
    assert result["best_accepted_state"]["commit"] == "commit-candidate-2"


async def _result(value):
    return value
