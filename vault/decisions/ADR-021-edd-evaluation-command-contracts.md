# ADR-021: EDD Evaluation Commands May Exit Non-Zero and Inspect Commands Return Raw Result Lists

**Status:** Accepted
**Date:** 2026-09-22
**Author:** @project-team

## Bottom line

The EDD evaluation harness must treat a non-zero exit from `promptfoo eval` as a normal test-result signal, not as an infrastructure failure, and must derive `passing/failing/total/percentage` metrics from the raw list that `scripts/inspect-eval.js` returns.

## Context

The EDD baseline Activity runs:

```bash
npm run test gradeDesign.tests.yaml
```

which internally invokes `promptfoo eval`. When any assertion fails, `promptfoo` exits with code 100. The Activity harness used `subprocess.run(..., check=True)`, which raised `CalledProcessError` and crashed the Activity. This made it impossible to baseline a skill that currently fails its evals, which is the normal starting state for an EDD refinement loop.

After relaxing the exit-code check, a second problem appeared: the inspect command (`scripts/inspect-eval.js --all --json`) returns a JSON array of per-result objects, not the pre-computed summary map the Activity expected. The fields `passing`, `failing`, `total`, and `percentage` were missing, so the metric was rejected as malformed.

## Decision

- The subprocess harness runs evaluation commands with `check=False`.
- It parses JSON from stdout when present; if stdout is not JSON (e.g. promptfoo's formatted table), it returns an empty result and lets the inspect command supply the metrics.
- `subprocess.TimeoutExpired` is still converted to `TimeoutError` so the Activity can distinguish timeouts from assertion failures.
- When the inspect command returns a list, the Activity computes:
  - `passing` = count of results with `success === true`
  - `failing` = total − passing
  - `total` = list length
  - `percentage` = passing / total × 100
- The inspect command is only required to carry an `{evaluation_id}` placeholder when the test command itself reliably emits an evaluation id; otherwise the inspect command may resolve the latest eval itself (as `inspect-eval.js` does).

## Consequences

### Positive

- Baseline and candidate evaluations can start from a failing skill and still produce usable metrics.
- The Activity no longer confuses assertion failures with infra failures.

### Negative

- Test commands that legitimately crash with a non-zero, non-100 exit code now look like a run with zero results unless stderr is inspected. We accept this trade-off because the inspect command is the authoritative metric source.

### Neutral / Follow-up

- Consider logging stderr / exit codes for observability without failing the Activity.
- If promptfoo adds a machine-readable summary output, prefer consuming that over counting raw result rows.

## Alternatives Considered

- **Whitelist only exit code 100 as success** — rejected because other eval harnesses may use different non-zero codes for failed tests.
- **Require the test command to print a JSON summary with metrics** — rejected because it forces every promptfoo-based eval to be wrapped in a custom script; deriving metrics from the inspect list is more general.

## 2026-09-26 addendum: direct Node invocation

In practice `npm run test <config>` polluted stdout with npm's lifecycle banner, so the Python harness could not parse the JSON `evaluation_id`. EDD refinement inputs now invoke `node scripts/run-eval.js <config>` directly. See [[services/edd-evaluation-commands.md]].
