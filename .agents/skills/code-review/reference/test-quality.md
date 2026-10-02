# Test quality

Tests are declarations of expectations. Their value is in the confidence and shared understanding they give, not in the count. They are a form of living documentation, useful for onboarding.

## Measure behavior, not coverage
Coverage is an indirect measure of what we care about: **coverage of valuable behavior**. They correlate, but coverage can rise without any valuable behavior being covered. Chasing the number invites empty tests (`expect(true).toBe(true)`, bare pass assertions) and tests of the framework itself.

- Do not ask for tests of the underlying framework; if the framework is distrusted, the choice of framework is the real problem.
- For third-party libraries, tests are worthwhile when they verify your *assumed* behavior of the library, which gives confidence to keep using it as it changes.
- Ask "what valuable behavior does this test protect?" rather than "what is the coverage?"

## What bad tests look like
- **Fake tests**: they assert something passes without testing the named functionality.
- **Enigma tests**: unclear, or testing through association rather than directly.
- **Copy-paste tests** with meaningless differences between them. Bad tests are as harmful as bad code.
- **Tests that verify nothing**: mutate a value in the code under test; if the test still passes, it does not test that value.
- Tests of irrelevant things.
- **Flaky tests** left in the codebase. Diagnose rather than retry.
- **Failing tests** left in the codebase.
- Assertions missing, or so weak that almost any result passes.

## What good tests look like
- **Descriptive names** that state the scenario and expectation, so a failure report alone says what broke.
- **Given / When / Then** (or an equivalent readable structure):
  - Given: the situation or state, declared as state ("Given an invoice").
  - When: exactly one triggering action, in subject-verb-object form ("When the user adds an item to the cart"). If a test seems to need several Whens, the extras are Givens.
  - Then: the system's expectation, not its implementation ("an out-of-stock warning is shown", not "the system queries inventory and displays a toast for 30 seconds").
  - Keep the number of "And" clauses around three or fewer; more suggests over-specification.
- Written in business language, so stakeholders could read them.
- Cover happy path, edge cases, and corner cases.
- **Independent and fast** for unit tests: the unit is tested in isolation, so dependencies are mocked or injected.
- Integration tests are clearly distinct: they test the integration of components, not their units.

## Test code has its own standards
Production code should be quiet, succinct, and intent-revealing. Test code should "yell": long, descriptive names and scenario-focused structure, because the reader is someone looking at a test report who must decide what failed and why. Do not hold tests to production code's brevity standard, or production code to a test's verbosity.

## Review questions
- Does a test exist for each acceptance criterion and each significant behavior?
- Would this test fail if the code it guards were wrong?
- Can I read the test name and know the scenario and expectation?
- Is the test coupled to implementation details so that refactoring would break it?
- Are tests deterministic, or dependent on time, order, or shared state?
- Does testing exist for failure and fail-safe paths?

## Priorities
- No test for a core acceptance criterion, or tests that provably verify nothing on critical behavior: `blocking`.
- Missing edge and failure tests: `suggestion`.
- Naming and structure improvements: `suggestion` or `comment`.
