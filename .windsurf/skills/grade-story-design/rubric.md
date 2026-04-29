# Design Plan Quality Rubric

## Scoring Overview

Each dimension is scored on a **0-3 scale**:
- **0**: Missing or critically deficient
- **1**: Minimal; significant gaps present
- **2**: Adequate; meets baseline requirements
- **3**: Exemplary; complete and well-articulated

---

## Evaluation Dimensions

### 1. **Design Reasoning & Architectural Justification**

**What this measures**: Are design decisions grounded in architecture, patterns, and minimalism?

#### Criteria:

| Score | Descriptor | Evidence |
|-------|-----------|----------|
| **0** | No architectural justification; decisions appear arbitrary or over-engineered | No reference to ADRs or patterns; unnecessary abstractions introduced |
| **1** | Some decisions justified; significant gaps in reasoning; heuristic-driven | "For simplicity" without architectural context; some over-engineering present |
| **2** | Most decisions justified by ADRs or patterns; design is mostly minimal; some intents could be clearer | Decisions reference existing patterns; one or two questionable components |
| **3** | All decisions grounded in ADRs, target architecture, or established patterns; design is lean; intents clearly differentiated | Every component serves a clear purpose; extension favored over creation; defensive programming explicit |

#### Improvement Questions:
- Are design decisions backed by existing ADRs or target architecture?
- Is the design minimal, or does it include unnecessary abstractions?
- When multiple layers handle the same responsibility, is the *different intent* for each layer explicit?
- Does the design avoid over-engineering or scope creep?
- Is defensive programming (backend enforcement vs. frontend UX feedback) clearly articulated?

---

### 2. **Workflow Changes & Happy Path**

**What this measures**: Is the user journey fully specified with clear steps, data flows, and edge cases?

#### Criteria:

| Score | Descriptor | Evidence |
|-------|-----------|----------|
| **0** | Happy path is missing, vague, or unintelligible; no edge cases identified | Workflow is unclear; no step-by-step description; no error states |
| **1** | Happy path sketched but incomplete; 1-2 edge cases mentioned with vague divergences | Workflow exists but lacks clarity on layer ownership or data flow; minimal edge case coverage |
| **2** | Happy path fully specified with layer identification and data flow; 2-3 edge cases with clear divergences | Each step identifies which layer performs the action; data transformations explicit; most edge cases addressed |
| **3** | Happy path unambiguous and implementable; 4+ edge cases with clear divergences and recovery paths; all acceptance criteria mapped | User journey is step-by-step from trigger to completion; sequence and timing clear; business rules documented; no scope creep |

#### Improvement Questions:
- Is the user journey described step-by-step from trigger to completion?
- Does each step identify which layer (API, FE, Component) performs the action?
- Are data transformations explicit (what enters, what exits each step)?
- Is the sequence and timing of operations clear (synchronous vs. asynchronous)?
- Are at least 3 edge cases or error states identified with recovery behavior?
- Do all acceptance criteria from the user story map to workflow steps?

---

### 3. **Interface & Contract Specifications**

**What this measures**: Are API contracts and component interfaces fully specified with clear shapes and alignment?

#### Criteria:

| Score | Descriptor | Evidence |
|-------|-----------|----------|
| **0** | No API contracts or component interfaces specified; workflow and contracts disconnected | No endpoint definitions; no payload shapes; no component props defined |
| **1** | Contracts sketched but incomplete; significant gaps in shapes or error handling; partial workflow mapping | Some endpoints listed; payload shapes incomplete; component interfaces vague; some workflow steps unmapped |
| **2** | Most contracts defined with complete shapes; most workflow steps mapped; minor gaps in constraints or error cases | All endpoints listed with methods and paths; request/response shapes mostly complete; component props defined; minor data shape mismatches |
| **3** | All contracts complete with full shape definitions and error handling; perfect 1:1 mapping between workflow and contracts | All endpoints specified with HTTP method, path, request/response shapes, status codes, and error messages; all components have complete interface definitions; all workflow steps map to specific calls |

