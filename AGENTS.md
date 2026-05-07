## Vault Protocol

This repo maintains a compounding `vault/` of project knowledge. The vault is the
first place you look and the last place you write.

### At Session Start

1. Read `vault/INDEX.md` to see what's documented.
2. If the task touches a topic with an existing vault page, read it BEFORE reading source code.
3. If the task touches a topic WITHOUT a vault page, note it — you'll write one at the end.

### During the Session

- When you encounter something non-obvious (a gotcha, a decision, a pattern):
  - Check if `vault/` has a page for it. If yes, do not re-discover it.
  - If no, note it for end-of-session capture.
- Never cite internal knowledge the user can't verify. If it's not in `vault/`, don't claim it as fact.

### At Session End

When the session produced a decision, solved a non-obvious problem, or established a pattern:

1. Write a vault page. Location rules (match the directories that exist in this repo's `vault/`):
   - Decisions (why we chose X over Y) → `vault/decisions/ADR-NNN-<slug>.md` (next sequential number)
   - Postmortems → `vault/incidents/<YYYY-MM-DD>-<slug>.md`
   - Service/component notes, runbooks, gotchas → `vault/services/<service>.md`
   - Personas → `vault/personas/<name>.md`
   - Cross-cutting topic hubs → `vault/moc/<topic>.md` (a "Map of Content" that links related pages)
   - Glossary entries → append to `vault/glossary.md`
2. Update `vault/INDEX.md` to link the new page.
3. One page per topic. If a page grows > 300 lines, split it (same threshold as `vault/INDEX.md`).

### Writing Style

- Plain markdown. No front-matter unless required by another tool.
- Lead with the **bottom line**: the answer in the first 2 lines, details below.
- Use the present tense for current state ("we use Redis") and past tense for history ("we tried DynamoDB, it didn't fit").
- Include dates on decisions — these age, and agents need to know how fresh a claim is.
- No prose walls. Headers, lists, tables, code blocks.

### Never

- Put secrets in `vault/`. It's git-tracked — assume public.
- Put PII in `vault/`. Same reason.
- Write vault pages that duplicate code comments. The vault is for things code can't express.
- Leave `vault/INDEX.md` out of date. The index is the API.

### Skills Involved

- `wiki-query` — called first, reads relevant vault pages for the current intent.
- `wiki-update` — called last, writes new or updated pages before session ends.