# Refactor Workflow Modules: Proposed Architecture

## Bottom line

Refactor the current implementation into three layers: `common` provides workflow-agnostic interfaces and execution infrastructure, each workflow package owns its complete business workflow, and `orchestrator` is the composition root that loads configured workflow modules and runs one Cadence Worker per task list.

The orchestrator may import supported workflow modules because composition is its responsibility. `common` must never import a workflow package, and workflow packages must not import one another.

## Status

**Status:** Proposed  
**Date:** 2026-09-03  
**Scope:** Architecture and migration proposal; no implementation is included.

## Goals

- Separate reusable orchestration infrastructure from Story Analysis behavior.
- Make `story_analysis_workflow` the owner of the complete Story Analysis workflow definition.
- Add another workflow without placing its behavior in `orchestrator` or changing Story Analysis code.
- Make `orchestrator` the explicit catalog and composition root for supported workflows.
- Load configured Python workflow-module paths and validate them at startup.
- Run a separate Cadence Worker for each configured task list.
- Preserve a top-level single-Activity diagnostic capability, subject to a routing design decision.
- Move generic harness, skill invocation, and logging infrastructure into `common`.

## Non-goals

- Generalizing skill output fallback and artifact resolution. That work is deferred to a separate refactor.
- Designing workflow-to-workflow result chaining.
- Preserving existing Cadence event history or wire compatibility during this development-stage refactor.
- Automatically discovering workflow packages by scanning the repository.
- Refactoring the internal behavior of Story Analysis beyond what is needed to establish module boundaries.

## Current problem

The current `orchestrator` package combines three responsibilities:

1. generic Cadence and Devin execution infrastructure;
2. Story Analysis workflow behavior;
3. application composition and Worker startup.

Examples of this coupling include:

- `orchestrator.workflow` defines `StoryAnalysisWorkflow`, imports all Story Analysis Activities, and owns their Cadence registry;
- `orchestrator.story_analysis_engine`, `escalation`, `grade_repair`, and `grade_scoring` contain Story Analysis domain logic;
- `orchestrator.worker` imports the Story Analysis registry and polls one task list;
- `orchestrator.activities` contains the entire Story Analysis Activity implementation folder;
- `orchestrator.single_activity_workflow` imports the Story Analysis registry and Activity policy;
- `orchestrator.skill_activity` contains Story Analysis-specific output-path fallback rules.

This makes the current package a Story Analysis application named as a generic orchestrator. Adding another workflow would expand the same registry and package until workflow ownership and operational boundaries became unclear.

## Target architecture

```text
                         configuration
                              |
                              v
+-----------------------------------------------------------+
| orchestrator                                              |
|                                                           |
| supported workflow catalog                               |
| configured module-path loader                            |
| registry composition                                     |
| one Worker lifecycle per task list                       |
| process startup/shutdown and health                      |
| top-level single-Activity diagnostic workflow            |
+--------------------------+--------------------------------+
                           |
                  imports module contracts
                           |
          +----------------+----------------+
          |                                 |
          v                                 v
+---------------------------+     +---------------------------+
| story_analysis_workflow   |     | story_design_workflow     |
|                           |     |                           |
| module descriptor         |     | module descriptor         |
| workflow definition       |     | workflow definition       |
| pure engine               |     | pure engine               |
| complete activities/      |     | complete activities/      |
| contracts                 |     | contracts                 |
| config and starter        |     | config and starter        |
| domain tests              |     | domain tests              |
+-------------+-------------+     +-------------+-------------+
              |                                 |
              +----------------+----------------+
                               |
                               v
+-----------------------------------------------------------+
| common                                                    |
|                                                           |
| workflow-module and Worker-spec interfaces               |
| Harness and DevinHarness                                  |
| invocation context                                       |
| generic skill Activity execution                         |
| generic logging contexts                                 |
| shared Activity/runtime utilities                        |
+-----------------------------------------------------------+
```

## Dependency rules

The architecture is enforced through directional dependencies.

```text
common <- workflow modules <- orchestrator
   ^                              |
   +------------------------------+
```

More precisely:

| Package | May import | Must not import |
|---|---|---|
| `common` | Python/Cadence libraries and other `common` modules | `orchestrator` or any workflow package |
| Workflow package | `common` and its own modules | `orchestrator` or another workflow package |
| `orchestrator` | `common` and configured workflow modules | workflow-internal implementation details beyond the module contract |

