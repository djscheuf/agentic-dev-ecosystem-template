# ADR-025: Shared Skills Live in `.agents/skills/` with a Generated `.claude/skills/` Mirror

**Date:** 2026-10-01

Skills are authored once in `.agents/skills/<name>/`. Devin discovers that
directory natively; `scripts/sync-agent-skills.sh` mirrors it into
`.claude/skills/` for Claude Code. `.devin/skills/` no longer exists in this repo.

## Context

We want the same skill set usable by both Devin (CLI/Desktop/Local) and Claude
Code without copy-pasting folders. The constraint is discovery paths — neither
tool accepts a configurable skills directory:

| Agent | Project skills paths |
|---|---|
| Devin | `.agents/skills/`, `.devin/skills/`, `.windsurf/skills/` |
| Claude Code | `.claude/skills/` (plus legacy `.claude/commands/`) |

Devin supports the `.agents` skill standard, so `.agents/skills/` is discovered
by Devin out of the box. Claude Code has no `.agents/` support, so a mirror is
required for Claude.

Alternatives considered:

- **Symlink `.claude/skills` → `.agents/skills`** — zero maintenance, but fragile
  in git and across OSes; rejected in favor of an explicit, portable script.
- **Canonical in `.devin/skills/` + mirror both ways** — would put Devin-visible
  skills in two discovered locations (`.agents/` and `.devin/`) if `.agents/`
  were also used, causing duplicates.
- **Nested canonical (e.g. `.agents/source/skills/`)** — avoids dual discovery,
  but adds a nonstandard indirection when `.agents/skills/` already works for Devin.

## Decision

1. `.agents/skills/` is the single source of truth. All skill authoring and
   editing happens there; `AGENTS.md` documents this.
2. `scripts/sync-agent-skills.sh` copies `.agents/skills/` → `.claude/skills/`
   and rewrites `.agents/skills` and `.devin/skills` path references inside text
   files to `.claude/skills`, so mirrored instructions point at the mirror.
   Knowledge skills describing the tools' own path vocabularies
   (`devin-desktop/`, `claude-code/`) are copied verbatim to keep their docs
   factually correct.
3. The mirror is protected by a sha256 manifest
   (`.claude/skills/.sync-manifest`): files hand-edited in `.claude/skills/` are
   reported as conflicts and skipped unless `--force` is passed. `--prune`
   removes unmodified stale files; `--dry-run` previews everything.
4. No `.devin/skills/` mirror is maintained — Devin reads `.agents/skills/`
   directly, avoiding duplicate discovery.
5. `.claude/skills/` is committed so Claude users get skills without running the
   sync; treat it as a generated artifact.
6. Historical run artifacts under `docs/reqs/` and past ADRs keep their original
   `.devin/skills/` references — they are records, not living docs.

## Consequences

- Functional references (workflow schema paths in `src/`, evals, the
  `post-edit-verify-skill.sh` hook, `.devin/config.local.json` permissions)
  all point at `.agents/skills/`.
- Every skill-content change requires a sync run for the Claude mirror; a stale
  mirror is detectable via `scripts/sync-agent-skills.sh --dry-run`.
- A skill instruction that tells an agent to *write* into the skills tree is
  rewritten to `.claude/skills/` in the mirror — AGENTS.md covers the rule that
  authoring always happens in `.agents/skills/`; this is a known limitation of
  the mechanical rewrite.
