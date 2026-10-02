---
name: cadence-workflow-orchestration
description: Build, configure, and debug durable Cadence workflows and activities for local development. Covers core concepts, the Go and Python client SDKs, worker/client configuration, the CLI and HTTP API, and troubleshooting for workflow orchestration.
---

# Cadence Workflow Orchestration

## What is Cadence?

Cadence is an open-source **fault-oblivious stateful programming model**: a durable virtual memory
that is not tied to a specific process and preserves full application state — including function
stacks and local variables — across host and software failures. You write ordinary code; Cadence
guarantees it keeps running (and resumes exactly where it left off) even if the process, host, or
network fails.

A Cadence application is composed of **Workflows** (durable orchestration code) and **Activities**
(the actual side effects: API calls, DB writes, file I/O). **Workers** are processes you run that
host your Workflow and Activity code and poll the Cadence service for work. The **Cadence service**
(frontend/history/matching) is the stateless backend that stores workflow state and durable timers,
backed by Cassandra/MySQL/PostgreSQL. **External clients** (your app code, a CLI, a UI) start, signal,
query, and cancel workflow executions via the service's gRPC API.

Official SDKs: **Go** and **Java** (production-ready). Community SDKs: **Python** and **Ruby**. This
skill covers **Go** and **Python** client development for local workflow/activity authoring, testing,
and debugging. It does not cover production cluster operations (multi-node deployment, Cassandra/
Elasticsearch tuning, cross-DC replication) — see the [Operation Guide](https://cadenceworkflow.io/docs/operation-guide)
upstream for that.

---

## Glossary

- **Workflow**: Deterministic orchestration code that survives crashes by replaying its **Event
  History**. Workflows delegate all side effects to Activities.
- **Activity**: A normal function that performs one side effect (HTTP call, DB write, file I/O).
  Runs in a standard runtime, is retried on failure, and should be idempotent.
- **Worker**: A long-lived process that connects to the Cadence service, registers Workflow/Activity
  implementations, polls a **Task List**, and executes the tasks it receives.
- **Task List**: A named queue the Cadence service uses to dispatch **Decision Tasks** (to run/resume
  a workflow) and **Activity Tasks** (to run an activity) to Workers.
- **Decision Task**: A unit of work delivered to a workflow worker telling it to advance a workflow.
- **Domain**: A logical isolation boundary for workflows, registered via the CLI or API before you
  can run anything in it.
- **Workflow Execution**: One running instance of a Workflow, identified by a `WorkflowID` and
  `RunID`, with an immutable Event History used to recover state after a crash.
- **Determinism**: A Workflow function must produce the same sequence of decisions on every replay.
  No direct `time.Now()`, random numbers, network calls, or unordered goroutine/thread scheduling —
  use the SDK's deterministic equivalents (`workflow.Now`, `workflow.SideEffect`, `workflow.Channel`,
  `workflow.Selector` in Go).
- **Idempotency**: Activities may run more than once (retries), so their side effects should be safe
  to repeat.
- **Retry Policy**: Governs how failed Activity (and, since decision failures are handled
  differently, Workflow) executions are retried: initial interval, backoff coefficient, max interval,
  max attempts.
- **Heartbeat**: A periodic "still alive" signal from a long-running Activity to the service; can also
  checkpoint progress and deliver cancellation.
- **Signal**: An async message sent into a running Workflow Execution.
- **Query**: A synchronous, read-only request against a running Workflow Execution's in-memory state.
- **Continue-As-New**: A workflow atomically completes its current run and starts a new run with a
  fresh Event History, used to keep long-running/looping workflows' histories small.
- **Cadence Service**: The cluster (Frontend / History / Matching / Internal Worker services) that
  stores workflow state and routes tasks. Locally, a single `cadence-server` process backed by
  embedded SQLite is sufficient.

---

## Key Mental Models

### Workflows orchestrate, Activities do the work

Workflow code is replayed from Event History to recover state, so it must be deterministic and must
not perform side effects directly. Everything non-deterministic — I/O, randomness, wall-clock time —
belongs in an Activity, invoked and awaited from the workflow.

### Workers are the only thing you deploy

The Cadence service never runs your code. You write and run Worker processes that register your
Workflow/Activity implementations and poll a Task List. One Worker process can host many workflow
types and activity types; many Worker processes can poll the same Task List for horizontal scaling.

### How the pieces fit together

```
Client -> StartWorkflowExecution (domain, task list, workflow type, input)
              |
              v
Cadence Service (Frontend -> History -> Matching)
              |
              v
Worker polls Task List -> executes Workflow code -> decides to run Activity "charge"
              |
              v
Cadence Service schedules an Activity Task on the Task List
              |
              v
Worker (same or different process) polls Task List -> executes Activity "charge"
              |
              v
Result recorded in Event History -> Workflow resumes
```

