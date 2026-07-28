#!/usr/bin/env bash
# verify.sh - Verify failing test sentinel structure
# Validates sentinel against schema using jq

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

# Track failures
FAILURES=()

# Add failure message
fail() {
  FAILURES+=("$1")
}

# Exit with error if any failures
exit_if_failed() {
  if [[ ${#FAILURES[@]} -gt 0 ]]; then
    echo -e "${RED}Verification failed:${NC}" >&2
    printf '%s\n' "${FAILURES[@]}" >&2
    exit 2
  fi
}

# Verify sentinel JSON structure
verify_sentinel_structure() {
  local sentinel_path="$1"
  
  if [[ ! -f "$sentinel_path" ]]; then
    fail "Sentinel file not found: $sentinel_path"
    return
  fi
  
  # Validate JSON is well-formed
  if ! jq empty "$sentinel_path" 2>/dev/null; then
    fail "Sentinel file is not valid JSON: $sentinel_path"
    return
  fi
  
  local sentinel
  sentinel=$(jq '.' "$sentinel_path")
  
  # Check required top-level properties
  local required_props=("task" "status" "verify_params")
  for prop in "${required_props[@]}"; do
    if ! jq -e ".$prop" <<< "$sentinel" &>/dev/null; then
      fail "Schema validation failed: Missing required property '$prop'"
    fi
  done
  
  # Validate status is one of the allowed values
  if jq -e '.status' <<< "$sentinel" &>/dev/null; then
    local status
    status=$(jq -r '.status' <<< "$sentinel")
    if [[ ! "$status" =~ ^(pending|in_progress|completed|failed)$ ]]; then
      fail "Schema validation failed: status must be one of 'pending', 'in_progress', 'completed', or 'failed', got '$status'"
    fi
  fi
  
  # Check verify_params structure
  if jq -e '.verify_params' <<< "$sentinel" &>/dev/null; then
    local verify_params
    verify_params=$(jq '.verify_params' <<< "$sentinel")
    
    # Check required verify_params fields
    local required_verify_fields=("failing_test_path" "failing_test_name")
    for field in "${required_verify_fields[@]}"; do
      if ! jq -e ".$field" <<< "$verify_params" &>/dev/null || [[ $(jq -r ".$field" <<< "$verify_params") == "null" ]]; then
        fail "Schema validation failed: Missing required verify_params field '$field'"
      fi
    done
  fi
}

# Verify test cases file exists
verify_test_cases_file() {
  local test_cases_path="$1"
  
  if [[ -z "$test_cases_path" ]]; then
    fail "test_cases_path is empty"
    return
  fi
  
  if [[ ! -f "$test_cases_path" ]]; then
    fail "Test cases file not found: $test_cases_path"
    return
  fi
}

# Verify failing test file exists
verify_failing_test_file() {
  local failing_test_path="$1"
  
  if [[ -z "$failing_test_path" ]]; then
    fail "failing_test_path is empty"
    return
  fi
  
  if [[ ! -f "$failing_test_path" ]]; then
    fail "Failing test file not found: $failing_test_path"
    return
  fi
}

# Check if Node.js dependencies are installed
check_node_dependencies() {
  local framework="$1"
  
  if [[ ! -d "$PROJECT_DIR/node_modules" ]]; then
    fail "node_modules directory not found. Dependencies must be installed before verification."
    fail "Please ensure 'npm install' completes successfully before writing the sentinel file."
    return 1
  fi
  
  # Check if specific framework is installed
  case "$framework" in
    jest)
      if [[ ! -d "$PROJECT_DIR/node_modules/jest" ]]; then
        fail "Jest not found in node_modules. Dependencies may still be installing."
        fail "Ensure 'npm install' completes before writing the sentinel file."
        fail "If npm install has completed, verify Jest is listed in package.json devDependencies."
        return 1
      fi
      ;;
    mocha)
      if [[ ! -d "$PROJECT_DIR/node_modules/mocha" ]]; then
        fail "Mocha not found in node_modules. Dependencies may still be installing."
        fail "Ensure 'npm install' completes before writing the sentinel file."
        fail "If npm install has completed, verify Mocha is listed in package.json devDependencies."
        return 1
      fi
      ;;
    vitest)
      if [[ ! -d "$PROJECT_DIR/node_modules/vitest" ]]; then
        fail "Vitest not found in node_modules. Dependencies may still be installing."
        fail "Ensure 'npm install' completes before writing the sentinel file."
        fail "If npm install has completed, verify Vitest is listed in package.json devDependencies."
        return 1
      fi
      ;;
  esac
  
  return 0
}

