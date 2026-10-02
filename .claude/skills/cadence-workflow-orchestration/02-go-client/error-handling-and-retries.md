# Go: Error Handling and Retries

## Retry policies

Activities, child workflows, and parent workflows can each be given a `RetryPolicy`:

```go
RetryPolicy struct {
    InitialInterval    time.Duration // required
    BackoffCoefficient float64       // default 2.0, must be >= 1
    MaximumInterval    time.Duration // default 100x InitialInterval
    ExpirationInterval time.Duration // either this or MaximumAttempts required
    MaximumAttempts    int32         // either this or ExpirationInterval required
    NonRetryableErrorReasons []string
}
```

Attach it via `ActivityOptions.RetryPolicy`, `ChildWorkflowOptions.RetryPolicy`, or
`StartWorkflowOptions.RetryPolicy` respectively:

```go
retryPolicy := &cadence.RetryPolicy{
    InitialInterval:    time.Second,
    BackoffCoefficient: 2,
    MaximumInterval:    time.Minute * 10,
    ExpirationInterval: time.Minute * 10,
    MaximumAttempts:    5,
}
ao := workflow.ActivityOptions{
    ScheduleToStartTimeout: time.Minute * 10,
    StartToCloseTimeout:    time.Minute * 10,
    HeartbeatTimeout:       time.Second * 30,
    RetryPolicy:            retryPolicy,
}
ctx = workflow.WithActivityOptions(ctx, ao)
activityFuture := workflow.ExecuteActivity(ctx, SampleActivity, params)
```

`NonRetryableErrorReasons` lets you exclude specific error reasons from retry (e.g. invalid-argument
errors that will never succeed no matter how many times you retry). Reason strings:
- Custom errors: whatever reason string you passed to `cadence.NewCustomError(reason, ...)`.
- Panics: `"cadenceInternal:Panic"`.
- Generic errors: `"cadenceInternal:Generic"`.
- Timeouts: `"cadenceInternal:Timeout TIMEOUT_TYPE"` (`START_TO_CLOSE` or `HEARTBEAT`).
- Cancellation is never retried (it isn't treated as a failure).

### Resuming from heartbeat progress on retry

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

### History effects of RetryPolicy (useful when reading a workflow's history while debugging)

- For a retried **activity**: `ActivityTaskScheduledEvent`'s `ScheduleToStart`/`ScheduleToClose`
  timeouts get overwritten to match `RetryPolicy.ExpirationInterval` (or the workflow's own timeout
  if unset). `ActivityTaskStartedEvent` won't appear until the activity finally completes or
  exhausts retries — check `DescribeWorkflowExecution`'s `PendingActivityInfo.attemptCount` to see
  an in-progress retry count.
- For a retried **workflow**: a failed run closes with a `ContinueAsNew` event
  (`ContinueAsNewInitiator = RetryPolicy`) and a new `RunID` for the next attempt. The next attempt
  is created immediately, but its first decision task waits for the backoff duration
  (`firstDecisionTaskBackoffSeconds` in `WorkflowExecutionStartedEventAttributes`).

## Error handling

Errors returned by activities/child workflows arrive at the caller typed by cause:

```go
err := workflow.ExecuteActivity(ctx, YourActivityFunc).Get(ctx, nil)
switch err := err.(type) {
case *cadence.CustomError:
    switch err.Reason() {
    case "err-reason-a":
        var details YourErrorDetailsType
        err.Details(&details)
        // handle details
    case "err-reason-b":
        // handle
    default:
        // handle other reasons
    }
case *workflow.GenericError: // from errors.New()/fmt.Errorf() in the activity
    switch err.Error() {
    case "err-msg-1":
        // handle
    default:
        // handle
    }
case *workflow.TimeoutError:
    switch err.TimeoutType() {
    case shared.TimeoutTypeScheduleToStart:
        // handle
    case shared.TimeoutTypeStartToClose:
        // handle
    case shared.TimeoutTypeHeartbeat:
        // handle
    }
case *workflow.PanicError:
    // handle activity panic
case *cadence.CanceledError:
    // handle cancellation
default:
    // should not normally happen
}
```

| Error type | Cause |
|---|---|
| `*workflow.GenericError` | Activity returned `errors.New(...)` / `fmt.Errorf(...)`. |
| `*cadence.CustomError` | Activity returned `cadence.NewCustomError(reason, details)` — inspect `.Reason()` and `.Details()`. |
| `*workflow.TimeoutError` | One of the activity/workflow timeouts fired — check `.TimeoutType()`. |
| `*workflow.PanicError` | The activity (or workflow) panicked. |
| `*cadence.CanceledError` | The activity/workflow was cancelled. |

Decide per error type whether to retry manually, compensate, fail the workflow, or take an
alternative path — this switch typically lives right after the `.Get()` call that surfaced the error.
