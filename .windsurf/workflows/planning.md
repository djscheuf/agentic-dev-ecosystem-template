# Planning Workflow

## Purpose
Create a detailed implementation plan for a feature or task, breaking it into manageable steps with clear dependencies and sequencing.

## Trigger
- After `analyze-user-story` indicates "Ready to develop"
- Starting work on a new feature
- Beginning a complex task
- Sprint planning requires detailed breakdown

## Prerequisites
- Completed story analysis (from `analyze-user-story`)
- Understanding of acceptance criteria
- Access to codebase (run `explore-codebase` if unfamiliar)

## Workflow Steps

### Step 1: Review Story Analysis
```
Confirm understanding:
□ Story goal is clear
□ Acceptance criteria understood
□ Edge cases identified
□ Dependencies known
□ Questions resolved

If anything unclear → Return to analyze-user-story
```

### Step 2: Identify Work Streams
```
Break the work into parallel tracks:

TYPICAL WORK STREAMS:
├── Backend/API
│   ├── Data model changes
│   ├── Business logic
│   └── API endpoints
├── Frontend/UI
│   ├── Components
│   ├── State management
│   └── API integration
├── Infrastructure
│   ├── Database migrations
│   ├── Configuration
│   └── Deployment
└── Testing
    ├── Unit tests
    ├── Integration tests
    └── E2E tests

Mark streams that can run in parallel vs. sequential.
```

### Step 3: Create Task Breakdown
```
For each work stream, create atomic tasks:

TASK DEFINITION:
├── ID: [Unique identifier]
├── Title: [Clear, actionable description]
├── Type: [Code/Test/Config/Doc/Research]
├── Estimate: [Hours or points]
├── Depends on: [Task IDs]
└── Acceptance: [How to verify complete]

Tasks should be:
- Small enough to complete in < 4 hours
- Self-contained and testable
- Clearly defined completion criteria
```

### Step 4: Sequence Tasks
```
Order tasks considering:

1. DEPENDENCIES
   - What must be done first?
   - What can be parallelized?

2. RISK REDUCTION
   - Tackle unknowns early
   - Validate assumptions first

3. VALUE DELIVERY
   - Core functionality first
   - Nice-to-haves last

4. FEEDBACK LOOPS
   - Get testable code early
   - Enable integration testing
```

### Step 5: Create Implementation Order
```
Generate a numbered task list:

PHASE 1: Foundation
├── Task 1.1: [Description] (X hrs)
├── Task 1.2: [Description] (X hrs)
└── Gate: [What must be true before Phase 2]

PHASE 2: Core Implementation
├── Task 2.1: [Description] (X hrs)
├── Task 2.2: [Description] (X hrs) [parallel with 2.1]
└── Gate: [What must be true before Phase 3]

PHASE 3: Integration & Polish
├── Task 3.1: [Description] (X hrs)
└── Gate: [Feature complete criteria]

PHASE 4: Testing & Documentation
├── Task 4.1: [Description] (X hrs)
└── Done: [Definition of done met]
```

### Step 6: Identify Checkpoints
```
Define verification points:

CHECKPOINT FORMAT:
├── After Task: [Task ID]
├── Verify: [What to check]
├── Method: [How to verify - test, demo, review]
└── Stakeholder: [Who should verify, if anyone]

Examples:
□ After database schema → Run migrations, verify rollback
□ After API endpoints → Integration tests pass
□ After UI components → Manual smoke test
□ Before merge → Code review complete
```

### Step 7: Risk Assessment
```
For each phase, consider:

RISKS:
├── Technical risks
│   ├── [Risk]: [Likelihood] / [Impact]
│   └── Mitigation: [Approach]
├── Schedule risks
│   ├── [Risk]: [Likelihood] / [Impact]
│   └── Mitigation: [Approach]
└── Dependency risks
    ├── [Risk]: [Likelihood] / [Impact]
    └── Mitigation: [Approach]

If high-risk items exist:
- Add spike/research task
- Create fallback plan
- Identify earlier checkpoint
```

