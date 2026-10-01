# ADR-024: Approval for Evaluation-Expectation Changes is Decoupled from Diff Hash

Approval for `propose_evaluation_expectation_change` is gated on the action type and a stable `proposal_id`, not on a pre-computed diff hash. The actual applied diff hash is recorded only after `edd_do` executes.

## Context

The EDD refinement workflow supports a `propose_evaluation_expectation_change` action that edits the evaluation suite (e.g., an LLM rubric or expected score). The original implementation gated `requires_approval` on the presence of a `proposed_diff_hash`, and the workflow called `record_human_approved_evaluation_change` before `edd_do` using a value from the request.

That coupling was wrong because:

- The planner runs before any files are modified, so it cannot produce a meaningful diff hash.
- Preflight executes against a clean worktree, so it cannot supply a diff hash either.
- Recording an "applied" diff hash before execution meant the approval audit compared a hash that had not been produced by the actual run.

## Decision

1. `EddPlanRunner` sets `requires_approval = (action == "propose_evaluation_expectation_change")` regardless of any hash.
2. `EddPlanRunner` generates a stable `proposal_id` from `run_id + iteration_number` when the skill output does not provide one. The identifier is deterministic so a resumed workflow references the same approval request.
3. The workflow requests human approval immediately after planning when `requires_approval` is true, but only records the applied change after `edd_do` completes, using the actual `execution.diff_hash`.
4. `ApprovalService` treats `proposed_diff_hash` as optional. If it is present, `record_applied_change` still enforces the integrity check; if it is absent, the service records the applied hash without comparison.
5. `EddDoRunner` no longer takes or validates an `approved_diff_hash`; the guard is enforced by the workflow's approval step instead.

## Consequences

- A `propose_evaluation_expectation_change` plan always pauses for explicit human approval before any evaluation suite changes are committed.
- The CLI and any UI must surface the generated `proposal_id` so the approver knows which identifier to pass to the `approve` or `reject` command.
- Approval history still captures the actual applied diff hash, but only after it has been produced by the execution step.
