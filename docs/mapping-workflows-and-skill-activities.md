# Mapping Cadence Workflows and Devin Skill Activities

## Bottom line

Use the Story Analysis implementation as a pattern, not as a base class. Keep each business workflow in its own package, put decision logic in a Cadence-independent engine, expose stable input/result contracts, and compose workflow registries in the worker.

To chain independent workflows, use either a separate durable coordinator workflow or an external coordinator. Do not make one business workflow import or start the next business workflow directly.

## Scope

This guide explains:

1. How the Story Analysis workflow is mapped into Cadence.
2. How Devin skills are exposed as Cadence Activities.
3. What must change to add another workflow and its skill Activities.
4. How to pass one workflow result to another without coupling the workflows.

## Current Story Analysis architecture

```text
kickoff script / Python client
        |
        | start_workflow("StoryAnalysisWorkflow", story_document, config)
        v
Cadence domain: story-analysis
        |
        | task list: story-analysis
        v
orchestrator.worker
        |
        | Registry
        +-- StoryAnalysisWorkflow
        +-- SingleActivityWorkflow
        +-- extract_story_intent Activity
        +-- analyze_story Activity
        +-- grade_story_analysis Activity
        +-- repair_story_analysis Activity
                |
                v
        skill_activity.run_skill
                |
                v
        Harness protocol -> DevinHarness
                |
                | devin -p --permission-mode ... --model ...
                v
        .devin/skills/<skill>/SKILL.md
                |
                +-- output artifact
                +-- .process/<skill>.done.json
```

### End-to-end execution path

1. `story_analysis_workflow.starter` selects the workflow type, builds a WorkflowID, loads client configuration, and calls `client.start_workflow`.
2. Cadence records the execution in the configured domain and routes decision tasks to the configured task list.
3. `orchestrator.worker` connects to the domain, installs a `Registry`, and polls the task list.
4. `StoryAnalysisWorkflow` is the replay-safe Cadence adapter. It delegates sequencing and decisions to `StoryAnalysisEngine`.
5. `StoryAnalysisEngine` invokes injected callables for extraction, analysis, grading, repair, and human-response waiting.
6. The workflow adapter maps those calls to named Cadence Activities using `execute_activity`.
7. Each Activity maps its Cadence wire name to a canonical Devin skill name and calls `run_skill` in a thread.
8. `run_skill` builds the prompt, invokes the configured `Harness`, and resolves the output artifact from the sentinel or the known naming convention.
9. `DevinHarness` resolves a per-skill model and permission mode, then runs the host `devin` CLI non-interactively.
10. Activity results flow back through Cadence history. The engine passes each returned artifact path to the next Activity.
11. The workflow returns a serializable result dictionary to Cadence.

## Elements that define a workflow

| Element | Story Analysis implementation | Responsibility |
|---|---|---|
| Workflow wire type | `StoryAnalysisWorkflow` | Stable name used by clients and Cadence history. |
| Input contract | `story_document`, optional config dictionary | Serializable arguments recorded in workflow history. |
| Result contract | `WorkflowResult` converted to a dictionary | Stable completion value for clients or downstream workflows. |
| Pure engine | `StoryAnalysisEngine` | Sequencing, branching, bounded loops, and state transitions. |
| Cadence adapter | `orchestrator.workflow.StoryAnalysisWorkflow` | Converts engine ports into Activities, timers, Signals, and Queries. |
| Activity names | `extract_story_intent`, `analyze_story`, and others | Stable Cadence wire names. |
| Registry | `orchestrator.workflow.registry` | Registers workflow and Activity implementations with a Worker. |
| Worker | `orchestrator.worker` | Connects to Cadence and polls a task list with the registry. |
| Domain | `story-analysis` | Cadence isolation boundary selected when constructing the client. |
| Task list | `story-analysis` | Queue that routes workflow and Activity tasks to compatible Workers. |
| Starter/client | `story_analysis_workflow.starter` | Starts a run with the correct type, arguments, ID, and options. |
| Runtime config | `domain-task-list-retry-config.json` | Client-side domain, task list, target, and workflow timeout defaults. |
| Operations | scripts and CLI | Starts the server/worker and initiates, queries, or signals executions. |

