# Devin ATIF usage exports

**Bottom line:** The foundations layer normalizes four optional aggregate metrics from Devin ATIF exports while treating malformed telemetry as non-fatal. Raw exports remain the source for unknown billing dimensions.

## Observed CLI contract (2026-09-04)

A minimal authenticated `devin -p --export` invocation produced:

- Schema version `ATIF-v1.7`.
- Top-level `agent`, `final_metrics`, `schema_version`, `session_id`, and `steps` fields.
- `total_prompt_tokens`, `total_completion_tokens`, `total_cached_tokens`, and `total_steps` in `final_metrics`.
- No `total_cost_usd`, credit, ACU, or other billing field in that sample.

The reproducible characterization is in `docs/reqs/capture-cost-metrics/streams/devin-atif-characterization.md`.

## Foundations contract

- `HarnessUsage` is frozen and exposes optional `prompt_tokens`, `completion_tokens`, `cached_tokens`, and `cost_usd` fields.
- `HarnessResult.usage` defaults to `None`, preserving three-field construction.
- `read_atif_usage()` rejects booleans and wrong-typed metric values independently while retaining valid siblings.
- Missing files, filesystem read errors, malformed JSON, and non-object `final_metrics` return `None`.
- Unknown aggregate dimensions are not copied into `HarnessUsage`.

## Related decision

See [[decisions/ADR-015-devin-cost-metric-scope]].
