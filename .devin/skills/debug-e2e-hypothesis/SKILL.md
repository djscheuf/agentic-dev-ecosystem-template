---
description: Analyze test failures and form hypotheses for root causes
---

# Debug E2E Hypothesis Workflow

## Purpose
Analyze evidence from failing tests and form explicit hypotheses about root causes. Identify common causes across multiple failures.

## When to Use
- After completing /debug-e2e-review
- Have evidence gathered for all failing tests
- Ready to diagnose root causes

## Prerequisites
- [ ] Debugging session document exists (`docs/ephemyra/debug-e2e-MMDD-HHMM.md`)
- [ ] All failing tests reviewed
- [ ] Evidence gathered for each test
- [ ] Failure types classified

## Workflow Steps

### Step 0: Route to Appropriate Analysis Path

**Based on review phase classification, follow the appropriate path:**

```markdown
## Hypothesis Phase Routing

**From Review Phase:**
- Setup Failures: [count] tests
- Test Execution Failures: [count] tests

**Analysis Paths:**
1. If setup failures exist → Follow **Setup Failure Analysis** (Step 1A)
2. If test execution failures exist → Follow **Test Execution Analysis** (Step 1B)
3. If both exist → Analyze setup failures FIRST, then test execution failures
```

**Why setup failures first?**
- Setup failures block all tests from running properly
- Fixing infrastructure issues may resolve some "test execution" failures
- Infrastructure must be stable before debugging test logic

---

### Step 1A: Analyze Setup Failures (Infrastructure/Environment)

**For each test that failed during setup:**

#### Setup Failure Hypothesis Template:
```markdown
## Test: [test-name] ⚠️ SETUP FAILURE ANALYSIS

### Hypothesis

**Root Cause Category:** [Select one]
- [ ] Environment Variable Issue - Wrong name, missing, or undefined
- [ ] Authentication Issue - Token invalid, expired, or not passed
- [ ] Container Issue - Service not healthy, not started, or crashed
- [ ] Network Issue - Cannot reach API/DB from test container
- [ ] Configuration Issue - docker-compose or test config incorrect

**Hypothesis Statement:**
[Clear, specific statement about the infrastructure issue]

### Evidence from Run Log

**Run Log:** `e2e-run-logs/e2e-run-[TIMESTAMP].log`

**Commands to extract evidence:**
```bash
# Find this test's failure in run log
grep -B 10 -A 10 "[test-name]" e2e-run-logs/e2e-run-*.log

# Check for auth errors
grep -i "401\|403\|unauthorized\|forbidden" e2e-run-logs/e2e-run-*.log

# Check for environment issues
grep -i "undefined\|not defined\|missing" e2e-run-logs/e2e-run-*.log
```

**Evidence Found:**
- [Log excerpt 1]
- [Log excerpt 2]

### Evidence from Code/Configuration

**Check environment variable usage and configuration files**

**Code/Config Evidence:**
- Test code uses: [variable name]
- Configuration passes: [variable name]
- Environment defines: [variable name]
- Mismatch: [yes/no - describe]

### Causal Chain

**Why this explains the failure:**
1. [Step 1 - what was configured/expected]
2. [Step 2 - what actually happened]
3. [Step 3 - how this caused the error]
4. Therefore: [failure occurs]

### Confidence Level

**Confidence:** High | Medium | Low

**Reasoning:**
[Why you have this confidence level based on evidence from run log and code]

### Validation Strategy

**How to confirm (using code/config only):**
1. [Validation step 1]
2. [Validation step 2]

### Impact Assessment

**Affected Tests:**
- [This test only | Multiple tests - list them]

**Fix Scope:**
- [ ] Single test file
- [ ] Multiple test files
- [ ] Helper/setup code
- [ ] Configuration files
- [ ] Environment files
```

---

### Step 1B: Analyze Test Execution Failures (Application/Test Logic)

**For each test that failed during execution:**

