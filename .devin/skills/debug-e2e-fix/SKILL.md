---
description: Apply TDD-style approach to fix validated hypothesis
---

# Debug E2E Fix Workflow

## Purpose
Fix a validated hypothesis using Test-Driven Development principles. Create tests at appropriate layers, implement fixes surgically, and verify the solution.

## When to Use
- After completing /debug-e2e-hypothesis
- Have a validated hypothesis ready to fix
- Clear understanding of root cause

## Prerequisites
- [ ] Debugging session document exists with validated hypothesis
- [ ] Hypothesis has high confidence level
- [ ] Root cause category identified
- [ ] Impact assessment complete

## Workflow Structure

This workflow follows the TDD pattern for each hypothesis:
1. **Think** - Identify all affected layers and plan tests
2. **Red** - Create failing test at closest reasonable layer
3. **Green** - Make surgical fix to pass the test
4. **Refactor** - Clean up if needed
5. **Verify** - Confirm e2e tests pass

## Step 1: Think Phase (Plan the Fix)

### 1.1: Identify Affected Layers

**Application Layers:**
```markdown
## Affected Layers Analysis

**Hypothesis:** [hypothesis statement]

**Layers Potentially Affected:**
- [ ] E2E Test Layer (test specs, contexts, page objects)
- [ ] Component Layer (UI components)
- [ ] API Layer (API calls, data fetching)
- [ ] Business Logic Layer (services, utilities)
- [ ] Data Layer (types, interfaces, constants)

**Primary Layer:** [the layer where the root cause exists]
**Secondary Layers:** [layers that may need updates due to fix]
```

### 1.2: Plan Tests for Each Layer

**Test Strategy:**
```markdown
## Test Strategy

### Layer 1: [Primary layer]
**Test Type:** Unit | Integration | E2E
**Test Location:** [file path]
**Test Purpose:** [what this test will verify]
**Test Approach:** [how to test this]

**Existing Test:**
- [ ] Test already exists - needs update
- [ ] Test exists - already correct
- [ ] No test exists - need to create
```

### 1.3: Determine Fix Approach

**Fix Strategy:**
```markdown
## Fix Approach

**Root Cause Category:** [Test Bug | Application Bug | Test Data | Timing | Environment]

**Fix Type:**
- [ ] Update test code (selector, assertion, logic)
- [ ] Update application code (component, API, service)
- [ ] Update test data (seed data, fixtures)
- [ ] Add synchronization (waits, state checks)
- [ ] Update configuration (environment, setup)

**Files to Modify:**
1. [file-1] - [what will change]
2. [file-2] - [what will change]

**Risk Assessment:** Low | Medium | High
- Low: Simple change, well-understood impact
- Medium: Moderate change, some uncertainty
- High: Complex change, wide impact

**Rollback Plan:**
[How to undo changes if fix doesn't work]
```

## Step 2: Red Phase (Create Failing Test)

### 2.1: Choose Test Layer

**Decision Tree:**
```
Is this a test bug (wrong selector, assertion)?
├─ YES → Fix at E2E layer, no new test needed
└─ NO → Is this an application bug?
    ├─ YES → Create unit/integration test at closest layer
    └─ NO → Is this a timing issue?
        ├─ YES → Add test for synchronization
        └─ NO → Is this test data issue?
            └─ YES → Add test for data validation
```

### 2.2: Write Failing Test

**For Test Bugs (E2E Layer):**
```markdown
## Red Phase: E2E Test Update

**File:** `e2e/tests/[path]/[file].spec.ts`

**Current (Failing) Test:**
```typescript
// Current test that fails
await page.getByTestId('old-pattern').click();
```

**Issue:**
[Why this fails - e.g., testId pattern changed]

**No new test needed** - will update existing test in Green phase
```

**For Application Bugs (Unit/Integration Layer):**
```markdown
## Red Phase: Create Failing Unit Test

**File:** `src/[component]/__tests__/[Component].test.tsx`

**New Test:**
```typescript
describe('[Component]', () => {
  it('should [expected behavior]', () => {
    // Arrange
    const props = { /* test props */ };
    
    // Act
    render(<Component {...props} />);
    
    // Assert
    expect(screen.getByTestId('expected-element')).toBeInTheDocument();
  });
});
```

**Expected Result:** ❌ Test fails (reproduces the bug)
```

### 2.3: Run Test and Verify Failure

**Verify:**
```markdown
## Red Phase Verification

**Test Run Result:** ❌ Failed (as expected)

**Failure Message:**
```
[paste failure message]
```

**Confirms Hypothesis:** [yes/no]
- If no: Re-evaluate hypothesis, return to hypothesis phase

**Ready for Green Phase:** [yes/no]
```

## Step 3: Green Phase (Make Test Pass)

### 3.1: Implement Minimal Fix

**Fix Guidelines:**
- Make the smallest change that fixes the issue
- Don't over-engineer
- Don't fix unrelated issues
- Follow existing code patterns
- Add comments if logic is complex

**Common Fix Patterns:**

#### Pattern 1: Update Test Selector
```typescript
// Before (fails)
await page.getByTestId('field-name').fill('value');

// After (passes)
await page.getByTestId('card-name-field-fieldName-input').fill('value');
```

