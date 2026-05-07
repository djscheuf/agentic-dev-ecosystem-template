# SDLC Workflow Summary: Refactor Wrapper and Orchestrator Responsibility Split

**Date:** 2026-05-07  
**Status:** Complete (Analysis → Design → Plan)

## Overview

This document summarizes the Software Delivery Lifecycle (SDLC) analysis, design, and planning for the refactoring requirement to split responsibilities between the DevinWrapper (thin CLI adapter) and the Orchestrator (instrumentation and state management).

## Artifacts Generated

### Phase 1: Analysis
- **Intent Document:** `refactor-wrapper-orchestrator-responsibilities.intent.json`
  - Extracted user story in structured format
  - Identified target persona (Orchestrator Developer)
  - Broke down capability requirements
  - Extracted 7 acceptance criteria + 3 additional error handling criteria

- **Analysis Document:** `refactor-wrapper-orchestrator-responsibilities.analysis.json`
  - Comprehensive analysis of requirements
  - 10 acceptance criteria with testability assessment
  - 10 edge cases identified (input, state, system)
  - 6 open questions documented
  - Complexity assessment: High (8 story points, Medium-High risk)

### Phase 2: Design
- **Audit Document:** `current-reality.audit.json`
  - Current architecture: Graph-based saga orchestration with Devin CLI wrapper
  - Identified 3 core components: DevinWrapper, SagaExecutor, EnrichmentDictionary
  - Key findings: DevinWrapper has too many responsibilities; no generic agent interface
  - Related ADRs: ADR-008 (Devin CLI Saga Orchestration), ADR-009 (Saga State Persistence)

- **Design Document:** `refactor-wrapper-orchestrator-responsibilities.design.json`
  - 8-step workflow sequence with layer responsibilities
  - 7 instrumentation events defined
  - Layer responsibility allocation (AgentWrapper, Orchestrator, SagaExecutor, Enrichment)
  - 4 contracts defined (AgentWrapper Interface, Orchestrator.invoke_step(), Step Execution Flow, Session State Files)
  - 6 architectural decisions with justification and basis
  - 7 open questions addressed

### Phase 3: Plan
- **Implementation Plan:** `refactor-wrapper-orchestrator-responsibilities.plan.json`
  - 15 implementation steps across orchestrator and tests
  - Impacted layers: orchestrator, interfaces, tests
  - 13 unit tests, 6 integration tests, 3 E2E tests
  - 8 risks identified with mitigations

## Key Design Decisions

### 1. Generic AgentWrapper Interface
- **Decision:** Define abstract base class for agent CLI tools
- **Rationale:** Enables multiple agent implementations (Devin, Claude, Anthropic, etc.) without modifying orchestrator
- **Impact:** DevinWrapper implements interface; future agents can be added by implementing same interface

### 2. Orchestrator Owns Instrumentation
- **Decision:** Move enrichment, session management, verification, and timeout enforcement to Orchestrator
- **Rationale:** Orchestrator has full context of step execution and saga state
- **Impact:** Wrapper becomes thin CLI adapter; Orchestrator handles all orchestration concerns

### 3. Session Lifecycle Management
- **Decision:** Orchestrator writes and manages session state files (session_id.txt, feedback.txt, stderr.txt)
- **Rationale:** Session state is part of saga execution context; enables future state persistence (ADR-009)
- **Impact:** Wrapper becomes stateless; Orchestrator manages all state files

### 4. Timeout Enforcement at Orchestrator Level
- **Decision:** Orchestrator enforces timeout around entire step lifecycle
- **Rationale:** Orchestrator has full context; ensures consistent timeout behavior across all steps
- **Impact:** Wrapper receives timeout parameter but doesn't enforce it

### 5. Enrichment Integration
- **Decision:** Orchestrator integrates EnrichmentDictionary into step execution
- **Rationale:** Prompt enrichment is part of step execution context
- **Impact:** Enrichment is now automatic for all steps; enables context-aware agent execution

## Acceptance Criteria Status

