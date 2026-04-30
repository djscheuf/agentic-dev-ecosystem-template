# SDLC Implement Workflow

## Purpose
Implement some functionality based on a provided plan, in a test-driven development manner.

## Trigger
- After Planning an implementation, and before writing any production code

## Inputs Required
- Design of the user story
- Implementation plan
- Relevant domain context

## Overview
This workflow orchestrates the four TDD phases in a continuous cycle until the feature is complete.

## TDD Implementation Cycle
0. Review Context
1. Think
2. Red-Green Loop
    a. Red - Write a failing test
    b. Green - Write minimal passing code
    c. More Tests in Priority Group?
        - If yes, go back to a.
        - If no, Jump to 3. 
3. Refactor
    a. Identify improvements (if any)
    b. Apply refactorings (tests stay green)
    c. More Tests to Complete in Plan?
        - If yes, go back to 2.
        - If no, jump to 4.
4. Done. 


## Workflow Chain
### Phase 0: Review Context
**Input**
- User Story Analysis Document
- This Workstream's Implementation Plan
- Existing Test Cases Document (if any)
- Relevant domain context
**Output:** None

### Phase 1: Design Test Cases
Use the `design-test-cases` skill to design comprehensive test cases.

### Phase 2-4: Red-Green-Refactor Loop
**Repeat for each test in the plan**
For each priority group of tests, you will loop through:
    For Each test in the group:
        - use `write-failing-test` skill to write a failing test
        - use `write-minimal-implementation` skill to write minimal passing code
        - commit changes with message: "feat: [description] - test [N] of [total]"
    - After each priority group, use `refactor-code` skill to refactor if needed
    - commit refactor changes with message: "refactor: [description]"
    - loop back to the next priority-group.

### Phase 5: Confirmation & Reporting
Skip this phase for now. 
// TODO - Verify completion by checking if all tests pass and the implementation matches the design.

