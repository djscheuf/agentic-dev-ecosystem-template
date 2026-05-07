# Model User Flow Through System

**Inputs**: Many [[../artifacts/Acceptance Criteria]], One [[../artifacts/Current State Audit]], One [[../artifacts/Domain Model]]  
**Outputs**: One [[../artifacts/User Flow Model]]

**Description**: Create a model of the user's flow through the system as a sequence of domain events (not UI clicks). This shows how the story modifies the current reality workflow, focusing on "current reality + one step."

**Process**:
1. Start from current reality workflow (existing persona flow)
2. Identify workflow state transitions
3. Model as sequence of domain events
4. Show story's specific change from current state
5. Developer derives, QA Engineer ensures user/business domain focus

**Scope Difference**:
- Feature refinement: Future reality user workflow (all events)
- Design session: Current reality + one step (story's change)
