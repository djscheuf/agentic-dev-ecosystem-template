from edd_refinement_workflow.activities.rerun_degraded_candidate import RerunDegradedCandidateActivity
from edd_refinement_workflow.progress_record import ProgressRecordStore


def test_rerun_degraded_candidate_with_unchanged_candidate_records_confirmation(tmp_path) -> None:
    store = ProgressRecordStore(tmp_path)
    configuration = {
        "command": ["promptfoo", "eval"],
        "configuration": "promptfooconfig.yaml",
        "pinned_provider_version": "provider@1",
        "timeout_seconds": 30,
        "measurement_context": "baseline",
    }
    store.create_or_resume(
        "run-1",
        {"evaluation_configuration": configuration, "confirmation_evaluations": []},
    )
    calls = []

    def harness(**kwargs):
        calls.append(kwargs)
        return {"passing": 4, "total": 6}

    result = RerunDegradedCandidateActivity(store, harness).run(
        "run-1", "candidate-1", str(tmp_path)
    )

    assert calls == [{
        "command": configuration["command"],
        "configuration": configuration["configuration"],
        "provider": configuration["pinned_provider_version"],
        "cwd": str(tmp_path),
        "timeout": configuration["timeout_seconds"],
    }]
    assert result == {
        "candidate_id": "candidate-1",
        "is_confirmation_rerun": True,
        "result": {"passing": 4, "total": 6},
    }
    assert store.create_or_resume("run-1", {})["confirmation_evaluations"] == [result]