### Local dev loop

Cadence ships an embedded-SQLite server for zero-dependency local development (no Docker or
Cassandra required). See [00-get-started/local-quickstart.md](00-get-started/local-quickstart.md).

---

## When to Use Cadence

### Good fit
- Long-running business processes that must survive crashes (order fulfillment, onboarding,
  provisioning, data pipelines).
- Processes with long delays or human-in-the-loop steps (hours to months).
- Orchestration of unreliable third-party APIs needing retries/timeouts/compensation (Sagas).
- Complex state machines with branching and timeout logic.

### Not a good fit
- Latency-sensitive real-time request/response paths — every decision round-trips the service.
- Simple CRUD APIs with no durability requirement.
- Anything where in-memory state with no recovery guarantee is acceptable.

---

## How to Use This Skill (Progressive Disclosure)

This skill is an index. Read this file first, then jump to the specific page you need — don't read
the whole tree. Use the table below to route yourself.

| I want to...                                              | Go to |
|-------------------------------------------------------------|-------|
| Run a local Cadence server and my first workflow            | [00-get-started/local-quickstart.md](00-get-started/local-quickstart.md) |
| Understand workflows, activities, task lists, topology      | [01-concepts/](01-concepts/) |
| Write/debug a workflow or worker in **Go**                  | [02-go-client/](02-go-client/) |
| Write/debug a workflow or worker in **Python**               | [03-python-client/](03-python-client/) |
| Configure workers, timeouts, retries, or client connections | [04-configuration/](04-configuration/) |
| Use the `cadence` CLI or the HTTP API directly               | [05-api-and-cli/](05-api-and-cli/) |
| Diagnose a stuck, timed-out, or failing workflow             | [06-debugging/](06-debugging/) |
| Copy a minimal runnable example                              | [examples/go/](examples/go/), [examples/python/](examples/python/) |

### 01-concepts/
- [workflows.md](01-concepts/workflows.md) — determinism, decisions, the fault-oblivious model
- [activities.md](01-concepts/activities.md) — semantics, retries, heartbeats, idempotency
- [events-and-queries.md](01-concepts/events-and-queries.md) — event handling, synchronous queries
- [task-lists.md](01-concepts/task-lists.md) — how work is routed to workers
- [timers-and-schedules.md](01-concepts/timers-and-schedules.md) — durable timers, cron, schedules
- [topology.md](01-concepts/topology.md) — service components, workers, external clients

### 02-go-client/ (production-ready, most mature SDK)
- [workflows-and-workers.md](02-go-client/workflows-and-workers.md)
- [activities.md](02-go-client/activities.md)
- [child-workflows-and-messaging.md](02-go-client/child-workflows-and-messaging.md)
- [control-flow.md](02-go-client/control-flow.md) — continue-as-new, side effect, sleep, versioning
- [error-handling-and-retries.md](02-go-client/error-handling-and-retries.md)
- [testing-and-replay.md](02-go-client/testing-and-replay.md)
- [sessions-and-tracing.md](02-go-client/sessions-and-tracing.md)

### 03-python-client/ (community SDK — check [feature-gaps.md](03-python-client/feature-gaps.md) first)
- [setup-and-workers.md](03-python-client/setup-and-workers.md)
- [workflows-and-activities.md](03-python-client/workflows-and-activities.md)
- [messaging.md](03-python-client/messaging.md) — signals, queries, child workflows
- [retries-and-error-handling.md](03-python-client/retries-and-error-handling.md)
- [control-flow.md](03-python-client/control-flow.md) — continue-as-new, cron, schedules
- [testing.md](03-python-client/testing.md)
- [feature-gaps.md](03-python-client/feature-gaps.md) — what Python does **not** yet support vs Go

### 04-configuration/
- [worker-options.md](04-configuration/worker-options.md)
- [retry-policies-and-timeouts.md](04-configuration/retry-policies-and-timeouts.md)
- [client-connection.md](04-configuration/client-connection.md)
- [local-server-config.md](04-configuration/local-server-config.md)

### 05-api-and-cli/
- [cli-reference.md](05-api-and-cli/cli-reference.md)
- [http-api.md](05-api-and-cli/http-api.md)

### 06-debugging/
- [timeouts.md](06-debugging/timeouts.md)
- [activity-failures.md](06-debugging/activity-failures.md)
- [retries.md](06-debugging/retries.md)
- [non-deterministic-errors.md](06-debugging/non-deterministic-errors.md)
- [troubleshooting-playbook.md](06-debugging/troubleshooting-playbook.md)

---

## Source

All content in this skill is derived from the official Cadence docs at
[cadenceworkflow.io/docs](https://cadenceworkflow.io/docs/get-started) (retrieved 2026-08-25). If
something here seems stale or you need an API not covered, check the live docs — this skill trades
completeness for being fast to load; it is not a full mirror.
