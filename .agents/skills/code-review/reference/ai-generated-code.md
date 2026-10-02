# Reviewing AI-generated code

Apply when the code was produced or substantially assisted by an AI agent. Treat it as a competent draft: fast and syntactically clean, but lacking full knowledge of the project. Give it the same rigor as hand-written code, and focus on the failure modes below.

**Warning sign**: a 100% acceptance rate on AI output is not proof of quality. It usually means nobody is checking. Verify with evidence, not because it sounds right.

## Common failure modes and how to check

### 1. Structural disorganization
The agent lacks the full architecture, so it tends to group things together (controllers, services, models, utilities in one file) or place logic in the wrong layer.
- Is each function in the correct module?
- Does the logic belong to the layer where it was added?
- Is one file handling several responsibilities?
- Is separation of concerns respected?

### 2. Reimplementation of existing code
The agent cannot see the whole codebase, so it recreates logic that already exists, especially when utilities are poorly named or documented.
- Does this function already exist elsewhere? Search for it.
- Could this be an import of an existing helper?
- Do old and new versions behave differently in a way that matters?

### 3. Invalid or invented references
The agent assumes components exist from common naming patterns.
- Do all imported modules, functions, classes, and packages actually exist?
- Are names exactly right, and paths aligned with the project's organization?
- Do packages exist in the registry, and are they the intended ones (watch for look-alike names)?
- Do called APIs and options exist in the installed version?

### 4. Misalignment with project standards
- Do names follow team conventions?
- Are type annotations present where the project requires them?
- Is business logic in the right place (not in controllers)?
- Does the code feel native to the codebase, or like an outside addition?
- Has the agent copied a poor practice that already exists in the project?

### 5. AI-specific patterns
- **Repetition**: needless duplicated code.
- **Plausible but wrong**: syntactically correct, but misaligned with business logic. Check against the story, not just for compilation.
- **Missing edge cases and error handling**, including non-standard input.
- **Insecure patterns** that look fine at a glance.
- **Overconfident comments and naming** that describe intent the code does not deliver.
- **Tests that mirror the implementation** and therefore verify nothing independent (see `test-quality.md`).
- Claims about the code or its tests made without checking (for example, "no end-to-end tests exist").

## Reviewing practices that work
- Check the change against the requirements in Phase 2, since AI is weakest on business context.
- Cross-check against existing utilities before accepting new ones.
- Validate every import and reference immediately.
- Prefer small, well-scoped changes; they are easier to review and less likely to cross architectural boundaries.
- Ask what design you expected, what the agent produced, and whether the differences are justified.
- When the agent repeats a mistake, fix the instructions or context (standards files, architecture notes), not only the output.

## If you are reviewing your own AI-produced work
Hold yourself to the same standard: name the evidence behind each claim of "done", re-verify searches and test runs rather than relying on memory, and record gaps honestly.

## Priorities
- Invented imports or APIs that fail at runtime, wrong-layer logic causing incorrect behavior: `blocking`.
- Reimplemented utilities, standards drift: `suggestion`.
- Stylistic mismatches: `comment`.
