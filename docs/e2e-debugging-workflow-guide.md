# E2E Debugging Workflow System - Complete Guide

## Overview

This guide explains the E2E debugging workflow system - a systematic, evidence-based approach to debugging end-to-end test failures using Test-Driven Development principles.

## What is the E2E Debugging Workflow?

The E2E debugging workflow is a **composite workflow** that orchestrates three specialized sub-workflows to systematically debug failing E2E tests:

1. **Review** (`/debug-e2e-review`) - Classify failures and gather evidence
2. **Hypothesis** (`/debug-e2e-hypothesis`) - Form and validate root cause hypotheses
3. **Fix** (`/debug-e2e-fix`) - Apply TDD-style fixes and verify

## ⚠️ Important: Repository-Specific Adaptation Required

**This workflow was developed for a specific E2E test infrastructure and requires adaptation to your repository.**

### Original Context
This workflow was built for a repository with the following E2E test setup:
- **Playwright** as the test framework
- **Docker Compose** network for test execution (not running tests directly on the host)
- **Containerized test environment** with services orchestrated via docker-compose
- **Environment variables** passed from host → docker-compose → test containers
- **Run logs** captured from Docker container execution

### What You Need to Adapt

The **infrastructure checks** in the Review and Hypothesis phases are **built-in knowledge** of the original repository's E2E testing system. You will need to customize these checks based on your repository's setup:

**If your tests run in Docker (like the original):**
- ✅ Infrastructure checks for docker-compose configuration are relevant
- ✅ Environment variable passing patterns (host → compose → container) apply
- ✅ Container health checks are applicable
- ✅ Run log analysis patterns are relevant

**If your tests run directly on the host:**
- ❌ Skip docker-compose configuration checks
- ✅ Check environment variables directly in test process
- ❌ Skip container health checks
- ✅ Adapt run log analysis to your test runner's output format
- ✅ Check for local service dependencies (databases, APIs running locally)

**If your tests use a different orchestration (Kubernetes, cloud services, etc.):**
- 🔄 Adapt infrastructure checks to your orchestration platform
- 🔄 Modify environment variable verification to match your config system
- 🔄 Adjust health checks to your platform's patterns
- 🔄 Update run log analysis to your logging infrastructure

### Why Context Hasn't Been Extracted

The infrastructure verification steps are **integral to the workflow sequence** - they define the boundary between setup failures and test execution failures. Extracting this context into a separate skill would break the workflow's systematic approach of:

1. **Review**: Classify based on infrastructure vs test execution
2. **Hypothesis**: Two-path analysis (infrastructure path vs test logic path)
3. **Fix**: Priority 0 (infrastructure) before Priority 1+ (tests)

The infrastructure knowledge must remain embedded in the workflow steps to maintain the proper classification and prioritization logic.

### How to Adapt This Workflow

1. **Review your E2E test infrastructure**:
   - How are tests executed? (Docker, host, CI platform)
   - Where are environment variables configured?
   - What services need to be healthy for tests to run?
   - Where are run logs captured?

2. **Update the workflow files** (`.windsurf/workflows/debug-e2e-*.md`):
   - Replace docker-compose references with your orchestration system
   - Update environment variable check commands
   - Modify health check patterns
   - Adjust run log locations and analysis commands

3. **Update the skills** (`.windsurf/skills/running-e2e-tests/`):
   - Replace test execution commands with your project's commands
   - Update test results directory locations
   - Modify artifact collection patterns

4. **Test the adapted workflow**:
   - Run through a debugging session with a known failure
   - Verify infrastructure checks catch setup issues correctly
   - Confirm test execution failures are properly classified
   - Adjust based on what works in your environment

## Why This Workflow Exists

### The Problem

E2E test failures are complex to debug because:
- **Multiple failure types**: Infrastructure issues vs application bugs
- **Contaminated results**: Setup failures can mask real test failures
- **Missing context**: Without proper logging, failures are hard to diagnose
- **Guesswork debugging**: Jumping to fixes without understanding root cause
- **Regression risk**: Fixes that break other tests

### The Solution

This workflow provides:
- **Systematic classification**: Distinguish setup failures from test execution failures
- **Evidence-based analysis**: Form hypotheses from logs, not assumptions
- **Two-path debugging**: Different strategies for infrastructure vs application issues
- **Priority-driven fixes**: Fix setup failures first, then test failures
- **TDD discipline**: Think → Red → Green → Refactor → Verify
- **Re-run gate**: Clean test results after infrastructure fixes

