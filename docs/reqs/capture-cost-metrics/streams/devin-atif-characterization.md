# Devin ATIF characterization

**Bottom line:** Devin CLI currently exports `ATIF-v1.7`; the observed minimal invocation includes aggregate prompt, completion, and cached-token totals, but no USD-cost or extra billing dimension.

**Observed:** 2026-09-04

## Invocation

```bash
devin -p --export "$tmpdir/devin-trajectory.json" \
  --respect-workspace-trust false -- "Reply with exactly OK."
```

## Result

- Exit code: `0`
- Standard output: `OK`
- Schema version: `ATIF-v1.7`
- Top-level keys: `agent`, `final_metrics`, `schema_version`, `session_id`, `steps`
- `final_metrics` keys observed:
  - `total_prompt_tokens`
  - `total_completion_tokens`
  - `total_cached_tokens`
  - `total_steps`
- `total_cost_usd` was not present.
- No credit, ACU, or other billing dimension was present.

Metric values are intentionally omitted because they vary per invocation and are not part of the schema contract.
