# ADR-004: Skill Output Contracts & Sentinel Files

**Date:** 2026-04-29  
**Status:** Accepted

## Decision

Each skill is responsible for:

1. Defining its own output schema
2. Writing a sentinel file to `.process/` upon completion
3. Including task name and verify parameters in the sentinel file

Sentinel files enable deterministic completion detection and parameterized verification.

## Sentinel File Format

Each sentinel file includes:

- **Task name** — The name of the skill that completed (e.g., "expand-story-analysis")
- **Verify params** — Parameters suitable for verification of that skill's output

This allows the verification hook to identify which skill completed and how to verify its output.

## Output Schema

Each skill defines a JSON schema that describes the structure of its output. The schema:

- Is stored in the skill's `schema/` directory
- Defines all required and optional fields
- Is used by agents and verification scripts to understand the skill's output
- May differ from the input schema of downstream skills (adapters handle transformation)

## Verification Hook

A hook monitors the `.process/` directory for new sentinel files. When a sentinel file is written:

1. The hook identifies the skill that completed
2. It invokes the skill's `verify.sh` script with the verify params from the sentinel file
3. The verification script performs quantitative analysis of the skill's output
4. Results are reported back to the workflow

## Related Decisions

- [ADR-003: Skills-Based Architecture with Workflow Coordination](ADR-003-skills-based-architecture.md)
- [ADR-005: Quantitative vs. Qualitative Analysis Separation](ADR-005-analysis-separation.md)
