# Stage 4 Certification Criteria

These are the five required artifacts for a Stage 4 agentic-workflow certification, as shown in the certification framework screenshot.

---

## 1. Workflow Definition

A file describing the multi-step workflow that connects validated Stage 3 agents.

### Required evidence

- Multiple Stage 3 agents wired into an end-to-end workflow.
- Handoffs and branching logic are documented.
- Every agent passes its Stage 3 quality bar (95%+) on real work.
- No agents still require regular manual correction.

---

## 2. Guardrails

Deterministic validation checks positioned **between** workflow steps, not inside them.

### Required evidence

- Adversarial review agents that challenge prior step outputs.
- Hooks and sentinel files for deterministic runtime checks.
- Guardrails sit between steps, not inside them.
- Guardrails must be automated; human review between steps is a Stage 2 pattern, not Stage 4.

---

## 3. Punch-Out Evidence

Documentation of human evacuation points with active bypass testing.

### Required evidence

- Explicit human decision points where the workflow must stop for sign-off.
- Actively tested — someone attempted to bypass and was blocked.
- Clear separation of "fail workflow" (automated) vs "punch to human" (manual).
- Punch-out points that exist on paper but were never tested do **not** qualify.

---

## 4. End-to-End Success Rate

A report showing the end-to-end success rate across the full workflow.

### Required evidence

- The end-to-end number, not just per-step accuracy.
- Measured across the full workflow, start to finish.
- Trend showing stability or improvement over time.
- If the end-to-end number is unknown, the workflow has not reached Stage 4.

---

## 5. Audit Trail

An artifact demonstrating that any failure can be traced to its origin step.

### Required evidence

- Structured logs identifying which step produced which output.
- Ability to trace a specific failure to its exact origin step.
- Per-step model and token/cost data — which model, input tokens, output tokens, and cost per step.
- Coverage of all workflow steps, not just some.
