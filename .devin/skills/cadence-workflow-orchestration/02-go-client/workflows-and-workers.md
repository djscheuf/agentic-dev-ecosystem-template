# Go: Workflows and Workers

## Defining a workflow

A workflow is a Go function. Register it in an `init()` (or explicitly before starting the worker):

```go
package sample

import (
    "time"
    "go.uber.org/cadence/workflow"
)

func init() {
    workflow.Register(SimpleWorkflow)
}

func SimpleWorkflow(ctx workflow.Context, value string) error {
    ao := workflow.ActivityOptions{
        TaskList:               "sampleTaskList",
        ScheduleToCloseTimeout: time.Second * 60,
        ScheduleToStartTimeout: time.Second * 60,
        StartToCloseTimeout:    time.Second * 60,
        HeartbeatTimeout:       time.Second * 10,
        WaitForCancellation:    false,
    }
    ctx = workflow.WithActivityOptions(ctx, ao)

    future := workflow.ExecuteActivity(ctx, SimpleActivity, value)
    var result string
    if err := future.Get(ctx, &result); err != nil {
        return err
    }
    workflow.GetLogger(ctx).Info("Done", zap.String("result", result))
    return nil
}
```

### Function signature

```go
func SimpleWorkflow(ctx workflow.Context, value string) error
```

- First parameter is always `workflow.Context` — the Cadence-provided replacement for
  `context.Context` (its `Done()` returns a `workflow.Channel`, not a native `chan`).
- Remaining parameters are your workflow's inputs — **must be serializable** (no channels, funcs,
  variadic args, unsafe pointers).
- Return `error` to indicate failure; return an additional value before `error` to return a result.

### Determinism rules (see also [../01-concepts/workflows.md](../01-concepts/workflows.md))

- Read/manipulate only local state or values returned from Cadence client library calls.
- Never touch external systems except through Activities.
- Use `workflow.Now()` / `workflow.Sleep()` — never `time.Now()` / `time.Sleep()`.
- Use `workflow.Go()` / `workflow.Channel` / `workflow.Selector` — never native `go` / `chan` /
  `select`.
- Log via `workflow.GetLogger(ctx)` — not a global logger.
- Never `range` over a map in workflow code (iteration order is randomized in Go).

### Registration

```go
workflow.Register(SimpleWorkflow)
```

Safe to call from `init()`. This creates an in-memory mapping from the fully-qualified function name
to the implementation inside the worker process. A decision task for an unregistered workflow type
fails that task (not the whole workflow).

## Starting a workflow (from a client)

```go
import "go.uber.org/cadence/client"

var cadenceClient client.Client

cadenceClient.StartWorkflow(
    ctx,
    client.StartWorkflowOptions{
        TaskList:                     "workflow-task-list",
        ExecutionStartToCloseTimeout: 10 * time.Second,
    },
    WorkflowFunc,
    workflowArg1, workflowArg2, workflowArg3,
)
```

Key `StartWorkflowOptions` fields:

| Field | Purpose |
|---|---|
| `ID` | Business-meaningful workflow ID; defaults to a generated UUID. |
| `TaskList` | Where decision tasks (and by default, activities) are scheduled. Mandatory. |
| `ExecutionStartToCloseTimeout` | Total workflow execution timeout. Mandatory. |
| `DecisionTaskStartToCloseTimeout` | Retry window if a decision task is lost. Default 10s. |
| `WorkflowIDReusePolicy` | See [../01-concepts/workflows.md](../01-concepts/workflows.md#workflow-id-run-id-and-uniqueness). |
| `RetryPolicy` | Optional whole-workflow retry policy (see [error-handling-and-retries.md](error-handling-and-retries.md)). |
| `CronSchedule` | Legacy cron string; prefer [Schedules](../01-concepts/timers-and-schedules.md#schedules). |
| `Memo` / `SearchAttributes` | Non-indexed / indexed metadata for list/search. |
| `DelayStart` / `JitterStart` / `FirstRunAt` | Delay or randomize the actual start time. |

### JitterStart for batch starts

Starting many workflows at once can overload Cadence and its DB, and cause a scaling scramble for
workers. `JitterStart: 6 * time.Hour` randomly spreads 1000 workflow starts across a 6-hour window
instead of firing them all at once — ideal for batch-style loads (e.g., end-of-month jobs) where an
acceptable-but-random delay is fine.

## Worker service

A worker is any process (new or existing service) that links in your workflow/activity
implementations and polls the Cadence service. Minimal gRPC-based worker:

```go
package main

import (
    "go.uber.org/cadence/.gen/go/cadence/workflowserviceclient"
    "go.uber.org/cadence/compatibility"
    "go.uber.org/cadence/worker"

    apiv1 "github.com/cadence-workflow/cadence-idl/go/proto/api/v1"
    "github.com/uber-go/tally"
    "go.uber.org/zap"
    "go.uber.org/yarpc"
    "go.uber.org/yarpc/transport/grpc"
)

const (
    HostPort       = "127.0.0.1:7833" // gRPC port; use 7933 for tchannel
    Domain         = "SimpleDomain"
    TaskListName   = "SimpleWorker"
    ClientName     = "SimpleWorker"
    CadenceService = "cadence-frontend"
)

func main() {
    serviceClient := buildCadenceClient()
    w := buildWorker(serviceClient)
    if err := w.Start(); err != nil {
        panic(err)
    }
}

func buildCadenceClient() workflowserviceclient.Interface {
    dispatcher := yarpc.NewDispatcher(yarpc.Config{
        Name: ClientName,
        Outbounds: yarpc.Outbounds{
            CadenceService: {Unary: grpc.NewTransport().NewSingleOutbound(HostPort)},
        },
    })
    if err := dispatcher.Start(); err != nil {
        panic(err)
    }
    clientConfig := dispatcher.ClientConfig(CadenceService)
    return compatibility.NewThrift2ProtoAdapter(
        apiv1.NewDomainAPIYARPCClient(clientConfig),
        apiv1.NewWorkflowAPIYARPCClient(clientConfig),
        apiv1.NewWorkerAPIYARPCClient(clientConfig),
        apiv1.NewVisibilityAPIYARPCClient(clientConfig),
    )
}

func buildWorker(service workflowserviceclient.Interface) worker.Worker {
    workerOptions := worker.Options{
        Logger:       zap.NewExample(),
        MetricsScope: tally.NewTestScope(TaskListName, map[string]string{}),
    }
    return worker.New(service, Domain, TaskListName, workerOptions)
}
```

Cadence supports two transport protocols: **tchannel** (legacy, port 7933 by default) and **gRPC**
(port 7833). Prefer gRPC for new code — see [../04-configuration/client-connection.md](../04-configuration/client-connection.md)
for tchannel vs. gRPC setup and TLS configuration.

`worker.Options` also controls autoscaling and session support — see
[../04-configuration/worker-options.md](../04-configuration/worker-options.md).
