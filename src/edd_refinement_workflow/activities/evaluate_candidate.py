import json
import logging
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

_PLACEHOLDER = "{evaluation_id}"


def _get_activity_logger() -> logging.Logger:
    try:
        from common.workflow_logger import get_activity_logger

        return get_activity_logger()
    except Exception:  # pragma: no cover
        return logging.getLogger(__name__)


def _summarize_eval_results(results: list) -> dict:
    """Derive pass/fail metrics from a promptfoo result list."""
    passing = sum(1 for r in results if r.get("success") is True)
    failing = len(results) - passing
    total = len(results)
    percentage = (passing / total * 100) if total > 0 else 0.0
    return {
        "passing": passing,
        "failing": failing,
        "total": total,
        "percentage": percentage,
    }


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
        self,
        command: list[str],
        inspect_command: list[str],
        repo_root: str,
        timeout: int,
        provider: str,
        configuration_path: str,
        artifact_dir: Path | None,
    ) -> dict:
        test_result = self.harness(
            command=command,
            configuration=configuration_path,
            provider=provider,
            cwd=repo_root,
            timeout=timeout,
            artifact_dir=artifact_dir,
            command_label="run",
        )
        evaluation_id = extract_evaluation_id(test_result)
        inspect_argv = build_inspect_command(inspect_command, evaluation_id)
        return self.harness(
            command=inspect_argv,
            configuration=configuration_path,
            provider=provider,
            cwd=repo_root,
            timeout=timeout,
            artifact_dir=artifact_dir,
            command_label="inspect",
        )

    def run(
        self,
        run_id: str,
        candidate_id: str,
        repo_root: str,
        iteration: int | None = None,
    ) -> dict:
        record = self.store.create_or_resume(run_id, {})
        configuration = record["evaluation_configuration"]
        test_cases = record.get("test_cases") or configuration.get("test_cases")
        coverage_property = record.get("coverage_metadata_property") or configuration.get("coverage_metadata_property")
        inspect_command = record.get("inspect_command") or configuration.get("inspect_command")

        if iteration is None:
            logical_iteration = record.get("logical_iteration_count")
            if logical_iteration is not None:
                iteration = logical_iteration
            else:
                iteration = len(record.get("candidate_metrics", [])) + 1
        artifact_dir = (
            Path(repo_root)
            / ".process"
            / "edd"
            / run_id
            / "iterations"
            / str(iteration)
        )
        artifact_dir.mkdir(parents=True, exist_ok=True)

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
                    artifact_dir,
                )
            else:
                inspect_result = self.harness(
                    command=configuration["command"],
                    configuration=configuration["configuration"],
                    provider=configuration["pinned_provider_version"],
                    cwd=repo_root,
                    timeout=configuration["timeout_seconds"],
                    artifact_dir=artifact_dir,
                    command_label="run",
                )
            if isinstance(inspect_result, list):
                inspect_result = _summarize_eval_results(inspect_result)
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


def _write_command_artifact(
    artifact_dir: Path,
    command_label: str,
    command: list[str],
    cwd: str,
    timeout: int,
    provider: str,
    configuration: str,
    completed: subprocess.CompletedProcess | None,
    parsed_stdout,
    exc: BaseException | None,
) -> None:
    """Persist raw command invocation details for later debugging."""
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact = {
        "command_label": command_label,
        "command": command,
        "cwd": cwd,
        "timeout": timeout,
        "provider": provider,
        "configuration": configuration,
        "timestamp": datetime.now(UTC).isoformat(),
        "timed_out": isinstance(exc, TimeoutError),
        "returncode": completed.returncode if completed is not None else None,
        "stdout": completed.stdout if completed is not None else None,
        "stderr": completed.stderr if completed is not None else None,
        "parsed_stdout": parsed_stdout,
    }
    artifact_path = artifact_dir / f"{command_label}-command.json"
    artifact_path.write_text(json.dumps(artifact, indent=2, default=str))


def _run_evaluation_command(**kwargs) -> dict:
    logger = _get_activity_logger()
    command = kwargs["command"]
    cwd = kwargs["cwd"]
    timeout = kwargs["timeout"]
    provider = kwargs.get("provider", "")
    configuration = kwargs.get("configuration", "")
    artifact_dir = kwargs.get("artifact_dir")
    command_label = kwargs.get("command_label")
    logger.info(
        "running evaluation command: %s (cwd=%s, timeout=%s)",
        " ".join(str(c) for c in command),
        cwd,
        timeout,
    )
    completed = None
    parsed_stdout = None
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        logger.warning("evaluation command timed out: %s", command)
        if artifact_dir is not None and command_label is not None:
            _write_command_artifact(
                Path(artifact_dir),
                command_label,
                command,
                cwd,
                timeout,
                provider,
                configuration,
                completed,
                parsed_stdout,
                TimeoutError(),
            )
        raise TimeoutError from exc

    logger.info(
        "evaluation command finished: returncode=%s stdout_len=%s stderr_len=%s",
        completed.returncode,
        len(completed.stdout),
        len(completed.stderr),
    )
    if completed.returncode != 0:
        preview = completed.stderr[:500] if completed.stderr else completed.stdout[:500]
        logger.warning("evaluation command stderr preview: %s", preview)

    stdout = completed.stdout.strip()
    if stdout:
        try:
            parsed_stdout = json.loads(stdout)
            logger.info("evaluation command produced JSON stdout")
        except json.JSONDecodeError:
            logger.info("evaluation command stdout is not JSON")

    if artifact_dir is not None and command_label is not None:
        _write_command_artifact(
            Path(artifact_dir),
            command_label,
            command,
            cwd,
            timeout,
            provider,
            configuration,
            completed,
            parsed_stdout,
            None,
        )

    return parsed_stdout if parsed_stdout is not None else {}


@activity.defn(name="evaluate_candidate")
async def evaluate_candidate_activity(
    run_id: str, candidate_id: str, repo_root: str, iteration: int | None = None
) -> dict:
    from ..progress_record import ProgressRecordStore

    return EvaluateCandidateActivity(
        ProgressRecordStore(repo_root), _run_evaluation_command
    ).run(run_id, candidate_id, repo_root, iteration=iteration)
