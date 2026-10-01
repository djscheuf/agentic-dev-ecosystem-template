# ADR-022: Capture Raw EDD Evaluation Command Artifacts

**Status:** Accepted  
**Date:** 2026-09-24  
**Author:** Project Team

## Bottom line

`CheckCandidateActivity` (and the underlying `EvaluateCandidateActivity`) now writes the raw stdout, stderr, exit code, parsed output, and invocation context for every evaluation `run` and `inspect` command into the per-iteration activity subfolder. This makes it possible to debug why a baseline or candidate evaluation produced zero coverage or an `infra_error` without rerunning the whole eval.

## Context

During an EDD refinement run for `grade-story-design`, the baseline check reported `infra_error` with `failure_reason: "evaluation result missing evaluation_id: []"` and all 30 required test cases showed zero coverage. The only available clues were the summarized metric record and log messages; the actual subprocess output that caused the failure was discarded.

The configured `test_command` is:

```bash
npm run test gradeDesign.tests.yaml
```

This invokes `promptfoo eval` and prints a formatted ASCII table, then exits with code `100` when any assertion fails (per ADR-021). Because the stdout is not JSON, the harness returned an empty result, `extract_evaluation_id` raised `EvaluationIdentityError`, and the `inspect_command` never ran. Without the raw stdout/stderr/exit code, we could not confirm whether the test command had even executed or what it had emitted.

## Decision

1. The real evaluation harness (`_run_evaluation_command` in `src/edd_refinement_workflow/activities/evaluate_candidate.py`) writes a JSON artifact for every invocation it performs:
   - `iterations/<n>/run-command.json` for the test/eval command.
   - `iterations/<n>/inspect-command.json` for the inspect command.
2. Each artifact contains:
   - `command_label` — `"run"` or `"inspect"`.
   - `command`, `cwd`, `timeout`, `provider`, `configuration`.
   - `returncode`, `stdout`, `stderr`, `parsed_stdout`.
   - `timed_out` flag and ISO timestamp.
3. `EvaluateCandidateActivity.run` computes the iteration directory from the progress record (preferring `logical_iteration_count`, falling back to `len(candidate_metrics) + 1`) and passes it to the harness. `CheckCandidateActivity` passes its already-resolved iteration number so the artifacts land next to `check.json`.
4. `check.json` includes a `command_artifacts` list referencing any `*-command.json` files written during that check, and `check.done.json` lists them as well.
5. The harness still returns the parsed JSON (or `{}`) so existing metric logic is unchanged. Artifacts are a side effect, not a new return-value contract.

## Consequences

### Positive

- Failed baselines and candidates now leave a complete forensic trail.
- We can distinguish "the eval command crashed", "the eval command produced non-JSON output", "the inspect command failed", and "the inspect command returned malformed metrics" without re-running the eval.
- Future EDD planning decisions can cite the artifact paths as evidence.

### Negative

- Iteration directories may contain large stdout/stderr files. We accept this because eval output is the primary debugging signal for EDD.
- Fake harnesses in unit tests must accept the new `artifact_dir` and `command_label` kwargs; existing tests already use `**kwargs`, so this is only a concern for future harness implementations.

### Neutral / Follow-up

- The root cause observed today is that `extract_evaluation_id` fails when the test command stdout is not JSON. ADR-021 already allows the `inspect_command` to resolve the latest eval itself, but the current identity chain raises before the inspect command can run. Fixing that is a separate change; the artifact capture added here will make verifying the fix straightforward.
- A duplicate `_run_evaluation_command` exists in `src/edd_refinement_workflow/activities/run_baseline_evaluation.py` (the old baseline activity). That activity is no longer used by `initialize_run`, but if it is revived it should be updated to share the same artifact-writing harness to avoid divergent behavior.
