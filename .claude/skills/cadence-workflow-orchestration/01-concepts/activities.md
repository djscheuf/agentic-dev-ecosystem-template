# Activities

Activities are where all non-deterministic, side-effecting work happens: HTTP calls, DB writes, file
I/O. Unlike workflows, Cadence does **not** recover activity state on failure — an activity function
can contain any code without restriction, but if it fails or is interrupted mid-execution, Cadence's
answer is to retry it, not resume it, so activities must be **idempotent**.

Activities are dispatched asynchronously through **Task Lists**: the workflow requests execution, the
service places an `ActivityTask` on a task list, and any available worker polling that task list picks
it up, runs it, and reports the result back.

## Timeouts

Cadence imposes no system limit on activity duration — you choose the timeouts:

| Timeout | Meaning |
|---|---|
| `ScheduleToStart` | Max time from the workflow requesting the activity to a worker starting it. Fires mainly when all workers are down or backlogged. |
| `StartToClose` | Max time the activity can run once a worker picks it up. |
| `ScheduleToClose` | Max end-to-end time from request to completion (covers both of the above plus retries). |
| `Heartbeat` | Max allowed time between heartbeat calls for a long-running activity. |

You must specify either `ScheduleToClose`, or both `ScheduleToStart` and `StartToClose`.

## Retries

Activities support automatic retry via a `RetryPolicy`:

- `InitialInterval` — delay before the first retry.
- `BackoffCoefficient` — exponential growth factor (1 = constant interval).
- `MaximumInterval` — cap on the retry interval.
- `MaximumAttempts` — hard cap on attempts (mutually substitutable with `ExpirationInterval`).
- `ExpirationInterval` — hard cap on total retry duration.
- `NonRetryableErrorReasons` — error types that should fail immediately without retry (e.g. invalid
  argument errors).

If retries are exhausted, the error propagates back to the calling workflow, which decides what to do
next (compensate, fail the workflow, try an alternative path).

## Long-running activities and heartbeats

For long-running activities, set a relatively short `Heartbeat` timeout and call the heartbeat API
periodically from inside the activity. This lets Cadence detect a dead worker within seconds rather
than waiting for `StartToClose`/`ScheduleToClose` to expire. A heartbeat call can carry an
application-defined payload to checkpoint progress — on retry, the next attempt can read that payload
and resume from where it left off instead of starting over.

This pattern also supports a lightweight leader-election-like use case: an activity loops, polls a
condition, and heartbeats each iteration; if its worker dies, the activity times out on missed
heartbeat and is retried elsewhere. (Not suitable for sub-second real-time needs — Cadence timeouts
are second-resolution.)

## Cancellation

A workflow can request cancellation of an activity it started. The *only* way an activity currently
learns it was cancelled is through a failed heartbeat call (the heartbeat request itself returns a
cancellation error) — so an activity that wants to be cancellable must heartbeat. It is then
responsible for its own cleanup; the workflow decides whether to wait for confirmation or move on.
The same mechanism fires if the invoking workflow has already completed.

## Task list routing (why you'd use more than one)

Multiple activity task lists in one workflow let you:

- **Flow-control** work — a worker only polls when it has spare capacity, so it's never overloaded.
- **Throttle** per-worker or globally (server-side rate limiting per task list), often to protect a
  downstream dependency.
- **Deploy independently** — a separately-deployable activity-hosting service gets its own task list.
- **Route by capability** — e.g., GPU vs non-GPU workers.
- **Route to a specific host/process** — e.g., download/transform/upload must run on the same host;
  activities that share an in-memory cache must land on the same process.
- **Prioritize** — one task list (and worker pool) per priority tier.
- **Version** — a backwards-incompatible activity implementation can use a new task list.

## Asynchronous activity completion

Normally an activity completes when its function returns. If the real work is handed off to an
external system (e.g., forwarded over a message queue, completed by a webhook), the activity can
instead be completed later via a separate "complete activity" API call — from any process, even in a
different language than the original worker.

## Local activities

For very short-lived activities that don't need task-list queuing/flow-control/routing, Cadence
supports **local activities**, executed in-process by the same worker running the workflow. Trade-offs:

- Less debuggability — no `ActivityTaskScheduled`/`ActivityTaskStarted` history events.
- No task-list dispatch — always runs on the same worker as the workflow decision.
- Higher chance of duplicate execution (result isn't recorded to history until the decision task
  completes).
- No long-running/heartbeat support, no global task-list rate limiting.

Good candidates: idempotent, sub-few-seconds, no need for routing/global rate limiting, safe to run
in the same binary as the workflow, non-business-critical (e.g. logging, loading config) — or when
many timers fire simultaneously and you need to avoid overloading the Cadence service with a burst of
regular activity scheduling.
