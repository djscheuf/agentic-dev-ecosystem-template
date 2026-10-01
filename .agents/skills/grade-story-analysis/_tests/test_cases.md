# Tests Cases for Analysis Grader

## Happy Path
Given ANY valid analysis output
THEN
- Scores on all fields
- All Scores 3 or less.
- All Scores provide reasoning
- Matches Schema

## Goal Rubric
GIVEN Analysis MISSING GOAL
THEN GOAL Score is 0
AND Reasoning explains missing goal
AND Recommendation suggests adding goal with specific user, and business value declared

GIVEN Analysis Vague or Generic GOAL
THEN GOAL Score is 1
AND Reasoning explains vagueness
AND Recommendation suggests clarifying goal with specific user, and business value declared

GIVEN Analysis CLEAR GOAL tied to a Persona
THEN GOAL Score is 2
AND Reasoning explains the goal is clear but could be more specific
AND Recommendation suggests making goal more specific and measurable in business value

GIVEN Analysis SPECIFIC, Measruable, Observable GOAL
THEN GOAL Score is 3
AND Reasoning explains the goal is specific, measurable, and observable
AND no Recommendation needed

## Scope Rubric
GIVEN Analysis Multi-system spanning Scope
THEN Scope Score is 0
AND Reasoning explains unbounded scope
AND Recommendation suggests narrowing scope to cover components necessary for the vertical slice

GIVEN Analysis with partially bounded scope, covering some layers, but not enough to complete the vertical slice
THEN Scope Score is 1
AND Reasoning explains partial bounded scope
AND Recommendation suggests completing vertical slice with missing components

GIVEN Analysis Clear and Bounded Scope
THEN Scope Score is 2
AND Reasoning explains the scope is clear and bounded
AND Recommendation suggests adding more detail to the scope, like covering non-functional needs, or validation rules

GIVEN Analysis Precisely Bounded Scope
THEN Scope Score is 3
AND Reasoning explains the scope is precisely bounded, with proper support for vertical slice
AND no Recommendation needed

## Acceptance Criteria Rubric
GIVEN Analysis MISSING AC
THEN Scope Score is 0
AND Reasoning explains missing acceptance criteria
AND Recommendation suggests providing specific, testable acceptance criteria including happy path, negative cases, and edge cases

GIVEN Analysis with vague AC
THEN Scope Score is 0
AND Reasoning explains Acceptance criteria are vague, untestable
AND Recommendation suggests providing specific, testable acceptance criteria including happy path, negative cases, and edge cases


GIVEN Analysis with incomplete AC
THEN Scope Score is 1
AND Reasoning explains incomplete acceptance criteria, such as missing cases, or unconnected from user need
AND Recommendation suggests adding more comprehensive acceptance criteria, tied to user need, in Given-when-then format.

GIVEN Analysis with AC that mix implementation details with requirements
THEN Scope Score is 1
AND Reasoning explains acceptance criteria mix implementation details with requirements
AND Recommendation suggests focusing on what the user can do, not how the system does it.

GIVEN Analysis with some clear, testable AC but NOT comprehensive
THEN Scope Score is 2
AND Reasoning explains acceptance criteria are clear and testable but not comprehensive, possibly missing edge cases or business rules
AND Recommendation suggests adding more comprehensive acceptance criteria, including edge cases and business rules

GIVEN Analysis with precise, testable, comprehensive AC
THEN Scope Score is 3
AND Reasoning explains the AC is comprehensive, testable, and covers happy path, edge cases, and business rules
AND no Recommendation needed

## Format Rubric

Given Analysis with Missing story Structure
THEN Story Score is 0
AND Reasoning explains story is incoherent, lacking a clear actor, or intent
AND Recommendation suggests providing a clear, structured story with "So That ..., As a ..., and I want to ..." format

Given Analysis with Incoherent story
THEN Story Score is 0
AND Reasoning explains story is incoherent, lacking a clear actor, or intent
AND Recommendation suggests providing a clear, structured story with "So That ..., As a ..., and I want to ..." format

Given Analysis with Structured, but poorly articulated story
THEN Story Score is 1
AND Reasoning explains story is structured but poorly articulated, with a muddled or unclear business goal, persona, or intended outcome
AND Recommendation suggests improving articulation, by clarifying target persona, a measurable outcome, and a clear business value

Given Analysis with Well-structured and clear story
THEN Story Score is 2
AND Reasoning explains story is well-structured and clear, but could be more compelling
AND Recommendation suggests making the story more compelling, by leading with the business goal, for a specific persona, or to achieve a specific, measurable outcome

Given Analysis with Precise and compelling story
THEN Story Score is 3
AND Reasoning explains story is clear, and compelling, leading with the story goal, for a specific persona, to achieve a specific outcome
AND no Recommendation needed

## Dependencies Rubric

Given Analysis with Unresolved external dependency
Then Dependency score is 0
AND Reasoning explains story has unresolved external dependencies
AND Recommendation suggests resolving external dependencies

Given Analysis with Documented but unresolved dependency
Then Dependency score is 1
AND Reasoning explains story has dependencies that are documented but not resolved
AND Recommendation suggests resolving the dependencies

Given Analysis with No external dependencies
Then Dependency score is 2
AND Reasoning explains story has no external dependencies
AND no Recommendation needed

Given Analysis with Documented AND Resolved dependency
Then Dependency score is 3
AND Reasoning explains story has dependencies that are documented and resolved
AND no Recommendation needed

Given Analysis with Fully autonomous (All Depdencies Identified, and in scope for the story)
Then Dependency score is 3
AND Reasoning explains story is fully autonomous
AND no Recommendation needed
