from datetime import timedelta

from cadence import workflow
from cadence.workflow import execute_activity


class EddRefinementWorkflow:
    @workflow.run
    async def run(self, preflight_result, request: dict):
        record = await execute_activity(
            "initialize_run",
            dict,
            request["workflow_run_id"],
            preflight_result,
            start_to_close_timeout=timedelta(minutes=5),
        )

        baseline = await execute_activity(
            "run_baseline_evaluation",
            dict,
            record["run_id"],
            request["profile"],
            str(preflight_result.target_context.repo_root),
            start_to_close_timeout=timedelta(minutes=30),
        )

        planning = await execute_activity(
            "plan_refinement_action",
            dict,
            record,
            baseline,
            request.get("proposed_action"),
            start_to_close_timeout=timedelta(minutes=5),
        )

        return {
            "record": record,
            "baseline": baseline,
            "planning": planning,
        }
