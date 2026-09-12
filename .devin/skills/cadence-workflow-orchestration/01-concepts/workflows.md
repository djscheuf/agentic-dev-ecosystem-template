# Workflows

## The core abstraction: fault-oblivious stateful functions

A Cadence Workflow is ordinary application code that Cadence makes durable: local variables,
in-progress loops, and blocked waits all survive process crashes, host failures, and Cadence service
downtime. You do not write retry/checkpoint plumbing — you write the business logic directly, and it
is safe to `sleep` for 30 days or block on a slow downstream call for an entire day inside workflow
code.

**The workflow author never has to answer "what if my worker crashes mid-execution?"** As soon as a
worker (any worker, not necessarily the same process) recovers and the workflow needs to handle the
next event (a timer firing, an activity completing, a signal arriving), Cadence fully restores the
workflow's state and continues it. The *only* thing that fails a workflow is the workflow's own
business logic throwing an unhandled exception — never infrastructure outages.

A worker can also safely evict a blocked (not actively running) workflow from memory/cache; it gets
resurrected on demand when an external event arrives. This is why a single worker process can service
millions of open workflow executions even though it can only hold a small working set in memory at
once.

## State recovery and determinism

Workflow state recovery uses **event sourcing**: Cadence replays the recorded Event History to
reconstruct workflow state after any interruption. This requires workflow code to be **deterministic**
— it must produce the exact same sequence of decisions every time it's executed with the same history.
Concretely, this rules out:

- Direct external API/network calls (must go through an Activity)
- Native language randomness or wall-clock time (use the SDK's deterministic equivalents)
- Native sleep/threading primitives (use the SDK's workflow-context timer/goroutine equivalents)

All communication with the outside world must happen through **Activities** (see
[activities.md](activities.md)).

## Workflow ID, Run ID, and uniqueness

- `WorkflowID` is client-assigned, usually a business-meaningful ID (customer ID, order ID).
- Cadence guarantees **only one open workflow with a given `WorkflowID` per domain at a time**,
  across all workflow types. Starting a duplicate fails with `WorkflowExecutionAlreadyStarted`.
- `RunID` is a server-assigned UUID that disambiguates multiple runs (e.g., via retry or
  continue-as-new) of the same `WorkflowID`. A workflow execution is uniquely identified by the
  triple `(Domain, WorkflowID, RunID)`.
- Starting a workflow when a *previous* run with the same ID has already completed is governed by
  `WorkflowIdReusePolicy`:
  - `AllowDuplicateFailedOnly` (default) — only if the prior run failed.
  - `AllowDuplicate` — always allowed regardless of prior completion status.
  - `RejectDuplicate` — never allowed, even after completion.
  - `TerminateIfRunning` — terminate the current run (if any) and start fresh.

## Child workflows

A workflow can start other workflows as children; a child's completion/failure is reported back to
its parent. Use child workflows to:

- Host logic on a separate worker pool (acts like an independently deployable service).
- Partition work around Cadence's per-workflow size limits (e.g., 1000 children x 1000 activities
  each = 1M activities instead of one workflow trying to run 1M activities).
- Manage a resource under a stable ID for serialization (one child per host/resource, `WorkflowID` =
  resource name).
- Run periodic logic without growing the parent's history (child loops via continue-as-new; parent
  just sees one child invocation).

Parent and child workflows share **no state** — they can only communicate via asynchronous signals.
**Default to a single workflow** unless your problem has unbounded size or needs independent
worker pools; child workflows add complexity.

## Workflow-level retries

A workflow can optionally specify a retry policy at start time, distinct from per-Activity retries.
If the workflow fails (unhandled exception, or an activity failure not handled by application code),
Cadence restarts it from the beginning after a computed backoff. Parameters mirror Activity retry
policies (see [activities.md](activities.md)): `InitialInterval`, `BackoffCoefficient`,
`MaximumInterval`, `MaximumAttempts` or `ExpirationInterval`, and `NonRetryableErrorReasons`.

Use workflow-level retry only for whole-workflow restarts; if only *part* of a workflow needs to be
retried atomically as a group of activities (e.g., "download, transform, upload must all rerun on the
same host if the host dies"), implement that retry loop explicitly in the workflow code — Cadence has
no equivalent of a "retry this block" primitive.
