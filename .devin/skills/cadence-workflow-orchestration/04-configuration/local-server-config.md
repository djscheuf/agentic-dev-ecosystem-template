# Local Cadence Server Configuration

## Config files

A `cadence-server` process reads a YAML config (e.g. `base.yaml`, layered with an environment file
like `development.yaml` when running from the cloned `cadence` repo). This is where you configure:

- Persistence backend (SQLite for the zero-dependency local quickstart; Cassandra/MySQL/Postgres for
  a closer-to-production local setup via docker-compose).
- Which internal services run (frontend/history/matching/worker) and their ports.
- RPC settings (tchannel/gRPC ports, and optionally HTTP — see below).
- Dynamic config file path, for runtime feature flags.

See [../00-get-started/local-quickstart.md](../00-get-started/local-quickstart.md) for the two
supported local paths (embedded SQLite vs. docker-compose with Cassandra) and which config each uses
by default.

## Enabling the HTTP API locally

By default only gRPC/tchannel are exposed. To also enable Cadence's HTTP API (useful for scripting
against Cadence from bash/curl without a client library — see
[../05-api-and-cli/http-api.md](../05-api-and-cli/http-api.md)), add an `http` section under the
frontend service's `rpc` config:

```yaml
services:
  frontend:
    rpc:
      # ... existing tchannel/grpc config ...
      http:
        port: 8800
        procedures:
          - uber.cadence.api.v1.WorkflowAPI::StartWorkflowExecution
```

`procedures` is an allowlist — only listed RPCs are reachable over HTTP. Add more entries (e.g. other
`WorkflowAPI`/`DomainAPI` methods) as needed.

### Applying this when running via Docker

**`docker run`:**

```bash
docker run \
  -e FRONTEND_HTTP_PORT=8800 \
  -e FRONTEND_HTTP_PROCEDURES="uber.cadence.api.v1.WorkflowAPI::StartWorkflowExecution" \
  ubercadence/server:<tag>
```

**`docker-compose`** (add to the `cadence` service's `environment` and expose the port):

```yaml
cadence:
  image: ubercadence/server:master-auto-setup
  ports:
    - "8800:8800"
    # ... other ports (8000-8003 metrics, 7933/7934/7935/7939 tchannel, 7833 grpc) ...
  environment:
    - "CASSANDRA_SEEDS=cassandra"
    - "DYNAMIC_CONFIG_FILE_PATH=config/dynamicconfig/development.yaml"
    - "FRONTEND_HTTP_PORT=8800"
    - "FRONTEND_HTTP_PROCEDURES=uber.cadence.api.v1.WorkflowAPI::StartWorkflowExecution"
```

**Local binary:** build and run `./cadence-server` as usual (see
[../00-get-started/local-quickstart.md](../00-get-started/local-quickstart.md)); it picks up the
`http` section from your `base.yaml`/`development.yaml` directly, no env vars needed.

## Dynamic config

`DYNAMIC_CONFIG_FILE_PATH` (or the equivalent config-file setting) points at a YAML file of runtime
feature flags and limits the server reads without a restart-required code change — e.g. history size
limits, throttling knobs, feature gates. For local development you generally don't need to touch this
beyond what the default `development.yaml` already sets; it becomes relevant when you're
reproducing a specific production behavior locally (see
[../06-debugging/troubleshooting-playbook.md](../06-debugging/troubleshooting-playbook.md)).

## Ports reference (docker-compose default layout)

| Port | Purpose |
|---|---|
| 7933 / 7934 / 7935 / 7939 | tchannel (frontend/history/matching/worker internal ports) |
| 7833 | gRPC frontend |
| 8800 | HTTP API (only if explicitly enabled, see above) |
| 8088 | Cadence Web UI |
| 8000-8003 | Prometheus metrics endpoints per internal service |

These are the defaults baked into the `cadence-workflow/cadence` repo's `docker/docker-compose.yml`
— if you're running the embedded-SQLite quickstart instead, only the gRPC (7833) and Web UI (8088)
ports are typically relevant.
