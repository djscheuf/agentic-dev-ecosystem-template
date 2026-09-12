# Cadence CLI Reference

The `cadence` CLI performs domain, workflow, task-list, and admin/cluster operations against a
running Cadence server. It's the fastest way to inspect/debug workflows without writing client code.

## Installing

```bash
brew install cadence-workflow      # always installs latest
cadence --help
```

Or via Docker (no local install):

```bash
docker run -it --rm ubercadence/cli:master --address <frontendAddress> --domain samples-domain domain describe
```

Pin `ubercadence/cli:<version>` to match your server version if you need an older CLI (see
[Docker Hub tags](https://hub.docker.com/r/ubercadence/cli/tags)); CLI 0.20.0 is compatible with
server versions 0.12–0.19.

**Docker networking:** if the server is also in Docker (e.g. docker-compose) and you get
"connection refused," use `host.docker.internal` instead of `localhost`:

```bash
docker run -it --rm ubercadence/cli:master --address host.docker.internal:7833 -t grpc --domain samples-domain domain describe
```

If running inside the server's docker-compose network, `docker exec` into the container instead:

```bash
docker exec -it docker_cadence_1 /bin/bash
cadence --address $(hostname -i):7833 -t grpc --do samples-domain domain register
```

## Global options and environment variables

| Flag | Env var | Purpose |
|---|---|---|
| `--address` / `--ad` | `CADENCE_CLI_ADDRESS` | Frontend `host:port`. |
| `--domain` / `--do` | `CADENCE_CLI_DOMAIN` | Default domain — set this to skip `--domain` on every call. |
| `--transport` / `-t` | `CADENCE_CLI_TRANSPORT_PROTOCOL` | `grpc` or `tchannel` (default `tchannel`). |
| `--context_timeout` / `--ct` | `CADENCE_CONTEXT_TIMEOUT` | RPC timeout in seconds (default 5). |
| `--jwt`, `--jwt-private-key` / `--jwt-pk` | `CADENCE_CLI_JWT` | JWT auth (one of the two required if enabled server-side). |
| `--tls_cert_path` / `--tcp` | `CADENCE_CLI_TLS_CERT_PATH` | TLS certificate path. |

Every command supports `--help` / `-h` at every level: `cadence --help`, `cadence workflow --help`,
`cadence workflow signal --help`.

## Top-level command groups

```
cadence domain, d      # register/update/describe a domain
cadence workflow, wf   # start/signal/query/cancel/show/reset workflows
cadence tasklist, tl   # inspect task lists / pollers
cadence admin, adm     # admin operations (shard management, DLQ, etc.)
cadence cluster, cl    # cluster operations
```

## Domain operations

```bash
cadence --domain samples-domain domain register -rd 1     # -rd = retention in days
cadence --domain samples-domain domain describe
```

For a global (XDC-replicated) domain, specify replication settings at registration:

```bash
cadence --domain samples-domain domain register --active_cluster clusterNameA --clusters clusterNameA,clusterNameB
```

## Workflow operations

Assuming `CADENCE_CLI_DOMAIN` is set (all examples below omit `--domain`).

**Start and watch a workflow until it completes:**

```bash
cadence workflow run --tl helloWorldGroup --wt main.Workflow --et 60 -i '"cadence"'
```

- `--tl` task list, `--wt` workflow type, `--et` execution-start-to-close timeout (seconds), `-i`
  JSON input (single-quote-wrap to protect the JSON from the shell).
- Multiple args: `-i '"str_input" 123 {"Name":"x","Age":5}'` (space/newline separated JSON values).

**Start without waiting** (returns immediately with IDs; use `show`/`describe` to check progress):

```bash
cadence workflow start --tl helloWorldGroup --wt main.Workflow --et 60 -i '"cadence"'
```

**Control ID reuse** with `--workflowidreusepolicy` / `--wrp`:

| Value | Policy |
|---|---|
| `0` | `AllowDuplicateFailedOnly` — only if the prior run with this ID failed/cancelled/terminated/timed out. |
| `1` | `AllowDuplicate` — always allowed if not currently running. |
| `2` | `RejectDuplicate` — never allowed once any execution with this ID has existed. |

```bash
cadence workflow start --tl helloWorldGroup --wt main.Workflow --et 60 -i '"cadence"' --wid "<id>" --wrp 0
```

**Attach a memo** (immutable key/value metadata, visible in `list`):

```bash
cadence wf start -tl helloWorldGroup -wt main.Workflow -et 60 -i '"cadence"' -memo_key '"Service" "Env"' -memo '"serverName1" "test"'
```

**Show history / execution info:**

```bash
cadence workflow show -w <workflowID> -r <runID>                 # full history
cadence workflow showid <workflowID> <runID>                      # shortcut, no -w/-r flags
cadence workflow show -w <workflowID>                              # latest run if runID omitted

cadence workflow describe -w <workflowID> -r <runID>               # execution summary
cadence workflow describeid <workflowID> <runID>                   # shortcut
```

**Signal, query, cancel, terminate:**

```bash
cadence workflow signal -w <workflowID> -n <signalName> -i '<json>'
cadence workflow query   -w <workflowID> -qt <queryType>
cadence workflow query   -w <workflowID> -qt __stack_trace         # built-in stuck-workflow diagnostic
cadence workflow cancel  -w <workflowID>
cadence workflow terminate -w <workflowID>
```

**Reset a workflow** (rewind to an earlier point in its history — useful to recover from a bad
deploy without losing the whole execution) by event ID or by reset type:

```bash
cadence workflow reset -w <workflowID> -r <runID> --event_id <eventID>
# or by a named reset type, e.g. one of:
#   LastContinuedAsNew, BadBinary, DecisionCompletedTime, FirstDecisionScheduled,
#   LastDecisionScheduled, FirstDecisionCompleted, LastDecisionCompletedTo
cadence workflow reset -w <workflowID> -r <runID> --reset_type BadBinary
```

There is also `reset-batch` to reset many workflows matching a query/file at once. Run
`cadence workflow reset --help` / `cadence workflow reset-batch --help` to confirm current flags.

**List / search executions:**

```bash
cadence workflow list                     # open or closed executions in the domain
cadence workflow listall                  # all executions
cadence workflow scan                     # faster, unsorted; needs ElasticSearch
cadence workflow count                    # needs ElasticSearch
```

**Inspect a task list's workers:**

```bash
cadence tasklist desc --tl helloWorldGroup
```

## Schedule operations

The CLI exposes a `cadence schedule` command group (create/describe/pause/unpause/backfill/delete)
mirroring the client-library schedule APIs described in
[../01-concepts/timers-and-schedules.md](../01-concepts/timers-and-schedules.md#schedules). Exact
flag names vary by CLI version — run `cadence schedule --help` and `cadence schedule <subcommand> --help`
locally to confirm the current flags before scripting against them, rather than relying on
memorized syntax.

## Downloading history for replay testing

```bash
cadence --do <domain> workflow show --wid <workflowID> --rid <runID> --of history.json
```

Feed this into the Go client's Workflow Replayer — see
[../02-go-client/testing-and-replay.md](../02-go-client/testing-and-replay.md).

## Quick discovery

```bash
cadence help                # top-level commands
cadence help workflow       # all workflow subcommands
cadence workflow signal -h  # options for one subcommand
```
