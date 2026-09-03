# Skill Activity Template Method and Colocated Configuration Refactor

## Bottom line

Refactor `run_skill` into a `SkillActivity` template-method class. Each concrete Skill Activity owns an adjacent JSON configuration file and optional typed transformation hooks, while the template retains control of execution order, stale-sentinel handling, logging, timing, Harness invocation, validation, and result construction.

Change `Harness.run` to accept an immutable configuration mapping. The generic layer passes Harness namespaces without interpretation; each Harness implementation validates and translates only its own namespace. `DevinHarness` consumes `devin` settings and is solely responsible for producing safe Devin CLI arguments.

## Status

Proposed design. No implementation is included in this document.

## Motivation

The current implementation has three scaling problems:

1. `run_skill` is a function with fixed prompt, sentinel, context, and output-resolution behavior, so specialization requires adding skill-name conditionals to generic code.
2. Devin model and permission settings live in one orchestrator-level file keyed by skill name, separating Activity behavior from its configuration.
3. `Harness.run(prompt, cwd)` receives no explicit invocation configuration. `DevinHarness` recovers the current skill through context and performs centralized profile lookup, which makes configuration ownership indirect.

The refactor should let a workflow module add a Skill Activity without modifying `orchestrator.skill_activity` or a central skill catalog.

## Current state

### Current execution sequence

`run_skill` currently performs this fixed sequence:

1. Derive `.process/<skill>.done.json`.
2. Delete a stale sentinel.
3. Build a standard prompt.
4. Enter Activity logging context.
5. Enter canonical skill invocation context.
6. Call `harness.run(prompt, cwd=repo_root)`.
7. Measure duration and handle nonzero exit status.
8. Read and validate the sentinel.
9. Resolve an output path from `verify_params`.
10. Fall back to a hardcoded skill-name output convention when the sentinel is absent.
11. Return `SkillActivityOutput`.

### Existing coupling

- `_conventional_output_path` knows the four Story Analysis canonical skill names.
- `_build_prompt` is global and cannot be specialized without replacing the function.
- `_sentinel_path` assumes one sentinel convention.
- `skill_invocation_context` is always constructed in the same way.
- `output_path_key` is supplied separately at every `run_skill` call.
- `DevinHarness` owns a central profile store and discovers the current skill through context.
- Every fake Harness implements the old two-argument contract.

### Decisions this proposal changes

This proposal supersedes the following parts of ADR-012:

- Configuration is no longer primarily stored in `src/orchestrator/devin_harness.config.json` by canonical skill key.
- `Harness.run(prompt, cwd)` is no longer preserved unchanged.
- `DevinHarness` no longer needs invocation context to select a profile.

This proposal retains these ADR-012 invariants:

- secure least-privilege defaults;
- explicit write permission for unattended artifact-producing skills;
- immutable effective configuration per invocation;
- field validation before process launch;
- no prompt parsing;
- no mutable process-global current-skill state;
- sanitized logs that do not expose prompts, secrets, or raw configuration.

A follow-up ADR should mark ADR-012 partially superseded when this design is accepted and implemented.

## Goals

- Group each Skill Activity definition and configuration together.
- Configure model, permissions, and future Harness options per Activity.
- Keep the generic Skill Activity algorithm stable and reusable.
- Permit targeted specialization through typed no-op transformation hooks.
- Keep Harness-specific CLI knowledge out of `SkillActivity`.
- Make configuration flow explicit and testable.
- Remove the generic runner's knowledge of Story Analysis skill names and filenames.
- Preserve current sentinel validation, retry safety, observability, and output contracts.
- Support Harness implementations other than Devin without forcing them to understand Devin settings.

## Non-goals

- Changing Cadence workflow or Activity wire names.
- Changing skill output schemas or sentinel schema.
- Dynamically reloading configuration while a Worker is running.
- Passing arbitrary dictionary keys directly to a shell command.
- Moving Story Analysis Activities into their final workflow package as part of this refactor.
- Changing Cadence retry policies.
- Implementing referenced external Devin profiles.

## Proposed ownership model

```text
concrete Cadence Activity function
        |
        v
concrete SkillActivity instance
  - adjacent JSON path
  - skill identity
  - output key
  - expected output convention
  - optional transformation hooks
        |
        v
SkillActivity.execute template method
  - fixed lifecycle and invariants
        |
        v
Harness.run(prompt, cwd, config)
        |
        +-- DevinHarness consumes config["devin"]
        +-- OtherHarness consumes config["other-harness"]
```

