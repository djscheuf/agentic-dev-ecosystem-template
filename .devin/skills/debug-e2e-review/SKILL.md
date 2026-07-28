---
description: Review test failures and initiate debugging session
---

# Debug E2E Review Workflow

## Purpose
Initial phase of e2e test debugging. Gather all failure information and create a debugging session document.

## When to Use
- E2E tests failed in CI or locally
- Multiple tests are failing
- Need to investigate test results from a previous run
- Starting a new debugging session

## Prerequisites
- [ ] Test failure information available (terminal output or test-results folder)
- [ ] Access to test-results directory if available

## Workflow Steps

### Step 1: Create Debugging Session Document

Create a new file to track the debugging session:

```bash
# File naming convention: docs/ephemyra/debug-e2e-MMDD-HHMM.md
# Example: docs/ephemyra/debug-e2e-0227-1430.md (Feb 27 at 2:30pm)
```

**Document Template:**
```markdown
# E2E Test Debugging Session
**Created:** YYYY-MM-DD HH:MM
**Last Updated:** YYYY-MM-DD HH:MM

## Session Overview
**Total Failing Tests:** [count]
**Test Run Source:** CI | Local | Test Results Folder
**Branch:** [branch-name]
**Commit:** [commit-hash]

## Failing Tests Summary
- [ ] Test 1: [test-name] - [failure-type]
- [ ] Test 2: [test-name] - [failure-type]
- [ ] Test 3: [test-name] - [failure-type]

## Investigation Status
- Tests Reviewed: 0/[total]
- Hypotheses Formed: 0
- Common Causes Identified: 0
- Fixes Applied: 0

---

## Test Analysis

(Individual test analyses will be added below)
```

### Step 2: Identify All Failing Tests

**From Terminal Output:**
```bash
# Look for test failure summary
# Playwright typically shows:
# - Test file path
# - Test name
# - Error message
# - Stack trace
```

**From Test Results Folder:**
```bash
# List all test result directories
ls -la test-results/

# Identify failed tests (have test-failed-*.png)
find test-results -name "test-failed-*.png" -exec dirname {} \; | sort -u
```

**Document each failing test:**
```markdown
## Test 1: [test-name] ⏳ PENDING REVIEW

**File:** `e2e/tests/[path]/[file].spec.ts`
**Test Results:** `test-results/[test-name]-chromium/`
**Failure Type:** [Timeout | Assertion | JavaScript Error | Unknown]

**Error Message:**
```
[paste error message]
```

**Initial Observations:**
- [ ] Error message reviewed
- [ ] Logs available: [yes/no]
- [ ] Screenshot available: [yes/no]
- [ ] Video available: [yes/no]
```

### Step 3: Classify Each Test Failure (Setup vs Test Execution)

**CRITICAL**: Before gathering evidence, determine if each test failed during **setup** or during **test execution**. This determines the debugging path.

**For each failing test:**

#### 3.0: Determine Failure Type

**Setup Failure Indicators:**
- [ ] Error occurs in helper/setup code (not test spec)
- [ ] No test-context logs exist or log directory is empty
- [ ] Error happens before test steps execute
- [ ] Error is 401, 403, 500, or connection-related
- [ ] Stack trace points to setup/helper methods

**Test Execution Failure Indicators:**
- [ ] Error occurs in test spec file
- [ ] Test-context logs exist and contain data
- [ ] Error happens during test steps
- [ ] Error is timeout, assertion, or element not found
- [ ] Stack trace points to test code or page objects

**Check Commands:**
```bash
# Check if test has logs (empty = likely setup failure)
ls -la test-results/[test-name]-chromium/logs/

# Count log files
ls test-results/[test-name]-chromium/logs/ | wc -l
```

#### 3.1: For Setup Failures - Reference Run Log

**If test failed during setup:**

