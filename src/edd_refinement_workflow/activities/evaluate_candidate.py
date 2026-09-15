from collections.abc import Callable
from datetime import UTC, datetime

from cadence import activity

from ..candidate_results import CandidateMetricRecord


class EvaluateCandidateActivity:
    def __init__(self, store, harness: Callable[..., dict], now: Callable[[], str] | None = None) -> None:
        self.store = store
        self.harness = harness
        self.now = now or (lambda: datetime.now(UTC).isoformat())

    def run(self, run_id: str, candidate_id: str, repo_root: str) -> dict:
        record = self.store.create_or_resume(run_id, {})
        configuration = record["evaluation_configuration"]
        result = self.harness(
            command=configuration["command"],
            configuration=configuration["configuration"],
            provider=configuration["pinned_provider_version"],
            cwd=repo_root,
            timeout=configuration["timeout_seconds"],
        )
        metric = CandidateMetricRecord(
            candidate_id=candidate_id,
            run_id=run_id,
            attempt_number=len(record.get("candidate_metrics", [])) + 1,
            passing=result["passing"],
            failing=result["failing"],
            total=result["total"],
            percentage=result["percentage"],
            required_coverage=result["required_coverage"],
            artifact_references=result["artifact_references"],
            pinned_provider_version=configuration["pinned_provider_version"],
            measurement_context=configuration["measurement_context"],
            evaluated_at=self.now(),
            status="success",
            failure_reason=None,
            usable_for_acceptance=True,
        ).to_dict()
        record["candidate_metrics"] = record.get("candidate_metrics", []) + [metric]
        self.store.save(run_id, record)
        return metric


@activity.defn(name="evaluate_candidate")
async def evaluate_candidate_activity(run_id: str, candidate_id: str, repo_root: str) -> dict:
    raise NotImplementedError
