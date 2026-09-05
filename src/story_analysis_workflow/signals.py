"""Client-side helpers for sending the Story Analysis Workflow's human_response Signal."""

from .escalation import parse_human_response

SIGNAL_NAME = "human_response"


async def send_human_response(
    client,
    workflow_id: str,
    decision: str,
    notes: str = "",
    *,
    run_id: str = "",
) -> None:
    """Send a ``human_response`` Signal to the running workflow.

    ``decision`` must be one of ``retry``, ``accept``, or ``abort``.
    """
    parse_human_response(decision, notes)  # validate before any network call
    await client.signal_workflow(workflow_id, run_id, SIGNAL_NAME, decision, notes)
