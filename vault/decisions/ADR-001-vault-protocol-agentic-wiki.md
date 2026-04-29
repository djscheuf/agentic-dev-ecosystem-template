# ADR-001: Vault Protocol for Agentic Wiki

**Date:** 2026-04-29  
**Status:** Accepted

## Decision

We will adopt the vault protocol to create an agentic wiki capable of understanding the structure of this template project for future software factories.

## Rationale

The vault protocol provides a structured, agent-readable documentation system optimized for rapid discovery and comprehension at lower token cost. This enables AI agents to:

- Quickly locate relevant architectural decisions and patterns
- Understand project structure and conventions without extensive context
- Reduce token overhead when querying project knowledge
- Maintain a single source of truth for non-obvious decisions and patterns

## Alternatives Considered

**Hierarchical Documentation Pattern**
- Worked well in other projects but gradually became unwieldy for agents
- Not optimized for rapid read and discovery by AI systems
- Requires more context and token overhead for agents to extract relevant information

## Implementation

The vault is organized into:
- `decisions/` — Architectural Decision Records (ADRs)
- `incidents/` — Postmortems and incident reports
- `services/` — Service/component notes, runbooks, gotchas
- `personas/` — User and stakeholder personas
- `moc/` — Maps of Content (topic hubs linking related pages)
- `glossary.md` — Shared terminology

All vault content is plain markdown, leading with the bottom line, using present tense for current state and past tense for history. Dates are included on decisions to track freshness.

## Related Decisions

- [ADR-002: Software Factory Purpose & Dual Audience](ADR-002-software-factory-dual-audience.md)
