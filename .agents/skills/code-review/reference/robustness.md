# Robustness: security, edge cases, errors, performance

Core question: **What could go wrong, and how would we know?**

## Input validation and edge cases
- Is untrusted input validated and sanitized before use?
- What happens with null, empty, zero, negative, very large, and malformed values?
- Boundary conditions: off-by-one, inclusive versus exclusive limits, empty collections, single-element collections.
- What happens with unexpected types, such as non-numeric input where a number is expected?
- What happens on partial failure, retry, or duplicate submission?

## Error handling and logging
- Are errors handled at a sensible boundary rather than swallowed or caught everywhere?
- Do failures produce informative messages without exposing sensitive details (stack traces, internal identifiers, secrets)?
- If the code breaks on an unexpected condition, how would a developer find where and why? Is logging in place at the right level?
- Do fail-safe paths (fallbacks, audit logging, cleanup) exist and work? These are often untested.

## Security
- Are secrets kept out of source, logs, and responses?
- Is authentication and authorization consistent and applied on every relevant path? Check for a missed endpoint.
- Is data access scoped to the caller (object-level authorization)?
- Queries parameterized, output encoded, file paths and URLs validated?
- Are new dependencies necessary and from trusted sources?
- Is sensitive data minimized, protected in transit and at rest where applicable?

Treat security findings by scale and criticality: a gap affecting every call is `blocking`; a hardening opportunity on an internal, low-risk path may be a `suggestion`.

## Performance
Look for obvious problems, not micro-optimizations.
- **Load-then-filter**: reading all records into memory and filtering afterward. Push filtering to the data store.
- **N+1 queries**: queries inside loops.
- Blocking or slow calls on hot paths.
- Redundant work in tight loops, unnecessary copying or transformation.
- Unbounded growth: collections, caches, logs, queues without limits.
- Missing pagination or limits on list endpoints.

Do not demand optimization without evidence of a problem, but do flag scalability risks that will bite as data grows. Recommend the simplest fix first (for example, database-level filtering, using the ORM's translation with raw SQL as a fallback), plus tests that lock in the behavior.

## Testability of robustness
- Are dependencies injectable so failure modes can be simulated?
- Are there tests for the error paths named above?

## Priorities
- Exploitable or data-corrupting gaps, or a failure affecting every call: `blocking`.
- Scalability risk, missing validation on a constrained path: `suggestion`.
- Message wording, extra logging: `comment`.
