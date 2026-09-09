# Ramp-Up Dossier: Agentic Development Ecosystem Template

**Last Updated**: 2026-09-09

---

## Project Purpose

This repository is a template for AI-assisted software development. It serves humans through documentation and structural examples, and AI agents through executable skills, rules, schemas, verification hooks, and workflows. Its intended lifecycle moves human intent toward analyzed, designed, implemented, and verified code ([README](../README.md), [ADR-002](../vault/decisions/ADR-002-software-factory-dual-audience.md)).

The current branch extends that template with durable Cadence orchestration. Two independently owned Python workflow modules—Story Analysis and Story Design—turn repository skills into Cadence Activities and are composed into workers by a shared orchestrator ([workflow catalog](../src/orchestrator/workflow_catalog.json), [ADR-013](../vault/decisions/ADR-013-three-layer-workflow-module-architecture.md)).

---

## Domain Terminology

- **Software factory**: The combined rules, skills, workflows, documentation, and runtime patterns that help humans and agents progress from intent to working code ([ADR-002](../vault/decisions/ADR-002-software-factory-dual-audience.md)).
- **Skill**: A self-contained, composable unit of agent work with explicit inputs, an output schema, verification, and a completion sentinel ([ADR-003](../vault/decisions/ADR-003-skills-based-architecture.md), [`.devin/skills/`](../.devin/skills/)).
- **Workflow**: A coordinator that sequences skills, passes artifacts between them, and handles branches, retries, and completion ([ADR-003](../vault/decisions/ADR-003-skills-based-architecture.md)).
- **Skill Activity**: A Cadence Activity adapter that runs a canonical Devin skill through the Harness boundary. Concrete Activities own adjacent JSON configuration and specialize the common lifecycle ([ADR-014](../vault/decisions/ADR-014-colocated-skill-activity-template-method.md), [`common/skill_activity.py`](../src/common/skill_activity.py)).
- **Sentinel**: A persistent `<first-input-parent>/.process/<skill-name>.done.json` file containing the completed task and verification parameters. The runtime removes only the exact stale sentinel before invocation ([ADR-004](../vault/decisions/ADR-004-skill-output-contracts.md)).
- **Harness / DevinHarness**: The workflow-independent execution boundary and its Devin CLI implementation. `DevinHarness` invokes skills non-interactively and captures optional ATIF usage ([`common/harness.py`](../src/common/harness.py), [`common/devin_harness.py`](../src/common/devin_harness.py), [Devin ATIF notes](../vault/services/devin-atif.md)).
- **Workflow module**: An independently owned package exposing an immutable `WorkflowModuleSpec` with its domain, task list, workflow and Activity wire names, and registration callback ([`common/workflow_module.py`](../src/common/workflow_module.py)).
- **Workflow catalog**: The versioned, orchestrator-owned list of Python workflow-module paths loaded at startup ([`orchestrator/workflow_catalog.json`](../src/orchestrator/workflow_catalog.json), [`orchestrator/catalog.py`](../src/orchestrator/catalog.py)).
- **Domain / task list**: Cadence routing boundaries. The current modules use `story-analysis/story-analysis` and `story-design/story-design` respectively ([Story Analysis module](../src/story_analysis_workflow/module.py), [Story Design module](../src/story_design_workflow/module.py)).
- **Pure engine**: Cadence-independent decision logic with injected Activity-like callables. It isolates branching and state transitions from replay-sensitive workflow adapters ([ADR-013](../vault/decisions/ADR-013-three-layer-workflow-module-architecture.md)).
- **Story Analysis**: The workflow that validates a Markdown source story, extracts intent, analyzes it, grades and optionally repairs it, then publishes a run report ([Story Analysis module](../src/story_analysis_workflow/module.py)).
- **Story Design**: The workflow that validates an analysis handoff, audits current reality (i.e. what code, services, and patterns already exist), designs and grades the design, drafts a plan, and publishes a design report ([Story Design module](../src/story_design_workflow/module.py)).
- **EDD**: Eval Driven Development of skill prompts using Promptfoo; result CSVs live in `docs/edd/` ([EDD README](edd/README.md), [`evals/`](../evals/)).
- **ATIF**: Devin's exported trajectory format. The observed repository contract is `ATIF-v1.7`; normalized aggregate usage is optional and malformed telemetry is non-fatal ([Devin ATIF notes](../vault/services/devin-atif.md)).
- **Zettel ID**: A kickoff-time `YYYYMMDDHHmm` suffix used in generated Story Analysis WorkflowIDs ([Cadence service notes](../vault/services/cadence.md), [ADR-010](../vault/decisions/ADR-010-workflow-id-zettel-timestamp.md)).

