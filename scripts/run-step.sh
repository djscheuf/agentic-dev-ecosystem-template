#!/usr/bin/env bash
# Run a specific step through the Devin wrapper
#
# Usage: ./scripts/run-step.sh <step_name> <input_file>
#
# Examples:
#   ./scripts/run-step.sh extract-story-intent docs/example.md
#   ./scripts/run-step.sh my-step path/to/input.txt
#
# The script will:
# 1. Validate that the step directory exists
# 2. Validate that the input file exists
# 3. Run the step through devin_wrapper.py with the input file
# 4. Display the results

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Function to print error and exit
error() {
    echo -e "${RED}ERROR: $1${NC}" >&2
    exit 1
}

# Function to print info
info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

# Function to print warning
warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Function to print usage
usage() {
    cat << EOF
Usage: $(basename "$0") <step_name> <input_file>

Arguments:
  step_name    Name of the step directory (e.g., extract-story-intent)
  input_file   Path to the input file to process

Examples:
  $(basename "$0") extract-story-intent docs/example.md
  $(basename "$0") my-step path/to/input.txt

The script will run the step through devin_wrapper.py with the specified input file.
EOF
}

# Validate arguments
if [[ $# -lt 2 ]]; then
    echo "Error: Missing required arguments" >&2
    usage
    exit 1
fi

STEP_NAME="$1"
INPUT_FILE="$2"

# Validate step directory exists
STEP_DIR="$PROJECT_ROOT/steps/$STEP_NAME"
if [[ ! -d "$STEP_DIR" ]]; then
    error "Step directory not found: $STEP_DIR"
fi

# Validate step.json exists
STEP_JSON="$STEP_DIR/step.json"
if [[ ! -f "$STEP_JSON" ]]; then
    error "step.json not found in step directory: $STEP_JSON"
fi

# Validate input file exists
if [[ ! -f "$INPUT_FILE" ]]; then
    error "Input file not found: $INPUT_FILE"
fi

# Get absolute path of input file
INPUT_FILE_ABS="$(cd "$(dirname "$INPUT_FILE")" && pwd)/$(basename "$INPUT_FILE")"

# Print execution info
info "Running step: $STEP_NAME"
info "Input file: $INPUT_FILE_ABS"
info "Step directory: $STEP_DIR"
echo ""

# Run the step through devin_wrapper
cd "$PROJECT_ROOT"

info "Executing devin_wrapper..."
python orchestrator/devin_wrapper.py "$STEP_JSON" "$INPUT_FILE_ABS"
EXIT_CODE=$?

echo ""
if [[ $EXIT_CODE -eq 0 ]]; then
    info "Step completed successfully"
else
    warn "Step failed with exit code: $EXIT_CODE"
fi

exit $EXIT_CODE
