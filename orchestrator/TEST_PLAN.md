# Saga Orchestrator - Test Plan

**Status**: Not Implemented  
**Last Updated**: 2026-05-03

This document outlines comprehensive test cases for the saga orchestrator components. All tests are currently **not implemented**.

---

## Test Coverage Summary

| Component | Total Tests | Implemented | Coverage |
|-----------|-------------|-------------|----------|
| saga_models.py | 21 | 0 | 0% |
| saga_validator.py | 24 | 0 | 0% |
| saga_executor.py | 35 | 0 | 0% |
| devin_wrapper.py | 16 | 0 | 0% |
| Integration | 8 | 0 | 0% |
| **TOTAL** | **104** | **0** | **0%** |

---

## 1. saga_models.py Tests

### 1.1 Happy Path Tests (9 tests)

| ID | Test Case | Status | Priority |
|----|-----------|--------|----------|
| M-H-01 | Parse simple saga with minimal fields | ❌ Not Implemented | High |
| M-H-02 | Parse directed connection with `then` | ❌ Not Implemented | High |
| M-H-03 | Parse branching connection with `pass`/`fail` | ❌ Not Implemented | High |
| M-H-04 | Parse connection with traversal limit | ❌ Not Implemented | Medium |
| M-H-05 | Parse connection without traversal limit (None) | ❌ Not Implemented | Medium |
| M-H-06 | Parse node with timeout specified | ❌ Not Implemented | Medium |
| M-H-07 | Parse node without timeout (None) | ❌ Not Implemented | Medium |
| M-H-08 | Parse saga with custom max_recursion_depth | ❌ Not Implemented | Medium |
| M-H-09 | Parse saga with default max_recursion_depth (50) | ❌ Not Implemented | Medium |

### 1.2 Edge Cases (4 tests)

| ID | Test Case | Status | Priority |
|----|-----------|--------|----------|
| M-E-01 | Traversal limit of 0 (immediate failure) | ❌ Not Implemented | Low |
| M-E-02 | Very large traversal limit (999999) | ❌ Not Implemented | Low |
| M-E-03 | Timeout of 0 (immediate timeout) | ❌ Not Implemented | Low |
| M-E-04 | Very large timeout (86400 seconds) | ❌ Not Implemented | Low |

### 1.3 Error Handling Tests (8 tests)

| ID | Test Case | Status | Priority |
|----|-----------|--------|----------|
| M-ER-01 | Missing `name` property raises ValueError | ❌ Not Implemented | Critical |
| M-ER-02 | Missing `start` property raises ValueError | ❌ Not Implemented | Critical |
| M-ER-03 | Empty or missing `nodes` section | ❌ Not Implemented | Critical |
| M-ER-04 | Connection missing `node` property | ❌ Not Implemented | Critical |
| M-ER-05 | Connection with neither `then` nor `pass`/`fail` | ❌ Not Implemented | Critical |
| M-ER-06 | Connection with only `pass` (missing `fail`) | ❌ Not Implemented | Critical |
| M-ER-07 | Connection with only `fail` (missing `pass`) | ❌ Not Implemented | Critical |
| M-ER-08 | Node missing `type` or `reference` | ❌ Not Implemented | Critical |

---

## 2. saga_validator.py Tests

### 2.1 Happy Path Tests (5 tests)

| ID | Test Case | Status | Priority |
|----|-----------|--------|----------|
| V-H-01 | Valid simple saga (single step → end) | ❌ Not Implemented | High |
| V-H-02 | Valid branching saga (pass/fail routes) | ❌ Not Implemented | High |
| V-H-03 | Valid retry saga (self-referencing with limit) | ❌ Not Implemented | High |
| V-H-04 | Valid composite saga (steps + sub-sagas) | ❌ Not Implemented | High |
| V-H-05 | Circular reference produces warning (not error) | ❌ Not Implemented | Medium |

### 2.2 Edge Cases (5 tests)