---

## Repository Structure

```text
root/
├── .devin/                       Agent rules, skills, hooks, and verification scripts
├── docker/                       Local Cadence server/Web UI with SQLite persistence
├── docs/                         Process maps, guides, EDD results, examples, and requirements
│   ├── Development Process Map/  Business-case-to-deployed-code process and artifacts
│   ├── edd/                      Prompt evaluation result CSVs
│   └── reqs/                     Intent, analysis, design, plans, and workstream artifacts
├── evals/                        Promptfoo evaluation suites and support scripts
├── scripts/                      Test, workflow-engine, kickoff, cleanup, and utility entry points
├── src/
│   ├── common/                   Workflow-independent contracts, Harness, SkillActivity, usage, logging
│   ├── orchestrator/             Catalog loading, registry composition, worker topology, diagnostic workflow
│   ├── story_analysis_workflow/  Story Analysis workflow, engine, Activities, contracts, CLI, tests
│   └── story_design_workflow/    Story Design workflow, engine, Activities, contracts, CLI, tests
├── tests/                        Cross-package unit, integration, and end-to-end tests
├── vault/                        Indexed ADRs and durable service/environment knowledge
├── AGENTS.md                     Vault protocol and NixOS environment conventions
├── package.json                  Promptfoo/Ajv dependencies and evaluation scripts
└── shell.nix                     Node/Python native development environment
```

The three-layer source boundary is intentional: `common` imports no workflow or orchestrator package; workflow packages depend on `common` but not on each other or `orchestrator`; `orchestrator` is the composition root ([ADR-013](../vault/decisions/ADR-013-three-layer-workflow-module-architecture.md), architecture tests under [`src/`](../src/)).

---

## Technology Stack

- **Language/Runtime**: Python 3 from Nixpkgs for orchestration and tests; Bash for operator scripts; Node.js 24 from `shell.nix` for prompt evaluations ([`shell.nix`](../shell.nix)).
- **Workflow Framework**: `cadence-python-client==0.3.0`; workflows run against a local Uber Cadence server ([requirements](../src/orchestrator/requirements.txt)).
- **Agent Runtime**: Host `devin` CLI invoked through `common.DevinHarness` ([`common/devin_harness.py`](../src/common/devin_harness.py)).
- **Validation**: `jsonschema==4.26.0` for Python artifacts and Ajv `^8.20.0` for JavaScript-side schema validation ([requirements](../src/orchestrator/requirements.txt), [`package.json`](../package.json)).
- **Testing**: `pytest==9.1.1`, `pytest-asyncio==1.4.0`, package-local suites, cross-package unit tests, integration tests, and E2E tests ([requirements](../src/orchestrator/requirements.txt), [`pytest.ini`](../pytest.ini), [`tests/`](../tests/)).
- **Evaluation**: Promptfoo `^0.121.17`, with repository scripts for normal and verbose evaluations ([`package.json`](../package.json), [`evals/`](../evals/)).
- **Build/Package**: Nix shell for reproducible runtime dependencies; Python virtual environment and pip requirements; npm lockfile for Node dependencies ([`shell.nix`](../shell.nix), [`package-lock.json`](../package-lock.json)).
- **Containers**: Docker Compose runs `ubercadence/server:master` and `ubercadence/web:latest` ([`docker/docker-compose.yml`](../docker/docker-compose.yml), [Cadence service notes](../vault/services/cadence.md)).
- **Data/Storage**: SQLite persistence for the local Cadence stack; workflow artifacts, logs, sentinels, reports, and ATIF exports are filesystem-based ([`docker/cadence-sqlite.yaml`](../docker/cadence-sqlite.yaml), [ADR-016](../vault/decisions/ADR-016-consolidated-run-reporting.md)).
- **CI/CD**: [Not found in repo]. No `.github/workflows/` files or equivalent pipeline configuration were discovered on 2026-09-09.
- **Application web framework**: [Not found in repo]. Cadence Web is an operational dependency, not an application framework implemented here.

