#!/usr/bin/env bash
# Start a Story Design Workflow execution for a given analysis JSON file.
#
# Usage: scripts/kickoff-design-story <analysis-json>
#
# Assumes scripts/start-workflow-engine.sh has already brought the local
# Cadence stack and orchestrator worker up. See src/story_design_workflow/cli.py
# for the underlying `story-design-cli` command.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

log() { printf '[kickoff-design-story] %s\n' "$1"; }

if [[ $# -ne 1 ]]; then
  log "Usage: ${BASH_SOURCE[0]} <analysis-json>"
  exit 1
fi

ANALYSIS_FILE="$1"

if [[ ! -f "$ANALYSIS_FILE" ]]; then
  # The supplied path may be a typo or shorthand; try to find it by basename.
  target_basename="$(basename "$ANALYSIS_FILE")"
  mapfile -d '' -t matches < <(
    find "$REPO_ROOT" -type f -name "$target_basename" \
      ! -path "*/.git/*" ! -path "*/.venv/*" ! -path "*/.process/*" ! -path "*/.devin/*" -print0 2>/dev/null
  )

  if [[ ${#matches[@]} -eq 1 ]]; then
    log "Discovered analysis file: ${matches[0]}"
    ANALYSIS_FILE="${matches[0]}"
  elif [[ ${#matches[@]} -gt 1 ]]; then
    log "ERROR: multiple analysis files named '$target_basename' found:"
    for match in "${matches[@]}"; do
      log "  $match"
    done
    exit 1
  else
    log "ERROR: analysis file not found: $ANALYSIS_FILE"
    exit 1
  fi
fi

if [[ ! -x "$REPO_ROOT/.venv/bin/python" ]]; then
  log "ERROR: .venv not found -- run: nix-shell --run \"python3 -m venv .venv && .venv/bin/pip install -r src/orchestrator/requirements.txt\""
  exit 1
fi

# Resolve to an absolute path so it stays valid after we cd to REPO_ROOT.
ANALYSIS_FILE_ABS="$(cd "$(dirname "$ANALYSIS_FILE")" && pwd)/$(basename "$ANALYSIS_FILE")"

# `printf '%q'` shell-quotes the path for safe interpolation into the nix-shell command.
START_CMD="PYTHONPATH=src .venv/bin/python -m story_design_workflow.cli start $(printf '%q' "$ANALYSIS_FILE_ABS")"

cd "$REPO_ROOT"
exec nix-shell --run "$START_CMD"
