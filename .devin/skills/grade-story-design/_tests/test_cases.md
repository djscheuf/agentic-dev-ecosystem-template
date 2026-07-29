# Tests Cases for Design Grader

## Happy Path
Given ANY valid design output
THEN
- Scores on all fields
- All Scores 3 or less.
- All Scores provide reasoning
- Matches Schema

## Design Reasoning Rubric
Given Design Missing Architectural Justification
THEN Design Reasoning Score is 0
AND Reasoning explains missing justification
AND Recommendation suggests grounding decisions in ADRs or existing code patterns

Given Design has Vague, or hueristic-driven Architectural Justification
THEN Design Reasoning Score is 1
AND Reasoning explains vagueness
AND Recommendation suggests strengthening justification with specific patterns

Given Design has over-engineered Architectural Justification
THEN Design Reasoning Score is 1
AND Reasoning explains over-engineering in significant excess of user story scope
AND Recommendation suggests simplifying design to match story scope and RoI. 

Given Design exhibits solid Architectural Justification, with a few unclear design intentions
THEN Design Reasoning Score is 2
AND Reasoning explains mostly solid justification, and highlights some components whose justification is unclear.
AND Recommendation suggests making design intent of all components explicit, and avoiding overlap to tighten scope.

Given Analysis Exemplary Architectural Justification wtih every component exhibiting clear, distinct design intent, grounded in proper justifications, and minimal over-engineering
THEN Design Reasoning Score is 3
AND Reasoning explains exemplary justification
AND no Recommendation needed


## Workflow Changes Rubric

Given Design Missing Workflow Changes such as happy path or edge cases
THEN Workflow Changes Score is 0
AND Reasoning explains missing workflow changes such as missing happy path or edge cases
AND Recommendation suggests specifying user journey step-by-step, including happy and edge paths, as well as data flows.

Given Design has Vague Workflow Changes, such as edge cases with unclear divergence from the happy path
THEN Workflow Changes Score is 1
AND Reasoning explains vagueness of edge cases
AND Recommendation suggests strengthening workflow changes by clarifying and diostinguishing edge cases, and improving clarity of design intent as expressed in the proposed workflow changes

Given Design has Workflow Changes with unclear layer responsibilities
THEN Workflow Changes Score is 1
AND Reasoning explains unclear layer responsibilities, making the location of expected changes unclear, muddling the flow of data
AND Recommendation suggests clarifying workflow change responsibility assignment

Given Design exhibits clear workflow changes, differentiated edge cases, and layer responsibility assignment
THEN Design Reasoning Score is 2
AND Reasoning explains clear Happy path data flows, and differentiated edge cases, and some layer responsibility assignment
AND Recommendation suggests identifying recovery paths for each edge case, and ensuring that all acceptance criteria are mapped.

Given Analysis Exemplary Workflow Changes with an unambiguous happy path, edge cases with clear divergences, and recovery paths, and all acceptance criteria mapped
THEN Workflow Changes Score is 3
AND Reasoning explains exemplary workflow changes
AND no Recommendation needed


## Interface And Contracts Rubric

## Layer Responsibilities & Consistency Rubric

## Instrumentation & Observability Rubric


