from edd_refinement_workflow.candidate_results import (
    CandidateValidationResult,
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
