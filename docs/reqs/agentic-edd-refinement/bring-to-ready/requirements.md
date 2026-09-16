# Bring Agentic EDD Refinement to Ready

## Bottom line

The Agentic EDD Refinement implementation is ready for use only when a requester can start a durable, multi-iteration run from a validated input document against an existing local target repository, observe its status, and receive a terminal audit record with the repository at its best accepted state.

This document closes the integration and operability gaps that remain after implementing the individual EDD refinement Activities and unit-level workflow branches.

## Status

- Requirements captured: 2026-09-15
- Implementation status: not ready
- Source feature: `docs/reqs/agentic-edd-refinement/feature-description.md`
- Input example: `docs/reqs/agentic-edd-refinement/edd_input.example.json`
- Required-test example: `docs/reqs/agentic-edd-refinement/test-cases.example.yaml`

## User story

So that an engineer can safely improve an existing skill through evaluation-driven refinement

As a workflow requester

I want to start the EDD refinement workflow from one portable input document, have every operation run against the intended target repository, and receive durable progress and terminal evidence

So that the workflow is usable as an exposed capability rather than only as a collection of internal Activities.

## Goals

1. Define and validate the public EDD refinement input contract.
2. Resolve the target Git worktree from the supplied skill folder.
3. Run evaluation and inspection commands supplied by the target repository.
4. Execute a real bounded refinement loop rather than one refinement attempt.
5. Hold repository mutation ownership for the complete mutating run.
6. Expose the workflow through the orchestrator catalog, a Python client, and a kickoff script.
7. Prove the integrated capability against a separate local target repository.

## Confirmed decisions

### Target repository

- `skill_folder` is the repository anchor.
- Relative paths in the input resolve from the input document's parent directory.
- Preflight resolves the nearest Git worktree containing the canonical skill folder.
- The resolved Git worktree is the immutable target repository for the run.
- Every repository-scoped input must resolve inside that worktree after symlink resolution.
- Evaluation, inspection, agent, file, and Git commands run with the target repository as their working directory.

### Progress artifacts

- Progress artifacts are colocated with the input document under:

  ```text
  <input-parent>/.process/edd/<run-id>/
  ```

- Preflight checks repository cleanliness before creating the run artifact directory.
- The workflow may exclude only its exact run-owned artifact directory from later candidate-diff and cleanliness checks.
- An exclusion must not hide unrelated staged, unstaged, or untracked files.
- If the input document is outside the target repository, every worker executing the run must still have access to both the target worktree and artifact location.

### Evaluation provider

- The EDD input does not contain a provider field.
- Provider configuration belongs to the target repository's evaluation configuration.
- Preflight inspects the resolved evaluation configuration and requires exactly one execution provider for the run.
- The workflow snapshots provider identity from the resolved configuration so baseline and candidate evaluations remain comparable.
- Credentials and secret environment values are never copied into the progress record.

### Timeouts

- `eval_timeout_seconds` is part of the EDD input because evaluation duration is suite-specific.
- Workflow, general Activity, and approval timeouts use the deployed Cadence and workflow-module configuration.
- Absence of a human approval before the configured approval timeout never implies approval.
- Iteration and token limits remain requester-supplied refinement limits.

### Git commits

- The EDD input does not define Git author or committer identity.
- Accepted changes follow the repository's `git-commit` skill and repository commit conventions.
- Commit messages identify the EDD refinement purpose and relevant run or iteration evidence without adding AI/tool attribution.
- The workflow fails safely when the target repository lacks the Git configuration required to create an accepted commit.

## Public input contract

The public request is a versioned JSON document. The initial implementation must support the shape demonstrated by `edd_input.example.json`.

| Property | Required | Contract |
|---|---:|---|
| `skill_folder` | Yes | Path to the existing target skill folder and anchor for Git-root discovery. |
| `eval_config` | Yes | Path to the authoritative evaluation-tool configuration. |
| `related_content` | No | Paths to supporting content the planner may inspect. |
| `test_command` | Yes | Argument vector that runs the complete evaluation suite. |
| `inspect_command` | Yes | Argument vector that emits structured results for the completed evaluation. |
| `test_cases` | Yes | Path to the structured required-test-case document. |
| `coverage_metadata_property` | Yes | Dotted property path used to map evaluation metadata to required test-case IDs. |
| `modification_scope` | Yes | Non-empty list of files or directories the refiner may modify. |
| `limits.max_iterations` | Conditional | Maximum logical refinement iterations; required when no token limit is supplied. |
| `limits.max_tokens` | Conditional | Maximum cumulative observed agent tokens; required when no iteration limit is supplied. |
| `limits.eval_timeout_seconds` | Yes | Start-to-close bound for one logical evaluation attempt. |