| ID | Test Case | Status | Priority |
|----|-----------|--------|----------|
| V-E-01 | Empty saga (no nodes defined) | ❌ Not Implemented | Medium |
| V-E-02 | Single node saga (start → end) | ❌ Not Implemented | Low |
| V-E-03 | Max recursion depth at boundary (exactly 50) | ❌ Not Implemented | Medium |
| V-E-04 | Deeply nested sub-sagas (multiple levels) | ❌ Not Implemented | Medium |
| V-E-05 | Multiple paths to end (complex convergence) | ❌ Not Implemented | Low |

### 2.3 Error Handling Tests (14 tests)

| ID | Test Case | Status | Priority |
|----|-----------|--------|----------|
| V-ER-01 | Missing `start` property | ❌ Not Implemented | Critical |
| V-ER-02 | Start is 'end' (invalid) | ❌ Not Implemented | Critical |
| V-ER-03 | Start node not defined in nodes section | ❌ Not Implemented | Critical |
| V-ER-04 | Step node references non-existent step folder | ❌ Not Implemented | Critical |
| V-ER-05 | Saga node references non-existent saga file | ❌ Not Implemented | Critical |
| V-ER-06 | Dead-end node (no outgoing connections) | ❌ Not Implemented | Critical |
| V-ER-07 | Unreachable end (graph not closed) | ❌ Not Implemented | Critical |
| V-ER-08 | Connection references undefined node | ❌ Not Implemented | Critical |
| V-ER-09 | Branching without `fail` | ❌ Not Implemented | Critical |
| V-ER-10 | Branching without `pass` | ❌ Not Implemented | Critical |
| V-ER-11 | Exceeds max recursion depth (> 50 levels) | ❌ Not Implemented | Critical |
| V-ER-12 | Invalid node type (not "step" or "saga") | ❌ Not Implemented | Critical |
| V-ER-13 | Malformed sub-saga JSON file | ❌ Not Implemented | Medium |
| V-ER-14 | Sub-saga validation failure propagates | ❌ Not Implemented | Medium |

---

## 3. saga_executor.py Tests

### 3.1 Happy Path Tests (7 tests)

| ID | Test Case | Status | Priority |
|----|-----------|--------|----------|
| E-H-01 | Execute simple linear saga successfully | ❌ Not Implemented | High |
| E-H-02 | Execute branching saga (pass path) | ❌ Not Implemented | High |
| E-H-03 | Execute branching saga (fail path) | ❌ Not Implemented | High |
| E-H-04 | Execute retry saga (retries until success) | ❌ Not Implemented | High |
| E-H-05 | Execute composite saga (parent + sub-saga) | ❌ Not Implemented | High |
| E-H-06 | Output propagation between steps | ❌ Not Implemented | High |
| E-H-07 | Sub-saga outputs passed to parent's next node | ❌ Not Implemented | High |

### 3.2 Edge Cases (5 tests)

| ID | Test Case | Status | Priority |
|----|-----------|--------|----------|
| E-E-01 | Empty initial inputs | ❌ Not Implemented | Medium |
| E-E-02 | Step with no outputs | ❌ Not Implemented | Medium |
| E-E-03 | Immediate end (start → end directly) | ❌ Not Implemented | Low |
| E-E-04 | Nested saga at max recursion depth | ❌ Not Implemented | Medium |
| E-E-05 | Step completes just before timeout | ❌ Not Implemented | Low |

### 3.3 Error Handling Tests (13 tests)

| ID | Test Case | Status | Priority |
|----|-----------|--------|----------|
| E-ER-01 | Non-existent saga file | ❌ Not Implemented | Critical |
| E-ER-02 | Invalid saga definition (fails validation) | ❌ Not Implemented | Critical |
| E-ER-03 | Step execution failure with no fail route | ❌ Not Implemented | Critical |
| E-ER-04 | Traversal limit exceeded on connection | ❌ Not Implemented | Critical |
| E-ER-05 | Step timeout exceeded (hard timeout) | ❌ Not Implemented | Critical |
| E-ER-06 | Sub-saga timeout exceeded (soft warning) | ❌ Not Implemented | Critical |
| E-ER-07 | Missing step executable (step.json not found) | ❌ Not Implemented | Medium |
| E-ER-08 | Node not found in saga definition | ❌ Not Implemented | Critical |
| E-ER-09 | No connection from node | ❌ Not Implemented | Critical |
| E-ER-10 | Recursion depth exceeded during execution | ❌ Not Implemented | Critical |
| E-ER-11 | Sub-saga execution returns failure | ❌ Not Implemented | High |
| E-ER-12 | Invalid node type during execution | ❌ Not Implemented | Medium |
| E-ER-13 | Malformed outputs.json from step | ❌ Not Implemented | Medium |

