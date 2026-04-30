---
name: write-failing-test
description: Write a single test from a given test plan. Use as part of a TDD loop to write a failing test before writing code.
---

### Step 1: Select Next Test Case
```
From your test plan, identify:
- The highest priority unimplemented test
- The specific behavior being tested
- The expected outcome
```

### Step 2: Write the Test Shell
Create the Test with the proper structure. Identify the appripriate language for the component and review an example in one of these files:
- C#: `/reference/test_example.cs`
- Python: `/reference/test_example.py`
- TypeScript: `/reference/test_example.ts`


### Step 3: Implement Arrange Section
```
Set up the test preconditions:
- Create test data using factories/builders
- Configure mocks for dependencies
- Initialize the system under test (SUT)

Keep setup minimal - only what's needed for THIS test.
```

### Step 4: Implement Act Section
```
Execute the behavior under test:
- Single method call or action
- Capture the result if needed
- Should be ONE line in most cases
```

### Step 5: Implement Assert Section
```
Verify the expected outcome:
- Use specific assertions (not just assertTrue)
- One logical assertion per test
- Assert on behavior, not implementation
```

### Step 6: Verify Test Fails
```
Run the test and confirm:
✓ Test executes without setup errors
✓ Test fails for the RIGHT reason
✓ Failure message is clear and helpful
✗ Test should NOT pass yet

If test passes → Something is wrong:
- Test may not be testing new behavior
- Code already exists
- Test has a bug
```

### Step 7: Document the Failure
Update the test plan and mark the test as "failing".

### Step 8: Report Progress

## Quality Checks
- [ ] Test name clearly describes the scenario
- [ ] Arrange section is minimal and focused
- [ ] Act section is a single action
- [ ] Assert section verifies specific outcome
- [ ] Test fails with a clear message
- [ ] No production code written yet

## Output
- A single failing test
- Clear failure message indicating missing behavior
- Ready for `tdd-green` phase

## Next Workflow
→ `tdd-green`: Write minimal code to make the test pass

## Anti-Patterns to Avoid
```
❌ Writing multiple tests at once
❌ Writing any production code
❌ Tests that pass immediately
❌ Vague assertion messages
❌ Testing implementation details
❌ Over-complicated test setup
```

## Example
```csharp
// Good: Focused, clear, fails correctly
[Fact]
public void Calculate_WithTwoPositiveNumbers_ReturnsSum()
{
    // Arrange
    var calculator = new Calculator();

    // Act
    var result = calculator.Add(2, 3);

    // Assert
    Assert.Equal(5, result);
}

// Run: dotnet test --filter "Calculate_WithTwoPositiveNumbers"
// Result: FAIL - Calculator class does not exist
// ✓ Correct failure - ready for tdd-green
```