### Input validation

The request is rejected before agent invocation when any of the following is true:

1. The JSON is malformed or does not satisfy the versioned request schema.
2. `skill_folder` does not exist, is not a directory, or is not inside a Git worktree.
3. `eval_config`, `test_cases`, or any required related path does not exist.
4. A repository-scoped path escapes the resolved target worktree.
5. `test_command` or `inspect_command` is empty or contains non-string arguments.
6. `modification_scope` is empty or includes a path outside the target worktree.
7. Both `max_iterations` and `max_tokens` are absent or non-positive.
8. `eval_timeout_seconds` is absent or non-positive.
9. The required-test-case document is malformed or contains duplicate or missing IDs.
10. `coverage_metadata_property` is empty or cannot be evaluated as a dotted metadata path.
11. The evaluation configuration resolves zero or multiple execution providers.
12. The target worktree is not clean before run-owned artifacts are created.

## Required test-case contract

The required-test-case document is YAML with a top-level list of groups. Each group contains a non-empty `tests` list.

Each test case contains:

- `id`: required, unique, stable string such as `TC-001`;
- `description`: required non-empty summary;
- `given`: required non-empty list of conditions;
- `when`: required non-empty action;
- `then`: required non-empty list of expected outcomes.

The workflow normalizes the document into an immutable set of required test-case IDs and descriptions at run start. Refinement may add evaluation coverage for these cases but may not silently remove a required case from the request contract.

## Coverage metadata contract

Promptfoo and equivalent evaluation tools may attach metadata to individual evaluations. The requester identifies the metadata location with `coverage_metadata_property`.

For the example value:

```json
"coverage_metadata_property": "metadata.covers_test_case_ids"
```

an evaluation result associates itself with required tests as follows:

```yaml
metadata:
  covers_test_case_ids:
    - TC-001
    - TC-004
```

Requirements:

1. The resolved property value is a non-empty string or list of strings.
2. Every referenced ID exists in the required-test-case document.
3. One evaluation may cover multiple required cases.
4. Multiple evaluations may cover one required case.
5. Disabled or skipped evaluations do not establish active coverage.
6. Unknown IDs make the candidate evidence invalid rather than being ignored.
7. Missing metadata means that evaluation establishes no required-case coverage.
8. A coverage improvement requires at least one previously uncovered required ID to become covered by an enabled evaluation with enforceable assertions.
9. Merely duplicating an existing ID does not qualify as meaningful coverage growth.

## Evaluation and inspection command contract

### Command execution

- Commands are argument arrays and execute without shell interpolation.
- Commands execute from the resolved target repository root.
- The environment may supply credentials, but command arguments and progress artifacts must not expose them.
- The evaluation Activity applies `eval_timeout_seconds`, cancellation, and configured retry policy.
- A physical Activity retry does not create another logical refinement iteration.

### Evaluation handoff

The evaluation command must make the completed evaluation identity available to the workflow. The implementation may use structured stdout, an Activity return value, or another deterministic adapter, but it must identify the exact completed evaluation rather than infer "latest" state.

### Inspection

- `inspect_command` is supplied by the target repository.
- The workflow invokes it for the exact evaluation produced by the corresponding `test_command` execution.
- The command must support a deterministic way to receive that evaluation identity.
- The command emits machine-readable JSON for all passing, failing, and errored evaluations.
- The emitted records preserve the metadata addressed by `coverage_metadata_property`.
- Human-oriented truncation may apply to console summaries but not to fields needed for metric, failure, assertion, or coverage extraction.
- Selecting the latest evaluation is permitted for interactive human use but is not permitted for workflow result attribution.

### Structured result minimum

The inspector output must provide enough information to derive:

- evaluation identity;
- result status: pass, fail, skipped, timeout, or error;
- total enabled evaluation count;
- passing and failing counts;
- assertion outcomes and failure reasons;
- test description or stable result identity;
- metadata used for required-case coverage;
- provider identity as resolved by the evaluation tool;
- artifact references when available.

