#!/usr/bin/env bash
# Sync canonical agent skills from .agents/skills/ into agent-specific mirrors.
#
# Canonical source of truth: .agents/skills/<name>/SKILL.md
#   - Devin CLI / Devin Desktop discovers .agents/skills/ natively; no mirror needed.
#   - Claude Code only discovers .claude/skills/, so we mirror there.
#
# During the copy, literal path references to the canonical/other-agent trees are
# rewritten so instructions inside the mirror point at the mirror itself:
#   .agents/skills  -> .claude/skills
#   .devin/skills   -> .claude/skills
#
# Edit-safety: a manifest (.claude/skills/.sync-manifest) records the sha256 of
# every synced file. A destination file that differs from both the synced source
# AND the manifest is treated as hand-edited and skipped unless --force is given.
#
# Usage: scripts/sync-agent-skills.sh [--dry-run] [--force] [--prune]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

SOURCE_DIR="$REPO_ROOT/.agents/skills"
DEST_DIR="$REPO_ROOT/.claude/skills"
MANIFEST_NAME=".sync-manifest"
MANIFEST_PATH="$DEST_DIR/$MANIFEST_NAME"

DRY_RUN=0
FORCE=0
PRUNE=0

usage() {
  cat <<EOF
Usage: ${BASH_SOURCE[0]} [options]

Sync agent skills from the canonical source to the Claude Code skills mirror.

  Source:      .agents/skills/   (canonical, edit here; Devin reads it directly)
  Destination: .claude/skills/   (generated mirror; do not hand-edit)

Options:
  -n, --dry-run   Show what would be created/updated/skipped/deleted without
                  changing anything.
  -f, --force     Overwrite destination files that were modified by hand since
                  the last sync (normally reported as conflicts and skipped).
  -p, --prune     Delete destination files/dirs that no longer exist in the
                  source, but only when they were not hand-modified.
  -h, --help      Show this help.

Behavior:
  - Text files are copied with path references rewritten so instructions in the
    mirror point at .claude/skills/ (both .agents/skills and .devin/skills are
    rewritten). Binary files are copied verbatim.
  - Files whose contents already match are skipped.
  - A destination file that differs from both the synced source and the recorded
    manifest hash is a conflict: skipped and reported unless --force.
  - With --prune, destination paths missing from the source are deleted only if
    they match the manifest (i.e. were not hand-edited); otherwise reported.
  - Exit status is 0 unless a conflict was skipped (then 2) or an error occurs.

Examples:
  scripts/sync-agent-skills.sh --dry-run     # preview
  scripts/sync-agent-skills.sh               # sync
  scripts/sync-agent-skills.sh --force --prune   # overwrite edits + remove stale
EOF
}

log()  { printf '[sync-agent-skills] %s\n' "$1"; }
warn() { printf '[sync-agent-skills] WARN: %s\n' "$1" >&2; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    -n|--dry-run) DRY_RUN=1; shift ;;
    -f|--force)   FORCE=1; shift ;;
    -p|--prune)   PRUNE=1; shift ;;
    -h|--help)    usage; exit 0 ;;
    *) warn "unknown option: $1"; usage >&2; exit 1 ;;
  esac
done

[[ -d "$SOURCE_DIR" ]] || { warn "source directory not found: $SOURCE_DIR"; exit 1; }

sha_of() { sha256sum "$1" | awk '{print $1}'; }

# Load previous manifest: relpath -> synced sha256
declare -A MANIFEST=()
if [[ -f "$MANIFEST_PATH" ]]; then
  while IFS=$'\t' read -r h rel; do [[ -n "$rel" ]] && MANIFEST["$rel"]="$h"; done < "$MANIFEST_PATH"
fi

declare -A NEW_MANIFEST=()
declare -A SOURCE_FILES=()
created=0; updated=0; skipped=0; conflicts=0; pruned=0; conflicted_paths=()

