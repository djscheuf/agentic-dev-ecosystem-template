# Python: Testing with `TestWorkflowEnvironment`

`TestWorkflowEnvironment` runs workflow (and activity) code **in-memory**, with no real Cadence
server: deterministic execution, activity mocking, and virtual time for timer-based workflows.

## Basic test

```python
import pytest
from cadence import Registry, workflow
from cadence.workflow import execute_activity
from cadence.testing import TestWorkflowEnvironment
from datetime import timedelta

registry = Registry()

@registry.workflow()
class GreetingWorkflow:
    @workflow.run
    async def run(self, name: str) -> str:
        return await execute_activity(
            "greet", str, name,
            start_to_close_timeout=timedelta(seconds=5),
        )

@pytest.mark.asyncio
async def test_greeting():
    env = TestWorkflowEnvironment(registry)
    env.on_activity("greet", result="Hello, World!")

    client = env.client
    await client.start_workflow(
        "GreetingWorkflow", "World",
        workflow_id="test-greeting",
        task_list="tl",
        execution_start_to_close_timeout=timedelta(minutes=1),
    )

    result = env.get_workflow_result(str, workflow_id="test-greeting")
    assert result == "Hello, World!"
```

`TestWorkflowEnvironment` also works as a sync context manager: `with TestWorkflowEnvironment(registry) as env: ...`.

## Mocking activities

Fixed return value:

```python
env.on_activity("fetch_order", result={"id": "123", "status": "pending"})
```

Function mock (sync or async), to inspect args or compute a dynamic result:

```python
def fake_fetch(order_id: str) -> dict:
    assert order_id == "123"
    return {"id": order_id, "status": "pending"}

env.on_activity("fetch_order", fn=fake_fetch)
```

The mock function receives the **decoded** activity arguments.

## Checking results

```python
result = env.get_workflow_result(str, workflow_id="my-wf")  # re-raises on workflow failure
error = env.get_workflow_error(workflow_id="my-wf")           # inspect without raising
assert env.is_workflow_completed(workflow_id="my-wf")
```

## Testing signals

```python
@pytest.mark.asyncio
async def test_approval():
    env = TestWorkflowEnvironment(registry)
    client = env.client

    execution = await client.start_workflow(
        "ApprovalWorkflow",
        workflow_id="approval-test",
        task_list="tl",
        execution_start_to_close_timeout=timedelta(minutes=1),
    )

    await client.signal_workflow(execution.workflow_id, "", "approve", True)

    result = env.get_workflow_result(bool, workflow_id="approval-test")
    assert result is True
```

## Testing queries

```python
await client.signal_workflow("my-wf", "", "set_status", "processing")
status = await client.query_workflow("my-wf", "", "get_status", result_type=str)
assert status == "processing"
```

## `TestWorkflowEnvironment` reference

| Member | Description |
|---|---|
| `env.client` | `Client`-compatible object for starting/interacting with workflows. |
| `env.on_activity(name, result=...)` | Mock an activity with a fixed value. |
| `env.on_activity(name, fn=...)` | Mock an activity with a callable. |
| `env.get_workflow_result(type, workflow_id="")` | Decoded result; raises if the workflow failed. |
| `env.get_workflow_error(workflow_id="")` | The error if failed, else `None`. |
| `env.is_workflow_completed(workflow_id="")` | Whether the workflow finished. |
| `env.now()` | Current virtual time. |
| `env.close()` | Shut down the executor. |

**Limitation vs. the Go client:** there is currently no Python equivalent of the Go client's
Workflow Replayer/Shadower for validating a code change against real recorded production history —
see [feature-gaps.md](feature-gaps.md). If you need replay-based compatibility testing today, do it
from a Go-based tooling process against the same domain, or rely on careful manual review + staged
rollout instead.
