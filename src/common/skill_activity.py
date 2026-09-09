"""Generic class-based skill Activity lifecycle."""

import json
import time
from abc import ABC, abstractmethod
from contextlib import AbstractContextManager
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Mapping

from .harness import Harness, HarnessResult
from .invocation_context import skill_invocation_context
from .skill_activity_config import SkillActivityConfig
from .workflow_logger import (
    _resolve_activity_info,
    activity_log_context,
    get_activity_artifact_dir,
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
    ambiguity_reason: str = ""
    observation: dict = field(default_factory=dict)


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
        sentinel_parent = (
            self.repo_root / Path(skill_input.input_paths[0]).parent
            if skill_input.input_paths
            else self.repo_root
        )
        sentinel = self.modify_sentinel_path(
            sentinel_parent / ".process" / f"{self.skill_name}.done.json"
        )
        if sentinel.exists():
            sentinel.unlink()
        with activity_log_context():
            logger = get_activity_logger()
            logger.info("RunSkill: skill_name=%s", self.skill_name)
            started_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
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
            status = "success"
            ambiguity_reason = ""
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
                status = payload.get("status", "success")
                ambiguity_reason = payload.get("ambiguity_reason", "")
                if status == "ambiguity":
                    output_path = Path("")
                else:
                    value = payload.get("verify_params", {}).get(self.output_path_key)
                    if not value:
                        raise SkillActivityError(
                            f"Sentinel for skill '{self.skill_name}' is missing verify_params.{self.output_path_key}"
                        )
                    output_path = Path(value)
            resolved_output_path = (
                "" if status == "ambiguity" else str(self.modify_output_path(output_path))
            )
            activity_log_path = get_activity_log_path() or ""
            devin_log_path = get_devin_log_path() or ""
            info = _resolve_activity_info()
            harness_namespace = self.harness_config.get("devin", {})
            usage = getattr(result, "usage", None)
            artifact_dir = get_activity_artifact_dir()
            observation = {
                "workflow_id": getattr(info, "workflow_id", ""),
                "run_id": getattr(info, "workflow_run_id", ""),
                "sequence": 0,
                "step_name": self.skill_name,
                "activity_type": getattr(info, "activity_type", self.skill_name),
                "activity_id": getattr(info, "activity_id", ""),
                "attempt": getattr(info, "attempt", 0),
                "started_at": started_at,
                "duration_ms": duration_ms,
                "outcome": "success",
                "model": harness_namespace.get("model", "SWE-1.7"),
                "permission_mode": harness_namespace.get("permission_mode", "auto"),
                "output_path": resolved_output_path,
                "activity_log_path": activity_log_path,
                "devin_log_path": devin_log_path,
                "atif_path": str(artifact_dir / "devin-trajectory.json")
                if usage is not None and artifact_dir is not None
                else None,
                "usage": asdict(usage) if usage is not None else None,
            }
            output = SkillActivityOutput(
                status=status,
                output_path=resolved_output_path,
                sentinel_path=str(sentinel.relative_to(self.repo_root)),
                duration_ms=duration_ms,
                activity_log_path=activity_log_path,
                devin_log_path=devin_log_path,
                ambiguity_reason=ambiguity_reason,
                observation=observation,
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
    sentinel_parent = (
        repo_root / Path(skill_input.input_paths[0]).parent
        if skill_input.input_paths
        else repo_root
    )
    sentinel = sentinel_parent / ".process" / f"{skill_input.skill_name}.done.json"
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
