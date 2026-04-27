# Implement Using TDD Workflow

**Inputs**: Many [[../artifacts/Implementation Plan]]  
**Outputs**: Many [[../artifacts/Deployed Code]], Many [[../artifacts/Test Case]] (passing)

**Description**: Execute implementation plans using Test-Driven Development. Each task is "make this test pass" with the smallest possible implementation. Progress tracked by updating plan checkboxes.

**Red-Green-Refactor Cycle**:

**Red-Green** (rapid iteration per test):
1. Write test code that fails (Red)
2. Write code that makes it pass (Green)

**Refactor** (after component completion):
1. Simplify component code while passing tests
2. Look for "rule of three" overlap in surrounding code
3. Refactor for commonality
4. All tests must continue passing

**Progress Tracking**:
- Update implementation plan checkboxes as tasks complete
- Mark both TOC and individual tasks
- Add tasks if unexpected work discovered
- Living document: "here was my plan, here's where I'm going"

**Continuous Quality Gates** (per component):
- All existing unit tests pass (not just new ones)
- Broken tests fixed by:
  - Update test expectations (if story modifies behavior)
  - Fix usage of modified code (new parameters, etc.)
