"""Generic Activity-side wrapper for invoking an agentic SDLC skill.

Builds the prompt that connects a skill (extract-story-intent, analyze-story,
grade-story-analysis, repair-story-analysis) and its inputs, sends that prompt
to a given `Harness` to execute, then reads the skill's sentinel file from
`.process/` to discover the repository-relative path of the artifact it
produced (ADR-004).

This module knows nothing about *how* the prompt gets executed -- that is the
`Harness`'s job (see `harness.py`; `devin_harness.DevinHarness` is the default
implementation). `repo_root` is also injectable so this module can be unit
tested without a real repository checkout.
"""

import json
import time
from dataclasses import dataclass, field
from pathlib import Path

from .harness import Harness
from .invocation_context import skill_invocation_context
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
                "Harness failed for skill '%s': %s",
                skill_input.skill_name,
                result.stderr or result.stdout,
            )
            raise SkillActivityError(
                f"Harness exited {result.exit_code} while running skill "
                f"'{skill_input.skill_name}': {result.stderr or result.stdout}"
            )

        if not sentinel_file.exists():
            logger.error(
                "FailSkillArtifactVerification: skill_name=%s failure_reason=%s",
                skill_input.skill_name,
                "missing_sentinel",
            )
            raise SkillActivityError(
                f"Skill '{skill_input.skill_name}' completed without writing "
                f"sentinel file {sentinel_file}"
            )

        sentinel = json.loads(sentinel_file.read_text())
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
