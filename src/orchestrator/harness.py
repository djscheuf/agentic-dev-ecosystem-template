"""Harness abstraction: the pluggable backend that actually executes a skill prompt.

`skill_activity.run_skill()` is only responsible for connecting a skill and its
inputs to a prompt; it delegates *running* that prompt to whichever `Harness`
is injected. `DevinHarness` (`devin_harness.py`) is the default implementation,
shelling out to the `devin` CLI, but any object implementing this Protocol
(e.g. a fake in tests, or a different agent CLI/runtime) can be substituted.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class HarnessResult:
    exit_code: int
    stdout: str
    stderr: str


class Harness(Protocol):
    def run(self, prompt: str, *, cwd: Path) -> HarnessResult:
        """Execute `prompt` with the harness's agent, rooted at `cwd`.

        Implementations are expected to let the agent act on the repository at
        `cwd` (e.g. writing files) and to return the process's exit code and
        captured output; they do not interpret the skill's output themselves.
        """
        ...
