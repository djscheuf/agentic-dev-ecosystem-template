# Testing Standards (tests/)

## Core Principles

- Each test verifies one behavior.
- Tests are independent, isolated, deterministic — no shared mutable state between tests, no
  reliance on execution order.
- Test behavior, not implementation: if a test would break from an internal refactor that doesn't
  change observable behavior, it's testing the wrong thing.
- Prefer Given/When/Then structure (via nested test classes or clearly commented sections) for
  multi-step tests; plain `test_<behavior>` names are fine for simple ones.

## Naming

- `test_<behavior>`, e.g. `test_returns_404_when_story_not_found`
- Avoid `test_works`, `test_1`, `test_it_should_*`

## Structure (matches existing split)

- `tests/unit/` — pure logic, no I/O, no external services
- `tests/integration/` — multiple components wired together, may hit a real local dependency
  (DB, workflow engine)
- `tests/e2e/` — full workflow through the system boundary

## Mocking

- Mock your own seams (ports/adapters) directly; wrap third-party clients before mocking them.
- Reset mocks/fixtures between tests via `autouse=True` fixtures in `conftest.py` rather than
  manual resets scattered per test.

## Forbidden

- Hardcoded `time.sleep()` to wait for async state — poll with a timeout or use a proper wait helper
- Asserting on internal/private state instead of observable behavior or return values
- Flaky tests merged "to fix later" — fix or skip with a tracked reason
- Multiple unrelated assertions bundled into one test when they verify different behaviors

## Coverage

Coverage % is not a goal — write tests to pin behavior, not to hit a number.
