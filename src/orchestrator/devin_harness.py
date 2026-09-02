"""`Harness` implementation that runs a prompt via the `devin` CLI.

Same subprocess pattern as `evals/devin.js`. Configuration (which model to use,
and permission mode -- more permission-related settings may follow) is
file-based (`devin_harness.config.json` by default) rather than hardcoded, so it
can be changed per-environment without editing code.
"""

import json
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .harness import HarnessResult
from .workflow_logger import get_activity_logger, get_devin_log_path, get_devin_logger

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent / "devin_harness.config.json"
DEFAULT_MODEL = "SWE-1.7"
DEFAULT_PERMISSION_MODE = "auto"


@dataclass(frozen=True)
class EffectiveDevinProfile:
    model: str
    permission_mode: str


@dataclass(frozen=True)
class DevinHarnessConfig:
    model: str = DEFAULT_MODEL
    permission_mode: str = DEFAULT_PERMISSION_MODE

    def resolve(self, skill_name: str) -> EffectiveDevinProfile:
        return EffectiveDevinProfile(
            model=self.model,
            permission_mode=self.permission_mode,
        )

    @classmethod
    def load(cls, config_path: Path = DEFAULT_CONFIG_PATH) -> "DevinHarnessConfig":
        """Load config from `config_path`, falling back to defaults for any
        missing file or missing/unrecognized keys."""
        if not config_path.exists():
            return cls()
        data = json.loads(config_path.read_text())
        return cls(
            model=data.get("model", DEFAULT_MODEL),
            permission_mode=data.get("permission_mode", DEFAULT_PERMISSION_MODE),
        )


class DevinHarness:
    """`Harness` that shells out to the `devin` CLI."""

    def __init__(
        self,
        config: "DevinHarnessConfig | None" = None,
        *,
        runner: Callable[..., "subprocess.CompletedProcess[str]"] = subprocess.run,
    ) -> None:
        self.config = config or DevinHarnessConfig.load()
        self._runner = runner

    def run(self, prompt: str, *, cwd: Path) -> HarnessResult:
        command = [
            "devin",
            "-p",
            "--permission-mode",
            self.config.permission_mode,
            "--model",
            self.config.model,
            "--",
            prompt,
        ]
        activity_logger = get_activity_logger()
        devin_logger = get_devin_logger()
        activity_logger.debug("Running devin command: %s", command)

        start = time.monotonic()
        result = self._runner(command, cwd=str(cwd), capture_output=True, text=True)
        duration_ms = int((time.monotonic() - start) * 1000)

        activity_logger.debug(
            "devin exited with code %s in %s ms", result.returncode, duration_ms
        )
        if result.stdout:
            devin_logger.debug("--- stdout ---")
            for line in result.stdout.splitlines():
                devin_logger.debug("%s", line)
        if result.stderr:
            devin_logger.debug("--- stderr ---")
            for line in result.stderr.splitlines():
                devin_logger.debug("%s", line)
        activity_logger.debug("Devin output log: %s", get_devin_log_path() or "unknown")

        return HarnessResult(
            exit_code=result.returncode, stdout=result.stdout, stderr=result.stderr
        )
