from datetime import datetime, timedelta

import pytest
from cadence.api.v1 import workflow_pb2

from story_analysis_workflow.config import CadenceConfig
from story_analysis_workflow.starter import WORKFLOW_TYPE, _default_workflow_id, start_story_analysis_workflow

from .fake_client import ExecutionResult, FakeClient


def make_config(**overrides):
    defaults = dict(
        domain="story-analysis",
        task_list="story-analysis",
        cadence_target="localhost:7833",
        execution_start_to_close_timeout=timedelta(hours=1),
        task_start_to_close_timeout=timedelta(seconds=10),
        escalation_timeout=timedelta(minutes=5),
    )
    defaults.update(overrides)
    return CadenceConfig(**defaults)


@pytest.mark.asyncio
async def test_starter_starts_story_analysis_workflow_with_defaults():
    client = FakeClient(start_result=ExecutionResult(workflow_id="story-analysis-story", run_id="run-1"))
    config = make_config()

    execution = await start_story_analysis_workflow(client, "docs/reqs/workflow-orchestration/story.md", config=config)

    assert len(client.start_calls) == 1
    call = client.start_calls[0]
    assert call["workflow"] == WORKFLOW_TYPE
    assert call["args"][0] == "docs/reqs/workflow-orchestration/story.md"
    assert call["options"]["task_list"] == "story-analysis"
    assert call["options"]["execution_start_to_close_timeout"] == timedelta(hours=1)
    assert call["options"]["workflow_id_reuse_policy"] == workflow_pb2.WORKFLOW_ID_REUSE_POLICY_REJECT_DUPLICATE
    assert execution.run_id == "run-1"


@pytest.mark.asyncio
async def test_starter_generates_workflow_id_from_story_name_and_kickoff_time():
    client = FakeClient()
    config = make_config()

    await start_story_analysis_workflow(client, "docs/reqs/workflow-orchestration/example_story.md", config=config)
    workflow_id = client.start_calls[0]["options"]["workflow_id"]

    assert workflow_id.startswith("story-analysis-example_story_")
    # Zettel id is a 12-digit YYYYMMDDHHmm timestamp, no file extension leaks through.
    timestamp = workflow_id.rsplit("_", 1)[-1]
    assert timestamp.isdigit()
    assert len(timestamp) == 12


def test_default_workflow_id_is_deterministic_for_a_given_kickoff_time():
    when = datetime(2026, 8, 31, 14, 30)

    first = _default_workflow_id("docs/reqs/workflow-orchestration/example_story.md", when=when)
    second = _default_workflow_id("docs/reqs/workflow-orchestration/example_story.md", when=when)

    assert first == second == "story-analysis-example_story_202608311430"


def test_default_workflow_id_differs_across_kickoff_times():
    first = _default_workflow_id("example_story.md", when=datetime(2026, 8, 31, 14, 30))
    second = _default_workflow_id("example_story.md", when=datetime(2026, 8, 31, 14, 31))

    assert first != second


@pytest.mark.asyncio
async def test_starter_accepts_explicit_workflow_id_and_config_overrides():
    client = FakeClient()
    config = make_config(execution_start_to_close_timeout=timedelta(minutes=10))

    await start_story_analysis_workflow(
        client, "docs/reqs/workflow-orchestration/story.md", workflow_id="my-custom-id", config=config
    )

    call = client.start_calls[0]
    assert call["options"]["workflow_id"] == "my-custom-id"
    assert call["options"]["execution_start_to_close_timeout"] == timedelta(minutes=10)


@pytest.mark.asyncio
async def test_starter_passes_engine_config_as_second_workflow_arg():
    client = FakeClient()
    config = make_config()

    await start_story_analysis_workflow(
        client,
        "docs/reqs/workflow-orchestration/story.md",
        config=config,
        max_attempts=5,
        escalation_timeout_seconds=60,
    )

    call = client.start_calls[0]
    assert call["args"][1] == {"max_attempts": 5, "escalation_timeout_seconds": 60}