### Step 8: Select Development Approach
```
Choose the appropriate methodology:

IF behavior-focused feature with business rules:
    → Use: bdd-workflow
    REASON: Stakeholder communication, living docs

IF technical implementation or internal logic:
    → Use: tdd-workflow
    REASON: Design emergence, unit test coverage

IF both business rules AND complex internal logic:
    → Use: bdd-workflow (outer loop)
    → Use: tdd-workflow (inner loop)
    REASON: Full test pyramid coverage

IF exploring unknown territory:
    → Use: spike workflow first
    → Then: plan with learned information
```

### Step 9: Document the Plan
```
Create the implementation plan document:
(See Output Template below)
```

## Output Template
```markdown
# Implementation Plan: [Story/Feature Name]

## Overview
**Story:** [Link to story or brief description]
**Goal:** [One sentence summary of what we're building]
**Approach:** [BDD/TDD/Both]
**Total Estimate:** [X hours/days]

## Prerequisites
- [ ] [Prerequisite 1]
- [ ] [Prerequisite 2]

## Work Streams

### Stream 1: Backend
| Task | Description | Est | Depends On |
|------|-------------|-----|------------|
| B1 | Create data model | 2h | - |
| B2 | Implement service logic | 4h | B1 |
| B3 | Add API endpoints | 2h | B2 |

### Stream 2: Frontend
| Task | Description | Est | Depends On |
|------|-------------|-----|------------|
| F1 | Create UI components | 3h | - |
| F2 | Add state management | 2h | F1 |
| F3 | Integrate with API | 2h | F2, B3 |

### Stream 3: Testing
| Task | Description | Est | Depends On |
|------|-------------|-----|------------|
| T1 | Unit tests | 2h | B2 |
| T2 | Integration tests | 2h | B3 |
| T3 | E2E tests | 2h | F3 |

## Implementation Phases

### Phase 1: Foundation (Day 1)
**Tasks:** B1, F1 (parallel)
**Checkpoint:** Schema defined, component stubs created
**Gate:** Run tests, verify no regressions

### Phase 2: Core Logic (Day 1-2)
**Tasks:** B2, F2 (parallel), then B3
**Checkpoint:** Service logic complete, API testable
**Gate:** Integration tests pass

### Phase 3: Integration (Day 2)
**Tasks:** F3, T1, T2
**Checkpoint:** Feature functional end-to-end
**Gate:** Manual smoke test passes

### Phase 4: Polish (Day 3)
**Tasks:** T3, Documentation
**Checkpoint:** All tests pass, docs updated
**Gate:** Definition of Done met

## Risks & Mitigations
| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| [Risk 1] | Medium | High | [Approach] |
| [Risk 2] | Low | Medium | [Approach] |

## Definition of Done
- [ ] All acceptance criteria met
- [ ] All tests passing
- [ ] Code reviewed
- [ ] Documentation updated
- [ ] Deployed to staging
- [ ] Product owner sign-off

## Notes
- [Any additional context or decisions]
```

## Quality Checks
- [ ] All work streams identified
- [ ] Tasks are atomic (< 4 hours)
- [ ] Dependencies are explicit
- [ ] Checkpoints defined
- [ ] Risks assessed
- [ ] Development approach chosen
- [ ] Definition of done clear

## Next Workflows
→ `bdd-workflow`: For behavior-driven implementation, NOT AVAILABLE
→ `tdd-workflow`: For test-driven implementationm, NOT AVAILABLE
→ `explore-codebase`: If more context needed

## Common Patterns

### Simple Feature (1-2 days)
```
Phase 1: Setup (2-3 tasks)
Phase 2: Implement (3-5 tasks)
Phase 3: Test & Ship (2-3 tasks)
```

### Complex Feature (3-5 days)
```
Phase 1: Foundation (3-4 tasks)
Phase 2: Core Logic (5-8 tasks)
Phase 3: Integration (3-5 tasks)
Phase 4: Edge Cases (2-4 tasks)
Phase 5: Polish (2-3 tasks)
```

### Refactoring Project
```
Phase 1: Characterization Tests (add tests first)
Phase 2: Extract (create new structure)
Phase 3: Migrate (move code incrementally)
Phase 4: Cleanup (remove old code)
```
