# Troubleshooting Playbook: "My Workflow Is Stuck / Failed / Behaving Wrong"

A single entry point that routes you to the right detailed page, plus the CLI commands to gather
evidence fast.

## Step 0: Gather the basics

```bash
cadence workflow describe -w <workflowID> -r <runID>   # status, pending activity/decision info
cadence workflow show    -w <workflowID> -r <runID>     # full event history
cadence tasklist desc --tl <task-list-name>              # confirm pollers exist
```

If you don't have a `runID`, omit `-r` to get the latest run.

## Step 1: What does `describe` say the workflow is doing right now?

| `describe` shows... | Go to |
|---|---|
| `PendingActivityInfo` with a growing `attemptCount` | [retries.md](retries.md), then [timeouts.md](timeouts.md) |
| Workflow `OPEN` but no pending activity/decision, no progress | [timeouts.md](timeouts.md) (§ missing pollers) — check `tasklist desc` |
| Workflow `CLOSED` with status `FAILED` | [activity-failures.md](activity-failures.md) if an activity failed; otherwise read the closing event in `show` |
| Workflow `CLOSED` with status `TIMED_OUT` | [timeouts.md](timeouts.md) |
| A non-deterministic-error message anywhere in history/logs | [non-deterministic-errors.md](non-deterministic-errors.md) |

## Step 2: Query live state without disturbing anything

If the workflow defines query handlers (or just use the built-in stack trace query):

```bash
cadence workflow query -w <workflowID> -qt __stack_trace   # dump goroutine/coroutine stacks
cadence workflow query -w <workflowID> -qt <your_query>     # e.g. get_status
```

This is often the fastest way to see exactly where a workflow is blocked (waiting on an activity,
a timer, a signal) without needing to parse the raw event history.

## Step 3: Read the event history for the actual failure point

```bash
cadence workflow show -w <workflowID> -r <runID>
```

Look for the last few events before the workflow stopped progressing:
- `ActivityTaskScheduled` with no matching `...Started`/`...Completed` -> stuck waiting for a worker
  ([timeouts.md](timeouts.md), missing pollers).
- `ActivityTaskFailed` -> [activity-failures.md](activity-failures.md).
- `ActivityTaskTimedOut` -> [timeouts.md](timeouts.md); check the `TimeoutType`.
- `DecisionTaskFailed` repeatedly -> possible non-deterministic error or a workflow-code panic; see
  [non-deterministic-errors.md](non-deterministic-errors.md).
- `WorkflowExecutionTimedOut` -> the overall `ExecutionStartToCloseTimeout` expired; check whether
  individual steps or the whole flow is slower than expected.

## Step 4: If this looks like a bad deploy (code change), suspect non-determinism first

If the workflow was running fine before a recent deploy and now fails/hangs on replay:

1. Go straight to [non-deterministic-errors.md](non-deterministic-errors.md).
2. Download the history and replay it locally against both the old and new code (Go only — see
   [../02-go-client/testing-and-replay.md](../02-go-client/testing-and-replay.md)) to confirm exactly
   which code change broke compatibility.
3. Decide: version the change (`workflow.GetVersion`), reset the workflow to before the incompatible
   point, or drain/terminate and let it restart clean.

## Step 5: If retries seem broken (not firing, firing forever, firing too fast/slow)

Go straight to [retries.md](retries.md) — the two most common causes
(`MaximumAttempts: 1` accidentally meaning "no retry," and `HeartbeatTimeout >= StartToCloseTimeout`
making heartbeating a no-op) account for the majority of "why isn't this retrying" questions.

## Step 6: If nothing above explains it — escalate to server-side / cluster-level

This skill intentionally does not cover production cluster operations (see
[../00-get-started/local-quickstart.md](../00-get-started/local-quickstart.md) for local dev's
narrower server troubleshooting). For cluster health, persistence store issues, or cross-DC
replication problems, see the upstream
[Operation Guide](https://cadenceworkflow.io/docs/operation-guide) — outside this skill's scope by
design.

## Quick reference: which CLI verb answers which question

| Question | Command |
|---|---|
| Is anything polling this task list? | `cadence tasklist desc --tl <name>` |
| What's this workflow doing right now? | `cadence workflow describe -w <id>` |
| What happened, in order? | `cadence workflow show -w <id>` |
| What's its live internal state? | `cadence workflow query -w <id> -qt __stack_trace` (or a custom query) |
| Can I unstick it without losing everything? | `cadence workflow reset -w <id> ...` |
| Do I just need to kill it? | `cadence workflow terminate -w <id>` |

See [../05-api-and-cli/cli-reference.md](../05-api-and-cli/cli-reference.md) for full flag details on
every command above.
