# Deployment Topology

A Cadence-based application has three kinds of role, which can be collocated in one process or split
across many: the **Cadence Service** itself, **Workers** (workflow + activity), and **External
Clients**.

## Cadence Service

The service exposes all functionality through a strongly-typed gRPC API and is itself composed of
several internal services, each independently scalable across multiple nodes:

- **Frontend** — stateless; handles incoming requests from workers and clients. Put an external load
  balancer in front of multiple Frontend instances.
- **History Service** — implements the core logic of orchestrating workflow steps and activities;
  this is where workflow state and Event History live.
- **Matching Service** — matches pending workflow/activity tasks to workers able to execute them;
  receives task assignments from the History Service.
- **Internal Worker Service** — runs Cadence's own internal workflows/activities (e.g. archival).
- **Workers** — not part of the service; these are *your* client applications (see below).

The service persists to Cassandra, MySQL, PostgreSQL, CockroachDB (Postgres-compatible), or TiDB
(MySQL-compatible). For advanced visibility (complex list/search predicates), it also integrates with
ElasticSearch/OpenSearch. For local development, a single `cadence-server` process with an embedded
SQLite backend is enough — see
[../00-get-started/local-quickstart.md](../00-get-started/local-quickstart.md).

The service is **multitenant**: many independent applications/teams can run against one Cadence
service instance (a single Uber-internal instance serves 100+ applications), or you can dedicate one
instance per application. It keeps workflow state and durable timers, and maintains internal queues
(**Task Lists**) to dispatch tasks to workers.

## Workflow Worker

The Cadence service never executes your workflow code directly. Your **workflow worker** process
receives **decision tasks** (bundles of events the workflow needs to handle) from the service, runs
them against your workflow code, and reports the resulting **decisions** back. Because workflow code
is external to the service, it can be written in any language with a client that talks the service's
API — Go and Java are production-ready; Python is a community SDK under active development (see
[../03-python-client/](../03-python-client/) for its current coverage).

## Activity Worker

Activities are how workflow code touches the unreliable outside world. An **activity worker**
receives **activity tasks** from the service, invokes the corresponding activity implementation, and
reports completion status back. Cadence activities are richer than a typical queue consumer: they
support task routing to specific processes/pools, effectively unlimited retries, heartbeats, and
unbounded execution time.

In many small deployments, the workflow worker and activity worker roles run in the *same* process —
the distinction is logical, not necessarily physical.

## External Clients

Clients are the entities — your app code, a UI, a CLI, another microservice — that call
`StartWorkflowExecution` and other service APIs to:

- Start a workflow execution.
- Send **signals** for asynchronous external events.
- Send **synchronous queries** against workflow state.
- Wait synchronously for a workflow's completion.
- Cancel, terminate, restart, or reset a workflow execution.
- Search for workflows via the list API.

## Putting it together

```
External Client -- StartWorkflowExecution --> Frontend --> History Service
                                                                 |
                                                                 v
                                                          Matching Service
                                                            (Task Lists)
                                                            /          \
                                                 Decision Task      Activity Task
                                                       |                  |
                                                       v                  v
                                              Workflow Worker      Activity Worker
                                            (executes workflow    (executes activity,
                                             code, returns          reports result)
                                             decisions)
```

For local development you typically run: one `cadence-server` process (all internal services
collapsed into one binary), one worker process registering both your workflow and activity code, and
a CLI or small client program to start/signal/query workflows.
