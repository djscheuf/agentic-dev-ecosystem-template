# Cadence Local Runbook

Start a local Cadence server with embedded SQLite persistence and the Web UI using Docker Compose.

## Prerequisites

- Docker Engine with `docker compose` support
- No Cassandra, MySQL, or external database required

## Stack

- `docker/docker-compose.yml` — `ubercadence/server:master` with SQLite
- `docker/cadence-sqlite.yaml` — Cadence server configuration
- `docker/cadence-ping.py` — Python client smoke test

## Start the stack

```bash
cd docker
docker compose up -d
```

This runs:

- Cadence frontend, history, matching, and worker services on port `7833`
- Cadence Web UI on `http://localhost:8088`
- SQLite database files in a Docker named volume `cadence-sqlite-data` mounted at `/data`

## Verify services are running

```bash
docker compose ps
nc -z 127.0.0.1 7833
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8088
```

Expected:

- `nc` returns success on port `7833`
- Web UI returns `307` or `200` (redirects to `/domains`)

## Register the workflow domain

```bash
docker compose exec cadence \
  cadence --ad 127.0.0.1:7833 -t grpc \
  --do story-analysis domain register -rd 1
```

Verify:

```bash
docker compose exec cadence \
  cadence --ad 127.0.0.1:7833 -t grpc \
  --do story-analysis domain describe
```

Expected: `Status: REGISTERED`, `RetentionInDays: 1`.

## Task list

Cadence task lists do not require explicit registration. The Story Analysis Workflow uses the `story-analysis` task list per `domain-task-list-retry-config.json`. You can inspect a task list once a Worker is polling it:

```bash
docker compose exec cadence \
  cadence --ad 127.0.0.1:7833 -t grpc \
  --do story-analysis tasklist desc --tl story-analysis
```

Before a Worker is started, this returns `No poller for tasklist`, which is expected.

## Verify the Python client

Install the Python client in a virtual environment:

```bash
cd ../..  # repo root
python3 -m venv .venv
cd .venv/bin && ./pip install cadence-python-client
```

Run the ping test:

```bash
./python ../../docker/cadence-ping.py
```

Expected output includes the `story-analysis` domain name, domain ID, and `Python client connection OK.`

## View the Web UI

Open `http://localhost:8088`.

## Stop the stack

```bash
docker compose down
```

To remove the SQLite data volume as well:

```bash
docker compose down -v
```

## Notes

- Persistence is SQLite; do not use this stack for production workloads.
- The server image is started as `root` in the container so it can initialize the named Docker volume (`/data`).
- Schema setup is performed automatically on the first start by `cadence-server --env docker update-schema` before the server processes begin.
