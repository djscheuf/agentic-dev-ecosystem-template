# Task Lists

A task list is the queue Cadence uses to hand work to workers — it decouples the service from workers
so neither has to know about the other's location or availability.

## How it works

- When a workflow invokes an activity, the workflow worker returns a `ScheduleActivityTask` decision.
  The service enqueues an `ActivityTask` on the named **activity task list**; a worker long-polls
  that list and picks it up.
- When a workflow needs to handle an external event (timer fired, signal received, activity
  completed), the service creates a `DecisionTask` on the **decision task list**; a workflow worker
  (also called a "decider") long-polls it and resumes the workflow.

Task lists require **no explicit registration** — they're created on demand simply by a worker or
task showing up referencing that name. There's no limit on how many you can have; a common pattern is
one task list per worker process or per worker pool.

## Why a queue instead of direct RPC to workers

- Workers never need an open inbound port — no service discovery, no exposed attack surface.
- If all workers are down, tasks simply queue up and wait — no lost work.
- Workers pull tasks only when they have spare capacity, so they can't be overloaded by a spike.
- Automatic load balancing across however many workers are polling.
- Server-side throttling: cap the dispatch rate to a pool of workers even under load, while still
  allowing bursts within that cap.
- Task lists can route work to a specific pool, or even a specific process, just by using a
  differently-named list.

## When to use multiple task lists

See [activities.md](activities.md#task-list-routing-why-youd-use-more-than-one) for the concrete
motivations (flow control, throttling, independent deployability, capability-based routing,
host/process affinity, priority tiers, versioning). The same task-list mechanism underlies both
activity dispatch and decision-task dispatch.
