# Require Human Approval for Evaluation Expectation Changes

## Story

So that automated refinement never silently redefines what passing means
As a human approver
I want every proposed evaluation expectation change bound to an explicit, durable approval decision before it is applied

## Source Deliverables

- `EDD-005` — Human approval for evaluation expectation changes

## Entry Outcome

Planning has selected an action that proposes changing an evaluation expectation, including an LLM evaluation rubric.

## Scope

### In Scope

- Pause the workflow durably for a decision on an exact diff or stable proposal identifier.
- Treat timeout or absence of a decision as no approval.
- Preserve proposal context across worker restarts.
- Route rejection back to planning or stop according to policy.
- Apply only the exact approved diff and distinguish it from a skill-behavior change.

### Out of Scope

- Approval for ordinary skill, coverage, scripted-check, or supporting-document refinements that do not change evaluation expectations.
- Defining approver identity or authorization infrastructure.
- Candidate quality comparison after an approved change is applied.

## Acceptance Criteria

- **EDD-005-AC1:** Given the selected action proposes changing an evaluation expectation, including an LLM rubric, when the workflow reaches the approval step, then it pauses durably and waits for an explicit human decision bound to the exact proposed diff or a stable proposal identifier.
- **EDD-005-AC2:** Given an approval request is pending, when no decision is received before the configured approval timeout, then the workflow treats the absence of a decision as no approval, never as implicit approval.
- **EDD-005-AC3:** Given a human rejects the proposed evaluation change, when the rejection is recorded, then the workflow returns to planning or stops according to policy, and the change is not applied.
- **EDD-005-AC4:** Given a human approves the exact proposed diff, when execution proceeds, then only the approved diff is applied and it is recorded as a human-approved evaluation change distinct from a skill-behavior change.
- **EDD-005-AC5:** Given a worker restarts while a run is waiting for approval, when the workflow resumes, then it continues waiting on the same pending approval without losing the proposal context.

## Dependencies

- A planning result that identifies the exact proposed expectation change.
- Durable workflow signaling and approval timeout policy.
- Stable proposal identity or content-bound diff identity.
- A trusted human decision channel.

## Exit Outcome

The proposed expectation change is either rejected or times out without being applied, or the exact human-approved diff is authorized for execution with its distinct measurement context preserved.
