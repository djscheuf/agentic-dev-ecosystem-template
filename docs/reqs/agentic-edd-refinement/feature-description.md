# Agentic Evaluation-Driven Development Refinement

## Feature Summary

Provide a bounded, durable Cadence workflow that automatically improves the evaluation-driven development (EDD) test suite and implementation of an existing skill. The workflow establishes a measurable baseline, selects one permitted refinement action at a time, evaluates the resulting repository state with promptfoo, and operates as a quality ratchet: it commits only measured improvements and removes confirmed regressions. It stops when its configured iteration or token budget is exhausted, no justified action remains, or three consecutive proposed changes produce confirmed regressions.

The workflow is intended to improve an existing skill, not bootstrap a skill with no evaluation suite.

## Story

So that an existing skill and its evaluation suite can improve through repeatable, evidence-based iteration

As a software engineer or AI process designer responsible for skill quality

I want a bounded agentic workflow that proposes and applies controlled refinements, evaluates every change against user-supplied test cases, and preserves an auditable record of its decisions and results

## Business Value

- Turns EDD refinement into a repeatable process rather than an open-ended agent session.
- Preserves human control over changes that redefine evaluation expectations.
- Makes improvement claims traceable to baseline and post-change evaluation evidence.
- Limits cost and execution time through explicit budgets and Activity timeouts.
- Produces durable progress state that can survive worker or process interruption.

## Actors

### Workflow Requester

A technically proficient user who owns or maintains an existing skill and can provide its evaluation command, required test cases, provider configuration, and execution limits.

### Automatic Refiner

An agent operating inside the Cadence workflow. It may inspect the current state, choose among permitted actions, and modify only the authorized skill and evaluation scope.

### Human Approver

A user authorized to accept or reject a proposed change to evaluation definitions, especially LLM-graded rubrics. Human approval is required before such a change is applied or retained.

## Preconditions

The workflow must reject the request during preflight unless all of the following are true:

1. The target skill already exists.
2. The target skill already has an evaluation suite.
3. The requester supplies a non-empty set of required test cases for use during refinement.
4. The complete evaluation suite can be invoked deterministically through a requester-supplied command.
5. The promptfoo evaluation resolves to exactly one execution provider for the entire refinement run.
6. A maximum iteration count, cumulative token budget, or both are supplied.
7. The workflow can identify the files that the refiner is allowed to modify.
8. The repository begins in a state that permits changes made by this workflow to be isolated from unrelated work.
9. The evaluation output exposes enough structured data to calculate the configured score and determine pass, fail, timeout, or execution error.
10. The workflow has a configured timeout for each long-running evaluation Activity.

Preflight must have no refining side effects. On failure, it reports every failed condition and does not create a refinement commit.

## Proposed Input Template

The initial contract should capture the following information. Exact field names and JSON Schema remain an implementation-design decision.

| Input | Required | Purpose |
|---|---:|---|
| Target skill identifier or path | Yes | Selects the existing skill to refine. |
| Evaluation configuration path | Yes | Identifies the existing promptfoo suite. |
| Evaluation command | Yes | Provides the deterministic CLI invocation for the complete suite. |
| Required test cases | Yes | Defines scenarios that must be present or added and must remain exercised throughout the run. |
| Authorized file scope | Yes | Limits which skill, support-document, scripted-check, and evaluation files may change. |
| Single provider identifier | Yes | Pins the only promptfoo execution provider permitted during the run. |
| Evaluation metric mapping | Yes | Defines how structured results expose passing, failing, and total evaluations and required test-case coverage for ratchet comparison. |
| Evaluation timeout | Yes | Bounds each promptfoo evaluation Activity, expected to accommodate suites that may run for 10–20 minutes. |
| Maximum iterations | Conditional | Bounds the number of refinement loops. Required if no token budget is supplied. |
| Cumulative token budget | Conditional | Bounds aggregate agent usage. Required if no iteration limit is supplied. |
| Per-agent-step token limit | No | Optionally bounds an individual agentic invocation. |
| Coverage adequacy criteria | Yes | Defines when evaluations adequately cover each required test case and prevents duplicate test growth from qualifying as improvement. |
| Commit policy and identity | Yes | Defines whether and how deterministic commits are created for accepted improvements. |
| Human approval timeout | Yes | Bounds how long a run may wait for an evaluation-change decision. |
| Working artifact location | Yes | Selects where the schema-versioned progress JSON is published. |

## Authorized Refinement Actions

After each evaluation, an agentic planning step selects exactly one next action from this closed set:

1. **Add or extend evaluation coverage**
   - Add a missing required test case.
   - Extend deterministic or scripted assertions without weakening existing expectations.
2. **Repair scripted evaluation checks**
   - Correct defects in custom checks, transforms, fixtures, or evaluation plumbing.
   - A repair must preserve the intended requirement rather than make a failing output pass by lowering the bar.
3. **Refine the skill**
   - Modify the target skill instructions or implementation to improve behavior against the suite.
4. **Refine supporting skill documents**
   - Modify authorized examples, references, templates, or other documents used by the target skill.
5. **Propose an evaluation expectation change**
   - Clarify an ambiguous or defective evaluation, particularly an LLM rubric.
   - The proposal must explain why the current expectation is defective, identify the exact change, and predict its scoring effect.
   - No evaluation expectation change may be applied or committed without direct human approval.
6. **Stop**
   - Select when no justified action remains, the objective is met, or a limit prevents another safe iteration.

Any action outside this set, or any file change outside the authorized scope, fails the iteration and is not retained.

## Quality Ratchet

The workflow's fundamental responsibility is to move the accepted repository state forward without committing a measured degradation. Every candidate is compared with the current best accepted state, not only with the original baseline.

A candidate qualifies as an improvement in either of two ways, in priority order:

1. **Passing-evaluation improvement:** the number of passing evaluations increases without reducing required test-case coverage.
2. **Meaningful coverage improvement:** the evaluation suite adds assertions or scenarios needed to cover one or more previously uncovered required test cases, while preserving at least the prior number of passing evaluations.

Passing-evaluation improvement is preferred. Meaningful coverage improvement is valuable even when the larger denominator lowers the pass percentage, provided the absolute passing count does not decrease. Adding evaluations when every required test case is already adequately covered is not an improvement by itself and does not qualify for a commit.

The ratchet comparison therefore tracks at least:

- absolute number of passing evaluations;
- absolute number of failing evaluations;
- total enabled evaluation count;
- pass percentage as a diagnostic measure, not the sole acceptance criterion;
- required test cases covered and uncovered;
- whether newly added coverage is meaningful relative to the supplied test cases;
- the current best accepted commit and its evaluation evidence.

A change is never accepted merely because it increases the denominator, rearranges tests, duplicates existing coverage, or weakens an expectation. When evaluation expectations change with human approval, the workflow must preserve separate before-change and after-change measurement contexts rather than treating the scores as directly comparable.

## Workflow Outline

### 1. Preflight

A deterministic Activity validates all entry conditions, normalizes the request, verifies single-provider use, confirms the evaluation command and score parser, and records the resolved limits. It must distinguish invalid input from infrastructure failure.

### 2. Initialize Progress Record

Create a schema-versioned JSON progress document containing:

- workflow and run identity;
- normalized inputs and authorized scope;
- provider and evaluation command identity;
- iteration and token limits;
- evaluation metric mapping and coverage adequacy criteria;
- current lifecycle state;
- empty iteration history;
- cumulative token usage and consecutive confirmed-regression count initialized to zero.

Secrets, credentials, and sensitive environment values must not be written to this document.

### 3. Establish Baseline

Invoke the complete promptfoo suite through a deterministic evaluation Activity. Record the baseline passing, failing, total, percentage, and required-coverage metrics together with failures, evaluation artifact references, duration, and outcome. The workflow does not begin refinement if the baseline cannot be evaluated successfully.

### 4. Determine the Next Action

Invoke a generic prompt-based agentic Activity with the current progress record, latest evaluation evidence, authorized action set, required test cases, and remaining budgets.

The result must be structured and include:

- selected action type;
- rationale and evidence;
- intended files or file classes;
- expected effect;
- whether human approval is required;
- stop recommendation when no defensible action remains.

A generic prompt invocation is preferred over a fixed skill invocation because the planner must select among several action types. Purpose-built skills may still implement individual selected actions.

### 5. Obtain Human Approval When Required

If the selected action changes evaluation expectations, pause durably for explicit approval. Approval must bind to the exact proposed diff or a stable proposal identifier. Rejection returns the workflow to planning or stops it; silence never implies approval.

### 6. Execute One Refinement Action

Invoke the Activity appropriate to the selected action. Each agentic invocation returns structured usage metrics and a list of changed files. The workflow validates that the resulting diff matches the approved action and authorized file scope.

### 7. Evaluate the Candidate State

After any modifying agentic Activity completes, invoke the same deterministic promptfoo command used for the baseline. Apply the configured Activity timeout and capture structured results.