### Determinism boundary

Workflow code is replayed and must remain deterministic. It may coordinate Activities, child workflows, Signals, Queries, and Cadence timers, but it must not directly:

- read or write files;
- invoke Devin or another subprocess;
- call network services;
- use wall-clock time, random values, or generated UUIDs;
- depend on unordered process-local state.

Put those operations in Activities. The existing split between `StoryAnalysisEngine` and `StoryAnalysisWorkflow` also makes the decision logic testable without a live Cadence server.

### Current implementation constraints

The current implementation is a working example but is not yet a generic multi-workflow framework:

- `orchestrator.workflow` creates one registry and imports the four Story Analysis Activities directly.
- `orchestrator.worker` imports that registry and polls one environment-selected task list.
- Activity retry and timeout settings are hardcoded in `orchestrator.workflow`; the `activity_defaults` section of the colocated JSON is not consumed by that workflow adapter.
- `skill_activity._conventional_output_path` recognizes only the four Story Analysis skills. A successful new skill whose sentinel was consumed by a hook cannot use the fallback until this mapping is generalized.
- The generic `Harness` boundary is reusable; the workflow and registration boundaries need extraction before multiple workflows can be added cleanly.
- `cadence-python-client` 0.3.0 has no released in-memory `TestWorkflowEnvironment`, workflow versioning primitive, side-effect primitive, or replay tooling.

Treat these as explicit extension points rather than copying more imports into the existing workflow module.

## Elements that define a skill Activity

A skill Activity has two names with different conventions:

| Name | Example | Used by |
|---|---|---|
| Cadence Activity wire name | `analyze_story` | `execute_activity`, registry, Cadence history. |
| Canonical Devin skill name | `analyze-story` | Prompt invocation, `.devin/skills`, sentinel name, profile config. |

The Activity adapter is responsible for translating between them.

### Skill-side contract

Each skill should provide:

- `.devin/skills/<canonical-name>/SKILL.md`;
- a clear input document/path contract;
- its own output schema;
- a deterministic output naming convention;
- `.process/<canonical-name>.done.json` containing `task` and `verify_params`;
- a `verify.sh` script that validates the produced artifact.

Skills receive document paths and read the documents they need. They should not copy upstream output schemas into their own directories. This keeps skills reusable across workflow arrangements.

### Activity-side contract

Each Activity adapter should:

1. Use `@activity.defn(name="stable_wire_name")`.
2. Accept only Cadence-serializable arguments.
3. Build `SkillActivityInput` with the canonical skill name, input paths, and optional context.
4. Supply the sentinel's output key, such as `analysis_path`.
5. Run the blocking harness through `asyncio.to_thread`.
6. Return `dataclasses.asdict(SkillActivityOutput(...))`.
7. Be safe to retry. Artifact writes must be deterministic or otherwise idempotent.

`run_skill` removes a stale sentinel before invocation. This prevents a retried Activity from reporting an artifact produced by an earlier attempt. The artifact itself may still exist, so the skill must safely overwrite, validate, or reuse it.

### Devin invocation profile

`src/orchestrator/devin_harness.config.json` resolves configuration in this order for each field:

1. canonical skill override;
2. structured defaults;
3. legacy top-level defaults;
4. secure built-in defaults.

Keep the global permission mode at `auto`. An unattended skill that writes an artifact normally needs an explicit `accept-edits` override because `devin -p` cannot answer an interactive write confirmation. Broader modes should remain explicit exceptions.

The profile is loaded for the Worker lifetime. Restart the Worker after changing it.

## Mapping a new workflow into Cadence

### Recommended target layout

