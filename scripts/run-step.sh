#!/usr/bin/env bash
set -e

if [ $# -lt 2 ]; then
    echo "Usage: $0 <step_name> <input_file_path>" >&2
    exit 1
fi

STEP_NAME="$1"
INPUT_FILE_PATH="$2"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

nix-shell -p python3 \
  --run "python3 orchestrator/devin_wrapper.py '$STEP_NAME' '$INPUT_FILE_PATH'"
