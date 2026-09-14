# Execute and Validate a Scoped Refinement Action

## Story

So that automated changes remain inside the owner's authorized boundary and cannot game required evaluations
As a skill owner
I want each selected refinement action executed as a traceable candidate and validated against its approved intent and file scope

## Source Deliverables

- `EDD-006` — Refinement action execution and scope validation

## Entry Outcome

A valid action has been selected and, when it changes evaluation expectations, explicitly approved by a human.

## Scope

### In Scope

- Execute the corresponding refinement Activity.
- Return structured usage metrics and changed-file information.
- Validate the resulting diff against the approved action and authorized file scope.
- Reject out-of-scope changes.
- Reject changes that remove, skip, weaken, or rewrite a failing required test merely to improve the score.

### Out of Scope

- Selecting the refinement action.
- Human approval workflow for expectation changes.
- Evaluating, accepting, committing, or reverting the candidate.

## Acceptance Criteria

- **EDD-006-AC1:** Given a selected and, if required, approved action, when the corresponding refinement Activity runs, then it returns structured usage metrics and a list of changed files.
- **EDD-006-AC2:** Given the refinement Activity completes, when its resulting diff is validated, then the workflow confirms the diff matches the approved action and stays within the authorized file scope.
- **EDD-006-AC3:** Given an agent changes a file outside the authorized scope, when candidate validation runs, then the iteration is rejected and no refinement commit is created.
- **EDD-006-AC4:** Given a refinement action would remove, skip, weaken, or rewrite a failing required test to improve its score, when candidate validation runs, then the change is rejected rather than accepted as a repair.

## Dependencies

- One selected authorized action and any required approval evidence.
- Repository context and authorized file-scope rules.
- Structured Activity usage and changed-file contracts.
- Diff inspection capable of identifying required-test weakening.

## Exit Outcome

The workflow produces a scope-valid candidate with structured usage and changed-file evidence, or rejects the iteration without creating a refinement commit.
