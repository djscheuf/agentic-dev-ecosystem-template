#!/usr/bin/env bash
# Common utilities for DevBox verification hooks
# Sourced by all hook scripts — not executed directly

set -euo pipefail

# Project root (hooks are always invoked from project dir or via $CLAUDE_PROJECT_DIR)
HOOK_PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"

# Colors (disabled if not a terminal)
if [[ -t 2 ]]; then
  RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
else
  RED=''; GREEN=''; YELLOW=''; BLUE=''; NC=''
fi

# ── JSON helpers ──────────────────────────────────────────────────────────────

# Read stdin once and cache it (hooks receive JSON on stdin)
# Declare as global to persist across subshells
declare -g _STDIN_CACHE=""
declare -g _STDIN_READ=false

# Initialize stdin cache on first load
_init_stdin_cache() {
if [[ "$_STDIN_READ" = "false" ]] && ! [[ -t 0 ]]; then
    _STDIN_CACHE=$(cat 2>/dev/null || true)
    _STDIN_READ=true
  fi
}

# Call initialization immediately when sourced
_init_stdin_cache

read_stdin_json() {
  echo "$_STDIN_CACHE"
}

# Extract a field from the cached stdin JSON
# Usage: get_field '.tool_input.file_path'
get_field() {
  local field="$1"
  if [[ -n "$_STDIN_CACHE" ]]; then
    echo "$_STDIN_CACHE" | jq -r "$field // empty" 2>/dev/null || true
  fi
}

# Detect IDE from stdin JSON structure
# Returns: "claude", "windsurf", "cursor", or "unknown"
detect_ide() {
  local json
  json=$(read_stdin_json)
  if [[ -z "$json" ]]; then
    echo "unknown"
    return
  fi
  # Windsurf uses tool_info + trajectory_id; Claude uses tool_input + session_id
  if echo "$json" | jq -e '.tool_info' &>/dev/null; then
    echo "windsurf"
  elif echo "$json" | jq -e '.tool_input' &>/dev/null; then
    echo "claude"
  elif echo "$json" | jq -e '.edits' &>/dev/null; then
    echo "cursor"
  else
    echo "unknown"
  fi
}

# Get file_path from stdin regardless of IDE format
# Claude: .tool_input.file_path  |  Windsurf: .tool_info.file_path  |  Cursor: .file_path
get_file_path() {
  local result
  result=$(get_field '.tool_input.file_path')
  [[ -n "$result" ]] && echo "$result" && return
  result=$(get_field '.tool_info.file_path')
  [[ -n "$result" ]] && echo "$result" && return
  result=$(get_field '.file_path')
  [[ -n "$result" ]] && echo "$result" && return
}

# Get command string from stdin regardless of IDE format
# Claude: .tool_input.command  |  Windsurf: .tool_info.command_line  |  Cursor: .command
get_command() {
  local result
  result=$(get_field '.tool_input.command')
  [[ -n "$result" ]] && echo "$result" && return
  result=$(get_field '.tool_info.command_line')
  [[ -n "$result" ]] && echo "$result" && return
  result=$(get_field '.command')
  [[ -n "$result" ]] && echo "$result" && return
}

# ── File classification ───────────────────────────────────────────────────────

# Get list of changed files (staged + unstaged) relative to project root
get_changed_files() {
  cd "$HOOK_PROJECT_DIR"
  {
    git diff --name-only HEAD 2>/dev/null || true
    git diff --name-only --cached 2>/dev/null || true
    git diff --name-only 2>/dev/null || true
  } | sort -u
}

