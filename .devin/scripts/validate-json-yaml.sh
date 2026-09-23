#!/usr/bin/env bash
# Post-write validation: confirm JSON/YAML files the agent just wrote actually
# parse. Catches malformed configs, fixtures, and eval suites immediately
# instead of letting them fail later in a promptfoo run or CI.
# Triggered after edit/write tool calls (see .devin/hooks.json).

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

# Get edited/written file from hook stdin
file_path=$(get_file_path)

if [[ -z "$file_path" ]]; then
  exit 0
fi

# Resolve relative to project root
if [[ "$file_path" != /* ]]; then
  file_path="$HOOK_PROJECT_DIR/$file_path"
fi

if [[ ! -f "$file_path" ]]; then
  exit 0
fi

# Run from the project root so node can resolve node_modules (js-yaml)
cd "$HOOK_PROJECT_DIR"

case "$file_path" in
  *.json)
    if ! error=$(python3 -c "
import json, sys
try:
    with open(sys.argv[1], encoding='utf-8') as f:
        json.load(f)
except Exception as e:
    print(f'{type(e).__name__}: {e}')
    sys.exit(1)
" "$file_path" 2>&1); then
      block "Invalid JSON in $file_path\n\n$error"
    fi
    info "JSON OK: $file_path"
    ;;

  *.yml|*.yaml)
    if ! error=$(node -e "
const yaml = require('js-yaml');
const fs = require('fs');
try {
  yaml.load(fs.readFileSync(process.argv[1], 'utf8'));
} catch (e) {
  console.log(e.message);
  process.exit(1);
}
" "$file_path" 2>&1); then
      block "Invalid YAML in $file_path\n\n$error"
    fi
    info "YAML OK: $file_path"
    ;;

  *)
    exit 0
    ;;
esac

exit 0
