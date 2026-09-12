#!/usr/bin/env bash
# Tears down what scripts/start-workflow-engine.sh brought up:
#
#   1. Stops the `orchestrator.worker` process (and its whole nix-shell
#      process group) started by start-workflow-engine.sh.
#   2. Brings down the Cadence docker network (docker/docker-compose.yml).
#
# Usage: scripts/stop-workflow-engine.sh

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
RUN_DIR="$SCRIPT_DIR/.run"
WORKER_PID_FILE="$RUN_DIR/worker.pid"
WORKER_PGID_FILE="$RUN_DIR/worker.pgid"
COMPOSE_FILE="$REPO_ROOT/docker/docker-compose.yml"

log() { printf '[stop-workflow-engine] %s\n' "$1"; }

# --- 1. Stop the worker -----------------------------------------------------
if [[ -f "$WORKER_PGID_FILE" ]]; then
  pgid="$(cat "$WORKER_PGID_FILE" 2>/dev/null || true)"
  if [[ -n "$pgid" ]] && kill -0 "-$pgid" 2>/dev/null; then
    log "Stopping worker process group (pgid $pgid)..."
    kill -TERM "-$pgid" 2>/dev/null || true
    for _ in $(seq 1 10); do
      kill -0 "-$pgid" 2>/dev/null || break
      sleep 1
    done
    if kill -0 "-$pgid" 2>/dev/null; then
      log "Worker didn't stop in time, sending SIGKILL..."
      kill -KILL "-$pgid" 2>/dev/null || true
    fi
    log "Worker stopped."
  else
    log "No running worker process found for pgid $pgid."
  fi
else
  log "No worker.pgid file found (worker may not be running, or was started outside this script)."
fi
rm -f "$WORKER_PID_FILE" "$WORKER_PGID_FILE"

# --- 2. Stop the docker network ---------------------------------------------
log "Stopping Cadence docker network..."
docker compose -f "$COMPOSE_FILE" down || log "WARNING: docker compose down failed (see output above)."

log "Workflow engine stopped."