**Hypothesis Template:**
```markdown
## Test: [test-name] 🔍 ANALYZING

### Hypothesis

**Root Cause Category:** [Select one]
- [ ] Test Bug - Test code is incorrect
- [ ] Application Bug - Application code is broken
- [ ] Test Data Issue - Database/seed data is wrong
- [ ] Timing Issue - Race condition or async problem
- [ ] Environment Issue - Setup or configuration problem

**Hypothesis Statement:**
[Clear, specific statement of what you believe is causing the failure]

### Evidence Supporting This Hypothesis

**From Logs:**
- [Log evidence 1]
- [Log evidence 2]

**From Screenshot:**
- [Visual evidence 1]
- [Visual evidence 2]

**From Code Analysis:**
- [Code evidence 1]
- [Code evidence 2]

**From Git History:**
- [Recent change 1]
- [Recent change 2]

### Causal Chain

**Why this explains the failure:**
1. [Step 1 in causal chain]
2. [Step 2 in causal chain]
3. [Step 3 in causal chain]
4. Therefore: [failure occurs]

### Confidence Level

**Confidence:** High | Medium | Low

**Reasoning:**
[Why you have this confidence level]

High: Strong evidence from multiple sources, clear causal chain
Medium: Good evidence but some uncertainty remains
Low: Limited evidence, multiple possible causes

### Validation Strategy

**How to confirm this hypothesis:**
1. [Validation step 1]
2. [Validation step 2]
3. [Validation step 3]

**Expected results if hypothesis is correct:**
- [Expected result 1]
- [Expected result 2]

**How to rule out this hypothesis:**
- [What evidence would disprove this]

### Alternative Hypotheses

**Alternative 1:** [Description]
- **Why less likely:** [Reasoning]
- **Evidence against:** [Evidence]

### Impact Assessment

**Affected Components:**
- [Component/file 1]
- [Component/file 2]

**Affected Tests:**
- [This test only | Multiple tests - list them]

**User Impact:**
- [ ] Test-only issue (no user impact)
- [ ] Affects users (describe impact)

### Next Steps

- [ ] Validate hypothesis
- [ ] Check for common causes with other tests
- [ ] Proceed to fix phase
```

### Step 2: Look for Common Causes

After analyzing all tests individually, look for patterns **within each failure type**.

### Step 3: Prioritize Hypotheses

**CRITICAL: Setup failures ALWAYS have higher priority than test execution failures.**

**Prioritization Rules:**

1. **Setup Failures** (Priority 0 - Fix FIRST)
   - All setup failures must be fixed before debugging test execution failures
   - Infrastructure must be stable before test logic can be properly evaluated
   - Order within setup failures:
     - Affects all tests: Priority 0.1
     - Affects multiple tests: Priority 0.2
     - Affects single test: Priority 0.3

2. **Test Execution Failures** (Priority 1+ - Fix AFTER setup is stable)
   - Impact Radius:
     - Affects 5+ tests: Priority 1
     - Affects 2-4 tests: Priority 2
     - Affects 1 test: Priority 3
   - Confidence Level:
     - High confidence: +0 (no change)
     - Medium confidence: +1
     - Low confidence: +2
   - Fix Complexity (tiebreaker):
     - Simple fix: Higher priority
     - Complex fix: Lower priority

**Prioritized Hypothesis List:**
```markdown
## Prioritized Hypotheses

### Priority 0: Setup Failures (FIX FIRST - Infrastructure Issues)
**These MUST be fixed before debugging test execution failures**

1. **[Setup hypothesis name]** - [Test count] setup failures, [Confidence] confidence
   - Category: [Environment | Auth | Container | Network | Config]
   - Impact: Blocks [count] tests from executing
   - Fix location: [configuration files]
   - Fix complexity: [Simple | Medium | Complex]

---

### Priority 1+: Test Execution Failures (Fix AFTER setup is stable)

1. **[Test hypothesis name]** - [Test count] tests, [Confidence] confidence
   - Category: [Test Bug | Application Bug | Timing | Test Data]
   - Impact: [description]
   - Fix complexity: [Simple | Medium | Complex]
```

### Step 4: Validate High-Priority Hypotheses

Before proceeding to fixes, validate high-priority hypotheses:

**Validation Checklist:**
```markdown
## Hypothesis Validation

### Hypothesis: [name]

**Validation Steps Completed:**
- [ ] Step 1: [description] - Result: [pass/fail]
- [ ] Step 2: [description] - Result: [pass/fail]
- [ ] Step 3: [description] - Result: [pass/fail]

**Validation Results:**
- **Hypothesis confirmed:** [yes/no]
- **Confidence level:** [updated if changed]
- **Additional findings:** [any new information]

**Decision:**
- [ ] Proceed to fix phase
- [ ] Need more investigation
- [ ] Hypothesis rejected - form new hypothesis
```

