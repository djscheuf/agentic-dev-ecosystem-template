# ADR-017: Agentic EDD Quality Ratchet

**Status:** Proposed
**Date:** 2026-09-12
**Author:** djscheufl

## Bottom line

Agentic EDD refinement commits only measured pass-count or meaningful required-coverage improvements. It confirms apparent regressions, removes repeatable regressions, escalates flaky evidence, and stops after three consecutive confirmed harmful proposals.

## Context

A pass percentage alone cannot represent EDD progress. Adding valuable evaluations for previously uncovered requirements can lower the percentage while preserving quality, whereas adding duplicate evaluations can inflate suite size without value. LLM-backed evaluations can also vary between runs, so one degraded result is insufficient evidence for an automatic revert.

The detailed feature requirements are in `docs/reqs/agentic-edd-refinement/feature-description.md`.

## Decision

- Compare every candidate with the current best accepted state, not only the original baseline.
- Accept an increased absolute passing count when required test-case coverage does not decrease.
- Also accept meaningful coverage of previously uncovered required test cases when the prior absolute passing count is preserved, even if pass percentage falls.
- Do not treat duplicate coverage or suite growth after all required test cases are covered as improvement.
- Rerun an apparently degraded candidate unchanged before classifying it as a regression.
- Revert a confirmed regression, then reevaluate the restored accepted state before continuing.
- Escalate non-reproduced or inconclusive degradation evidence to a human without an autonomous commit or revert decision.
- Preserve semantic change summaries and all degradation, confirmation, revert, and recovery evidence for later planning.
- Stop after three consecutive confirmed-regression proposals regardless of remaining iteration or token budget.

## Consequences

### Positive

- Accepted commits form a monotonic quality ratchet under a stable measurement context.
- Valuable test coverage can grow without pass percentage becoming a misleading blocker.
- Agents receive enough failed-attempt memory to avoid repeating harmful changes.
- Human judgment resolves flaky or incomparable evidence.

### Negative

- Suspected regressions require additional long-running evaluation executions.
- Coverage adequacy needs a deterministic mapping between required test cases and evaluations.
- Revert recovery failures can stop the workflow before its normal budgets are exhausted.

### Neutral / Follow-up

- Define the exact test-case-to-evaluation coverage contract during implementation design.
- Keep human-approved evaluation expectation changes in a separate measurement context.
- Integrate regression confirmation and recovery runs into workflow-level token, duration, and artifact reporting.

## Alternatives Considered

- **Use pass percentage only** — rejected because meaningful new coverage can reduce the percentage without reducing the absolute passing count.
- **Accept any increase in evaluation count** — rejected because duplicate or already-satisfied coverage adds no required value.
- **Revert after one degraded run** — rejected because one LLM-backed evaluation may be flaky.
- **Continue until the normal budget after repeated regressions** — rejected because three consecutive confirmed harmful proposals indicate that autonomous refinement is no longer productive.
