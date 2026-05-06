# ADR-008: Devin CLI Saga Orchestration Harness

**Date:** 2026-05-01  
**Updated:** 2026-05-03  
**Status:** Implemented (Partial)

## Decision

Replace the Cascade skills-based system with a graph-based saga orchestration harness that uses Devin CLI as the execution engine. The orchestrator provides deterministic control over step sequencing, composable workflows, and verification-driven routing.

## Context

The Cascade skills-based architecture (ADR-003) was designed to provide modularity and composability through skill invocation and workflow coordination. However, we encountered critical limitations:

**Non-deterministic execution:** Cascade does not provide programmatic control over workflow execution. The agent may or may not follow workflow instructions consistently, making deterministic orchestration impossible.

**Budget enforcement:** Devin CLI does not support budget limits via command-line flags. ACU limits are managed at the account level in Devin Cloud, not at the invocation level.

To address these limitations, we implemented a simpler, incremental approach:
- **Graph-based orchestration** instead of state machines
- **Timeout-based limits** instead of budget tracking
- **Composable sagas** for workflow reuse
- **Sentinel files moved to step governance** (not orchestration concern)

## Requirements

The implemented system provides:

1. **Deterministic step sequencing** - Graph-based control over which steps execute and in what order
2. **Verification-driven routing** - Conditional routing (pass/fail) based on verification results
3. **Timeout enforcement** - Hard timeouts per step, soft timeouts per sub-saga
4. **Composable sagas** - Sub-sagas as first-class nodes in the workflow graph
5. **Traversal limits** - Prevent infinite loops via per-connection traversal tracking
6. **Recursion depth limits** - Prevent infinite sub-saga nesting

**Future requirements** (not yet implemented):
- **File-based state persistence** - Saga state survives crashes and can be resumed
- **Interactive command injection** - Ability to inject additional commands into running sessions
- **Parallel execution** - Support for concurrent step execution where dependencies allow

## Architecture

### Core Components (Implemented)

**1. Saga Models** (`orchestrator/saga_models.py`)
- Data structures for saga definitions
- Node types: `step` (atomic execution) and `saga` (sub-workflow)
- Connection types: `then` (directed) and `pass`/`fail` (branching)
- Traversal limits and recursion depth tracking

**2. Saga Validator** (`orchestrator/saga_validator.py`)
- Validates saga definitions before execution
- Checks graph connectivity (all paths lead to `end`)
- Validates node references (steps exist in `steps/`, sagas exist in `sagas/`)
- Detects circular references (warnings, not errors)
- Validates recursion depth limits

**3. Saga Executor** (`orchestrator/saga_executor.py`)
- Executes workflow graph with node-by-node traversal
- Routes based on exit codes (0=pass, non-zero=fail)
- Tracks traversal counts per connection (independent per saga instance)
- Handles sub-saga execution with nested executors
- Unified logging with indentation for nesting depth

**4. Devin Wrapper** (`orchestrator/devin_wrapper.py`)
- Executes individual steps via Devin CLI non-interactive mode (`-p` flag)
- Loads prompts from files or inline strings
- Enforces timeouts via Python subprocess (hard limit)
- Runs verification scripts embedded in step definitions
- Returns exit codes for routing decisions

**5. Verification Scripts**
- Embedded in step definitions (`steps/<name>/step.json`)
- Perform quantitative checks on step output
- Return pass/fail via exit codes (0=pass, non-zero=fail)
- No sentinel files required at orchestration level

### Future Components (Not Yet Implemented)

**State Persistence Layer**
- Will persist saga state to filesystem (`.sagas/<saga-id>/`)
- Will enable crash recovery and resume capability
- Will track execution history and state transitions

### Saga Definition Format (Implemented)

Sagas are defined as JSON files with graph structure:

```json
{
  "name": "composite-example",
  "max_recursion_depth": 10,
  "start": "validate",
  "nodes": {
    "validate": {
      "type": "step",
      "reference": "example",
      "timeout": 60
    },
    "retry-workflow": {
      "type": "saga",
      "reference": "retry-saga.json",
      "timeout": 300
    },
    "final-check": {
      "type": "step",
      "reference": "example",
      "timeout": 30
    }
  },
  "connections": [
    {
      "node": "validate",
      "pass": {"target": "retry-workflow"},
      "fail": {"target": "end"}
    },
    {
      "node": "retry-workflow",
      "then": {"target": "final-check"}
    },
    {
      "node": "final-check",
      "then": {"target": "end"}
    }
  ]
}
```

**Key Properties:**
- `name`: Saga identifier
- `max_recursion_depth`: Limit for sub-saga nesting (default: 50)
- `start`: Initial node to execute
- `nodes`: Explicit node registry with type (`step` or `saga`), reference, and optional timeout
- `connections`: Routing rules with `node` (origin), and either `then` (directed) or `pass`/`fail` (branching)
- `traversal_limit`: Optional per-connection limit to prevent infinite loops

**Connection Types:**
- **Directed (`then`)**: Unconditional routing to next node
- **Branching (`pass`/`fail`)**: Conditional routing based on exit code (0=pass, non-zero=fail)

### File Structure (Implemented)

```
sagas/
  example-saga.json         # Simple linear workflow
  retry-saga.json           # Retry with traversal limit
  composite-example.json    # Demonstrates sub-saga composition

steps/
  <step-name>/
    step.json               # Step definition (prompt, model, timeout, verify)
    prompts/                # Optional prompt files
    scripts/                # Optional verification scripts

orchestrator/
  saga_models.py            # Data structures
  saga_validator.py         # Validation logic
  saga_executor.py          # Execution engine
  devin_wrapper.py          # Step execution wrapper
  run_saga.py               # CLI entry point

.process/
  saga-logs/
    <saga-name>_<timestamp>.log  # Unified execution log
```

