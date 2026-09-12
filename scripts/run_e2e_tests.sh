#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [[ ! -x "$REPO_ROOT/.venv/bin/python" ]]; then
  printf '[run_e2e_tests] ERROR: .venv not found -- run: nix-shell --run "python3 -m venv .venv && .venv/bin/pip install -r src/orchestrator/requirements.txt"\n' >&2
  exit 1
fi

QUOTED_ARGS=()
for arg in "$@"; do
  QUOTED_ARGS+=("$(printf '%q' "$arg")")
done

RUN_CMD="PYTHONPATH=src .venv/bin/python -m pytest tests/e2e ${QUOTED_ARGS[*]}"

cd "$REPO_ROOT"
exec nix-shell --run "$RUN_CMD"