## Durable workflow behavior

### Workflow-owned preflight

- The public workflow input is the input-document path and optional workflow ID, not a Python `PreflightResult` object.
- The workflow schedules preflight as an Activity.
- Preflight resolves, validates, and snapshots the target repository and normalized request.
- No client or kickoff script constructs trusted repository context on the workflow's behalf.

### Run-lifetime mutation lease

- Successful preflight acquires a mutation lease associated with the target repository identity and workflow run.
- The lease remains held across all mutating iterations, waits, retries, and worker restarts.
- Long-running runs renew or heartbeat the lease before expiration.
- A competing mutating run cannot begin while the lease is valid.
- Finalization releases the lease on every terminal outcome.
- Failure to release is recorded and surfaced for operator recovery.

### Refinement loop

After a successful baseline, the workflow repeats:

1. Check durable limits and unresolved evidence.
2. Plan exactly one authorized action or stop.
3. Obtain human approval when required.
4. Execute one action.
5. Validate the candidate diff and modification scope.
6. Evaluate and inspect the candidate.
7. Compare it with the best accepted state.
8. Commit an improvement, reject no-value work, or confirm and recover a regression.
9. Persist counters, evidence, and the next durable phase.
10. Continue until a terminal condition is reached.

A branch that records `next_state: planning` must actually schedule another planning cycle. Returning a next-state label without continuing the durable workflow is insufficient.

### Resume behavior

On replay, retry, or worker restart, the workflow resumes from the persisted logical phase. It must not:

- recreate the run record;
- rerun a completed agent action;
- attribute a different evaluation to the candidate;
- abandon a persisted candidate merely because it exists;
- lose approval proposal identity or timeout state;
- reset iteration, token, or confirmed-regression counters;
- redirect work to another repository.

Continue-As-New may be used when needed, provided the normalized request, repository context, lease identity, progress reference, best accepted state, pending evidence, and counters are carried forward.

## Exposure requirements

### Workflow catalog

The orchestrator catalog includes:

```text
edd_refinement_workflow.module
```

Catalog inspection reports:

- workflow type `EddRefinementWorkflow`;
- domain `edd-refinement`;
- task list `edd-refinement`;
- every registered Activity wire name.

Workflow-engine startup registers the domain, starts the module worker, and verifies a poller for the EDD task list.

### Python starter and CLI

The EDD workflow package exposes a starter and CLI consistent with the existing Story Analysis workflow.

Required commands:

```text
edd-refinement-cli start <input-document>
edd-refinement-cli query <workflow-id> [--run-id <run-id>]
edd-refinement-cli approve <workflow-id> <proposal-id> [--run-id <run-id>]
edd-refinement-cli reject <workflow-id> <proposal-id> [--run-id <run-id>]
```

The start command:

1. resolves the input document to an absolute path;
2. validates its basic schema before contacting Cadence;
3. creates or accepts a stable workflow ID;
4. starts `EddRefinementWorkflow` on the configured EDD task list;
5. prints workflow and run IDs.

The query command returns machine-readable current phase, limits, latest metrics, pending approval or regression evidence, progress path, and terminal result when available.

### Kickoff script

Provide:

```text
scripts/kickoff-edd-refinement.sh <input-document>
```

The script follows the repository's existing kickoff conventions:

- requires exactly one input document;
- resolves it to an absolute path;
- verifies that the repository virtual environment is available;
- executes the EDD CLI through `nix-shell`;
- preserves safe argument quoting;
- returns a non-zero status for invalid input or startup failure.

## Finalization requirements

Every terminal path:

1. restores or confirms the target repository at the best accepted state;
2. publishes a terminal progress record beside the input document;
3. includes baseline and final metrics, coverage, attempts, accepted commits, rejected or reverted proposals, token usage, pending human evidence, and terminal reason;
4. identifies the target repository and final accepted revision;
5. releases the mutation lease or reports release failure;
6. returns a serializable workflow result.

A validation, baseline, command, infrastructure, or commit failure before the first accepted change still produces a terminal record when the artifact location is writable.

## Acceptance criteria

### AC-1: Start from the input document

Given a valid EDD input document and an existing clean skill repository

When the requester invokes `scripts/kickoff-edd-refinement.sh`

