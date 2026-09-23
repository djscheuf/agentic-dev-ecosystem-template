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


def test_rerun_degraded_candidate_with_repeated_degradation_confirms_regression(tmp_path) -> None:
    store = ProgressRecordStore(tmp_path)
    store.create_or_resume("run-1", {"evaluation_configuration": {"command": ["eval"], "configuration": "config", "pinned_provider_version": "provider@1", "timeout_seconds": 10}, "best_accepted_state": {"metrics": {"passing": 5}}, "confirmation_evaluations": [], "consecutive_confirmed_regressions": 0})
    activity = RerunDegradedCandidateActivity(store, lambda **kwargs: {"passing": 4})

    result = activity.run("run-1", "candidate-1", str(tmp_path))

    assert result["classification"] == "confirmed_regression"
    assert store.create_or_resume("run-1", {})["consecutive_confirmed_regressions"] == 1


def test_rerun_degraded_candidate_compares_against_iteration_start_baseline_when_given(tmp_path) -> None:
    store = ProgressRecordStore(tmp_path)
    store.create_or_resume(
        "run-1",
        {
            "evaluation_configuration": {
                "command": ["eval"],
                "configuration": "config",
                "pinned_provider_version": "provider@1",
                "timeout_seconds": 10,
            },
            # best_accepted_state has since raced ahead of what the plan started from.
            "best_accepted_state": {"metrics": {"passing": 10}},
            "confirmation_evaluations": [],
            "consecutive_confirmed_regressions": 0,
        },
    )
    activity = RerunDegradedCandidateActivity(store, lambda **kwargs: {"passing": 6})

    result = activity.run(
        "run-1",
        "candidate-1",
        str(tmp_path),
        iteration_start_baseline={"passing": 5},
    )

    # 6 >= 5 (the frozen iteration-start baseline), so this is not a confirmed
    # regression, even though 6 < 10 (best_accepted_state, which is ignored here).
    assert result["classification"] == "flaky_evidence"
    assert store.create_or_resume("run-1", {})["consecutive_confirmed_regressions"] == 0


def test_rerun_degraded_candidate_confirms_regression_against_iteration_start_baseline(
    tmp_path,
) -> None:
    store = ProgressRecordStore(tmp_path)
    store.create_or_resume(
        "run-1",
        {
            "evaluation_configuration": {
                "command": ["eval"],
                "configuration": "config",
                "pinned_provider_version": "provider@1",
                "timeout_seconds": 10,
            },
            "best_accepted_state": {"metrics": {"passing": 10}},
            "confirmation_evaluations": [],
            "consecutive_confirmed_regressions": 0,
        },
    )
    activity = RerunDegradedCandidateActivity(store, lambda **kwargs: {"passing": 4})

    result = activity.run(
        "run-1",
        "candidate-1",
        str(tmp_path),
        iteration_start_baseline={"passing": 5},
    )

    assert result["classification"] == "confirmed_regression"
    assert store.create_or_resume("run-1", {})["consecutive_confirmed_regressions"] == 1
