# ADR-012: Skill Activity Invocation Configuration

**Status:** Accepted
**Date:** 2026-09-02
**Author:** Project team

## Bottom line

Skill Activity invocation configuration starts with a core resolution slice: secure defaults, per-skill model and permission overrides, partial inheritance, validation, compatibility, tests, and documentation.

## Context

The current `DevinHarness` applies one flat model and permission mode to every Skill Activity. Artifact-producing unattended skills need explicit edit permission, while unrestricted permissions must not become the default.

## Decision

- Keep configuration colocated at `src/orchestrator/devin_harness.config.json`.
- Add `defaults` and canonical-skill-keyed `skills` objects.
- Use `auto` as the default permission mode.
- Require artifact-producing unattended skills to opt into `accept-edits` explicitly.
- Reject invalid known fields, including null, empty, wrong-typed, or unsupported values; ignore unknown keys for forward compatibility.
- Map the legacy flat `model` and `permission_mode` fields to the new defaults.
- Preserve the generic `Harness` interface and existing Skill output/sentinel contracts.
- Measure the slice by requiring all automated resolution cases and representative configured Story Analysis invocations to use expected settings without permission-related artifact failures.
- Defer referenced Devin profiles and Cadence retry snapshot transport to follow-up slices.
- In the retry follow-up, capture configuration at Activity start and reuse that snapshot for all retries of that Activity.

## Consequences

### Positive

- The first implementation remains bounded around profile resolution.
- Existing installations remain compatible.
- Default permissions remain conservative.
- New configuration keys can be introduced without breaking older readers.

### Negative

- Artifact-producing skills require explicit overrides to run unattended.
- Ignoring unknown keys can conceal misspellings outside known fields.
- Referenced profiles and retry snapshot transport require follow-up work.

### Neutral / Follow-up

- Define referenced-profile CLI and filesystem semantics.
- Decide where the Activity-start snapshot is serialized for Cadence retries.
- Decide whether legacy flat configuration receives a future deprecation date.

## Alternatives Considered

- **Keep the full feature in one story** — rejected because configuration, profiles, retries, migration, logging, and documentation formed an oversized slice.
- **Workflow-start or latest-per-attempt retry settings** — rejected in favor of an Activity-start snapshot.
- **Reject legacy flat configuration** — rejected in favor of backward-compatible mapping.
- **Reject all unknown keys** — rejected in favor of forward-compatible parsing.
- **Use `accept-edits` as the global default** — rejected to preserve least privilege; write-capable skills opt in explicitly.

## Design refinement (2026-09-02)

- `run_skill` exposes canonical `SkillActivityInput.skill_name` through invocation-scoped context while keeping `Harness.run(prompt, cwd)` unchanged; `DevinHarness` consumes the context and alternate Harness implementations may ignore it.
- Resolve each invocation to a fresh immutable effective profile from an immutable worker-loaded configuration. Per-field precedence is skill override, structured default, legacy flat default, then secure hardcoded default.
- Do not use prompt parsing or process-global mutable current-skill state.
- Configuration remains worker-loaded for this slice. Persisting an Activity-start snapshot in Cadence history remains deferred.