The orchestrator is intentionally allowed to import workflow module entry points. That is application composition, not unwanted business coupling. It must not contain Story Analysis skill names, artifact conventions, grading rules, or Activity implementations.

A workflow package must expose a small public module contract so the orchestrator never needs to inspect its internal files.

## Package responsibilities

### `common`

`common` owns reusable mechanisms and interfaces. Proposed contents:

```text
src/common/
├── __init__.py
├── workflow_module.py
├── worker_spec.py
├── activity_policy.py
├── harness.py
├── devin_harness.py
├── devin_harness.config.json
├── invocation_context.py
├── skill_activity.py
├── workflow_logger.py
├── activity_runtime.py
└── tests/
```

Responsibilities:

- define the workflow-module registration interface;
- define immutable module and Worker specifications;
- provide the `Harness` protocol and result type;
- implement the host Devin CLI harness;
- resolve per-skill invocation profiles;
- hold invocation-scoped canonical skill context;
- provide generic skill Activity invocation;
- provide workflow, Activity, Worker, client, and Devin logging contexts;
- provide shared Activity/runtime utilities and policy builders where behavior is truly generic.

The generic Worker lifecycle is intentionally not assigned permanently yet. Its reusable mechanics may live in `common`, but the orchestrator must remain responsible for deciding which Workers exist and managing their lifecycle. A practical split is:

- `common` supplies a `create_worker` or `run_worker` mechanism;
- `orchestrator` supplies validated `WorkerSpec` values and owns startup, shutdown, supervision, and health reporting.

### `orchestrator`

`orchestrator` is the executable composition root. Proposed contents:

```text
src/orchestrator/
├── __init__.py
├── config.py
├── workflow_catalog.json
├── module_loader.py
├── registry.py
├── worker.py
├── worker_runtime.py
├── single_activity_workflow.py
├── cli.py
└── tests/
```

Responsibilities:

- define which workflow modules the deployment supports;
- read configured Python module paths;
- import and validate each module entry point;
- group module registrations by domain and task list;
- create one Cadence registry per Worker/task-list boundary;
- register the workflows and Activities supplied by each module;
- create and supervise one Worker per configured task list;
- register the top-level diagnostic workflow where appropriate;
- expose process-level lifecycle, logs, health, and startup failures;
- provide the top-level command used by scripts.

The orchestrator does not decide the task list hidden inside workflow code. Each workflow module declares its required domain and task list through its public descriptor. The orchestrator reads those declarations, checks for conflicts, and mounts them.

### Workflow packages

Each workflow package is a cohesive business capability. For Story Analysis:

```text
src/story_analysis_workflow/
├── __init__.py
├── module.py
├── workflow.py
├── engine.py
├── contracts.py
├── escalation.py
├── grade_repair.py
├── grade_scoring.py
├── activities/
│   ├── __init__.py
│   ├── harness_instance.py        # refactor before deciding final ownership
│   ├── extract_story_intent.py
│   ├── analyze_story.py
│   ├── grade_story_analysis.py
│   └── repair_story_analysis.py
├── config.py
├── domain-task-list-retry-config.json
├── starter.py
├── signals.py
├── queries.py
├── cli.py
├── run_single_activity.py
└── tests/
```

The package owns:

- its Cadence workflow type and run method;
- its Signals and Queries;
- its pure sequencing and decision engine;
- its input, result, status, Signal, Query, and wire-name contracts;
- its complete `activities/` folder and all Activity behavior;
- its domain-specific retry, escalation, grading, and repair behavior;
- its client configuration, starter, CLI, and tests;
- its module descriptor used by the orchestrator.

The Activity migration is not a simple file move. The full contents of `orchestrator/activities/` must undergo a boundary refactor and then move into `story_analysis_workflow/activities/`. Activity imports of harness/runtime infrastructure must be redirected to `common`, while Story Analysis scoring and artifact behavior stays in the workflow package.

## Workflow module contract

Each workflow package exposes one configured Python module path, such as:

```text
story_analysis_workflow.module
story_design_workflow.module
```

That module exports a stable descriptor. A proposed interface is:

```python
from dataclasses import dataclass
from typing import Callable

from cadence import Registry


@dataclass(frozen=True)
class WorkflowModuleSpec:
    name: str
    domain: str
    task_list: str
    workflow_types: tuple[str, ...]
    activity_types: tuple[str, ...]
    register: Callable[[Registry], None]
```

