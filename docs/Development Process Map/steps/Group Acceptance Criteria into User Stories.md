# Group Acceptance Criteria into User Stories

**Inputs**: Many [[../artifacts/Acceptance Criteria]], One [[../artifacts/Current System State]]  
**Outputs**: Many [[../artifacts/User Story]], One [[../artifacts/Dependency Chain]]

**Description**: Organize acceptance criteria into independently deliverable user stories by analyzing dependencies and applying INVEST criteria. Each story represents a vertical slice of functionality that delivers incremental value.

**Process**:
1. Order ACs by workflow step sequence (from Functional Alchemy)
2. Group logically connected ACs within each workflow step
3. Apply grouping pattern: Happy path + boundary (Story 1), Error handling (Story 2)
4. Identify sequential dependencies from workflow steps
5. Identify logical dependencies from persona × workflow step
6. Determine independence from parallelizable data transformation paths
7. Draw INVEST boundaries around groupings
8. First story includes "activation energy" (framework, routes, landing zone)

**Quality Gates**:
- Each story meets INVEST criteria (Independent, Negotiable, Valuable, Estimable, Small, Testable)
- Story completable in <1 sprint (ideal: 5 human-days)
- 5-7 scenarios max per story (rule of thumb)
- Sum of story ACs = Feature ACs
- Each story delivers value (hard rule: no value = don't build)

**Story Sizing Triggers**:
- Too big: Handles >1 workflow step
- Too small: Not valuable alone → group more to create value
