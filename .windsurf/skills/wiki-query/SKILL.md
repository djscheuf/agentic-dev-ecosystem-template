---
name: wiki-query
description: Read the project wiki (vault/) before starting any non-trivial task. Surfaces relevant decisions, ownership, incidents, and glossary entries for the task at hand.
---

# Wiki Query

Before touching the code, check what the team already knows.

## When to Run

- Any task the user describes as "investigate", "add", "change", "fix", "migrate", "deploy", or "refactor"
- Any task that mentions a specific service, feature, or endpoint
- Not needed for: trivial one-liners, docs-only typo fixes, mechanical rename tasks

## Process

1. **Read `vault/INDEX.md`.** Note relevant pages.
2. **Grep vault/** for keywords from the task description — service names, feature names, technical terms.
3. **Read matching pages in parallel.** Don't read all of vault — only the ones that match.
4. **Summarize what's relevant** in 3–5 bullets for the user, each citing the vault page.
5. **Call out invariants / ADRs that constrain the task.** "ADR-023 says we do X; your task seems to propose Y."
6. **If the vault is silent on the topic**, say so explicitly. Don't make things up.

## Output Format

```
Wiki context for <task>:
- [decisions/ADR-023-rate-limit.md] Current rate limit is token-bucket at Redis, 100/min per user
- [services/api.md] /api/v2/checkout is owned by @alice, SLA 99.9%
- [incidents/2025-12-03-double-charge.md] Related incident — watch for idempotency
- Nothing in vault about <specific-subtopic>; proceeding without prior context.
```

## Never

- Read all of vault/. It grows over time; bounded reads only.
- Skip this step "to save tokens" on a real task. One minute of wiki context saves an hour of wrong-direction work.
- Paraphrase vault content as if it were your own knowledge. Always cite the page.
