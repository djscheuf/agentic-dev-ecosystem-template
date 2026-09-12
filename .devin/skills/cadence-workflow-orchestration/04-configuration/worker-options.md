# Worker Configuration (Go and Python)

## Go: `worker.Options`

Passed to `worker.New(service, domain, taskList, workerOptions)`. Commonly-set fields:

| Field | Purpose |
|---|---|
| `Logger` | `*zap.Logger` for worker/workflow logging. |
| `MetricsScope` | `tally.Scope` for metrics. |
| `MaxConcurrentActivityTaskPollers` | Number of concurrent activity-task pollers (ignored if AutoScaler is enabled). |
| `MaxConcurrentDecisionTaskPollers` | Number of concurrent decision-task pollers (ignored if AutoScaler is enabled). |
| `EnableSessionWorker` | Enables the [session framework](../02-go-client/sessions-and-tracing.md#sessions). |
| `MaxConcurrentSessionExecutionSize` | Caps concurrent sessions per worker **process**. |
| `AutoScalerOptions` | See below. |

### Worker AutoScaler

Cadence workers spend most of their time polling — a lightweight operation that keeps CPU usage low
(5-15%) even when a worker is doing meaningful work. Naive CPU-based infra autoscalers (Kubernetes
HPA, cloud ASGs) misread this as idle and scale workers **down**, which then causes task pickup
delays, cascading timeouts, and task-list backlogs. The Worker AutoScaler fixes this by scaling
poller counts based on Cadence-specific signals (poller utilization, task pickup latency, queue
depth) instead of CPU.

Enable it with sensible defaults:

```go
worker.Options{
    AutoScalerOptions: worker.AutoScalerOptions{
        Enabled: true,
    },
}
```

**When enabled, it ignores `MaxConcurrentActivityTaskPollers` / `MaxConcurrentDecisionTaskPollers`.**
If you're migrating from a manually-tuned worker, set the initial poller count to the max of your
previous manual values so the AutoScaler doesn't start under-provisioned:

```go
worker.Options{
    AutoScalerOptions: worker.AutoScalerOptions{
        Enabled:         true,
        PollerMinCount:  2,
        PollerMaxCount:  8,
        PollerInitCount: 4, // max(previous activity pollers, previous decision pollers)
    },
}
```

AutoScaler also helps balance load **across** task lists when traffic is uneven (some task lists
busy, others idle) by dynamically reallocating polling capacity instead of using a fixed
per-task-list poller count.

For local development this is usually unnecessary — enable it once you're thinking about production
scaling behavior, not for a single local worker process.

## Python: `Client`, `Registry`, `Worker`

Python has no direct AutoScaler equivalent (community SDK — see
[../03-python-client/feature-gaps.md](../03-python-client/feature-gaps.md)). Configuration surface is
smaller:

```python
from cadence.client import Client
from cadence.worker import Worker, Registry

registry = Registry()  # holds workflow/activity definitions; one per process, or shared

async with Client(domain="my-domain", target="localhost:7833") as client:
    async with Worker(client, "my-task-list", registry):
        await asyncio.Event().wait()
```

| Option | Where | Purpose |
|---|---|---|
| `domain` | `Client(...)` | Cadence domain (required). |
| `target` | `Client(...)` | Frontend `host:port` (default `localhost:7833`). |
| `identity` | `Client(...)` | Identity string shown in workflow history. |
| `data_converter` | `Client(...)` | Custom serializer. |
| `disable_activity_worker` | `Worker(...)` | Run a decision-task-only worker. |
| `disable_workflow_worker` | `Worker(...)` | Run an activity-task-only worker. |

Splitting activity-only and workflow-only workers (via the `disable_*_worker` flags) is the Python
equivalent of the Go pattern of dedicating separate worker pools per task list — useful when
activities and workflows have very different resource profiles (e.g., GPU-bound activities vs.
lightweight orchestration).

See also [../02-go-client/workflows-and-workers.md](../02-go-client/workflows-and-workers.md) and
[../03-python-client/setup-and-workers.md](../03-python-client/setup-and-workers.md) for the full
worker setup in context.