```markdown
## Test: [test-name] ⚠️ SETUP FAILURE

**File:** `e2e/tests/[path]/[file].spec.ts`
**Failure Type:** Setup Failure (before test execution)

**Error Message:**
```
[paste error message from terminal or test output]
```

**Evidence of Setup Failure:**
- Log directory: [empty | missing | only X files]
- Error location: [helper file/method]
- Stack trace points to: [helper file/method]

**Run Log Reference:**
Most recent run log: `e2e-run-logs/e2e-run-[TIMESTAMP].log`

**To investigate, check run log for:**
```bash
# Find this test's setup error in run log
grep -B 10 -A 10 "[test-name]" e2e-run-logs/e2e-run-*.log | grep -i "error\|401\|500"

# Check for environment/auth issues
grep -i "undefined\|401\|authorization" e2e-run-logs/e2e-run-*.log
```

**Next Steps:**
- [ ] Check run log for infrastructure errors
- [ ] Verify environment variables in configuration
- [ ] Check for auth token issues
- [ ] This will be analyzed in Setup Failure Hypothesis phase
```

**If run log is missing, prompt user:**
```markdown
⚠️ **Run log not found**

Please provide the most recent e2e-run-logs/e2e-run-*.log file, or re-run tests to capture the log.
```

#### 3.2: For Test Execution Failures - Gather Evidence

**If test failed during execution (logs exist):**

**Process:**
1. Read error message - what does it say failed?
2. Find the log evidence that shows this failure
3. Document both and move on

**Evidence Sufficiency** (stop when you have these):
- [ ] Error message - what failed?
- [ ] Log excerpt showing the failure point
- [ ] That's enough - move to next test

**For each failing test, collect:**

#### 3.2.1: Read Error Message
```markdown
**Error Message:**
```
[full error message from terminal or test output]
```

**Stack Trace:**
```
[stack trace if available]
```
```

#### 3.2.2: Find Log Evidence for the Failure

**Strategy**: Use grep to find the failure point, don't read entire files.

```bash
# Based on error message, search for relevant evidence
# Example: If error says "expected 'value1' but got 'value2'"
grep -i "value1\|value2" test-results/[test-name]-chromium/logs/console.log

# If timeout on element, check what was logged around that time
tail -50 test-results/[test-name]-chromium/logs/console.log

# If API error, find the specific request
grep -A5 -B5 "[api-endpoint]" test-results/[test-name]-chromium/logs/network.log

# If JavaScript error, check page errors
cat test-results/[test-name]-chromium/logs/page-errors.log
```

**Document the specific evidence:**
```markdown
**Log Evidence:**
- Error message says: [what test reported]
- Log shows: [specific log line that confirms this]
- Location: [which log file, approximate line or timestamp]

Example:
- Error message says: "PATCH request body was empty"
- Log shows: "Update request body {}" at console.log line 631
- Network log shows: Request body: {} in PATCH request
```

#### 3.2.3: Quick Visual Check (Optional)

**Only if error message is unclear:**
```bash
# View screenshot to see what state the page was in
ls test-results/[test-name]-chromium/test-failed-*.png
```

**Document only if it adds clarity:**
```markdown
**Screenshot shows:** [one line description if relevant]
```

**Skip this step if:** Error message and logs already make the failure clear.

#### 3.2.4: That's It - Move to Next Test

**Don't investigate further in review phase:**
- ❌ Don't read test code yet
- ❌ Don't check git history yet  
- ❌ Don't search for related components
- ❌ Don't use code_search tool
- ❌ Don't try to figure out the root cause

**Save that for hypothesis phase.** Right now you just need:
1. What the test says failed
2. Log evidence showing the failure

**Move to next failing test.**

### Step 4: Summary of Failure Classifications

After reviewing all tests, summarize the breakdown:

