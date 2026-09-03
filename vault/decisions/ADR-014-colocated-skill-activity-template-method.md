# ADR-014: Colocated Skill Activity Configuration and Template Method

**Status:** Accepted
**Date:** 2026-09-03
**Author:** Project team

## Bottom line

Skill Activities are proposed to own adjacent JSON configuration and specialize a fixed `SkillActivity.execute` lifecycle through typed no-op transformation hooks. Harnesses receive namespaced configuration mappings, and each implementation validates and translates only its own namespace.

## Context

The current function-based `run_skill` contains Story Analysis output conventions, while `DevinHarness` selects per-skill settings from one central configuration through invocation context. Adding independently owned workflow Activities would continue expanding generic skill-name switches and central profile maps.

## Proposed decision

- Place a same-stem `*.config.json` beside every concrete Activity.
- Use `activity` and `harness` top-level namespaces.
- Pass the immutable `harness` mapping to `Harness.run`.
- Let `DevinHarness` consume `harness.devin`, reject unknown keys inside that namespace, and ignore sibling Harness namespaces.
- Replace `run_skill` with a fixed template method and typed no-op hooks for prompt, sentinel path, Harness config, invocation context, output path, and result.
- Keep required skill identity and output-contract values explicit rather than optional hooks.
- Preserve least-privilege defaults, sentinel validation, stale-sentinel cleanup, logging hygiene, and Worker-lifetime configuration snapshots.

## Consequences

### Positive

- Activity behavior and configuration move together.
- New skills do not require edits to a central skill catalog.
- Harness-specific command translation remains isolated.
- Lifecycle invariants remain controlled by one template.

### Negative

- Every Activity gains an additional configuration file.
- The Harness protocol and all fakes/callers require coordinated migration.
- ADR-012 becomes partially superseded if this proposal is accepted.

### Neutral / follow-up

- Decide whether `skill_name` remains in invocation input.
- Decide whether to add a formal JSON Schema and runtime hook type checks.
- Keep operational overrides and Cadence-history configuration snapshots out of the initial refactor.

## Alternatives considered

- **Class dictionary configuration** — rejected in favor of adjacent JSON so runtime settings remain data rather than implementation code.
- **Typed object only** — rejected because adjacent JSON was selected as the source of Activity configuration.
- **Ignore all unknown keys** — rejected because misspellings inside the active Harness namespace should fail.
- **Blind dictionary-to-CLI conversion** — rejected because it bypasses validation and creates security and compatibility risks.

## Detailed design

See [Skill Activity Template Method and Colocated Configuration Refactor](../../docs/reqs/skill-activity-configs/refactor/skill-activity-template-method.design.md).
