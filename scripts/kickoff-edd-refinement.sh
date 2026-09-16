#!/usr/bin/env bash
# Start an EDD Refinement Workflow execution for a given input document.
#
# Usage: scripts/kickoff-edd-refinement <edd-input.json>
#
# Assumes scripts/start-workflow-engine.sh has already brought the local
# Cadence stack up. See src/edd_refinement_workflow/cli.py for the underlying
# `edd-refinement-cli` command.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

log() { printf '[kickoff-edd-refinement] %s\n' "$1"; }

if [[ $# -ne 1 ]]; then
  log "Usage: ${BASH_SOURCE[0]} <edd-input.json>"
  exit 1
fi

INPUT_FILE="$1"

if [[ ! -f "$INPUT_FILE" ]]; then
  target_basename="$(basename "$INPUT_FILE")"
  mapfile -d '' -t matches < <(
    find "$REPO_ROOT" -type f -name "$target_basename" \
      ! -path "*/.git/*" ! -path "*/.venv/*" ! -path "*/.process/*" ! -path "*/.devin/*" -print0 2>/dev/null
  )

  if [[ ${#matches[@]} -eq 1 ]]; then
    log "Discovered input file: ${matches[0]}"
    INPUT_FILE="${matches[0]}"
  elif [[ ${#matches[@]} -gt 1 ]]; then
    log "ERROR: multiple input files named '$target_basename' found:"
    for match in "${matches[@]}"; do
      log "  $match"
    done
    exit 1
  else
    log "ERROR: input file not found: $INPUT_FILE"
    exit 1
  fi
fi

if [[ ! -x "$REPO_ROOT/.venv/bin/python" ]]; then
  log "ERROR: .venv not found -- run: nix-shell --run \"python3 -m venv .venv && .venv/bin/pip install -r src/orchestrator/requirements.txt\""
  exit 1
fi

INPUT_FILE_ABS="$(cd "$(dirname "$INPUT_FILE")" && pwd)/$(basename "$INPUT_FILE")"

START_CMD="PYTHONPATH=src .venv/bin/python -m edd_refinement_workflow.cli start $(printf '%q' "$INPUT_FILE_ABS")"

cd "$REPO_ROOT"
exec nix-shell --run "$START_CMD"