### Step 5: Before Proposing Fix - Mandatory Verification Checklist

**CRITICAL:** Complete this checklist before proceeding to fix phase.

```markdown
## Pre-Fix Verification Checklist

### 1. Verify the Symptom is Real
- [ ] Check database state (does data exist?)
- [ ] Check API logs (what is actually being returned?)
- [ ] Check network logs (what is being requested?)
- [ ] Check other test cases for similar symptoms

### 2. Identify ALL Potential Causes
- [ ] List at least 3 possible root causes
- [ ] Rank by likelihood based on evidence
- [ ] Verify each hypothesis with data
- [ ] Explore all possibilities before settling on one

### 3. Confirm Root Cause Before Fixing
- [ ] Can you reproduce the issue with minimal test case?
- [ ] Does fixing this explain ALL symptoms?
- [ ] Are there unit tests that should have caught this?
- [ ] Will this fix work for ALL scenarios?

### 4. Test Impact Analysis
- [ ] How many tests currently pass that use this code?
- [ ] Could this fix cause those tests to fail?
- [ ] Do I need conditional logic to handle multiple scenarios?

### 5. Only Then Propose Fix
- [ ] Fix addresses root cause, not symptom
- [ ] Fix includes regression test
- [ ] Fix is minimal and focused
- [ ] Explained why fix will work

**NEVER try the same fix twice - if it failed, diagnose why first**
```

### Step 6: Update Session Document

Update the debugging session document with all hypotheses:

```markdown
## Hypothesis Phase Complete ✅

**Total Hypotheses Formed:** [count]
- Setup Failure Hypotheses: [count]
- Test Execution Hypotheses: [count]

**Common Causes Identified:** [count]
- Setup Failure Patterns: [count]
- Test Execution Patterns: [count]

**Priority Breakdown:**
- Priority 0 (Setup Failures): [count] - **MUST FIX FIRST**
- Priority 1 (High Impact Tests): [count]
- Priority 2 (Medium Impact Tests): [count]
- Priority 3 (Low Impact Tests): [count]

**Validation Status:**
- Setup failure hypotheses validated: [count]/[total]
- Test execution hypotheses validated: [count]/[total]
- Pre-fix verification checklist completed: [yes/no]
- Ready to proceed to fix phase: [yes/no]

## Next Steps

**CRITICAL: Fix setup failures FIRST**

**If setup failure hypotheses exist:**
1. Proceed to /debug-e2e-fix for Priority 0 hypotheses (setup failures)
2. After ALL setup failures fixed, re-run tests to get clean test execution results
3. THEN proceed to fix test execution failures

**If only test execution hypotheses exist (setup is stable):**
- Proceed to /debug-e2e-fix for highest priority test execution hypothesis
```

## Output

**Updated debugging session document:**
`docs/ephemyra/debug-e2e-MMDD-HHMM.md`

**Contains:**
- Individual hypotheses for each test
- Common cause analysis
- Prioritized hypothesis list
- Validation results

## Success Criteria

- [ ] Hypothesis formed for each failing test
- [ ] Common causes identified (if any)
- [ ] Hypotheses prioritized
- [ ] High-priority hypotheses validated
- [ ] Clear next steps identified

## Next Workflow

**For each hypothesis (starting with highest priority):**
```
/debug-e2e-fix
```

## Tips

**Forming good hypotheses:**
- Be specific, not vague
- Include causal chain (why → how → failure)
- Base on evidence, not assumptions
- Consider alternatives
- State confidence level honestly

**Common hypothesis mistakes:**
- Too broad: "Something is wrong with the test"
- No evidence: "Maybe the API changed"
- No causal chain: "The testId is wrong" (why? how does that cause failure?)
- Overconfident: "High confidence" with weak evidence

**When stuck:**
- Gather more evidence before hypothesizing
- Ask human for clarification on expected behavior
- Look at similar tests that pass for comparison

**Multiple possible causes:**
- Form multiple hypotheses
- Prioritize by evidence strength
- Validate highest confidence first
- Be prepared to pivot if hypothesis is wrong
