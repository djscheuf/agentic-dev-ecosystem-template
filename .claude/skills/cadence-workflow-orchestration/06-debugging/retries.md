# Debugging: Retries

## Reading retry history correctly

- **Activity retries**: Cadence does **not** store history for every failed attempt — only the
  latest attempt is shown, along with an attempt number. Attempt numbers are **0-indexed**:
  `Attempt: 0` is the original try, `Attempt: 1` is the first retry, etc. If you're staring at
  `Attempt: 0` in the Web UI/`DescribeWorkflowExecution` output and expecting to see prior failures,
  they aren't kept — only the current attempt's info is visible via `PendingActivityInfo`.
- **Workflow retries**: a failed/timed-out workflow with a `RetryPolicy` closes the current run with
  a `ContinuedAsNew` event (holding the failure details) and starts a new run at `Attempt: 1`. Look
  at the *previous* run's final event for why it failed, not the new run's history.

## Common misconfigurations that silently disable retry

### `MaximumAttempts: 1`

`MaximumAttempts` **includes the original attempt.** Setting it to `1` means "try once, never
retry" — a very common accidental foot-gun when someone means "retry once" (which is
`MaximumAttempts: 2`).

### `ExpirationInterval` shorter than `InitialInterval`

The first retry waits `InitialInterval` before firing. If `ExpirationInterval` is set lower than
`InitialInterval`, the policy is effectively invalid — the deadline expires before the first retry
would even be scheduled, so **no retry ever happens**, even though a retry policy is technically
configured.

**Fix for both:** always sanity check `MaximumAttempts >= 2` (if you want a retry) and
`ExpirationInterval > InitialInterval`, ideally with enough margin for a few real backoff steps.

### Heartbeat timeout >= StartToClose timeout

If `HeartbeatTimeout` is set equal to or greater than `StartToCloseTimeout`, the `StartToClose`
timeout will always fire first, making the heartbeat timeout dead configuration — you get none of
the "detect a dead worker quickly" benefit that heartbeating is supposed to provide.

**Fix:** set `HeartbeatTimeout` to something meaningfully shorter than `StartToCloseTimeout` —
typically a few minutes, so a dead worker is caught quickly rather than waiting for the whole
activity's close timeout.

## Diagnostic checklist

1. `cadence workflow describe -w <id>` — read `PendingActivityInfo.attemptCount` for an in-progress
   retry.
2. If a policy "isn't retrying," check in this order: `MaximumAttempts` (is it `1`?),
   `ExpirationInterval` vs `InitialInterval` ordering, `NonRetryableErrorReasons` (did the error
   reason match one of these and short-circuit retry on purpose?).
3. If retries are happening but too slowly/quickly, check `BackoffCoefficient` and `MaximumInterval`.
4. Cross-reference with [timeouts.md](timeouts.md) if the *cause* of the failure being retried is
   itself a timeout — heartbeat/retry-policy interplay is the most common source of confusing
   "why didn't this retry sooner" questions.

See [../04-configuration/retry-policies-and-timeouts.md](../04-configuration/retry-policies-and-timeouts.md)
for the full field reference across both SDKs.
