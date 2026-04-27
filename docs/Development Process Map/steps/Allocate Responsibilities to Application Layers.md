# Allocate Responsibilities to Application Layers

**Inputs**: Many [[../artifacts/Test Case]], One [[../artifacts/Current State Audit]], One [[../artifacts/User Flow Model]]  
**Outputs**: Many [[../artifacts/Layer Responsibilities]]

**Description**: Assign each test case and AC element to the appropriate application layer(s) using responsibility heuristics. This is an iterative "catch ball" negotiation between layers, not strictly unidirectional.

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

**Critical Principle**: "Where is the information available to act?" - Responsibility emerges from where new information/behavior originates.

**Process**:
1. Identify responsibilities for each layer based on heuristics
2. Determine if layer is touched by story ACs
3. If data model unchanged: Skip data layer planning
4. If endpoints exist: Skip backend planning
5. Negotiate between layers iteratively (Hoshin Kanri "catch ball")
