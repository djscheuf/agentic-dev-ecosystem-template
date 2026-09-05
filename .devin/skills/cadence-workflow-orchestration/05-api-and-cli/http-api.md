# HTTP API

Since Cadence server **v1.2.0**, the server can expose select gRPC procedures over plain HTTP/JSON —
useful for starting/interacting with workflows from bash scripts, curl, or any language without a
Cadence client library.

## Enabling it

The HTTP listener is off by default. Enable specific procedures via an allowlist — see
[../04-configuration/local-server-config.md](../04-configuration/local-server-config.md#enabling-the-http-api-locally)
for the full config-file / Docker / docker-compose setup. Minimal config addition:

```yaml
services:
  frontend:
    rpc:
      http:
        port: 8800
        procedures:
          - uber.cadence.api.v1.WorkflowAPI::StartWorkflowExecution
```

Only listed procedures are reachable — add more `WorkflowAPI`/`DomainAPI`/etc. entries as needed.

## Calling it

Every request is a `POST` to the HTTP port with headers identifying the target RPC and a JSON body
matching that RPC's request message:

```bash
curl -X POST http://0.0.0.0:8800 \
  -H 'context-ttl-ms: 2000' \
  -H 'rpc-caller: my-script' \
  -H 'rpc-service: cadence-frontend' \
  -H 'rpc-encoding: json' \
  -H 'rpc-procedure: uber.cadence.api.v1.WorkflowAPI::StartWorkflowExecution' \
  -d @data.json
```

Required headers:

| Header | Meaning |
|---|---|
| `context-ttl-ms` | Request timeout budget, milliseconds. |
| `rpc-caller` | Identifies the calling application (shown in server-side logs/metrics). |
| `rpc-service` | Always `cadence-frontend` for client-facing calls. |
| `rpc-encoding` | `json` (Cadence also supports other encodings for internal use; `json` is what you want for curl/scripting). |
| `rpc-procedure` | Fully-qualified RPC name, e.g. `uber.cadence.api.v1.WorkflowAPI::StartWorkflowExecution`. |

Example `data.json` for `StartWorkflowExecution`:

```json
{
  "domain": "sample-domain",
  "workflowId": "workflowid123",
  "execution_start_to_close_timeout": "11s",
  "task_start_to_close_timeout": "10s",
  "workflowType": { "name": "workflow_type" },
  "taskList": { "name": "tasklist-name" },
  "identity": "My custom caller identity",
  "requestId": "4D1E4058-6FCF-4BA8-BF16-8FA8B02F9651"
}
```

A successful call returns HTTP 200 with a JSON body matching the RPC's response message (often `{}`
for fire-and-forget operations like `StartWorkflowExecution`'s ack, or a structured payload for
read-style calls).

## Which procedures to expose

For local workflow authoring/debugging, the practically useful ones live under `WorkflowAPI` and
`DomainAPI` — start/signal/query/cancel/describe workflow, and register/describe domain. These
mirror exactly what the [CLI](cli-reference.md) and Go/Python clients do under the hood, so if you
already know the CLI flag or client method for an operation, the equivalent HTTP procedure name is
almost always `uber.cadence.api.v1.WorkflowAPI::<PascalCaseVerb>` (e.g. `SignalWorkflowExecution`,
`QueryWorkflow`, `RequestCancelWorkflowExecution`, `DescribeWorkflowExecution`).

## Admin API

Cadence also exposes a large `AdminAPI` surface (shard management, DLQ inspection/purge, search
attribute whitelisting, replication controls, and more) over the same HTTP mechanism — this is
**operator/cluster-administration tooling**, not something you'd typically call while authoring or
debugging a workflow locally. It follows the identical request shape shown above
(`rpc-procedure: uber.cadence.admin.v1.AdminAPI::<Verb>`, JSON body matching that verb's request
message).

Given its size and narrow (production-ops) audience, this skill does not reproduce the full endpoint
list. If you need it: the canonical, complete, always-current reference is the live docs page at
<https://cadenceworkflow.io/docs/concepts/http-api> (see the "HTTP API Reference" section), or the
proto definitions themselves in
[cadence-workflow/cadence-idl](https://github.com/cadence-workflow/cadence-idl/tree/master/proto/uber/cadence/api/v1).

## When to prefer HTTP API vs. CLI vs. a client library

| Use case | Prefer |
|---|---|
| Interactive debugging, one-off inspection | [CLI](cli-reference.md) |
| Scripting from a language with no Cadence SDK, or from bash/curl | HTTP API |
| Building an actual application/workflow/activity | [Go](../02-go-client/) or [Python](../03-python-client/) client |
