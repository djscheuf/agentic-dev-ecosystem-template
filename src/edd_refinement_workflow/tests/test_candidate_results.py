from edd_refinement_workflow.candidate_results import (
    CandidateMetricRecord,
    CandidateValidationResult,
    EvaluationRunConfiguration,
    ExecutionResult,
    UsageMetrics,
)


def test_execution_and_validation_results_preserve_structured_evidence() -> None:
    metrics = UsageMetrics(
        input_tokens=120,
        output_tokens=30,
        total_tokens=150,
        cost_usd=0.02,
    )

    execution = ExecutionResult(
        status="success",
        usage_metrics=metrics,
        changed_files=["src/skill.py"],
        diff_hash="abc123",
        failure_reason=None,
        atif_path=".process/edd/run-1/execution.atif.json",
        duration_ms=250,
    )
    validation = CandidateValidationResult(
        candidate_id="candidate-1",
        run_id="run-1",
        status="scope_valid",
        usage_metrics=metrics,
        changed_files=execution.changed_files,
        diff_hash=execution.diff_hash,
        rejection_reason=None,
        validated_at="2026-09-15T12:00:00Z",
    )

    assert execution.usage_metrics.total_tokens == 150
    assert validation.changed_files == ["src/skill.py"]


def test_candidate_metric_record_with_complete_metrics_serializes_all_fields() -> None:
    configuration = EvaluationRunConfiguration(
        command=["promptfoo", "eval", "-c", "promptfooconfig.yaml"],
        configuration="promptfooconfig.yaml",
        pinned_provider_version="openai:gpt-5@2026-08-07",
        timeout_seconds=120,
        measurement_context="baseline",
    )
    metric = CandidateMetricRecord(
        candidate_id="candidate-1",
        run_id="run-1",
        attempt_number=1,
        passing=7,
        failing=1,
        total=8,
        percentage=87.5,
        required_coverage={"required-1": 2},
        artifact_references=[".process/edd/run-1/candidate-1.json"],
        pinned_provider_version=configuration.pinned_provider_version,
        measurement_context=configuration.measurement_context,
        evaluated_at="2026-09-15T12:00:00Z",
        status="success",
        failure_reason=None,
        usable_for_acceptance=True,
    )

    assert configuration.to_dict() == {
        "command": ["promptfoo", "eval", "-c", "promptfooconfig.yaml"],
        "configuration": "promptfooconfig.yaml",
        "pinned_provider_version": "openai:gpt-5@2026-08-07",
        "timeout_seconds": 120,
        "measurement_context": "baseline",
    }
    assert metric.to_dict() == {
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
