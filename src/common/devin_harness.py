"""Harness implementation backed by the Devin CLI."""

import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping

from .atif_usage import read_atif_usage
from .harness import HarnessResult

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
        with tempfile.TemporaryDirectory() as temporary_dir:
            export_path = Path(temporary_dir) / "devin-trajectory.json"
            command = [
                "devin", "-p", "--export", str(export_path),
                "--permission-mode", profile.permission_mode,
                "--model", profile.model, "--", prompt,
            ]
            try:
                result = self._runner(command, cwd=str(cwd), capture_output=True, text=True)
            except OSError as exc:
                raise RuntimeError("devin_launch_failed") from exc
            usage = read_atif_usage(export_path)
        return HarnessResult(result.returncode, result.stdout, result.stderr, usage)