A workflow module constructs its descriptor:

```python
SPEC = WorkflowModuleSpec(
    name="story-analysis",
    domain="story-analysis",
    task_list="story-analysis",
    workflow_types=("StoryAnalysisWorkflow",),
    activity_types=(
        "extract_story_intent",
        "analyze_story",
        "grade_story_analysis",
        "repair_story_analysis",
    ),
    register=register,
)
```

The exact shape should be finalized with tests, but it must let the orchestrator:

- identify the module without inspecting implementation files;
- determine its domain and task list;
- report registered workflow and Activity names;
- register implementations into an orchestrator-owned `Registry`;
- detect duplicate or conflicting registrations before Worker startup.

The module descriptor is static process-start configuration. Workflow replay code must not read or dynamically reload this configuration.

## Configured Python module paths

The orchestrator owns a catalog of supported workflow module paths. A proposed configuration is:

```json
{
  "workflow_modules": [
    "story_analysis_workflow.module",
    "story_design_workflow.module"
  ]
}
```

The orchestrator uses `importlib.import_module` during startup and requires every configured module to expose `SPEC` matching the common contract.

Startup validation must reject:

- a missing or unimportable module;
- a module without `SPEC`;
- a descriptor with empty name, domain, or task list;
- duplicate module names;
- duplicate workflow or Activity wire names within a Worker registry;
- incompatible modules assigned to the same task-list boundary;
- two Worker specifications that unintentionally claim the same domain/task-list pair.

Unknown or invalid modules must fail startup rather than silently reducing the supported workflow catalog.

### Initial implementation path

Configured module paths are close to explicit deployment composition. Implement the boundary in two increments:

1. build and test registry composition using an explicit list of `WorkflowModuleSpec` instances;
2. add the configuration and module loader that resolves Python paths into the same list.

This keeps dynamic importing separate from Cadence registration logic and gives both parts small, deterministic tests.

## Registry composition

The orchestrator owns registry instances. Workflow modules contribute registrations through their public `register` callable.

Conceptually:

```python
def build_registry(modules: tuple[WorkflowModuleSpec, ...]) -> Registry:
    registry = Registry()
    for module in modules:
        module.register(registry)
    return registry
```

The workflow package should not export a process-global registry consumed directly by the Worker. Instead, its registration function applies the workflow and Activity implementations to the supplied registry.

The existing decorator behavior must be verified against the installed Cadence Python SDK. If a workflow class can be registered after definition, the Story Analysis module can use:

```python
def register(registry: Registry) -> None:
    registry.workflow(name=WORKFLOW_TYPE)(StoryAnalysisWorkflow)
    registry.register_activity(extract_story_intent)
    registry.register_activity(analyze_story)
    registry.register_activity(grade_story_analysis)
    registry.register_activity(repair_story_analysis)
```

If the SDK requires registry-bound decoration at class definition time, the package may expose a `build_registry_contribution` factory or a registration factory that defines the bound class. Do not select that more complex pattern until an executable SDK characterization test demonstrates it is necessary.

## Worker and task-list topology

The deployment uses a shared orchestrator process conceptually, but a separate Cadence Worker for every domain/task-list pair.

```text
orchestrator process
    |
    +-- Worker(domain=story-analysis, task_list=story-analysis)
    |       +-- StoryAnalysisWorkflow
    |       +-- Story Analysis Activities
    |
    +-- Worker(domain=story-design, task_list=story-design)
            +-- StoryDesignWorkflow
            +-- Story Design Activities
```

A Cadence Worker polls one task list through a client connected to one domain. The orchestrator therefore groups loaded module specs by `(domain, task_list)` and creates a registry and Worker lifecycle for each group.

A proposed internal type is:

```python
@dataclass(frozen=True)
class WorkerSpec:
    domain: str
    task_list: str
    cadence_target: str
    modules: tuple[WorkflowModuleSpec, ...]
```

The orchestrator is responsible for knowing the supported modules. Each module is responsible for declaring where its work is routed. This separation prevents a central catalog from duplicating task-list details while retaining one place that controls what the deployment mounts.

### Worker lifecycle ownership

The orchestrator owns:

- creating one Cadence client per domain or Worker boundary as supported by the SDK;
- creating every Worker with its composed registry;
- entering all Worker contexts;
- reporting startup only after all Workers are polling;
- cancelling and closing all Workers on shutdown;
- surfacing a failed Worker instead of leaving a partially healthy process unreported.

