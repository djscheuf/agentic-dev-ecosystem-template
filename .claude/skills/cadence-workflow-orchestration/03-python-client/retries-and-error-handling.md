# Python: Retries and Error Handling

## RetryPolicy

`RetryPolicy` is a `TypedDict` from `cadence.workflow`. `initial_interval` is required by the server;
at least one of `maximum_attempts` or `expiration_interval` must be non-zero.

```python
from datetime import timedelta
from cadence.workflow import RetryPolicy

policy = RetryPolicy(
    initial_interval=timedelta(seconds=1),      # delay before first retry
    backoff_coefficient=2.0,                     # multiplier per attempt (default 2.0, must be >= 1.0)
    maximum_interval=timedelta(minutes=5),       # cap on delay (must be >= initial_interval)
    maximum_attempts=5,                          # 0 = unlimited (then expiration_interval required)
    non_retryable_error_reasons=["InvalidInput"],
    expiration_interval=timedelta(hours=1),      # stop retrying after this wall-clock duration
)
```

### Applying to an activity

```python
from cadence.workflow import execute_activity, RetryPolicy

result = await execute_activity(
    "fetch_order",
    dict,
    order_id,
    start_to_close_timeout=timedelta(minutes=5),
    retry_policy=RetryPolicy(
        initial_interval=timedelta(seconds=1),
        maximum_attempts=3,
        non_retryable_error_reasons=["OrderNotFound"],
    ),
)
```

### Applying to a child workflow

```python
from cadence.workflow import execute_child_workflow, RetryPolicy

result = await execute_child_workflow(
    "ProcessOrderWorkflow",
    str,
    order_id,
    task_list="order-workers",
    execution_start_to_close_timeout=timedelta(hours=1),
    retry_policy=RetryPolicy(
        initial_interval=timedelta(seconds=1),
        maximum_attempts=2,
    ),
)
```

### Non-retryable errors

`non_retryable_error_reasons` short-circuits retry as soon as the raised exception's string
representation matches one of the listed reasons — the error propagates to the caller immediately:

```python
retry_policy=RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_attempts=10,
    non_retryable_error_reasons=["InvalidInput", "Unauthorized"],
)
```

## Error handling

The SDK converts server-side failures into Python exceptions caught with normal `try`/`except`.

### Activity failures

After all retries are exhausted (or a non-retryable error fires), `execute_activity` raises
`ActivityFailure`:

```python
from cadence.error import ActivityFailure
from cadence.workflow import execute_activity

@registry.workflow()
class OrderWorkflow:
    @workflow.run
    async def run(self, order_id: str) -> str:
        try:
            result = await execute_activity(
                "fetch_order", dict, order_id,
                start_to_close_timeout=timedelta(minutes=5),
            )
        except ActivityFailure as e:
            await execute_activity(
                "send_alert", type(None), str(e),
                start_to_close_timeout=timedelta(seconds=30),
            )
            return "failed"
        return result["status"]
```

### Child workflow failures

```python
from cadence.error import (
    StartChildWorkflowExecutionFailed,
    ChildWorkflowExecutionFailed,
    ChildWorkflowExecutionCanceled,
    ChildWorkflowExecutionTimedOut,
    ChildWorkflowExecutionTerminated,
)

try:
    result = await execute_child_workflow("ProcessWorkflow", str, ...)
except StartChildWorkflowExecutionFailed:
    ...  # e.g. duplicate workflow ID
except ChildWorkflowExecutionFailed:
    ...  # started but failed during execution
except ChildWorkflowExecutionCanceled:
    ...
except ChildWorkflowExecutionTimedOut as e:
    ...  # e.timeout_type indicates which timeout fired
except ChildWorkflowExecutionTerminated:
    ...
```

All five subclass `ChildWorkflowError` — catch that base class for a single handler across the whole
child lifecycle.

### Signal failures

```python
from cadence.error import SignalExternalWorkflowFailed
from cadence.workflow import signal_external_workflow

try:
    await signal_external_workflow("target-wf", "my-signal")
except SignalExternalWorkflowFailed:
    ...  # target not found or couldn't receive the signal
```

### Workflow cancellation

A cancellation surfaces as `asyncio.CancelledError` at pending `await` points — catch it to run
cleanup, then **re-raise** so Cadence correctly records the cancellation:

```python
@registry.workflow()
class LongWorkflow:
    @workflow.run
    async def run(self) -> None:
        try:
            await execute_activity("long_activity", type(None), ...)
        except asyncio.CancelledError:
            await execute_activity("cleanup_activity", type(None), ...)
            raise
```

### Error reference

| Exception | When raised |
|---|---|
| `ActivityFailure` | Activity exhausted retries or hit a non-retryable error. |
| `WorkflowFailure` | A workflow execution failed. |
| `StartChildWorkflowExecutionFailed` | Child workflow could not be started. |
| `ChildWorkflowExecutionFailed` | Child started but failed. |
| `ChildWorkflowExecutionCanceled` | Child was cancelled. |
| `ChildWorkflowExecutionTimedOut` | Child exceeded its execution timeout. |
| `ChildWorkflowExecutionTerminated` | Child was forcibly terminated. |
| `ChildWorkflowError` | Base class for all five child-workflow lifecycle errors above. |
| `SignalExternalWorkflowFailed` | Signal delivery to an external workflow failed. |
| `SignalFailure` | Internal signal routing failure. |
| `ContinueAsNewError` | Raised internally by `workflow.continue_as_new()` — do not catch it. |
| `CadenceRpcError` | Client-side gRPC-level error talking to the Cadence server. |

```python
from cadence.error import ActivityFailure, ChildWorkflowExecutionFailed, CadenceRpcError
```
