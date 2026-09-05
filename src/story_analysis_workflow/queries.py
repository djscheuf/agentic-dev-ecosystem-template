"""Client-side helpers for querying Cadence Workflow status/result Queries."""

QUERY_NAME = "get_status"
ACTIVITY_RESULT_QUERY_NAME = "get_result"


async def get_status(client, workflow_id: str, *, run_id: str = "") -> dict:
    """Query the current status of a Story Analysis Workflow execution."""
    return await client.query_workflow(
        workflow_id,
        run_id,
        QUERY_NAME,
        result_type=dict,
    )


async def get_activity_result(client, workflow_id: str, *, run_id: str = "") -> dict:
    """Query the current result of a `SingleActivityWorkflow` execution.

    Returns ``{"status": "running"}`` until the probed Activity has
    succeeded or failed (see `orchestrator.single_activity_workflow`).
    """
    return await client.query_workflow(
        workflow_id,
        run_id,
        ACTIVITY_RESULT_QUERY_NAME,
        result_type=dict,
    )
