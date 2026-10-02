# Go: Continue-As-New, Side Effect, Sleep, and Versioning

## Continue-As-New

A naive "runs forever" workflow (big `for` loop + sleep with all logic inside the loop body) grows
its Event History without bound until it hits the service's max history size. **`ContinueAsNew`**
atomically completes the current execution and starts a fresh execution with the same `WorkflowID`
and **no carried-over history**. Trigger it by returning the special error from the workflow
function:

```go
func SimpleWorkflow(ctx workflow.Context, value string) error {
    // ... do bounded amount of work ...
    return workflow.NewContinueAsNewError(ctx, SimpleWorkflow, value)
}
```

Use this for any workflow that loops/recurs indefinitely inside one logical "session" — e.g.
processing an unbounded stream of signals, or periodic work across many iterations.

## Side Effect

`workflow.SideEffect` executes a short, non-deterministic snippet exactly once and records its result
in history; on replay it returns the **recorded** result instead of re-running the function. Good for
short things like random values or UUIDs:

```go
encodedRandom := workflow.SideEffect(ctx, func(ctx workflow.Context) interface{} {
    return rand.Intn(100)
})

var random int
encodedRandom.Get(&random)
if random < 50 {
    // ...
} else {
    // ...
}
```

Caveats:
- Unlike activities, Cadence does **not** guarantee at-most-once execution for `SideEffect` — under
  certain failure conditions the function can run more than once.
- The only way `SideEffect` "fails" is by panicking, which fails the decision task; Cadence
  reschedules the decision task and gives `SideEffect` another chance.
- Never return data from a side effect except through its recorded return value.

## Sleep

```go
func SleepWorkflow(ctx workflow.Context) error {
    workflow.GetLogger(ctx).Info("sleeping for 30s")
    if err := workflow.Sleep(ctx, 30*time.Second); err != nil {
        return err
    }
    workflow.GetLogger(ctx).Info("awake")
    return nil
}
```

- Always `workflow.Sleep(ctx, duration)`, never `time.Sleep` — see
  [../01-concepts/timers-and-schedules.md](../01-concepts/timers-and-schedules.md) for why native
  sleep breaks durability and determinism.
- Sleeping does not consume worker resources — Cadence persists the wait and resumes the workflow
  when it's over, even across worker crashes/restarts.
- Very large numbers of simultaneous sleeps/timers can strain the cluster; consider jittering
  (`JitterStart` at workflow-start time, or staggering timer durations) if you're firing many at once.

## Versioning (`workflow.GetVersion`)

Because workflow replay reconstructs state by re-running your *current* code against a *historical*
event log, an incompatible code change (e.g., swapping which activity runs at a given step) breaks
replay for any workflow execution that is already in flight. `workflow.GetVersion` lets old and new
logic coexist safely.

### The problem

```go
func MyWorkflow(ctx workflow.Context, data string) (string, error) {
    // ... originally called ActivityA here ...
    var result1 string
    err := workflow.ExecuteActivity(ctx, ActivityA, data).Get(ctx, &result1) // now replaced by ActivityC — BREAKS replay of in-flight executions
    ...
}
```

### The fix

```go
v := workflow.GetVersion(ctx, "Step1", workflow.DefaultVersion, 1)
if v == workflow.DefaultVersion {
    err = workflow.ExecuteActivity(ctx, ActivityA, data).Get(ctx, &result1)
} else {
    err = workflow.ExecuteActivity(ctx, ActivityC, data).Get(ctx, &result1)
}
```

`GetVersion(ctx, changeID, minSupported, maxSupported)` records a marker in history the first time
it runs for a given `changeID`; every subsequent replay of that execution returns the *recorded*
version, so old executions keep taking the old branch while new executions take the new one.

### Evolving further

Adding a second change bumps `maxSupported`:

```go
v := workflow.GetVersion(ctx, "Step1", workflow.DefaultVersion, 2)
switch v {
case workflow.DefaultVersion:
    err = workflow.ExecuteActivity(ctx, ActivityA, data).Get(ctx, &result1)
case 1:
    err = workflow.ExecuteActivity(ctx, ActivityC, data).Get(ctx, &result1)
default: // 2
    err = workflow.ExecuteActivity(ctx, ActivityD, data).Get(ctx, &result1)
}
```

Once you're sure no execution older than version 1 is still running, raise `minSupported` to `1` —
any attempt to replay a `DefaultVersion` history will now fail fast instead of silently
misbehaving. Once version 1 is also fully drained, you can collapse to a single branch, but **keep
the `GetVersion` call** (`workflow.GetVersion(ctx, "Step1", 2, 2)`) — it guards against a straggling
old execution and gives you a place to branch from for the *next* change.

Only the **first** `GetVersion()` call for a given `changeID` needs to be preserved indefinitely;
later calls for the same ID can be pruned once their minimum version is fully retired. If you retire
the `changeID` entirely, you cannot reuse that same ID for a future change to the same code location —
start a new `changeID` (e.g. `"Step1-fix2"`) from `DefaultVersion` again.

### Safe rollout without breaking rollback: `ExecuteWithMinVersion`

To decouple "deploy the new branching code" from "activate the new behavior" (so you can roll back
safely if something looks wrong), use `workflow.ExecuteWithMinVersion()`:

1. **Deploy with compatibility** — new code recognizes version `1` but is pinned to still execute the
   old activity:
   ```go
   v := workflow.GetVersion(ctx, "fooToBarChange", workflow.DefaultVersion, 1, workflow.ExecuteWithMinVersion())
   if v == workflow.DefaultVersion {
       err = workflow.ExecuteActivity(ctx, FooActivity).Get(ctx, nil)
   } else {
       err = workflow.ExecuteActivity(ctx, BarActivity).Get(ctx, nil)
   }
   ```
   Old code only understands `DefaultVersion`, so rollback to it is still safe.
2. **Activate** — remove `ExecuteWithMinVersion()`; now new-started workflows actually take the
   `BarActivity` branch, while both code versions remain rollback-compatible.
3. **Clean up** — once nothing is running on `DefaultVersion`, delete the old branch as described
   above.

### Alternative: new workflow type

If you don't need in-flight executions to adopt new logic at all, you can define the changed logic
as a **new `WorkflowType`** and just point new `StartWorkflow` calls at it — no `GetVersion` needed,
at the cost of maintaining two workflow types until the old one drains.

For catching incompatible changes *before* they hit production, see
[testing-and-replay.md](testing-and-replay.md#workflow-replayer-and-shadower).
