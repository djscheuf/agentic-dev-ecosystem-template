# Cadence

Local Cadence stack runs SQLite persistence in Docker using `docker/docker-compose.yml`.

## Files

- `docker/docker-compose.yml` — `ubercadence/server:master` + `ubercadence/web:latest`
- `docker/cadence-sqlite.yaml` — server config for SQLite
- `docker/cadence-ping.py` — Python client smoke test
- `docs/reqs/workflow-orchestration/streams/cadence-local-runbook.md` — operator runbook

## Commands

```bash
cd docker
docker compose up -d
docker compose exec cadence \
  cadence --ad 127.0.0.1:7833 -t grpc --do story-analysis domain register -rd 1
```

## Gotchas

- `ubercadence/server:master` runs as the `cadence` (uid 1000) user by default. The compose file sets `user: root` so the container can write the SQLite files in the named Docker volume at `/data`.
- `cadence-sql-tool` in the `ubercadence/server` image does not include the SQLite driver (`unknown driver "sqlite3"` error). Use `cadence-server --root /etc/cadence --env docker update-schema` instead; it applies the SQLite schema from the config file.
- `start-cadence.sh` copies `CADENCE_CONFIG_FILE` to `/etc/cadence/config/docker.yaml` and then runs the configured services. Run the `update-schema` command first, then exec `start-cadence.sh`.
- The Python client `cadence-python-client` on Nix/Linux may need `LD_LIBRARY_PATH` pointed at a `libstdc++.so.6` location because the `grpcio` wheel links it.

## Ports

- `localhost:7833` — gRPC frontend (used by workers and clients)
- `localhost:8088` — Cadence Web UI
