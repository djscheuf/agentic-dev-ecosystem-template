# Go: Sessions and Tracing/Context Propagation

## Sessions

The session framework pins a group of activities to run on **the same worker process** without you
manually managing task list names — plus concurrent-session limiting and worker-failure detection.

### When to use sessions

- **File processing**: download -> process -> upload must happen on the same host (shared local
  file).
- **ML model training**: download dataset -> train -> upload params, where GPU/memory constraints
  mean you need to cap how many training sessions run per host.

### Enabling and using sessions

1. Set `EnableSessionWorker: true` on `worker.Options` for the worker(s) that should host sessions.
2. In the workflow, wrap the session's activities with a **session context**:

```go
func FileProcessingWorkflow(ctx workflow.Context, fileID string) (err error) {
    ao := workflow.ActivityOptions{
        ScheduleToStartTimeout: time.Second * 5,
        StartToCloseTimeout:    time.Minute,
    }
    ctx = workflow.WithActivityOptions(ctx, ao)

    so := &workflow.SessionOptions{
        CreationTimeout:  time.Minute, // max time to wait for a worker slot
        ExecutionTimeout: time.Minute, // max total session duration
    }
    sessionCtx, err := workflow.CreateSession(ctx, so)
    if err != nil {
        return err
    }
    defer workflow.CompleteSession(sessionCtx)

    var fInfo *fileInfo
    if err = workflow.ExecuteActivity(sessionCtx, downloadFileActivityName, fileID).Get(sessionCtx, &fInfo); err != nil {
        return err
    }
    var fInfoProcessed *fileInfo
    if err = workflow.ExecuteActivity(sessionCtx, processFileActivityName, *fInfo).Get(sessionCtx, &fInfoProcessed); err != nil {
        return err
    }
    return workflow.ExecuteActivity(sessionCtx, uploadFileActivityName, *fInfoProcessed).Get(sessionCtx, nil)
}
```

- `CreateSession` picks a worker polling the task list named in `ActivityOptions` (or
  `StartWorkflowOptions` if unset) and pins the session there. It retries internally until
  `CreationTimeout` elapses if all workers are busy.
- All activities executed with `sessionCtx` run on that same worker.
- If the worker executing the session dies, activities using `sessionCtx` fail with
  `workflow.ErrSessionFailed` — this doesn't auto-fail the session; you still handle the error and
  call `CompleteSession` (safe to call even on a failed session, e.g. from `defer`).
- `CompleteSession` releases the worker's reserved capacity — call it as soon as you're done with the
  session.

### Concurrency limits

Set `worker.Options.MaxConcurrentSessionExecutionSize` to bound sessions-per-worker-**process** (not
per host — run only one worker process per host if you rely on this). Default is effectively
unlimited.

### Long sessions + Continue-As-New

`workflow.RecreateSession(ctx, recreateToken, sessionOptions)` re-establishes a session on the *same*
worker across a `ContinueAsNew` boundary. Get the token before continuing as new:

```go
token := workflow.GetSessionInfo(sessionCtx).GetRecreateToken()
```

## Tracing

The Go client integrates with [OpenTracing](https://opentracing.io/): supply an `opentracing.Tracer`
in both `ClientOptions` and `WorkerOptions`. This gives you a call graph across workflows, activities,
and child workflows — validated against [Jaeger](https://www.jaegertracing.io/), but any OpenTracing
implementation should work. Tracing relies on the same context-propagation mechanism described below.

## Context propagation

Cadence lets you propagate custom values across a workflow's `context.Context` / `workflow.Context`
boundary (e.g., request IDs, tenant info) via a **Context Propagator**, configured on both
`ClientOptions` and `WorkerOptions`.

The server itself supports carrying an opaque `Header` (`map[string, binary]`) across workflow
transitions. `HeaderWriter`/`HeaderReader` read/write that header:

```go
type HeaderWriter interface {
    Set(string, []byte)
}
type HeaderReader interface {
    ForEachKey(handler func(string, []byte) error) error
}
```

Implement a `ContextPropagator` with four methods:

```go
type ContextPropagator interface {
    Inject(context.Context, HeaderWriter) error
    Extract(context.Context, HeaderReader) (context.Context, error)
    InjectFromWorkflow(Context, HeaderWriter) error
    ExtractToWorkflow(Context, HeaderReader) (Context, error)
}
```

- `Inject` / `InjectFromWorkflow` — pull values of interest out of the Go/workflow context and write
  them into the header.
- `Extract` / `ExtractToWorkflow` — read the header back into a Go/workflow context.

You can register multiple propagators, each responsible for a different kind of context — this is
the recommended pattern rather than one large propagator. The Go client's own tracing support is
itself implemented as a context propagator, so it's a good reference implementation to model a
custom one on.
