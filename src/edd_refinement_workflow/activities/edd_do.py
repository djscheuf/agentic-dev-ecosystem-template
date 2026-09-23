import asyncio
import dataclasses
import hashlib
import subprocess
from pathlib import Path

from cadence import activity

from common.skill_activity import SkillActivity, SkillActivityError, SkillActivityInput

from ..candidate_results import ExecutionResult, UsageMetrics
from .harness_instance import HARNESS, REPO_ROOT


class EddDoSkillActivity(SkillActivity):
    def expected_output_path(self, skill_input: SkillActivityInput) -> Path:
        if not skill_input.input_paths:
            raise SkillActivityError("Cannot derive output path without a plan path")
        return Path(skill_input.input_paths[0])


EDD_DO_ACTIVITY = EddDoSkillActivity(
    config_path=Path(__file__).with_suffix(".config.json"), harness=HARNESS, repo_root=REPO_ROOT
)


class EddDoRunner:
    """Applies the plan's single refinement action via the agentic `edd-do` skill,
    then measures the diff it produced. Approval gating for
    `propose_evaluation_expectation_change` stays deterministic here, never inside
    the skill itself.
    """

    def __init__(self, skill_activity: SkillActivity | None = None) -> None:
        self.skill_activity = skill_activity or EDD_DO_ACTIVITY

    def run(
        self,
        run_id: str,
        planning: dict,
        approved_diff_hash: str | None,
        repo_root: str,
    ) -> ExecutionResult:
        if planning.get("requires_approval"):
            if approved_diff_hash is None:
                raise ValueError("missing_approval")
            if approved_diff_hash != planning.get("proposed_diff_hash"):
                raise ValueError("diff_hash_mismatch")

        plan_path = planning.get("plan_path")
        if not plan_path:
            raise SkillActivityError(
                "planning result is missing plan_path; cannot invoke edd-do"
            )

        try:
            output = self.skill_activity.execute(
                SkillActivityInput(input_paths=[plan_path])
            )
        except SkillActivityError as exc:
            return ExecutionResult(
                status="failed",
                usage_metrics=UsageMetrics(0, 0, 0, 0.0),
                changed_files=[],
                diff_hash="",
                failure_reason=str(exc),
                atif_path=None,
                duration_ms=0,
            )

        diff = subprocess.run(
            ["git", "diff", "--no-ext-diff", "--binary"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        changed_files = subprocess.run(
            ["git", "diff", "--name-only"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
        usage = output.observation.get("usage") or {}
        prompt_tokens = usage.get("prompt_tokens") or 0
        completion_tokens = usage.get("completion_tokens") or 0
        return ExecutionResult(
            status="success",
            usage_metrics=UsageMetrics(
                input_tokens=prompt_tokens,
                output_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                cost_usd=usage.get("cost_usd") or 0.0,
            ),
            changed_files=changed_files,
            diff_hash=hashlib.sha256(diff.encode()).hexdigest(),
            failure_reason=None,
            atif_path=output.observation.get("atif_path"),
            duration_ms=output.duration_ms,
        )


EDD_DO_RUNNER = EddDoRunner()


@activity.defn(name="edd_do")
async def edd_do_action(
    run_id: str,
    planning: dict,
    approved_diff_hash: str | None,
    repo_root: str,
) -> dict:
    result = await asyncio.to_thread(
        EDD_DO_RUNNER.run, run_id, planning, approved_diff_hash, repo_root
    )
    return dataclasses.asdict(result)
