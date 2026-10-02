# Python: Setup, Client, and Workers

The Cadence Python client is an **async** SDK that talks to the Cadence frontend over gRPC. It is a
community SDK — see [feature-gaps.md](feature-gaps.md) before relying on anything not covered here.

## Installation

```bash
pip install cadence-python-client
```

- GitHub: [cadence-workflow/cadence-python-client](https://github.com/cadence-workflow/cadence-python-client)
- Samples: [cadence-samples/python_sdk_samples](https://github.com/cadence-workflow/cadence-samples/tree/master/python_sdk_samples)

## Packages at a glance

| Package | Purpose |
|---|---|
| `cadence.client` | `Client` — connects to the frontend, starts/signals/queries workflows, manages schedules. |
| `cadence.worker` | `Worker` polls for tasks; `Registry` holds workflow/activity definitions. |
| `cadence.workflow` | Decorators/functions for workflow logic: `@workflow.run`, `@workflow.signal`, `@workflow.query`, `execute_activity`, `execute_child_workflow`, `sleep`, `continue_as_new`. |
| `cadence.activity` | Decorators for activities: `@activity.defn`, `@activity.method`; context functions `activity.heartbeat()`, `activity.info()`. |
| `cadence.testing` | `TestWorkflowEnvironment` — run workflows in-memory without a real server. |

## Client

`Client` is an async context manager connecting to the Cadence frontend:

```python
from cadence.client import Client

CADENCE_TARGET = "localhost:7833"  # Cadence frontend gRPC address

async with Client(domain="my-domain", target=CADENCE_TARGET) as client:
    ...  # client is ready here
```

| Option | Description |
|---|---|
| `domain` | Cadence domain (required). |
| `target` | Frontend address `host:port` (default `localhost:7833`). |
| `identity` | Identity string shown in workflow history (default auto-generated). |
| `data_converter` | Custom serializer for workflow arguments. |

## Registry

`Registry` holds workflow/activity definitions — create one per worker process (or share across
several):

```python
from cadence.worker import Registry

registry = Registry()

@registry.workflow()
class MyWorkflow:
    @workflow.run
    async def run(self, name: str) -> str:
        ...

@registry.activity()
async def my_activity(input: str) -> str:
    ...
```

You can also register imperatively: `registry.register_activity(my_activity)`,
`registry.register_activities(SomeActivitiesInstance())`.

## Worker

`Worker` is an async context manager that polls a task list and dispatches tasks. Internally it runs
two concurrent pollers: one for decision (workflow) tasks, one for activity tasks.

```python
from cadence.worker import Worker

async with Client(domain="my-domain", target=CADENCE_TARGET) as client:
    async with Worker(client, "my-task-list", registry):
        await asyncio.Event().wait()  # keep alive until interrupted
```

Disable one poller if a process should only handle one kind of task (e.g. a dedicated activity-only
worker pool):

```python
Worker(client, "my-task-list", registry, disable_activity_worker=True)
Worker(client, "my-task-list", registry, disable_workflow_worker=True)
```

## Full minimal example

```python
import asyncio
from cadence.client import Client
from cadence.worker import Worker, Registry
from cadence import workflow

CADENCE_TARGET = "localhost:7833"

registry = Registry()

@registry.workflow()
class GreetingWorkflow:
    @workflow.run
    async def run(self, name: str) -> str:
        return f"Hello, {name}!"

async def main():
    async with Client(domain="my-domain", target=CADENCE_TARGET) as client:
        print("Worker running, press Ctrl-C to stop")
        async with Worker(client, "my-task-list", registry):
            await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
```

See [../00-get-started/local-quickstart.md](../00-get-started/local-quickstart.md) for getting a
local Cadence server and domain up before running this.
