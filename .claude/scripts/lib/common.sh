#!/usr/bin/env bash
# Common utilities for Claude Code hook scripts
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

# Get the Claude Code hook event name from stdin (PreToolUse, PostToolUse, SessionEnd, ...)
get_hook_event() {
  get_field '.hook_event_name'
}

# Get the tool name from stdin (Edit, Write, Read, Bash, ...)
get_tool_name() {
  get_field '.tool_name'
}

# Get file_path from stdin (Claude Code tool_input shape: .tool_input.file_path)
get_file_path() {
  get_field '.tool_input.file_path'
}

# Get command string from stdin (Claude Code Bash tool_input shape: .tool_input.command)
get_command() {
  get_field '.tool_input.command'
}

# Get the transcript path for the current session (present on most hook events)
get_transcript_path() {
  get_field '.transcript_path'
}

# Get the session id for the current session
get_session_id() {
  get_field '.session_id'
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

  echo "$langs" | xargs
}

# ── Output formatting ────────────────────────────────────────────────────────

# Block an action (exit 2) — PreToolUse/PostToolUse read stderr as the block reason
block() {
  local message="$1"
  echo -e "${RED}[Claude Hook] BLOCKED: ${message}${NC}" >&2
  log_entry "ERROR" "$message"
  exit 2
}

# Warn without blocking — message to stderr, continue
warn() {
  local message="$1"
  echo -e "${YELLOW}[Claude Hook] WARNING: ${message}${NC}" >&2
  log_entry "WARN" "$message"
}

# Success info — to stderr so it doesn't pollute JSON stdout
info() {
  local message="$1"
  echo -e "${GREEN}[Claude Hook] ${message}${NC}" >&2
  log_entry "INFO" "$message"
}

# ── Logging helpers ──────────────────────────────────────────────────────────

# Ensure log file is ready (creates .process directory and log file if needed)
# Usage: ensure_log_file
ensure_log_file() {
  local log_dir="$HOOK_PROJECT_DIR/.process"
  local log_file="$log_dir/$(date +%Y%m%d).hooks.log"

  mkdir -p "$log_dir" 2>/dev/null || true

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
