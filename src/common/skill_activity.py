"""Generic class-based skill Activity lifecycle."""

import json
import time
from abc import ABC, abstractmethod
from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Mapping

from .harness import Harness, HarnessResult
from .invocation_context import skill_invocation_context
from .skill_activity_config import SkillActivityConfig
from .workflow_logger import (
    activity_log_context,
    get_activity_log_path,
    get_activity_logger,
    get_devin_log_path,
)


class SkillActivityError(RuntimeError):
    pass


@dataclass(frozen=True)
class SkillActivityInput:
    skill_name: str = ""
    input_paths: list[str] = field(default_factory=list)
    context: str = ""


@dataclass(frozen=True)
class SkillActivityOutput:
    status: str
    output_path: str
    sentinel_path: str
    duration_ms: int
    activity_log_path: str = ""
    devin_log_path: str = ""


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

    def modify_prompt(self, prompt: str) -> str:
        return prompt

    def modify_sentinel_path(self, sentinel_path: Path) -> Path:
        return sentinel_path

    def modify_harness_config(
        self, config: Mapping[str, object]
    ) -> Mapping[str, object]:
        return config

    def modify_invocation_context(
        self, context: AbstractContextManager[None]
    ) -> AbstractContextManager[None]:
        return context

    def modify_output_path(self, output_path: Path) -> Path:
        return output_path

    def modify_result(self, result: SkillActivityOutput) -> SkillActivityOutput:
        return result

    def build_prompt(self, skill_input: SkillActivityInput) -> str:
        lines = [f"Invoke the '{self.skill_name}' skill."]
        if skill_input.input_paths:
            lines.append("Input document path(s): " + ", ".join(skill_input.input_paths))
            lines.append(
                f"Write the skill's output file in the same directory as the first "
                f"input path ({skill_input.input_paths[0]}), following the skill's "
                f"naming convention."
            )
        if skill_input.context:
            lines.append(skill_input.context)
        return self.modify_prompt("\n".join(lines))

    def execute(self, skill_input: SkillActivityInput) -> SkillActivityOutput:
        sentinel = self.modify_sentinel_path(
            self.repo_root / ".process" / f"{self.skill_name}.done.json"
        )
        if sentinel.exists():
            sentinel.unlink()
        with activity_log_context():
            logger = get_activity_logger()
            logger.info("RunSkill: skill_name=%s", self.skill_name)
            start = time.monotonic()
            with self.modify_invocation_context(
                skill_invocation_context(self.skill_name)
            ):
                result = self.harness.run(
                    self.build_prompt(skill_input),
                    cwd=self.repo_root,
                    config=self.modify_harness_config(self.harness_config),
                )
            duration_ms = int((time.monotonic() - start) * 1000)
            if not isinstance(result, HarnessResult) and not all(
                hasattr(result, field) for field in ("exit_code", "stdout", "stderr")
            ):
                raise SkillActivityError("invalid_harness_result")
            if result.exit_code:
                logger.error(
                    "FailSkillHarnessInvocation: skill_name=%s exit_code=%s",
                    self.skill_name,
                    result.exit_code,
                )
                raise SkillActivityError(
                    f"Harness exited {result.exit_code} while running skill '{self.skill_name}'"
                )
            try:
                payload = json.loads(sentinel.read_text())
            except FileNotFoundError:
                output_path = self.expected_output_path(skill_input)
                logger.warning(
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
            output = SkillActivityOutput(
                status="success",
                output_path=str(self.modify_output_path(output_path)),
                sentinel_path=str(sentinel.relative_to(self.repo_root)),
                duration_ms=duration_ms,
                activity_log_path=get_activity_log_path() or "",
                devin_log_path=get_devin_log_path() or "",
            )
        return self.modify_result(output)


def run_skill(
    skill_input: SkillActivityInput,
    *,
    output_path_key: str,
    harness: Harness,
    repo_root: Path,
    expected_output_path: Callable[[SkillActivityInput], Path] | None = None,
) -> SkillActivityOutput:
    sentinel = repo_root / ".process" / f"{skill_input.skill_name}.done.json"
    if sentinel.exists():
        sentinel.unlink()
    lines = [f"Invoke the '{skill_input.skill_name}' skill."]
    if skill_input.input_paths:
        lines.append("Input document path(s): " + ", ".join(skill_input.input_paths))
    if skill_input.context:
        lines.append(skill_input.context)
    start = time.monotonic()
    with skill_invocation_context(skill_input.skill_name):
        result = harness.run("\n".join(lines), cwd=repo_root)
    if result.exit_code:
        raise SkillActivityError(
            f"Harness exited {result.exit_code} while running skill '{skill_input.skill_name}'"
        )
    try:
        payload = json.loads(sentinel.read_text())
    except FileNotFoundError:
        if expected_output_path is None:
            raise SkillActivityError(
                f"Missing sentinel for skill '{skill_input.skill_name}'"
            )
        output_path = expected_output_path(skill_input)
    else:
        if payload.get("task") != skill_input.skill_name:
            raise SkillActivityError(
                f"Sentinel task mismatch for skill '{skill_input.skill_name}'"
            )
        value = payload.get("verify_params", {}).get(output_path_key)
        if not value:
            raise SkillActivityError(
                f"Sentinel for skill '{skill_input.skill_name}' is missing verify_params.{output_path_key}"
            )
        output_path = Path(value)
    return SkillActivityOutput(
        status="success",
        output_path=str(output_path),
        sentinel_path=str(sentinel.relative_to(repo_root)),
        duration_ms=int((time.monotonic() - start) * 1000),
    )