Reusable lifecycle helpers may live in `common`, but they receive specifications from the orchestrator and must not load workflow modules themselves.

## Story Analysis move and refactor matrix

| Current path | Target path | Required work |
|---|---|---|
| `orchestrator/workflow.py` | `story_analysis_workflow/workflow.py` | Remove registry ownership; import Story Analysis contracts/domain code locally and generic logging from `common`. |
| `orchestrator/story_analysis_engine.py` | `story_analysis_workflow/engine.py` | Update local domain imports; preserve pure async callable injection. |
| `orchestrator/escalation.py` | `story_analysis_workflow/escalation.py` | Move domain types and parser; update `signals.py` imports. |
| `orchestrator/grade_repair.py` | `story_analysis_workflow/grade_repair.py` | Move decision logic and tests. |
| `orchestrator/grade_scoring.py` | `story_analysis_workflow/grade_scoring.py` | Move scoring logic and update grading Activity. |
| `orchestrator/activities/` | `story_analysis_workflow/activities/` | Refactor and move the entire folder, not only Activity `.py` entry points. |
| `orchestrator/harness.py` | `common/harness.py` | Move generic protocol and result. |
| `orchestrator/devin_harness.py` | `common/devin_harness.py` | Move generic implementation and update configuration path. |
| `orchestrator/devin_harness.config.json` | `common/devin_harness.config.json` | Move with its reader; preserve profile behavior. |
| `orchestrator/invocation_context.py` | `common/invocation_context.py` | Move generic invocation context. |
| `orchestrator/skill_activity.py` | `common/skill_activity.py` | Move generic runner; leave generalized output resolution deferred and explicitly tracked. |
| `orchestrator/workflow_logger.py` | `common/workflow_logger.py` | Move logging contexts and generalize logger naming. |
| `orchestrator/single_activity_workflow.py` | remains in `orchestrator` | Remove dependencies on Story Analysis registry/policy and resolve cross-task-list routing. |
| `orchestrator/worker.py` | remains/rebuilt in `orchestrator` | Replace the single Story Analysis registry with module loading, grouping, registry composition, and multi-Worker lifecycle. |
| Story Analysis domain tests under `orchestrator/tests/` | `story_analysis_workflow/tests/` | Move and update imports according to ownership. |
| Generic harness/logger tests | `common/tests/` | Move with generic infrastructure. |

## Story Analysis contracts

Add `story_analysis_workflow/contracts.py` as the package-level public contract surface. It should own:

- workflow wire type names;
- Activity wire names;
- Signal and Query names;
- workflow input and result structures;
- status structures;
- Story Analysis-specific configuration structures where appropriate.

The workflow implementation, module descriptor, starter, Signals, Queries, CLI, and tests import these values from the Story Analysis package. The orchestrator does not import individual Story Analysis constants; it sees the names exposed through `WorkflowModuleSpec` for diagnostics and conflict validation.

## Story Analysis Activity-folder refactor

The entire current Activity folder belongs to Story Analysis, but its contents cross the proposed boundary and must be untangled before or during the move.

Required changes include:

- replace imports of `orchestrator.skill_activity` with `common.skill_activity`;
- replace imports of `orchestrator.devin_harness` and `orchestrator.harness` with `common` equivalents;
- keep grading/scoring imports inside `story_analysis_workflow`;
- decide whether `harness_instance.py` remains a workflow-local adapter or becomes a generic `common.activity_runtime` provider;
- update Activity wire-name constants to come from Story Analysis contracts;
- move Activity tests with the package and retain fake-Harness injection;
- ensure the folder exports a single registration function or explicit Activity tuple for `module.py`.

Generalized skill output-path resolution is not part of this proposal. The current Story Analysis-specific fallback may temporarily move with the Story Analysis adapter or remain as acknowledged technical debt in `common`; a separate requirement must decide its final design before additional skill catalogs rely on it.

## Single-Activity diagnostic workflow

`SingleActivityWorkflow` remains an orchestrator concern because it is a top-level operational probe rather than Story Analysis business behavior.

Its current implementation depends on the Story Analysis registry and retry constants. That dependency must be removed. The unresolved issue is task-list routing: an Activity is executed only by a Worker polling the task list to which Cadence schedules it.

Possible designs to evaluate in implementation planning:

1. **Register the diagnostic workflow in every Worker registry.** Start it on the target workflow module's task list, so its Activity executes on the same Worker. This is simple but repeats the diagnostic workflow registration across task lists.
2. **Use a dedicated diagnostic workflow task list and allow it to schedule Activities onto a selected target task list.** This requires confirming that the installed Python SDK exposes per-Activity task-list routing with the needed semantics.
3. **Generate a module-specific probe registration.** The orchestrator mounts the generic probe class plus the module's known Activity names into each Worker.

The first option is the safest initial direction. The orchestrator already knows every `WorkerSpec`, and the client can select the target module/task list. The final choice requires a live Cadence characterization test.

Until this is resolved, treat `SingleActivityWorkflow` migration as a watch-out rather than assuming it will work unchanged after registry separation.

## Logging changes

Move generic logging implementation into `common`, then remove the Story Analysis-specific logger namespace.

Required behavior:

- context paths remain scoped by WorkflowID, RunID, and ActivityID;
- Worker logs identify domain and task list;
- workflow logs accept a component/module name, such as `story-analysis`;
- Activity logs identify both Cadence Activity wire name and canonical skill name where available;
- the orchestrator can distinguish concurrent Worker lifecycle events;
- no logger in `common` assumes `orchestrator.workflow` is the workflow implementation module.

Workflow modules use the common logging API but supply their own component identity.

## Script and process changes

The existing workflow-engine startup assumes one Story Analysis Worker. Replace that assumption with orchestrator-owned multi-Worker startup.

The start path becomes:

```text
start-workflow-engine.sh
    |
    +-- start Cadence server and Web UI
    +-- register/verify configured domains
    +-- start python -m orchestrator.worker
    |       +-- read workflow_catalog.json
    |       +-- load configured Python modules
    |       +-- compose WorkerSpecs
    |       +-- start one Worker per task list
    +-- wait until every configured Worker reports polling
```

Required script changes:

- derive expected domain/task-list pairs from orchestrator configuration or a machine-readable status command;
- register every configured domain idempotently;
- start one orchestrator process that supervises all Workers, or one generic Worker subprocess per `WorkerSpec` if process isolation is chosen later;
- wait for all task-list pollers rather than only `story-analysis`;
- write process identifiers and logs for reliable shutdown;
- fail startup if any configured module, domain, or Worker fails;
- update the stop script to stop all Worker processes/contexts;
- keep workflow-specific kickoff scripts as clients of their workflow package starters;
- add new kickoff wrappers for new workflows without embedding their behavior in the orchestrator.

The current decision is one Cadence Worker per task list. Whether those Workers share one Python process or use one subprocess per task list is an operational follow-up. The architecture supports either because `WorkerSpec` is the unit of composition.

## Testing strategy

### `common` tests

- `WorkflowModuleSpec` and `WorkerSpec` validation;
- Harness protocol and DevinHarness configuration;
- invocation context isolation;
- generic skill Activity execution;
- generic logging contexts and component names;
- shared Activity policy helpers.

### Workflow-module tests

Story Analysis owns tests for:

- engine sequencing and state transitions;
- escalation parsing and decisions;
- grade/repair decisions and scoring;
- every Activity adapter;
- workflow contracts;
- registration contribution contents;
- starter, CLI, Signals, and Queries.

A second workflow owns an equivalent independent suite and must not import Story Analysis fixtures or implementation modules.

### Orchestrator tests

- valid configured Python module loading;
- clear failures for missing or invalid modules;
- grouping modules by `(domain, task_list)`;
- one registry per WorkerSpec;
- registration conflict detection;
- one Worker lifecycle per task list;
- partial startup failure cleanup;
- graceful shutdown across all Workers;
- domain/task-list health reporting;
- diagnostic workflow registration and target routing.

### Integration verification

- start local Cadence with at least Story Analysis and a minimal second workflow configured;
- confirm separate pollers for each task list;
- run both workflows independently;
- run representative skill Activities through their owning task lists;
- verify the single-Activity diagnostic path against each module;
- stop and restart the orchestrator and confirm all Workers return;
- verify a malformed module path fails startup visibly.

Existing Cadence history may be cleared during this development refactor. Wire compatibility is not an acceptance requirement.

## Migration stages

### Stage 1: establish `common`

1. Create the `common` package.
2. Move Harness, DevinHarness, invocation context, skill Activity infrastructure, and logging.
3. Move associated configuration and generic tests.
4. Update imports while retaining existing runtime behavior.
5. Add dependency tests or static checks proving `common` imports no workflow package or orchestrator module.