```text
src/
  orchestrator/
    worker.py
    registry.py                  # composes workflow-owned registries
    skill_activity.py
    devin_harness.py
  story_analysis_workflow/
    engine.py                    # eventual move from orchestrator
    workflow.py
    activities/
    contracts.py
    config.py
    starter.py
  <new_workflow>/
    engine.py
    workflow.py
    activities/
    contracts.py
    config.py
    domain-task-list-retry-config.json
    starter.py
```

This is a target direction, not the current layout. A migration can be incremental: add the new package first, then extract Story Analysis ownership separately.

### Implementation checklist

#### 1. Define stable contracts

Create serializable, versioned-by-convention contracts for:

- workflow input;
- workflow result;
- Signal payloads, if any;
- Query responses, if any;
- Activity inputs and results when plain positional arguments become ambiguous.

Prefer dictionaries or frozen dataclasses converted to dictionaries at the Cadence boundary. Include a contract identifier or schema version when independent deployments may evolve at different times.

Example result envelope:

```python
{
    "contract": "workflow-result/v1",
    "workflow": "design-story-implementation",
    "status": "succeeded",
    "artifacts": {
        "primary": "docs/ex2/admin_story.design.json",
        "design": "docs/ex2/admin_story.design.json"
    },
    "metadata": {
        "attempt_count": 1
    }
}
```

Downstream orchestration should depend on this envelope, not on a workflow class or engine implementation.

#### 2. Implement a pure engine

Put sequencing and business decisions in a class that does not import `cadence`. Inject callable ports for Activities, timers, and human/external responses. Unit test success, retry/repair branches, terminal failures, and escalation with async fakes.

#### 3. Implement a thin Cadence adapter

Create a new `Registry` owned by the workflow package. Register the workflow under an explicit stable name. Map engine ports to:

- `execute_activity` for side effects;
- `sleep` and `wait_condition` for durable waiting;
- `execute_child_workflow` only in a generic coordinator;
- parenthesized `@workflow.signal(name="...")` and `@workflow.query(name="...")` decorators.

Always use the parenthesized Signal and Query decorators. Bare decorators silently fail to register with the current Python SDK.

#### 4. Register Activities

Register every Activity implementation needed by the workflow's task list. Registration controls what a Worker can execute; starting a workflow does not upload code to Cadence.

#### 5. Compose registries in the Worker

Extract registration composition from the Story Analysis workflow module. The composition root may merge workflow-owned registrations into one Worker registry when they share a task list, or start separate Workers when isolation is desired.

Choose task lists intentionally:

- **Shared task list:** simpler local operation; all polling Workers need compatible registrations.
- **Per-workflow task list:** independent scaling, deployment, permissions, and failure isolation.
- **Dedicated Activity task list:** useful when Activities require a specific host or toolchain.

A domain is a broader logical boundary. New workflows do not require a new domain unless retention, ownership, security, or operational isolation requires one.

#### 6. Add colocated client configuration

Create `<workflow-package>/domain-task-list-retry-config.json` and a typed loader beside it. Keep runtime configuration out of `docs/`.

Ensure there is one source of truth for each setting. If Activity settings are present in JSON, either wire them into the workflow adapter or remove them from the advertised runtime configuration.

#### 7. Add a starter and operational entry point

The starter owns:

- the workflow wire type;
- WorkflowID policy;
- domain client selection;
- task-list and timeout options;
- serialization of workflow input.

Keep starter/client code outside the workflow implementation so callers do not import Worker internals.

#### 8. Verify the mapping

At minimum:

- unit-test the pure engine;
- unit-test Activity adapters with a fake Harness;
- unit-test configuration precedence and validation;
- unit-test the starter with a fake client;
- manually start the real Worker and run against local Cadence;
- inspect workflow and Activity history in the Web UI;
- exercise Signals and Queries against the live server;
- verify retries do not corrupt or misidentify artifacts.

Because the Python SDK lacks released replay/versioning tools, drain or isolate in-flight executions before deploying incompatible workflow code changes.

## Creating and configuring new skill Activities

### Checklist

