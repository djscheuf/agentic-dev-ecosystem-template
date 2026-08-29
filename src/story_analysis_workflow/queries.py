"""Client-side helpers for querying the Story Analysis Workflow's get_status Query."""

QUERY_NAME = "get_status"


async def get_status(client, workflow_id: str, *, run_id: str = "") -> dict:
    """Query the current status of a Story Analysis Workflow execution."""
    return await client.query_workflow(
        workflow_id,
        run_id,
        QUERY_NAME,
        result_type=dict,
    )
