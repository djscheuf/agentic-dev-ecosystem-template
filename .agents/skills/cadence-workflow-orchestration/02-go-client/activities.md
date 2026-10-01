# Go: Activities

## Defining an activity

```go
package simple

import (
    "context"
    "go.uber.org/cadence/activity"
    "go.uber.org/zap"
)

func init() {
    activity.Register(SimpleActivity)
}

func SimpleActivity(ctx context.Context, value string) (string, error) {
    activity.GetLogger(ctx).Info("SimpleActivity called.", zap.String("Value", value))
    return "Processed: " + value, nil
}
```

- First parameter is conventionally `context.Context` (a plain Go context — activities are **not**
  subject to workflow determinism rules and may use any Go library).
- Remaining parameters are activity inputs, any number, all **serializable**.
- Must return `error`; may also return one result value (also serializable).
- Values passed to/from activities are recorded in the workflow's Event History and transferred to
  every workflow worker replaying it — **keep activity inputs/outputs small**; large payloads hurt
  workflow performance.

### Registration

```go
func init() {
    activity.Register(SimpleActivity)
}
```

Same in-memory-mapping model as workflow registration. An unregistered activity type fails that
specific request.

### Failing an activity

Return a non-nil `error`. See [error-handling-and-retries.md](error-handling-and-retries.md) for how
callers should branch on error type.

## Heartbeating

For long-running activities, report progress/liveness periodically:

```go
progress := 0
for hasWork {
    cadence.RecordActivityHeartbeat(ctx, progress)
    // do some work
    progress++
}
```

If the activity times out due to a missed heartbeat, the last heartbeat `details` payload (here,
`progress`) is returned as the `details` field of the resulting `TimeoutError` (type
`TimeoutType_HEARTBEAT`) — the next retry attempt can read it and resume:

```go
func SampleActivity(ctx context.Context, inputArg InputParams) error {
    startIdx := inputArg.StartIndex
    if activity.HasHeartbeatDetails(ctx) {
        var finishedIndex int
        if err := activity.GetHeartbeatDetails(ctx, &finishedIndex); err == nil {
            startIdx = finishedIndex + 1
        }
    }
    for i := startIdx; i < inputArg.EndIdx; i++ {
        // process item i
        activity.RecordHeartbeat(ctx, i)
    }
    return nil
}
```

**Auto-heartbeat** (Go client 0.17.0+): if you don't need to report progress but still want liveness
detection, enable it at registration time instead of calling `RecordActivityHeartbeat` yourself:

```go
RegisterActivityOptions{
    EnableAutoHeartbeat: true, // no effect if HeartbeatTimeout is 0
}
```

You can also heartbeat from an external process (e.g. the system the activity delegated work to),
using the `TaskToken` from `ActivityInfo` inside the activity:

```go
client.RecordActivityHeartbeat(taskToken, details)
```

## Cancellation

When an activity is cancelled — or its workflow completes/fails — the `context.Context` passed into
the activity is cancelled (`Done()` channel closes). **Cancellation is only delivered to activities
that call `RecordActivityHeartbeat`** — a non-heartbeating activity has no way to observe
cancellation and will run to completion regardless.

## Executing an activity from a workflow

```go
ao := workflow.ActivityOptions{
    TaskList:               "sampleTaskList",
    ScheduleToCloseTimeout: time.Second * 60,
    ScheduleToStartTimeout: time.Second * 60,
    StartToCloseTimeout:    time.Second * 60,
    HeartbeatTimeout:       time.Second * 10,
    WaitForCancellation:    false,
}
ctx = workflow.WithActivityOptions(ctx, ao)

future := workflow.ExecuteActivity(ctx, SimpleActivity, value)
var result string
if err := future.Get(ctx, &result); err != nil {
    return err
}
```

- `ActivityOptions` must be attached to the context before calling `ExecuteActivity` — reuse the same
  context for multiple activities that share options.
- `ExecuteActivity`'s second argument can be the function itself (framework validates parameter
  types) or its registered name as a string.
- The call returns immediately with a `workflow.Future`; call `.Get(ctx, &result)` when you actually
  need the result — this lets you fan out multiple activities in parallel before blocking:

```go
f1 := workflow.ExecuteActivity(ctx, ActivityA, ...)
f2 := workflow.ExecuteActivity(ctx, ActivityB, ...)

var r1, r2 string
if err := f1.Get(ctx, &r1); err != nil { return err }
if err := f2.Get(ctx, &r2); err != nil { return err }
```

For more complex wait conditions across multiple futures, use `workflow.Selector` instead of calling
`Get` sequentially.

### Activity timeouts

| Timeout | Meaning |
|---|---|
| `StartToCloseTimeout` | Max time a worker can take to process the task once received. |
| `ScheduleToStartTimeout` | Max time a task can wait for a worker to pick it up (fires if no worker is available). |
| `ScheduleToCloseTimeout` | Max total time from scheduling to completion (usually > `StartToClose` + `ScheduleToStart`). |
| `HeartbeatTimeout` | Max time between heartbeats before the activity is considered failed. |

Cadence guarantees **at-most-once** activity execution — it either succeeds or fails with one of the
above timeouts (retries notwithstanding).

## Async (externally-completed) activities

If the "real" work is delegated to an external system (message queue, webhook), don't return from the
activity function immediately — instead complete it later via a separate client API call, from any
process. See the Go client's `ActivityCompletionClient` / `CompleteActivity` for the concrete API,
and [../01-concepts/activities.md](../01-concepts/activities.md#asynchronous-activity-completion) for
when to use this pattern.
