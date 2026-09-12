# Timers and Schedules

Cadence has two related but distinct durable-time mechanisms: **timers** (wait without holding a
worker thread, inside a running workflow) and **schedules** (recurring workflow *starts*, managed by
the server).

## Timers

A timer lets a workflow durably wait — for a delay, reminder, deadline, or signal timeout — without
occupying a worker thread or process while waiting. The wait survives worker restarts and cache
eviction.

### Lifecycle

1. Workflow code starts a timer -> the worker returns a `StartTimer` decision.
2. Cadence records a `TimerStarted` event and schedules an internal timer task for the expiry time.
3. When the timer task fires, Cadence records `TimerFired` and schedules a decision task.
4. A workflow worker picks up the decision task and resumes the workflow.

Cadence also uses internal (non-user-visible) timer tasks for workflow/decision/activity timeouts,
activity retries, and workflow backoff — these do not show up as `TimerStarted`/`TimerFired` events.

### Cancelling a timer

Create the timer in a cancellable workflow context, then cancel that context:

```go
timerCtx, cancelTimer := workflow.WithCancel(ctx)
timer := workflow.NewTimer(timerCtx, time.Hour)

cancelTimer() // request cancellation

err := timer.Get(ctx, nil) // completes with a cancellation error
```

Cancellation races with expiry: a `TimerFired` event means it fired anyway; `TimerCanceled` means it
was cancelled in time; if the timer already fired, cancellation fails with `CancelTimerFailed`.
Handle both outcomes in workflow code.

### Always use the SDK's timer/sleep API, never the language runtime's

| Client | Simple wait | Timer for composition (e.g. `Selector`) | Never use in workflow code |
|---|---|---|---|
| Go | `workflow.Sleep(ctx, duration)` | `workflow.NewTimer(ctx, duration)` | `time.Sleep`, `time.NewTimer` |
| Python | `await workflow.sleep(duration)` | `workflow.sleep()` (awaitable alongside other work) | `asyncio.sleep`, `time.sleep` |

Native sleeps only run in the worker process's real clock and are **not recorded in history** — if
the worker fails or the workflow replays elsewhere, the sleep cannot be resumed, and racing native
sleeps against signals/cancellation can produce non-deterministic replay decisions. The SDK timer
records its outcome in history so replay uses that recorded outcome instead of the new worker's clock.

### Determinism note

Starting a timer is a recorded decision. Adding, removing, or reordering timers in code that already
has running executions can produce a non-deterministic-workflow error on replay — use workflow
versioning (see [../02-go-client/control-flow.md](../02-go-client/control-flow.md)) before changing
timer behavior for in-flight executions.

Timer expiry is a target, not a latency guarantee — monitor timer-task latency in production.

## Schedules

Schedules are first-class **server-side objects** that run a target workflow on a recurring cadence
— a strict upgrade over the older `CronSchedule` option on `StartWorkflowOptions`, since you can
inspect, pause, update, and backfill a schedule without touching workflow code. Internally, the
server runs a durable scheduler workflow that evaluates the cron expression on each tick, applies the
overlap policy, and starts your target workflow with normal arguments — your target workflow doesn't
need to know it's scheduled.

### Cron expression

Standard 5-field cron (`minute hour day-of-month month day-of-week`), all times UTC:

```
0 9 * * *      # every day at 09:00 UTC
*/15 * * * *   # every 15 minutes
0 18 * * 1-5   # weekdays at 18:00 UTC
```

### Overlap policy — what happens if a new fire arrives while the previous run is still active

| Policy | Behavior |
|---|---|
| `SkipNew` (default) | Skip the new fire; current run continues. |
| `Buffer` | Queue fires, run sequentially. Depth configurable (`BufferLimit`), server ceiling 1000; excess dropped. |
| `Concurrent` | Start every fire regardless of active runs; optionally cap with `--concurrency_limit N` (0 = unlimited). |
| `CancelPrevious` | Cooperatively cancel the current run, then start the new one (current run may take time to actually stop). |
| `TerminatePrevious` | Immediately, unconditionally kill the current run, then start the new one. |

Can be changed live via `UpdateSchedule`; applies to future fires only.

### Pause/unpause and catch-up

Pausing (optionally with a note, e.g. referencing an incident) stops new fires. Unpausing supports a
`--catch_up_policy`:

| Policy | Behavior |
|---|---|
| `Skip` (default) | Resume from now, drop all missed fires. |
| `One` | Dispatch at most one missed fire, then resume from now. |
| `All` | Dispatch all missed fires within the catch-up window, then resume from now. |

If the server itself was down, the catch-up window (default one year) bounds how far back missed
fires are replayed on recovery; older fires are dropped silently.

### Backfill

Manually request fires for an arbitrary past time range (e.g., to process a missed period after an
outage, or backfill runs before the schedule existed). Subject to the overlap policy — with the
default `SkipNew`, a large backfill range will only actually run its first fire; use `Concurrent` or
`CancelPrevious` for a real backfill sweep.

### Schedules vs. plain timers vs. distributed cron

- Use a **timer** for a wait *inside* one workflow execution.
- Use a **Schedule** to start new workflow executions on a recurring cadence, with full server-side
  observability/control.
- Use **distributed cron** (`CronSchedule` on `StartWorkflowOptions`) only for legacy compatibility —
  Schedules are the newer, more capable primitive.
- For repeating work inside one long-running execution without growing its history unbounded,
  combine timers with continue-as-new (see [../02-go-client/control-flow.md](../02-go-client/control-flow.md)).
