# Confirm Regressions, Revert Harmful Changes, and Verify Recovery

## Story

So that flaky evidence cannot discard useful work and confirmed harmful changes cannot leave the repository degraded
As a skill owner
I want an apparently worse candidate re-evaluated unchanged, a confirmed regression reverted, and the restored accepted state verified before refinement continues

## Source Deliverables

- `EDD-009` — Regression confirmation, revert, and recovery

## Entry Outcome

Comparison has found that a candidate evaluation performs worse than the current best accepted state.

## Scope

### In Scope

- Re-evaluate the unchanged candidate before classifying a regression.
- Distinguish confirmed regression from unstable, flaky, timed-out, errored, or inconclusive evidence.
- Notify and hand off to a human when evidence does not support an autonomous decision.
- Record degraded evidence and increment the consecutive confirmed-regression counter.
- Restore the last accepted state and rerun the suite to verify recovery.
- Preserve reverted-proposal context for future planning.

### Out of Scope

- Initial candidate evaluation and ordinary quality-ratchet acceptance.
- Selecting or executing a replacement refinement action.
- Defining the stop threshold after consecutive confirmed regressions.

## Acceptance Criteria

- **EDD-009-AC1:** Given a second evaluation run against the unchanged candidate also performs worse than the current best state, when the regression is confirmed, then both degraded results and the change summary are recorded, the consecutive-regression counter increments, the last accepted state is restored, and the suite is rerun to verify recovery.
- **EDD-009-AC2:** Given the second evaluation run returns to or exceeds the current best state, when results are compared, then the result is treated as unstable, a human is notified, and no autonomous commit or revert decision is made.
- **EDD-009-AC3:** Given the second evaluation run errors, times out, or otherwise fails to establish stable equivalence, improvement, or regression, when results are classified, then the evidence is recorded as suspected flakiness, a human is notified, and autonomous refinement does not continue.
- **EDD-009-AC4:** Given a confirmed regression has been reverted, when the recovery evaluation runs, then it must demonstrate that the restored accepted state matches its previously recorded performance before another proposal is allowed.
- **EDD-009-AC5:** Given the recovery evaluation cannot verify the restored performance, when recovery fails, then autonomous refinement stops and hands off to a human.
- **EDD-009-AC6:** Given a proposal is reverted, when it is recorded, then its change summary, affected files, rationale, observed degradation, confirmation result, and recovery result remain visible to future planning steps.

## Dependencies

- Current-best accepted-state metrics and restorable repository revision.
- Repeatable complete-suite evaluation with stable configuration and provider.
- Human notification and handoff path.
- Durable progress history and consecutive-regression counter.

## Exit Outcome

The evidence either remains unresolved and is handed to a human without autonomous mutation, or a confirmed harmful proposal is reverted and recovery is verified before another proposal can begin.
