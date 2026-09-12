# Python: Defining Workflows and Activities

## Defining a workflow

A workflow is a class decorated with `@registry.workflow()`, with exactly one `@workflow.run` method
holding the orchestration logic:

```python
from cadence import Registry, workflow

registry = Registry()

@registry.workflow()
class OrderWorkflow:
    @workflow.run
    async def run(self, order_id: str) -> str:
        # workflow logic
        return "completed"
```

`@registry.workflow()` registers under the class name by default; override with `name=`:

```python
@registry.workflow(name="order-workflow-v2")
class OrderWorkflow:
    ...
```

### Initialization

`__init__` runs before `run` and is where you set up instance state that signal/query handlers will
read and write:

```python
@registry.workflow()
class CounterWorkflow:
    def __init__(self):
        self._count = 0

    @workflow.run
    async def run(self) -> int:
        await workflow.sleep(timedelta(hours=1))
        return self._count

    @workflow.signal
    def increment(self) -> None:
        self._count += 1
```

### Workflow info

```python
from cadence.workflow import WorkflowContext

ctx = WorkflowContext.get()
print(ctx.info().workflow_id)
print(ctx.info().workflow_run_id)
print(ctx.info().workflow_domain)
print(ctx.info().workflow_task_list)
```

### Determinism constraints (Python-specific)

Same underlying requirement as every Cadence SDK — see
[../01-concepts/workflows.md](../01-concepts/workflows.md) — expressed in Python terms:

- **Never** `time.time()` / `datetime.now()` — use `workflow.sleep()` (durable timer) instead.
- **Never** `random`, `uuid`, or other non-deterministic sources directly in workflow code.
- **Never** make I/O calls directly — always via `execute_activity`.
- **Never** use raw `threading` or `asyncio.create_task()` — the workflow event loop is owned and
  controlled by the worker; spawning your own tasks breaks replay determinism.

## Defining activities

Standalone async (or sync) function:

```python
from cadence import activity

@activity.defn()
async def fetch_order(order_id: str) -> dict:
    # HTTP call, DB query, etc.
    return {"id": order_id, "status": "pending"}

@activity.defn()
def send_email(to: str, subject: str) -> None:
    # sync activities work too
    ...
```

Override the registered name with `name=`:

```python
@activity.defn(name="fetch-order-v2")
async def fetch_order_v2(order_id: str) -> dict:
    ...
```

### Grouping activities in a class

```python
from cadence import activity

class OrderActivities:
    @activity.method()
    async def fetch_order(self, order_id: str) -> dict:
        ...

    @activity.method()
    async def update_status(self, order_id: str, status: str) -> None:
        ...
```

Register an instance (not the class):

```python
registry.register_activities(OrderActivities())
```

### Registering activities (all forms)

```python
from cadence.worker import Registry
registry = Registry()

registry.register_activity(fetch_order)             # standalone function
registry.register_activities(OrderActivities())      # all @activity.method on an instance

@registry.activity()                                 # decorator form
async def process_payment(amount: float) -> str:
    ...
```

## Calling an activity from a workflow

```python
from datetime import timedelta
from cadence.workflow import execute_activity

@registry.workflow()
class OrderWorkflow:
    @workflow.run
    async def run(self, order_id: str) -> str:
        order = await execute_activity(
            "fetch_order",
            dict,                      # expected return type
            order_id,                  # positional args to the activity
            start_to_close_timeout=timedelta(minutes=5),
        )
        await execute_activity(
            "send_email",
            type(None),
            order["email"],
            "Your order is ready",
            start_to_close_timeout=timedelta(seconds=30),
        )
        return "done"
```

`execute_activity(name, return_type, *args, **options)` — always pass the activity's **registered
name** (a string) and the **expected Python return type** so the client can deserialize the result.

### Activity options

| Option | Description |
|---|---|
| `start_to_close_timeout` | Max time for one attempt. Required if `schedule_to_close_timeout` isn't set. |
| `schedule_to_close_timeout` | Max total time including scheduling and all retries. |
| `schedule_to_start_timeout` | Max time waiting in the task list before a worker starts it. |
| `heartbeat_timeout` | Max time between heartbeats for long-running activities. |
| `task_list` | Override task list for this specific activity call. |
| `retry_policy` | See [retries-and-error-handling.md](retries-and-error-handling.md). |

## Heartbeating

```python
from cadence import activity
import asyncio

@activity.defn()
async def process_large_file(file_path: str) -> int:
    rows_processed = 0
    with open(file_path) as f:
        for line in f:
            process_line(line)
            rows_processed += 1
            if rows_processed % 1000 == 0:
                activity.heartbeat(rows_processed)  # report progress
            await asyncio.sleep(0)  # yield control back to the event loop
    return rows_processed
```

Resume from the last heartbeat's progress on retry with `activity.heartbeat_details()`.

## Activity context

```python
@activity.defn()
async def my_activity() -> None:
    info = activity.info()
    print(info.activity_id)
    print(info.workflow_id)
    print(info.workflow_run_id)
    print(info.attempt)
    print(info.heartbeat_timeout)
```
