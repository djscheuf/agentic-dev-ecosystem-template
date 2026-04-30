---
description: Implement some planned functionality, in a test-driven development manner.
---
# SDLC Implement Workflow

## Purpose
Implement some planned functionality, in a test-driven development manner.

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
    a. Red - Write a failing test (INVOKE write-failing-test skill)
    b. Green - Write minimal passing code (INVOKE write-minimal-implementation skill)
    c. PAUSE & COMMIT: git commit ONLY YOUR CHANGES with message "feat: [description] - test [N] of [total]"
    d. More Tests in Priority Group?
        - If yes, go back to a.
        - If no, Jump to 3. 
3. Refactor
    a. Identify improvements (if any)
    b. Apply refactorings (tests stay green)
    c. PAUSE & COMMIT: git commit ONLY REFACTORING CHANGES with message "refactor: [description]"
    d. More Tests to Complete in Plan?
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

**CRITICAL: One Test at a Time**
Each iteration of the loop handles ONE test only:
- Do NOT add multiple tests in a single edit
- Do NOT implement multiple features in one code change
- Each test gets its own Red-Green-Commit cycle

For each priority group of tests, you will loop through:
    For EACH test in the group:
        - INVOKE `write-failing-test` skill (mandatory - do not skip)
        - INVOKE `write-minimal-implementation` skill (mandatory - do not skip)
        - git commit ONLY YOUR CHANGES with message: "feat: [description] - test [N] of [total]"
        - Verify test passes before moving to next test
    - After each priority group completes:
        - INVOKE `refactor-code-with-ai` skill to refactor if improvements identified
        - git commit ONLY REFACTORING CHANGES with message: "refactor: [description]"
    - Loop back to the next priority-group

### Phase 5: Confirmation & Reporting
Skip this phase for now. 
// TODO - Verify completion by checking if all tests pass and the implementation matches the design.