#### Improvement Questions:
- Are all new or modified endpoints listed with HTTP method and path?
- Are request and response payload shapes defined (required/optional fields, types, constraints)?
- Are status codes and error messages specified?
- Are new or modified components named with clear responsibility?
- Are component props/inputs listed with types and whether required?
- Does each workflow step map to a specific API endpoint or component method call?
- Do data flows between steps match the contract shapes?

---

### 4. **Layer Responsibilities & Consistency**

**What this measures**: Is ownership clear across layers, and does the design follow established patterns?

#### Criteria:

| Score | Descriptor | Evidence |
|-------|-----------|----------|
| **0** | No layer responsibilities defined; contradicts existing architecture | Unclear which layer owns state or manages operations; no pattern alignment |
| **1** | Vague layer assignments; significant overlap or gaps; limited reuse of existing patterns | Some responsibilities sketched; some ambiguity about ownership; significant deviations from pattern |
| **2** | Most responsibilities assigned with some rationale; mostly consistent with existing patterns; some reuse of existing components | Clear ownership for most decisions; follows established patterns; minor deviations unexplained |
| **3** | All responsibilities clearly assigned with explicit rationale; fully consistent with existing architecture; boundaries explicit | For each major operation, responsible layer is identified with clear rationale; no ambiguity about ownership; reuses existing components/utilities; deviations justified |

#### Improvement Questions:
- For each major decision/operation, is the responsible layer identified (API, FE, Component)?
- Is the rationale for layer choice stated?
- Is the boundary between layers explicit (what crosses the API boundary)?
- Does the design follow established patterns in the codebase?
- Are there contradictions with existing layer responsibilities?
- Does the design reuse existing components/utilities where applicable?

---

### 5. **Instrumentation & Observability**

**What this measures**: Are observability points and debugging support defined?

#### Criteria:

| Score | Descriptor | Evidence |
|-------|-----------|----------|
| **0** | No instrumentation events specified; no debugging support | No logging, metrics, or observability points defined |
| **1** | Minimal instrumentation; 1 point with minimal context; limited debugging support | One instrumentation point; error states lack logging strategy; no timing instrumentation |
| **2** | 2-3 instrumentation points with good context; some debugging support for errors and performance | Key workflow milestones identified; some context included; error logging or timing instrumentation present |
| **3** | 4+ instrumentation points with rich context; comprehensive debugging support; all error states covered | At least one metric/log point per major workflow branch; error states include logging/alerting; performance-critical paths have timing; data transformations include validation logging |

#### Improvement Questions:
- Are key workflow milestones identified for logging/metrics?
- Is there at least one metric or log point per major workflow branch?
- Do events include relevant context (user ID, item ID, error type, etc.)?
- Is there a logging/alerting strategy for error states?
- Do performance-critical paths have timing instrumentation?
- Are data transformations logged (what passed/failed)?

---

## Common Gaps & Remediation

### Gap: Vague Architectural Justification
**Symptom**: Design decisions lack reference to ADRs or patterns; over-engineering present
**Fix**: Ground each decision in existing architecture or target architecture. If introducing new elements, explicitly justify why. Prefer extending existing components over creating new ones.

### Gap: Incomplete Happy Path
**Symptom**: Workflow is unclear or missing layer identification; data flow is implicit
**Fix**: Describe the user journey step-by-step. For each step, identify which layer performs it and what data enters/exits. Make sequence and timing explicit.

### Gap: Unmapped Workflow Steps
**Symptom**: Workflow steps don't correspond to API endpoints or component calls; data shapes mismatch
**Fix**: Create a 1:1 mapping table between workflow steps and contracts. Verify that data flowing between steps matches the contract shapes.

### Gap: Unclear Layer Responsibilities
**Symptom**: Same responsibility assigned to multiple layers without clear intent; pattern deviations unexplained
**Fix**: For each major operation, explicitly state which layer owns it and why. If validation happens in multiple layers, explain the distinct intent (e.g., API for enforcement, FE for UX feedback).

### Gap: Missing Instrumentation
**Symptom**: No observability points defined; error states lack logging strategy
**Fix**: Identify key workflow milestones for logging. Define at least one metric/log point per major workflow branch. Specify logging/alerting for error states and timing for performance-critical paths.
