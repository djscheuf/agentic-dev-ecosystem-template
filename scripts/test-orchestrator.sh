#!/usr/bin/env bash
set -e

# Test script for saga orchestrator
# Runs all tests with coverage reporting

echo "Running orchestrator tests..."
echo ""

nix-shell -p python3Packages.pytest python3Packages.pytest-timeout python3Packages.pytest-cov \
  --run "python3 -m pytest orchestrator/tests/ -v --cov=orchestrator --cov-report=term-missing"

echo ""
echo "✅ All tests completed"
