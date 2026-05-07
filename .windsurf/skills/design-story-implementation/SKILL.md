---
name: design-story-implementation
description: Design the implementation of a new user story based on the current application reality, and analysis of the proposed user story. 
---

## Steps:
### 1. Read the story analysis document
- Read the story analysis document provided by the user. This document contains the user story in a structured format, as well as some basic analysis of the upcoming functionality. The document will follow the schema defined in `/schema/analysis.schema.json`.

### 2. Read the current reality audit file
- Read the current reality audit file provided by the user. This file contains the current application reality, as well as some basic analysis of the upcoming functionality. The file will follow the schema defined in `/schema/audit.schema.json`.

### 3. Create the design document
- Create a design document in the same directory, as the provided analysis and audit json files, named `{story title}.design.json`.
- The design document will follow the schema defined in `/schema/design.schema.json`.

### 4. Model the user's flow 
Model the user's flow through the system as a sequence of domain events (not UI clicks). This shows how the story modifies the current reality workflow, focusing on "current reality + one step."

- Start from current reality workflow (existing persona flow)
- Identify workflow state transitions
- Model as sequence of domain events
- Show story's specific change from current state

Update the relevant section of the JSON

### 5. Define Instrumentation Events
Identify key events that should be instrumented for observability and monitoring.

Update the relevant section of the JSON

### 6. Allocate Layer Responsibilities
Assign each AC element to the appropriate application layer(s) using responsibility heuristics. This is an iterative "catch ball" negotiation between layers, not strictly unidirectional.

**Critical Principle**: "Where is the information available to act?" - Responsibility emerges from where new information/behavior originates.

**Layer Responsibility Heuristics**:
**Frontend**:
- Display (what user sees)
- Accessibility, colors, dialogue
- Sequence (occasionally)
- Security role differentiation/adaptation (NOT enforcement)
- Configuration based on user role

**Backend**:
- Business logic (in defensible zone)
- Security enforcement
- Performance optimization
- Scope of supported functionality
- Caching/paging decisions
- Data permissions
- Filter hierarchy and application

**Data Layer**:
- Storage
- Schema and models
- Data integrity
- Heavy computations

Update the relevant section of the JSON

### 7. Define Contracts Between Layers
Define inter-layer contracts (Frontend↔Backend, Backend↔Data) based on data model changes and interaction patterns. This is an iterative negotiation process where contract usage expectations drive data model decisions.

- Design data model changes first
- Determine interaction patterns needed
- Define API contracts based on patterns
- Negotiate optimizations using Functional Alchemy
- Ensure contracts enable independent mockability

**Contract Definition Heuristics**:
**Data model first** (heuristic): Closest to data transformation core
   - New data capture → new models
   - Extended relationships → model extensions
   - Smallest change from current reality to next

**Frontend needs drive backend requirements**:
  - Identify what frontend needs, and how it will interact with the backend.
   - Frontend responsibility → requires backend data
   - Backend must provide → requires model data
   - Find easiest, cleanest way given responsibilities

**Data → API contract precipitation**:
   - Based on desired interaction pattern
   - Server-side paging: Many calls, caching critical
   - Client-side paging: One big chunk, UI handles sorting  
   - Authorization timing: Session start vs. just-in-time
   - Authorization granularity: Overall vs. property-level

**Functional Alchemy optimization**:
   - Can property be derived? → No data model change
   - Derive across million records? → Compute once, store

Update the relevant section of the JSON

### 8. Identify Architectural Decisions
- Identify architectural decisions that need to be made
- Document the decisions and the rationale for each decision
- Favor the application's ADRs, and it's Target Architecture first, then suitable industry architectural patterns, then known best practices.
- Call out any decision that strays from current Architecture explicitly!

Update the relevant section of the JSON

### 9. Clarify Ambiguities
```
When dependencies or questions are identified:

Review existing related code, ADRs, and documentation to understand the context and make informed assumptions.
For each question, capture the following:
- the question
- your assumed answer
- the rationale for your assumption
- the basis for your assumption (e.g., "pattern seen in {existing code}", "desicion precedent in {specific ADR}", "documented business rule per {specific documentation}")
```

Update the relevant section of the JSON

### 10. Write the Sentinel File
- create a sentinel file in the `.process` directory, named `{skill-name}.done.json`.
- the sentinel file will follow `/schema/sentinel.schema.json`. 
- set the task field to "{skill-name}".
- the verify_params of the sentinel file will follow `/schema/verify-params.schema.json`. 
- set the verify_params as follows:
    - set "design_path" as the path to the design file  relative to repo root.
