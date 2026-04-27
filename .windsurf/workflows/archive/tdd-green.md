# TDD-Green Workflow

## Purpose
Write the MINIMUM code necessary to make the failing test pass. No more, no less.

## Trigger
- After `tdd-red` produces a failing test
- Test failure is understood
- Ready to implement behavior

## Prerequisites
- One failing test from `tdd-red`
- Clear understanding of WHY it's failing
- No other failing tests (fix one at a time)

## Workflow Steps

### Step 1: Analyze the Failure
```
Review the test failure:
- What class/method is missing?
- What behavior is not implemented?
- What's the simplest fix?
```

### Step 2: Write Minimal Implementation
```
CRITICAL: Write ONLY enough code to pass the test.

Acceptable approaches:
- Return a hardcoded value
- Implement the simplest algorithm
- Add the minimal structure needed

Do NOT:
- Implement features not tested
- Add error handling not tested
- Optimize prematurely
- Add "obvious" code paths
```

### Step 3: Make It Compile
```
If the test fails due to missing types/methods:

1. Create the class/interface if missing
2. Add method signatures with minimal body
3. Return default/hardcoded values initially

Example progression:
// Step 1: Make it compile
public class Calculator
{
    public int Add(int a, int b) => 0; // Just compile
}

// Step 2: Make it pass
public class Calculator
{
    public int Add(int a, int b) => 5; // Hardcoded for first test
}
```

### Step 4: Run the Test
```
Execute ONLY the specific test:
- dotnet test --filter "TestName"
- pytest -k "test_name"
- npm test -- --grep "test name"

Verify:
✓ The specific test now passes
✓ No compilation errors
✓ Test passes for the right reason
```

### Step 5: Run All Tests
```
Ensure no regressions:
- Run the entire test suite
- All tests should pass
- If any test fails, fix immediately

If new failures appear:
- Your change broke something
- Revert and reconsider approach
- Smaller steps needed
```

### Step 6: Evaluate Code Quality
```
Ask yourself:
- Is this code embarrassingly simple? (Good!)
- Did I add anything extra? (Remove it!)
- Can I explain why every line exists?

Remember: Refactoring comes NEXT, not now.
```

## Quality Checks
- [ ] Test that was red is now green
- [ ] All other tests still pass
- [ ] No code written beyond what test requires
- [ ] No premature optimization
- [ ] No error handling for untested scenarios
- [ ] Code compiles without warnings

## Output
- All tests passing
- Minimal implementation in place
- Ready for `tdd-refactor` phase

## Next Workflow
→ `tdd-refactor`: Improve code quality while keeping tests green

## The "Fake It Till You Make It" Approach

### Level 1: Return Constant
```csharp
// Test expects Add(2,3) = 5
public int Add(int a, int b) => 5;
```

### Level 2: Use Inputs Simply
```csharp
// After second test expects Add(1,1) = 2
public int Add(int a, int b) => a + b;
```

### Why This Works
- Forces you to write another test
- Reveals the algorithm incrementally
- Prevents over-engineering
- Keeps you in the TDD rhythm

## Anti-Patterns to Avoid
```
❌ Writing more code than needed
❌ Adding "obvious" error handling
❌ Implementing multiple behaviors
❌ Refactoring during green phase
❌ Skipping test execution
❌ Ignoring other test failures
```

## Example Progression
```python
# Test 1: test_greet_returns_hello_name
# RED: NameError: name 'greet' is not defined

# GREEN - Step 1:
def greet(name):
    return "Hello, Alice"  # Hardcoded

# Test passes! Move to refactor or add next test.

# Test 2: test_greet_bob_returns_hello_bob
# RED: AssertionError: "Hello, Alice" != "Hello, Bob"

# GREEN - Step 2:
def greet(name):
    return f"Hello, {name}"  # Now generalized

# Both tests pass! The algorithm emerged from tests.
```
