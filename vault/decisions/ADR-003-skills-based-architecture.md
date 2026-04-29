# ADR-003: Skills-Based Architecture with Workflow Coordination

**Date:** 2026-04-29  
**Status:** Accepted

## Decision

The software factory is primarily skills-based. Workflows are responsible for coordinating the invocation of skills in appropriate sequences. Each skill is a self-contained, composable unit of work.

## Rationale

A skills-based architecture provides:

- **Modularity** — Each skill has a single, well-defined responsibility
- **Composability** — Workflows can combine skills in different sequences for different use cases
- **Testability** — Each skill can be independently verified and improved
- **Reusability** — Skills can be shared across multiple workflows and projects
- **Agent-friendly** — AI agents can understand and orchestrate skills without deep domain knowledge

Workflows serve as the orchestration layer, determining which skills to invoke and in what order, based on the current state and user intent.

## Skill Characteristics

- Self-contained unit of work with clear inputs and outputs
- Defines its own output schema
- Writes a sentinel file upon completion
- Includes a verification script for quantitative analysis
- Named in verb-object-context format (e.g., "create-workstream-plans", "expand-story-analysis")

## Workflow Characteristics

- Sequences skills based on dependencies and user intent
- Monitors sentinel files to detect skill completion
- Passes outputs from one skill as inputs to the next
- Handles error conditions and retry logic

## Related Decisions

- [ADR-002: Software Factory Purpose & Dual Audience](ADR-002-software-factory-dual-audience.md)
- [ADR-004: Skill Output Contracts & Sentinel Files](ADR-004-skill-output-contracts.md)
