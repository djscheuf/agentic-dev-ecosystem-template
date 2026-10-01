---
name: query-code
description: Read the project code (src/) to find existing implementation patterns, and related functionality. Surfaces relevant patterns, services, interfaces, and components for the task at hand.
---

# Code Query

Before touching the code, check what related code already exists.

## When to Run

- As part of assessing current project state. 
- Any task that mentions a specific service, feature, or endpoint
- Not needed for: trivial one-liners, docs-only typo fixes, mechanical rename tasks

## Process

1. **Read the task description** carefully.
2. **Identify relevant domain terms** from the task description.
3. **Grep src/** for keywords from the task description — service names, feature names, technical terms.
4. **Read matching files in parallel.** Don't read all of src/ — only the ones that match.
5. **Summarize what's relevant** in 3–5 bullets for the user, each citing the file path.
7. **If the src/ is silent on the topic**, say so explicitly. Don't make things up.

## Output Format

```
Code context for <task>:
- [src/ui/services/payment.ts] Payment service handles charge creation and refund operations
- [src/api/models/transaction.cs] Transaction model includes status and timestamp fields
- [src/scripts/seed_data.cs] Seed data script for initializing transaction records
- Nothing in src/ about <specific-subtopic>; proceeding without prior context.
```

## Never

- Read all of src/. It grows over time; bounded reads only.
- Skip this step "to save tokens" on a real task. One minute of code context saves an hour of wrong-direction work.
- Paraphrase code content as if it were your own knowledge. Always cite the file path.
