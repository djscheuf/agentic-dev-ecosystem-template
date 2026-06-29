#!/usr/bin/env bash
set -e

if [ $# -lt 1 ]; then
    echo "Usage: $0 <saga_name> [input_files...]" >&2
    exit 1
fi

SAGA_NAME="$1"
shift
INPUT_FILES=("$@")

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

SAGA_DEF_PATH="sagas/${SAGA_NAME}.json"

if [ ! -f "$SAGA_DEF_PATH" ]; then
    echo "Error: Saga definition not found: $SAGA_DEF_PATH" >&2
    exit 1
fi

nix-shell -p python3 \
  --run "python3 orchestrator/run_saga.py '$SAGA_DEF_PATH' ${INPUT_FILES[@]}"
