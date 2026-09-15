SIGNAL_NAME = "approve_evaluation_change"
QUERY_NAME = "get_approval_status"


async def send_approval_decision(
    client,
    workflow_id: str,
    proposal_id: str,
    decision: str,
    notes: str = "",
    *,
    run_id: str = "",
) -> None:
    if decision not in {"approve", "reject"}:
        raise ValueError("invalid approval decision")
    await client.signal_workflow(
        workflow_id, run_id, SIGNAL_NAME, decision, proposal_id, notes
    )


async def get_approval_status(client, workflow_id: str, *, run_id: str = "") -> dict:
    return await client.query_workflow(
        workflow_id, run_id, QUERY_NAME, result_type=dict
    )