# Map file paths to affected monorepo packages
# Returns: space-separated list of package names (core, cli, web)
affected_packages() {
  local files="${1:-$(get_changed_files)}"
  local packages=""

  if echo "$files" | grep -q "^packages/core/"; then
    packages="$packages core"
  fi
  if echo "$files" | grep -q "^packages/cli/"; then
    packages="$packages cli"
  fi
  if echo "$files" | grep -q "^packages/web/"; then
    packages="$packages web"
  fi

  # Root-level TS config changes affect all packages
  if echo "$files" | grep -qE "^(tsconfig|package\.json|pnpm-lock)"; then
    packages="core cli web"
  fi

  echo "$packages" | xargs  # trim whitespace
}

# Check if any files match a pattern
# Usage: has_changes '\.tsx?$'
has_changes() {
  local pattern="$1"
  local files="${2:-$(get_changed_files)}"
  echo "$files" | grep -qE "$pattern" 2>/dev/null
}

# ── Language detection ────────────────────────────────────────────────────────

# Returns space-separated list of languages with changes
detect_languages() {
  local files="${1:-$(get_changed_files)}"
  local langs=""

  if has_changes '\.(ts|tsx)$' "$files"; then
    langs="$langs typescript"
  fi
  if has_changes '\.py$' "$files"; then
    langs="$langs python"
  fi
  if has_changes '\.sh$' "$files"; then
    langs="$langs shell"
  fi
  if has_changes '\.sql$' "$files"; then
    langs="$langs sql"
  fi
  if has_changes '(schema\.ts|migration)' "$files"; then
    langs="$langs database"
  fi
  # Add .NET detection
  if has_changes '\.(cs|csproj)$' "$files"; then
    langs="$langs dotnet"
  fi

  echo "$langs" | xargs
}

# ── Output formatting ────────────────────────────────────────────────────────

# Block an action (exit 2) — message goes to stderr for the IDE to display
block() {
  local message="$1"
  echo -e "${RED}[DevBox Hook] BLOCKED: ${message}${NC}" >&2
  log_entry "ERROR" "$message"
  exit 2
}

# Warn without blocking — message to stderr, continue
warn() {
  local message="$1"
  echo -e "${YELLOW}[DevBox Hook] WARNING: ${message}${NC}" >&2
  log_entry "WARN" "$message"
}

# Success info — to stderr so it doesn't pollute JSON stdout
info() {
  local message="$1"
  echo -e "${GREEN}[DevBox Hook] ${message}${NC}" >&2
  log_entry "INFO" "$message"
}

# Return JSON on stdout (for hooks that need structured output)
json_output() {
  local json="$1"
  echo "$json"
}

# ── Logging helpers ──────────────────────────────────────────────────────────

# Ensure log file is ready (creates .process directory and log file if needed)
# Usage: ensure_log_file
ensure_log_file() {
  local log_dir="$HOOK_PROJECT_DIR/.process"
  local log_file="$log_dir/$(date +%Y%m%d).hooks.log"
  
  mkdir -p "$log_dir" 2>/dev/null || true
  
  # Create log file if it doesn't exist
  if [[ ! -f "$log_file" ]]; then
    touch "$log_file" 2>/dev/null || true
  fi
  
  echo "$log_file"
}

# Append entry to log file with timestamp and log level
# Usage: log_entry "INFO" "message text"
log_entry() {
  local level="$1"
  local message="$2"
  local log_file
  log_file=$(ensure_log_file)
  
  if [[ -w "$log_file" ]]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$level] $message" >> "$log_file"
  fi
}

# ── Execution helpers ─────────────────────────────────────────────────────────

# Run a command and capture result, returning success/failure
# Usage: run_check "typecheck" "pnpm --filter @devbox/core typecheck"
run_check() {
  local name="$1"
  shift
  local output
  local exit_code=0

  info "Running $name..."
  output=$("$@" 2>&1) || exit_code=$?

  if [[ $exit_code -ne 0 ]]; then
    warn "$name failed (exit $exit_code)"
    echo "$output" >&2
  else
    info "$name passed"
  fi

  return $exit_code
}