### Stage 2: establish module and Worker contracts

1. Define and test `WorkflowModuleSpec` and `WorkerSpec` in `common`.
2. Add orchestrator registry composition using explicit spec objects.
3. Add Story Analysis `module.py` implementing the contract.
4. Characterize dynamic workflow registration against the installed Cadence SDK.
5. Rebuild `orchestrator.worker` around composed WorkerSpecs.

### Stage 3: move Story Analysis ownership

1. Add Story Analysis contracts.
2. Move the workflow definition and pure engine.
3. Move escalation, grade/repair, and scoring modules.
4. Refactor and move the complete Activity folder.
5. Move Story Analysis domain tests.
6. Update clients, scripts, docs, and imports.
7. Remove Story Analysis behavior and conventions from `orchestrator`.

### Stage 4: configured workflow catalog

1. Add the orchestrator workflow catalog file.
2. Implement Python module-path loading and validation.
3. Group modules into one Worker per domain/task-list pair.
4. Add multi-Worker lifecycle and health reporting.
5. Update start and stop scripts for all configured Workers.

### Stage 5: restore top-level diagnostics

1. Decouple `SingleActivityWorkflow` from the old Story Analysis registry.
2. Select and test a target-task-list routing model.
3. Expose configured task lists through the diagnostic client.
4. Verify a representative Activity from every mounted module.

### Stage 6: prove extensibility

1. Add a minimal second workflow module.
2. Add its configured Python module path to the orchestrator catalog.
3. Start its independent Worker/task-list poller.
4. Run both workflows without changing Story Analysis implementation code.
5. Confirm only orchestrator composition/configuration changes were required to mount it.

## Risks and follow-ups

| Risk or open question | Treatment |
|---|---|
| Cadence workflow classes may require registry-bound definition | Write a characterization test before choosing the registration implementation. |
| Multiple Workers in one process may complicate failure isolation | Make `WorkerSpec` process-neutral; decide supervision model separately. |
| Single-Activity probe may schedule onto the wrong task list | Keep as an explicit design watch-out and test routing live. |
| Current skill output fallback contains Story Analysis knowledge | Defer to the separately requested Activity/output-resolution refactor. |
| Moving logging changes file paths or logger names | Preserve context behavior and test component-aware naming. |
| Dynamic imports can fail only at runtime | Validate the complete catalog before starting any Worker. |
| Modules sharing a task list may conflict on wire names | Detect duplicates before registry/Worker startup. |
| Configuration may duplicate workflow package settings | Module declares routing; orchestrator catalog declares supported module paths only. |

## Definition of done

The refactor is complete when:

- `common` contains generic interfaces and infrastructure and imports no workflow package or `orchestrator` module;
- each workflow package imports generic capabilities from `common` and never imports another workflow package;
- `story_analysis_workflow` owns its workflow definition, engine, contracts, complete Activity folder, domain logic, clients, configuration, and tests;
- `orchestrator` imports `common` and configured workflow module entry points as the application composition root;
- `orchestrator` contains no Story Analysis skill names, grading rules, artifact conventions, Activity implementations, or result details;
- the orchestrator loads supported workflow modules from configured Python module paths;
- each workflow module declares its domain, task list, workflow names, Activity names, and registration callable;
- the orchestrator validates registrations and creates one Cadence Worker per domain/task-list pair;
- the start script registers all configured domains and waits for every configured Worker to poll;
- the stop path shuts down every Worker cleanly;
- generic logging identifies workflow modules and task-list-specific Workers without assuming a Story Analysis module name;
- the single-Activity diagnostic workflow remains top-level and can target Activities on each mounted task list, or its unresolved routing behavior is captured in an approved follow-up before the old path is removed;
- a second workflow is mounted by adding its package and orchestrator catalog entry, without changing Story Analysis code;
- all common, workflow-module, orchestrator, and live Cadence integration tests pass;
- stale Story Analysis implementations and imports are removed from `orchestrator` after migration.

## Source areas affected

- `src/orchestrator/`
- `src/story_analysis_workflow/`
- new `src/common/`
- future workflow packages such as `src/story_design_workflow/`
- `scripts/start-workflow-engine.sh`
- `scripts/stop-workflow-engine.sh`
- workflow-specific kickoff and diagnostic scripts
- `tests/unit/test_workflow_state.py`
- workflow orchestration documentation and vault decisions
