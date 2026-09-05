#!/usr/bin/env bash
# Brings up the Story Analysis Workflow engine from a flat start:
#
#   1. Starts the local Cadence docker network (docker/docker-compose.yml)
#      and waits for the server to report healthy.
#   2. Registers the `story-analysis` domain if it doesn't exist yet.
#   3. Starts the `orchestrator.worker` process in the background and waits
#      until it is actually polling the `story-analysis` task list, then
#      leaves it running.
#
# Aborts and cleans up anything it started if the whole process takes longer
# than TIMEOUT_SECONDS.
#
# Usage:   scripts/start-workflow-engine.sh
# Stop:    scripts/stop-workflow-engine.sh

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
RUN_DIR="$SCRIPT_DIR/.run"
WORKER_LOG="$RUN_DIR/worker.log"
WORKER_PID_FILE="$RUN_DIR/worker.pid"
WORKER_PGID_FILE="$RUN_DIR/worker.pgid"
COMPOSE_FILE="$REPO_ROOT/docker/docker-compose.yml"

TIMEOUT_SECONDS=180
POLL_INTERVAL=2

SECONDS=0
WORKER_STARTED=0

log() { printf '[start-workflow-engine] %s\n' "$1"; }

cleanup() {
  if [[ "$WORKER_STARTED" -eq 1 && -f "$WORKER_PGID_FILE" ]]; then
    local pgid
    pgid="$(cat "$WORKER_PGID_FILE" 2>/dev/null || true)"
    if [[ -n "$pgid" ]] && kill -0 "-$pgid" 2>/dev/null; then
      log "Stopping worker process group (pgid $pgid) after failure/timeout."
      kill -TERM "-$pgid" 2>/dev/null || true
    fi
  fi
}

die() {
  log "ERROR: $1"
  cleanup
  exit 1
}

deadline_exceeded() { (( SECONDS >= TIMEOUT_SECONDS )); }

require_deadline() {
  if deadline_exceeded; then
    die "Timed out after ${TIMEOUT_SECONDS}s waiting for: $1"
  fi
}

mkdir -p "$RUN_DIR"

command -v docker >/dev/null 2>&1 || die "docker is not on PATH"
command -v nix-shell >/dev/null 2>&1 || die "nix-shell is not on PATH"
[[ -x "$REPO_ROOT/.venv/bin/python" ]] || die \
  ".venv not found -- run: nix-shell --run \"python3 -m venv .venv && .venv/bin/pip install -r src/orchestrator/requirements.txt\""

# The worker shells out to `devin` for every skill Activity (see
# `src/orchestrator/devin_harness.py`). Fail fast here instead of letting it
# surface later as a buried SkillActivityError in the worker log -- see
# `vault/services/orchestrator-harness.md` for why plain `devin auth login`
# can be insufficient (browser/Windsurf-session-bridged tokens can be flaky).
#
# NOTE: `devin auth status` always exits 0, even when logged out -- it must
# be checked by matching its output text, not its exit code.
command -v devin >/dev/null 2>&1 || die "devin CLI is not on PATH"
if devin auth status 2>&1 | grep -qi "not logged in"; then
  die "devin CLI is not authenticated. Run: devin auth login --force-manual-token-flow (see vault/services/orchestrator-harness.md)"
fi

TOPOLOGY_JSON="$(cd "$REPO_ROOT" && nix-shell --run \
  "PYTHONPATH=src '$REPO_ROOT/.venv/bin/python' -m orchestrator.worker inspect-catalog")" \
  || die "failed to inspect workflow catalog"
WORKER_COUNT="$(TOPOLOGY_JSON="$TOPOLOGY_JSON" "$REPO_ROOT/.venv/bin/python" -c \
  'import json, os; print(json.loads(os.environ["TOPOLOGY_JSON"])["worker_count"])')" \
  || die "invalid inspect-catalog output"
mapfile -t DOMAINS < <(TOPOLOGY_JSON="$TOPOLOGY_JSON" "$REPO_ROOT/.venv/bin/python" -c \
  'import json, os; print("\n".join(json.loads(os.environ["TOPOLOGY_JSON"])["domains"]))')
