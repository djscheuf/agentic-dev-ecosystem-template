# Debugging: Non-Deterministic Workflow Errors

## Root cause

Cadence workflows must be deterministic because their state is recovered by **replaying history**,
not by persisting live process state. When a workflow's worker/host dies (or a workflow is simply
long-running enough to move between workers), Cadence:

1. Picks up the workflow on a new host (**change of ownership**).
2. That host has no in-memory state — it must **replay** every historical decision task by re-running
   the current workflow code against the recorded Event History from the beginning.
3. If the current code's decisions at any point diverge from what's recorded in history (a different
   activity, a different branch, activities in a different order, etc.), Cadence raises a
   **non-deterministic error** for that workflow.

This is fundamentally a **history replay** problem, not a "this specific worker had a bug" problem —
it happens because you changed the *code* out from under an execution that's still in-flight and
whose history was recorded against the *old* code.

## Decision tasks: the mechanism

Every meaningful step a workflow takes (start, schedule activity, activity result arrives, timer
fires, signal arrives, etc.) is recorded as a sequence of history events —
`DecisionTaskScheduled` / `DecisionTaskStarted` / `DecisionTaskCompleted`, interleaved with
`ActivityTaskScheduled` / `...Started` / `...Completed`, `TimerStarted` / `...Fired`, and so on.
During replay, if Cadence finds a decision task already recorded for a given step, it returns the
recorded value instead of re-executing that step's logic from scratch. This is exactly why an
incompatible code change breaks replay: the recorded decision task at position N was "call
ActivityA," but the new code tries to schedule "ActivityC" at that same position — mismatch, replay
fails.

## What typically causes this

- Replacing/reordering/adding/removing an activity call in a workflow that has running executions
  (see the example in [../02-go-client/control-flow.md](../02-go-client/control-flow.md#the-problem)).
- Adding/removing/reordering a timer for a workflow with in-flight executions (see
  [../01-concepts/timers-and-schedules.md](../01-concepts/timers-and-schedules.md#determinism)).
- Introducing a native (non-SDK) source of non-determinism: `time.Now()`, `random`, raw
  goroutines/threads/`asyncio.create_task()`, map iteration order in Go, direct I/O in workflow code.
- Changing signal/query handler registration in a way that changes how buffered/pending
  signals are processed relative to history.

## How to fix it going forward

- **Use `workflow.GetVersion()`** (Go) to branch old vs. new logic so in-flight executions keep
  taking the old path while new executions take the new path — see
  [../02-go-client/control-flow.md](../02-go-client/control-flow.md#versioning-workflowgetversion).
  (Python has no equivalent yet — see
  [../03-python-client/feature-gaps.md](../03-python-client/feature-gaps.md); prefer draining old
  executions or introducing a new `WorkflowType` instead.)
- **Or**, if you don't need in-flight executions to survive, drain/terminate them before deploying
  the incompatible change.
- **Or**, define the changed logic as a new `WorkflowType` and point new starts at it, leaving old
  executions running against the old type.

## How to catch it *before* it hits production

Don't wait for a live workflow to hit this — validate the change against real recorded history
first:

- **Go**: use the [Workflow Replayer](../02-go-client/testing-and-replay.md#workflow-replayer) to
  replay a downloaded history file (or fetch directly from the server) against your new code, in a
  fast local/CI test. For broad coverage across many in-flight executions, use the
  [Workflow Shadower](../02-go-client/testing-and-replay.md#workflow-shadower).
- **Python**: no replayer/shadower equivalent exists yet. Mitigate with extra caution around any
  change to a workflow function's control flow (see
  [../03-python-client/feature-gaps.md](../03-python-client/feature-gaps.md)) — prefer draining
  in-flight executions or shipping the change as a new `WorkflowType`.

## Diagnostic flow when you already hit the error

1. Find the failing workflow: `cadence workflow show -w <id>` — look for where replay diverges (the
   error usually names the mismatched event type/attributes).
2. Identify what code changed between when this execution started and now (git log on the workflow
   file, deployment history).
3. If it's an activity/timer/branching change: wrap it in `workflow.GetVersion()` (Go) matching the
   pattern in [../02-go-client/control-flow.md](../02-go-client/control-flow.md), redeploy, and let
   the in-flight execution recover.
4. If you can't recover it in place, consider `cadence workflow reset` to roll the execution back to
   a point before the incompatible change took effect (see
   [../05-api-and-cli/cli-reference.md](../05-api-and-cli/cli-reference.md#workflow-operations)), or
   terminate it if it's not recoverable/needed.
5. Add a Replayer test (Go) so this specific regression can't recur silently.
