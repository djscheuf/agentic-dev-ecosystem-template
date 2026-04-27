# TDD-Think Workflow

## Purpose
Analyze requirements and design test cases before writing any code. This is the planning phase of TDD.

## Trigger
- Starting a new feature or bug fix
- Before writing any production code
- When requirements need clarification

## Inputs Required
- User story or requirement description
- Acceptance criteria (if available)
- Relevant domain context

## Workflow Steps

### Step 1: Understand the Requirement
```
Analyze the requirement and answer:
1. What is the core behavior being requested?
2. What are the inputs and expected outputs?
3. What are the boundary conditions?
4. What could go wrong (error cases)?
```

### Step 2: Identify Test Cases
```
Create a test case list covering:

HAPPY PATH:
- [ ] Basic successful scenario
- [ ] Typical use case with valid inputs

EDGE CASES:
- [ ] Empty/null inputs
- [ ] Minimum valid values
- [ ] Maximum valid values
- [ ] Boundary conditions

ERROR CASES:
- [ ] Invalid input types
- [ ] Out of range values
- [ ] Missing required data
- [ ] System/dependency failures

SPECIAL CASES:
- [ ] Concurrent access (if applicable)
- [ ] Idempotency requirements
- [ ] Performance constraints
```

### Step 3: Prioritize Test Cases
```
Order tests by:
1. Core happy path (proves basic functionality)
2. Critical error handling
3. Edge cases
4. Nice-to-have scenarios
```

### Step 4: Design Test Structure
```
For each prioritized test, define:
- Test name following convention: Method_Scenario_ExpectedResult
- Arrange: What setup is needed?
- Act: What action triggers the behavior?
- Assert: What outcome proves success?
```

## Output
A structured test plan document with:
- Numbered test cases
- Clear descriptions
- Expected behaviors
- Priority order for implementation

## Next Workflow
→ `tdd-red`: Write the first failing test

## Example Output
```markdown
## Test Plan: UserRegistration.Register

### Priority 1: Happy Path
1. Register_WithValidEmail_CreatesUser
   - Arrange: Valid email, password meeting requirements
   - Act: Call Register()
   - Assert: User created, returns success, welcome email queued

### Priority 2: Validation Errors
2. Register_WithEmptyEmail_ReturnsValidationError
3. Register_WithInvalidEmailFormat_ReturnsValidationError
4. Register_WithPasswordTooShort_ReturnsValidationError

### Priority 3: Business Rules
5. Register_WithExistingEmail_ReturnsDuplicateError
6. Register_WithDisposableEmail_ReturnsValidationError

### Priority 4: Edge Cases
7. Register_WithMaxLengthEmail_CreatesUser
8. Register_WithUnicodeCharacters_CreatesUser
```