The evaluation Activity is a side-effecting, retryable Cadence Activity, not workflow code. Its retry and timeout policy must avoid accidentally treating two physical attempts as two logical refinement iterations.

### 8. Compare, Confirm, and Decide

Compare the candidate result to the current best accepted state using the quality-ratchet rules.

- **More passing evaluations:** accept when required test-case coverage is not reduced. Record the improvement, commit deterministically, reset the consecutive-regression counter to zero, and make the candidate the new current-best state.
- **Meaningfully extended coverage:** accept when the candidate covers previously uncovered required test cases and preserves the prior absolute passing count. Record that the lower pass percentage, if any, results from valuable added coverage; commit deterministically; reset the consecutive-regression counter; and make the candidate the new current-best state.
- **No meaningful improvement:** do not commit. Record why the candidate adds no qualifying value and return to planning or stop according to policy.
- **Apparent regression:** do not immediately revert or commit. Run the complete evaluation suite a second time against the same unchanged candidate state.
- **Evaluation error or timeout:** record the failed execution, apply the configured retry policy, and stop or continue only if budgets and policy permit. An infrastructure error is not by itself evidence of a product regression.

The second candidate run classifies an apparent regression:

1. **Confirmed regression:** the second run also performs worse than the current best state. Record both degraded results and the candidate-change summary, increment the consecutive confirmed-regression counter, restore the last accepted repository state, and rerun the complete suite to verify recovery before another proposal is allowed.
2. **Not reproduced:** the second run returns to or exceeds the current best state. Treat the result as unstable rather than as a confirmed improvement. Record both results and punch out to a human; do not commit or revert the candidate until the human decides how to classify it.
3. **Inconclusive:** the second run errors, times out, or differs in a way that does not establish stable equivalence, improvement, or regression. Record the evidence as suspected flakiness and punch out to a human; do not continue autonomous refinement.

After reverting a confirmed regression, the recovery evaluation must demonstrate that the accepted state has returned to its previously recorded performance. If recovery cannot be verified, stop autonomous refinement and hand off to a human. A reverted proposal, its change summary, affected files, rationale, observed degradation, confirmation result, and recovery result remain in the progress record so later planning Activities can avoid repeating the same unsuccessful approach.

Passing newly added tests is not sufficient when they duplicate already-covered test cases or reduce the absolute passing count. Evaluation changes approved by a human must still be reported separately so that an apparent score increase caused by changed measurement is not conflated with an implementation improvement.

### 9. Check Limits and Continue

Before scheduling another agentic or evaluation Activity, check:

- accepted objective or stop recommendation;
- three consecutive confirmed-regression proposals;
- maximum iterations;
- cumulative token usage;
- remaining per-step token allowance;
- human approval deadline;
- unresolved flaky or inconclusive evaluation evidence;
- unverified recovery after a revert;
- unrecoverable workflow or repository errors.

If three consecutive proposed changes have each produced a confirmed regression, stop immediately regardless of the remaining iteration or token budget. Publish a human handoff report describing the three attempted changes, their rationale, files affected, measured degradations, evaluation evidence, reverts, recovery checks, and total resource spend.

If another step could exceed a known hard limit, do not schedule it. If actual usage causes the cumulative token total to meet or exceed the budget, record that fact and stop before the next agentic step.

For long histories, the Cadence implementation may use Continue-As-New while carrying forward the normalized request, best score, cumulative usage, accepted commit, and progress-record reference.

### 10. Finalize

Publish a terminal progress record and workflow result containing:

- baseline and final accepted pass, fail, total, percentage, and required-coverage metrics;
- absolute passing-count, evaluation-count, coverage, and percentage changes;
- terminal reason, including whether three consecutive confirmed regressions stopped the loop;
- accepted iteration and commit references;
- rejected or reverted iteration summaries and semantic change descriptions;
- degradation confirmation and post-revert recovery evidence;
- cumulative token usage and iteration count;
- pending or resolved human decisions and flaky-result evidence;
- evaluation artifact references.

The terminal repository state must correspond to the best accepted state, not merely the last attempted state.

## Progress Record Requirements

The JSON progress document is the audit view of the logical refinement run. Cadence history remains the durable orchestration source of truth; the document is a deterministic, human- and machine-readable projection.

Each iteration record must include at least:

