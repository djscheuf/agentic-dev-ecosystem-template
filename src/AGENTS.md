# Coding Standards (src/)

## General Principles

- Add type hints to all function signatures and public APIs; let obvious local variables infer.
- Never use untyped data (`dict`, bare `object`) where a precise type, `TypedDict`, `Protocol`, or
  dataclass would do. If you must accept arbitrary input, say so with a comment on why.
- Name by intent, not implementation — a function name describes what it does, not how.

## Naming

| Item | Format | Example |
|---|---|---|
| Module/package | snake_case | `story_design_workflow` |
| Class | PascalCase | `WorkflowState` |
| Function/variable | snake_case | `get_user_profile` |
| Constant | SCREAMING_SNAKE_CASE | `MAX_RETRY_COUNT` |
| Boolean | `is_`/`has_`/`can_`/`should_` prefix | `is_loading`, `has_permission` |

## Error Handling

- Raise specific exception subclasses (e.g. `class WorkflowNotFoundError(AppError)`), not bare
  `Exception` or a generic `ValueError` for domain errors.
- Don't swallow exceptions silently — catch narrowly, and either re-raise with context or log and
  handle explicitly.

## Dependencies

- When adding a new package, check its current docs/changelog before pinning — don't carry over an
  outdated config pattern from memory or training data.
- If you deliberately pin below latest (compatibility, known issue), say why in the commit/PR.

## Forbidden

- Bare `except:` (catch specific exception types)
- Mutating function arguments in place unless that's the documented contract
- `==`/`!=` for singleton checks (`None`, `True`, `False`) — use `is`/`is not`
