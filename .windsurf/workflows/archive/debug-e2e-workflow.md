---
description: Complete E2E test debugging workflow (composite orchestrator)
---

# E2E Test Debugging Workflow (Composite)

## Purpose
Complete systematic debugging workflow for E2E test failures. Orchestrates review, hypothesis formation, and TDD-style fixes across multiple failing tests.

## Overview
This workflow coordinates the debugging process through multiple phases, similar to the TDD workflow structure.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    E2E DEBUGGING CYCLE (Two-Path)                    │
│                                                                      │
│   ┌──────────┐    ┌────────────────────────────────────────┐        │
│   │  REVIEW  │───▶│         HYPOTHESIS                     │        │
│   │          │    │                                        │        │
│   │ Classify │    │  ┌──────────────┐  ┌──────────────┐   │        │
│   │ Each     │    │  │ Setup        │  │ Test Exec    │   │        │
│   │ Test:    │    │  │ Failures     │  │ Failures     │   │        │
│   │          │    │  │ (Infra/Env)  │  │ (App/Test)   │   │        │
│   │ • Setup  │    │  └──────┬───────┘  └──────┬───────┘   │        │
│   │   Failure│    │         │                  │           │        │
│   │ • Test   │    │    Priority 0         Priority 1+      │        │
│   │   Exec   │    │    (Fix FIRST)       (Fix AFTER)       │        │
│   │   Failure│    │         │                  │           │        │
│   └──────────┘    └─────────┼──────────────────┼───────────┘        │
│                              │                  │                    │
│                              ▼                  │                    │
│                   ┌──────────────────┐          │                    │
│                   │ FIX Setup Issues │          │                    │
│                   │ (TDD Loop)       │          │                    │
│                   └────────┬─────────┘          │                    │
│                            │                    │                    │
│                            ▼                    │                    │
│                   ┌──────────────────┐          │                    │
│                   │ RE-RUN TESTS     │          │                    │
│                   │ (Get clean       │          │                    │
│                   │  results)        │          │                    │
│                   └────────┬─────────┘          │                    │
│                            │                    │                    │
│                            └────────────────────┘                    │
│                                     │                                │
│                                     ▼                                │
│                          ┌──────────────────┐                        │
│                          │ FIX Test Issues  │                        │
│                          │ (TDD Loop)       │                        │
│                          └────────┬─────────┘                        │
│                                   │                                  │
│                                   ▼                                  │
│                          ┌──────────────────┐                        │
│                          │ FINAL VERIFY     │                        │
│                          │ & COMMIT         │                        │
│                          └──────────────────┘                        │
└─────────────────────────────────────────────────────────────────────┘
```

## Workflow Chain

### Phase 1: Review
**Workflow:** `/debug-e2e-review`  
**Goal:** For each test: classify as setup vs test execution failure  
**Time per test:** 2-5 minutes  
**Output:** Debugging session document with classified failures

```
Execute: /debug-e2e-review
├── Create session document (docs/ephemyra/debug-e2e-MMDD-HHMM.md)
├── For each failing test:
│   ├── Determine failure type: Setup Failure OR Test Execution Failure
│   ├── For Setup Failures:
│   │   ├── Check if logs are empty/missing
│   │   ├── Reference run log: e2e-run-logs/e2e-run-YYYYMMDD-HHMM.log
│   │   └── Note: Will need run log for hypothesis phase
│   └── For Test Execution Failures:
│       ├── Read error message - what does it say failed?
│       ├── Find log evidence - grep for the specific failure
│       └── Classify type - Timeout|Assertion|JS Error|Network
└── Output: Each test classified with appropriate evidence

⚠️ CRITICAL DISTINCTION:
- Setup Failure = Empty logs, error in helper/setup code, 401/500/connection
- Test Execution Failure = Logs exist, error in test spec, timeout/assertion

