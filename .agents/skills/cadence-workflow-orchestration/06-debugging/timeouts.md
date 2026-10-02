# Debugging: Timeouts

A workflow fails when an activity times out (and isn't retried away) or when the workflow's own
execution timeout expires. Below are the common root causes, in the order to check them.

## 1. Missing pollers

**Symptom:** Tasks never seem to be picked up; `tasklist desc` shows no pollers.

Workers have two poller types — activity pollers and decision (workflow) pollers — each polling a
specific task list. If no worker is polling the task list your workflow/activity is scheduled on,
nothing progresses, and eventually `ScheduleToStartTimeout` fires.

**Check:**
```bash
cadence tasklist desc --tl <task-list-name>
```
**Fix:** make sure a running worker is registered with the exact same task list name used by the
workflow/activity options. See
[../02-go-client/workflows-and-workers.md](../02-go-client/workflows-and-workers.md) /
[../03-python-client/setup-and-workers.md](../03-python-client/setup-and-workers.md).

## 2. Task list backlog despite having pollers

**Symptom:** Pollers exist, but the backlog keeps growing.

This is a supply/demand problem — tasks are arriving faster than your workers can process them.

**Fix:** scale out (more worker processes/instances) and/or increase pollers per worker (Go:
`worker.Options.MaxConcurrentActivityTaskPollers`/`MaxConcurrentDecisionTaskPollers`, or better, enable
the [Worker AutoScaler](../04-configuration/worker-options.md#worker-autoscaler) instead of manually
tuning poller counts).

## 3. No heartbeat timeout or retry policy on a long-running activity

**Symptom:** A long-running activity's worker died mid-execution, but the workflow just sits there
until `StartToCloseTimeout`/`ScheduleToCloseTimeout` finally fires — much later than you'd expect.

Cadence has no way to know a worker died unless the activity heartbeats. Without a `HeartbeatTimeout`,
a dead worker's activity is only noticed once the (usually much longer) close timeout expires.

**Fix:** configure `HeartbeatTimeout` and call `RecordActivityHeartbeat` periodically (see
[../02-go-client/activities.md](../02-go-client/activities.md#heartbeating) /
[../03-python-client/workflows-and-activities.md](../03-python-client/workflows-and-activities.md#heartbeating)),
plus a retry policy so the activity actually gets rescheduled after the heartbeat timeout fires.

## 4. Retry policy configured without heartbeat timeout

Same root cause as #3 from a different angle: a `RetryPolicy` alone doesn't help a long-running
activity recover quickly from a dead worker — the retry only kicks in *after* `StartToClose`/
`ScheduleToClose` expires, because there's no heartbeat to notice the worker died sooner.

**Fix:** add `HeartbeatTimeout` alongside the retry policy for any activity that runs long enough for
a worker restart to plausibly happen mid-execution.

## 5. Heartbeat timeout configured without a retry policy

Heartbeat timeout alone makes Cadence *detect* a dead worker faster, but without a retry policy the
activity is never rescheduled onto a healthy worker — it just fails.

**Fix:** always pair `HeartbeatTimeout` with a `RetryPolicy`.

## 6. Heartbeat timeout actually firing after being configured

If you see a `TimeoutType_HEARTBEAT` failure after adding heartbeating, it means the server didn't
receive a heartbeat within the configured interval. Two possibilities:

- The activity really did die/stall — this is the heartbeat timeout doing its job (good: you now
  fail fast instead of waiting for `StartToClose`/`ScheduleToClose`).
- The activity is alive but not actually calling the heartbeat API often enough.

**Fix for the second case:** call `activity.RecordHeartbeat`/`activity.heartbeat()` more frequently
inside your loop, or in Go, register the activity with `EnableAutoHeartbeat: true` so the client
heartbeats automatically in the background even if you don't call it yourself.

## Also check: retry misconfiguration masking a timeout as "never retries"

See [retries.md](retries.md) — a `MaximumAttempts: 1` or a mis-ordered `ExpirationInterval` vs.
`InitialInterval` can make a policy silently retry zero times, which looks like a timeout with "no
retry" even though a policy was configured.

## General diagnostic flow

1. `cadence workflow describe -w <id>` — check `PendingActivityInfo` for attempt count and which
   timeout is pending.
2. `cadence tasklist desc --tl <name>` — confirm pollers exist.
3. `cadence workflow show -w <id>` — read the history for `ActivityTaskTimedOut` /
   `DecisionTaskTimedOut` events and their `TimeoutType`.
4. Cross-reference the timeout type against [../01-concepts/activities.md](../01-concepts/activities.md#timeouts).
