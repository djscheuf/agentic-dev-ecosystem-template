# Signal and Query Contracts for the Story Analysis Workflow

These contracts define the human-in-the-loop surface and the introspection query used by the Story Analysis Workflow running in the `story-analysis` domain on the `story-analysis` task list.

## Signal: `human_response`

Sent by a human reviewer to resolve an escalation.

### Payload

```json
{
  "decision": "retry | accept | abort",
  "notes": "optional human-readable explanation"
}
```

### Decision semantics

| Decision | Workflow behavior |
|---|---|
| `retry` | Resume the grade-repair loop if attempts remain, or retry the failed Activity if the escalation was for retry exhaustion. If no attempts remain and `retry` is chosen, the Workflow treats it as `accept`. |
| `accept` | Mark the current analysis as the final result and complete the Workflow with `final_status` set to `human_resolved`. |
| `abort` | Complete the Workflow with `final_status` set to `aborted`; the latest analysis JSON remains in the repository for inspection. |

### Delivery

- The Workflow blocks on a `Selector` over the `human_response` Signal channel plus a bounded timer.
- The Signal must be sent to the Workflow's `workflow_id` (RunID may be empty to target the current run).
- Only a client authenticated for the `story-analysis` domain can send this Signal.

## Query: `get_status`

Allows a client or the Web UI to inspect the Workflow's current state without mutating it.

### Return value

```json
{
  "step": "extracting_intent | analyzing | grading | repairing | awaiting_human | completed",
  "attempt_count": 0,
  "max_attempts": 3,
  "escalated": false,
  "escalation_reason": null,
  "final_status": null
}
```

### Field semantics

| Field | Type | Meaning |
|---|---|---|
| `step` | `string` | Current high-level step. |
| `attempt_count` | `int` | Number of `repair-story-analysis` invocations in the current grade-repair loop. |
| `max_attempts` | `int` | Maximum allowed repair attempts (3). |
| `escalated` | `bool` | Whether the Workflow is currently waiting on a human Signal. |
| `escalation_reason` | `string \| null` | One of `activity_failure_exhausted_retries`, `grade_repair_loop_exhausted`, or `step_ambiguity`. |
| `final_status` | `string \| null` | Set to `passed`, `human_resolved`, `aborted`, or `needs_human_review` once the Workflow completes. |

## Scope and isolation

Workflows of this type are isolated to:

- **Domain:** `story-analysis`
- **Task list:** `story-analysis`

Only Workers configured with this domain and task list will poll and execute the Workflow's Activities. Only clients using this domain can start, signal, or query the Workflow. Cadence enforces this at the server; mismatched Worker or client configuration results in a `WorkflowExecutionAlreadyStarted` or `EntityNotExists` error.