---

## Technical Patterns and Key Players

- **Skills-based architecture**: Work is decomposed into independently verifiable skills, while workflows coordinate their order and artifact handoffs ([ADR-003](../vault/decisions/ADR-003-skills-based-architecture.md)).
- **Three-layer workflow modules**: Shared infrastructure lives in `common`, business orchestration in workflow-owned packages, and deployment composition in `orchestrator` ([ADR-013](../vault/decisions/ADR-013-three-layer-workflow-module-architecture.md)).
- **Explicit plugin catalog**: The orchestrator loads configured module paths, validates `SPEC` descriptors, groups exact domain/task-list routes, and rejects duplicate wire names ([`orchestrator/catalog.py`](../src/orchestrator/catalog.py), [`orchestrator/composition.py`](../src/orchestrator/composition.py)).
- **One worker per route, one host process**: `compose_worker_specs` produces route-specific worker specifications; `run_worker_topology` manages all Cadence Client/Worker contexts transactionally with `AsyncExitStack` ([`orchestrator/composition.py`](../src/orchestrator/composition.py), [`orchestrator/runtime.py`](../src/orchestrator/runtime.py)).
- **Pure engine + thin replay-safe adapter**: Workflow decision logic avoids Cadence imports and side effects; workflow adapters translate ports to Activities, Signals, Queries, and timers. This also compensates for the released Python SDK's lack of `TestWorkflowEnvironment` ([Cadence service notes](../vault/services/cadence.md)).
- **Template-method SkillActivity lifecycle**: Common code controls prompt construction, stale-sentinel cleanup, harness execution, configuration, output resolution, and result conversion; concrete Activities override typed hooks ([ADR-014](../vault/decisions/ADR-014-colocated-skill-activity-template-method.md), [`common/skill_activity.py`](../src/common/skill_activity.py)).
- **Colocated configuration**: Workflow runtime settings sit beside their package, while each harness-backed Activity owns a same-stem `*.config.json` ([ADR-009](../vault/decisions/ADR-009-colocate-workflow-config.md), [`story_analysis_workflow/activities/`](../src/story_analysis_workflow/activities/)).
- **Persistent sentinel contracts**: Every skill owns its output schema and verification parameters; sentinels remain available for audit after verification ([ADR-004](../vault/decisions/ADR-004-skill-output-contracts.md)).
- **Route-aware structured file logging**: The orchestrator configures worker logging, while common context carries workflow, run, Activity, domain, and task-list identity ([ADR-011](../vault/decisions/ADR-011-workflow-logging.md), [`common/workflow_logger.py`](../src/common/workflow_logger.py)).
- **Atomic, schema-versioned reporting**: Terminal workflow reports are validated and atomically replaced; aggregate windows include auditable operands and exclusions ([ADR-016](../vault/decisions/ADR-016-consolidated-run-reporting.md), [`story_analysis_workflow/reporting.py`](../src/story_analysis_workflow/reporting.py)).
- **TDD and architecture tests**: Tests are colocated with each package and supplemented by top-level contract, integration, and E2E suites. AST/static tests enforce dependency boundaries ([`scripts/run_unit_tests.sh`](../scripts/run_unit_tests.sh), [`tests/`](../tests/)).
- **Eval-driven skill development**: Promptfoo suites evaluate skill prompts separately from Python orchestration behavior ([`evals/`](../evals/), [EDD README](edd/README.md)).

Key runtime entry points are [`orchestrator.worker`](../src/orchestrator/worker.py), [`story_analysis_workflow.cli`](../src/story_analysis_workflow/cli.py), [`story_design_workflow.cli`](../src/story_design_workflow/cli.py), and the shell scripts under [`scripts/`](../scripts/).

---

## Historical Context and Architectural Decisions

