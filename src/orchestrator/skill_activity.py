"""Generic Activity-side wrapper for invoking an agentic SDLC skill.

Shells out to the `devin` CLI (same subprocess pattern as `evals/devin.js`) to run
one of the SDLC skills (extract-story-intent, analyze-story, grade-story-analysis,
repair-story-analysis), then reads the skill's sentinel file from `.process/` to
discover the repository-relative path of the artifact it produced (ADR-004).

The `runner` (defaults to `subprocess.run`) and `repo_root` are injectable so this
module can be unit tested without a real `devin` CLI or repository checkout.
"""

import json
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL = "SWE-1.6"


class SkillActivityError(RuntimeError):
    """Raised when the skill subprocess fails or produces an invalid sentinel."""


@dataclass(frozen=True)
class SkillActivityInput:
    skill_name: str
    input_paths: list[str] = field(default_factory=list)
    context: str = ""
    model: str = DEFAULT_MODEL


@dataclass(frozen=True)
class SkillActivityOutput:
    status: str
    output_path: str
    sentinel_path: str
    duration_ms: int


def _sentinel_path(repo_root: Path, skill_name: str) -> Path:
    return repo_root / ".process" / f"{skill_name}.done.json"


def _build_prompt(skill_input: SkillActivityInput) -> str:
    lines = [f"Invoke the '{skill_input.skill_name}' skill."]
    if skill_input.input_paths:
        lines.append("Input document path(s): " + ", ".join(skill_input.input_paths))
    if skill_input.context:
        lines.append(skill_input.context)
    return "\n".join(lines)


def run_skill(
    skill_input: SkillActivityInput,
    *,
    output_path_key: str,
    repo_root: Path = REPO_ROOT,
    runner: Callable[..., "subprocess.CompletedProcess[str]"] = subprocess.run,
) -> SkillActivityOutput:
    sentinel_file = _sentinel_path(repo_root, skill_input.skill_name)
    # Idempotency: discard any stale sentinel from a previous (e.g. crashed)
    # attempt so we never read a result that didn't come from this invocation.
    if sentinel_file.exists():
        sentinel_file.unlink()

    prompt = _build_prompt(skill_input)
    command = [
        "devin",
        "-p",
        "--permission-mode",
        "auto",
        "--model",
        skill_input.model,
        "--",
        prompt,
    ]

    start = time.monotonic()
    result = runner(command, cwd=str(repo_root), capture_output=True, text=True)
    duration_ms = int((time.monotonic() - start) * 1000)

    if result.returncode != 0:
        raise SkillActivityError(
            f"devin CLI exited {result.returncode} while running skill "
            f"'{skill_input.skill_name}': {result.stderr or result.stdout}"
        )

    if not sentinel_file.exists():
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

    return SkillActivityOutput(
        status="success",
        output_path=output_path,
        sentinel_path=str(sentinel_file.relative_to(repo_root)),
        duration_ms=duration_ms,
    )
