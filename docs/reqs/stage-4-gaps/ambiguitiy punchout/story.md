# Punch Out on Ambiguous or Invalid Workflow Handoffs

## Story

So that uncertain or invalid intermediate results never advance silently through story analysis
As a Story Analysis Workflow operator
I want every activity handoff validated and ambiguous failures routed to a controlled human decision

## Entry Outcome

A Skill Activity has returned an output path or an explicit ambiguity result that must be evaluated before the next workflow step.

## Scope

### In Scope

- Run an explicit guardrail between every pair of successive Skill Activities.
- Verify that the previous activity's output file exists, is readable, and conforms to the expected JSON Schema before scheduling the dependent activity.
- Verify after a passing grader step that the expected intent, analysis, and analysis-grade artifacts exist and conform to their schemas.
- Classify deterministic missing, unreadable, and schema-invalid artifacts as automated guardrail failures.
- Connect explicit ambiguous activity or guardrail outcomes to `ACTIVITY_FLAGGED_AMBIGUITY`.
- Transition an ambiguity punch-out to a durable awaiting-human state.
- Accept only supported `retry`, `accept`, or `abort` decisions while awaiting a decision.
- Reject or ignore unsupported, stale, duplicate, or out-of-state decisions without advancing the workflow.
- Record guardrail outcomes, escalation reason, decision, decision origin, and terminal path.
- Add live integration or end-to-end tests that attempt to bypass the human wait.
- Record at least one exercised ambiguity punch-out run as certification evidence.

### Out of Scope

- Workflow source validation before the first activity.
- Creating a new independent adversarial-review agent.
- Redesigning the ordinary grade/repair quality loop.
- Defining identity infrastructure or a new authentication provider; signal authorization may rely on the existing trusted operator boundary.
- Consolidated per-run reporting and success-rate aggregation.
- Per-agent Stage 3 quality remediation or certification evidence.

## Acceptance Criteria

- Given a completed activity points to an existing readable artifact that matches the expected schema, when the handoff guardrail runs, then the dependent activity is scheduled exactly once.
- Given an activity output path is missing, nonexistent, a directory, or unreadable, when the handoff guardrail runs, then the dependent activity is not scheduled and the workflow records an automated guardrail failure naming the step and failed rule.
- Given an activity artifact is malformed JSON or violates its expected schema, when the handoff guardrail runs, then the dependent activity is not scheduled and the workflow records an automated guardrail failure.
- Given the grader passes, when the post-grader guardrail runs, then it confirms the intent, analysis, and analysis-grade artifacts all exist and match their schemas before the workflow can complete successfully.
- Given concurrent workflows or retries produce similarly named artifacts, when a handoff is validated, then only the artifact associated with the current workflow run and activity attempt is accepted.
- Given an activity or guardrail explicitly reports an ambiguous outcome, when the engine evaluates it, then the workflow enters `awaiting_signal` with reason `ACTIVITY_FLAGGED_AMBIGUITY` and does not schedule the next activity.
- Given a workflow awaits an ambiguity decision, when a supported `retry` decision is received through the trusted operator path, then the bounded retry transition occurs once and is logged.
- Given a workflow awaits an ambiguity decision, when a supported `accept` or `abort` decision is received through the trusted operator path, then the corresponding human-resolved or human-aborted terminal path occurs once and is logged distinctly from automated failure.
- Given a workflow awaits a decision, when an unsupported, stale, duplicate, or out-of-state decision is sent, then it does not advance or overwrite the workflow's valid state.
- Given no valid decision arrives before the configured timeout, when timeout handling completes, then the documented bounded timeout policy is applied once and the outcome is logged.
- An integration or end-to-end test sends an invalid decision to a live awaiting workflow and proves that the wait cannot be bypassed.
- At least one recorded workflow run demonstrates the full ambiguity path from flagged result through a valid human decision.

## Dependencies

- Existing Story Analysis engine sequencing and bounded retry behavior.
- Existing `HumanDecision` values and Cadence `human_response` Signal.
- Existing skill artifact schemas and deterministic expected output paths.
- A structured way for an activity or guardrail to report ambiguity.
- A documented trusted-operator boundary for sending human decisions.
- A deterministic timeout policy for unresolved punch-outs.

## Exit Outcome

No downstream activity consumes a missing or invalid artifact, and explicit ambiguity stops the workflow until a valid bounded human decision resolves it.
