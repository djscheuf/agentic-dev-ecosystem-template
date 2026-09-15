from collections.abc import Callable

from cadence import activity


class RerunDegradedCandidateActivity:
    def __init__(self, store, harness: Callable[..., dict]) -> None:
        self.store = store
        self.harness = harness

    def run(self, run_id: str, candidate_id: str, repo_root: str) -> dict:
        record = self.store.create_or_resume(run_id, {})
        configuration = record["evaluation_configuration"]
        evaluation = self.harness(
            command=configuration["command"],
            configuration=configuration["configuration"],
            provider=configuration["pinned_provider_version"],
            cwd=repo_root,
            timeout=configuration["timeout_seconds"],
        )
        result = {
            "candidate_id": candidate_id,
            "is_confirmation_rerun": True,
            "result": evaluation,
        }
        record["confirmation_evaluations"] = record.get(
            "confirmation_evaluations", []
        ) + [result]
        self.store.save(run_id, record)
        return result


@activity.defn(name="rerun_degraded_candidate")
async def rerun_degraded_candidate_activity(
    run_id: str, candidate_id: str, repo_root: str
) -> dict:
    raise NotImplementedError
