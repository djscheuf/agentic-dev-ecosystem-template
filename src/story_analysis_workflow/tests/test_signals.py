import pytest

from story_analysis_workflow.signals import SIGNAL_NAME, send_human_response

from .fake_client import FakeClient


@pytest.mark.asyncio
async def test_send_human_response_with_valid_decision_calls_client_signal_workflow():
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
async def test_send_human_response_accepts_all_valid_decisions():
    for decision in ("retry", "accept", "abort"):
        client = FakeClient()
        await send_human_response(client, "wf-1", decision)
        assert client.signal_calls[0]["signal_args"][0] == decision