- iteration number and timestamps;
- starting and candidate pass counts, fail counts, totals, pass percentages, and required test-case coverage;
- selected action, rationale, and a brief semantic summary of the proposed changes;
- approval requirement, proposal identity, and decision when applicable;
- agentic invocation identity;
- files changed;
- evaluation command/config/provider identity;
- first candidate evaluation status, metrics, failures, and artifact references;
- second candidate evaluation evidence when an apparent regression requires confirmation;
- regression classification: not applicable, confirmed, not reproduced, or inconclusive;
- revert status and post-revert recovery evaluation evidence when applicable;
- consecutive confirmed-regression count;
- prompt, completion, cached, and total tokens when available;
- cumulative token usage;
- commit reference when accepted;
- disposition: accepted-pass-improvement, accepted-coverage-improvement, no-improvement, confirmed-regression, awaiting-human-flakiness-decision, reverted, recovery-failed, timed out, errored, or stopped.

Updates must be atomic, schema-validated, and idempotent for a workflow run and logical iteration. Missing usage must be represented as unavailable rather than estimated.

## Cadence Responsibilities

### Workflow Code

- Own deterministic control flow, iteration state, budget checks, score comparisons, and stop conditions.
- Never invoke the CLI, inspect Git, access files, or call an agent directly.
- Wait durably for human approval through a Signal and expose current status through a Query.
- Carry logical iteration identity across Activity retries.

### Activities

Activities perform all side effects, including:

- preflight inspection;
- progress-record publication;
- prompt or skill invocation;
- repository diff inspection and scope validation;
- promptfoo CLI execution and result parsing;
- deterministic Git commit creation;
- restoration of the last accepted working state;
- final report publication.

Long-running promptfoo Activities must use explicit start-to-close timeouts, heartbeat while work is active when practical, honor cancellation, and return artifact references rather than oversized raw output. Activities that mutate files or create commits must be idempotent under retry.

## Guardrails and Invariants

- Exactly one promptfoo execution provider is used for all comparable evaluations in a run.
- The baseline and candidate evaluations use the same command, configuration, provider, metric mapping, coverage criteria, and required test set unless an exact evaluation change receives human approval.
- The refiner cannot silently remove, skip, weaken, or rewrite a failing test to improve its score.
- Required user-supplied test cases remain present and enabled for every accepted state.
- Evaluation/rubric changes are never auto-approved.
- Only authorized files may change.
- Every accepted repository state has evaluation evidence and a deterministic commit.
- A candidate is accepted only by increasing the absolute passing count without losing required coverage, or by adding meaningful missing test-case coverage without reducing the absolute passing count.
- Increasing evaluation count without covering a previously uncovered required test case is not a qualifying improvement.
- An apparent regression is evaluated a second time against the unchanged candidate before it is classified.
- A confirmed regression is reverted and the restored accepted state is reevaluated before autonomous refinement continues.
- An unrepeatable or inconclusive degradation requires human review; the workflow does not guess whether it is flaky.
- Failed proposal summaries remain visible to future planning steps so the agent does not repeat a known harmful approach.
- Three consecutive confirmed-regression proposals terminate the loop even when other budgets remain.
- A retry of an Activity does not consume an additional logical iteration, though its actual token usage must still count toward the cumulative budget when observable.
- The workflow never claims improvement when scores are incomparable or evaluation evidence is incomplete.
- The final state is no worse than the successfully measured baseline under the authoritative unchanged measurement, unless the requester explicitly accepts a changed-measurement outcome.

## Initial Acceptance Criteria

