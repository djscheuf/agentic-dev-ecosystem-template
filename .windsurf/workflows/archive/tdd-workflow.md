# TDD Workflow (Composite)

## Purpose
Complete Test-Driven Development cycle for implementing a feature or fixing a bug.

## Overview
This workflow orchestrates the four TDD phases in a continuous cycle until the feature is complete.

```
┌─────────────────────────────────────────────────────────────────┐
│                         TDD CYCLE                                │
│                                                                  │
│   ┌──────────┐    ┌─────────┐    ┌──────────┐    ┌───────────┐ │
│   │  THINK   │───▶│   RED   │───▶│  GREEN   │───▶│ REFACTOR  │ │
│   │          │    │         │    │          │    │           │ │
│   │ Plan     │    │ Write   │    │ Make it  │    │ Clean up  │ │
│   │ Tests    │    │ Failing │    │ Pass     │    │ Code      │ │
│   │          │    │ Test    │    │          │    │           │ │
│   └──────────┘    └─────────┘    └──────────┘    └─────┬─────┘ │
│        ▲                                               │       │
│        │                                               │       │
│        │         More tests in plan?                   │       │
│        └───────────────YES─────────────────────────────┘       │
│                         │                                       │
│                         NO                                      │
│                         ▼                                       │
│                    ┌─────────┐                                  │
│                    │  DONE   │                                  │
│                    └─────────┘                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Workflow Chain

### Phase 1: Think
**Workflow:** /tdd-think.md
**Duration:** 10-20 minutes
**Output:** Prioritized test plan

```
Execute: tdd-think
├── Understand requirement
├── Identify all test cases
├── Prioritize by importance
└── Output: Test plan document
```

### Phase 2-4: Red-Green-Refactor Loop
**Repeat for each test in the plan**

```
FOR each test in test_plan:
    
    Execute: /tdd-red.md
    ├── Write single failing test
    ├── Verify failure is correct
    └── Output: One red test
    
    Execute: /tdd-green.md
    ├── Write minimal passing code
    ├── Verify test passes
    └── Output: All tests green
    
    Execute: /tdd-refactor.md
    ├── Identify improvements
    ├── Apply refactorings (tests stay green)
    └── Output: Clean code, all green
    
    Commit changes with message:
    "feat: [description] - test [N] of [total]"
```

## Entry Points

### Starting Fresh
```
1. Receive requirement/story
2. Run: analyze-user-story (if story provided)
3. Run: tdd-think (creates test plan)
4. Begin Red-Green-Refactor loop
```

### Continuing Existing Work
```
1. Review existing test plan
2. Identify next unimplemented test
3. Run: /tdd-red.md (write next test)
4. Continue Red-Green-Refactor loop
```

### Bug Fix Mode
```
1. Run: /tdd-red.md (write test that exposes bug)
2. Verify test fails (reproduces bug)
3. Run: /tdd-green.md (fix the bug)
4. Run: /tdd-refactor.md (clean up if needed)
```

## State Tracking

### Test Plan Checklist
```markdown
## Feature: [Name]
## Status: In Progress

### Test Plan
- [x] Test 1: Happy path - basic scenario ✓
- [x] Test 2: Validation - empty input ✓
- [ ] Test 3: Validation - invalid format ← CURRENT
- [ ] Test 4: Edge case - maximum length
- [ ] Test 5: Error handling - service failure

### Current Phase: RED
### Next Action: Write failing test for Test 3
```

## Timing Guidelines

| Phase    | Typical Duration | Max Duration |
|----------|------------------|--------------|
| Think    | 10-20 min        | 30 min       |
| Red      | 2-5 min          | 10 min       |
| Green    | 2-10 min         | 20 min       |
| Refactor | 5-15 min         | 30 min       |

**If exceeding max duration:**
- Think: Break feature into smaller pieces
- Red: Test may be too complex, simplify
- Green: Taking too long means test is too big
- Refactor: Stop and continue with next test

## Commit Strategy

### During TDD
```bash
# After each Green-Refactor cycle
git add -A
git commit -m "test: add [test description]"
git commit -m "feat: implement [behavior]"
git commit -m "refactor: [improvement description]"
```

### On Completion
```bash
# Squash if desired for clean history
git rebase -i HEAD~[number_of_commits]

# Or keep granular history for traceability
git push origin feature/[name]
```

## Integration with Other Workflows

### Before TDD
```
planning → analyze-user-story → tdd (this workflow)
```

### During TDD (if needed)
```
tdd-think → explore-codebase (understand existing patterns)
tdd-red → explore-codebase (find similar tests)
```

### After TDD
```
tdd → code-review → merge
```

## Success Criteria

### Feature Complete When:
- [ ] All tests from plan are implemented
- [ ] All tests pass
- [ ] Code coverage meets team standards
- [ ] No obvious code smells remain
- [ ] Documentation updated (if required)

## Troubleshooting

### "I can't think of test cases"
→ Review acceptance criteria
→ Ask: What could go wrong?
→ Use: explore-codebase to find similar features

### "Test is too hard to write"
→ Test scope too large, break it down
→ Missing test utilities, create helpers
→ Design issue, reconsider approach

### "Green phase taking too long"
→ Test covers too much behavior
→ Go back to Red, simplify the test
→ Consider if requirement is too complex

### "Refactoring breaks tests"
→ Change too large, undo and try smaller
→ Tests may be testing implementation
→ Consider if tests need improvement too
