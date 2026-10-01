# Go: Child Workflows, Signals, and Queries

## Choosing the right building block

| Option | When to use it |
|---|---|
| **Activity** | The work is a single non-deterministic operation (API call, DB write, email). Lowest overhead, independently retried. |
| **Child Workflow** | You need reusable, self-contained orchestration with its own Event History, timeouts, retry policy — but its lifecycle is still tied to the parent. |
| **Standalone Workflow** | The process should be fully independent of the caller's lifecycle. Start it as a top-level execution via `client.Client` instead of a child. |

## Starting a child workflow

```go
cwo := workflow.ChildWorkflowOptions{
    WorkflowID:                   "BID-SIMPLE-CHILD-WORKFLOW", // omit to auto-generate
    ExecutionStartToCloseTimeout: time.Minute * 30,
}
ctx = workflow.WithChildOptions(ctx, cwo)

future := workflow.ExecuteChildWorkflow(ctx, SimpleChildWorkflow, value)
```

The child is only **scheduled** by this call — it doesn't actually start executing until the parent
yields control back to Cadence (matters if the parent might finish quickly right after — see
`ParentClosePolicy` below).

### Waiting for a result / running children in parallel

```go
var result string
if err := future.Get(ctx, &result); err != nil {
    return err
}
```

```go
child1 := workflow.ExecuteChildWorkflow(ctx, GreetingChild, "Hello", name)
child2 := workflow.ExecuteChildWorkflow(ctx, GreetingChild, "Bye", name)

var g1, g2 string
if err := child1.Get(ctx, &g1); err != nil { return err }
if err := child2.Get(ctx, &g2); err != nil { return err }
```

### Signaling a running child

```go
var childWE workflow.Execution
if err := future.GetChildWorkflowExecution().Get(ctx, &childWE); err != nil {
    return err
}
if err := workflow.SignalExternalWorkflow(
    ctx, childWE.ID, childWE.RunID, "updateName", "Cadence",
).Get(ctx, nil); err != nil {
    return err
}
```

**A parent cannot query a child from workflow code.** Queries must come from an activity or an
external process using a `client.Client` stub.

### What happens to a child when the parent closes

`ParentClosePolicy` (set on `ChildWorkflowOptions`) governs child behavior when the parent completes,
fails, times out, or is terminated:

| Policy | Go constant | Behavior |
|---|---|---|
| **Terminate** (default) | `client.ParentClosePolicyTerminate` | Child is terminated immediately. |
| **Request Cancel** | `client.ParentClosePolicyRequestCancel` | Child receives a cancellation request, gets a chance to clean up. |
| **Abandon** | `client.ParentClosePolicyAbandon` | Child keeps running independently. |

Use `Abandon` for children meant to outlive their parent (e.g., a long-running detached process
started by a short-lived orchestrator). If you do, block until the child has actually started before
letting the parent return, or the child may never get created:

```go
cwo := workflow.ChildWorkflowOptions{
    WorkflowID:                   "detached-child",
    ExecutionStartToCloseTimeout: time.Minute * 30,
    ParentClosePolicy:            client.ParentClosePolicyAbandon,
}
ctx = workflow.WithChildOptions(ctx, cwo)
future := workflow.ExecuteChildWorkflow(ctx, SimpleChildWorkflow, value)
if err := future.GetChildWorkflowExecution().Get(ctx, nil); err != nil {
    return err
}
```

## Signals

Signals deliver data to a running workflow asynchronously and durably (persisted in Event History, so
no risk of losing the payload if the workflow isn't ready to process it yet):

```go
var signalVal string
signalChan := workflow.GetSignalChannel(ctx, signalName)

s := workflow.NewSelector(ctx)
s.AddReceive(signalChan, func(c workflow.Channel, more bool) {
    c.Receive(ctx, &signalVal)
    workflow.GetLogger(ctx).Info("Received signal!", zap.String("signal", signalName), zap.String("value", signalVal))
})
s.Select(ctx)
```

### SignalWithStart

Use `client.SignalWithStartWorkflow` when you don't know whether a workflow instance is already
running: it signals the current run if one exists, or starts a new run and signals it. It therefore
does not take a `RunID`.

## Queries

Register a query handler with `workflow.SetQueryHandler`. The handler must be non-blocking,
read-only, and return `(result, error)`:

```go
func MyWorkflow(ctx workflow.Context, input string) error {
    currentState := "started"
    err := workflow.SetQueryHandler(ctx, "current_state", func() (string, error) {
        return currentState, nil
    })
    if err != nil {
        return err
    }

    currentState = "waiting timer"
    if err := workflow.NewTimer(ctx, time.Hour).Get(ctx, nil); err != nil {
        currentState = "timer failed"
        return err
    }

    currentState = "waiting activity"
    ctx = workflow.WithActivityOptions(ctx, myActivityOptions)
    if err := workflow.ExecuteActivity(ctx, MyActivity, "my_input").Get(ctx, nil); err != nil {
        currentState = "activity failed"
        return err
    }
    currentState = "done"
    return nil
}
```

Query it via CLI:

```bash
cadence-cli --domain samples-domain workflow query -w my_workflow_id -r my_run_id -qt current_state
```

Or from code: `cadenceClient.QueryWorkflow(...)`.

### Query consistency

- **Eventual** (default): if you signal a workflow then immediately query it, the query result may
  or may not reflect the signal yet.
- **Strong**: guaranteed to reflect all events that completed *before* the query was issued.
  Higher latency than eventual. Request it explicitly:

```bash
cadence-cli --domain samples-domain workflow query -w my_workflow_id -r my_run_id -qt current_state --qcl strong
```

```go
resp, err := cadenceClient.QueryWorkflowWithOptions(ctx, &client.QueryWorkflowWithOptionsRequest{
    WorkflowID:            workflowID,
    RunID:                 runID,
    QueryType:             queryType,
    QueryConsistencyLevel: shared.QueryConsistencyLevelStrong.Ptr(),
})
```

See also the built-in `__stack_trace` query in
[../01-concepts/events-and-queries.md](../01-concepts/events-and-queries.md#built-in-stack-trace-query)
for debugging stuck workflows.
