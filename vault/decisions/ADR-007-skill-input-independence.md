# ADR-007: Skill Input Independence

**Date:** 2026-04-29  
**Status:** Accepted

## Decision

Skills should not maintain copies of their expected input formats. Instead, each skill reads the provided input document(s) directly and derives what it needs from there. Skills should be sufficiently independent that they do not require tight coupling to the output format of preceding skills.

## Rationale

Maintaining copies of input schemas in each skill creates unnecessary coupling and synchronization burden:

- **Schema duplication** — Each skill would need its own copy of upstream output schemas
- **Update burden** — When an earlier skill in the workflow updates its output format, all downstream skills must be updated
- **Maintenance complexity** — Multiple copies of the same schema create inconsistency and drift
- **Reduced flexibility** — Tight coupling makes it harder to reorder skills or reuse them in different workflows

By having each skill read and parse its input documents directly, we achieve:

- **Single source of truth** — Each skill's output schema lives in one place
- **Loose coupling** — Skills can be composed in different orders without schema conflicts
- **Resilience** — Skills can gracefully handle input documents with extra or optional fields
- **Flexibility** — Input documents can be extended without breaking downstream skills

## Implementation

Each skill:

1. Receives input document path(s) as parameters
2. Reads the input document(s) directly
3. Parses and validates the content as needed for its own logic
4. Extracts only the information it requires
5. Does not maintain a local copy of the input schema

Downstream skills do the same with the current skill's output, creating a chain of independent, loosely-coupled transformations.

## Trade-offs

**Advantage:** Loose coupling, reduced maintenance burden, schema flexibility

**Disadvantage:** Each skill must be robust in parsing potentially variable input structures; requires clear documentation of what fields each skill expects to find in its input documents

## Related Decisions

- [ADR-003: Skills-Based Architecture with Workflow Coordination](ADR-003-skills-based-architecture.md)
- [ADR-004: Skill Output Contracts & Sentinel Files](ADR-004-skill-output-contracts.md)
