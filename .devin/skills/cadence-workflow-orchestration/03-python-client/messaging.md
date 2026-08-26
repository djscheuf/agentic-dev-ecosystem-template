# Python: Signals, Queries, and Child Workflows

## Signals

### Defining a handler

```python
from cadence import Registry, workflow
from cadence.workflow import wait_condition

registry = Registry()

@registry.workflow()
class ApprovalWorkflow:
    def __init__(self):
        self._approved: bool | None = None

    @workflow.run
    async def run(self) -> bool:
        await wait_condition(lambda: self._approved is not None)
        return self._approved

    @workflow.signal
    def approve(self, approved: bool) -> None:
        self._approved = approved
```

Signal handlers may be sync or async. Override the wire name with `@workflow.signal(name="cancel-order")`.

### Sending a signal from a client

```python
await client.signal_workflow(
    "my-workflow-id",  # workflow_id
    "",                 # run_id (empty = current run)
    "approve",          # signal name
    True,                # signal argument
)
```

### Signal-with-start

```python
execution = await client.signal_with_start_workflow(
    "ApprovalWorkflow",
    "approve",       # signal name
    [True],          # signal args (list)
    workflow_id="approval-123",
    task_list="approval-workers",
    execution_start_to_close_timeout=timedelta(hours=1),
)
```

### Signaling an external workflow from inside a workflow

```python
from cadence.workflow import signal_external_workflow

@registry.workflow()
class OrchestratorWorkflow:
    @workflow.run
    async def run(self, child_id: str) -> None:
        await signal_external_workflow(child_id, "start", "go")
```

Target a specific run or a different domain:

```python
await signal_external_workflow(
    "other-workflow-id", "cancel",
    run_id="specific-run-id",  # default: current run
    domain="other-domain",      # default: same domain
)
```

### Signaling a child you already hold a future for

```python
future = await start_child_workflow("ChildWorkflow", str, ...)
await future.signal("start-processing", payload)
result = await future
```

## Queries

### Defining a handler

```python
@registry.workflow()
class OrderWorkflow:
    def __init__(self):
        self._status = "pending"

    @workflow.run
    async def run(self, order_id: str) -> str:
        self._status = "processing"
        result = await execute_activity(...)
        self._status = "completed"
        return result

    @workflow.query
    def get_status(self) -> str:
        return self._status
```

Parameterized query:

```python
@workflow.query
def get_item(self, item_id: str) -> dict:
    return self._items.get(item_id)
```

### Constraints (enforced, not just convention)

- Must be **synchronous** (`def`, not `async def`).
- Must **not** call `execute_activity`, `execute_child_workflow`, `sleep`, or any other
  work-scheduling workflow API.
- Must return a value.
- Querying a closed workflow returns its last known state.

### Querying from a client

```python
status = await client.query_workflow(
    "order-123", "", "get_status", result_type=str,
)
```

With arguments:

```python
item = await client.query_workflow(
    "order-123", "", "get_item", "item-42", result_type=dict,
)
```

## Child workflows

### Execute and await the result

```python
from datetime import timedelta
from cadence.workflow import execute_child_workflow

@registry.workflow()
class ParentWorkflow:
    @workflow.run
    async def run(self, order_id: str) -> str:
        return await execute_child_workflow(
            "ProcessOrderWorkflow",
            str,
            order_id,
            task_list="order-workers",
            execution_start_to_close_timeout=timedelta(minutes=30),
        )
```

### Start now, await (or signal) later

```python
from cadence.workflow import start_child_workflow

future = await start_child_workflow(
    "ChildWorkflow", str,
    task_list="child-workers",
    execution_start_to_close_timeout=timedelta(hours=1),
)
await future.signal("start-processing")
result = await future
```

`ChildWorkflowFuture`:

| Member | Description |
|---|---|
| `await future` | Wait for completion, get the result. |
| `future.workflow_id` / `future.run_id` | Identify the child execution. |
| `future.cancel()` | Request cancellation. |
| `await future.signal(name, *args)` | Signal the child. |

### Child workflow options

| Option | Description |
|---|---|
| `workflow_id` | ID for the child (auto-generated if omitted). |
| `task_list` | Task list for the child worker. |
| `execution_start_to_close_timeout` | Max total duration. |
| `task_start_to_close_timeout` | Max time per decision task. |
| `retry_policy` | See [retries-and-error-handling.md](retries-and-error-handling.md). |
| `cron_schedule` | Run the child as a recurring cron workflow (prefer Schedules — see [schedules](../01-concepts/timers-and-schedules.md#schedules)). |
| `domain` | Defaults to the parent's domain. |
| `parent_close_policy` | What happens to the child when the parent closes. |
| `memo` | Key-value metadata. |

### Parent close policy

```python
from cadence.api.v1 import workflow_pb2

future = await start_child_workflow(
    "ChildWorkflow", str,
    task_list="child-workers",
    execution_start_to_close_timeout=timedelta(hours=1),
    parent_close_policy=workflow_pb2.PARENT_CLOSE_POLICY_ABANDON,
)
```

| Policy | Behavior |
|---|---|
| `PARENT_CLOSE_POLICY_TERMINATE` (default) | Terminate the child when the parent closes. |
| `PARENT_CLOSE_POLICY_ABANDON` | Child keeps running independently of the parent. |
| `PARENT_CLOSE_POLICY_REQUEST_CANCEL` | Child receives a cancellation request. |

Same semantics as the Go client — see
[../02-go-client/child-workflows-and-messaging.md](../02-go-client/child-workflows-and-messaging.md#when-the-parent-closes).
