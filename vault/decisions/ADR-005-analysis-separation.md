# ADR-005: Quantitative vs. Qualitative Analysis Separation

**Date:** 2026-04-29  
**Status:** Accepted

## Decision

We separate quantitative and qualitative analysis of skill outputs:

- **Quantitative analysis** is the responsibility of the skill itself via its `verify.sh` script
- **Qualitative analysis** is the responsibility of a dedicated grader skill

This separation enables clear ownership, independent testing, and flexible feedback loops.

## Quantitative Analysis

Each skill's `verify.sh` script performs quantitative verification of its own output:

- Validates output against the defined schema
- Checks for required fields and correct types
- Performs structural and format validation
- Reports pass/fail and any validation errors
- Runs automatically when the skill's sentinel file is written

## Qualitative Analysis

Grader skills (ADR-006) perform qualitative evaluation of upstream skill outputs:

- Assess the quality and correctness of the output beyond schema validation
- Apply domain-specific rubrics to score the output
- Provide detailed feedback for improvement
- Enable agents to iterate on upstream skill inputs based on grader feedback

## Workflow Integration

A typical workflow sequence:

1. Skill executes (e.g., "expand-story-analysis")
2. Skill writes sentinel file
3. Verification hook triggers skill's `verify.sh` (quantitative)
4. Workflow invokes grader skill (e.g., "grade-story-analysis") (qualitative)
5. If grader score is below threshold, workflow reports feedback to agent
6. Agent iterates on input and re-invokes upstream skill

## Related Decisions

- [ADR-004: Skill Output Contracts & Sentinel Files](ADR-004-skill-output-contracts.md)
- [ADR-006: Grader Skill Pattern](ADR-006-grader-skill-pattern.md)