1. Create or identify the canonical Devin skill.
2. Confirm its inputs can be supplied as repository-relative document paths.
3. Define its output schema, output filename, sentinel task name, and `verify_params` output key.
4. Ensure its verification hook behavior is understood: the hook may consume the sentinel.
5. Add a Cadence Activity adapter with an explicit wire name.
6. Add the Activity to its workflow-owned registry.
7. Add a per-skill Devin profile when the default model or permissions are insufficient.
8. Add fake-Harness unit tests for prompt construction, output resolution, harness failure, missing/malformed sentinel, and stale sentinel behavior.
9. Run the Activity through Cadence, not only as a direct Python call, to validate routing, timeout, retry, and logging behavior.

### Generalize output fallback before scaling

The current fallback is a conditional over four canonical skill names. Replace it with declarative metadata before relying on many new skills. For example, each Activity can supply an output resolver or an expected output path to `run_skill`.

Conceptual API:

```python
run_skill(
    skill_input,
    output_path_key="design_path",
    expected_output_path=derive_design_path(input_path),
    harness=HARNESS,
)
```

This keeps generic orchestration code unaware of the skill catalog and preserves the missing-sentinel recovery behavior.

Do not infer contracts by parsing prompts. Use explicit Activity arguments and invocation context.

## Chaining workflow results without coupling business workflows

### Principle

Business workflow A should return a stable result. Business workflow B should accept a stable input. Neither should import, name, start, or signal the other.

The component that owns the pipeline is the only component that knows the sequence.

### Option A: separate durable coordinator workflow

Use this when the pipeline itself must survive process failures, wait durably, retry child starts, expose one status, or apply Cadence parent/child policies.

```text
PipelineCoordinatorWorkflow
    |
    +-- configured child type: StoryAnalysisWorkflow
    |       returns workflow-result/v1
    |
    +-- adapter maps selected artifacts to next input
    |
    +-- configured child type: DesignStoryWorkflow
            returns workflow-result/v1
```

The coordinator receives a pipeline specification containing workflow type, task list, timeout, input mapping, and result mapping. It invokes children by wire name using `execute_child_workflow`. Business workflows remain unaware of each other.

Keep mapping deterministic. The pipeline specification must be supplied as workflow input so it is recorded in Cadence history; do not read a mutable configuration file from workflow code.

Advantages:

- durable end-to-end orchestration;
- child results are naturally recorded in history;
- cancellation and parent-close policy can be explicit;
- one WorkflowID can represent the whole pipeline.

Trade-offs:

- the coordinator owns compatibility with all contract versions;
- changing a pipeline definition for an in-flight run is constrained by replay determinism;
- child-workflow support must be tested against the installed Python SDK and live Cadence.

Use `PARENT_CLOSE_POLICY_TERMINATE` when children must not outlive the pipeline, `REQUEST_CANCEL` for cooperative cleanup, or `ABANDON` only when independent continuation is intentional.

### Option B: external coordinator

Use a client, service, script, or event consumer that waits for workflow A, validates its result envelope, maps it to workflow B's input, and starts workflow B through its public starter/client API.

```text
External coordinator
    +-- start workflow A
    +-- wait/query for completion
    +-- validate and map result envelope
    +-- start workflow B
```

Advantages:

- workflows and Workers can be deployed independently;
- pipeline definitions can change without replaying coordinator workflow code;
- simplest way to cross domains or organizational boundaries;
- avoids adding generic dynamic orchestration to workflow history.

Trade-offs:

- the coordinator must persist its own progress and idempotency keys if it needs crash recovery;
- polling, result retrieval, duplicate-start handling, and retries become application responsibilities;
- there is no automatic Cadence parent/child relationship.

A stateless shell script is acceptable only for development. Production chaining needs durable coordinator state or an idempotent event/message handoff.

### Choosing between them

| Requirement | Prefer |
|---|---|
| Durable chain with one observable execution | Cadence coordinator workflow |
| Independent workflow deployments | External coordinator |
| Dynamic pipeline definitions changed frequently | External coordinator |
| Long waits and automatic crash recovery | Cadence coordinator workflow |
| Cross-domain or cross-team boundary | External coordinator |
| Parent/child cancellation semantics | Cadence coordinator workflow |
| Minimal initial infrastructure | External coordinator, with explicit durability limits |