# Detect test framework based on file and project structure
detect_test_framework() {
  local test_file="$1"
  local file_ext="${test_file##*.}"
  
  case "$file_ext" in
    js|mjs|cjs|ts|tsx)
      if [[ -f "$PROJECT_DIR/package.json" ]]; then
        if grep -q '"vitest"' "$PROJECT_DIR/package.json" 2>/dev/null; then
          echo "vitest"
        elif grep -q '"jest"' "$PROJECT_DIR/package.json" 2>/dev/null; then
          echo "jest"
        elif grep -q '"mocha"' "$PROJECT_DIR/package.json" 2>/dev/null; then
          echo "mocha"
        else
          echo "unknown"
        fi
      else
        echo "unknown"
      fi
      ;;
    py)
      if command -v pytest &>/dev/null; then
        echo "pytest"
      elif command -v python -m unittest &>/dev/null; then
        echo "unittest"
      else
        echo "unknown"
      fi
      ;;
    cs)
      if command -v dotnet &>/dev/null; then
        echo "dotnet-test"
      else
        echo "unknown"
      fi
      ;;
    go)
      echo "go-test"
      ;;
    *)
      echo "unknown"
      ;;
  esac
}

# Run test with Mocha
run_mocha_test() {
  local test_file="$1"
  local test_name="$2"
  
  if ! command -v npx &>/dev/null; then
    fail "npx not found - cannot run Mocha tests"
    return 1
  fi
  
  if ! command -v timeout &>/dev/null; then
    fail "timeout command not found - cannot enforce test timeout"
    return 1
  fi
  
  cd "$PROJECT_DIR" || return 1
  timeout 5s npx mocha "$test_file" --grep "^${test_name}$" &>/dev/null
  local exit_code=$?
  
  if [[ $exit_code -eq 124 ]]; then
    fail "Test '$test_name' timed out after 5 seconds"
    return 124
  fi
  
  return $exit_code
}

# Run test with Jest
run_jest_test() {
  local test_file="$1"
  local test_name="$2"
  
  if ! command -v npx &>/dev/null; then
    fail "npx not found - cannot run Jest tests"
    return 1
  fi
  
  if ! command -v timeout &>/dev/null; then
    fail "timeout command not found - cannot enforce test timeout"
    return 1
  fi
  
  cd "$PROJECT_DIR" || return 1
  timeout 5s npx jest "$test_file" -t "$test_name" &>/dev/null
  local exit_code=$?
  
  if [[ $exit_code -eq 124 ]]; then
    fail "Test '$test_name' timed out after 5 seconds"
    return 124
  fi
  
  return $exit_code
}

# Run test with Vitest
run_vitest_test() {
  local test_file="$1"
  local test_name="$2"
  
  if ! command -v npx &>/dev/null; then
    fail "npx not found - cannot run Vitest tests"
    return 1
  fi
  
  if ! command -v timeout &>/dev/null; then
    fail "timeout command not found - cannot enforce test timeout"
    return 1
  fi
  
  cd "$PROJECT_DIR" || return 1
  timeout 5s npx vitest run "$test_file" -t "$test_name" &>/dev/null
  local exit_code=$?
  
  if [[ $exit_code -eq 124 ]]; then
    fail "Test '$test_name' timed out after 5 seconds"
    return 124
  fi
  
  return $exit_code
}

# Run test with pytest
run_pytest_test() {
  local test_file="$1"
  local test_name="$2"
  
  if ! command -v pytest &>/dev/null; then
    fail "pytest not found - cannot run pytest tests"
    return 1
  fi
  
  if ! command -v timeout &>/dev/null; then
    fail "timeout command not found - cannot enforce test timeout"
    return 1
  fi
  
  cd "$PROJECT_DIR" || return 1
  timeout 5s pytest "$test_file" -k "$test_name" &>/dev/null
  local exit_code=$?
  
  if [[ $exit_code -eq 124 ]]; then
    fail "Test '$test_name' timed out after 5 seconds"
    return 124
  fi
  
  return $exit_code
}

# Run test with dotnet test
run_dotnet_test() {
  local test_file="$1"
  local test_name="$2"
  
  if ! command -v dotnet &>/dev/null; then
    fail "dotnet not found - cannot run .NET tests"
    return 1
  fi
  
  if ! command -v timeout &>/dev/null; then
    fail "timeout command not found - cannot enforce test timeout"
    return 1
  fi
  
  local test_dir
  test_dir=$(dirname "$test_file")
  
  cd "$PROJECT_DIR" || return 1
  timeout 5s dotnet test --filter "FullyQualifiedName~$test_name" --no-build --verbosity quiet &>/dev/null
  local exit_code=$?
  
  if [[ $exit_code -eq 124 ]]; then
    fail "Test '$test_name' timed out after 5 seconds"
    return 124
  fi
  
  return $exit_code
}