## Core Concepts

### Two Types of Test Failures

The workflow distinguishes between two fundamentally different failure types:

#### Setup Failures (Infrastructure/Environment)
**Characteristics:**
- Error occurs in helper/setup code (not test spec)
- No test-context logs exist or log directory is empty
- Error happens before test steps execute
- Error is 401, 403, 500, or connection-related
- Stack trace points to setup/helper methods

**Examples:**
- Environment variable mismatch (test uses `TOKEN_A`, docker-compose passes `TOKEN_B`)
- Authentication token expired
- Container not healthy
- Network connectivity issues
- Configuration file errors

**Debugging approach:**
- Check run logs (not test-context logs)
- Verify environment variables
- Check infrastructure configuration (docker-compose, kubernetes manifests, CI config, etc.)
- Validate authentication tokens
- Review service health (containers, local services, external dependencies)

**Note**: The specific checks depend on your repository's infrastructure. See "Repository-Specific Adaptation Required" section above.

#### Test Execution Failures (Application/Test Logic)
**Characteristics:**
- Error occurs in test spec file
- Test-context logs exist and contain data
- Error happens during test steps
- Error is timeout, assertion, or element not found
- Stack trace points to test code or page objects

**Examples:**
- Wrong testId selector
- Component refactoring changed UI structure
- API contract changed
- Timing/race condition
- Test data issue

**Debugging approach:**
- Check test-context logs
- Review error messages and screenshots
- Analyze code changes (git history)
- Examine component/API code
- Validate test logic

### The Re-Run Gate

**Critical Concept:** After fixing setup failures, you MUST re-run tests before fixing test execution failures.

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

### Priority System

**Priority 0: Setup Failures (Fix FIRST)**
- All setup failures must be fixed before debugging test execution failures
- Infrastructure must be stable before test logic can be properly evaluated
- Order within setup failures:
  - Affects all tests: Priority 0.1
  - Affects multiple tests: Priority 0.2
  - Affects single test: Priority 0.3

**Priority 1+: Test Execution Failures (Fix AFTER setup is stable)**
- Impact Radius: Affects 5+ tests (Priority 1), 2-4 tests (Priority 2), 1 test (Priority 3)
- Confidence Level: High (+0), Medium (+1), Low (+2)
- Fix Complexity: Simple (higher priority), Complex (lower priority)

## Workflow Phases

### Phase 1: Review (`/debug-e2e-review`)

**Goal:** Classify each failing test as setup failure or test execution failure

**Time:** 2-5 minutes per test

**Process:**
1. Create debugging session document (`docs/ephemyra/debug-e2e-MMDD-HHMM.md`)
2. Identify all failing tests
3. For each test, determine failure type:
   - **Setup failure**: Reference run log, note infrastructure issue
   - **Test execution failure**: Find log evidence showing the failure
4. Summarize failure breakdown
5. Move to hypothesis phase

**Key Principle:** Don't investigate root causes yet - just classify and gather evidence

**Output:**
- Session document with all tests classified
- For setup failures: Run log references
- For test execution failures: Error messages + log evidence

### Phase 2: Hypothesis (`/debug-e2e-hypothesis`)

**Goal:** Form explicit, testable hypotheses about root causes

**Time:** 20-40 minutes (depends on complexity)

**Process:**

#### Path A: Setup Failure Analysis (Priority 0)
1. Analyze run log for infrastructure errors
2. Check environment variables (test code vs configuration)
3. Check authentication (token names, expiration)
4. Check configuration files (docker-compose, CI config, orchestration manifests)
5. Form infrastructure hypotheses
6. Identify common setup failure patterns

**Repository-Specific**: The infrastructure checks in this path are based on the original repository's Docker Compose setup. Adapt these checks to match your infrastructure:
- **Docker setup**: Check docker-compose.yml, container health, network configuration
- **Direct execution**: Check local environment variables, service availability, port conflicts
- **CI/Cloud**: Check CI environment variables, service provisioning, network policies

#### Path B: Test Execution Analysis (Priority 1+)
1. Analyze test-context logs
2. Review error messages and screenshots
3. Examine code changes (git history)
4. Form test/application hypotheses
5. Identify common test execution patterns

#### For Both Paths:
1. Prioritize ALL hypotheses (setup failures always first)
2. Validate high-priority hypotheses
3. Complete pre-fix verification checklist

**Key Principle:** Evidence-based hypotheses with clear causal chains

