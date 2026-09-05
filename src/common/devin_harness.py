"""Harness implementation backed by the Devin CLI."""

import subprocess
import tempfile
import time
from contextlib import ExitStack
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping

from .atif_usage import read_atif_usage_result
from .harness import HarnessResult
from .invocation_context import get_current_skill_name
from .workflow_logger import (
    get_activity_artifact_dir,
    get_activity_logger,
    get_devin_logger,
    get_devin_log_path,
)

DEFAULT_MODEL = "SWE-1.7"
DEFAULT_PERMISSION_MODE = "auto"
SUPPORTED_PERMISSION_MODES = frozenset({"auto", "accept-edits", "dangerous", "bypass"})
_SUPPORTED_KEYS = frozenset({"model", "permission_mode"})


@dataclass(frozen=True)
class DevinHarnessConfig:
    model: str = DEFAULT_MODEL
    permission_mode: str = DEFAULT_PERMISSION_MODE

    @classmethod
    def from_mapping(cls, config: Mapping[str, object]) -> "DevinHarnessConfig":
        namespace = config.get("devin", {})
        if not isinstance(namespace, Mapping):
            raise ValueError("invalid_namespace_type: devin")
        unknown = set(namespace) - _SUPPORTED_KEYS
        if unknown:
            raise ValueError(f"unknown_key: devin.{sorted(unknown)[0]}")
        model = namespace.get("model", DEFAULT_MODEL)
        permission_mode = namespace.get("permission_mode", DEFAULT_PERMISSION_MODE)
        if not isinstance(model, str) or not model.strip():
            raise ValueError("invalid_value: devin.model")
        if not isinstance(permission_mode, str) or permission_mode not in SUPPORTED_PERMISSION_MODES:
            raise ValueError("invalid_value: devin.permission_mode")
        return cls(model=model, permission_mode=permission_mode)


class DevinHarness:
    def __init__(
        self,
        *,
        runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    ) -> None:
        self._runner = runner

    def run(
        self,
        prompt: str,
        *,
        cwd: Path,
        config: Mapping[str, object],
    ) -> HarnessResult:
        profile = DevinHarnessConfig.from_mapping(config)
        skill_name = get_current_skill_name() or ""
        with ExitStack() as stack:
            artifact_dir = get_activity_artifact_dir()
            storage_mode = "activity_artifact" if artifact_dir else "temporary"
            export_dir = artifact_dir or Path(stack.enter_context(tempfile.TemporaryDirectory()))
            export_path = export_dir / "devin-trajectory.json"
            activity_logger = get_activity_logger()
            devin_logger = get_devin_logger()
            activity_logger.info(
                "SelectDevinExportPath storage_mode=%s export_path=%s",
                storage_mode,
                export_path,
            )
            devin_logger.info(
                "SelectDevinExportPath storage_mode=%s export_path=%s",
                storage_mode,
                export_path,
            )
            command = [
                "devin", "-p", "--export", str(export_path),
                "--permission-mode", profile.permission_mode,
                "--model", profile.model, "--", prompt,
            ]
            activity_logger.info(
                "StartDevinInvocation skill_name=%s model=%s permission_mode=%s",
                skill_name,
                profile.model,
                profile.permission_mode,
            )
            start = time.monotonic()
            try:
                result = self._runner(command, cwd=str(cwd), capture_output=True, text=True)
            except OSError as exc:
                activity_logger.error(
                    "FailDevinInvocationLaunch skill_name=%s error_category=devin_launch_failed",
                    skill_name,
                )
                devin_logger.error(
                    "FailDevinInvocationLaunch skill_name=%s error_category=devin_launch_failed",
                    skill_name,
                )
                raise RuntimeError("devin_launch_failed") from exc
            duration_ms = int((time.monotonic() - start) * 1000)
            usage, error_category = read_atif_usage_result(export_path)
            if error_category:
                activity_logger.warning(
                    "RejectAtifTelemetry storage_mode=%s error_category=%s",
                    storage_mode,
                    error_category,
                )
                devin_logger.warning(
                    "RejectAtifTelemetry storage_mode=%s error_category=%s",
                    storage_mode,
                    error_category,
                )
            activity_logger.info(
                "CompleteDevinInvocation skill_name=%s exit_code=%s duration_ms=%s usage_available=%s devin_log_path=%s",
                skill_name,
                result.returncode,
                duration_ms,
                usage is not None,
                get_devin_log_path() or "unknown",
            )
            devin_logger.info(
                "CompleteDevinInvocation skill_name=%s exit_code=%s duration_ms=%s usage_available=%s",
                skill_name,
                result.returncode,
                duration_ms,
                usage is not None,
            )
            if result.stdout:
                devin_logger.debug("--- stdout ---")
                for line in result.stdout.splitlines():
                    devin_logger.debug("%s", line)
            if result.stderr:
                devin_logger.debug("--- stderr ---")
                for line in result.stderr.splitlines():
                    devin_logger.debug("%s", line)
        return HarnessResult(result.returncode, result.stdout, result.stderr, usage)
