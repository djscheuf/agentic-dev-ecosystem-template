"""`SingleActivityWorkflow`: a minimal probe workflow that schedules exactly
one Story Analysis Activity.

Cadence has no API to invoke an Activity outside of a Workflow -- only a
Workflow can schedule an Activity Task -- so manual "run just this one
Activity" testing against a real Cadence server (see
`scripts/run-single-activity` / `story_analysis_workflow.run_single_activity`)
goes through this thin probe Workflow instead of the full
`StoryAnalysisWorkflow`. It reuses the same `ACTIVITY_RETRY_POLICY` /
`ACTIVITY_START_TO_CLOSE_TIMEOUT` as the real workflow, so retries/timeouts
behave identically to a normal run.

Rather than raising and failing the Workflow Execution outright, both an
unrecognized Activity name and an Activity failure are captured into the
returned/queryable result dict -- so a caller polling `get_result` always
sees a consistent `{status, ...}` shape instead of having to distinguish
"workflow failed" from "activity failed".
"""

from typing import Optional

from cadence import workflow
from cadence.error import ActivityFailure as CadenceActivityFailure
from cadence.workflow import execute_activity

from story_analysis_workflow.workflow import (
    ACTIVITY_RETRY_POLICY,
    ACTIVITY_START_TO_CLOSE_TIMEOUT,
    registry,
)

WORKFLOW_TYPE = "SingleActivityWorkflow"

KNOWN_ACTIVITY_NAMES = frozenset(
    {"extract_story_intent", "analyze_story", "grade_story_analysis", "repair_story_analysis"}
)

# `repair_story_analysis` needs two input files (analysis + grade); the
# single-input-file scripts/clients this workflow backs don't support it.
UNSUPPORTED_ACTIVITY_NAMES = {
    "repair_story_analysis": "needs two input files (analysis + grade)",
}


@registry.workflow(name=WORKFLOW_TYPE)
class SingleActivityWorkflow:
    def __init__(self) -> None:
        self._result: Optional[dict] = None

    @workflow.run
    async def run(self, activity_name: str, args: Optional[list] = None) -> dict:
        args = args or []

        if activity_name not in KNOWN_ACTIVITY_NAMES:
            self._result = {
                "status": "failed",
                "activity_name": activity_name,
                "error": (
                    f"Unrecognized activity '{activity_name}'. "
                    f"Supported activities: {', '.join(sorted(KNOWN_ACTIVITY_NAMES))}"
                ),
            }
            return self._result

        try:
            result = await execute_activity(
                activity_name,
                dict,
                *args,
                start_to_close_timeout=ACTIVITY_START_TO_CLOSE_TIMEOUT,
                retry_policy=ACTIVITY_RETRY_POLICY,
            )
            self._result = {"status": "succeeded", "activity_name": activity_name, "result": result}
        except CadenceActivityFailure as exc:
            self._result = {"status": "failed", "activity_name": activity_name, "error": str(exc)}

        return self._result

    @workflow.query(name="get_result")
    def get_result(self) -> dict:
        return self._result if self._result is not None else {"status": "running"}
