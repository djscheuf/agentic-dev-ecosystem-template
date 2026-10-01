# Python Client: Feature Gaps vs. Go

The Python client is a **community SDK**, not one of the two officially-supported clients (Go and
Java). Check this table before assuming a Go-client pattern has a Python equivalent.

## Feature coverage (as published by the Cadence docs)

| Feature | Supported in Python? |
|---|---|
| Workers and task lists | Yes |
| Workflow definition and registration | Yes |
| Starting, signaling, querying, cancelling workflows | Yes |
| Activities with retry and heartbeat | Yes |
| Child workflows | Yes |
| Signals (inbound and outbound) | Yes |
| Queries | Yes |
| Retry policies | Yes |
| Continue-as-new | Yes |
| Sleep and wait conditions | Yes |
| Distributed cron | Yes |
| Schedules | Yes |
| In-memory workflow testing (`TestWorkflowEnvironment`) | Yes |
| **Workflow versioning** (`GetVersion` equivalent) | **Not yet** |
| **Side effects** (`SideEffect` equivalent) | **Not yet** |
| **Activity async completion** | **Not yet** |
| **Sessions** | **Not yet** |

## What this means in practice

- **No versioning primitive**: you cannot use a `workflow.GetVersion()`-style guard to safely evolve
  workflow code while old executions are in flight (see the Go client's
  [control-flow.md](../02-go-client/control-flow.md#versioning-workflowgetversion) for what you'd be
  missing). Until this lands, treat in-flight Python workflow executions as **fragile to code
  changes** — prefer draining old executions (or using continue-as-new to roll them onto new code at
  a clean boundary) over hot-patching workflow logic with running executions in flight.
- **No `SideEffect`**: there's no sanctioned way to record a one-off non-deterministic value (random
  number, UUID) directly in workflow code. Push that into an **Activity** instead — slightly more
  overhead, but replay-safe today.
- **No async activity completion**: an activity must complete by returning from its function. If you
  need to hand work off to an external system and complete later from a different process, you
  cannot do that from Python yet — either poll from inside a long-running/heartbeating activity, or
  implement that specific activity in Go/Java and call it from a Python-orchestrated workflow (mixed
  clients against the same Cadence service work fine, since they share the same wire protocol).
- **No sessions**: no built-in mechanism to pin a sequence of activities to the same worker process.
  If you need host/process affinity (e.g., all three steps of a file-processing pipeline must run on
  the same machine), you'll need to implement your own routing via a dedicated task list per
  worker/host (see [../01-concepts/activities.md](../01-concepts/activities.md#task-list-routing-why-youd-use-more-than-one)),
  since the session framework itself isn't available.
- **No replay/shadow testing tools**: see [testing.md](testing.md) — there's no Python equivalent of
  the Go client's Workflow Replayer/Shadower yet for catching non-deterministic changes against real
  history before deploying.

## When to reach for Go instead

If your use case needs any of the above four gaps, and you can't work around them with the patterns
above, prefer writing that specific workflow/activity in Go (see [../02-go-client/](../02-go-client/))
even in an otherwise Python-centric codebase — the Cadence wire protocol is language-agnostic, so
Go and Python workers/clients can coexist against the same domain and even signal/query each other's
workflows.