### Responsibility table

| Component | Owns | Must not own |
|---|---|---|
| Concrete Cadence Activity | Cadence wire name and serializable arguments | CLI translation or lifecycle sequencing |
| Concrete `SkillActivity` | Skill identity, adjacent config, default prompt/output semantics, optional hooks | Devin CLI flags |
| Base `SkillActivity` | Template order, errors, logging, stale-sentinel cleanup, validation, result construction | Specific skill catalog |
| `Harness` protocol | Generic invocation boundary | Skill output interpretation |
| `DevinHarness` | Devin namespace validation and CLI translation | Sentinel or artifact semantics |
| Adjacent JSON | Activity and Harness invocation settings | Secrets or runtime workflow state |

## Colocated configuration

### File location

Each Activity has a same-stem configuration file:

```text
src/orchestrator/activities/
  analyze_story.py
  analyze_story.config.json
  extract_story_intent.py
  extract_story_intent.config.json
  grade_story_analysis.py
  grade_story_analysis.config.json
  repair_story_analysis.py
  repair_story_analysis.config.json
```

When workflow ownership is separated later, both files move together into the workflow module.

### Proposed schema

```json
{
  "activity": {
    "skill_name": "analyze-story",
    "output_path_key": "analysis_path"
  },
  "harness": {
    "devin": {
      "model": "SWE-1.7",
      "permission_mode": "accept-edits"
    }
  }
}
```

The namespaces have different owners:

- `activity` is parsed and validated by `SkillActivityConfig`.
- `harness` is passed as an immutable mapping to the selected Harness.
- `harness.devin` is parsed and validated only by `DevinHarness`.
- A different Harness consumes its own namespace and ignores unrelated Harness namespaces.

### Namespaced-key behavior

A Harness must:

1. Select only its documented namespace.
2. Treat a missing namespace as an empty configuration.
3. Validate all known keys and values in its namespace.
4. Reject unknown keys inside its own namespace.
5. Ignore sibling namespaces intended for other Harness implementations.
6. Never infer CLI flags by converting dictionary keys mechanically.

For example, `DevinHarness` ignores `harness.other-agent`, but rejects `harness.devin.permisson_mode` as a misspelling.

### Configuration loading

- Load and validate adjacent JSON when the concrete `SkillActivity` instance is constructed at Worker startup.
- Convert nested dictionaries to immutable mappings.
- Retain one immutable configuration snapshot for the Worker lifetime.
- Do not read the file during every invocation or retry.
- Fail Worker startup for missing, unreadable, malformed, or invalid required Activity configuration.
- Do not log raw configuration values.

This preserves predictable retry behavior within a running Worker. Persisting a configuration snapshot in Cadence history remains separate future work.

### Defaults and precedence

Recommended precedence:

1. Values explicitly supplied by the concrete Activity constructor for tests or deployment composition.
2. Adjacent JSON values.
3. base `SkillActivity` defaults for generic Activity fields;
4. Harness implementation defaults for its own namespace.

Environment or central-file overrides are deliberately excluded from the first implementation. Adding them immediately would weaken the goal that an Activity and its configuration move together. If operational overrides become necessary, define and test an explicit precedence layer rather than allowing arbitrary mutation.

## Harness contract

### Proposed protocol

```python
from pathlib import Path
from typing import Mapping, Protocol

HarnessConfig = Mapping[str, object]


class Harness(Protocol):
    def run(
        self,
        prompt: str,
        *,
        cwd: Path,
        config: HarnessConfig,
    ) -> HarnessResult:
        ...
```

`config` is the content below the top-level `harness` key. It may contain multiple Harness namespaces.

### Why the generic Harness receives namespaces

Passing the full namespaced Harness mapping allows one Activity configuration to remain portable across Harness implementations. It also keeps selection logic inside each implementation without coupling `SkillActivity` to Devin types.

### Devin translation

`DevinHarness.run` performs these steps:

1. Read the `devin` namespace or use an empty mapping.
2. Validate namespace type.
3. Resolve known fields against secure defaults.
4. Validate model and permission mode.
5. Build a fresh command list.
6. Invoke the runner without a shell.
7. Log only sanitized effective fields.
8. Return `HarnessResult`.

Initial supported keys:

| JSON key | CLI representation | Default |
|---|---|---|
| `model` | `--model <value>` | Existing secure model default |
| `permission_mode` | `--permission-mode <value>` | `auto` |
| `sandbox` | `--sandbox` when true | `false` |
| `config_path` | `--config <path>` | omitted |

