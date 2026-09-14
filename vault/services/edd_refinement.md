# EDD Refinement ProgressRecord

The `edd_refinement_workflow` persists durable, schema-versioned run state in the target repository under `.process/edd/<run_id>/progress.json`.

- `ProgressRecordStore` provides idempotent `create_or_resume`.
- `ProgressRecordSerializer` enforces the schema version and an explicit field allow-list before writing.
- `ProgressRecordFactory` derives a stable `run_id` from the Cadence workflow run id and the starting Git revision, and refuses duplicate creation.
- `InitializeRunActivity` verifies a successful `PreflightResult`, creates or resumes the progress record, and emits `InitializeRun` or `ResumeRun` events.
- `RunBaselineEvaluationActivity` invokes a pinned evaluation profile through a pluggable harness and records each attempt in the progress record.
- `BaselineResultParser` extracts and validates pass/fail/coverage metrics and failures from structured output.
- `BaselineResultArtifactWriter` writes the baseline result to a repository-relative artifact file.
- `PlanRefinementActivity` produces a `PlanningResult`, choosing `stop` when budgets or the regression limit is exhausted, validating proposed actions against the taxonomy and required-test-case mapping, and flagging `propose_evaluation_expectation_change` for human approval.
- `EddRefinementWorkflow` and `WorkflowModuleSpec` register the workflow and the three Cadence Activities with the orchestrator.

See [[decisions/ADR-017-agentic-edd-quality-ratchet.md]] and [[decisions/ADR-018-target-repository-context.md]] for background.