### Contract and idempotency rules

For either model:

- use a stable result envelope and validate it at the coordination boundary;
- pass artifact references, not large artifact contents, to avoid Cadence history payload growth;
- include the upstream WorkflowID and RunID in coordination metadata when traceability is required;
- derive deterministic downstream WorkflowIDs from the pipeline execution and step name;
- use duplicate rejection as an idempotency guard, not as the only recovery strategy;
- make artifact-producing Activities safe to retry;
- keep translation logic in the coordinator or dedicated adapters, not in either business workflow.

## Concrete change matrix

| Goal | Add | Change |
|---|---|---|
| New workflow | New workflow package, contracts, engine, Cadence adapter, config, starter, tests | Worker composition/registration and start scripts if a new Worker/task list is used. |
| New skill Activity | Skill files, schema, verifier, Activity adapter, tests | Workflow-owned registry and `devin_harness.config.json`; generalize output fallback if sentinel may be consumed. |
| Shared Worker | Workflow-owned registry contribution | Composition root combines all registrations. |
| Separate Worker | Worker entry point and task-list config | Engine startup/health scripts manage an additional process. |
| Durable chaining | Coordinator workflow, pipeline contracts, mapping tests | Register coordinator and child workflow types with compatible Workers/task lists. |
| External chaining | Coordinator service/script with persisted state and idempotency | Public starters expose result retrieval and stable contracts. |
| Runtime-configured Activity retries | Typed Activity policy config | Replace hardcoded timeout/retry values in workflow adapters. |

## Operational and design gotchas

- Only the Cadence server and Web UI run in Docker. The Worker and Devin CLI run on the host.
- Authenticate the host Devin CLI before starting the Worker.
- `auto` permission mode can exit successfully without writing an artifact when non-interactive write approval is required.
- Worker-loaded Devin profile changes require a Worker restart.
- Cadence Activity retries and a workflow's business retry loop are separate mechanisms and should have separate counters and logs.
- Queries must be synchronous and side-effect free.
- Signals are asynchronous and should update workflow state deterministically.
- Artifact paths should be repository-relative and portable across Workers. If Workers do not share a filesystem, move artifacts to durable shared storage and return stable references.
- A shared task list does not guarantee Activity affinity to the Worker that ran a previous Activity.
- Avoid hot-changing Python workflow logic while executions are in flight because the installed SDK has no workflow versioning or replay validation support.

## Source map

- `src/orchestrator/workflow.py` — current Cadence adapter and registry.
- `src/orchestrator/story_analysis_engine.py` — framework-independent workflow logic.
- `src/orchestrator/worker.py` — Worker connection and polling.
- `src/orchestrator/activities/` — Story Analysis Activity adapters.
- `src/orchestrator/skill_activity.py` — generic skill invocation and artifact resolution.
- `src/orchestrator/harness.py` — pluggable execution boundary.
- `src/orchestrator/devin_harness.py` — host Devin CLI implementation and profile resolution.
- `src/orchestrator/devin_harness.config.json` — per-skill model and permission settings.
- `src/story_analysis_workflow/config.py` — client-side Cadence configuration.
- `src/story_analysis_workflow/starter.py` — public workflow kickoff API.
- `src/story_analysis_workflow/cli.py` — operational start, query, Signal, and domain commands.
- `vault/decisions/ADR-003-skills-based-architecture.md` — skills are reusable units coordinated by workflows.
- `vault/decisions/ADR-004-skill-output-contracts.md` — output schema and sentinel contract.
- `vault/decisions/ADR-007-skill-input-independence.md` — path-based, loosely coupled skill inputs.
- `vault/decisions/ADR-009-colocate-workflow-config.md` — runtime config belongs beside its module.
- `vault/decisions/ADR-012-skill-activity-invocation-configuration.md` — per-skill invocation profiles and secure defaults.