mapfile -t ROUTES < <(TOPOLOGY_JSON="$TOPOLOGY_JSON" "$REPO_ROOT/.venv/bin/python" -c \
  'import json, os; print("\n".join(f"{route['"'"'domain'"'"']}\t{route['"'"'task_list'"'"']}" for route in json.loads(os.environ["TOPOLOGY_JSON"])["routes"]))')

# --- 1. Start the docker network (Cadence server + Web UI) -----------------
log "Starting Cadence docker network..."
docker compose -f "$COMPOSE_FILE" up -d || die "docker compose up failed"

log "Waiting for the cadence container to become healthy..."
until [[ "$(docker inspect -f '{{.State.Health.Status}}' cadence 2>/dev/null)" == "healthy" ]]; do
  require_deadline "cadence container to become healthy"
  sleep "$POLL_INTERVAL"
done
log "Cadence server is healthy (gRPC localhost:7833, Web UI http://localhost:8088)."

# --- 2. Register the domain if needed --------------------------------------
for domain in "${DOMAINS[@]}"; do
  log "Checking domain '$domain'..."
  if ! docker compose -f "$COMPOSE_FILE" exec -T cadence \
        cadence --ad 127.0.0.1:7833 -t grpc --do "$domain" domain describe >/dev/null 2>&1; then
    log "Domain '$domain' not found, registering it..."
    docker compose -f "$COMPOSE_FILE" exec -T cadence \
      cadence --ad 127.0.0.1:7833 -t grpc --do "$domain" domain register -rd 1 \
      || die "failed to register domain '$domain'"
  else
    log "Domain '$domain' already registered."
  fi
done

if [[ "$WORKER_COUNT" -eq 0 ]]; then
  log "No configured Workers; Cadence is ready with no worker routes."
  exit 0
fi

# --- 3. Start the worker in the background, and leave it running -----------
log "Starting the orchestrator worker (log: $WORKER_LOG)..."
: > "$WORKER_LOG"
(
  cd "$REPO_ROOT"
  exec nix-shell --run "PYTHONPATH=src '$REPO_ROOT/.venv/bin/python' -m orchestrator.worker"
) >"$WORKER_LOG" 2>&1 &
WORKER_JOB_PID=$!
echo "$WORKER_JOB_PID" > "$WORKER_PID_FILE"
ps -o pgid= -p "$WORKER_JOB_PID" | tr -d ' ' > "$WORKER_PGID_FILE"
WORKER_STARTED=1
disown

# Fail fast if the worker process dies immediately (e.g. import errors).
sleep 1
WORKER_PID="$(cat "$WORKER_PID_FILE")"
if ! kill -0 "$WORKER_PID" 2>/dev/null; then
  die "worker process exited immediately, see $WORKER_LOG"
fi

for route in "${ROUTES[@]}"; do
  IFS=$'\t' read -r domain task_list <<< "$route"
  log "Waiting for the worker to start polling domain '$domain' task list '$task_list'..."
  until docker compose -f "$COMPOSE_FILE" exec -T cadence \
          cadence --ad 127.0.0.1:7833 -t grpc --do "$domain" tasklist desc --tl "$task_list" >/dev/null 2>&1; do
    require_deadline "worker to start polling domain '$domain' task list '$task_list'"
    if ! kill -0 "$WORKER_PID" 2>/dev/null; then
      die "worker process died while starting, see $WORKER_LOG"
    fi
    sleep "$POLL_INTERVAL"
  done
done

log "Workflow engine is ready."
log "  Cadence gRPC:    localhost:7833"
log "  Cadence Web UI:  http://localhost:8088"
for route in "${ROUTES[@]}"; do
  IFS=$'\t' read -r domain task_list <<< "$route"
  log "  Worker route:    $domain / $task_list (poller pid $WORKER_PID)"
done
log "  Worker log:      $WORKER_LOG"
log "Stop everything with: $SCRIPT_DIR/stop-workflow-engine.sh"
