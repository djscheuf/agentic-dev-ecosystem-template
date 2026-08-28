"""`Harness` implementation that runs a prompt via the `devin` CLI.

Same subprocess pattern as `evals/devin.js`. Configuration (which model to use,
and permission mode -- more permission-related settings may follow) is
file-based (`devin_harness.config.json` by default) rather than hardcoded, so it
can be changed per-environment without editing code.
"""

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .harness import HarnessResult

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent / "devin_harness.config.json"
DEFAULT_MODEL = "SWE-1.6"
DEFAULT_PERMISSION_MODE = "auto"


@dataclass(frozen=True)
class DevinHarnessConfig:
    model: str = DEFAULT_MODEL
    permission_mode: str = DEFAULT_PERMISSION_MODE

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
        result = self._runner(command, cwd=str(cwd), capture_output=True, text=True)
        return HarnessResult(exit_code=result.returncode, stdout=result.stdout, stderr=result.stderr)