Then the CLI starts `EddRefinementWorkflow` and prints its workflow and run IDs.

### AC-2: Derive the repository from the skill

Given `skill_folder` is relative to the input document

When preflight resolves it

Then the nearest containing Git worktree becomes the immutable target root and every scoped path is validated against it.

### AC-3: Reject path escape

Given any input path resolves outside the target worktree through traversal or symlink resolution

When preflight validates the request

Then the workflow rejects it before invoking an agent or evaluation command.

### AC-4: Use the evaluation configuration provider

Given `eval_config` resolves exactly one provider

When baseline and candidate evaluations run

Then both use that provider and the progress record captures its non-secret identity.

Given the configuration resolves zero or multiple providers

Then preflight rejects the request.

### AC-5: Inspect the exact evaluation

Given an evaluation command completes and returns an evaluation identity

When result inspection runs

Then `inspect_command` receives that identity and the workflow does not infer the most recent evaluation.

### AC-6: Calculate required coverage

Given inspector results contain IDs at the configured `coverage_metadata_property`

When metrics are extracted

Then covered and uncovered required test-case IDs are calculated from enabled evaluations and unknown IDs invalidate the evidence.

### AC-7: Enforce evaluation timeout

Given an evaluation exceeds `limits.eval_timeout_seconds`

When Cadence times out the Activity

Then the attempt is recorded, retry policy is applied, and no duplicate logical iteration is created.

### AC-8: Hold the lease for the run

Given preflight succeeds

When the workflow waits, retries, or advances through multiple iterations

Then its repository lease remains valid until finalization and blocks another mutating run against the same target.

### AC-9: Execute multiple iterations

Given the first candidate is accepted and limits permit more work

When its commit and state update complete

Then the workflow schedules another planning cycle rather than returning after one attempt.

### AC-10: Resume a persisted candidate

Given a worker restarts after candidate execution but before comparison

When Cadence replays the workflow

Then it resumes evaluation or comparison for the same candidate without rerunning the agent action.

### AC-11: Expose the worker

Given the EDD module is present in the workflow catalog

When the workflow engine starts

Then catalog inspection includes the EDD topology and a worker polls the `edd-refinement` task list.

### AC-12: Follow repository commit conventions

Given a candidate qualifies for acceptance

When the workflow commits it

Then the commit follows the target repository's applicable rules and the `git-commit` skill conventions without requiring identity fields in the input.

### AC-13: Publish colocated progress

Given an input document at `<parent>/edd-input.json`

When the run initializes

Then its progress record is published under `<parent>/.process/edd/<run-id>/` without allowing that run-owned path to hide unrelated changes.

### AC-14: Finalize every terminal branch

Given any successful, rejected, timed-out, failed, or human-handoff terminal outcome

When the workflow terminates

Then it publishes a terminal record, leaves the target at the best accepted state, and releases or reports failure to release the lease.

### AC-15: Prove an external target run

Given the orchestration repository and target skill repository are different local Git worktrees

When an end-to-end EDD run is executed

Then all skill, evaluation, inspection, artifact, and Git operations use the intended target and input locations, and the orchestration worktree remains unchanged.

## Verification requirements

Readiness requires automated evidence at four levels:

1. **Schema tests**
   - valid example input and required-test documents pass;
   - malformed commands, limits, IDs, metadata paths, and escaped paths fail.
2. **Workflow tests**
   - accepted, no-value, approval, confirmed-regression, flaky, timeout, and budget branches continue or finalize correctly;
   - replay resumes each durable phase without duplicate side effects.
3. **Catalog and CLI integration tests**
   - catalog loading imports and registers EDD;
   - CLI serialization starts the workflow with a document path;
   - query and approval commands address the correct execution.
4. **End-to-end Cadence test**
   - a real local Cadence service and worker operate on a temporary external Git worktree;
   - at least two logical iterations execute or one iteration followed by a terminal plan;
   - evaluation identity is handed to the inspector;
   - progress publication, accepted state, and lease release are verified.

## Definition of ready

The feature is ready when all acceptance criteria have automated evidence, the EDD module starts from the production workflow catalog, the example input starts a real run through the kickoff script, and an external target-repository test demonstrates durable refinement and safe finalization.

Unit tests for individual Activities alone do not satisfy readiness.
