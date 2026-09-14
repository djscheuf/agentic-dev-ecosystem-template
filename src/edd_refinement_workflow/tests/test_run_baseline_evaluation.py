from edd_refinement_workflow.activities.run_baseline_evaluation import (
    RunBaselineEvaluationActivity,
)
from edd_refinement_workflow.progress_record import ProgressRecordFactory, ProgressRecordStore


def test_baseline_evaluation_records_attempt_and_returns_result(tmp_path) -> None:
    store = ProgressRecordStore(tmp_path)
    factory = ProgressRecordFactory(store)
    run_id = factory.derive_run_id("wf-1", "abcdef123456")
    factory.create_or_resume(run_id, {"schema_version": 1, "run_id": run_id})

    def fake_harness(command: list[str], cwd: str, timeout: int) -> dict:
        return {"passing": 5, "failing": 1, "total": 6, "provider": "openai"}

    activity = RunBaselineEvaluationActivity(store=store, harness=fake_harness)
    profile = {
        "command": ["promptfoo", "eval"],
        "provider": "openai",
        "timeout": 120,
    }

    result = activity.run(run_id, profile, str(tmp_path))

    assert result == {
        "passing": 5,
        "failing": 1,
        "total": 6,
        "provider": "openai",
    }

    record = store.create_or_resume(run_id, {})
    assert len(record["attempts"]) == 1
    assert record["attempts"][0]["result"] == result
    assert record["attempts"][0]["provider"] == "openai"