Only add a key after its type, allowed values, security implications, logging treatment, and CLI rendering are tested. Path values must be validated and must not expose secrets in logs.

### Compatibility migration

During migration, either update all Harness implementations and fakes atomically or provide a short-lived adapter around legacy Harnesses. Do not use signature introspection or catch `TypeError` to guess which interface an implementation supports; that can conceal real implementation errors.

The centralized `DevinHarnessConfig` may temporarily remain as a deprecated default provider, but Activity-owned values must take precedence. Remove it once every Activity has adjacent configuration and migration tests pass.

## SkillActivity template method

### Shape

`SkillActivity` is an ordinary infrastructure class, not itself a Cadence Activity. Existing `@activity.defn` functions delegate to an instance so Cadence wire compatibility remains unchanged.

```python
class SkillActivity:
    def execute(self, skill_input: SkillActivityInput) -> SkillActivityOutput:
        """Fixed template method. Concrete classes do not override this."""
        ...
```

The Cadence adapter continues to use `asyncio.to_thread(activity.execute, input)` because Harness execution is blocking.

### Fixed template algorithm

`execute` owns this order:

1. Resolve the repository root.
2. Obtain the immutable Activity configuration.
3. Create the default sentinel path.
4. Pass it through `modify_sentinel_path`.
5. Remove an existing stale sentinel.
6. Create the default prompt.
7. Pass it through `modify_prompt`.
8. Obtain the Harness configuration mapping.
9. Pass it through `modify_harness_config`.
10. Create the default invocation context manager.
11. Pass it through `modify_invocation_context`.
12. Enter Activity logging context.
13. Enter the invocation context.
14. Call `harness.run(prompt, cwd, config)` and measure duration.
15. Validate the Harness result.
16. Read and validate the sentinel when present.
17. Resolve the default output path from the sentinel or concrete Activity convention.
18. Pass it through `modify_output_path`.
19. Construct the default `SkillActivityOutput`.
20. Pass it through `modify_result` and return it.

Concrete implementations may transform values, but may not reorder or omit lifecycle steps.

### Typed no-op hooks

Every base implementation accepts one value and returns the same type unchanged:

```python
from contextlib import AbstractContextManager
from pathlib import Path
from typing import Mapping

class SkillActivity:
    def modify_prompt(self, prompt: str) -> str:
        return prompt

    def modify_sentinel_path(self, sentinel_path: Path) -> Path:
        return sentinel_path

    def modify_harness_config(
        self,
        config: Mapping[str, object],
    ) -> Mapping[str, object]:
        return config

    def modify_invocation_context(
        self,
        context: AbstractContextManager[None],
    ) -> AbstractContextManager[None]:
        return context

    def modify_output_path(self, output_path: Path) -> Path:
        return output_path

    def modify_result(
        self,
        result: SkillActivityOutput,
    ) -> SkillActivityOutput:
        return result
```

Using a context manager as the invocation-context hook value satisfies the same-type transformation rule while preserving guaranteed cleanup through `with`.

### Hook constraints

Hooks must:

- be synchronous and deterministic relative to their arguments and immutable Activity configuration;
- return the declared type;
- avoid I/O and side effects;
- not mutate the received mapping or result;
- not log prompts, input document content, secrets, or raw configuration;
- not invoke the Harness;
- not manage stale sentinel cleanup;
- not suppress template validation.

The template should perform runtime type checks at hook boundaries where an invalid return would otherwise cause an obscure failure.

### Required specialization versus optional hooks

Not every varying behavior should be a no-op hook. Concrete Activities must explicitly provide required identity and contract values:

- canonical skill name;
- output `verify_params` key;
- configuration path;
- expected output-path convention for missing-sentinel recovery.

These should be constructor values or abstract properties. Making required values no-op hooks would permit incomplete Activities that fail only after Harness execution.

### Output resolution

Remove `_conventional_output_path` from generic infrastructure. A concrete Activity supplies its expected output path calculation. The template then passes the calculated `Path` through `modify_output_path`.

Sentinel resolution remains preferred. Missing-sentinel fallback remains supported because the verification hook may consume the sentinel after a successful invocation.

The template must continue to reject:

- malformed sentinel JSON;
- mismatched sentinel task;
- missing required `verify_params` output key;
- output paths outside allowed repository policy, if such validation is introduced.

## Example concrete Activity