- **Dual-audience software factory (2026-04-29)**: The repository is both a human-readable reference and an agent-executable template ([ADR-002](../vault/decisions/ADR-002-software-factory-dual-audience.md)).
- **Skills coordinate through workflows (2026-04-29)**: Skills remain small and reusable; workflow logic owns sequencing, retries, and handoffs ([ADR-003](../vault/decisions/ADR-003-skills-based-architecture.md)).
- **Skill-owned output contracts (2026-04-29; updated 2026-09-08)**: Skills define schemas and persistent, colocated sentinel files for deterministic verification ([ADR-004](../vault/decisions/ADR-004-skill-output-contracts.md)).
- **Colocated workflow configuration (2026-08-31)**: Runtime configuration moved out of requirement documents and next to the workflow package, fixing silent fallback to defaults ([ADR-009](../vault/decisions/ADR-009-colocate-workflow-config.md)).
- **Kickoff-time WorkflowID policy (2026-08-31)**: Story Analysis IDs use the story name and minute-resolution Zettel timestamp instead of a content hash, allowing intentional reruns of unchanged content ([ADR-010](../vault/decisions/ADR-010-workflow-id-zettel-timestamp.md)).
- **Workflow-aware logging (2026-09-01)**: Logs and artifacts are scoped by sanitized workflow/run and Activity-attempt identity ([ADR-011](../vault/decisions/ADR-011-workflow-logging.md)).
- **Three-layer module architecture (2026-09-03)**: A broad refactor separated common infrastructure, workflow-owned packages, and the orchestrator composition root; the implementation status was recorded through 2026-09-08 ([ADR-013](../vault/decisions/ADR-013-three-layer-workflow-module-architecture.md); related history includes `bdef4af` through `96bf70a`).
- **Colocated SkillActivity configuration (2026-09-03)**: Adjacent JSON and a template-method lifecycle replaced central skill-name switches and profile maps ([ADR-014](../vault/decisions/ADR-014-colocated-skill-activity-template-method.md)).
- **ATIF metric scope (2026-09-04)**: Only independently present token/cost fields are normalized; missing cost is not estimated ([ADR-015](../vault/decisions/ADR-015-devin-cost-metric-scope.md), [Devin ATIF notes](../vault/services/devin-atif.md)).
- **Consolidated run reporting (proposed 2026-09-08, substantially integrated)**: Story Analysis publishes one schema-versioned report per modeled terminal execution and supports explicit-window aggregates ([ADR-016](../vault/decisions/ADR-016-consolidated-run-reporting.md); history includes `c27c7cd` and `0c6de50`).

Commit messages predominantly use a Karma/Conventional-style `type(scope): summary`, often pairing implementation and test scopes, for example `feat(design engine)/test(design engine): ...`. Branches reflect purpose prefixes such as `feat/`, `refactor/`, `test/`, `maint/`, `cicd/`, and `update/` (`git log --oneline -30`, `git branch -a`, observed 2026-09-09).

---

## Recent Development Focus

The recent history is concentrated on the Story Design workflow and on hardening workflow artifact contracts:

- Story Design engine branches for passing grades, failed grades, planning failures, invalid handoffs, and Activity failures (`50dcbf1` through `880fb80`).
- Draft-plan and report Activities, including `analysis_path`, score propagation, and `StoryDesignReport` (`f3be5fd` through `5f56171`).
- Persistent sentinel lifecycle and colocated `.process` paths (`3d785f0`, `63d218b`, `9e537e8`).
- Utility support for validating JSON schemas and cleaning interim requirement artifacts (`ae0dd8d`, `8f97493`, `9fb14e2`).
- Earlier workflow-orchestration work established Story Analysis, Cadence client/worker wiring, logging, IDs, module refactoring, and consolidated run reporting (`cb743c5`, `7d59fb7`, `ae343a2`, `96bf70a`, `a5bfd33`).

Active local and remote branch names include `feat/workflow-orchestration`, `refactor/orchestrator`, `feat/edd`, `maint/edd-providers-and-patterns`, test branches for SDLC/design work, and `cicd/release-pipeline` (`git branch -a`, observed 2026-09-09).

---

## Quick Start Guide

### Prerequisites

- Nix/Nix shell; the repository records NixOS 25.11 and `nix-shell` 2.31.3 as its working environment ([`AGENTS.md`](../AGENTS.md)).
- Docker with Docker Compose for the local Cadence stack ([`scripts/start-workflow-engine.sh`](../scripts/start-workflow-engine.sh)).
- Authenticated `devin` CLI for harness-backed workflow Activities ([`scripts/start-workflow-engine.sh`](../scripts/start-workflow-engine.sh)).
- Node/npm for Promptfoo evaluations; `shell.nix` supplies Node.js 24 ([`shell.nix`](../shell.nix)).

### Local Setup