### 3.4 Timeout Tests (5 tests)

| ID | Test Case | Status | Priority |
|----|-----------|--------|----------|
| E-T-01 | Step timeout enforcement (hard, process killed) | ❌ Not Implemented | Critical |
| E-T-02 | Sub-saga timeout warning (soft, logged only) | ❌ Not Implemented | Critical |
| E-T-03 | Very short timeout (1 second) triggers immediately | ❌ Not Implemented | Critical |
| E-T-04 | No timeout specified (runs indefinitely) | ❌ Not Implemented | Medium |
| E-T-05 | Nested saga timeout independent of parent | ❌ Not Implemented | Critical |

### 3.5 Traversal Tracking Tests (5 tests)

| ID | Test Case | Status | Priority |
|----|-----------|--------|----------|
| E-TR-01 | Independent traversal tracking per saga instance | ❌ Not Implemented | Critical |
| E-TR-02 | Traversal limit enforced on pass route | ❌ Not Implemented | Critical |
| E-TR-03 | Traversal limit enforced on fail route | ❌ Not Implemented | Critical |
| E-TR-04 | Traversal limit enforced on then route | ❌ Not Implemented | Critical |
| E-TR-05 | Traversal counts persist throughout execution | ❌ Not Implemented | High |

---

## 4. devin_wrapper.py Tests

### 4.1 Happy Path Tests (6 tests)

| ID | Test Case | Status | Priority |
|----|-----------|--------|----------|
| D-H-01 | Execute step successfully (exit code 0) | ❌ Not Implemented | High |
| D-H-02 | Execute with verification (both pass) | ❌ Not Implemented | High |
| D-H-03 | Execute with input files | ❌ Not Implemented | Medium |
| D-H-04 | Execute without input files | ❌ Not Implemented | Medium |
| D-H-05 | Prompt loaded from external file | ❌ Not Implemented | Medium |
| D-H-06 | Prompt specified as string directly | ❌ Not Implemented | Medium |

### 4.2 Edge Cases (3 tests)

| ID | Test Case | Status | Priority |
|----|-----------|--------|----------|
| D-E-01 | Empty prompt file | ❌ Not Implemented | Low |
| D-E-02 | Very long prompt content | ❌ Not Implemented | Low |
| D-E-03 | No verification script specified | ❌ Not Implemented | Medium |

### 4.3 Error Handling Tests (7 tests)

| ID | Test Case | Status | Priority |
|----|-----------|--------|----------|
| D-ER-01 | Missing step definition file (step.json) | ❌ Not Implemented | Critical |
| D-ER-02 | Malformed step.json (invalid JSON) | ❌ Not Implemented | Critical |
| D-ER-03 | Missing `prompt` property | ❌ Not Implemented | Critical |
| D-ER-04 | Missing `model` property | ❌ Not Implemented | Critical |
| D-ER-05 | Prompt file not found | ❌ Not Implemented | Medium |
| D-ER-06 | Verification script not found | ❌ Not Implemented | Medium |
| D-ER-07 | Verification script fails (non-zero exit) | ❌ Not Implemented | High |

---

## 5. Integration Tests

### 5.1 End-to-End Scenarios (8 tests)

