# Phase 3: Test review

**Goal**: Check for evidence that the acceptance criteria are met and will stay met. Measure against criteria and behavior, never against coverage percentages.

**Comment type**: `testing`

**Consult**: `reference/test-quality.md` for what makes a test meaningful and readable.

## Step A: Map evidence to criteria
Using the Phase 2 traceability table, find the test (unit, integration, or end-to-end) that proves each criterion. Search thoroughly before concluding a test does not exist, including other test directories and test types.

## Step B: Check coverage of what matters
For each criterion and each significant changed behavior:
- Happy path covered?
- Edge cases and boundaries covered (empty, null, zero, negative, maximums)?
- Failure modes covered (errors, timeouts, invalid input, fail-safe paths such as logging and fallbacks)?
- Regression risk covered for code the change touches but did not intend to alter?

Untested failure and fail-safe paths are a frequent gap. Look for them explicitly.

## Step C: Run the tests when possible
Run the project's test command. Record failures, flakiness, and anything skipped. A failing or flaky test left in the change is a finding. If you cannot run tests, say so in the general commentary.

## Step D: Judge test quality
Apply `reference/test-quality.md`. Key tests for each test:
- Does it verify the behavior it claims to verify?
- Would it fail if the code broke? Mentally (or actually) alter a value or condition in the code under test. If the test still passes, it verifies nothing.
- Can a reader tell the scenario and expectation without reading the implementation?
- Is it a copy-paste of a sibling test with meaningless differences?

## Step E: Test-side design
- Are dependencies injectable so units can be tested in isolation?
- Are side effects explicit and minimized?
- Is test code held to its own standard: descriptive names that reveal what failed, rather than the terse naming suited to production code?

## Priorities
- No evidence for an acceptance criterion: usually `blocking`.
- Missing edge-case or failure-path tests: `suggestion`, or `blocking` if the path is critical (security, data integrity, money).
- Readability or naming of tests: `comment` or `suggestion`.
