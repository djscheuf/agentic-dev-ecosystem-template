---
name: code-review
description: Conduct a value-first code review of a branch, PR, or diff. Identifies the requirements under review, scopes the changes, checks story fidelity, tests, implementation and architecture, then sweeps for reuse and refactoring opportunities, and produces a structured YAML review document. Use when asked to review a PR, branch, diff, or AI-generated code.
---

# Code Review

A value-first review starts from *why the change exists*, not from syntax. Requirements first, then tests as evidence, then implementation, then refactoring opportunities. The output is a structured YAML review document.

## Inputs
- **Target**: branch, PR, or diff. Default: the current branch against its merge-base with the default branch.
- **Requirements location** (optional): story, ticket, spec, or doc paths. If not given, Phase 1 finds them.
- **Output path**: ask the user at invocation. Default to `code-review-<branch>.yaml` in the working directory.

The code may be human- or AI-written. Apply `reference/ai-generated-code.md` only when it is relevant.

## Non-negotiables
1. **No review without requirements.** Identify the story or stories first. If none can be found, ask the user; if none exist, infer requirements from the PR description and commits, and record a `blocking` `story` comment about the gap.
2. **Intent before syntax.** Understand what the change is for before judging how it is written.
3. **Skip what machines catch.** Do not comment on formatting, spacing, or style that a linter or formatter enforces. Spend attention on design, intent, and future risk.
4. **Evidence for every comment.** Each comment names concrete source locations and an observed gap. Verify a claim by searching before asserting it (for example, do not claim "no end-to-end tests exist" without checking).
5. **Review the code, not the person.** Do no harm, do good: the aim is a better codebase and a better developer.
6. **Record comments in the order discovered.** Assign priority at the end, not while discovering.

## Process

| # | Phase | Question it answers | Read before starting |
|---|-------|---------------------|----------------------|
| 1 | Scope | What requirements are under review, and what actually changed? | `phases/1-scope.md` |
| 2 | Story fidelity | Does the change honor the story and its acceptance criteria? | `phases/2-story-fidelity.md` |
| 3 | Tests | Is there evidence that each acceptance criterion is met and stays met? | `phases/3-test-review.md` |
| 4 | Implementation and architecture | Does it fit the system, and will it create tomorrow's problems? | `phases/4-implementation.md` |
| 5 | Refactor and reuse | Looking beyond the diff, what should be reused or refactored? | `phases/5-refactor-and-reuse.md` |

Finish by synthesizing: assign priorities, write general commentary and the verdict, and emit the YAML using `output/review-template.md`. Word every comment per `output/feedback-style.md`.

Work the phases in order. Phases 1 to 4 review the diff; Phase 5 is the only phase that looks outside it.

## Output contract (summary)

```yaml
code_review:
  identified_requirements: []   # stories, criteria, and where they came from
  impacted_scope: []            # what changed, and what it touches
  general_commentary:
    verdict: approve | approve-with-suggestions | request-changes
    summary: ""
  review_comments:              # in order discovered
    - description: ""           # the observed gap
      type: story               # story|testing|design|implementation|security|performance|readability|documentation|refactor
      impact: ""                # why it matters
      recommendation: ""        # direct
      guidance: ""              # question-style, coaching
      priority: blocking        # blocking|suggestion|comment
      locations: []             # path:line-range
      in_diff: true
```

**Priority** is judged from impact, scale, and criticality together:
- `blocking`: must be fixed before merge (e.g. a security gap affecting every call, a broken acceptance criterion).
- `suggestion`: should be addressed, or tracked as follow-up (e.g. a gap affecting several workflows, a scalability risk).
- `comment`: optional or informational (e.g. a typo in a label).

Full schema, rubric, and a worked example: `output/review-template.md`.

## Reference index
Consult these from the phases, or directly when a question arises.

| File | Consult when |
|------|--------------|
| `reference/readability-and-trust.md` | Judging names, structure, cognitive load, hidden side effects |
| `reference/design-principles.md` | Judging responsibilities, coupling, abstractions, layering, architectural fit |
| `reference/robustness.md` | Checking security, input validation, error handling, edge cases, performance |
| `reference/test-quality.md` | Judging whether tests are meaningful and readable |
| `reference/ai-generated-code.md` | The code was produced or assisted by an AI agent |
| `reference/smells-and-refactors.md` | Naming a smell and recommending a concrete refactor |
| `output/review-template.md` | Writing the YAML, assigning priority, choosing the verdict |
| `output/feedback-style.md` | Wording comments, guidance, and general commentary |
