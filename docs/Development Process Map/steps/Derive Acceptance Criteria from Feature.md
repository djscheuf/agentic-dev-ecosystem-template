# Derive Acceptance Criteria from Feature

**Inputs**: One [[../artifacts/Feature Definition]], Many [[../artifacts/User Persona]], Many [[../artifacts/Jobs-to-be-Done]], One [[../artifacts/Current System State]]  
**Outputs**: Many [[../artifacts/Acceptance Criteria]]

**Description**: Transform the feature definition into testable acceptance criteria using BDD format. Developers propose ACs based on the feature, Product Owner verifies coverage. Work through happy paths, boundary conditions, and error handling for each workflow step and persona combination.

**Process**:
1. Developers analyze feature and propose ACs in Given-When-Then format
2. Express ACs as future-state statements capturing value moments
3. Use Functional Alchemy to identify workflow steps (work backward from target output)
4. Ensure coverage: happy path → boundary conditions → error handling
5. Cover all combinations: workflow step × persona
6. Product Owner verifies field coverage

**Quality Gates**:
- Junior Developer Test: Can explain future system state from ACs
- Product Owner Test: Confirms all fields/scenarios covered
- All ACs testable in Gherkin format

**Remediation**:
- If junior dev can't explain: Simplify/clarify ACs (not add more detail)
- If PO identifies gaps: Add AC for gap
- Re-run the quality gates after AC change.
