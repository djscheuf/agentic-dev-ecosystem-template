"""Unit test for HelloWorldWorkflow using TestWorkflowEnvironment.

See ../../03-python-client/testing.md for the full explanation of this pattern
(mocking activities, testing signals/queries).

Run with: pytest test_hello_world_workflow.py
"""

from datetime import timedelta

import pytest
from cadence.testing import TestWorkflowEnvironment

from hello_world_workflow import registry


@pytest.mark.asyncio
async def test_hello_world_success():
    env = TestWorkflowEnvironment(registry)
    env.on_activity("hello_world_activity", result="Hello World!")

    client = env.client
    await client.start_workflow(
        "HelloWorldWorkflow",
        "World",
        workflow_id="test-hello-world",
        task_list="tl",
        execution_start_to_close_timeout=timedelta(minutes=1),
    )

    result = env.get_workflow_result(str, workflow_id="test-hello-world")
    assert result == "Hello World!"


@pytest.mark.asyncio
async def test_hello_world_activity_failure():
    env = TestWorkflowEnvironment(registry)

    def failing_activity(name: str) -> str:
        raise RuntimeError("boom")

    env.on_activity("hello_world_activity", fn=failing_activity)

    client = env.client
    await client.start_workflow(
        "HelloWorldWorkflow",
        "World",
        workflow_id="test-hello-world-fail",
        task_list="tl",
        execution_start_to_close_timeout=timedelta(minutes=1),
    )

    error = env.get_workflow_error(workflow_id="test-hello-world-fail")
    assert error is not None
