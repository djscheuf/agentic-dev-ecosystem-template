# Enforce Iteration, Token, and Harmful-Proposal Limits

## Story

So that agentic refinement remains bounded in cost and execution regardless of agent behavior
As a workflow requester
I want the workflow to enforce iteration and token limits, account for retry usage, and stop after repeated confirmed harmful proposals

## Source Deliverables

- `EDD-010` — Iteration and budget limit enforcement

## Entry Outcome

The workflow has current iteration, token-usage, regression-counter, and unresolved-evidence state available before scheduling another agentic or evaluation step.

## Scope

### In Scope

- Stop scheduling refinement when the maximum logical iteration count or cumulative token budget is reached.
- Prevent scheduling a step known to exceed a hard limit.
- Count observable retry token usage without counting retries as new logical iterations.
- Stop immediately after three consecutive confirmed-regression proposals and publish a human handoff report.
- Block further autonomous refinement while flaky or inconclusive evidence or unverified recovery remains unresolved.
- Exit with the best accepted state.

### Out of Scope

- Evaluating whether an individual candidate is an improvement or regression.
- Performing regression revert and recovery.
- Defining token prices or monetary budget estimation.

## Acceptance Criteria

- **EDD-010-AC1:** Given the cumulative token budget or maximum iteration count has been reached, when the workflow checks its limits, then it schedules no further refinement step and exits with the best accepted state.
- **EDD-010-AC2:** Given three consecutive proposed changes have each produced a confirmed regression, when the third revert and recovery check complete, then the workflow stops immediately regardless of remaining iteration or token budget and publishes a human handoff report of the three attempts.
- **EDD-010-AC3:** Given scheduling another agentic or evaluation step would exceed a known hard limit, when the workflow checks before scheduling, then that step is not scheduled.
- **EDD-010-AC4:** Given an Activity is retried after a timeout or worker restart, when token usage is tallied, then the retry does not count as an additional logical iteration, but its observable token usage still counts toward the cumulative budget.
- **EDD-010-AC5:** Given unresolved flaky or inconclusive evaluation evidence, or an unverified recovery, is pending, when the workflow checks limits, then it does not schedule another autonomous refinement step until the pending condition is resolved.

## Dependencies

- Durable logical-iteration and cumulative-token counters.
- Observable token usage for every Activity attempt.
- Consecutive confirmed-regression state and completed recovery checks.
- Best-accepted-state tracking and terminal human handoff reporting.

## Exit Outcome

No work is scheduled beyond configured or safety limits, retries are accounted for correctly, and the workflow stops with the best accepted state plus a human-readable handoff when autonomous continuation is unsafe.