# Run test with Go
run_go_test() {
  local test_file="$1"
  local test_name="$2"
  
  if ! command -v go &>/dev/null; then
    fail "go not found - cannot run Go tests"
    return 1
  fi
  
  if ! command -v timeout &>/dev/null; then
    fail "timeout command not found - cannot enforce test timeout"
    return 1
  fi
  
  local test_dir
  test_dir=$(dirname "$test_file")
  cd "$test_dir" || return 1
  timeout 5s go test -run "^${test_name}$" &>/dev/null
  local exit_code=$?
  
  if [[ $exit_code -eq 124 ]]; then
    fail "Test '$test_name' timed out after 5 seconds"
    return 124
  fi
  
  return $exit_code
}

# Run the failing test and verify it fails (Red phase of TDD)
run_failing_test() {
  local failing_test_path="$1"
  local failing_test_name="$2"
  
  echo "Running test '$failing_test_name' from '$failing_test_path'..." >&2
  
  # Detect framework
  local framework
  framework=$(detect_test_framework "$failing_test_path")
  
  if [[ "$framework" == "unknown" ]]; then
    fail "Unable to detect test framework for: $failing_test_path"
    return
  fi
  
  echo "Detected test framework: $framework" >&2
  
  # Check dependencies for Node.js frameworks
  if [[ "$framework" == "jest" || "$framework" == "mocha" || "$framework" == "vitest" ]]; then
    if ! check_node_dependencies "$framework"; then
      return
    fi
  fi
  
  # Run the test and capture exit code
  local exit_code
  case "$framework" in
    mocha)
      run_mocha_test "$failing_test_path" "$failing_test_name"
      exit_code=$?
      ;;
    jest)
      run_jest_test "$failing_test_path" "$failing_test_name"
      exit_code=$?
      ;;
    vitest)
      run_vitest_test "$failing_test_path" "$failing_test_name"
      exit_code=$?
      ;;
    pytest)
      run_pytest_test "$failing_test_path" "$failing_test_name"
      exit_code=$?
      ;;
    dotnet-test)
      run_dotnet_test "$failing_test_path" "$failing_test_name"
      exit_code=$?
      ;;
    go-test)
      run_go_test "$failing_test_path" "$failing_test_name"
      exit_code=$?
      ;;
    *)
      fail "Unsupported test framework: $framework"
      return
      ;;
  esac
  
  # In TDD Red phase, we EXPECT the test to fail
  # Exit code 0 means test passed, which is BAD
  # Exit code 124 means timeout, which is also BAD
  # Other non-zero exit codes mean test failed, which is GOOD
  if [[ $exit_code -eq 124 ]]; then
    # Timeout already added to failures in the runner function
    fail "Test '$failing_test_name' timed out after 5 seconds, we should check for infinite loops, or other issues. We expected test to run and fail (Red Phase)."
    return
  elif [[ $exit_code -eq 0 ]]; then
    fail "Test '$failing_test_name' PASSED, but it should FAIL in the Red phase of TDD"
  else
    echo -e "${GREEN}✓${NC} Test '$failing_test_name' failed as expected (Red phase)" >&2
  fi
}

# Main execution
main() {
  local sentinel_path="$1"
  
  if [[ -z "$sentinel_path" ]]; then
    echo "Usage: verify.sh <sentinel_file>" >&2
    exit 2
  fi
  
  if [[ ! -f "$sentinel_path" ]]; then
    echo "Sentinel file not found: $sentinel_path" >&2
    exit 2
  fi
  
  # Extract test details from sentinel
  local sentinel
  sentinel=$(jq '.' "$sentinel_path")
  local test_cases_path
  local failing_test_path
  local failing_test_name
  
  test_cases_path=$(jq -r '.verify_params.test_cases_path // empty' <<< "$sentinel")
  failing_test_path=$(jq -r '.verify_params.failing_test_path // empty' <<< "$sentinel")
  failing_test_name=$(jq -r '.verify_params.failing_test_name // empty' <<< "$sentinel")
  
  if [[ -z "$test_cases_path" ]] || [[ -z "$failing_test_path" ]] || [[ -z "$failing_test_name" ]]; then
    echo "Sentinel file missing required verify_params fields" >&2
    exit 2
  fi
  
  # Run verifications
  verify_sentinel_structure "$sentinel_path"
  verify_test_cases_file "$test_cases_path"
  verify_failing_test_file "$failing_test_path"
  run_failing_test "$failing_test_path" "$failing_test_name"
  
  # Delete sentinel file after verification
  rm -f "$sentinel_path"

  # Exit if any failures
  exit_if_failed
  
  echo -e "${GREEN}Verification passed${NC}" >&2
}

main "$@"