| ID | Test Case | Status | Priority |
|----|-----------|--------|----------|
| I-01 | Complete multi-step workflow (start to finish) | ❌ Not Implemented | High |
| I-02 | Retry until success (within limit) | ❌ Not Implemented | High |
| I-03 | Retry until limit exceeded (fails) | ❌ Not Implemented | High |
| I-04 | Nested saga execution (3+ levels deep) | ❌ Not Implemented | High |
| I-05 | Mixed success/failure paths in complex saga | ❌ Not Implemented | Medium |
| I-06 | Logging verification (all expected entries) | ❌ Not Implemented | Medium |
| I-07 | Indented logging for nested sagas | ❌ Not Implemented | Medium |
| I-08 | Exit code propagation through saga chain | ❌ Not Implemented | Medium |

---

## Testing Infrastructure Requirements

### Test Framework
- **pytest** - Test runner and framework
- **unittest.mock** - Mocking subprocess, file I/O
- **pytest-timeout** - Timeout test support
- **pytest-cov** - Coverage reporting
- **pytest-xdist** - Parallel test execution

### Directory Structure
```
orchestrator/
├── tests/
│   ├── __init__.py
│   ├── test_saga_models.py          # 21 tests
│   ├── test_saga_validator.py       # 24 tests
│   ├── test_saga_executor.py        # 35 tests
│   ├── test_devin_wrapper.py        # 16 tests
│   ├── test_integration.py          # 8 tests
│   ├── conftest.py                  # Shared fixtures
│   └── fixtures/
│       ├── sagas/
│       │   ├── valid/
│       │   │   ├── simple.json
│       │   │   ├── branching.json
│       │   │   ├── retry.json
│       │   │   └── composite.json
│       │   └── invalid/
│       │       ├── no_start.json
│       │       ├── dead_end.json
│       │       ├── unreachable_end.json
│       │       └── ...
│       └── steps/
│           ├── mock_success/
│           │   └── step.json
│           ├── mock_failure/
│           │   └── step.json
│           └── mock_timeout/
│               └── step.json
```

### Mocking Strategy
1. **devin_wrapper execution** - Mock subprocess calls to avoid actual Devin CLI
2. **File system** - Use pytest's `tmp_path` fixture for temporary files
3. **Time-based tests** - Mock datetime for consistent timestamps
4. **Subprocess timeouts** - Mock TimeoutExpired exceptions

### Coverage Goals
- **Overall**: 90%+ line coverage
- **Critical paths**: 100% coverage (validation, timeout enforcement, traversal limits)
- **Error handling**: 95%+ coverage
- **Edge cases**: 80%+ coverage

---

## Implementation Priority

### Phase 1: Critical Tests (Week 1)
- All validator error handling tests (V-ER-*)
- Executor timeout tests (E-T-*)
- Executor traversal tracking tests (E-TR-*)
- Models error handling tests (M-ER-*)

### Phase 2: Core Functionality (Week 2)
- All happy path tests (V-H-*, E-H-*, M-H-*, D-H-*)
- Executor error handling tests (E-ER-*)
- Devin wrapper error handling tests (D-ER-*)

### Phase 3: Edge Cases & Integration (Week 3)
- All edge case tests (V-E-*, E-E-*, M-E-*, D-E-*)
- Integration tests (I-*)

---

## Test Execution Commands

```bash
# Run all tests
pytest orchestrator/tests/

# Run specific test file
pytest orchestrator/tests/test_saga_validator.py

# Run with coverage
pytest --cov=orchestrator --cov-report=html orchestrator/tests/

# Run only critical priority tests
pytest -m critical orchestrator/tests/

# Run with verbose output
pytest -v orchestrator/tests/

# Run in parallel
pytest -n auto orchestrator/tests/
```

---

## Notes

- **Timeout tests** require careful setup to avoid flaky tests
- **Integration tests** should use isolated temporary directories
- **Mock strategy** critical for devin_wrapper to avoid external dependencies
- **Fixture sagas** should cover all validation error cases
- **Logging tests** should verify both content and indentation
- **Traversal tracking** tests must verify independence between saga instances

---

**Next Steps**:
1. Set up pytest infrastructure
2. Create fixture saga definitions
3. Implement Phase 1 critical tests
4. Set up CI/CD integration
5. Establish coverage baseline
