from collections.abc import Callable

from cadence import activity

from ..candidate_results import ExecutionResult, UsageMetrics


class ExecuteRefinementActionActivity:
    def __init__(self, harness_runner: Callable[..., object]) -> None:
        self.harness_runner = harness_runner

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
        output = self.harness_runner(
            run_id=run_id,
            planning=planning,
            repo_root=repo_root,
        )
        observation = output["observation"]
        usage = observation["usage"]
        prompt_tokens = usage["prompt_tokens"]
        completion_tokens = usage["completion_tokens"]
        return ExecutionResult(
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


@activity.defn(name="execute_refinement_action")
async def execute_refinement_action_activity(
    run_id: str,
    planning: dict,
    approved_diff_hash: str | None,
    repo_root: str,
) -> dict:
    raise RuntimeError("execute_refinement_action runner is not configured")