Create the Python environment using the command emitted by the repository scripts:

```bash
nix-shell --run "python3 -m venv .venv && .venv/bin/pip install -r src/orchestrator/requirements.txt"
```

Install the locked Node dependencies:

```bash
npm install
```

Start the configured Cadence domains and worker routes:

```bash
scripts/start-workflow-engine.sh
```

Start workflow executions after the engine is ready:

```bash
scripts/kickoff-analyze-story.sh <story-file>
scripts/kickoff-design-story.sh <analysis-json>
```

Stop the local engine with:

```bash
scripts/stop-workflow-engine.sh
```

Sources: [`requirements.txt`](../src/orchestrator/requirements.txt), [`start-workflow-engine.sh`](../scripts/start-workflow-engine.sh), [`kickoff-analyze-story.sh`](../scripts/kickoff-analyze-story.sh), [`kickoff-design-story.sh`](../scripts/kickoff-design-story.sh).

### Running Tests

```bash
scripts/run_unit_tests.sh
scripts/run_integration_tests.sh
scripts/run_e2e_tests.sh
```

The integration and E2E suites require their external runtime conditions; inspect [`tests/integration/`](../tests/integration/) and [`tests/e2e/`](../tests/e2e/) before assuming they are isolated.

Run a Promptfoo evaluation by passing a config path to the package script:

```bash
npm test -- <config>
npm run test:verbose -- <config>
npm run view
```

Sources: [`scripts/run_unit_tests.sh`](../scripts/run_unit_tests.sh), [`scripts/run_integration_tests.sh`](../scripts/run_integration_tests.sh), [`scripts/run_e2e_tests.sh`](../scripts/run_e2e_tests.sh), [`package.json`](../package.json).

### Common Workflows

- Browse executable agent workflows in [`.devin/skills/`](../.devin/skills/), including story extraction, analysis, grading/repair, current-reality audit, design, planning, TDD, schema validation, Promptfoo, and Cadence references.
- Follow the repository knowledge protocol in [`AGENTS.md`](../AGENTS.md): query [`vault/INDEX.md`](../vault/INDEX.md) before non-trivial work and update the vault when durable knowledge changes.
- Use the [Development Process Map](Development%20Process%20Map/Software%20Development%20Process%20-%20Business%20Case%20to%20Deployed%20Code.md) for the documented path from business case through deployed code.
- Use [Mapping Cadence Workflows and Devin Skill Activities](mapping-workflows-and-skill-activities.md) for workflow/activity concepts, but prefer ADR implementation-status sections and current source where older “current constraints” in that guide conflict with the completed module refactor.
- Use the [Cadence local runbook](reqs/workflow-orchestration/cadence-local-runbook.md) and [Cadence vault page](../vault/services/cadence.md) for local operation and SDK gotchas.

---

## Key Resources

**Architecture and Decisions:**
- [Vault index](../vault/INDEX.md)
- [Three-layer workflow architecture ADR](../vault/decisions/ADR-013-three-layer-workflow-module-architecture.md)
- [Workflow/activity mapping guide](mapping-workflows-and-skill-activities.md)
- [Workflow-module proposed architecture](reqs/refactor-workflow-modules/proposed-architecture.md)
- [Development Process Map canvas](Development%20Process%20Map/202604221317%20-%20Process%20Map%20-%20Software%20Development%20from%20Business%20Case%20to%20Deployed%20Code.canvas)

**Development Guidelines:**
- [Agent and vault conventions](../AGENTS.md)
- [Repository rules](../.devin/rules/)
- [Skill definitions](../.devin/skills/)
- [E2E debugging guide](e2e-debugging-workflow-guide.md)
- [Hooks overview](hooks-overview.md)

**API and Requirements:**
- [Requirements and design artifacts](reqs/)
- [Story Analysis report schemas](../src/story_analysis_workflow/schemas/)
- [Story Analysis workflow module](../src/story_analysis_workflow/module.py)
- [Story Design workflow module](../src/story_design_workflow/module.py)
- [Development artifact templates](Development%20Process%20Map/artifacts/)

**Known Documentation Gaps:**
- A repository-level CI/CD implementation is not present.
- The root README still describes some historical skill names and a `.devin/workflows/` layout that are not present in the current tree; use the current `.devin/skills/`, source modules, scripts, and vault index as the operational references.