```python
CONFIG_PATH = Path(__file__).with_suffix(".config.json")


class AnalyzeStorySkillActivity(SkillActivity):
    def expected_output_path(self, skill_input: SkillActivityInput) -> Path:
        input_path = Path(skill_input.input_paths[0])
        if input_path.name.endswith(".intent.json"):
            return input_path.with_name(
                f"{input_path.name[:-len('.intent.json')]}.analysis.json"
            )
        return input_path.with_name("analysis.json")


ANALYZE_STORY_ACTIVITY = AnalyzeStorySkillActivity(
    config_path=CONFIG_PATH,
    harness=HARNESS,
)


@activity.defn(name="analyze_story")
async def analyze_story(intent_path: str) -> dict:
    output = await asyncio.to_thread(
        ANALYZE_STORY_ACTIVITY.execute,
        SkillActivityInput(input_paths=[intent_path]),
    )
    return dataclasses.asdict(output)
```

The JSON owns `skill_name`, `output_path_key`, and Devin settings. The Python subclass owns only output naming behavior that cannot be represented safely as static data.

## Error handling and observability

Preserve these behaviors:

- stale sentinel removal before Harness execution;
- invocation context reset after success or failure;
- nonzero Harness result becomes `SkillActivityError`;
- missing sentinel logs a sanitized warning and uses the expected path;
- malformed or mismatched sentinels fail;
- Activity and Devin log paths are returned;
- prompt, input paths, raw config, subprocess output, and secrets stay out of Activity logs;
- Devin subprocess output remains in its dedicated debug log only;
- launch `OSError` remains sanitized.

Add error categories for:

- missing Activity config;
- malformed Activity config;
- invalid `activity` namespace;
- invalid `harness` namespace;
- invalid or unknown key inside `harness.devin`;
- invalid hook return type;
- missing required input for expected output calculation.

## Security requirements

- Adjacent JSON is git-tracked and must not contain credentials or PII.
- Keep `auto` as the default permission mode.
- Require explicit `accept-edits` for unattended artifact-writing Activities.
- Treat `dangerous`, `bypass`, `smart`, and `autonomous` as explicit reviewed choices.
- `autonomous` requires sandbox support and must not be emitted without the required CLI combination.
- Use an argument list with `subprocess.run`; never construct a shell command string.
- Validate path-valued options before command construction.
- Do not support arbitrary `extra_args` in the initial design because it bypasses typed validation and makes security review ineffective.

## File changes

### Add

- `src/orchestrator/skill_activity_config.py`
- adjacent `*.config.json` for each concrete Activity
- tests for configuration loading, template order, every hook, and namespaced Harness translation

### Replace or substantially refactor

- `src/orchestrator/skill_activity.py`
- `src/orchestrator/harness.py`
- `src/orchestrator/devin_harness.py`
- `src/orchestrator/activities/extract_story_intent.py`
- `src/orchestrator/activities/analyze_story.py`
- `src/orchestrator/activities/grade_story_analysis.py`
- `src/orchestrator/activities/repair_story_analysis.py`
- `src/orchestrator/tests/test_skill_activity.py`
- `src/orchestrator/tests/test_devin_harness.py`

### Remove after migration

- skill-name branches in `_conventional_output_path`;
- invocation-context-based profile selection in `DevinHarness`;
- centralized per-skill entries in `devin_harness.config.json`;
- legacy `run_skill` function once all callers use `SkillActivity.execute`;
- `DevinHarnessConfig.resolve(skill_name)` once no compatibility caller remains.

### Retain

- `SkillActivityInput`, unless a later contract change removes `skill_name` after full migration;
- `SkillActivityOutput` wire shape;
- `HarnessResult` wire shape;
- `skill_invocation_context` for observability and nested invocation scope;
- Cadence Activity wire names and argument/result shapes.

## Migration sequence

### Phase 1: characterize current behavior

1. Preserve existing tests as characterization tests.
2. Add tests for all four output naming conventions.
3. Add tests that prove stale sentinel, logging, and context cleanup order.
4. Record current Harness command behavior.

### Phase 2: expand the Harness boundary

1. Add namespaced configuration to `Harness.run`.
2. Update `DevinHarness`, fake Harnesses, and all direct callers atomically.
3. Move command translation to a fresh per-invocation builder.
4. Retain central config temporarily as defaults.

### Phase 3: introduce the template

1. Add the base `SkillActivity` with a fixed `execute` method.
2. Add typed no-op hooks.
3. Move prompt, sentinel, context, timing, validation, and output lifecycle into the template.
4. Port one representative Activity, preferably `analyze_story`.
5. Compare old and new output and logging behavior.

### Phase 4: colocate configuration

