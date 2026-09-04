"""Protocol for pluggable skill execution backends."""

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Protocol


@dataclass(frozen=True)
class HarnessResult:
    exit_code: int
    stdout: str
    stderr: str


class Harness(Protocol):
    def run(
        self,
        prompt: str,
        *,
        cwd: Path,
        config: Mapping[str, object],
    ) -> HarnessResult:
        """Execute a prompt rooted at ``cwd`` using namespaced configuration."""
        ...
