# ClaudeHarness (claude CLI adapter)

**Bottom line:** Unlike `DevinHarness`, the `claude` CLI does not write its own trajectory file — `ClaudeHarness` must capture stdout itself and write it to `export_path`. This was missed in the initial implementation (2026-10-02) and fixed by adding an explicit `export_path.write_text(result.stdout)` call.

## Vendor asymmetry with DevinHarness

- `devin -p --export <path>` has the CLI write its own trajectory/export file; `DevinHarness` only ever *reads* that path back (`read_atif_usage_result`). There is no write call in `devin_harness.py`.
- `claude -p --output-format stream-json --verbose` streams NDJSON to **stdout**, not to a file. `ClaudeHarness` computes an `export_path` (`claude-trajectory.jsonl`) and logs it as the telemetry source, but must explicitly persist `result.stdout` there itself — the CLI has no equivalent of `--export`.
- Anyone adding a third harness should check which behavior their CLI has before copying either pattern verbatim.

## Harness integration (2026-10-02)

- `common.ClaudeHarness.run()` writes `result.stdout` to `export_path` immediately after the subprocess call, before parsing usage via `read_claude_usage_result()`.
- Storage mode mirrors Devin: activity-context runs retain `claude-trajectory.jsonl` beside `activity.log` and `claude.log`; out-of-context runs use a temporary directory that is parsed then cleaned up via `ExitStack`.
- Usage parsing is independent of exit code and never raises; parse failures are logged as a sanitized `RejectClaudeTelemetry` warning, never the trajectory content itself.
- Tests: `test_run_without_activity_context_writes_parses_and_cleans_temporary_trajectory` and `test_run_with_activity_context_retains_trajectory_beside_activity_logs` in `src/common/tests/test_claude_harness.py`.

## Shared usage-coercion helpers

`_token()`/`_cost()` were duplicated verbatim between `claude_harness.py` and `atif_usage.py` in the initial implementation. They are now extracted into `common/harness_usage.py` as `coerce_token`/`coerce_cost`, imported by both parsers, and unit-tested in isolation in `src/common/tests/test_harness_usage.py`.

## Related

See `docs/reqs/claude-harness/claude-harness.review.yaml` for the code review that surfaced both issues above, and [[devin-atif]] for the parallel Devin-side usage contract.
