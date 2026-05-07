# Analyze User Story Workflow

## Purpose
Systematically analyze a user story to understand requirements, identify edge cases, assess complexity, and prepare for implementation.

## Trigger
- New user story assigned
- Sprint planning preparation
- Before starting development
- Story needs estimation

## Inputs Required
- User story text
- Acceptance criteria (if available)
- Related documentation or designs
- Access to codebase

## Workflow Steps

### Step 1: Parse the User Story
```
Extract components from the story format:

AS A [role]          → Who is the user? What's their context?
I WANT [capability]  → What feature/behavior is requested?
SO THAT [benefit]    → Why? What value does this provide?

If not in this format, rewrite it properly first.
```

### Step 2: Identify the User/Persona
```
Document the user context:

USER PROFILE:
├── Role: [e.g., Customer, Admin, Guest]
├── Technical level: [Novice/Intermediate/Expert]
├── Frequency of use: [Daily/Weekly/Occasional]
├── Environment: [Desktop/Mobile/Both]
└── Permissions: [What can they access?]

Questions to answer:
- What other actions does this user typically perform?
- What's their journey before/after this feature?
- Are there different user types affected?
```

### Step 3: Analyze the Capability
```
Break down what's being requested:

CAPABILITY ANALYSIS:
├── Core action: [The main thing user does]
├── Inputs required: [What data is needed?]
├── Outputs expected: [What should result?]
├── State changes: [What data is modified?]
└── Side effects: [Notifications, logs, etc.]

Map to system components:
├── UI affected: [Screens, forms, buttons]
├── API endpoints: [New or modified]
├── Database changes: [Schema, queries]
└── External services: [Third-party integrations]
```

### Step 4: Examine Acceptance Criteria
```
For each acceptance criterion:

CRITERION: [Statement]
├── Testable: Yes/No (rewrite if No)
├── Type: Functional/Non-functional/Edge case
├── Dependencies: [Other criteria this relates to]
└── Test scenario: [How to verify this]

If acceptance criteria missing, generate them:
- Happy path scenarios
- Error handling scenarios
- Boundary conditions
- Permission/access scenarios
```

### Step 5: Identify Edge Cases
```
Systematically consider:

INPUT EDGE CASES:
□ Empty/null values
□ Maximum length inputs
□ Special characters (unicode, emojis)
□ Invalid formats
□ Boundary values

STATE EDGE CASES:
□ First-time use (no existing data)
□ Maximum data limits
□ Concurrent modifications
□ Partial completion states

USER EDGE CASES:
□ No permissions
□ Expired sessions
□ Multiple devices
□ Interrupted workflows

SYSTEM EDGE CASES:
□ External service unavailable
□ Network timeout
□ Database errors
□ Rate limiting
```

### Step 6: Assess Dependencies
```
Identify what this story depends on:

TECHNICAL DEPENDENCIES:
├── Existing code: [Classes, services to modify]
├── New code: [What needs to be created]
├── Infrastructure: [Databases, queues, etc.]
└── External services: [APIs, integrations]

STORY DEPENDENCIES:
├── Blocked by: [Stories that must complete first]
├── Blocks: [Stories waiting on this]
└── Related: [Stories that share components]

KNOWLEDGE DEPENDENCIES:
├── Domain knowledge needed: [Business rules to learn]
├── Technical knowledge needed: [Technologies to understand]
└── Questions for stakeholders: [Clarifications needed]
```

### Step 7: Estimate Complexity
```
Assess using multiple dimensions:

COMPLEXITY FACTORS:
├── Code changes: [S/M/L] - How much code?
├── Risk level: [Low/Medium/High] - What could break?
├── Uncertainty: [Low/Medium/High] - How clear is it?
├── Dependencies: [Few/Some/Many] - External factors?
└── Testing effort: [S/M/L] - How hard to verify?

STORY POINTS (Fibonacci):
1 = Trivial, well-understood
2 = Small, some complexity
3 = Medium, typical feature
5 = Medium-large, some unknowns
8 = Large, significant complexity
13 = Very large, consider splitting
21+ = Epic, must split

If > 8 points, run: story-split workflow
```

### Step 8: Generate Implementation Approach
```
Outline high-level approach:

IMPLEMENTATION PLAN:
1. [First major step]
2. [Second major step]
3. [Third major step]
...

TESTING STRATEGY:
├── Unit tests: [Key behaviors to test]
├── Integration tests: [System interactions]
└── E2E tests: [User scenarios]

RISKS AND MITIGATIONS:
├── Risk 1: [Description]
│   └── Mitigation: [Approach]
└── Risk 2: [Description]
    └── Mitigation: [Approach]
```

### Step 9: Document Questions
```
Capture all uncertainties:

BLOCKING QUESTIONS (Must answer before starting):
1. [Question] - Ask: [Person/Team]
2. [Question] - Ask: [Person/Team]

NON-BLOCKING QUESTIONS (Can clarify during work):
1. [Question] - Default assumption: [Assumption]
2. [Question] - Default assumption: [Assumption]

CLARIFICATIONS NEEDED:
1. Acceptance criteria #X is ambiguous because...
2. The story doesn't specify what happens when...
```

## Output Document
```markdown
# Story Analysis: [Story ID] - [Title]

## Story
AS A [role]
I WANT [capability]
SO THAT [benefit]

## User Context
- **Role:** [description]
- **Journey:** [before → this story → after]

## Capability Breakdown
- **Core action:** [description]
- **Inputs:** [list]
- **Outputs:** [list]
- **State changes:** [list]

## Acceptance Criteria Analysis
| # | Criterion | Testable | Type | Notes |
|---|-----------|----------|------|-------|
| 1 | [text] | Yes | Functional | [notes] |
| 2 | [text] | Yes | Edge case | [notes] |

## Edge Cases Identified
1. [Edge case with expected behavior]
2. [Edge case with expected behavior]

## Dependencies
- **Technical:** [list]
- **Stories:** Blocked by [X], Blocks [Y]
- **Knowledge:** [list]

## Complexity Assessment
- **Estimate:** X story points
- **Risk level:** [Low/Medium/High]
- **Rationale:** [explanation]

## Implementation Approach
1. [Step 1]
2. [Step 2]
3. [Step 3]

## Open Questions
1. [Question] - Owner: [name]
2. [Question] - Owner: [name]

## Recommendation
[Ready to develop / Needs clarification / Should split / etc.]
```

## Quality Checks
- [ ] Story is well-formed (As a, I want, So that)
- [ ] All acceptance criteria are testable
- [ ] Edge cases documented
- [ ] Dependencies identified
- [ ] Questions captured with owners
- [ ] Complexity reasonably estimated
- [ ] Implementation approach outlined

## Next Workflows
- Ready to develop → `planning` (AVAILABLE) → `bdd-workflow` (NOT AVAILABLE) or `tdd-workflow` (NOT AVAILABLE)
- Needs clarification → Schedule stakeholder discussion
- Should split → `story-split` workflow, NOT AVAILABLE
- Too uncertain → `spike` workflow for research, NOT AVAILABLE
