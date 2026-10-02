# Event Handling (Signals) and Synchronous Queries

Cadence workflows interact with the outside world in two complementary ways: **signals** (async,
write) and **queries** (sync, read-only).

## Signals

A signal is a point-to-point async message delivered to one specific running workflow execution.
Signals for a given workflow are always processed **in the order received**.

Common use cases:

- **Event aggregation/correlation per entity.** One workflow instance per business entity (customer,
  device, order) accumulates events over time and acts once a condition is met. Works well when the
  per-entity event rate is bounded — a single workflow has limited throughput, but the number of
  workflows is effectively unlimited. (Don't use Cadence as a substitute for a stream processor like
  Flink/Spark when you need to aggregate *across* entities at high aggregate rate.)
- **Human-in-the-loop tasks.** An activity creates an external task (email, ticket, mobile push).
  When the human acts (submits a form, taps a button), an external system sends a signal to resume
  the workflow. Multiple signal types can represent different actions (claim/return/complete/reject).
- **Altering an in-flight process.** E.g., an order-shipment workflow receiving a signal about a
  changed item quantity, or a deployment workflow being told to pause/rollback/continue mid-rollout.
- **Synchronization.** Because a single workflow execution is strongly consistent, use one workflow
  per key (e.g., per user) and signal it to guarantee sequential processing even if the underlying
  messaging layer delivers out of order.

## Synchronous queries

Queries expose a workflow's live in-memory state to external callers via a synchronous read-only
callback. Multiple named query handlers can be exposed per workflow type.

**Constraints on query handlers:**
- Must be **read-only** — cannot mutate workflow state.
- Must be **non-blocking** — cannot invoke activities or otherwise block.

An external client calls a query with `(domain, workflowID, queryName, [args])` and gets a synchronous
response.

### Built-in stack trace query

Every Cadence client exposes a built-in `__stack_trace` query that dumps the stacks of all
workflow-owned coroutines/threads — extremely useful for diagnosing a stuck workflow in production
without instrumenting your own query:

```bash
cadence --do samples-domain wf query -w <workflowID> -qt __stack_trace
```

See [../06-debugging/troubleshooting-playbook.md](../06-debugging/troubleshooting-playbook.md) for
using this in a debugging flow.

### Signal vs. Query cheat sheet

| | Signal | Query |
|---|---|---|
| Direction | External -> Workflow | External -> Workflow -> response |
| Mutates state? | Yes (indirectly, via workflow logic) | No |
| Recorded in history? | Yes | No |
| Can block/call activities? | The workflow code handling it can | No |
| Delivery order | FIFO per workflow | N/A (point read) |
