# Local Quickstart

Two ways to get a Cadence server running locally. Prefer the SQLite path unless you need
Cassandra/MySQL parity with production.

## Option A: Embedded SQLite (fastest, no Docker)

```bash
git clone https://github.com/cadence-workflow/cadence.git
cd cadence
make bins
make install-schema-sqlite
./cadence-server --zone sqlite start
```

Open the Web UI at `http://localhost:8088`.

## Option B: Docker Compose (closer to production topology)

```bash
git clone https://github.com/cadence-workflow/cadence.git
cd cadence/docker && docker-compose up
```

Keep this running in a terminal. This brings up Cassandra + the full Cadence service.

## Register a domain

A **domain** must exist before you can start any workflow in it. Using the CLI (see
[../05-api-and-cli/cli-reference.md](../05-api-and-cli/cli-reference.md) for full CLI usage):

```bash
# local binary build
cadence --do test-domain domain register -rd 1

# or, against the docker-compose stack, via the CLI docker image
docker run --network=host --rm ubercadence/cli:master --do test-domain domain register -rd 1
```

`-rd 1` sets a 1-day workflow history retention — fine for local dev. Verify with:

```bash
cadence --do test-domain domain describe
```

## Run a worker + workflow

1. Write a Worker process that connects to the service (`127.0.0.1:7833` by default for the SQLite
   quickstart), registers your workflow/activity functions, and polls a task list.
2. Start the worker.
3. Start the workflow via CLI or client code:

```bash
cadence --domain test-domain workflow start --et 60 --tl test-worker \
  --workflow_type main.helloWorldWorkflow --input '"World"'
```

For full runnable code see [../examples/go/](../examples/go/) and
[../examples/python/](../examples/python/), and the SDK-specific guides in
[../02-go-client/workflows-and-workers.md](../02-go-client/workflows-and-workers.md) or
[../03-python-client/setup-and-workers.md](../03-python-client/setup-and-workers.md).

## Troubleshooting server startup

- `docker-compose up` failing: `docker pull ubercadence/server:master-auto-setup` and retry, or
  `docker system prune --all` if the local docker environment is corrupted.
- Cassandra not coming up: `docker logs -f docker-cassandra-1`
- Cadence service not coming up: `docker logs -f docker-cadence-1`
- Cadence Web not coming up: `docker logs -f docker-cadence-web-1`
- "connection refused" from a containerized CLI/client on Docker 18.03+: use
  `host.docker.internal` instead of `localhost` as the frontend address.

For deeper issues once workflows are running, see [../06-debugging/troubleshooting-playbook.md](../06-debugging/troubleshooting-playbook.md).
