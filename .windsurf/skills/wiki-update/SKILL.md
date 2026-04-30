---
name: wiki-update
description: Maintain the project wiki in vault/. Use at the end of any session that produced a decision, fact, or state change. Extracts entities, updates topic pages, adds cross-links, never deletes. Pairs with the post_cascade_response_with_transcript hook.
---

# Wiki Update

After a session, update the project's `vault/` so future sessions have the context.

## When to Run

The session did at least one of:

- Made an architectural decision → `vault/decisions/ADR-NNN.md`
- Learned who owns a system → `vault/people/<name>.md` + link from `vault/services/<svc>.md`
- Fixed an incident → `vault/incidents/YYYY-MM-DD-<short>.md` with root cause + fix + invariant to add to `AGENTS.md`
- Added a term of art → `vault/glossary.md`
- Chose a library / service / pattern → capture the choice + the alternatives considered

If none of those happened, output "no wiki updates needed" and stop.

## Process

1. **Read `vault/INDEX.md`** to know the current shape of the wiki.
2. **For each new fact, prefer updating an existing page.** Only create new pages for genuinely new topics.
3. **Use `[[wikilinks]]` between entities.** If you reference a page that doesn't exist, create a stub with a "TODO" note.
4. **Append-only.** Never rewrite existing content. Mark stale sections with `> **Stale as of YYYY-MM-DD:** ...` and add the new section below.
5. **Update `vault/INDEX.md`** with any new pages.
6. **Number ADRs sequentially** — check the existing count in `vault/decisions/` before picking a number.
7. **Output a one-line summary** of what you updated.

## ADR Template

```markdown
# ADR-NNN: <Decision title>

**Status:** Proposed | Accepted | Deprecated | Superseded by ADR-XXX
**Date:** YYYY-MM-DD
**Author:** <name or @role>

## Context
Why are we deciding this now? What forces are at play?

## Decision
What are we doing?

## Consequences
### Positive
-

### Negative
-

### Neutral / Follow-up
-

## Alternatives Considered
- **<Alternative 1>** — rejected because...
- **<Alternative 2>** — rejected because...
```

## Incident Template

```markdown
# YYYY-MM-DD: <One-line title>

**Severity:** SEV1 | SEV2 | SEV3
**Duration:** X hours
**Customer impact:** <facts, numbers>

## Timeline
- HH:MM — first symptom observed
- HH:MM — on-call paged
- HH:MM — mitigation started
- HH:MM — resolved

## Root cause
One paragraph. Factual, not blame-assigning.

## Contributing factors
- Factor 1
- Factor 2

## What went well
-

## What could have gone better
-

## Action items
- [ ] **<Owner>** — <action> — by <date>

## Invariant to add to AGENTS.md
(If this incident reveals a rule that should be constitutional, write it here and add to AGENTS.md.)
```

## Never

- Delete or rewrite existing vault content.
- Create duplicate pages — always search first.
- Assume you know something; read the code or session transcript first.
- Write a wiki entry that's longer than it needs to be. The wiki is for *lookup*, not narrative.
