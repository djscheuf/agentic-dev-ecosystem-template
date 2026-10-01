import pytest
from edd_refinement_workflow.signals import get_approval_status, send_approval_decision
from story_analysis_workflow.tests.fake_client import FakeClient


@pytest.mark.asyncio
async def test_approval_helpers_signal_decision_and_query_status() -> None:
    expected = {"proposal_id": "proposal-1", "status": "pending"}
    client = FakeClient(query_result=expected)

    await send_approval_decision(
        client, "wf-1", "proposal-1", "approve", notes="approved", run_id="run-1"
    )
    status = await get_approval_status(client, "wf-1", run_id="run-1")

    assert client.signal_calls == [
        {
            "workflow_id": "wf-1",
            "run_id": "run-1",
            "signal_name": "approve_evaluation_change",
            "signal_args": ("approve", "proposal-1", "approved"),
        }
    ]
    assert client.query_calls[0]["query_type"] == "get_approval_status"
    assert status == expected
