# Derive Test Cases from Acceptance Criteria

**Inputs**: Many [[../artifacts/Acceptance Criteria]], One [[../artifacts/Current State Audit]], Many [[../artifacts/User Persona]]  
**Outputs**: Many [[../artifacts/Test Case]]

**Description**: Expand each AC into comprehensive test cases across all application layers. Identify test types (component, unit, integration) and assign implementation priority. Each AC should have at least one test case per affected layer.

**Process**:
1. Go AC-by-AC to expand test cases
2. Identify test type based on assertion needs:
   - Component test: UI validation (e.g., "user sees warning")
   - Unit test: Business logic, computation, service layer
   - Integration test: Cross-layer interactions
3. Separate AC components by layer (natural sifting)
4. Apply priority order: Happy path → Error handling → Edge cases → Corner cases → Security → Layer-specific (accessibility, performance)
5. Classify each AC by kind (happy/error/boundary/permissions/accessibility/performance)
6. Ensure minimum: 1 test per AC, typically 1+ per layer per AC

**Quality Gates**:
- Each AC has at least one test case
- Test types identified (happy/error/boundary/permissions)
- Dependencies on other tests noted
- Non-functional requirements surfaced from standards