1. Given an existing skill without an evaluation suite, when preflight runs, then the workflow rejects the request before refinement begins.
2. Given no required test cases or no deterministic full-suite command, when preflight runs, then the workflow reports the missing input and does not invoke an agent.
3. Given promptfoo resolves more than one execution provider, when preflight runs, then the workflow rejects the request.
4. Given valid inputs, when the workflow starts, then it creates a schema-valid progress record and captures a successful baseline before selecting a refinement action.
5. Given a refinement iteration, when planning completes, then exactly one authorized action or stop decision is recorded with rationale.
6. Given a proposed LLM-rubric or evaluation-expectation change, when no human approval exists for the exact proposal, then the workflow does not apply or commit it.
7. Given an agent changes an unauthorized file, when candidate validation runs, then the iteration is rejected and no refinement commit is created.
8. Given an agentic change completes, when candidate validation succeeds, then the complete suite is invoked through the configured promptfoo command with the pinned provider and timeout.
9. Given a candidate increases the absolute number of passing evaluations without reducing required test-case coverage, when comparison completes, then the change is committed deterministically and becomes the new best state.
10. Given a candidate adds meaningful coverage for a previously uncovered required test case while preserving the prior absolute passing count, when comparison completes, then the change may be committed even if the larger denominator lowers the pass percentage.
11. Given every required test case is already covered, when a candidate only increases the number of evaluations without increasing passing evaluations or adding meaningful coverage, then it is not classified or committed as an improvement.
12. Given the first candidate evaluation is worse than the current best state, when comparison completes, then the workflow runs the complete suite a second time against the unchanged candidate before deciding whether to revert.
13. Given both candidate runs demonstrate degradation, when confirmation completes, then the workflow records both results and the proposed-change summary, increments the consecutive-regression counter, reverts the candidate, and reruns the suite against the restored accepted state.
14. Given the second candidate run does not reproduce the first degradation, when confirmation completes, then the workflow records suspected flakiness, makes no autonomous commit or revert decision, and waits for a human decision.
15. Given a confirmed regression has been reverted, when the recovery evaluation does not restore the accepted state's recorded performance, then autonomous refinement stops and hands off to a human.
16. Given a reverted harmful proposal appears in the progress record, when the next planning Activity runs, then it receives enough semantic change and evaluation detail to choose a materially different approach.
17. Given three consecutive proposed changes each produce confirmed degradation, when the third revert and recovery check complete, then the workflow stops regardless of remaining budgets and publishes a report of attempts, evidence, and resource spend.
18. Given an agentic Activity reports token usage, when the iteration is recorded, then per-step and cumulative usage are updated without estimating unavailable values.
19. Given the cumulative token budget or maximum iteration count is reached, when the workflow checks its limits, then it schedules no further refinement step and exits with the best accepted state.
20. Given a promptfoo evaluation exceeds its Activity timeout, when Cadence handles the timeout, then the attempt is recorded and retry/termination follows the configured policy without creating a duplicate logical iteration.
21. Given a worker restarts during the run or while awaiting approval, when workflow execution resumes, then the loop continues from durable state without losing accepted metrics, regression count, budget, or approval context.
22. Given the workflow terminates, when its report is read, then the baseline, final metrics, action history, changed files, repeated evaluation evidence, reverts, recovery checks, token usage, commits, and terminal reason are traceable.

## Out of Scope for the Initial Feature

- Creating the first evaluation suite for a skill that has none.
- Running comparative evaluations across multiple providers or models.
- Automatically approving changes to evaluation expectations.
- Optimizing provider selection or changing provider during a run.
- Unlimited autonomous refinement.
- Fabricating token usage or monetary cost when authoritative telemetry is unavailable.
- A graphical dashboard for progress or approval.
- Defining a universal quality score that applies to every skill.

## Dependencies

- Existing generic Cadence workflow-module and Skill Activity infrastructure.
- A generic prompt-invocation Activity capable of returning structured output, changed files, and usage evidence.
- Deterministic promptfoo execution and structured result parsing.
- Existing per-invocation raw ATIF and normalized usage capture, extended to workflow-level cumulative token accounting.
- Atomic, schema-versioned JSON report publication.
- Repository-state isolation and safe, idempotent commit/restore Activities.
- Cadence Signal and Query contracts for human approval and progress inspection.

## Open Decisions

1. What promptfoo metric or aggregation formula is authoritative when suites contain weighted tests, named metrics, partial credits, or LLM rubric scores?
2. How will the workflow deterministically map evaluations to required test cases and decide that newly added coverage is meaningful rather than duplicative?
3. Must both an iteration limit and token budget be mandatory, or is either one sufficient?
4. How is budget enforcement handled when usage telemetry is delayed or unavailable?
5. Does token usage from timed-out, failed, and retried agentic Activities count? The conservative expectation is yes whenever observable.
6. What is the exact approval transport and authorization model for Cadence Signals?
7. Should a rejected approval return to planning, consume an iteration, or terminate the run?
8. What repository isolation mechanism is required: clean branch, dedicated worktree, or another transaction boundary?
9. What deterministic commit message and metadata identify workflow, run, iteration, score delta, and approval evidence?
10. Which evaluation edits are mechanical scripted-check repairs versus expectation changes requiring approval?
11. How should score comparability be represented after an approved evaluation change?
12. What retry policy is safe for a 10–20 minute promptfoo invocation, and how will the Activity detect or prevent duplicate child processes after timeout or worker restart?
13. What terminal objective, beyond budget exhaustion, allows early success—for example, all required tests passing, a target score, or no justified next action?

## Desired Exit Outcome

The workflow terminates within its declared limits with a complete audit record and the repository at the best accepted, evaluated commit. Under an unchanged authoritative evaluation, that state is equal to or better than the measured baseline; any improvement resulting from a human-approved measurement change is explicitly distinguished from skill-behavior improvement.
