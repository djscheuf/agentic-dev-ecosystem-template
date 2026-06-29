# Implementation Workstreams

This directory contains the breakdown of the per-step agent configuration feature into parallel workstreams.

## Workstream Overview

| ID | Name | Priority | Phase | Effort | Dependencies |
|---|---|---|---|---|---|
| 01 | Core Implementation | Critical | Foundations | 3.5h | None |
| 02 | Validation | High | Foundations | 2h | 01 |
| 03 | Unit Testing | High | Testing | 5h | 01 |
| 04 | Integration Testing | High | Testing | 6h | 01, 02, 03 |
| 05 | Documentation | Medium | Documentation | 4h | 01, 04 |

**Total Effort:** 20.5 hours

## Workstream Dependencies

```
01-core-implementation (3.5h)
├── 02-validation (2h)
├── 03-unit-testing (5h)
└── 04-integration-testing (6h)
    └── 05-documentation (4h)
```

## Execution Strategy

### Phase 1: Foundations (Sequential)
1. **01-core-implementation** - Extend StepDefinition and DevinWrapper
   - Must complete first; blocks all other work
   - Estimated: 3.5 hours

2. **02-validation** - Add validation to saga validator
   - Can start after 01 completes
   - Estimated: 2 hours

### Phase 2: Testing (Parallel)
3. **03-unit-testing** - Unit tests for StepDefinition and DevinWrapper
   - Can run in parallel with 02-validation
   - Estimated: 5 hours

4. **04-integration-testing** - Integration tests for saga execution
   - Depends on 01, 02, and 03
   - Estimated: 6 hours

### Phase 3: Documentation (Sequential)
5. **05-documentation** - Schema, examples, and troubleshooting guide
   - Can start after 04 completes
   - Estimated: 4 hours

## Critical Path

```
01-core-implementation (3.5h)
  ↓
02-validation (2h)
  ↓
04-integration-testing (6h)
  ↓
05-documentation (4h)

Total Critical Path: 15.5 hours
```

## Parallel Opportunities

- **03-unit-testing** can run in parallel with **02-validation**
  - Both depend on 01-core-implementation
  - Can save ~2 hours by parallelizing

## Workstream Details

### [01-core-implementation.stream.json](01-core-implementation.stream.json)
**Extend StepDefinition and DevinWrapper classes**

- Add agent_config field to StepDefinition
- Implement path resolution (relative to step directory)
- Update DevinWrapper.build_devin_command() to use step-specific config
- Fall back to global config if not specified

**Acceptance Criteria:**
- StepDefinition accepts agent_config field
- Path resolution works for relative and absolute paths
- DevinWrapper uses step-specific config
- Fallback to global config works

### [02-validation.stream.json](02-validation.stream.json)
**Add validation for agent_config files**

- Validate agent_config file existence in saga validator
- Check file is readable
- Provide clear error messages
- Handle missing global config fallback case

**Acceptance Criteria:**
- Saga validation fails if agent_config file missing
- Error messages are clear and actionable
- Validation passes for valid configurations
- Backward compatibility maintained

### [03-unit-testing.stream.json](03-unit-testing.stream.json)
**Unit tests for StepDefinition and DevinWrapper**

- Test StepDefinition with/without agent_config
- Test path resolution (relative, absolute, edge cases)
- Test DevinWrapper command building
- Test fallback to global config

**Acceptance Criteria:**
- All unit tests pass
- Coverage includes happy path and edge cases
- Tests verify backward compatibility

### [04-integration-testing.stream.json](04-integration-testing.stream.json)
**Integration tests for saga execution**

- Create test fixtures (steps with/without agent_config)
- Test saga execution with step-specific config
- Test saga validation with missing/valid config
- Test backward compatibility with existing steps
- Verify no performance regressions

**Acceptance Criteria:**
- All integration tests pass
- Saga execution works correctly
- Backward compatibility verified
- No performance regressions

### [05-documentation.stream.json](05-documentation.stream.json)
**Documentation and examples**

- Update step.json schema documentation
- Create example step with agent-config.json
- Write troubleshooting guide
- Document permission model and patterns

**Acceptance Criteria:**
- Schema documentation is clear
- Example step is runnable
- Troubleshooting guide covers common issues

## Getting Started

1. **Start with 01-core-implementation**
   - This is the foundation; all other work depends on it
   - Estimated: 3.5 hours

2. **Then proceed with 02-validation and 03-unit-testing in parallel**
   - 02-validation: 2 hours
   - 03-unit-testing: 5 hours
   - Can run in parallel; total time ~5 hours

3. **Then proceed with 04-integration-testing**
   - Depends on 01, 02, and 03
   - Estimated: 6 hours

4. **Finally, complete 05-documentation**
   - Depends on 01 and 04
   - Estimated: 4 hours

## Success Criteria

- All workstreams completed
- All acceptance criteria met
- All tests pass (unit and integration)
- Backward compatibility verified
- Documentation complete and clear
- No performance regressions

## Related Documents

- **Requirement:** `extend-step-agent-config.md`
- **Analysis:** `extend-step-agent-config.analysis.json`
- **Design:** `extend-step-agent-config.design.json`
- **Plan:** `extend-step-agent-config.plan.json`
