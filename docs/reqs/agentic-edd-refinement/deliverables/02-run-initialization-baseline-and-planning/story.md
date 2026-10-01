# Initialize the Run, Establish the Baseline, and Plan Refinement

## Story

So that every refinement action begins from durable evidence and an explainable decision
As a workflow requester and skill owner
I want the workflow to initialize schema-versioned run state, establish a trustworthy baseline, and select one authorized next action

## Source Deliverables

- `EDD-002` — Schema-versioned progress record initialization
- `EDD-003` — Baseline evaluation establishment
- `EDD-004` — Refinement action planning

## Entry Outcome

Preflight has succeeded and the workflow holds the mutation lease for a validated target repository.

## Scope

### In Scope

- Create or resume one schema-versioned, secret-free progress record.
- Record normalized run context, limits, counters, and iteration history.
- Evaluate the complete suite with the deterministic command and pinned provider.
- Record baseline metrics, failures, artifacts, duration, and outcome.
- Select exactly one evidence-based action from the authorized action set.
- Record the action rationale, intended scope, expected effect, approval requirement, and stop recommendation.

### Out of Scope

- Human approval of evaluation expectation changes.
- Applying a planned refinement action.
- Candidate comparison, commit, regression recovery, or final reporting.

## Acceptance Criteria

### Progress Record Initialization

- **EDD-002-AC1:** Given preflight has succeeded for a run, when the workflow initializes, then a schema-versioned JSON progress record is created containing run identity, resolved repository identity, normalized inputs, authorized scope, limits, and an empty iteration history.
- **EDD-002-AC2:** Given the progress record is created, when it is inspected, then cumulative token usage and the consecutive confirmed-regression counter are initialized to zero.
- **EDD-002-AC3:** Given the run has access to secrets, credentials, or sensitive environment values, when the progress record is written, then none of those values appear in the document.
- **EDD-002-AC4:** Given a worker restarts immediately after initialization, when the workflow resumes, then the same progress record is reused rather than duplicated or recreated.

### Baseline Evaluation

- **EDD-003-AC1:** Given a valid initialized run, when the workflow establishes its baseline, then it invokes the complete evaluation suite through the deterministic evaluation command and pinned provider.
- **EDD-003-AC2:** Given the baseline evaluation completes, when results are recorded, then passing, failing, total, percentage, and required-test-case coverage metrics, along with failures, artifact references, duration, and outcome, are stored in the progress record.
- **EDD-003-AC3:** Given the baseline evaluation cannot be executed successfully, when the workflow checks the outcome, then refinement does not begin and the failure is recorded.
- **EDD-003-AC4:** Given the baseline evaluation exceeds its configured timeout, when the timeout is reached, then the attempt is recorded and handled per the configured retry policy without silently proceeding to refinement.

### Refinement Action Planning

- **EDD-004-AC1:** Given the current progress record, latest evaluation evidence, required test cases, and remaining budgets, when a planning step runs, then it selects exactly one action from the authorized set: add or extend coverage, repair scripted checks, refine the skill, refine supporting documents, propose an evaluation expectation change, or stop.
- **EDD-004-AC2:** Given a planning step completes, when its result is recorded, then it includes rationale and evidence, intended files or file classes, expected effect, whether human approval is required, and a stop recommendation when applicable.
- **EDD-004-AC3:** Given no defensible action remains, the objective is met, or a limit prevents another safe iteration, when planning runs, then the `stop` action is selected and no further refinement is scheduled.
- **EDD-004-AC4:** Given a planning result names an action outside the authorized set, when the result is validated, then the iteration is rejected and no refinement Activity is invoked for it.

## Dependencies

- Successful target repository preflight and an active mutation lease.
- Durable, schema-versioned progress-record storage.
- Deterministic evaluation command, pinned provider, required-test-case mapping, timeout, and retry policy.
- Authorized action taxonomy and remaining-budget information.

## Exit Outcome

The workflow has durable initial state, a recorded and trustworthy baseline, and exactly one validated authorized action or an explicit stop decision.
