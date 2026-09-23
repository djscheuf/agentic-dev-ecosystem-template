from collections.abc import Callable

from cadence import activity


class RerunDegradedCandidateActivity:
    def __init__(self, store, harness: Callable[..., dict]) -> None:
        self.store = store
        self.harness = harness

    def run(
        self,
        run_id: str,
        candidate_id: str,
        repo_root: str,
        iteration_start_baseline: dict | None = None,
    ) -> dict:
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
        # Prefer the frozen iteration-start baseline the plan believed it was
        # improving on; fall back to best_accepted_state for callers that predate
        # ADR-017's iteration-start-baseline requirement.
        best_state = record.get("best_accepted_state")
        comparison_baseline = iteration_start_baseline or (
            best_state["metrics"] if best_state is not None else None
        )
        if comparison_baseline is not None:
            confirmed = evaluation["passing"] < comparison_baseline["passing"]
            result["classification"] = (
                "confirmed_regression" if confirmed else "flaky_evidence"
            )
            if confirmed:
                record["consecutive_confirmed_regressions"] = record.get(
                    "consecutive_confirmed_regressions", 0
                ) + 1
        record["confirmation_evaluations"] = record.get(
            "confirmation_evaluations", []
        ) + [result]
        self.store.save(run_id, record)
        return result


@activity.defn(name="rerun_degraded_candidate")
async def rerun_degraded_candidate_activity(
    run_id: str,
    candidate_id: str,
    repo_root: str,
    iteration_start_baseline: dict | None = None,
) -> dict:
    from ..progress_record import ProgressRecordStore
    from .evaluate_candidate import _run_evaluation_command

    return RerunDegradedCandidateActivity(
        ProgressRecordStore(repo_root), _run_evaluation_command
    ).run(run_id, candidate_id, repo_root, iteration_start_baseline)
