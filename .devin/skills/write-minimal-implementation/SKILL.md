---
name: write-minimal-implementation
description: Write the MINIMUM code necessary to make the failing test pass. No more, no less. Use to write code in TDD loop, and to resolve a failing test.
---

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

FORBIDDEN:
- Implementing features not tested
- Adding error handling not tested
- Optimizing prematurely
- Adding "obvious" code paths
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

// TODO - Add Run-Test Skill specific to the project's testing framework, supporting that projects structure.

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

// TODO - Add Run-Test Skill specific to the project's testing framework, supporting that projects structure, and specifically declares how to run all of a projects/subprojects tests.

### Step 6: Document the Success
Update the test plan and mark that test as "passing".

### Step 7: Write the Sentinel File
- create a sentinel file in the `.process` directory, named `{skill-name}.done.json`.
- the sentinel file will follow @/schema/sentinel.schema.json. 
- set the task field to "{skill-name}".
- the verify_params of the sentinel file will follow @/schema/verify-params.schema.json. 
- set the verify_params as follows:
    - set "test_cases_path" to the path of the test cases file relative to repo root.
    - set "failing_test_path" to the path of the failing test file relative to repo root.
    - set "failing_test_name" to the name of the failing test.
    - set "changed_code_files" to an array of paths to all the changed code files relative to repo root.

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
