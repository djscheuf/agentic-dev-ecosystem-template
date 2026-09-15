from edd_refinement_workflow.activities.evaluate_candidate import EvaluateCandidateActivity
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
