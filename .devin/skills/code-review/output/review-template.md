# Review document template

Write the review as a single YAML document. Ask the user for the output path at invocation; default to `code-review-<branch>.yaml` in the working directory.

## Schema

```yaml
code_review:
  identified_requirements:
    - title: ""                 # story or requirement name / id
      intent: ""                # one-line statement of the need
      acceptance_criteria: []   # list of criteria, if any
      source: ""                # where it was found (doc path, PR description, ticket, inferred)
  impacted_scope:
    directly_changed: []        # modules, components, endpoints, tables, configs
    dependents: []              # callers and consumers of changed code
    contracts_touched: []       # APIs, schemas, migrations, events, config keys, flags
    workflows_affected: []      # behaviors in user terms
  general_commentary:
    verdict: approve            # approve | approve-with-suggestions | request-changes
    summary: ""                 # overall assessment: strengths, main risks, what to do next
    limitations: []             # what could not be checked (e.g. tests not run)
  review_comments:              # in the order discovered
    - description: ""           # the observed gap, stated factually
      type: implementation      # see types below
      impact: ""                # why it matters, and to whom
      recommendation: ""        # direct statement of what to do
      guidance: ""              # coaching, phrased as a question where possible
      priority: suggestion      # blocking | suggestion | comment
      locations: []             # list of "path:start-end" (or "path" when whole-file)
      in_diff: true             # true if on changed code; false if from the Phase 5 sweep
```

All fields are required for every comment except `guidance`, which may be an empty string when a question adds nothing.

## Types

| Type | Use for |
|---|---|
| `story` | Requirement missing, ambiguous, partially met, or unrequested change |
| `testing` | Missing, weak, fake, flaky, or unreadable tests |
| `design` | Responsibilities, coupling, abstractions, layering, architectural fit |
| `implementation` | Logic defects, edge cases, error handling, correctness of the code itself |
| `security` | Authentication, authorization, input handling, secrets, data exposure |
| `performance` | Scalability, inefficiency, unbounded growth |
| `readability` | Names, structure, cognitive load, hidden side effects |
| `documentation` | Missing or stale explanation, comments, change description |
| `refactor` | Reuse, duplication, or restructuring opportunities (usually from Phase 5) |

Choose the single best type. If a finding spans two, pick the one that best describes the fix.

## Priority

Priority is one of `blocking`, `suggestion`, or `comment`. It reflects whether the item should stop the merge, and is judged from three things together:

- **Impact**: what goes wrong (cosmetic, degraded experience, wrong result, data loss, security exposure).
- **Scale**: how much is affected (one spot, several workflows, every call).
- **Criticality**: how bad the failure is for users and the business.

| Priority | Meaning | Typical examples |
|---|---|---|
| `blocking` | Must be resolved before merge | Security gap affecting every call; a broken or missing acceptance criterion; data-corrupting bug; no requirement for the change |
| `suggestion` | Should be addressed, here or as tracked follow-up | A gap affecting several workflows; scalability risk; missing edge-case tests; design improvement with real payoff |
| `comment` | Optional or informational; author may decline | Typo in a label; naming nicety; observation for future reference |

Rules of thumb:
- A high-impact item at small scale can be `suggestion`; the same at wide scale is `blocking`.
- Do not escalate style or preference to `blocking`.
- If you are unsure whether something is `blocking`, say why in `impact` and choose `suggestion`, then mention it in `general_commentary.summary`.

## Verdict
- `request-changes`: at least one `blocking` comment exists.
- `approve-with-suggestions`: no `blocking` comments, but at least one `suggestion` worth acting on.
- `approve`: only `comment` items, or none.

## Field guidance
- **description**: factual and specific. Name what was observed, not what the author did wrong.
- **impact**: who or what is affected, and how, at what scale.
- **recommendation**: direct and actionable. State the change to make.
- **guidance**: coaching voice. Prefer a question, or the reasoning behind the recommendation.
- **locations**: real paths and line ranges from the reviewed revision. Include every location the comment applies to.
- **in_diff**: `false` for Phase 5 findings outside the changed lines.

## Worked example

```yaml
code_review:
  identified_requirements:
    - title: "Audit trail for failed operations"
      intent: "Testers need to quickly answer why something did not work during UAT"
      acceptance_criteria:
        - "Failures are recorded with user, time, and reason"
        - "Audit records can be filtered by date and user"
        - "Audit records can be exported"
      source: "docs/stories/audit-trail.md; PR description"
  impacted_scope:
    directly_changed:
      - "src/Audit/AuditService.cs"
      - "src/Audit/AuditController.cs"
    dependents:
      - "src/Orders/OrderService.cs (writes audit records)"
    contracts_touched:
      - "GET /api/audit (new)"
    workflows_affected:
      - "Tester investigates a failed order"
  general_commentary:
    verdict: request-changes
    summary: >
      Story intent is met and the approach is sound. One scalability problem
      blocks merge. Filtering and fail-safe logging lack tests. Export is
      partially implemented by design, per the PR description.
    limitations:
      - "Integration tests were not run (no database available)"
  review_comments:
    - description: "The audit query loads all audit records into memory and applies filters afterward."
      type: performance
      impact: "Memory use and latency grow with every audit record; affects every call to the audit endpoint."
      recommendation: "Push date and user filtering into the database query. Use the ORM's translation, with raw SQL only as a fallback."
      guidance: "What will the record count be in six months, and how would we notice the endpoint slowing down?"
      priority: blocking
      locations:
        - "src/Audit/AuditService.cs:48-67"
      in_diff: true
    - description: "No tests cover filtering by date or by user, and the fail-safe logging path is untested."
      type: testing
      impact: "Acceptance criterion 2 has no evidence, and a silent logging failure would defeat the feature's purpose."
      recommendation: "Add tests for each filter and for the path taken when the audit write fails."
      guidance: "If the filter logic regressed tomorrow, which test would tell us?"
      priority: suggestion
      locations:
        - "src/Audit/AuditService.cs:48-95"
        - "tests/Audit/"
      in_diff: true
    - description: "Export is only partially implemented (CSV only)."
      type: story
      impact: "Acceptance criterion 3 is partly met. The PR description states this is an intentional prioritization."
      recommendation: "Confirm a follow-up item exists for the remaining formats."
      guidance: ""
      priority: comment
      locations:
        - "src/Audit/AuditController.cs:30-41"
      in_diff: true
    - description: "OrderService and ReturnService build the same audit-message text in two places."
      type: refactor
      impact: "Message wording can drift between the two; future audit fields must be added twice."
      recommendation: "Extract a single audit-message builder and use it from both services."
      guidance: "Would a third caller appear soon? If so, this is the moment to extract it."
      priority: suggestion
      locations:
        - "src/Orders/OrderService.cs:120-134"
        - "src/Returns/ReturnService.cs:88-102"
      in_diff: false
```