⚠️ KEEP IT SIMPLE:
- Classify each test individually (don't assume all same type)
- For setup failures: Reference run log, don't dig into test logic
- For test execution failures: Find supporting log evidence
- Don't investigate code, git history, or root causes yet

🛑 PAUSE: Review evidence with human if needed
```

### Phase 2: Hypothesis (Two-Path Analysis)
**Workflow:** `/debug-e2e-hypothesis`  
**Duration:** 20-40 minutes (depends on complexity)  
**Output:** Prioritized hypotheses with setup failures FIRST

```
Execute: /debug-e2e-hypothesis
├── Route to appropriate analysis path
│   ├── Setup Failures → Infrastructure/Environment Analysis
│   └── Test Execution Failures → Application/Test Logic Analysis
│
├── Path A: Setup Failure Analysis (Priority 0 - FIX FIRST)
│   ├── Analyze run log: e2e-run-logs/e2e-run-YYYYMMDD-HHMM.log
│   ├── Check environment variables (test code vs docker-compose)
│   ├── Check authentication (token names, expiration)
│   ├── Check configuration (docker-compose, .envrc)
│   ├── Form infrastructure hypotheses
│   └── Identify common setup failure patterns
│
├── Path B: Test Execution Analysis (Priority 1+ - FIX AFTER)
│   ├── Analyze test-context logs
│   ├── Form test/application hypotheses
│   ├── Determine root cause category
│   ├── Create causal chain
│   └── Look for common test execution patterns
│
├── Prioritize ALL hypotheses
│   ├── Priority 0: Setup failures (MUST FIX FIRST)
│   ├── Priority 1+: Test execution failures (fix after setup stable)
│   └── Within each priority: by impact, confidence, complexity
│
├── Validate high-priority hypotheses
└── Output: Prioritized hypothesis list with setup failures at top

⚠️ CRITICAL: Setup failures ALWAYS have higher priority
- Infrastructure must be stable before debugging test logic
- Fixing setup issues may resolve some "test execution" failures

🛑 PAUSE: Review hypotheses with human
```

### Phase 3: Fix Loop (TDD-Style with Re-run Gate)
**Workflow:** `/debug-e2e-fix` (repeat for each hypothesis)  
**Duration:** 10-30 minutes per hypothesis  
**Output:** Fixed tests with verification

```
PART 1: Fix Setup Failures (Priority 0)
FOR each setup failure hypothesis:
    
    Execute: /debug-e2e-fix
    
    ├── THINK: Plan the infrastructure fix
    │   ├── Identify config/code to change
    │   ├── Determine fix approach
    │   └── Assess impact
    │
    ├── RED: Verify failure (from run log evidence)
    │   └── Confirm setup failure pattern
    │
    ├── GREEN: Make fix
    │   ├── Update docker-compose / .envrc / helper code
    │   ├── Verify configuration is correct
    │   └── Check for similar issues in other tests
    │
    ├── REFACTOR: Clean up (if needed)
    │
    └── VERIFY: Configuration correct
        └── Review changes, don't run tests yet
    
    IF all setup failures fixed:
        ┌─────────────────────────────────────┐
        │ ⚠️ RE-RUN TESTS (CRITICAL STEP)     │
        │                                     │
        │ cd src/ui                           │
        │ ./scripts/run-e2e-docker.sh         │
        │                                     │
        │ This generates:                     │
        │ • Clean test execution results      │
        │ • New run log with stable infra     │
        │ • Accurate test failure data        │
        └─────────────────────────────────────┘
        
        THEN: Return to Review phase with new results
              OR: Continue to Part 2 if no new failures

PART 2: Fix Test Execution Failures (Priority 1+)
FOR each test execution hypothesis:
    
    Execute: /debug-e2e-fix
    
    ├── THINK: Plan the fix
    │   ├── Identify affected layers
    │   ├── Plan tests for each layer
    │   └── Determine fix approach
    │
    ├── RED: Create failing test
    │   ├── Write/update test at appropriate layer
    │   ├── Run test and verify failure
    │   └── Confirm failure reproduces bug
    │
    ├── GREEN: Make test pass
    │   ├── Implement minimal fix
    │   ├── Run tests and verify pass
    │   └── Check related tests
    │
    ├── REFACTOR: Clean up (if needed)
    │   ├── Identify improvements
    │   ├── Apply refactorings
    │   └── Keep tests green
    │
    └── VERIFY: E2E tests pass
        ├── Run original failing test
        ├── Run full E2E suite
        └── Check for regressions
    
    🛑 PAUSE: Review fix results
    
    IF fix successful:
        Update session document
        Continue to next hypothesis
    ELSE:
        Re-evaluate hypothesis
        Return to hypothesis phase
```

### Phase 4: Final Verification
**Duration:** 10-20 minutes  
**Output:** Confirmed all tests passing, ready to commit

```
Execute: Final Verification
├── Run complete E2E test suite
├── Verify all originally failing tests now pass
├── Confirm no regressions introduced
├── Review all changes made
└── Prepare commit message

🛑 PAUSE: Final review before commit
```

## The Re-Run Gate (Critical Concept)

**After fixing setup failures, you MUST re-run tests before fixing test execution failures.**

**Why?**
- Setup failures contaminate test results
- Tests that "failed" may actually pass once infrastructure is stable
- You need clean, accurate failure data to debug test logic
- Avoids wasting time fixing tests that aren't actually broken

**The Gate:**
```
Setup Failures Fixed → RE-RUN TESTS → Clean Results → Fix Test Execution Failures
                           ↑
                    MANDATORY STEP
```

**What gets captured in re-run:**
- New run log: `e2e-run-logs/e2e-run-YYYYMMDD-HHMM.log` (with stable infrastructure)
- New test-results: Accurate test execution data
- True test failures: Not contaminated by setup issues

## Entry Points

### Starting Fresh (New Test Failures)
```
1. Receive test failure notification (CI or local)
   - Run log automatically captured: e2e-run-logs/e2e-run-YYYYMMDD-HHMM.log
2. Run: /debug-e2e-review (classify each test: setup vs test execution)
3. Run: /debug-e2e-hypothesis (two-path analysis)
4. IF setup failures exist:
   a. Run: /debug-e2e-fix (for setup failures)
   b. RE-RUN TESTS: cd src/ui && ./scripts/run-e2e-docker.sh
   c. Return to step 2 with new results
5. Run: /debug-e2e-fix (for test execution failures)
6. Final verification and commit
```

### Continuing Existing Session
```
1. Open existing session document (docs/ephemyra/debug-e2e-MMDD-HHMM.md)
2. Review current status
3. Identify next step:
   - If in review phase: Continue /debug-e2e-review
   - If in hypothesis phase: Continue /debug-e2e-hypothesis
   - If in fix phase: Continue /debug-e2e-fix for next hypothesis
```

### Quick Single Test Debug
```
1. Run: /debug-e2e-review (even for single test)
2. Run: /debug-e2e-hypothesis (form hypothesis)
3. Run: /debug-e2e-fix (apply fix)
4. Verify and commit
```

## Key Principles

1. **Setup failures first** - ALWAYS fix infrastructure before test logic
2. **Re-run after setup fixes** - Get clean results before debugging tests
3. **Classify each test individually** - Don't assume all failures are same type
4. **Systematic approach** - Follow phases in order
5. **Evidence-based** - Form hypotheses from evidence, not assumptions
6. **Document everything** - Keep session document updated
7. **One hypothesis at a time** - Don't try to fix everything at once
8. **TDD discipline** - Think → Red → Green → Refactor → Verify
9. **Verify thoroughly** - Always run full suite after fixes
10. **Pause for human review** - At key decision points
11. **Use run logs for setup failures** - Test-context logs won't help with infrastructure issues

## Skills and Workflows Used

### Skills
- **e2e-logging-and-artifacts** - Logging infrastructure for debugging
- **running-e2e-tests** - How to execute E2E tests with proper commands

### Workflows
- **debug-e2e-review** - Phase 1: Evidence gathering
- **debug-e2e-hypothesis** - Phase 2: Root cause analysis
- **debug-e2e-fix** - Phase 3: TDD-style fixes

## Summary

This workflow ensures systematic E2E test debugging by:

1. **Reviewing** - Gathering comprehensive evidence
2. **Hypothesizing** - Forming explicit, testable hypotheses
3. **Fixing** - Applying TDD discipline to each fix
4. **Verifying** - Confirming all tests pass without regressions

**Key Benefits:**
- ✅ Systematic approach prevents missed issues
- ✅ Evidence-based hypotheses reduce guesswork
- ✅ TDD approach ensures proper fixes with tests
- ✅ Session document provides debugging history
- ✅ Prioritization focuses effort on high-impact issues
- ✅ Verification prevents regressions

**Remember:**
- One phase at a time
- Document as you go
- Validate before fixing
- Test at appropriate layers
- Verify thoroughly
- Pause for human review at key points

Happy debugging! 🔍
