# ADR-013: Three-Layer Workflow Module Architecture

**Status:** Accepted
**Date:** 2026-09-03
**Author:** Project team

## Bottom line

Separate orchestration into `common` infrastructure, independently owned workflow packages, and an `orchestrator` composition root that loads configured module paths and runs one Cadence Worker per task list.

## Context

The current `orchestrator` package mixes generic Cadence/Devin infrastructure, Story Analysis behavior, and Worker startup. This prevents clear ownership and makes adding another workflow expand the Story Analysis-oriented registry and package.

## Decision

- Create `common` for workflow-agnostic interfaces, Harness/DevinHarness, invocation context, generic skill Activity execution, logging, and reusable runtime helpers.
- `common` imports no workflow package or `orchestrator` module.
- Each workflow package owns its workflow definition, engine, contracts, complete Activity folder, domain logic, client configuration, starter, CLI, and tests.
- Workflow packages import `common` but not `orchestrator` or other workflow packages.
- `orchestrator` is the application composition root and may import `common` and workflow module entry points.
- The orchestrator reads configured Python module paths, validates their descriptors, composes registries, and creates one Cadence Worker per domain/task-list pair.
- Workflow modules declare their own domain, task list, workflow names, Activity names, and registration callable.
- Keep `SingleActivityWorkflow` as a top-level orchestrator concern; decide and live-test its cross-task-list routing during implementation.
- Refactor and move the entire current `orchestrator/activities/` folder into `story_analysis_workflow/activities/`.
- Defer generalized skill output resolution to a separate requirement.
- Existing Cadence history and wire compatibility do not constrain this development-stage refactor.

## Consequences

### Positive

- Generic infrastructure has an enforceable dependency boundary.
- Workflow ownership is cohesive and new workflows do not modify Story Analysis code.
- The supported workflow catalog remains explicit and centrally operated.
- Separate task-list Workers support independent routing, scaling, and diagnostics.

### Negative

- Dynamic module paths introduce startup-time import and validation failures.
- Multi-Worker lifecycle and health handling become orchestrator responsibilities.
- Existing files, imports, tests, scripts, and logging namespaces require broad migration.

### Neutral / Follow-up

- Characterize dynamic workflow registration against the installed Cadence Python SDK.
- Decide whether Worker instances share one process or use one subprocess per task list.
- Resolve the single-Activity diagnostic workflow's target-task-list routing.
- Address skill output fallback in a separate refactor.

## Alternatives Considered

- **Keep generic infrastructure in `orchestrator`** — rejected because runtime mechanisms and application composition would remain blended.
- **Make workflow packages invisible to the orchestrator through automatic discovery** — rejected because implicit package scanning is harder to validate and operate.
- **Use only explicit imports in deployment code** — retained as the first implementation increment, then extended with configured Python module paths.
- **One Worker/task list for every workflow** — rejected in favor of a separate Worker for each declared task-list boundary.

## Detailed proposal

See [Refactor Workflow Modules: Proposed Architecture](../../docs/reqs/refactor-workflow-modules/proposed-architecture.md).

## Design refinement (2026-09-04)

The implementation design resolves the open topology choices for the first increment:

- Run all task-list-specific Workers in one host Python process and manage Client/Worker contexts transactionally with `AsyncExitStack`.
- Register the generic single-Activity diagnostic workflow in every Worker registry and start it on the selected target task list.
- Use a versioned orchestrator-owned catalog containing module paths only; module descriptors remain the source of domain and task-list data.
- Treat an empty valid catalog as a warned, successful no-op exit.
- Register workflow classes after definition through `registry.workflow(name=...)(WorkflowClass)`; local inspection confirms `cadence-python-client` 0.3.0 supports direct registration, and an executable characterization test must preserve this assumption.
- Keep Story Analysis artifact fallback behavior in concrete Story Analysis Activities while generalized resolution remains deferred.
- Use static architecture tests for package dependency rules and runtime validation for module descriptors and registry conflicts.

## Implementation status (2026-09-04)

- `src/common` now exposes frozen, intrinsically validated `WorkflowModuleSpec` and `WorkerSpec` contracts.
- Generic Harness, invocation context, colocated Activity configuration, Devin Harness, SkillActivity lifecycle, and route-aware worker logging have common-layer APIs.
- An AST-based test enforces that `common` does not import `orchestrator` or workflow packages.
- `scripts/run_unit_tests.sh` includes the common suite.
- Existing orchestrator implementations remain during the staged migration; later workstreams must redirect consumers before removing them.

## Story Analysis module migration status (2026-09-04)

- `story_analysis_workflow` owns its workflow, pure engine, escalation, grading, Activities, adjacent Activity configuration, clients, and tests.
- `story_analysis_workflow.module` exports an immutable `SPEC` and direct `register(registry)` callback declaring the existing workflow and Activity wire names.
- Static verification rejects imports from `story_analysis_workflow` into `orchestrator` or another workflow package.
- Stale Story Analysis workflow, engine, grading, escalation, and Activity implementations are removed from `orchestrator`.
- The NixOS unit entry point passes 163 tests after migration.
