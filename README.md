# Agentic Development Ecosystem Template

A referenceable, extensible, and reusable example of how to build agent skills, evaluate them, coordinate them into workflows, and apply them to an agentic software development lifecycle.

The repository combines:

- **Reusable rules and skills** — agent guidance and focused capabilities that can be adapted to another project;
- **Tested skill contracts** — structured outputs, schemas, verification scripts, and evaluation cases;
- **Proven workflows** — repeatable sequences for understanding codebases, analyzing work, designing changes, and implementing with TDD;
- **Working orchestration** — durable coordination of agentic calls across the Analysis and Design phases; and
- **Example artifacts** — inspectable inputs, outputs, grades, reports, and implementation references.

## Purpose

This repository is the basis for building an agentic development ecosystem rather than a single application. It shows how to move from one-off prompts toward capabilities that are:

- **Modular** — each skill has a focused responsibility;
- **Composable** — workflows combine skills into useful sequences;
- **Testable** — skills have repeatable evaluations and machine-verifiable output contracts;
- **Observable** — orchestrated runs leave artifacts, reports, logs, and execution history;
- **Reusable** — skills and workflow patterns can be carried into other repositories; and
- **Extensible** — additional SDLC phases can follow the same boundaries and conventions.

The current orchestration implementation demonstrates the first two SDLC phases, **Analysis** and **Design**. Implementation remains a documented skill-driven handoff rather than part of the durable orchestration.

## Use the repository by scenario

### Brownfield projects

When joining or modifying an existing codebase, begin by establishing current reality:

1. Use [Explore Codebase](.devin/skills/explore-codebase/SKILL.md) to identify architecture, conventions, dependencies, and testing patterns.
2. Use [Query Code](.devin/skills/query-code/SKILL.md) for focused follow-up exploration during analysis or design.
3. Record durable architectural knowledge and constraints in the repository documentation or vault before designing changes.

This sequence reduces the risk of proposing work that conflicts with existing patterns or rediscovering decisions already captured by the project.

### Greenfield projects

For a new project, establish the development system before scaling agentic work:

1. Define the target architecture, coding standards, quality expectations, and repository conventions with an active human-agent design conversation.
2. Capture those decisions as repository rules and architecture documentation.
3. Adapt the skills and output contracts in `.devin/skills/` to the new domain.
4. Add representative evaluation cases before treating a skill as reusable.
5. Introduce orchestration when several stable skills need sequencing, retries, quality gates, or durable state.

The repository is intended to be forked and tailored: retain the patterns, then replace examples and constraints with those of the target system.

### Feature development

The current feature-development path combines durable orchestration with a skill-driven implementation handoff:

1. **Analysis orchestration** — validate a Markdown story, extract intent, analyze it, grade the analysis, and retry or request human intervention when necessary.
2. **Design orchestration** — audit the current repository, validate handoffs, design the implementation, grade the design, and produce an implementation plan.
3. **Design clarification** — when the design does not pass or requires human judgment, use the manual [Design Buddy](.devin/rules/design-buddy.md) to challenge assumptions, clarify trade-offs, and refine the intended design before continuing.
4. **Implementation handoff** — use the [TDD Workflow](.devin/skills/tdd-workflow/SKILL.md) as the current working reference for implementing the approved plan through Think, Red, Green, and Refactor cycles.

The durable orchestration currently ends with the Design outputs and implementation plan. It does **not yet orchestrate the TDD implementation phase**. See [Orchestration: Analysis and Design](docs/orchestration.md) for the operating guide, execution model, and extension points.

## Orchestration

Orchestration coordinates independently executable skills into a reliable process with explicit ordering, inputs, outputs, retries, validation, quality gates, and terminal states.

In this repository, Cadence persists workflow state and decisions. Workers execute Activities that validate artifacts, invoke repository skills through Devin, grade outputs, and publish reports. The working Analysis and Design workflows demonstrate how skills can become durable SDLC building blocks without coupling business workflows to one another.

