from cadence import activity


class UpdateDurableCountersActivity:
    def __init__(self, store) -> None:
        self.store = store

    def run(self, run_id: str, attempt_record: dict) -> dict:
        record = self.store.create_or_resume(run_id, {})
        usage = attempt_record.get("usage_metrics") or {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }
        stored_attempt = {
            **attempt_record,
            "prompt_tokens": usage["prompt_tokens"],
            "completion_tokens": usage["completion_tokens"],
            "total_tokens": usage["total_tokens"],
            "usage_missing": "usage_metrics" not in attempt_record,
        }
        stored_attempt.pop("usage_metrics", None)
        record["attempt_records"] = record.get("attempt_records", []) + [stored_attempt]
        record["cumulative_token_usage"] = record.get("cumulative_token_usage", 0) + usage["total_tokens"]
        if not attempt_record["is_retry"]:
            record["logical_iteration_count"] = record.get("logical_iteration_count", 0) + 1
        self.store.save(run_id, record)
        return record


@activity.defn(name="update_durable_counters")
async def update_durable_counters_activity(run_id: str, attempt_record: dict, repo_root: str = ".") -> dict:
    from ..progress_record import ProgressRecordStore

    return UpdateDurableCountersActivity(ProgressRecordStore(repo_root)).run(run_id, attempt_record)
