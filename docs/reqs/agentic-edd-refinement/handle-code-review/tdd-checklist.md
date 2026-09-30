# TDD Checklist — Resolve Blocking Code Review and Finalize Terminal Branches

## Feature: Handle agentic-edd-refinement code review
## Status: In Progress

Source: `requirements.md` (CR-01..CR-07) + analysis JSON.
Test runner: `scripts/run_unit_tests.sh` (add `-k`/path args to scope).
Commit after every Green phase per `/git-commit` rules.

### Test Plan

- [x] T1 (CR-03): `check_refinement_limits` stops on `budgets.max_tokens` boundary (real `limits` shape, incl. exact-equality edge case) ✓
- [x] T2 (CR-03): `check_refinement_limits` does not invent keys absent from the input contract (`hard_token_limit` ignored) ✓
- [x] T3 (CR-02): `MutationLeaseStore.renew` extends `dead_by` for the holding run; rejects renewal by another run / expired lease ✓
- [x] T4 (CR-02): second `acquire` still blocked while a renewed lease is held; released lease frees the key ✓
- [x] T5 (CR-02): `renew_mutation_lease` activity exists, is registered in `module.py`, and the workflow schedules it per iteration and before approval waits ✓
- [x] T6 (CR-02): lease TTL is decoupled from `eval_timeout_seconds` (`DEFAULT_LEASE_TTL_SECONDS = 3600` in the preflight activity) ✓
- [x] T7 (CR-05): `EddPlanRunner.run` with an external `repo_root` invokes the skill harness with `cwd` inside the target repo (no module-singleton root) ✓
- [x] T8 (CR-05): `EddDoRunner.run` resolves skill `cwd`, sentinel, and `do.json` paths inside the target repo ✓
- [x] T9 (CR-01): workflow `run` accepts the input-document path (+ optional workflow id) and schedules `preflight` as the first activity ✓
- [x] T10 (CR-01): `preflight` activity resolves + validates the target repo and returns `PreflightResult` + normalized `request` (profile, lease ttl, limits) ✓
- [x] T11 (CR-01): CLI `start` performs only schema sanity-checks; it does not import/call `resolve_and_validate_target_repository` ✓
- [x] T12 (CR-04): `initialize_run` no longer runs the baseline evaluation inline (prepares record + lease only) ✓
- [x] T13 (CR-04): workflow schedules `run_baseline_evaluation` after `initialize_run` with `start_to_close_timeout` derived from `eval_timeout_seconds` ✓
- [x] T14 (CR-07): every terminal branch invokes `finalize_run` exactly once — approval rejected, execution failed, candidate rejected, regression handoff, budget stop, stop action, exception
- [x] T15 (CR-07): `finalize_run` produces `terminal.json` and releases the lease even when restore/release raises (failure recorded)
- [x] T16 (CR-06): external-target integration test — scratch git repo target, real skill-activity path, orchestration tree unchanged (AC-15)
- [ ] T17: full suite green via `scripts/run_unit_tests.sh`; fix any collateral in `test_workflow.py`, `test_cli.py`, `test_module.py`, `test_initialize_run.py`

### Current Phase: THINK complete — next is RED for T1
### Next Action: Write failing test for T1

### Notes / decisions made during TDD
- `budgets` keys: align checker to `max_tokens` (input contract); drop invented `hard_token_limit`; keep `regression_stop_threshold` when present in budgets.
- Lease: add `MutationLeaseStore.renew(repo_key, run_id, ttl)` + `renew_mutation_lease` activity; workflow renews each loop iteration and before approval waits.
- Preflight: new `preflight` activity owns input parsing + repo resolution + request construction; CLI keeps only `EddRefinementInput` schema validation.
