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


class EvaluateCandidateActivity:
    def __init__(self, store, harness: Callable[..., dict], now: Callable[[], str] | None = None) -> None:
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

    def _run_identity_chain(
        self, command: list[str], inspect_command: list[str], repo_root: str, timeout: int, provider: str, configuration_path: str
    ) -> dict:
        test_result = self.harness(
            command=command,
            configuration=configuration_path,
            provider=provider,
            cwd=repo_root,
            timeout=timeout,
        )
        evaluation_id = extract_evaluation_id(test_result)
        inspect_argv = build_inspect_command(inspect_command, evaluation_id)
        return self.harness(
            command=inspect_argv,
            configuration=configuration_path,
            provider=provider,
            cwd=repo_root,
            timeout=timeout,
        )

    def run(self, run_id: str, candidate_id: str, repo_root: str) -> dict:
        record = self.store.create_or_resume(run_id, {})
        configuration = record["evaluation_configuration"]
        test_cases = record.get("test_cases") or configuration.get("test_cases")
        coverage_property = record.get("coverage_metadata_property") or configuration.get("coverage_metadata_property")
        inspect_command = record.get("inspect_command") or configuration.get("inspect_command")
        infrastructure_error = None
        timed_out = False
        try:
            if inspect_command:
                inspect_result = self._run_identity_chain(
                    configuration["command"],
                    inspect_command,
                    repo_root,
                    configuration["timeout_seconds"],
                    configuration["pinned_provider_version"],
                    configuration["configuration"],
                )
            else:
                inspect_result = self.harness(
                    command=configuration["command"],
                    configuration=configuration["configuration"],
                    provider=configuration["pinned_provider_version"],
                    cwd=repo_root,
                    timeout=configuration["timeout_seconds"],
                )
        except EvaluationIdentityError as exc:
            inspect_result = {}
            infrastructure_error = str(exc)
            timed_out = False
        except TimeoutError:
            inspect_result = {}
            timed_out = True
        except RuntimeError as exc:
            inspect_result = {}
            infrastructure_error = str(exc)

        required_fields = {"passing", "failing", "total", "percentage"}
        has_metric_fields = required_fields <= inspect_result.keys()
        required_coverage, coverage_valid, coverage_failure = self._compute_coverage(
            inspect_result, test_cases, coverage_property
        )
        artifact_references = inspect_result.get("artifact_references", [])

        if timed_out:
            status = "timeout"
            failure_reason = "evaluation_timeout"
        elif infrastructure_error is not None:
            status = "infra_error"
            failure_reason = infrastructure_error
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
            and infrastructure_error is None
        )
        metric = CandidateMetricRecord(
            candidate_id=candidate_id,
            run_id=run_id,
            attempt_number=len(record.get("candidate_metrics", [])) + 1,
            passing=inspect_result.get("passing", 0),
            failing=inspect_result.get("failing", 0),
            total=inspect_result.get("total", 0),
            percentage=inspect_result.get("percentage", 0.0),
            required_coverage=required_coverage,
            artifact_references=artifact_references,
            pinned_provider_version=configuration["pinned_provider_version"],
            measurement_context=configuration["measurement_context"],
            evaluated_at=self.now(),
            status=status,
            failure_reason=failure_reason,
            usable_for_acceptance=valid,
        ).to_dict()
        for field in ("usage_metrics", "is_retry", "logical_iteration_number"):
            if field in inspect_result:
                metric[field] = inspect_result[field]
        record["candidate_metrics"] = record.get("candidate_metrics", []) + [metric]
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


@activity.defn(name="evaluate_candidate")
async def evaluate_candidate_activity(run_id: str, candidate_id: str, repo_root: str) -> dict:
    from ..progress_record import ProgressRecordStore

    return EvaluateCandidateActivity(
        ProgressRecordStore(repo_root), _run_evaluation_command
    ).run(run_id, candidate_id, repo_root)