### File Structure (Future - State Persistence)

```
.sagas/
  <saga-id>/
    saga-definition.json    # Saga definition snapshot
    state.json              # Current saga state
    state.pending.json      # Write-ahead log for transitions
    history.json            # State transition log
    steps/
      <step-id>/
        input.json          # Step input parameters
        output.json         # Step output (if completed)
        verification.json   # Verification results
        session.log         # Devin session output
```

### Execution Flow

1. **Load and Validate**: Saga definition loaded from JSON, validated for correctness
2. **Execute Nodes**: Starting from `start` node, execute each node in sequence
3. **Step Execution**: For step nodes, invoke `devin_wrapper.py` with step definition
4. **Sub-Saga Execution**: For saga nodes, create nested executor with shared logger
5. **Route Based on Exit Code**: Use exit code (0=pass, non-zero=fail) to determine next node
6. **Track Traversals**: Increment connection traversal count, check against limits
7. **Continue Until End**: Repeat until reaching `end` node or hitting a limit
8. **Log Everything**: Unified log with indentation showing nesting depth

### Timeout Enforcement

**Step Timeouts (Hard Limit):**
- Specified in node definition: `"timeout": 60`
- Enforced via Python `subprocess.run(timeout=...)`
- Process forcibly terminated (SIGTERM) if exceeded
- Returns exit code 124 on timeout

**Saga Timeouts (Soft Warning):**
- Specified in saga node definition
- Logged as warning if exceeded
- Does not terminate execution (sub-saga manages its own timeouts)

### Retry and Correction Patterns

**Traversal-Limited Retry:**
```json
{
  "node": "validate",
  "pass": {"target": "end"},
  "fail": {"target": "validate", "traversal_limit": 3}
}
```
- Step retries itself on failure
- Limited to 3 traversals of the fail connection
- Saga exits with failure if limit exceeded

**Correction via Separate Node:**
```json
{
  "node": "implement",
  "pass": {"target": "end"},
  "fail": {"target": "debug"}
},
{
  "node": "debug",
  "then": {"target": "implement", "traversal_limit": 5}
}
```
- Failure routes to separate debug/correction node
- Correction node routes back to original node
- Limited to 5 correction attempts

**Note**: Error context injection not yet implemented. Correction nodes currently work with same inputs as original nodes.

## Rationale

**Why Devin CLI over Cascade:**
- Devin CLI provides programmatic control over execution
- Non-interactive mode (`-p`) enables deterministic invocation
- Timeout enforcement via subprocess management
- Clear exit codes for routing decisions

**Why Graph-Based over State Machine:**
- Simpler mental model: nodes and connections
- Easier to visualize and reason about
- Natural support for composability (sub-sagas as nodes)
- No need for explicit state tracking (execution is the state)

**Why Timeout-Based Limits over Budget Tracking:**
- Devin CLI does not support budget enforcement via flags
- ACU limits managed at account level in Devin Cloud
- Timeouts provide predictable execution bounds
- Recursion depth prevents infinite sub-saga nesting

**Why Composable Sagas:**
- Enables workflow reuse and modularity
- Sub-sagas are first-class nodes in the graph
- Independent traversal tracking per saga instance
- Unified logging with indentation shows nesting

**Why File-Based Definitions:**
- Simple, inspectable, debuggable
- No external dependencies (databases, message queues)
- Easy to version control saga definitions
- JSON format is human-readable and machine-parseable

## Trade-offs

**Advantages:**
- Deterministic step execution and verification
- Explicit control over retry and correction flows
- Composable workflows via sub-sagas
- Timeout enforcement prevents runaway execution
- Traversal limits prevent infinite loops
- Saga definitions are declarative and reusable
- Unified logging with clear execution trace

**Disadvantages:**
- No budget tracking (ACU limits managed at account level)
- No state persistence yet (no crash recovery)
- No error context injection in correction loops
- Requires Devin CLI installation and configuration
- Verification scripts must be idempotent (may run multiple times on retry)

## Implementation Status

**Completed (2026-05-03):**
1. ✅ Core orchestrator with graph-based execution
2. ✅ Devin wrapper with timeout enforcement
3. ✅ Saga validator with graph connectivity checks
4. ✅ Composable sagas (sub-sagas as nodes)
5. ✅ Traversal limits and recursion depth protection
6. ✅ Unified logging with nesting indentation
7. ✅ Example sagas demonstrating patterns

**Not Yet Implemented:**
- ⏳ State persistence and crash recovery
- ⏳ Error context injection in correction loops
- ⏳ Interactive command injection
- ⏳ Parallel execution
- ⏳ Migration of existing TDD workflows to saga format

## Related Decisions

- [ADR-003: Skills-Based Architecture](ADR-003-skills-based-architecture.md) - Superseded by this decision for workflow orchestration
- [ADR-004: Skill Output Contracts & Sentinel Files](ADR-004-skill-output-contracts.md) - Sentinel files moved to step governance (not orchestration concern)
- [ADR-005: Quantitative vs. Qualitative Analysis Separation](ADR-005-analysis-separation.md) - Verification scripts unchanged
- [ADR-007: Skill Input Independence](ADR-007-skill-input-independence.md) - Steps remain loosely coupled

## Future Enhancements

**High Priority:**
- State persistence and crash recovery
- Error context injection in correction loops
- Budget tracking and reporting (informational, not enforced)

**Medium Priority:**
- Parallel step execution using worker pools
- Interactive command injection during execution
- Web UI for saga monitoring and control

**Low Priority:**
- Distributed execution across multiple machines
- Devin custom tools for step-specific capabilities
- Saga templates and parameterization
