from datetime import timedelta
from typing import Optional

from cadence import workflow
from cadence.error import ActivityFailure as CadenceActivityFailure
from cadence.workflow import RetryPolicy, execute_activity

WORKFLOW_TYPE = "SingleActivityWorkflow"
ACTIVITY_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=5),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(minutes=5),
    maximum_attempts=3,
)
ACTIVITY_START_TO_CLOSE_TIMEOUT = timedelta(minutes=30)


def build_single_activity_workflow(allowed_activity_types: frozenset[str]):
    class SingleActivityWorkflow:
        def __init__(self) -> None:
            self._result: Optional[dict] = None

        @workflow.run
        async def run(self, activity_name: str, args: Optional[list] = None) -> dict:
            args = args or []
            if activity_name not in allowed_activity_types:
                self._result = {
                    "status": "failed",
                    "activity_name": activity_name,
                    "error": (
                        f"Unrecognized activity '{activity_name}'. Supported activities: "
                        f"{', '.join(sorted(allowed_activity_types))}"
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
                self._result = {
                    "status": "succeeded",
                    "activity_name": activity_name,
                    "result": result,
                }
            except CadenceActivityFailure as exc:
                self._result = {
                    "status": "failed",
                    "activity_name": activity_name,
                    "error": str(exc),
                }
            return self._result

        @workflow.query(name="get_result")
        def get_result(self) -> dict:
            return self._result if self._result is not None else {"status": "running"}

    return SingleActivityWorkflow
