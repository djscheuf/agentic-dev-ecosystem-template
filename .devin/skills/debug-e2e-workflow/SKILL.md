---
name: debug-e2e-workflow
description: Complete E2E test debugging workflow (composite orchestrator). Starts by reviewing the provided test failure evidence, then forms hypotheses, applies fixes, and verifies results for a presumed E2E playwright test suite. 
disable-model-invocation: true
---

# E2E Test Debugging Workflow

## Purpose
Systematically debug E2E test failures across multiple tests by reviewing evidence, forming hypotheses, applying TDD-style fixes, and verifying the result.

## Overview

This workflow runs through four phases in order. The first three phases have detailed supporting documents in this skill directory; the main file provides the map and decision points.

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
│                   │ (see /reference/fix.md)     │          │                    │
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
│                          │ (see /reference/fix.md)     │                        │
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
**Goal:** For each failing test, classify as setup vs test execution failure.  
**Time per test:** 2-5 minutes  
**Output:** Debugging session document with classified failures

**High-level flow:**
1. Create session document: `docs/ephemyra/debug-e2e-MMDD-HHMM.md`
2. Identify all failing tests.
3. For each test, determine failure type:
   - **Setup Failure:** empty/missing logs, error in helper/setup code, 401/500/connection error.
   - **Test Execution Failure:** logs exist, error in test spec, timeout/assertion/JS error.
4. For setup failures, reference the run log and stop.
5. For test execution failures, find log evidence and stop.
6. Summarize classifications and move to Phase 2.

→ **Full procedure:** [`review.md`](review.md)

---

### Phase 2: Hypothesis
**Goal:** Analyze evidence and form explicit, prioritized hypotheses.  
**Duration:** 20-40 minutes  
**Output:** Prioritized hypothesis list with setup failures FIRST

**High-level flow:**
1. Route failures to the right path:
   - Setup failures → infrastructure/environment analysis
   - Test execution failures → application/test logic analysis
2. Analyze each failure using the appropriate template.
3. Look for common causes across tests.
4. Prioritize: setup failures (Priority 0) always come before test execution failures (Priority 1+).
5. Validate high-priority hypotheses.
6. Complete the pre-fix verification checklist before moving on.

→ **Full procedure:** [`hypothesis.md`](./reference/hypothesis.md)

**Critical rule:** setup failures always have higher priority than test execution failures.

---

### Phase 3: Fix
**Goal:** Apply a TDD-style fix for each validated hypothesis.  
**Duration:** 10-30 minutes per hypothesis  
**Output:** Fixed tests with verification

**High-level flow:**
1. Fix all Priority 0 setup failures first.
2. After setup failures are fixed, re-run tests (see The Re-Run Gate below).
3. Return to Review if new failures appear; otherwise continue.
4. Fix each Priority 1+ test execution failure using Think → Red → Green → Refactor → Verify.
5. Update the session document after each fix.

→ **Full procedure:** [`fix.md`](./reference/fix.md)

---

### Phase 4: Final Verification
**Goal:** Confirm everything passes and no regressions were introduced.  
**Duration:** 10-20 minutes  
**Output:** Confirmed passing tests, ready to commit

**Checklist:**
- [ ] Run complete E2E test suite
- [ ] Verify all originally failing tests now pass
- [ ] Confirm no regressions introduced
- [ ] Review all changes made
- [ ] Prepare commit message

**Pause for final human review before committing.**

## The Re-Run Gate

After fixing setup failures, you MUST re-run tests before fixing test execution failures.

**Why:**
- Setup failures contaminate test results.
- Tests that "failed" may pass once infrastructure is stable.
- You need clean, accurate failure data to debug test logic.

**The Gate:**
```
Setup Failures Fixed → RE-RUN TESTS → Clean Results → Fix Test Execution Failures
                           ^
                    MANDATORY STEP
```

**Command:**
```bash
cd src/ui
./scripts/run-e2e-docker.sh
```

**What gets captured in re-run:**
- New run log: `e2e-run-logs/e2e-run-YYYYMMDD-HHMM.log`
- New test-results with accurate test execution data
- True test failures, not contaminated by setup issues

## Entry Points

### Starting Fresh (New Test Failures)
1. Receive test failure notification (CI or local).
   - Run log is automatically captured: `e2e-run-logs/e2e-run-YYYYMMDD-HHMM.log`
2. Follow [`review.md`](./reference/review.md) to classify each test.
3. Follow [`hypothesis.md`](./reference/hypothesis.md) for two-path analysis.
4. If setup failures exist:
   a. Follow the setup section of [`fix.md`](./reference/fix.md).
   b. Re-run tests: `cd src/ui && ./scripts/run-e2e-docker.sh`
   c. Return to step 2 with new results.
5. Follow the test execution section of [`fix.md`](./reference/fix.md).
6. Final verification and commit.

### Continuing Existing Session
1. Open existing session document (`docs/ephemyra/debug-e2e-MMDD-HHMM.md`).
2. Review current status.
3. Resume the appropriate phase:
   - In review phase → [`review.md`](./reference/review.md)
   - In hypothesis phase → [`hypothesis.md`](./reference/hypothesis.md)
   - In fix phase → [`fix.md`](./reference/fix.md) for next hypothesis

### Quick Single Test Debug
1. [`review.md`](./reference/review.md) (even for single test)
2. [`hypothesis.md`](`./reference/hypothesis.md) (form hypothesis)
3. [`fix.md`](./reference/fix.md) (apply fix)
4. Verify and commit

## Key Principles

1. **Setup failures first** - Always fix infrastructure before test logic.
2. **Re-run after setup fixes** - Get clean results before debugging tests.
3. **Classify each test individually** - Do not assume all failures share the same type.
4. **Systematic approach** - Follow phases in order.
5. **Evidence-based** - Form hypotheses from evidence, not assumptions.
6. **Document everything** - Keep the session document updated.
7. **One hypothesis at a time** - Do not try to fix everything at once.
8. **TDD discipline** - Think → Red → Green → Refactor → Verify.
9. **Verify thoroughly** - Always run the full suite after fixes.
10. **Pause for human review** - At key decision points.
11. **Use run logs for setup failures** - Test-context logs will not help with infrastructure issues.

## Supporting Documents

- [`review.md`](./reference/review.md) - Phase 1 detail: classify failures and gather evidence.
- [`hypothesis.md`](./reference/hypothesis.md) - Phase 2 detail: form and prioritize hypotheses.
- [`fix.md`](./reference/fix.md) - Phase 3 detail: TDD-style fixes for setup and test execution failures.

## Related Skills

- **e2e-logging-and-artifacts** - Logging infrastructure for debugging
- **running-e2e-tests** - How to execute E2E tests with proper commands

## Summary

This workflow prevents missed issues and guesswork by:

1. **Reviewing** - Gathering comprehensive evidence.
2. **Hypothesizing** - Forming explicit, testable hypotheses.
3. **Fixing** - Applying TDD discipline to each fix.
4. **Verifying** - Confirming all tests pass without regressions.

**Key benefits:**
- Systematic approach prevents missed issues.
- Evidence-based hypotheses reduce guesswork.
- TDD approach ensures proper fixes with tests.
- Session document provides debugging history.
- Prioritization focuses effort on high-impact issues.
- Verification prevents regressions.

**Remember:** one phase at a time, document as you go, validate before fixing, test at appropriate layers, and pause for human review at key points.
