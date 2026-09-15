import asyncio
import dataclasses
import hashlib
import subprocess
import time
from collections.abc import Callable
from pathlib import Path

from cadence import activity

from common.devin_harness import DevinHarness
from common.skill_activity_config import SkillActivityConfig
from common.workflow_logger import get_activity_artifact_dir

from ..candidate_results import ExecutionResult, UsageMetrics


class ExecuteRefinementActionActivity:
    def __init__(
        self,
        harness_runner: Callable[..., object],
        on_event: Callable[..., None] | None = None,
    ) -> None:
        self.harness_runner = harness_runner
        self.on_event = on_event

    def run(
        self,
        run_id: str,
        planning: dict,
        approved_diff_hash: str | None,
        repo_root: str,
    ):
        if planning.get("requires_approval"):
            if approved_diff_hash is None:
                raise ValueError("missing_approval")
            if approved_diff_hash != planning.get("proposed_diff_hash"):
                raise ValueError("diff_hash_mismatch")
        try:
            output = self.harness_runner(
                run_id=run_id,
                planning=planning,
                repo_root=repo_root,
            )
        except RuntimeError as exc:
            result = ExecutionResult(
                status="failed",
                usage_metrics=UsageMetrics(0, 0, 0, 0.0),
                changed_files=[],
                diff_hash="",
                failure_reason=str(exc),
                atif_path=None,
                duration_ms=0,
            )
            if self.on_event is not None:
                self.on_event(
                    "RefinementActivityFailed",
                    run_id=run_id,
                    failure_reason=result.failure_reason,
                )
            return result
        observation = output["observation"]
        usage = observation["usage"]
        prompt_tokens = usage["prompt_tokens"]
        completion_tokens = usage["completion_tokens"]
        result = ExecutionResult(
            status=output["status"],
            usage_metrics=UsageMetrics(
                input_tokens=prompt_tokens,
                output_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                cost_usd=usage["cost_usd"],
            ),
            changed_files=output["changed_files"],
            diff_hash=output["diff_hash"],
            failure_reason=output.get("failure_reason"),
            atif_path=observation.get("atif_path"),
            duration_ms=observation["duration_ms"],
        )
        if self.on_event is not None:
            self.on_event(
                "RefinementActivitySucceeded",
                run_id=run_id,
                duration_ms=result.duration_ms,
                changed_files_count=len(result.changed_files),
            )
        return result


class HarnessBackedRefinementRunner:
    def __init__(self, harness=None) -> None:
        self.harness = harness or DevinHarness()
        self.config = SkillActivityConfig.load(
            Path(__file__).with_suffix(".config.json")
        ).harness

    def __call__(self, *, run_id: str, planning: dict, repo_root: str) -> dict:
        prompt = (
            f"Execute refinement action '{planning['action']}' for run '{run_id}'. "
            f"Only modify these files: {planning.get('intended_files', [])}."
        )
        started = time.monotonic()
        harness_result = self.harness.run(
            prompt,
            cwd=Path(repo_root),
            config=self.config,
        )
        if harness_result.exit_code:
            raise RuntimeError(f"harness_failure:{harness_result.exit_code}")
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
        usage = dataclasses.asdict(harness_result.usage) if harness_result.usage else {}
        artifact_dir = get_activity_artifact_dir()
        return {
            "status": "success",
            "observation": {
                "usage": {
                    "prompt_tokens": usage.get("prompt_tokens") or 0,
                    "completion_tokens": usage.get("completion_tokens") or 0,
                    "cost_usd": usage.get("cost_usd") or 0.0,
                },
                "atif_path": str(artifact_dir / "devin-trajectory.json")
                if harness_result.usage is not None and artifact_dir is not None
                else None,
                "duration_ms": int((time.monotonic() - started) * 1000),
            },
            "changed_files": changed_files,
            "diff_hash": hashlib.sha256(diff.encode()).hexdigest(),
        }


EXECUTION_ACTIVITY = ExecuteRefinementActionActivity(HarnessBackedRefinementRunner())


@activity.defn(name="execute_refinement_action")
async def execute_refinement_action_activity(
    run_id: str,
    planning: dict,
    approved_diff_hash: str | None,
    repo_root: str,
) -> dict:
    result = await asyncio.to_thread(
        EXECUTION_ACTIVITY.run,
        run_id,
        planning,
        approved_diff_hash,
        repo_root,
    )
    return dataclasses.asdict(result)
