# Smells and refactors

Use this to name what you see and recommend a concrete, incremental fix. Recommend small steps that tests can protect. Explain *why* the change is better so the author learns the technique, not only the result.

## Core refactor: separate the what from the how
Define *what* must happen in one place, and *how* to process it in another.

```text
Before: repeated condition mixed into processing
  for invoice in invoices:
      if invoice.total > 1000 and invoice.region == "US": ...

After: the decision is named once; processing just uses it
  def should_flag_for_review(invoice): return invoice.total > 1000 and invoice.region == "US"
  for invoice in invoices:
      if should_flag_for_review(invoice): ...
```

This applies to copy-pasted blocks, duplicated strings, and long if/else chains. Move the repeated data or rule into a dictionary, collection, or named function (the *what*), then iterate to process it (the *how*).

## Smell catalog

| Smell | Why it hurts | Fix |
|---|---|---|
| Same object or variable name repeated on every line ("wall of characters") | Noise hides the signal | Object or collection initializers; mapping libraries |
| Long if/else-if chain on an object's state | Each new state means edits scattered across code | State pattern: a new state is a new class implementing an interface |
| Long chain on a type or key | Same, plus easy to miss a case | Dictionary of handlers, or polymorphism; consider the Rule of 3 |
| Fat interface injected but barely used | Needless coupling; hard to fake in tests | Interface segregation: depend on a narrow abstraction of what is used |
| Region or fold blocks inside methods | They hide ugliness instead of fixing it | Do not use them; extract named methods |
| Comments narrating blocks of code | The block wants a name | Extract a method; make conditions read like questions |
| Multi-part boolean condition | Reader must parse every part | Extract into a well-named variable (`canComputeTotalBill`) |
| Deep nesting with the main path buried | Raises cognitive load | Guard clauses and early returns |
| Variable named after its assignment (`totalGreaterThan1000`) | Repeats the code; becomes misleading | Name the decision or concept (`exceedsCreditLimit`) |
| Placeholder names (`temp`, `data`) left behind | Forgot to finish the refactor | Name by business meaning |
| Method with hidden side effects | Breaks trust; causes surprise bugs | Rename for what it does, or remove the side effect |
| Copy-pasted tests with meaningless differences | Tests verify nothing new | Parameterize, or express each case's intent |
| Test that still passes when the code's values are changed | Test verifies nothing | Assert the behavior that matters |
| Long data migrations or scripts written dirty | They are copied most, so dirt multiplies | Apply the same clean-code rules |
| Same utility reimplemented | Drift and duplicate bugs | Reuse the existing one |
| Concrete types and `new` scattered through service code | Hard to test or swap | Inject abstractions |

## Recommending a refactor
1. **Cover with tests first** if the area lacks them.
2. **Take the smallest safe step**: extract a variable, rename, pull out a method.
3. **Explain why**, in terms the author can reuse next time.
4. **Point to IDE refactoring tools** where they make the step safe and cheap.
5. **Match the team's level.** The most idiomatic solution is a liability if the team cannot maintain it. Prefer a step the team can own, and coach beyond it over time.
6. **Keep refactors out of feature changes** when they are large. Recommend a separate change.
7. **Iterate.** Untrustworthy or tangled code cannot be fixed in one pass; expect a few rounds of design, refactor, and test.

## When not to recommend
- Repetition with fewer than three instances. The right abstraction is not yet visible (Rule of 3).
- Changes whose only benefit is stylistic preference.
- Rewrites of code unrelated to the change.
