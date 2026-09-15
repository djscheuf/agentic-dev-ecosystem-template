from concurrent.futures import ThreadPoolExecutor

from edd_refinement_workflow.activities.update_durable_counters import UpdateDurableCountersActivity
from edd_refinement_workflow.progress_record import ProgressRecordStore


def test_update_durable_counters_with_retry_tracks_tokens_without_iteration_advance(tmp_path) -> None:
    store = ProgressRecordStore(tmp_path)
    store.create_or_resume(
        "run-1",
        {
            "logical_iteration_count": 0,
            "cumulative_token_usage": 0,
            "attempt_records": [],
        },
    )
    activity = UpdateDurableCountersActivity(store)

    activity.run(
        "run-1",
        {
            "attempt_id": "attempt-1",
            "logical_iteration_number": 1,
            "is_retry": False,
            "usage_metrics": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            "status": "success",
        },
    )
    result = activity.run(
        "run-1",
        {
            "attempt_id": "attempt-2",
            "logical_iteration_number": 1,
            "is_retry": True,
            "usage_metrics": {"prompt_tokens": 6, "completion_tokens": 4, "total_tokens": 10},
            "status": "success",
        },
    )

    assert result["logical_iteration_count"] == 1
    assert result["cumulative_token_usage"] == 25
    assert [attempt["attempt_id"] for attempt in result["attempt_records"]] == [
        "attempt-1",
        "attempt-2",
    ]


def test_update_durable_counters_with_missing_usage_records_zero_and_marker(tmp_path) -> None:
    store = ProgressRecordStore(tmp_path)
    store.create_or_resume(
        "run-1",
        {
            "logical_iteration_count": 0,
            "cumulative_token_usage": 0,
            "attempt_records": [],
        },
    )

    result = UpdateDurableCountersActivity(store).run(
        "run-1",
        {
            "attempt_id": "attempt-1",
            "logical_iteration_number": 1,
            "is_retry": False,
            "status": "timeout",
        },
    )

    assert result["cumulative_token_usage"] == 0
    assert result["attempt_records"][0]["usage_missing"] is True
    assert result["attempt_records"][0]["total_tokens"] == 0


def test_update_durable_counters_with_concurrent_attempts_preserves_every_update(tmp_path) -> None:
    store = ProgressRecordStore(tmp_path)
    store.create_or_resume("run-1", {"logical_iteration_count": 0, "cumulative_token_usage": 0, "attempt_records": []})
    activity = UpdateDurableCountersActivity(store)

    def update(index):
        activity.run("run-1", {"attempt_id": f"attempt-{index}", "logical_iteration_number": index, "is_retry": False, "usage_metrics": {"prompt_tokens": 1, "completion_tokens": 0, "total_tokens": 1}, "status": "success"})

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(update, range(20)))

    result = store.create_or_resume("run-1", {})
    assert len(result["attempt_records"]) == 20
    assert result["cumulative_token_usage"] == 20
    assert result["logical_iteration_count"] == 20
