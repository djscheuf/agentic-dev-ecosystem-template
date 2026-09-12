import pytest

from story_analysis_workflow.queries import QUERY_NAME, get_status

from .fake_client import FakeClient


@pytest.mark.asyncio
async def test_get_status_calls_client_query_workflow():
    expected = {"status": "running", "attempt_count": 0}
    client = FakeClient(query_result=expected)

    result = await get_status(client, "wf-1")

    assert len(client.query_calls) == 1
    call = client.query_calls[0]
    assert call["workflow_id"] == "wf-1"
    assert call["run_id"] == ""
    assert call["query_type"] == QUERY_NAME
    assert call["result_type"] is dict
    assert result == expected


@pytest.mark.asyncio
async def test_get_status_accepts_optional_run_id():
    client = FakeClient(query_result={})

    await get_status(client, "wf-1", run_id="run-123")

    assert client.query_calls[0]["run_id"] == "run-123"