**Output:**
- Prioritized hypothesis list with setup failures at top
- Validation results
- Pre-fix verification checklist completed

### Phase 3: Fix (`/debug-e2e-fix`)

**Goal:** Apply TDD-style fixes for each validated hypothesis

**Time:** 10-30 minutes per hypothesis

**Process:**

#### Part 1: Fix Setup Failures (Priority 0)
For each setup failure hypothesis:
1. **THINK**: Plan the infrastructure fix
2. **RED**: Verify failure (from run log evidence)
3. **GREEN**: Make fix (update configuration/helper code)
4. **REFACTOR**: Clean up (if needed)
5. **VERIFY**: Configuration correct

**After ALL setup failures fixed:**
```bash
# RE-RUN TESTS (MANDATORY)
cd src/ui
./scripts/run-e2e-docker.sh
```

This generates:
- Clean test execution results
- New run log with stable infrastructure
- Accurate test failure data

**Then:** Return to Review phase with new results OR continue to Part 2

#### Part 2: Fix Test Execution Failures (Priority 1+)
For each test execution hypothesis:
1. **THINK**: Plan the fix (identify affected layers, plan tests)
2. **RED**: Create failing test (at appropriate layer)
3. **GREEN**: Make test pass (minimal fix)
4. **REFACTOR**: Clean up (if needed)
5. **VERIFY**: E2E tests pass (run original test + full suite)

**Key Principle:** TDD discipline ensures proper fixes with tests

**Output:**
- Fixed tests with verification
- Session document updated
- No regressions introduced

### Phase 4: Final Verification

**Goal:** Confirm all tests passing, ready to commit

**Time:** 10-20 minutes

**Process:**
1. Run complete E2E test suite
2. Verify all originally failing tests now pass
3. Confirm no regressions introduced
4. Review all changes made
5. Prepare commit message

## Skills Used by the Workflow

### `e2e-logging-and-artifacts`
**Purpose:** Set up comprehensive logging infrastructure for E2E tests

**Provides:**
- BaseContext with automatic log collection
- Console logs, network logs, page errors, test context logs
- Playwright artifacts (screenshots, videos, traces)
- `dumpLogsToFiles()` method for test failure diagnostics

**When to use:**
- Creating new E2E test suites
- Setting up Playwright from scratch
- Implementing BaseContext for test contexts
- Configuring test failure diagnostics

**Key concept:** All test contexts should extend BaseContext and call `dumpLogsToFiles()` in `test.afterEach` on failure.

### `running-e2e-tests`
**Purpose:** Execute E2E tests with proper commands

**Provides:**
- Standard Playwright test execution commands
- Patterns for running specific tests/files
- Debug mode and UI mode usage
- Test results location and structure

**When to use:**
- Running E2E tests (full suite or specific tests)
- Verifying test fixes after implementation
- Debugging test failures
- Need to know test execution commands

**Key concept:** Use `npx playwright test` with appropriate flags for different scenarios.

## How Workflows and Skills Interact

### Workflow Orchestration

```
┌─────────────────────────────────────────────────────────────┐
│                  /debug-e2e-workflow                         │
│                  (Composite Orchestrator)                    │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   REVIEW     │→ │  HYPOTHESIS  │→ │     FIX      │      │
│  │              │  │              │  │              │      │
│  │ Classify     │  │ Two-Path:    │  │ TDD Loop:    │      │
│  │ failures     │  │ • Setup      │  │ • Think      │      │
│  │              │  │ • Test Exec  │  │ • Red        │      │
│  │              │  │              │  │ • Green      │      │
│  │              │  │ Prioritize   │  │ • Refactor   │      │
│  │              │  │ hypotheses   │  │ • Verify     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                  │                  │             │
│         └──────────────────┴──────────────────┘             │
│                            │                                │
│                            ▼                                │
│                  ┌──────────────────┐                       │
│                  │ Session Document │                       │
│                  │ (State Tracking) │                       │
│                  └──────────────────┘                       │
└─────────────────────────────────────────────────────────────┘
```

### Skill Integration