Read [Orchestration: Analysis and Design](docs/orchestration.md) for setup, commands, execution paths, outputs, troubleshooting, and extension guidance. For the underlying platform, see the official [Cadence documentation](https://cadenceworkflow.io/docs/).

## Architecture at a glance

```text
Human intent and repository context
                |
                v
      Reusable rules and skills
                |
                +-----------------------------+
                | direct use                  | orchestrated use
                v                             v
      Skill outputs and tests       Workflow client -> Cadence service
                                                  |
                                                  v
                                      Orchestrator composition root
                                                  |
                                      +-----------+-----------+
                                      |                       |
                                      v                       v
                           Analysis Worker route    Design Worker route
                                      |                       |
                                      v                       v
                              Workflow engines and Activities
                                      |                       |
                                      +-----------+-----------+
                                                  |
                                                  v
                                      SkillActivity / DevinHarness
                                                  |
                                                  v
                                      Skills -> artifacts, grades,
                                               reports, and logs
```

The runtime uses three implementation layers:

- `src/common/` — reusable harness, Activity lifecycle, logging, and workflow-module contracts;
- `src/story_analysis_workflow/` and `src/story_design_workflow/` — workflow-specific engines, Activities, clients, configuration, and tests; and
- `src/orchestrator/` — workflow catalog loading, registry composition, and Worker lifecycle.

## A skill at a glance

A mature artifact-producing skill is a small, self-contained capability rather than just a prompt file. Representative skills such as [Analyze Story](.devin/skills/analyze-story/) and [Design Story Implementation](.devin/skills/design-story-implementation/) use this structure:

```text
.devin/skills/<skill-name>/
├── SKILL.md                 # Purpose, inputs, process, outputs, and completion contract
├── schema/
│   ├── <output>.schema.json # Machine-readable output contract
│   ├── <output>.example.json
│   ├── sentinel.schema.json
│   └── verify-params.schema.json
├── verify.sh                # Deterministic structural/output verification
└── _tests/
    ├── test_cases.md        # Intended behavior and coverage
    ├── prompt.md            # Evaluation prompt/template
    ├── *.tests.yaml         # Promptfoo cases and assertions
    ├── data/ or _data/      # Representative fixtures
    └── *Checks.js           # Optional custom assertions
```

Not every skill needs every file. Coordinating or reference skills may primarily contain `SKILL.md` and progressively disclosed reference pages. Artifact-producing skills should make their inputs, output schema, verification behavior, and completion signal explicit.

### What the evaluations provide

Skill evaluation assets live with the skill under `_tests/`:

- **test cases** describe expected capability, edge cases, and failure behavior;
- **fixtures** provide stable, representative inputs;
- **Promptfoo YAML** executes repeatable model evaluations;
- **custom checks** evaluate properties that simple text assertions cannot; and
- **evaluation prompts** isolate the skill behavior under test.

Cross-skill evaluation results and Evaluation-Driven Development guidance are collected under [`docs/edd/`](docs/edd/). This separates reusable test definitions from run results and broader evaluation analysis.

## Repository map

| Path | Purpose |
|---|---|
| `.devin/skills/` | Reusable capabilities, skill contracts, schemas, verification, and colocated evaluations |
| `.devin/rules/` | Repository and interaction guidance used by agents and human collaborators |
| `src/common/` | Workflow-independent Activity, harness, usage, and logging infrastructure |
| `src/orchestrator/` | Workflow catalog, registry composition, and Worker runtime |
| `src/story_analysis_workflow/` | Durable Analysis workflow and its Activities, clients, contracts, and tests |
| `src/story_design_workflow/` | Durable Design workflow and its Activities, clients, contracts, and tests |
| `scripts/` | Workflow operation, evaluation, and repository test entry points |
| `docker/` | Local Cadence service and Web UI configuration |
| `docs/edd/` | Evaluation-Driven Development guidance and consolidated evaluation results |
| `docs/Development Process Map/` | Wider SDLC stages, artifacts, and process relationships |
| `docs/reqs/` | Worked requirements, analyses, designs, plans, and implementation records |
| `vault/` | Architectural decisions, service notes, and durable project knowledge |

## Getting started

1. **Fork this repository** as the basis for your own agentic development ecosystem.
2. **Review the use-case paths above** and select the smallest relevant capability or workflow.
3. **Inspect a representative skill** to understand its instructions, schema, verification, and evaluations before adapting it.
4. **Follow the [orchestration quick start](docs/orchestration.md#quick-start)** to run the working Analysis and Design demonstrations.
5. **Replace examples and rules deliberately**, preserving explicit contracts and tests as the repository evolves.

## Additional documentation

- [Orchestration: Analysis and Design](docs/orchestration.md)
- [Development Process Map](docs/Development%20Process%20Map/Software%20Development%20Process%20-%20Business%20Case%20to%20Deployed%20Code.md)
- [Evaluation-Driven Development](docs/edd/README.md)
- [Hooks overview](docs/hooks-overview.md)
- [Creating personas](docs/creating-personas.md)
- [Architecture decisions and project knowledge](vault/INDEX.md)

## License

See [LICENSE](LICENSE) for details.
