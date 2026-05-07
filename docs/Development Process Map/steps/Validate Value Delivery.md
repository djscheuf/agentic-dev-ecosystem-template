# Validate Value Delivery

**Inputs**: Many [[../artifacts/Deployed Code]], Many [[../artifacts/Usage Instrumentation]]  
**Outputs**: Value validation data

**Description**: Validate that deployed story delivers promised value through instrumented value moments. Instrumentation is a cross-cutting concern handled during design session.

**Value Moments** (identified during Feature Refinement):
- When/whether user gets value from feature
- Must be instrumented for measurement

**Instrumentation Approach**:
- Logged by backend or frontend frameworks
- Capture specific user workflow moments
- Focus on "value in use" events
- User perspective: "When was this valuable?"

**Examples of Value Moments**:
- API endpoint calls (usage indication)
- Report generation
- Workflow initiation
- Other value-indicating events

**Validation Method**:
- First glimpse: Usage data from instrumented moments
- Analytics: Later analysis to assign "value alert" moments
- Feedback loop: Usage data → Product Owner/stakeholders

**MVP Principle**: User MUST get more value out than effort put in