# Run multiple checks in parallel, collect results
# Usage: run_parallel "check1:cmd1" "check2:cmd2"
# Returns: 0 if all pass, 1 if any fail
run_parallel() {
  local pids=()
  local names=()
  local tmpdir
  tmpdir=$(mktemp -d)
  local i=0

  for spec in "$@"; do
    local name="${spec%%:*}"
    local cmd="${spec#*:}"
    names+=("$name")

    (
      # Execute with bash, replacing script path with "bash script_path"
      if [[ "$cmd" =~ ^([^[:space:]]+\.sh)(.*)$ ]]; then
        bash "${BASH_REMATCH[1]}" ${BASH_REMATCH[2]} > "$tmpdir/$i.out" 2>&1
      else
        bash -c "$cmd" > "$tmpdir/$i.out" 2>&1
      fi
      echo $? > "$tmpdir/$i.exit"
    ) &
    pids+=($!)
    ((i++))
  done

  local all_passed=true
  for j in "${!pids[@]}"; do
    wait "${pids[$j]}" 2>/dev/null || true
    local code
    code=$(cat "$tmpdir/$j.exit" 2>/dev/null || echo "1")
    if [[ "$code" != "0" ]]; then
      warn "${names[$j]} failed:"
      cat "$tmpdir/$j.out" >&2
      all_passed=false
    else
      info "${names[$j]} passed"
    fi
  done

  rm -rf "$tmpdir"
  $all_passed
}

# ── Dual-stack detection (Phase 2A additions) ─────────────────────────────────

# Detect .NET changes
has_dotnet_changes() {
  local files="${1:-$(get_changed_files)}"
  echo "$files" | grep -qE '\.(cs|csproj)$'
}

# Detect TypeScript changes (wrapper for existing logic)
has_typescript_changes() {
  local files="${1:-$(get_changed_files)}"
  echo "$files" | grep -qE '\.(ts|tsx)$'
}

# ── Repository-specific package detection (Phase 3A additions) ────────────────

# Detect UI package changes
affected_ui_packages() {
  local files="${1:-$(get_changed_files)}"
  local packages=""
  
  if echo "$files" | grep -q "^src/ui/apps/tactic-builder/"; then
    packages="$packages @coupon-builder/tactic-builder"
  fi
  if echo "$files" | grep -q "^src/ui/apps/tactic-admin/"; then
    packages="$packages @coupon-builder/tactic-admin"
  fi
  if echo "$files" | grep -q "^src/ui/packages/ui/"; then
    packages="$packages @coupon-builder/ui"
  fi
  if echo "$files" | grep -q "^src/ui/packages/models/"; then
    packages="$packages @coupon-builder/models"
  fi
  
  # Root-level UI changes affect all packages
  if echo "$files" | grep -qE "^src/ui/(package\.json|pnpm-lock\.yaml|tsconfig)"; then
    packages="@coupon-builder/tactic-builder @coupon-builder/tactic-admin @coupon-builder/ui @coupon-builder/models"
  fi
  
  echo "$packages" | xargs
}

# Detect .NET project changes
affected_dotnet_projects() {
  local files="${1:-$(get_changed_files)}"
  local projects=""
  
  if echo "$files" | grep -q "^src/api/src/TacticManagement.Api/"; then
    projects="$projects Api"
  fi
  if echo "$files" | grep -q "^src/api/src/TacticManagement.Application/"; then
    projects="$projects Application"
  fi
  if echo "$files" | grep -q "^src/api/src/TacticManagement.Domain/"; then
    projects="$projects Domain"
  fi
  if echo "$files" | grep -q "^src/api/src/TacticManagement.Infrastructure/"; then
    projects="$projects Infrastructure"
  fi
  
  # Root-level changes affect all projects
  if echo "$files" | grep -qE "^src/api/(tactic-mgmt-api\.sln|Directory\.Build\.props)"; then
    projects="Api Application Domain Infrastructure"
  fi
  
  echo "$projects" | xargs
}
