#!/usr/bin/env bash
# Manually invoke a single Story Analysis Activity against a real Cadence
# server, by starting a SingleActivityWorkflow that schedules exactly that
# Activity on the already-running orchestrator worker.
#
# Assumes scripts/start-workflow-engine.sh has already brought the local
# Cadence stack and orchestrator worker up.
#
# Usage: scripts/run-single-activity --domain <domain> --task-list <task_list> <activity_name> <input_file>
#        scripts/run-single-activity --help
#
# See src/story_analysis_workflow/run_single_activity.py for the underlying
# logic and src/orchestrator/single_activity_workflow.py for the probe
# workflow it starts.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

log() { printf '[run-single-activity] %s\n' "$1"; }

if [[ ! -x "$REPO_ROOT/.venv/bin/python" ]]; then
  log "ERROR: .venv not found -- run: nix-shell --run \"python3 -m venv .venv && .venv/bin/pip install -r src/orchestrator/requirements.txt\""
  exit 1
fi

# Shell-quote each argument individually so activity names/paths survive
# interpolation into the nix-shell --run string.
QUOTED_ARGS=()
for arg in "$@"; do
  QUOTED_ARGS+=("$(printf '%q' "$arg")")
done

RUN_CMD="PYTHONPATH=src .venv/bin/python -m story_analysis_workflow.run_single_activity ${QUOTED_ARGS[*]}"

cd "$REPO_ROOT"
exec nix-shell --run "$RUN_CMD"