```
┌─────────────────────────────────────────────────────────────┐
│                         WORKFLOWS                            │
│  /debug-e2e-review  /debug-e2e-hypothesis  /debug-e2e-fix   │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ Uses
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                          SKILLS                              │
│                                                              │
│  ┌─────────────────────┐  ┌─────────────────────┐          │
│  │ e2e-logging-and-    │  │ running-e2e-tests   │          │
│  │ artifacts           │  │                     │          │
│  │                     │  │                     │          │
│  │ • BaseContext       │  │ • Test execution    │          │
│  │ • Log collection    │  │ • Command patterns  │          │
│  │ • dumpLogsToFiles() │  │ • Debug modes       │          │
│  └─────────────────────┘  └─────────────────────┘          │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ Produces
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      TEST ARTIFACTS                          │
│                                                              │
│  • test-results/[test-name]/logs/console.log                │
│  • test-results/[test-name]/logs/network.log                │
│  • test-results/[test-name]/logs/page-errors.log            │
│  • test-results/[test-name]/logs/test-context.log           │
│  • test-results/[test-name]/test-failed-*.png               │
│  • test-results/[test-name]/video.webm                      │
│  • test-results/[test-name]/trace.zip                       │
│  • e2e-run-logs/e2e-run-YYYYMMDD-HHMM.log (run log)         │
└─────────────────────────────────────────────────────────────┘
```

### Workflow → Skill Dependencies

**Review Phase:**
- Uses `running-e2e-tests` to understand test results location
- Uses `e2e-logging-and-artifacts` to understand log structure
- Reads logs from test-results directory
- References run log for setup failures

**Hypothesis Phase:**
- Uses `e2e-logging-and-artifacts` to interpret log contents
- Analyzes console logs, network logs, page errors, test context logs
- For setup failures: Focuses on run log analysis
- For test execution failures: Focuses on test-context logs

**Fix Phase:**
- Uses `running-e2e-tests` to execute specific tests for verification
- Uses `e2e-logging-and-artifacts` to verify logging still works after fixes
- Runs tests to verify fixes: `npx playwright test [test-file] -g "[test-name]"`
- Checks new logs to confirm fixes resolved issues

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

## Troubleshooting the Workflow

### "Can't form hypothesis with available evidence"
→ Return to review phase
→ Gather more evidence (run tests locally, add logging)
→ Ask human for expected behavior clarification

### "Hypothesis validated but fix doesn't work"
→ Re-evaluate hypothesis - may be incorrect
→ Check for additional root causes
→ Review fix implementation
→ Consider alternative approaches

### "Fix works but introduces regressions"
→ Review affected components
→ Check if fix is too broad
→ Consider more surgical fix
→ Add tests for regression cases

### "Multiple hypotheses, unclear priority"
→ Focus on impact radius (tests affected)
→ Prioritize blocking issues (setup failures)
→ Ask human for priority guidance
→ Fix high-confidence hypotheses first

### "Stuck in fix phase, can't make test pass"
→ Review hypothesis - may be wrong
→ Break down fix into smaller steps
→ Ask human for guidance
→ Consider if issue is more complex than expected

## Summary

The E2E debugging workflow system is a systematic, evidence-based approach to debugging test failures that distinguishes between infrastructure issues and application bugs.

### What the Workflow Does

**Three-Phase Process:**
1. **Review** - Classifies each failing test as either a setup failure (infrastructure) or test execution failure (application/test logic)
2. **Hypothesis** - Forms evidence-based hypotheses using different analysis paths for each failure type
3. **Fix** - Applies TDD-style fixes with mandatory re-run gate after infrastructure fixes

### Why This Approach Works

**The Core Insight:** Setup failures contaminate test results. Tests that appear to fail may actually pass once infrastructure is stable. By classifying failures first and fixing infrastructure issues before debugging test logic, you avoid wasting time on tests that aren't actually broken.

**The Re-Run Gate:** After fixing setup failures, the workflow requires re-running tests to get clean results before proceeding to fix test execution failures. This ensures you're debugging real issues, not symptoms of infrastructure problems.

**Evidence-Based Analysis:** The workflow uses logs, error messages, and configuration files to form hypotheses rather than jumping to conclusions. Different failure types require different evidence sources (run logs for setup failures, test-context logs for test execution failures).

**TDD Discipline:** Every fix follows Think → Red → Green → Refactor → Verify to ensure proper testing and prevent regressions.

### Adapting to Your Repository

**Critical First Step:** Before using this workflow, adapt the infrastructure checks to match your repository's E2E test setup. The workflow embeds knowledge of the original Docker Compose environment - you'll need to update references to docker-compose, environment variable patterns, and health checks to match your infrastructure (direct host execution, Kubernetes, CI platform, etc.).

See the "Repository-Specific Adaptation Required" section for detailed guidance on customizing the workflow for your environment.
