# Client/Worker Connection Configuration

## Transport protocols

Cadence supports two transports:

| Transport | Default port | Notes |
|---|---|---|
| **gRPC** | 7833 | Preferred for new code. |
| **tchannel** | 7933 | Legacy; still the CLI's default transport unless `--transport`/`-t grpc` is passed. |

## Go: building a client/worker connection

**gRPC** (preferred):

```go
import (
    "go.uber.org/cadence/.gen/go/cadence/workflowserviceclient"
    "go.uber.org/cadence/compatibility"
    "go.uber.org/yarpc"
    "go.uber.org/yarpc/transport/grpc"
    apiv1 "github.com/cadence-workflow/cadence-idl/go/proto/api/v1"
)

const HostPort = "127.0.0.1:7833"

func buildCadenceClient() workflowserviceclient.Interface {
    dispatcher := yarpc.NewDispatcher(yarpc.Config{
        Name: "my-client",
        Outbounds: yarpc.Outbounds{
            "cadence-frontend": {Unary: grpc.NewTransport().NewSingleOutbound(HostPort)},
        },
    })
    if err := dispatcher.Start(); err != nil {
        panic(err)
    }
    clientConfig := dispatcher.ClientConfig("cadence-frontend")
    return compatibility.NewThrift2ProtoAdapter(
        apiv1.NewDomainAPIYARPCClient(clientConfig),
        apiv1.NewWorkflowAPIYARPCClient(clientConfig),
        apiv1.NewWorkerAPIYARPCClient(clientConfig),
        apiv1.NewVisibilityAPIYARPCClient(clientConfig),
    )
}
```

**tchannel** (legacy, port 7933): swap `grpc.NewTransport().NewSingleOutbound(HostPort)` for a
`tchannel.NewChannelTransport(...)` outbound — see
[../02-go-client/workflows-and-workers.md](../02-go-client/workflows-and-workers.md#worker-service)
for the full snippet.

### TLS over gRPC

```go
caCert, _ := ioutil.ReadFile("/path/to/cert/file")
caCertPool := x509.NewCertPool()
caCertPool.AppendCertsFromPEM(caCert)

creds := credentials.NewTLS(&tls.Config{RootCAs: caCertPool})
grpcTransport := grpc.NewTransport()
dialer := grpcTransport.NewDialer(grpc.DialerCredentials(creds))
outbound := grpcTransport.NewOutbound(peer.NewSingle(hostport.PeerIdentifier(HostPort), dialer))

dispatcher := yarpc.NewDispatcher(yarpc.Config{
    Name:      "my-client",
    Outbounds: yarpc.Outbounds{"cadence-frontend": {Unary: outbound}},
})
```

Point `HostPort` at the server's TLS-enabled gRPC listener and use a cert matching the server's TLS
configuration.

## Python: `Client`

```python
from cadence.client import Client

async with Client(domain="my-domain", target="localhost:7833") as client:
    ...
```

| Option | Description |
|---|---|
| `domain` | Required. |
| `target` | `host:port`, gRPC only — the Python client does not support tchannel. Default `localhost:7833`. |
| `identity` | Shown in workflow history; auto-generated if omitted. |
| `data_converter` | Custom argument/result serializer. |

The Python client is gRPC-only, so always point `target` at the gRPC port (7833 by default), never
the tchannel port.

## CLI connection flags

```bash
cadence --address <host:port> --domain <domain> --transport grpc workflow list
```

| Flag | Env var | Purpose |
|---|---|---|
| `--address` / `--ad` | `CADENCE_CLI_ADDRESS` | Frontend `host:port`. |
| `--domain` / `--do` | `CADENCE_CLI_DOMAIN` | Default domain (skip passing `--domain` every call). |
| `--transport` / `-t` | `CADENCE_CLI_TRANSPORT_PROTOCOL` | `grpc` or `tchannel` (default `tchannel`). |
| `--tls_cert_path` / `--tcp` | `CADENCE_CLI_TLS_CERT_PATH` | Path to TLS certificate. |
| `--jwt` / `--jwt-private-key` | `CADENCE_CLI_JWT` | JWT-based authorization (one of the two required if JWT auth is enabled server-side). |
| `--context_timeout` / `--ct` | `CADENCE_CONTEXT_TIMEOUT` | RPC call timeout in seconds (default 5). |

Set `CADENCE_CLI_ADDRESS` and `CADENCE_CLI_DOMAIN` in your shell profile for local dev to avoid
repeating them on every command — see [../05-api-and-cli/cli-reference.md](../05-api-and-cli/cli-reference.md).

## Docker networking gotcha

When running the CLI (or a worker) from a Docker container against a Cadence server also running in
Docker/docker-compose on the host, `localhost` inside the container does not reach the host. On
Docker 18.03+, use `host.docker.internal` instead:

```bash
docker run -it --rm ubercadence/cli:master --address host.docker.internal:7833 --t grpc --domain samples-domain domain describe
```

See [../00-get-started/local-quickstart.md](../00-get-started/local-quickstart.md) for the full local
setup this fits into.
