"""Generic class-based skill Activity lifecycle."""

import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

from .harness import Harness, HarnessResult
from .invocation_context import skill_invocation_context
from .skill_activity_config import SkillActivityConfig
from .workflow_logger import get_activity_logger


class SkillActivityError(RuntimeError):
    pass


@dataclass(frozen=True)
class SkillActivityInput:
    input_paths: list[str] = field(default_factory=list)
    context: str = ""


@dataclass(frozen=True)
class SkillActivityOutput:
    status: str
    output_path: str
    sentinel_path: str
    duration_ms: int


class SkillActivity(ABC):
    def __init__(
        self, *, config_path: Path, harness: Harness, repo_root: Path
    ) -> None:
        config = SkillActivityConfig.load(config_path)
        self.skill_name = config.skill_name
        self.output_path_key = config.output_path_key
        self.harness_config = config.harness
        self.harness = harness
        self.repo_root = repo_root

    @abstractmethod
    def expected_output_path(self, skill_input: SkillActivityInput) -> Path:
        """Resolve an output when the successful harness consumed its sentinel."""

    def build_prompt(self, skill_input: SkillActivityInput) -> str:
        lines = [f"Invoke the '{self.skill_name}' skill."]
        if skill_input.input_paths:
            lines.append("Input document path(s): " + ", ".join(skill_input.input_paths))
        if skill_input.context:
            lines.append(skill_input.context)
        return "\n".join(lines)

    def execute(self, skill_input: SkillActivityInput) -> SkillActivityOutput:
        sentinel = self.repo_root / ".process" / f"{self.skill_name}.done.json"
        if sentinel.exists():
            sentinel.unlink()
        start = time.monotonic()
        with skill_invocation_context(self.skill_name):
            result = self.harness.run(
                self.build_prompt(skill_input),
                cwd=self.repo_root,
                config=self.harness_config,
            )
        duration_ms = int((time.monotonic() - start) * 1000)
        if not isinstance(result, HarnessResult) and not all(
            hasattr(result, field) for field in ("exit_code", "stdout", "stderr")
        ):
            raise SkillActivityError("invalid_harness_result")
        if result.exit_code:
            raise SkillActivityError(
                f"Harness exited {result.exit_code} while running skill '{self.skill_name}'"
            )
        try:
            payload = json.loads(sentinel.read_text())
        except FileNotFoundError:
            output_path = self.expected_output_path(skill_input)
            get_activity_logger().warning(
                "WarnSkillArtifactVerification: skill_name=%s failure_reason=missing_sentinel output_path=%s",
                self.skill_name,
                output_path,
            )
        except json.JSONDecodeError as exc:
            raise SkillActivityError(f"Malformed sentinel for skill '{self.skill_name}'") from exc
        else:
            if payload.get("task") != self.skill_name:
                raise SkillActivityError(f"Sentinel task mismatch for skill '{self.skill_name}'")
            value = payload.get("verify_params", {}).get(self.output_path_key)
            if not value:
                raise SkillActivityError(
                    f"Sentinel for skill '{self.skill_name}' is missing verify_params.{self.output_path_key}"
                )
            output_path = Path(value)
        return SkillActivityOutput(
            status="success",
            output_path=str(output_path),
            sentinel_path=str(sentinel.relative_to(self.repo_root)),
            duration_ms=duration_ms,
        )