1. Add and validate `analyze_story.config.json`.
2. Make adjacent values override temporary central defaults.
3. Port the remaining three Activities one at a time.
4. Remove corresponding central skill entries after each migration is proven.

### Phase 5: remove compatibility paths

1. Remove `run_skill` and skill-name output branches.
2. Remove central per-skill resolution.
3. Require the new Harness signature.
4. Update README and operational documentation.
5. Mark ADR-012 partially superseded with the accepted replacement decision.

Do not combine these phases with moving Activities into workflow-specific packages. First preserve behavior under the new interface; then perform the package-boundary refactor.

## Test requirements

### Configuration tests

- same-stem config path is selected;
- missing, unreadable, malformed, and wrong-typed config fails clearly;
- required Activity fields are enforced;
- mappings are immutable;
- constructor test overrides have documented precedence;
- no raw configuration appears in logs.

### Harness contract tests

- config mapping reaches the selected Harness unchanged;
- `DevinHarness` consumes only `devin`;
- sibling namespaces are ignored;
- unknown `devin` keys are rejected;
- model, permission, sandbox, and config path render correctly;
- default command remains least privilege;
- no arbitrary key becomes a CLI flag;
- a fresh command list is built for every invocation.

### Template tests

- template stages execute in documented order;
- every base hook returns the same object or equal value unchanged;
- every hook can replace its value with the same type;
- invalid hook return types fail before Harness invocation where possible;
- invocation context is reset on Harness exceptions;
- stale sentinel is removed before invocation;
- sentinel result wins over fallback convention;
- missing sentinel uses concrete expected output;
- malformed and mismatched sentinels fail;
- nonzero exit remains sanitized;
- result shape remains backward compatible.

### Concrete Activity tests

For each Story Analysis Activity:

- Cadence wire name is unchanged;
- canonical skill name comes from adjacent configuration;
- output key matches the skill sentinel contract;
- expected output convention matches current behavior;
- write-capable invocation uses explicit `accept-edits`;
- function arguments and returned dictionary remain unchanged.

### Integration verification

1. Start the local Worker and Cadence stack.
2. Run each supported Activity through `SingleActivityWorkflow`.
3. Confirm effective model and permission logging.
4. Confirm artifacts and output paths.
5. Run the complete Story Analysis workflow.
6. Confirm Cadence retries use a stable Worker-loaded configuration snapshot.

## Acceptance criteria

- Each concrete Skill Activity has an adjacent JSON configuration.
- Adding a new Activity requires no edit to a central skill-name switch or Devin profile map.
- `Harness.run` receives an immutable namespaced configuration mapping.
- `DevinHarness` alone validates `devin` settings and translates them to CLI arguments.
- Unknown keys inside `devin` fail; unrelated Harness namespaces are ignored.
- `SkillActivity.execute` owns and preserves the complete lifecycle order.
- Prompt, sentinel path, Harness config, invocation context, output path, and result have typed no-op transformation hooks.
- Required identity and output contract fields fail at construction/startup rather than after invocation.
- Existing Activity wire names, argument shapes, output shape, sentinel validation, logging hygiene, and retry behavior remain compatible.
- All unit and live integration checks pass before removing the old interface.

## Open decisions for implementation planning

- Whether `skill_name` remains in `SkillActivityInput` or moves entirely into immutable Activity configuration.
- Whether adjacent config absence is always fatal or a test-only constructor may omit it.
- Whether the initial `DevinHarness` supports only model and permission mode or also sandbox/config path.
- Whether configuration JSON receives a formal JSON Schema in the first implementation.
- Whether hook return types are checked at runtime or only through static typing and tests.
- Whether a future operational override layer is needed and how its snapshot enters Cadence history.

## Source references

- `src/orchestrator/skill_activity.py` — current `run_skill` lifecycle and skill-specific fallback.
- `src/orchestrator/harness.py` — current Harness protocol.
- `src/orchestrator/devin_harness.py` — current profile resolution and Devin CLI construction.
- `src/orchestrator/invocation_context.py` — current context manager.
- `src/orchestrator/activities/` — concrete Activity wrappers.
- `src/orchestrator/tests/test_skill_activity.py` — current lifecycle characterization.
- `src/orchestrator/tests/test_devin_harness.py` — current configuration and command behavior.
- `vault/decisions/ADR-004-skill-output-contracts.md` — sentinel and output contract.
- `vault/decisions/ADR-012-skill-activity-invocation-configuration.md` — configuration behavior this design partially supersedes.
