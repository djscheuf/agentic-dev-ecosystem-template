# Readability and trust

**Premise**: Code is read far more often than it is written, and changing code requires understanding it. The compiler optimizes away names and structure, so the code is written for the next developer, who may be the author in six months. Readability is the prerequisite for every other quality attribute.

Three properties to check: **informative**, **respectful of cognitive load**, **trustworthy**.

## 1. Informative (not merely descriptive)
Names should capture intent and the decision they enable, not repeat the instruction that produced them.

- Weak: `temp`, `billingTotalGreaterThan1000`
- Better: `exceedsCreditLimit`, `shouldFlagInvoice`, `canComputeTotalBill`

**Why descriptive names fail**: they rot like comments. `totalIsGreaterThan1000 = total > 1000` becomes misleading when the rule changes to `>=`, or when `1000` becomes a configurable limit. The name repeats the code, and repetition drifts.

**DRY applies to information and decisions, not just lines.** A name that restates its own assignment is a DRY violation. Ask what concept or decision the value represents, and name that. Pull names from the business domain where possible, so a business reader can follow the logic.

**Method names**: describe intent in domain terms. A name that just concatenates steps (`checkTaxableAndComputeTaxesAndMakeReadyToPost`) adds no information beyond the body.

**Pattern names** (Factory, Strategy, Adapter) are cognitive shorthand. Use them accurately so readers can skip the internals. Use domain language in the problem space and pattern vocabulary in the solution space.

Review questions:
- Could someone unfamiliar with this code infer the why from the names alone?
- If the implementation changes, will this name become wrong?
- Are any names still `temp`, `data`, `result`, `flag`, left after the concept became clear?
- Do terms carry domain or cultural meaning a newcomer would not know?

## 2. Respectful of cognitive load
Readers hold roughly five things (plus or minus two) in working memory. Structure should let them put context down.

- **Exit early.** Guard clauses and early returns are for the reader, not the compiler. Handling the exceptional case first lets the reader forget it.
- **Name complex conditions.** Extract a multi-part boolean into a well-named variable so the reader can treat it as one idea.
- **Limit nesting depth** and horizontal scroll.
- **Answer common questions quickly.** Order code so the main path is obvious.
- **If conditions should read like questions** (`if (isDuplicateAddress)`), not like evaluations.
- **Comments that narrate a block** usually mean an unextracted, unnamed method.

Review questions:
- How many concepts must I hold at once to understand this method?
- Do I have to read the whole method before I can predict its result?
- Does a branch force me to track a condition for hundreds of lines?

## 3. Trustworthy
Code should do what it says, nothing more and nothing less. Untrustworthy code forces readers to verify internals before using it, which costs comprehension effort and breeds more untrustworthy code.

**Main breaker of trust: hidden side effects.**
- `MarkServiceAssigned` that also re-enables the service. A later caller who disables then marks assigned gets a silent bug.
- An adapter with an optional parameter that permanently mutates its default, so call order changes behavior.
- Leaky abstractions that force readers to know the implementation.

Fixes:
- Name the operation for what it really does, using business terms (`ActivateAndAssignTo`, or better a domain verb), rather than appending `AndXYZ` for each effect.
- Remove or isolate the side effect.
- Add tests that prove what the code claims, then refactor incrementally toward trustworthy.

Other trust signals:
- Undocumented input-order or precondition assumptions.
- Missing edge-case handling that callers must discover by failure.
- Inconsistent use of patterns, so readers cannot predict behavior.

Review questions:
- Does this method do anything its name does not say?
- Would I need to read the body before calling it?
- Are preconditions and assumptions stated or enforced?

## Priorities
- Misleading name or hidden side effect that can cause a wrong result: `suggestion`, or `blocking` if it already causes one.
- Cognitive-load and naming improvements: usually `suggestion` or `comment`.
