# Python: Continue-As-New, Distributed Cron, and Schedules

## Continue-as-new

`workflow.continue_as_new(...)` never returns — internally it raises `ContinueAsNewError`, which the
worker intercepts to schedule a fresh execution with a clean history:

```python
from cadence import workflow, Registry
from cadence.workflow import execute_activity

registry = Registry()

@registry.workflow()
class ProcessorWorkflow:
    @workflow.run
    async def run(self, processed_count: int) -> None:
        for _ in range(1000):
            await execute_activity("process_item", type(None), ...)
            processed_count += 1

        workflow.continue_as_new(processed_count)  # never returns
```

The argument(s) passed to `continue_as_new` become the next execution's `run` arguments.

### Overriding parameters on the new run

```python
workflow.continue_as_new(
    processed_count,
    workflow_type="ProcessorWorkflowV2",   # switch workflow type
    task_list="new-task-list",             # move to a different task list
    execution_start_to_close_timeout=timedelta(hours=2),
    task_start_to_close_timeout=timedelta(minutes=1),
)
```

All parameters are optional; omitted ones are inherited from the current run.

### When to use it

- Multi-day/multi-week workflows accumulating many history events.
- Processing an unbounded stream of items (event-loop-style workflows).
- Long-lived cron-style loops not using `cron_schedule`/Schedules.

Cadence enforces a server-side history size limit — a workflow that never continues-as-new risks
automatic termination once it's exceeded. The Python SDK doesn't enforce a specific event count, but
as a rule of thumb, continue-as-new every few thousand events or at the end of each logical "epoch."

**Never catch `ContinueAsNewError`** — doing so silently prevents the continue-as-new from taking
effect.

## Distributed cron (`cron_schedule`)

Legacy recurring-workflow mechanism via `start_workflow(cron_schedule=...)`. Prefer
[Schedules](#schedules) for new work — see the comparison table below.

```python
from cadence.client import Client

async with Client(domain="my-domain", target=CADENCE_TARGET) as client:
    execution = await client.start_workflow(
        "DailyReportWorkflow",
        workflow_id="daily-report",
        task_list="report-workers",
        cron_schedule="0 9 * * *",  # every day at 9 AM UTC, 5-field cron
        execution_start_to_close_timeout=timedelta(hours=2),
    )
```

- After each run completes/fails, the server automatically starts the next execution at the next
  scheduled time — each execution gets a **fresh** history, running from the start of the workflow
  function.
- If a run is still executing when the next fire time arrives, that fire is **skipped** (no overlap
  control beyond "always skip").
- To carry state between runs, return it from `run()` — the next execution receives the previous
  run's result as its first argument:

```python
@registry.workflow()
class DailyReportWorkflow:
    @workflow.run
    async def run(self, last_cursor: str | None = None) -> str:
        new_cursor = await execute_activity(
            "generate_report", str, last_cursor,
            start_to_close_timeout=timedelta(hours=1),
        )
        return new_cursor  # becomes last_cursor on the next run
```

- To stop it: `await client.cancel_workflow("daily-report", "")`. There's no pause/resume — you must
  cancel and restart with a new execution if you need that.

### Cron vs. Schedules

| | `cron_schedule` | Schedules |
|---|---|---|
| Overlap control | Always skip | Configurable |
| Pause/unpause | No | Yes |
| Backfill | No | Yes |
| Visibility | No | Yes |
| Update without restart | No | Yes |

## Schedules

The Python client exposes schedule management as methods on `Client`, using protobuf types from
`cadence.api.v1.schedule_pb2`. See
[../01-concepts/timers-and-schedules.md](../01-concepts/timers-and-schedules.md) for the full concept
(overlap policy, catch-up, backfill).

```python
from datetime import timedelta
import datetime
from google.protobuf.duration import from_timedelta
from google.protobuf.timestamp_pb2 import Timestamp

def _ts(dt: datetime.datetime) -> Timestamp:
    t = Timestamp()
    t.FromDatetime(dt)
    return t
```

### Creating a schedule

```python
from cadence.api.v1 import common_pb2, schedule_pb2, tasklist_pb2

await client.create_schedule(
    "daily-etl",
    spec=schedule_pb2.ScheduleSpec(
        cron_expression="0 2 * * *",  # every day at 2 AM UTC
    ),
    action=schedule_pb2.ScheduleAction(
        start_workflow=schedule_pb2.ScheduleAction.StartWorkflowAction(
            workflow_type=common_pb2.WorkflowType(name="RunETL"),
            task_list=tasklist_pb2.TaskList(name="etl-workers"),
            workflow_id_prefix="daily-etl-",
            execution_start_to_close_timeout=from_timedelta(timedelta(hours=2)),
            task_start_to_close_timeout=from_timedelta(timedelta(seconds=10)),
        )
    ),
    policies=schedule_pb2.SchedulePolicies(
        overlap_policy=schedule_pb2.SCHEDULE_OVERLAP_POLICY_SKIP_NEW,
        catch_up_policy=schedule_pb2.SCHEDULE_CATCH_UP_POLICY_SKIP,
    ),
)
```

### Overlap policy constants

| Constant | Behavior |
|---|---|
| `SCHEDULE_OVERLAP_POLICY_SKIP_NEW` (default) | Skip the new fire if a run is still active. |
| `SCHEDULE_OVERLAP_POLICY_BUFFER` | Queue new fires, run sequentially. |
| `SCHEDULE_OVERLAP_POLICY_CONCURRENT` | Start every fire, up to `concurrency_limit` (0 = unlimited). |
| `SCHEDULE_OVERLAP_POLICY_CANCEL_PREVIOUS` | Cancel the active run, then start the new one. |
| `SCHEDULE_OVERLAP_POLICY_TERMINATE_PREVIOUS` | Terminate the active run immediately, then start. |

`SchedulePolicies` fields: `overlap_policy`, `catch_up_policy`, `catch_up_window`, `buffer_limit`
(cap for `BUFFER`), `concurrency_limit` (cap for `CONCURRENT`, 0 = unlimited).

### Jitter and bounded windows

```python
spec=schedule_pb2.ScheduleSpec(
    cron_expression="0 0 * * *",
    jitter=from_timedelta(timedelta(minutes=10)),  # random delay up to 10 min
)

spec=schedule_pb2.ScheduleSpec(
    cron_expression="0 9 * * 1-5",
    start_time=_ts(datetime.datetime(2026, 7, 1, tzinfo=datetime.timezone.utc)),
    end_time=_ts(datetime.datetime(2026, 12, 31, tzinfo=datetime.timezone.utc)),
)
```

### Describe, pause, unpause

```python
resp = await client.describe_schedule("daily-etl")
print(resp.state.paused)
print(resp.info.next_run_time)
print(resp.info.last_run_time)

await client.pause_schedule("daily-etl", reason="INFRA-4421: cluster maintenance")

await client.unpause_schedule(
    "daily-etl", reason="maintenance complete",
    catch_up_policy=schedule_pb2.SCHEDULE_CATCH_UP_POLICY_SKIP,
)
```

For backfill and the full catch-up policy enum, see
[../05-api-and-cli/cli-reference.md](../05-api-and-cli/cli-reference.md) (CLI has first-class
schedule backfill commands) or the schedule concept page linked above.
