# Phase 4: Implementation and architecture

**Goal**: Only now examine structure, patterns, and performance, grounded in the requirements and tests already understood. Ask: does it fit, and does it create tomorrow's problems?

**Comment types**: `design`, `implementation`, `readability`, `security`, `performance`, `documentation`

## Ground rule
First understand what the code is trying to do and why it is shaped the way it is. Critique second. Do not comment on style that tooling enforces. If the project has no linter or formatter, make one general comment recommending it instead of many line comments.

## Work through these lenses in order
Read the referenced file for any lens that applies before judging it.

1. **Architecture fit** → `reference/design-principles.md`
   - Is it in the correct layer or module? Does it respect separation of concerns?
   - Does it follow patterns already in the codebase, or drift from them?
   - Are contracts (interfaces, APIs, schemas) sensible, and is a change to one a revision or a breaking version?
2. **Design** → `reference/design-principles.md`
   - Single responsibility, extensibility, abstractions, coupling, dependency direction.
   - Premature abstraction (Rule of 3) and premature optimization.
3. **Readability and trust** → `reference/readability-and-trust.md`
   - Do names carry intent? Is cognitive load reasonable? Does code do only what it says?
4. **Robustness** → `reference/robustness.md`
   - Input validation, error handling, logging, security, performance hot spots.
5. **AI-generated code** (only if applicable) → `reference/ai-generated-code.md`
6. **Documentation and context**
   - Will someone reading this in six months know what it does and why? Are comments explaining *why*, and are they current?
   - Does the change description state the problem, the approach, the trade-offs, and edge cases?

## Finding hidden risks
Trace the data. Ask where it comes from, how much of it there is, and what happens when it grows. Examples worth catching: loading every record then filtering in memory, queries inside loops, unbounded collections, blocking calls in hot paths.

## Judging severity as you go
Note the likely priority, but assign final priority in synthesis. Weigh impact, scale (one call or every call), and criticality (cosmetic or data loss).

## Approve-with-suggestions mindset
A review that finds real risk but a sound approach should say so: flag the risk, give a remediation plan, and do not reject outright. Reserve `blocking` for things that must not ship.