#### Pattern 2: Fix Component TestId
```typescript
// Before (wrong testId)
<input data-testid="field-name" />

// After (correct testId)
<input data-testid={`${cardTestId}-field-${fieldName}-input`} />
```

#### Pattern 3: Add Missing Wait
```typescript
// Before (timing issue)
await page.getByTestId('button').click();

// After (proper synchronization)
await expect(page.getByTestId('button')).toBeEnabled();
await page.getByTestId('button').click();
```

### 3.2: Apply the Fix

```markdown
## Green Phase: Implement Fix

**Files Modified:**
1. [file-1]
   - Line [X]: [change description]
   - Line [Y]: [change description]

**Change Summary:**
[Brief description of what was changed and why]
```

### 3.3: Run Tests and Verify Pass

**Verify:**
```markdown
## Green Phase Verification

**Unit/Integration Tests:** ✅ Passing

**Test Results:**
- Target test: ✅ Pass
- Related tests: ✅ Pass ([count] tests)
- Component tests: ✅ Pass ([count] tests)

**Ready for Refactor Phase:** [yes/no]
```

## Step 4: Refactor Phase (Clean Up)

### 4.1: Identify Refactoring Opportunities

**Check for:**
```markdown
## Refactoring Opportunities

**Code Smells:**
- [ ] Duplicated code
- [ ] Magic numbers/strings
- [ ] Complex conditionals
- [ ] Long methods
- [ ] Inconsistent naming

**Improvements:**
- [ ] Extract constants
- [ ] Extract helper functions
- [ ] Improve naming
- [ ] Add comments
- [ ] Simplify logic

**Decision:**
- [ ] Refactoring needed
- [ ] No refactoring needed (code is clean)
- [ ] Defer refactoring (out of scope)
```

### 4.2: Apply Refactoring (if needed)

**Refactoring Guidelines:**
- Keep tests green throughout
- One refactoring at a time
- Run tests after each change
- Don't change behavior
- Improve readability/maintainability

## Step 5: Verify E2E Tests

### 5.1: Run Original Failing E2E Test

**Verify:**
```markdown
## E2E Test Verification

**Original Failing Test:** [test-name]

**Test Result:** ✅ Passing | ❌ Still Failing

**If still failing:**
- Review hypothesis - may be incorrect
- Check if fix was complete
- Look for additional issues

**If passing:**
- Proceed to full test suite verification
```

### 5.2: Run Full E2E Test Suite

**Verify:**
```markdown
## Full E2E Suite Verification

**Total Tests:** [count]
**Passing:** [count]
**Failing:** [count]

**New Failures:** [count]
- [If any new failures, list them]

**Regression Check:** ✅ No regressions | ⚠️ New failures detected

**If new failures:**
- Investigate if related to fix
- May need to adjust fix approach
- Document new failures in session document
```

## Step 6: Update Session Document

```markdown
## Fix: [Hypothesis name] - COMPLETE ✅

**Summary:**
- Hypothesis: [statement]
- Root Cause: [category]
- Fix Applied: [description]
- Tests Affected: [count]
- Files Modified: [count]

**TDD Phases:**
- ✅ Think: Planned approach
- ✅ Red: Created/verified failing test
- ✅ Green: Implemented fix
- ✅ Refactor: Cleaned up code
- ✅ Verify: E2E tests passing

**Verification Results:**
- Original test: ✅ Passing
- Unit tests: ✅ Passing ([count])
- E2E suite: ✅ Passing ([count])
- Regressions: None

**Next Steps:**
- [ ] Proceed to next hypothesis
- [ ] All hypotheses fixed - final verification
- [ ] Commit changes
```

## Output

**Updated debugging session document:**
`docs/ephemyra/debug-e2e-MMDD-HHMM.md`

**Contains:**
- Complete fix documentation
- TDD phase results
- Verification results
- Files modified
- Next steps

## Success Criteria

- [ ] Think phase complete - approach planned
- [ ] Red phase complete - failing test created/verified
- [ ] Green phase complete - fix implemented, tests pass
- [ ] Refactor phase complete - code cleaned up
- [ ] E2E verification complete - original test passes
- [ ] No regressions introduced
- [ ] Session document updated

## Next Steps

**If more hypotheses to fix:**
```
/debug-e2e-fix (for next hypothesis)
```

**If all hypotheses fixed:**
```
Proceed to final verification in main workflow
```

## Tips

**Think Phase:**
- Don't skip planning - it saves time later
- Consider all affected layers
- Assess risk before implementing

**Red Phase:**
- Test should fail for the right reason
- If test doesn't fail, hypothesis may be wrong
- Don't proceed to Green until Red is confirmed

**Green Phase:**
- Minimal fix - don't over-engineer
- Follow existing patterns
- One fix at a time

**Refactor Phase:**
- Optional but valuable
- Keep tests green
- Don't change behavior

**Verify Phase:**
- Always run full suite
- Check for regressions
- Document any new issues

**Common Mistakes:**
- Skipping Think phase (leads to wrong fix)
- Not verifying Red phase (fixing wrong thing)
- Over-engineering in Green phase (adds complexity)
- Skipping Verify phase (missing regressions)

**When Stuck:**
- Review hypothesis - may be incorrect
- Gather more evidence
- Ask human for guidance
- Consider alternative approaches
