# Retry Policies and Timeouts — Quick Reference

Consolidated cheat sheet across both SDKs. For full explanations and code, see
[../02-go-client/error-handling-and-retries.md](../02-go-client/error-handling-and-retries.md) and
[../03-python-client/retries-and-error-handling.md](../03-python-client/retries-and-error-handling.md).

## Activity timeouts

| Concept | Go field | Python field | Meaning |
|---|---|---|---|
| Start-to-close | `StartToCloseTimeout` | `start_to_close_timeout` | Max time for one attempt once a worker picks it up. |
| Schedule-to-start | `ScheduleToStartTimeout` | `schedule_to_start_timeout` | Max time waiting in the task list for a worker. |
| Schedule-to-close | `ScheduleToCloseTimeout` | `schedule_to_close_timeout` | Max total time, scheduling through completion (incl. retries). |
| Heartbeat | `HeartbeatTimeout` | `heartbeat_timeout` | Max time between heartbeats. |

You must set either `ScheduleToClose`, or both `ScheduleToStart` and `StartToClose`.

## Retry policy fields

| Concept | Go (`RetryPolicy`) | Python (`RetryPolicy` TypedDict) |
|---|---|---|
| Delay before first retry | `InitialInterval` (required) | `initial_interval` (required) |
| Exponential growth factor | `BackoffCoefficient` (default 2.0, >= 1) | `backoff_coefficient` (default 2.0, >= 1.0) |
| Cap on retry interval | `MaximumInterval` (default 100x initial) | `maximum_interval` (must be >= initial) |
| Hard cap on attempts | `MaximumAttempts` | `maximum_attempts` (0 = unlimited) |
| Hard cap on retry duration | `ExpirationInterval` | `expiration_interval` |
| Errors that skip retry | `NonRetryableErrorReasons` | `non_retryable_error_reasons` |

Either `MaximumAttempts` or `ExpirationInterval`/`expiration_interval` must be set — a policy with
neither is rejected by the server.

## Where to attach a retry policy

| Target | Go | Python |
|---|---|---|
| Activity | `ActivityOptions.RetryPolicy` | `execute_activity(..., retry_policy=...)` |
| Child workflow | `ChildWorkflowOptions.RetryPolicy` | `execute_child_workflow(..., retry_policy=...)` |
| Top-level workflow | `StartWorkflowOptions.RetryPolicy` | `start_workflow(..., retry_policy=...)` |

## Workflow-level timeouts (at start time)

| Concept | Go (`StartWorkflowOptions`) | Python (`start_workflow` kwargs) |
|---|---|---|
| Total execution timeout | `ExecutionStartToCloseTimeout` (required) | `execution_start_to_close_timeout` (required) |
| Decision task timeout | `DecisionTaskStartToCloseTimeout` (default 10s) | `task_start_to_close_timeout` (default 10s) |
| Task list | `TaskList` (required) | `task_list` (required) |
| Workflow ID reuse | `WorkflowIDReusePolicy` | `workflow_id_reuse_policy` |
| Cron (legacy) | `CronSchedule` | `cron_schedule` |
| Batch-start jitter | `JitterStart` (Go only) | *(not exposed — see below)* |

**Jitter for batch starts** is currently a Go-only `StartWorkflowOptions` field
(`JitterStart: 6 * time.Hour`). If you're starting many Python workflows at once and need to avoid a
thundering herd, stagger the calls yourself (e.g. `asyncio.sleep(random...)` between `start_workflow`
calls) since the SDK doesn't expose a native equivalent — see
[../03-python-client/feature-gaps.md](../03-python-client/feature-gaps.md) for other Go-only gaps.

## Debugging timeout/retry issues

See [../06-debugging/timeouts.md](../06-debugging/timeouts.md) and
[../06-debugging/retries.md](../06-debugging/retries.md) for how to tell which timeout fired and how
to read retry attempt counts from `DescribeWorkflowExecution`.
