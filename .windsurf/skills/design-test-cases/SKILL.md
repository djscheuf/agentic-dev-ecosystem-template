---
name: design-test-cases
description: Design comprehensive test cases for a given set of requirements. Use before starting TDD to plan coverage.
---

# Design Test Cases
## Purpose 
Analyze requirements and design test cases before writing any code. This is the planning phase of TDD.

## Trigger
- Starting a new feature or bug fix
- Before writing any production code
- When clarifying approach to an Implementation Plan

## Inputs Required
- Implementation Plan
- Acceptance criteria (if available)
- Relevant domain context

## Workflow Steps

### Step 1: Understand the Requirement
```
Analyze the requirements and answer:
1. What is the core behavior being requested?
2. What are the inputs and expected outputs?
3. What are the boundary conditions?
4. What could go wrong (error cases)?
```

### Step 2: Review Existing Test Cases

### Step 3: Identify All Test Cases
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

Utilize documented cases, and fill in any gaps.
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

### Step 5. Output Test Cases
Capture test cases in a JSON file that follows the schema in `schema/test-cases.schema.json`. File should be named `{workstream}.test-cases.json` and placed in the same directory as the implementation plan.

```
Output the test cases in the following format:
- Test name following convention: Method_Scenario_ExpectedResult
- Arrange: What setup is needed?
- Act: What action triggers the behavior?
- Assert: What outcome proves success?
```

## Step 6. Write the Sentinel File

### 7. Write the Sentinel File
- create a sentinel file in the `.process` directory, named `{skill-name}.done.json`.
- the sentinel file will follow @/schema/sentinel.schema.json. 
- set the task field to "{skill-name}".
- the verify_params of the sentinel file will follow @/schema/verify-params.schema.json. 
- set the verify_params as follows:
    - set "test_cases_path" as the path to the test cases file relative to repo root.


