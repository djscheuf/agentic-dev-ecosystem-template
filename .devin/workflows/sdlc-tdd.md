---
description: Single Cycle of TDD (Red-Green Phases)
---
# SDLC TDD Sub-Workflow

## Purpose
Implement one test from a Test plan. 

## Trigger
- After designing Test Cases, and for a Single Test.

## Inputs Required
- Design of the user story
- Implementation plan
- Relevant domain context
- Test Cases Document

## Overview
This workflow orchestrates the core TDD Red-Green Loop in a continuous cycle until the feature is complete.

## TDD Implementation Cycle
1. Red - Write a failing test (INVOKE write-failing-test skill)
2. Green - Write minimal passing code (INVOKE write-minimal-implementation skill)
3. PAUSE & COMMIT: git commit ONLY YOUR CHANGES with message "feat: [description] - test [N] of [total]"
4. More Tests in Priority Group?
    - If yes, go back to 1.
    - If no, finish workflow.

## Workflow Chain
**CRITICAL: One Test at a Time**
Run the cycle ONCE For EACH test in the priority group.
CRITICAL - Write Sentinel Files when instructed. 

### Phase 1 - Red Phase
- INVOKE `write-failing-test` skill (mandatory - do not skip)
- Address any verification failures before proceeding

### Phase 2 - Green Phase
- INVOKE `write-minimal-implementation` skill (mandatory - do not skip)
- Address any verification failures before proceeding

### Phase 3 - Commit Phase
- git commit ONLY YOUR CHANGES with message: "feat: [description] - test [N] of [total]"

### Phase 4 - Loop Decision
- If More test in Priority Group, go back to Phase 1
- If no more tests in Priority Group, finish workflow
