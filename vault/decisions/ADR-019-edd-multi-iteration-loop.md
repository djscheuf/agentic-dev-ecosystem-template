We run `EddRefinementWorkflow` as a single deterministic `while` loop over the planning, approval, execution, validation, evaluation, comparison, and commit activities, with the progress record as the only state carried between cycles.

## Context

The EDD refinement workflow was implemented as one pass through planning and one candidate evaluation. The bring-to-ready work required it to keep improving the target skill through multiple autonomous iterations until configured iteration or token budgets were exhausted, a stop recommendation from `PlanRefinementActivity` arrived, or a terminal regression happened.

## Decision

- Wrap the entire post-baseline agentic flow in one `while True`.
- Check `check_refinement_limits` at the start of every cycle and immediately `finalize_run` when it returns `schedule_next_step: false`.
- Update durable counters after `execute_refinement_action` and `evaluate_candidate` so `logical_iteration_count` and `cumulative_token_usage` always reflect the latest persisted state before the next planning decision.
- Compare the latest candidate against `record["best_accepted_state"]["metrics"]` when present; otherwise compare against the baseline evaluation.
- On `accept`, run `commit_accepted_candidate`, then set `record["best_accepted_state"]` and reset `record["consecutive_confirmed_regressions"]` so the next `plan_refinement_action` call sees the new state.
- On `rerun`, run the degraded-candidate confirmation and regression recovery path; if `next_state` is `planning`, continue the loop.
- On `reject`, append the rejected candidate to `record["candidate_history"]` and continue.

## Consequences

- The same `PlanRefinementActivity` sees the full, updated `progress_record` on each iteration, so it can use current budgets, regressions, and best state to recommend the next action or stop.
- Candidate comparison no longer needs an existing `best_accepted_state`; the first improvement over the baseline can be accepted and committed.
- `compare_candidate_to_best` now uses `.get` defaults for `passing`, `required_coverage`, and `measurement_context` so baseline or candidate records with missing fields still produce a decision.
- The workflow returns a terminal result on any cycle where limits, a planning stop, approval rejection, failed execution, invalid candidate, or non-recoverable regression ends the run.
- Continue-As-New is not implemented; the loop runs entirely inside one `EddRefinementWorkflow.run` invocation. If very long runs become common, split the loop across Continue-As-New boundaries.
