# Phase 5: Refactor and reuse

**Goal**: Look beyond the diff. After reviewing the implementation, find code reuse and refactoring opportunities related to the change.

**Comment types**: `refactor` (and `design` where the finding is structural)

**Comment flag**: set `in_diff: false` for findings outside the diff. Use `true` only when the finding is on a changed line.

**Consult**: `reference/smells-and-refactors.md` for smell names and concrete fixes.

## Step A: Reuse
For each new function, class, or helper in the diff:
- Search the codebase for existing code with the same or similar behavior (names, signatures, distinctive logic).
- If found: could the change call it instead? Note any behavioral differences between old and new.
- If not found: is the new code general enough to belong in a shared place, or is it specific to this context? Do not suggest generalizing before there are three cases (Rule of 3).

## Step B: Duplication
- Copy-pasted blocks, repeated literals, and repeated if/else chains inside the diff and in neighboring code.
- Repeated decisions or data, not only repeated lines.
- Recommend separating the *what* (the data or rule, defined once) from the *how* (the processing).

## Step C: Adjacent refactoring opportunities
Scan the modules the change touches and their immediate neighbors for:
- Smells named in `reference/smells-and-refactors.md` (fat interfaces, long condition chains, narrating comments, dead regions, copy-pasted tests).
- Code the change made harder to understand or extend.
- Places where a small extraction would simplify the change's own logic.

Keep it related to the change. Do not audit the whole codebase.

## Step D: Shape the recommendation
- Prefer small, incremental steps (extract variable, rename, extract method) that can be covered by tests first.
- Say what to do first, and why it is safe.
- If a larger refactor is warranted, recommend a separate change.

## Priorities
Findings here are usually `comment` or `suggestion`. Use `blocking` only when the change makes a pre-existing flaw newly dangerous (for example, it now routes every request through a duplicated, inconsistent rule).

## Then synthesize
With all phases done, assign final priorities, write the verdict and general commentary, and produce the YAML per `output/review-template.md`.
