#!/usr/bin/env bash
# Secret detection: scan staged/changed files for accidentally committed secrets
# Mirrors the programmatic checks from the Secret Detection agent
# Usage: verify-secrets.sh [--scope=staged|changed|all]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

cd "$HOOK_PROJECT_DIR"

SCOPE="changed"
for arg in "$@"; do
  case "$arg" in
    --scope=*) SCOPE="${arg#*=}" ;;
  esac
done

# ── Collect files to scan ────────────────────────────────────────────────────
files=""
case "$SCOPE" in
  staged)  files=$(git diff --cached --name-only 2>/dev/null) ;;
  changed) files=$(get_changed_files) ;;
  all)     files=$(git ls-files 2>/dev/null) ;;
esac

if [[ -z "$files" ]]; then
  info "No files to scan for secrets"
  exit 0
fi

# ── Secret patterns ───────────────────────────────────────────────────────────
# Common secret/credential patterns
SECRET_PATTERNS=(
  # API keys and tokens
  'AKIA[0-9A-Z]{16}'                           # AWS Access Key ID
  'sk-[a-zA-Z0-9]{20,}'                        # OpenAI/Stripe secret keys
  'ghp_[a-zA-Z0-9]{36}'                        # GitHub personal access token
  'gho_[a-zA-Z0-9]{36}'                        # GitHub OAuth token
  'github_pat_[a-zA-Z0-9_]{82}'                # GitHub fine-grained PAT
  'xox[bpors]-[a-zA-Z0-9-]+'                   # Slack tokens

  # Generic patterns
  '(password|passwd|pwd)\s*[:=]\s*["\x27][^"\x27]{8,}'  # Password assignments
  '(secret|token|key)\s*[:=]\s*["\x27][A-Za-z0-9+/=]{20,}'  # Generic secrets
  'Bearer\s+[A-Za-z0-9\-._~+/]+=*'            # Bearer tokens in code

  # Private keys
  '-----BEGIN (RSA |EC |DSA )?PRIVATE KEY-----'
  '-----BEGIN OPENSSH PRIVATE KEY-----'

  # Connection strings with credentials
  '(mysql|postgres|mongodb|redis)://[^:]+:[^@]+@'
  
  # Azure-specific patterns (for this repository)
  'DefaultEndpointsProtocol=https;AccountName=[^;]+;AccountKey=[A-Za-z0-9+/=]{88}'
  'Data Source=[^;]+;Initial Catalog=[^;]+;User ID=[^;]+;Password=[^;]+'
  'Server=[^;]+;Database=[^;]+;User Id=[^;]+;Password=[^;]+'
)

failures=0
findings=0

info "Scanning ${SCOPE} files for secrets..."

for file in $files; do
  # Skip binary files, lock files, and the hook scripts themselves
  if [[ "$file" =~ \.(png|jpg|gif|ico|woff|ttf|lock|dll|exe|bin)$ ]]; then
    continue
  fi
  if [[ "$file" =~ ^scripts/hooks/ ]]; then
    continue
  fi
  if [[ ! -f "$file" ]]; then
    continue
  fi

  for pattern in "${SECRET_PATTERNS[@]}"; do
    matches=$(grep -nE "$pattern" "$file" 2>/dev/null || true)
    if [[ -n "$matches" ]]; then
      # Skip if it's in a test file and looks like a placeholder
      if [[ "$file" =~ \.(test|spec|Test)\.(ts|js|cs)$ ]] && echo "$matches" | grep -qiE '(fake|mock|test|example|placeholder|dummy)'; then
        continue
      fi

      warn "Potential secret in $file:"
      echo "$matches" | head -3 >&2
      ((findings++))
    fi
  done
done

if [[ $findings -gt 0 ]]; then
  block "Found $findings potential secret(s) in ${SCOPE} files. Review and remove before committing."
fi

info "Secret scan clean — no secrets detected"
exit 0
