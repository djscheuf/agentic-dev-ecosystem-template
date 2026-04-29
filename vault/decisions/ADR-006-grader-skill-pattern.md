# ADR-006: Grader Skill Pattern

**Date:** 2026-04-29  
**Status:** Accepted

## Decision

Grader skills follow a standardized pattern for qualitative analysis of upstream skill outputs:

1. Named in grade-object-context format (e.g., "grade-story-analysis" for "expand-story-analysis")
2. Define a grade schema (distinct from the input schema) that captures the grading structure
3. Include a rubric file that defines the scoring criteria
4. Use a fixed-floor pass threshold (e.g., 80% minimum)
5. Provide detailed feedback when output does not meet the threshold

## Naming Convention

Grader skills follow the pattern: `grade-<object>-<context>`

- **Upstream skill:** `<verb>-<object>-<context>` (e.g., "expand-story-analysis")
- **Grader skill:** `grade-<object>-<context>` (e.g., "grade-story-analysis")

This naming convention makes the relationship between a skill and its grader immediately clear.

## Grade Schema

The grade schema defines the structure of the grader's output:

- Describes the grading results and feedback
- Is distinct from the input schema (the upstream skill's output schema)
- Includes fields for individual component scores and overall grade
- Includes fields for detailed feedback and improvement suggestions

## Rubric File

Each grader skill includes a `rubric.md` file that defines:

- Scoring criteria for each component being graded
- Point scale (e.g., 0-4 per component)
- Conversion to percentage (e.g., sum of component scores / max possible score * 100)
- Pass threshold (e.g., 80%)
- Examples of what constitutes each score level

## Feedback Loop

When a grader skill completes:

1. It calculates an overall grade based on the rubric
2. If the grade is below the pass threshold, it provides detailed feedback
3. The agent receives the feedback and understands what changes to make
4. The agent modifies the input to the upstream skill and re-invokes it
5. The cycle repeats until the output passes the grader

## Example: Grade Story Analysis

For the "expand-story-analysis" skill:

- **Grader skill:** "grade-story-analysis"
- **Rubric:** Scores story clarity, completeness, assumptions, and implementation feasibility (0-4 each)
- **Pass threshold:** 80% (minimum 16 points out of 20)
- **Feedback:** Specific guidance on which components fell short and why

## Related Decisions

- [ADR-005: Quantitative vs. Qualitative Analysis Separation](ADR-005-analysis-separation.md)
- [ADR-003: Skills-Based Architecture with Workflow Coordination](ADR-003-skills-based-architecture.md)