```markdown
## Failure Classification Summary

**Total Failing Tests:** [count]

**Setup Failures:** [count]
- Test 1: [name] - [401 Auth | 500 Server | Connection | Environment]
- Test 2: [name] - [failure type]

**Test Execution Failures:** [count]
- Test 3: [name] - [Timeout | Assertion | JS Error | Network]
- Test 4: [name] - [failure type]

**Run Log Available:** [yes - e2e-run-logs/e2e-run-TIMESTAMP.log | no - need to re-run]
```

**Classification Guide:**
- **Setup Failures:** 401 Auth | 500 Server | Connection | Environment | Undefined Variable
- **Test Execution Failures:** Timeout | Assertion | JavaScript Error | Network Error | Element Not Found

### Step 5: Update Session Document

After reviewing all tests, update the session overview:

```markdown
## Session Overview (Updated)
**Total Failing Tests:** [count]
**Tests Reviewed:** [count]/[total] ✅

## Failure Breakdown
**Setup Failures:** [count] tests
**Test Execution Failures:** [count] tests

## Setup Failures (Infrastructure/Environment Issues)
- Test 1: [name] - [401 Auth | 500 Server | etc.]
- Test 2: [name] - [failure type]

## Test Execution Failures (Application/Test Logic Issues)
- Test 3: [name] - [Timeout | Assertion | etc.]
- Test 4: [name] - [failure type]

**Run Log:** e2e-run-logs/e2e-run-[TIMESTAMP].log

**Ready for Hypothesis Phase:** Yes
**Hypothesis Paths Needed:** 
- [ ] Setup Failure Analysis (if setup failures exist)
- [ ] Test Execution Analysis (if test failures exist)
```

### Step 6: Move to Hypothesis Phase

**Review phase is complete when you have for each test:**
- [ ] Error message documented
- [ ] Failure type determined (Setup vs Test Execution)
- [ ] For setup failures: Run log referenced
- [ ] For test execution failures: Log evidence found

**Move to hypothesis phase:**
```
/debug-e2e-hypothesis
```

**Note:** The hypothesis workflow will follow different paths:
- **Setup failures** → Infrastructure/environment hypothesis (check run logs, docker-compose, env vars)
- **Test execution failures** → Application/test logic hypothesis (check test code, components, APIs)

## Output

**Debugging session document created at:**
`docs/ephemyra/debug-e2e-MMDD-HHMM.md`

**Contains for each test:**
- Error message
- Failure classification (Setup vs Test Execution)
- For setup failures: Run log reference and investigation commands
- For test execution failures: Log evidence showing failure
- Failure type (401 Auth, Timeout, Assertion, etc.)

## Success Criteria

- [ ] Session document created
- [ ] Each test classified as Setup Failure or Test Execution Failure
- [ ] For setup failures: Run log referenced with investigation commands
- [ ] For test execution failures: Error message + log evidence + failure type
- [ ] Ready to proceed to hypothesis phase (with appropriate path identified)

**Time expectation:** 2-5 minutes per test

## Next Workflow

```
/debug-e2e-hypothesis
```

## Tips

**Keep it simple:**
- **First:** Determine if setup failure or test execution failure
- **Setup failures:** Reference run log, don't dig into test logic
- **Test execution failures:** Find supporting log evidence
- Don't investigate code yet - that's for hypothesis phase
- Don't try to figure out root cause yet

**Critical distinction:**
- **Setup failure** = Infrastructure issue (auth, env, containers) → Check run logs
- **Test execution failure** = Application/test issue → Check test-context logs

**If run log is missing:**
- Re-run tests to capture the log automatically

**If many tests failing:**
- Process each one quickly (2-5 min each)
- Classify each individually (some may be setup, others test execution)
- Look for patterns but don't deep-dive yet
- Hypothesis phase will identify common causes

**Common mistakes to avoid:**
- ❌ Assuming all tests have same failure type
- ❌ Trying to debug setup failures without run log
- ❌ Reading entire log files
- ❌ Using code_search tool
- ❌ Checking git history
- ❌ Trying to diagnose root cause
- ❌ Over-investigating
