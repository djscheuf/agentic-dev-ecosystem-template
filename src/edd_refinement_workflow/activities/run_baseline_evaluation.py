import json
import subprocess
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from cadence import activity

from ..candidate_results import CandidateMetricRecord
from ..coverage import CoverageCalculator, CoverageError
from ..evaluation_identity import (
    EvaluationIdentityError,
    build_inspect_command,
    extract_evaluation_id,
)


class RunBaselineEvaluationActivity:
    def __init__(
        self,
        store,
        harness: Callable[..., dict],
        now: Callable[[], str] | None = None,
    ) -> None:
        self.store = store
        self.harness = harness
        self.now = now or (lambda: datetime.now(UTC).isoformat())

    def _compute_coverage(
        self, result: dict, test_cases: str | None, coverage_property: str | None
    ) -> tuple[dict, bool, str | None]:
        if not test_cases or not coverage_property:
            return result.get("required_coverage", {}), True, None
        try:
            coverage = CoverageCalculator(Path(test_cases)).calculate(
                result, coverage_property
            )
        except CoverageError as exc:
            return {}, False, f"coverage_calculation_error:{exc}"
        if not coverage["valid"]:
            return coverage["required_coverage"], False, "unknown_test_case_ids"
        return coverage["required_coverage"], True, None

    def _run_identity_chain(self, profile: dict, repo_root: str) -> dict:
        test_result = self.harness(
            command=profile["command"],
            cwd=repo_root,
            timeout=profile["timeout"],
        )
        evaluation_id = extract_evaluation_id(test_result)
        inspect_command = build_inspect_command(
            profile["inspect_command"], evaluation_id
        )
        return self.harness(
            command=inspect_command,
            cwd=repo_root,
            timeout=profile["timeout"],
        )

    def run(self, run_id: str, profile: dict, repo_root: str) -> dict:
        record = self.store.create_or_resume(run_id, {})
        configuration = record.get("evaluation_configuration", {})
        provider = profile.get("provider") or configuration.get(
            "pinned_provider_version", "default"
        )
        measurement_context = configuration.get("measurement_context", "baseline")
        test_cases = profile.get("test_cases") or record.get("test_cases")
        coverage_property = profile.get(
            "coverage_metadata_property"
        ) or record.get("coverage_metadata_property")

        try:
            inspect_result = self._run_identity_chain(profile, repo_root)
        except (EvaluationIdentityError, TimeoutError) as exc:
            inspect_result = {}
            timed_out = isinstance(exc, TimeoutError)
            identity_error = None if timed_out else str(exc)
        except RuntimeError as exc:
            inspect_result = {}
            timed_out = False
            identity_error = str(exc)
        else:
            timed_out = False
            identity_error = None

        required_fields = {"passing", "failing", "total", "percentage"}
        has_metric_fields = required_fields <= inspect_result.keys()
        required_coverage, coverage_valid, coverage_failure = self._compute_coverage(
            inspect_result, test_cases, coverage_property
        )
        artifact_references = inspect_result.get("artifact_references", [])

        if timed_out:
            status = "timeout"
            failure_reason = "evaluation_timeout"
        elif identity_error is not None:
            status = "infra_error"
            failure_reason = identity_error
        elif not has_metric_fields:
            status = "rejected"
            failure_reason = "malformed_metrics"
        elif not coverage_valid:
            status = "rejected"
            failure_reason = coverage_failure
        else:
            status = "success"
            failure_reason = None

        valid = (
            has_metric_fields
            and coverage_valid
            and not timed_out
            and identity_error is None
        )
        metric = CandidateMetricRecord(
            candidate_id="baseline",
            run_id=run_id,
            attempt_number=1,
            passing=inspect_result.get("passing", 0),
            failing=inspect_result.get("failing", 0),
            total=inspect_result.get("total", 0),
            percentage=inspect_result.get("percentage", 0.0),
            required_coverage=required_coverage,
            artifact_references=artifact_references,
            pinned_provider_version=provider,
            measurement_context=measurement_context,
            evaluated_at=self.now(),
            status=status,
            failure_reason=failure_reason,
            usable_for_acceptance=valid,
        ).to_dict()

        attempt = {
            "command": profile["command"],
            "inspect_command": profile["inspect_command"],
            "provider": provider,
            "timeout": profile["timeout"],
            "result": metric,
        }
        record["attempts"] = record.get("attempts", []) + [attempt]
        record["baseline_metrics"] = metric
        self.store.save(run_id, record)
        return metric


def _run_evaluation_command(**kwargs) -> dict:
    completed = subprocess.run(
        kwargs["command"],
        cwd=kwargs["cwd"],
        capture_output=True,
        text=True,
        timeout=kwargs["timeout"],
        check=True,
    )
    return json.loads(completed.stdout)


@activity.defn(name="run_baseline_evaluation")
async def run_baseline_evaluation_activity(
    run_id: str, profile: dict, repo_root: str
) -> dict:
    from ..progress_record import ProgressRecordStore

    return RunBaselineEvaluationActivity(
        ProgressRecordStore(repo_root), _run_evaluation_command
    ).run(run_id, profile, repo_root)
