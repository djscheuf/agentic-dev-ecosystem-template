---
description: Implement some planned functionality, in a test-driven development manner.
---
# SDLC Implement Workflow

## Purpose
Implement planned functionality using Test-Driven Development (TDD) methodology by orchestrating skills and subworkflows.

## Trigger
- After Planning an implementation, and before writing any production code

## Inputs Required
- User Story Analysis Document (path to .json file)
- Implementation Plan for this Workstream (path to .json file)
- Relevant domain context

## **CRITICAL RULES**
1. **FORBIDDEN: Writing production code directly** - You MUST use the designated skills and subworkflows
2. **FORBIDDEN: Skipping skill invocations** - Each phase requires specific skill/workflow invocation
3. **FORBIDDEN: Proceeding to next phase** until current phase verification passes
4. **ONE priority group at a time** - Complete all tests in a priority group before moving to next

---

## Workflow Phases

### Phase 0: Review Context
**MANDATORY**: Read all input documents before proceeding.

**Required Inputs:**
- User Story Analysis Document
- This Workstream's Implementation Plan
- Existing Test Cases Document (if any from previous run)
- Relevant domain context (vault pages, existing code)

**Actions:**
- Read and understand the requirements
- Identify what needs to be built
- Note any dependencies or constraints

**Output:** Mental model of the task (no files created)

---

### Phase 1: Design Test Cases
**MANDATORY**: INVOKE the `design-test-cases` skill.

**FORBIDDEN:**
- Write test cases manually
- Skip this step if test cases already exist (review them instead)

**Skill to Invoke:** `design-test-cases`

**Expected Output:**
- Test cases JSON file at path specified in sentinel file
- Sentinel file: `.process/design-test-cases.done.json`

**Verification:**
- Confirm test cases file exists and follows schema
- Confirm sentinel file exists
- Review test cases for completeness

**Before Proceeding:** Ensure verification passes.

---

### Phase 2: Red-Green Loop (Per Priority Group)
**CRITICAL**: You MUST invoke the `/sdlc-tdd` subworkflow. DO NOT write tests or implementation code directly.

**For EACH priority group in the test cases document:**

**Subworkflow to Invoke:** `/sdlc-tdd`

**Required Inputs to Provide:**
- User Story Analysis Document path
- Implementation Plan path
- Test Cases Document path
- Current Priority Group ID/number

**What the Subworkflow Does:**
- Writes one failing test at a time (using `write-failing-test` skill)
- Writes minimal implementation to pass (using `write-minimal-implementation` skill)
- Commits after each test passes
- Repeats for all tests in the priority group

**FORBIDDEN:**
- Write test files yourself
- Write implementation files yourself
- Skip the subworkflow and code directly

**Expected Output (from subworkflow):**
- Test files with passing tests
- Implementation files with minimal code
- Git commits for each test (format: "feat: [description] - test [N] of [total]")
- Sentinel files from `write-failing-test` and `write-minimal-implementation` skills

**Verification:**
- All tests in priority group are passing
- Sentinel files exist for each skill invocation
- Git commits exist for each test

**Loop Condition:**
- If more priority groups remain → Repeat Phase 2 for next priority group
- If all priority groups complete → Proceed to Phase 3

---

### Phase 3: Refactor
**OPTIONAL**: Only if improvements are identified.

**When to Refactor:**
- Code duplication exists
- Code clarity can be improved
- Better patterns are available
- Tests remain green after refactoring

**Skill to Invoke (if refactoring):** `refactor-code-with-ai`

**Required Inputs:**
- Files to refactor
- Refactoring goals/improvements

**FORBIDDEN:**
- Refactor without running tests
- Change test behavior
- Skip committing refactoring separately

**Actions:**
1. Identify improvements (if any)
2. If improvements found:
   - INVOKE `refactor-code-with-ai` skill
   - Verify all tests still pass
   - Commit ONLY refactoring changes: `git commit -m "refactor: [description]"`
3. If no improvements needed, skip to Phase 4

**Expected Output (if refactored):**
- Improved code with same behavior
- All tests still passing
- Git commit with "refactor:" prefix

---

### Phase 4: Completion Verification
**MANDATORY**: Verify all work is complete.

**Verification Checklist:**
- [ ] All priority groups have been implemented
- [ ] All tests are passing
- [ ] Sentinel files exist for all skill invocations
- [ ] Git commits exist for all tests and refactorings
- [ ] Implementation matches the design document

**Actions:**
- Run all tests to confirm they pass
- Review git log to confirm proper commit messages
- Confirm all sentinel files deleted from `.process/` directory

**Output:** Confirmation that implementation is complete

---

## Summary

This workflow is a **skill orchestrator**. Your role is to:
1. **Invoke skills** - not write code directly
2. **Invoke subworkflows** - not implement TDD manually  
3. **Verify outputs** - ensure each phase completes correctly
4. **Follow the chain** - complete phases in order

**Remember:** The skills and subworkflows contain the actual implementation logic. This workflow coordinates them.