| Criterion | Status | Notes |
|-----------|--------|-------|
| DevinWrapper accepts prompt, agent_config, timeout, session_id | Pending | Refactor wrapper to thin adapter |
| DevinWrapper doesn't manage session files | Pending | Move file management to orchestrator |
| Orchestrator loads step definition and enriches prompts | Pending | Create Orchestrator.invoke_step() |
| Orchestrator manages session lifecycle | Pending | Write session state files in orchestrator |
| Orchestrator invokes verification scripts | Pending | Move verification invocation to orchestrator |
| Generic AgentWrapper interface enables future agents | Pending | Create abstract base class |
| Timeout enforcement at orchestrator level | Pending | Move timeout to orchestrator |

## Implementation Roadmap

### Phase 1: Core Refactoring (High Priority)
1. Create AgentWrapper abstract base class
2. Refactor DevinWrapper to implement interface
3. Create Orchestrator class with invoke_step()
4. Integrate EnrichmentDictionary
5. Move session file management
6. Move verification script invocation
7. Move timeout enforcement
8. Update SagaExecutor to use Orchestrator

### Phase 2: Testing (High Priority)
1. Write unit tests for AgentWrapper interface
2. Write unit tests for DevinWrapper refactoring
3. Write unit tests for Orchestrator.invoke_step()
4. Write integration tests for step execution flow
5. Write integration tests for session resumption
6. Update existing saga execution tests

### Phase 3: Integration (Medium Priority)
1. Update run_saga.py to initialize Orchestrator
2. Verify backward compatibility with existing sagas
3. Update documentation and examples

## Related Decisions

- **ADR-008:** Devin CLI Saga Orchestration - Defines current saga orchestration architecture
- **ADR-009:** Saga State Persistence - Defines future state persistence; refactoring enables cleaner state management
- **ADR-003:** Skills-Based Architecture - Predecessor; understanding skills pattern informs generic agent interface design

## Open Questions Addressed

1. **AgentWrapper interface type:** Abstract base class (for explicit contract enforcement)
2. **Timeout enforcement:** Process kill via subprocess.run(timeout=...) at Orchestrator level
3. **Orchestrator retry logic:** Fail immediately; retry handled by saga routing (traversal limits)
4. **Session state isolation:** Unique session IDs per invocation; ADR-009 defines persistence structure
5. **Verification output:** Capture both exit code and stderr; store stderr for debugging
6. **Enrichment failure:** Orchestrator should fail step with clear error message
7. **Multi-agent support:** Devin-only initially; interface enables future agents

## Risks and Mitigations

| Risk | Mitigation |
|------|-----------|
| Breaking change to SagaExecutor | Provide clear migration path; update incrementally |
| Session file management moved | Location and format unchanged; only responsibility moves |
| Timeout behavior changes | Orchestrator enforces around entire lifecycle; test thoroughly |
| Enrichment initialization failure | Validate enrichment before use; fail with clear error |
| Verification behavior changes | Location and invocation unchanged; only responsibility moves |
| AgentWrapper interface inflexibility | Design minimal and extensible interface; plan for evolution |
| Concurrent execution conflicts | Use unique session IDs per invocation; ADR-009 handles isolation |
| Test failures | Update tests incrementally; maintain coverage throughout |

## Next Steps

1. **Review and Approve:** Review design and plan documents with team
2. **Address Open Questions:** Clarify any remaining ambiguities with stakeholders
3. **Begin Implementation:** Start with Phase 1 (Core Refactoring) following the implementation plan
4. **Continuous Testing:** Write tests incrementally as components are refactored
5. **Documentation:** Update code comments and architecture documentation as refactoring progresses

## Files Generated

```
docs/reqs/refactor devin wrapper/
├── refactor-wrapper-orchestrator-responsibilities.md (original requirement)
├── refactor-wrapper-orchestrator-responsibilities.intent.json (Phase 1)
├── refactor-wrapper-orchestrator-responsibilities.analysis.json (Phase 1)
├── current-reality.audit.json (Phase 2)
├── refactor-wrapper-orchestrator-responsibilities.design.json (Phase 2)
├── refactor-wrapper-orchestrator-responsibilities.plan.json (Phase 3)
└── SDLC_SUMMARY.md (this file)
```

## Sentinel Files

```
.process/
├── analyze-story.done.json
├── audit-current-reality.done.json
├── design-story-implementation.done.json
└── draft-implementation-plan.done.json
```
