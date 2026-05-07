#!/usr/bin/env bash
# Hard reset Devin: clear cache and re-authenticate
#
# Usage: ./scripts/hard-reset-devin.sh
#
# This script performs a complete reset of Devin by:
# 1. Clearing the Devin cache directory
# 2. Running the auth login flow to re-authenticate
#
# Use this when you encounter cache-related issues or need to switch accounts.

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

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

# Determine cache directory based on OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    CACHE_DIR="$HOME/Library/Caches/devin"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    CACHE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/devin"
else
    CACHE_DIR="$HOME/.devin-cache"
fi

info "Starting Devin hard reset..."
echo ""

# Clear Devin cache
if [ -d "$CACHE_DIR" ]; then
    info "Clearing Devin cache at: $CACHE_DIR"
    rm -rf "$CACHE_DIR"
    info "Cache cleared"
else
    warn "No cache directory found at: $CACHE_DIR"
fi

# Run auth login flow
echo ""
info "Running Devin auth login..."
devin auth login
EXIT_CODE=$?

echo ""
if [[ $EXIT_CODE -eq 0 ]]; then
    info "Devin hard reset complete"
else
    error "Auth login failed with exit code: $EXIT_CODE"
fi

exit $EXIT_CODE
