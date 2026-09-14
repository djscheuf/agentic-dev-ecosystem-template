from collections.abc import Callable


class RunBaselineEvaluationActivity:
    def __init__(
        self,
        store,
        harness: Callable[..., dict],
    ) -> None:
        self.store = store
        self.harness = harness

    def run(self, run_id: str, profile: dict, repo_root: str) -> dict:
        result = self.harness(
            command=profile["command"],
            cwd=repo_root,
            timeout=profile["timeout"],
        )

        attempt = {
            "command": profile["command"],
            "provider": profile["provider"],
            "timeout": profile["timeout"],
            "result": result,
        }

        record = self.store.create_or_resume(run_id, {})
        record["attempts"] = record.get("attempts", []) + [attempt]
        self.store.save(run_id, record)

        return result


from cadence import activity


@activity.defn(name="run_baseline_evaluation")
async def run_baseline_evaluation_activity(
    run_id: str, profile: dict, repo_root: str
) -> dict:
    raise NotImplementedError
