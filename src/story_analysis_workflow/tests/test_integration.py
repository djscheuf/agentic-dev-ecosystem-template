"""Round-trip check that starter/signals/queries agree on domain, task list,
signal name, and query name from a single shared `CadenceConfig`."""

import pytest

from story_analysis_workflow.config import load_config
from story_analysis_workflow.queries import QUERY_NAME, get_status
from story_analysis_workflow.signals import SIGNAL_NAME, send_human_response
from story_analysis_workflow.starter import WORKFLOW_TYPE, start_story_analysis_workflow

from .fake_client import FakeClient


@pytest.mark.asyncio
async def test_client_api_round_trip_start_signal_query_uses_consistent_defaults():
    config = load_config()
    client = FakeClient(query_result={"status": "completed"})

    await start_story_analysis_workflow(client, "docs/reqs/workflow-orchestration/story.md", config=config)
    await send_human_response(client, "wf-1", "accept")
    await get_status(client, "wf-1")

    start_call = client.start_calls[0]
    assert start_call["workflow"] == WORKFLOW_TYPE
    assert start_call["options"]["task_list"] == config.task_list

    signal_call = client.signal_calls[0]
    assert signal_call["signal_name"] == SIGNAL_NAME

    query_call = client.query_calls[0]
    assert query_call["query_type"] == QUERY_NAME
