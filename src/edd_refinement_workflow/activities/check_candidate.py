import json
from collections.abc import Callable
from pathlib import Path

from cadence import activity

from ..quality_ratchet import compare_candidate_to_best
from .evaluate_candidate import EvaluateCandidateActivity, _run_evaluation_command


class CheckCandidateActivity:
    """Deterministic Check step: run the eval, inspect it, compare, persist.

    Reuses ``EvaluateCandidateActivity`` for the run/inspect/metrics mechanics
    (ADR-021 contract), then compares the result against the comparison
    baseline persisted in the progress record -- preferring the frozen
    ``iteration_start_baseline`` that ``edd_plan`` wrote at Plan time, then
    ``best_accepted_state.metrics``, then the original ``baseline_metrics``.
    Writes the per-iteration ``check.json`` artifact and a ``check.done.json``
    sentinel so downstream activities and humans can see what was checked and
    what was determined.
    """

    def __init__(
        self,
        store,
        harness: Callable[..., dict],
        now: Callable[[], str] | None = None,
    ) -> None:
        self.store = store
        self.harness = harness
        self.now = now

    def _resolve_baseline(self, record: dict) -> tuple[dict | None, str | None]:
        if record.get("iteration_start_baseline"):
            return record["iteration_start_baseline"], "iteration_start_baseline"
        best = record.get("best_accepted_state")
        if best and best.get("metrics"):
            return best["metrics"], "best_accepted_state"
        if record.get("baseline_metrics"):
            return record["baseline_metrics"], "baseline_metrics"
        return None, None

    def run(self, run_id: str, candidate_id: str, repo_root: str) -> dict:
        record = self.store.create_or_resume(run_id, {})
        logical_iteration = record.get("logical_iteration_count")
        iteration = (
            logical_iteration
            if logical_iteration is not None
            else len(record.get("candidate_metrics", [])) + 1
        )
        baseline, compared_against = self._resolve_baseline(record)

        metric = EvaluateCandidateActivity(
            self.store, self.harness, now=self.now
        ).run(run_id, candidate_id, repo_root, iteration=iteration)

        if metric["usable_for_acceptance"] and baseline is not None:
            comparison = compare_candidate_to_best(metric, baseline)
            determination = comparison["decision"]
        else:
            comparison = None
            compared_against = None
            determination = metric["status"]

        check_path = (
            Path(repo_root)
            / ".process"
            / "edd"
            / run_id
            / "iterations"
            / str(iteration)
            / "check.json"
        )
        check_path.parent.mkdir(parents=True, exist_ok=True)
        command_artifacts = [
            str(p.relative_to(repo_root))
            for p in sorted(check_path.parent.glob("*-command.json"))
            if p.is_file()
        ]
        check = {
            "run_id": run_id,
            "iteration": iteration,
            "candidate_id": candidate_id,
            "metrics": metric,
            "determination": determination,
            "comparison": comparison,
            "compared_against": compared_against,
            "baseline": baseline,
            "command_artifacts": command_artifacts,
        }
        check_path.write_text(json.dumps(check, indent=2, sort_keys=True))

        sentinel_path = Path(repo_root) / ".process" / "check.done.json"
        sentinel = {
            "task": "check_candidate",
            "run_id": run_id,
            "iteration": iteration,
            "determination": determination,
            "files": [str(check_path.relative_to(repo_root))] + command_artifacts,
        }
        sentinel_path.write_text(json.dumps(sentinel, indent=2, sort_keys=True))

        return {
            "run_id": run_id,
            "iteration": iteration,
            "candidate_id": candidate_id,
            "metrics": metric,
            "determination": determination,
            "comparison": comparison,
            "compared_against": compared_against,
            "baseline": baseline,
            "check_path": str(check_path.relative_to(repo_root)),
            "sentinel_path": str(sentinel_path.relative_to(repo_root)),
        }


@activity.defn(name="check_candidate")
async def check_candidate_activity(
    run_id: str, candidate_id: str, repo_root: str
) -> dict:
    from ..progress_record import ProgressRecordStore

    return CheckCandidateActivity(
        ProgressRecordStore(repo_root), _run_evaluation_command
    ).run(run_id, candidate_id, repo_root)
