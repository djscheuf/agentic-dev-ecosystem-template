# Eval Standards (evals/)

## Test Case Design

- Each test case (`.tests.yaml` entry) verifies one behavior/claim about model output — not several
  unrelated assertions bundled together.
- Name test cases by the behavior under test, not the mechanism: `"rejects story with missing
  acceptance criteria"`, not `"test case 3"`.
- Assert on observable output (content, structure, pass/fail of a graded claim), not on incidental
  formatting that could change without the underlying behavior changing.

## JS Assertion Helpers

- Keep assertion functions pure and independent — no shared mutable state between test cases.
- When adding a new provider/package dependency, check current docs before copying an old config
  shape.

## Forbidden

- Flaky eval cases tolerated "because LLMs are nondeterministic" — set an appropriate
  threshold/grader instead of ignoring failures
- Hardcoded sleeps/retries without a documented reason
