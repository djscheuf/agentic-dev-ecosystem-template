# Evaluate Candidates, Advance the Quality Ratchet, and Finalize the Run

## Story

So that accepted skill state only moves forward and every terminal outcome remains independently auditable
As a skill owner and workflow requester
I want each valid candidate evaluated comparably, accepted only when it adds qualifying value, and summarized with the repository left at its best accepted state

## Source Deliverables

- `EDD-007` — Candidate state evaluation
- `EDD-008` — Quality ratchet comparison and acceptance decision
- `EDD-011` — Run finalization and audit report

## Entry Outcome

A refinement action has produced a candidate that passed intent and scope validation.

## Scope

### In Scope

- Evaluate the candidate with the same deterministic command, configuration, and pinned provider as the baseline.
- Record candidate metrics, required coverage, artifacts, timeout attempts, retries, and infrastructure errors.
- Compare candidates with the current best accepted state using absolute passing count and meaningful required coverage.
- Commit qualifying improvements deterministically and retain the best accepted state.
- Keep human-approved expectation changes in separate measurement contexts.
- Publish a terminal progress record and workflow result for every terminal outcome.
- Leave the repository at its best accepted state and release its mutation lease.

### Out of Scope

- Executing or scope-validating the refinement action.
- Confirming and recovering from an apparent regression beyond initiating the required rerun path.
- Enforcing iteration, token, or consecutive-regression stop limits.

## Acceptance Criteria

### Candidate Evaluation

- **EDD-007-AC1:** Given a refinement action has completed and passed scope validation, when the candidate is evaluated, then the same deterministic evaluation command, configuration, and pinned provider used for the baseline are invoked again.
- **EDD-007-AC2:** Given the candidate evaluation completes, when results are recorded, then structured passing, failing, total, percentage, and required-coverage metrics and artifact references are captured.
- **EDD-007-AC3:** Given the candidate evaluation exceeds its configured Activity timeout, when the timeout is reached, then the attempt is recorded, the configured retry policy is applied, and the attempt does not count as an additional logical iteration.
- **EDD-007-AC4:** Given the evaluation Activity errors for infrastructure reasons, when the failure is recorded, then it is not treated by itself as evidence of a product regression.

### Quality Ratchet Decision

- **EDD-008-AC1:** Given a candidate increases the absolute number of passing evaluations without reducing required test-case coverage, when comparison completes, then the change is committed deterministically, the consecutive-regression counter resets, and the candidate becomes the new best accepted state.
- **EDD-008-AC2:** Given a candidate covers a previously uncovered required test case while preserving the prior absolute passing count, when comparison completes, then the change may be committed and accepted even if a larger denominator lowers the pass percentage.
- **EDD-008-AC3:** Given every required test case is already covered and a candidate only increases the total evaluation count, when comparison completes, then the candidate is not classified or committed as an improvement.
- **EDD-008-AC4:** Given a candidate performs worse than the current best accepted state, when comparison completes, then it is not immediately reverted or committed, and the workflow reruns the complete suite against the unchanged candidate before deciding.
- **EDD-008-AC5:** Given a candidate neither improves passing count nor adds meaningful coverage, when comparison completes, then no commit is made and the reason no qualifying value was added is recorded.
- **EDD-008-AC6:** Given an evaluation expectation change was applied with human approval, when comparing before-change and after-change scores, then the two measurement contexts are kept separate rather than treated as directly comparable.

### Finalization and Audit

- **EDD-011-AC1:** Given a run reaches any terminal outcome, when finalization runs, then it publishes a terminal progress record and workflow result containing baseline and final metrics, absolute changes, terminal reason, accepted iteration and commit references, and rejected or reverted iteration summaries.
- **EDD-011-AC2:** Given a run reaches any terminal outcome, when finalization completes, then the repository mutation lease is released and the progress record identifies the target repository and final accepted commit.
- **EDD-011-AC3:** Given a run finalizes, when the terminal repository state is checked, then it corresponds to the best accepted state, not merely the last attempted state.
- **EDD-011-AC4:** Given pending human decisions or flaky-result evidence exist at the time of termination, when the report is published, then those pending or resolved items are included in the report rather than silently dropped.
- **EDD-011-AC5:** Given the workflow terminates due to an unrecoverable error before any commit is accepted, when finalization runs, then the report still identifies the target repository, the failure reason, and that no accepted commit exists, and the lease is still released.

## Dependencies

- A scope-valid candidate and recorded baseline or current-best metrics.
- Deterministic evaluation configuration, pinned provider, timeout, and retry policy.
- Deterministic required-test-case coverage mapping.
- Git commit and best-accepted-state tracking.
- Durable progress records and terminal cleanup behavior.
- Regression confirmation and recovery handling for degraded candidates.

## Exit Outcome

A qualifying candidate becomes the new committed best state, a non-qualifying candidate remains uncommitted, or a degraded candidate enters confirmation; on termination, the repository is restored to the best accepted state, the lease is released, and a complete audit report is published.