# --- plan + execute sync -----------------------------------------------------
while IFS= read -r -d '' src; do
  rel="${src#"$SOURCE_DIR"/}"
  [[ "$rel" == "$MANIFEST_NAME" ]] && continue
  dest="$DEST_DIR/$rel"
  SOURCE_FILES["$rel"]=1

  # Build synced content (path rewrite for text files). Knowledge skills that
  # document the tools' own path vocabularies are copied verbatim.
  tmp="$(mktemp)"
  case "$rel" in
    devin-desktop/*|claude-code/*|create-knowledge-skill/*) REWRITE=0 ;;
    *) REWRITE=1 ;;
  esac
  if [[ "$REWRITE" -eq 1 ]] && grep -Iq . "$src"; then
    sed -e 's|\.agents/skills|.claude/skills|g' -e 's|\.devin/skills|.claude/skills|g' "$src" > "$tmp"
  else
    cp "$src" "$tmp"
  fi
  src_hash="$(sha_of "$tmp")"

  if [[ -f "$dest" ]]; then
    dest_hash="$(sha_of "$dest")"
    if [[ "$dest_hash" == "$src_hash" ]]; then
      skipped=$((skipped+1)); NEW_MANIFEST["$rel"]="$src_hash"; rm -f "$tmp"; continue
    fi
    if [[ "$FORCE" -eq 0 && "${MANIFEST[$rel]:-}" != "$dest_hash" ]]; then
      conflicts=$((conflicts+1)); conflicted_paths+=("$rel")
      log "CONFLICT (hand-edited, skipping): $rel"
      rm -f "$tmp"; continue
    fi
    log "would update: $rel"; [[ "$DRY_RUN" -eq 1 ]] || { cp "$tmp" "$dest"; }
    updated=$((updated+1)); NEW_MANIFEST["$rel"]="$src_hash"; rm -f "$tmp"; continue
  fi

  log "would create: $rel"
  if [[ "$DRY_RUN" -eq 0 ]]; then
    mkdir -p "$(dirname "$dest")"
    cp "$tmp" "$dest"
    chmod --reference="$src" "$dest" 2>/dev/null || true
  fi
  created=$((created+1)); NEW_MANIFEST["$rel"]="$src_hash"; rm -f "$tmp"
done < <(find "$SOURCE_DIR" -type f -print0 | sort -z)

# --- plan + execute prune -----------------------------------------------------
if [[ "$PRUNE" -eq 1 && -d "$DEST_DIR" ]]; then
  while IFS= read -r -d '' dest; do
    rel="${dest#"$DEST_DIR"/}"
    [[ "$rel" == "$MANIFEST_NAME" ]] && continue
    [[ -n "${SOURCE_FILES[$rel]:-}" ]] && continue
    dest_hash="$(sha_of "$dest")"
    if [[ "${MANIFEST[$rel]:-}" == "$dest_hash" ]]; then
      log "would delete (stale): $rel"; [[ "$DRY_RUN" -eq 1 ]] || rm -f "$dest"; pruned=$((pruned+1))
    else
      log "kept (stale, hand-edited): $rel"
    fi
  done < <(find "$DEST_DIR" -type f -print0 | sort -z)
  if [[ "$DRY_RUN" -eq 0 ]]; then
    find "$DEST_DIR" -mindepth 1 -type d -empty -delete 2>/dev/null || true
  fi
fi

# --- write manifest -----------------------------------------------------------
if [[ "$DRY_RUN" -eq 0 ]]; then
  mkdir -p "$DEST_DIR"
  : > "$MANIFEST_PATH"
  for rel in $(printf '%s\n' "${!NEW_MANIFEST[@]}" | sort); do
    printf '%s\t%s\n' "${NEW_MANIFEST[$rel]}" "$rel" >> "$MANIFEST_PATH"
  done
fi

# --- summary ------------------------------------------------------------------
log "created=$created updated=$updated up-to-date=$skipped pruned=$pruned conflicts=$conflicts $([[ $DRY_RUN -eq 1 ]] && echo '(dry-run)')"
if [[ "$conflicts" -gt 0 ]]; then
  warn "conflicted files (rerun with --force to overwrite):"; printf '  %s\n' "${conflicted_paths[@]}"
  exit 2
fi
