"""Unit tests for the client-side Signal and Query helpers."""

import pytest

from story_analysis_workflow.queries import QUERY_NAME, get_status
from story_analysis_workflow.signals import SIGNAL_NAME, send_human_response
from story_analysis_workflow.tests.fake_client import FakeClient


@pytest.mark.asyncio
async def test_send_human_response_emits_signal_with_valid_decision():
    client = FakeClient()

    await send_human_response(client, "wf-1", "retry", notes="focus on edge cases")

    assert len(client.signal_calls) == 1
    call = client.signal_calls[0]
    assert call["workflow_id"] == "wf-1"
    assert call["run_id"] == ""
    assert call["signal_name"] == SIGNAL_NAME
    assert call["signal_args"] == ("retry", "focus on edge cases")


@pytest.mark.asyncio
async def test_send_human_response_defaults_notes_to_empty_string():
    client = FakeClient()

    await send_human_response(client, "wf-1", "accept")

    assert client.signal_calls[0]["signal_args"] == ("accept", "")


@pytest.mark.asyncio
async def test_send_human_response_rejects_unknown_decision():
    client = FakeClient()

    with pytest.raises(ValueError, match="Unknown human_response decision: 'invalid'"):
        await send_human_response(client, "wf-1", "invalid")

    assert len(client.signal_calls) == 0


@pytest.mark.asyncio
async def test_get_status_queries_workflow_and_returns_result():
    expected = {"status": "running", "attempt_count": 2, "escalated": True}
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
