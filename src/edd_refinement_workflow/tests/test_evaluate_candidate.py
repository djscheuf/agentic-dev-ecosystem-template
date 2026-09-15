import pytest
from edd_refinement_workflow.activities.evaluate_candidate import (
    EvaluateCandidateActivity,
    evaluate_candidate_activity,
)
from edd_refinement_workflow.progress_record import ProgressRecordStore


def test_evaluate_candidate_with_successful_result_records_structured_metrics(tmp_path) -> None:
    store = ProgressRecordStore(tmp_path)
    configuration = {
        "command": ["promptfoo", "eval", "-c", "promptfooconfig.yaml"],
        "configuration": "promptfooconfig.yaml",
        "pinned_provider_version": "openai:gpt-5@2026-08-07",
        "timeout_seconds": 120,
        "measurement_context": "baseline",
    }
    store.create_or_resume(
        "run-1",
        {
            "schema_version": 4,
            "run_id": "run-1",
            "evaluation_configuration": configuration,
            "candidate_metrics": [],
        },
    )
    invocations = []

    def harness(**kwargs) -> dict:
        invocations.append(kwargs)
        return {
            "passing": 7,
            "failing": 1,
            "total": 8,
            "percentage": 87.5,
            "required_coverage": {"required-1": 2},
            "artifact_references": [".process/edd/run-1/candidate-1.json"],
        }

    activity = EvaluateCandidateActivity(store, harness, now=lambda: "2026-09-15T12:00:00Z")

    result = activity.run("run-1", "candidate-1", str(tmp_path))

    assert invocations == [
        {
            "command": configuration["command"],
            "configuration": configuration["configuration"],
            "provider": configuration["pinned_provider_version"],
            "cwd": str(tmp_path),
            "timeout": configuration["timeout_seconds"],
        }
    ]
    assert result == {
        "candidate_id": "candidate-1",
        "run_id": "run-1",
        "attempt_number": 1,
        "passing": 7,
        "failing": 1,
        "total": 8,
        "percentage": 87.5,
        "required_coverage": {"required-1": 2},
        "artifact_references": [".process/edd/run-1/candidate-1.json"],
        "pinned_provider_version": "openai:gpt-5@2026-08-07",
        "measurement_context": "baseline",
        "evaluated_at": "2026-09-15T12:00:00Z",
        "status": "success",
        "failure_reason": None,
        "usable_for_acceptance": True,
    }
    assert store.create_or_resume("run-1", {})["candidate_metrics"] == [result]


def test_evaluate_candidate_with_usage_and_retry_context_returns_accounting_fields(tmp_path) -> None:
    store = ProgressRecordStore(tmp_path)
    store.create_or_resume("run-1", {"evaluation_configuration": {"command": ["eval"], "configuration": "config", "pinned_provider_version": "v1", "timeout_seconds": 10, "measurement_context": "baseline"}, "candidate_metrics": []})
    result = EvaluateCandidateActivity(store, lambda **kwargs: {"passing": 1, "failing": 0, "total": 1, "percentage": 100.0, "required_coverage": {}, "artifact_references": [], "usage_metrics": {"prompt_tokens": 4, "completion_tokens": 2, "total_tokens": 6}, "is_retry": True, "logical_iteration_number": 2}).run("run-1", "candidate-1", str(tmp_path))

    assert result["usage_metrics"] == {"prompt_tokens": 4, "completion_tokens": 2, "total_tokens": 6}
    assert result["is_retry"] is True
    assert result["logical_iteration_number"] == 2


def test_evaluate_candidate_with_malformed_metrics_records_rejected_attempt(tmp_path) -> None:
    store = ProgressRecordStore(tmp_path)
    store.create_or_resume(
        "run-1",
        {
            "evaluation_configuration": {
                "command": ["promptfoo", "eval"],
                "configuration": "promptfooconfig.yaml",
                "pinned_provider_version": "openai:gpt-5@2026-08-07",
                "timeout_seconds": 120,
                "measurement_context": "baseline",
            },
            "candidate_metrics": [],
        },
    )
    activity = EvaluateCandidateActivity(store, lambda **kwargs: {"passing": 1})

    result = activity.run("run-1", "candidate-1", str(tmp_path))

    assert result["status"] == "rejected"
    assert result["failure_reason"] == "malformed_metrics"
    assert result["usable_for_acceptance"] is False
    assert store.create_or_resume("run-1", {})["candidate_metrics"] == [result]


def test_evaluate_candidate_with_infrastructure_error_records_non_regression_attempt(tmp_path) -> None:
    store = ProgressRecordStore(tmp_path)
    store.create_or_resume("run-1", {"evaluation_configuration": {"command": ["eval"], "configuration": "config", "pinned_provider_version": "provider@1", "timeout_seconds": 10, "measurement_context": "baseline"}, "candidate_metrics": []})

    def failing_harness(**kwargs):
        raise RuntimeError("runner unavailable")

    result = EvaluateCandidateActivity(store, failing_harness).run("run-1", "candidate-1", str(tmp_path))

    assert result["status"] == "infra_error"
    assert result["failure_reason"] == "runner unavailable"
    assert result["usable_for_acceptance"] is False


def test_evaluate_candidate_with_timeout_records_attempt_without_iteration_advance(tmp_path) -> None:
    store = ProgressRecordStore(tmp_path)
    store.create_or_resume(
        "run-1",
        {
            "evaluation_configuration": {
                "command": ["eval"],
                "configuration": "config",
                "pinned_provider_version": "provider@1",
                "timeout_seconds": 10,
                "measurement_context": "baseline",
            },
            "candidate_metrics": [],
            "iteration_history": [{"iteration": 1}],
        },
    )

    def timed_out_harness(**kwargs):
        raise TimeoutError

    result = EvaluateCandidateActivity(store, timed_out_harness).run(
        "run-1", "candidate-1", str(tmp_path)
    )

    record = store.create_or_resume("run-1", {})
    assert result["status"] == "timeout"
    assert result["failure_reason"] == "evaluation_timeout"
    assert result["usable_for_acceptance"] is False
    assert record["candidate_metrics"] == [result]
    assert record["iteration_history"] == [{"iteration": 1}]


@pytest.mark.asyncio
async def test_evaluate_candidate_activity_executes_persisted_configuration(tmp_path, monkeypatch) -> None:
    store = ProgressRecordStore(tmp_path)
    store.create_or_resume("run-1", {"evaluation_configuration": {"command": ["eval"], "configuration": "config", "pinned_provider_version": "provider@1", "timeout_seconds": 10, "measurement_context": "baseline"}, "candidate_metrics": []})
    monkeypatch.setattr("edd_refinement_workflow.activities.evaluate_candidate._run_evaluation_command", lambda **kwargs: {"passing": 1, "failing": 0, "total": 1, "percentage": 100.0, "required_coverage": {}, "artifact_references": []})

    result = await evaluate_candidate_activity("run-1", "candidate-1", str(tmp_path))

    assert result["status"] == "success"
    assert result["candidate_id"] == "candidate-1"
