"""Compatibility API for the common Activity-side skill wrapper.

This module contains workflow-agnostic infrastructure. It builds a configured
skill prompt, delegates execution to a `Harness`, and resolves the configured
sentinel output. `repo_root` remains injectable for isolated unit tests.
"""

import json
import time
from abc import ABC, abstractmethod
from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

from .harness import Harness, HarnessResult
from .invocation_context import skill_invocation_context
from .skill_activity_config import SkillActivityConfig
from .workflow_logger import (
    activity_log_context,
    get_activity_log_path,
    get_activity_logger,
    get_devin_log_path,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


class SkillActivityError(RuntimeError):
    """Raised when the harness fails or produces an invalid sentinel."""


@dataclass(frozen=True)
class SkillActivityInput:
    skill_name: str
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


def _sentinel_path(repo_root: Path, skill_name: str) -> Path:
    return repo_root / ".process" / f"{skill_name}.done.json"


def _conventional_output_path(skill_input: SkillActivityInput) -> str:
    if not skill_input.input_paths:
        raise SkillActivityError(
            f"Cannot derive output path for skill '{skill_input.skill_name}' without an input path"
        )

    input_path = Path(skill_input.input_paths[0])
    name = input_path.name
    if len(skill_input.input_paths) > 1:
        output_name = name
    elif name.endswith(".intent.json"):
        output_name = f"{name[:-len('.intent.json')]}.analysis.json"
    elif name.endswith(".analysis.json"):
        output_name = f"{name[:-len('.analysis.json')]}.analysis-grade.json"
    else:
        output_name = f"{input_path.stem}.intent.json"
    return str(input_path.with_name(output_name))


def _build_prompt(skill_input: SkillActivityInput) -> str:
    lines = [f"Invoke the '{skill_input.skill_name}' skill."]
    if skill_input.input_paths:
        lines.append("Input document path(s): " + ", ".join(skill_input.input_paths))
        lines.append(
            f"Write the skill's output file in the same directory as the first "
            f"input path ({skill_input.input_paths[0]}), following the skill's "
            f"naming convention."
        )
    if skill_input.context:
        lines.append(skill_input.context)
    return "\n".join(lines)


class SkillActivity(ABC):
    def __init__(
        self,
        *,
        config_path: Path,
        harness: Harness,
        repo_root: Path = REPO_ROOT,
    ) -> None:
        config = SkillActivityConfig.load(config_path)
        self.skill_name = config.skill_name
        self.output_path_key = config.output_path_key
        self.harness_config = config.harness
        self.harness = harness
        self.repo_root = repo_root

    @abstractmethod
    def expected_output_path(self, skill_input: SkillActivityInput) -> Path:
        raise NotImplementedError

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

    def _hook(self, name: str, value: object, expected: type) -> object:
        result = getattr(self, name)(value)
        valid = isinstance(result, expected)
        if expected is AbstractContextManager:
            valid = hasattr(result, "__enter__") and hasattr(result, "__exit__")
        if not valid:
            get_activity_logger().error(
                "RejectHookResult: skill_name=%s hook_name=%s "
                "error_category=invalid_hook_return_type",
                self.skill_name,
                name,
            )
            raise SkillActivityError(f"invalid_hook_return_type: {name}")
        return result

    def execute(self, skill_input: SkillActivityInput) -> SkillActivityOutput:
        sentinel_file = self._hook(
            "modify_sentinel_path",
            _sentinel_path(self.repo_root, self.skill_name),
            Path,
        )
        if sentinel_file.exists():
            sentinel_file.unlink()
        prompt = self._hook(
            "modify_prompt",
            _build_prompt(
                SkillActivityInput(
                    skill_name=self.skill_name,
                    input_paths=skill_input.input_paths,
                    context=skill_input.context,
                )
            ),
            str,
        )
        config = self._hook(
            "modify_harness_config", self.harness_config, Mapping
        )
        context = self._hook(
            "modify_invocation_context",
            skill_invocation_context(self.skill_name),
            AbstractContextManager,
        )

        with activity_log_context():
            start = time.monotonic()
            with context:
                result = self.harness.run(
                    prompt, cwd=self.repo_root, config=config
                )
            duration_ms = int((time.monotonic() - start) * 1000)
            if not isinstance(result, HarnessResult):
                raise SkillActivityError("invalid_harness_result")
            if result.exit_code != 0:
                get_activity_logger().error(
                    "FailSkillHarnessInvocation: skill_name=%s exit_code=%s",
                    self.skill_name,
                    result.exit_code,
                )
                raise SkillActivityError(
                    f"Harness exited {result.exit_code} while running skill "
                    f"'{self.skill_name}'"
                )
            try:
                sentinel = json.loads(sentinel_file.read_text())
            except FileNotFoundError:
                output_path = self.expected_output_path(skill_input)
                get_activity_logger().warning(
                    "WarnSkillArtifactVerification: skill_name=%s "
                    "failure_reason=%s output_path=%s",
                    self.skill_name,
                    "missing_sentinel",
                    output_path,
                )
            except json.JSONDecodeError as exc:
                raise SkillActivityError(
                    f"Malformed sentinel for skill '{self.skill_name}'"
                ) from exc
            else:
                if sentinel.get("task") != self.skill_name:
                    raise SkillActivityError(
                        f"Sentinel task mismatch for skill '{self.skill_name}'"
                    )
                output_value = sentinel.get("verify_params", {}).get(
                    self.output_path_key
                )
                if not output_value:
                    raise SkillActivityError(
                        f"Sentinel for skill '{self.skill_name}' is missing "
                        f"verify_params.{self.output_path_key}"
                    )
                output_path = Path(output_value)
            output_path = self._hook(
                "modify_output_path", output_path, Path
            )
            output = SkillActivityOutput(
                status="success",
                output_path=str(output_path),
                sentinel_path=str(sentinel_file.relative_to(self.repo_root)),
                duration_ms=duration_ms,
                activity_log_path=get_activity_log_path() or "",
                devin_log_path=get_devin_log_path() or "",
            )
        return self._hook("modify_result", output, SkillActivityOutput)


def run_skill(
    skill_input: SkillActivityInput,
    *,
    output_path_key: str,
    harness: Harness,
    repo_root: Path = REPO_ROOT,
) -> SkillActivityOutput:
    sentinel_file = _sentinel_path(repo_root, skill_input.skill_name)
    # Idempotency: discard any stale sentinel from a previous (e.g. crashed)
    # attempt so we never read a result that didn't come from this invocation.
    if sentinel_file.exists():
        sentinel_file.unlink()

    prompt = _build_prompt(skill_input)

    with activity_log_context():
        logger = get_activity_logger()
        logger.info("RunSkill: skill_name=%s", skill_input.skill_name)

        start = time.monotonic()
        with skill_invocation_context(skill_input.skill_name):
            result = harness.run(prompt, cwd=repo_root)
        duration_ms = int((time.monotonic() - start) * 1000)

        logger.debug(
            "Harness finished in %s ms with exit_code=%s",
            duration_ms,
            result.exit_code,
        )

        if result.exit_code != 0:
            logger.error(
                "FailSkillHarnessInvocation: skill_name=%s exit_code=%s",
                skill_input.skill_name,
                result.exit_code,
            )
            raise SkillActivityError(
                f"Harness exited {result.exit_code} while running skill "
                f"'{skill_input.skill_name}': {result.stderr or result.stdout}"
            )

        try:
            sentinel = json.loads(sentinel_file.read_text())
        except FileNotFoundError:
            output_path = _conventional_output_path(skill_input)
            logger.warning(
                "WarnSkillArtifactVerification: skill_name=%s failure_reason=%s output_path=%s",
                skill_input.skill_name,
                "missing_sentinel",
                output_path,
            )
        else:
            if sentinel.get("task") != skill_input.skill_name:
                raise SkillActivityError(
                    f"Sentinel task mismatch for skill '{skill_input.skill_name}': "
                    f"got {sentinel.get('task')!r}"
                )

            verify_params = sentinel.get("verify_params", {})
            output_path = verify_params.get(output_path_key)
            if not output_path:
                raise SkillActivityError(
                    f"Sentinel for skill '{skill_input.skill_name}' is missing "
                    f"verify_params.{output_path_key}"
                )

        activity_log_path = get_activity_log_path() or ""
        devin_log_path = get_devin_log_path() or ""
        logger.debug("Activity log: %s", activity_log_path)
        logger.debug("Devin log: %s", devin_log_path)

    return SkillActivityOutput(
        status="success",
        output_path=output_path,
        sentinel_path=str(sentinel_file.relative_to(repo_root)),
        duration_ms=duration_ms,
        activity_log_path=activity_log_path,
        devin_log_path=devin_log_path,
    )
