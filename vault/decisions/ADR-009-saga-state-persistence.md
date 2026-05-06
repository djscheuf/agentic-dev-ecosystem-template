# ADR-009: Saga State Persistence with File-Based Storage

**Date:** 2026-05-05  
**Status:** Approved (Not Yet Implemented)

## Decision

Implement file-based state persistence for saga orchestration using a `.process/saga-<hash>/` directory structure. Each saga execution creates a unique folder identified by a hash, containing `saga.json` for state tracking and supporting resume/recovery capabilities.

## Context

The current saga orchestrator (ADR-008) executes workflows deterministically but lacks state persistence. If a saga crashes or is interrupted, there is no way to resume from the last successful step. Additionally, there is no historical record of saga execution for debugging or auditing purposes.

**Current limitations:**
- No crash recovery - interrupted sagas must restart from the beginning
- No execution history - debugging requires parsing logs
- No resume capability - cannot continue from a specific step
- No intermediate artifact storage - steps cannot easily share context
- No sub-saga tracking - parent sagas don't track child saga state

**Requirements for state persistence:**
1. Unique saga instance identification
2. Persistent state across crashes and interruptions
3. Step-by-step execution history with status tracking
4. Support for resume operations
5. Sub-saga relationship tracking
6. Devin session ID capture for continuation flows
7. Future support for intermediate artifact storage

## Architecture

### Saga Instance Identification

Each saga execution is assigned a unique identifier using a hash of the saga name, input path, and invocation timestamp:

```python
import hashlib
from datetime import datetime

def generate_saga_id(saga_name: str, input_path: str) -> str:
    """
    Generate unique saga ID from name, input path, and timestamp.
    
    Args:
        saga_name: Name of the saga being executed
        input_path: Path to input file or string representation of input
    
    Returns:
        8-character hash prefix (e.g., 'a3f2b9c1')
    """
    timestamp = datetime.now().isoformat()
    content = f"{saga_name}:{input_path}:{timestamp}"
    hash_full = hashlib.sha256(content.encode()).hexdigest()
    return hash_full[:8]  # Use first 8 characters
```

**Example:** `saga-a3f2b9c1`

**Rationale:** Using the input path (rather than saga definition path) in the hash ensures that:
- Different inputs to the same saga produce different IDs
- The same input re-run produces a different ID (due to timestamp)
- The hash is unique per invocation, not per saga definition

### Directory Structure

```
.process/
  saga-<hash>/
    saga.json              # Saga state file
    <step-name>/           # Per-step artifacts (future)
      input.json
      output.json
      session.log
```

**Location:** The `.process/` directory is created in the same directory where the orchestrator is invoked (current working directory).

### Saga State File Format

The `saga.json` file contains:

```json
{
  "saga_id": "a3f2b9c1",
  "saga_definition": "/path/to/sagas/example-saga.json",
  "original_input": "/path/to/input.txt",
  "created_at": "2026-05-05T21:17:00Z",
  "updated_at": "2026-05-05T21:18:30Z",
  "status": "in_progress",
  "current_node": "step-2",
  "state": [
    {
      "node": "start",
      "status": "success",
      "started_at": "2026-05-05T21:17:00Z",
      "completed_at": "2026-05-05T21:17:00Z",
      "session_id": null
    },
    {
      "node": "step-1",
      "status": "starting",
      "started_at": "2026-05-05T21:17:01Z",
      "completed_at": null,
      "session_id": null
    },
    {
      "node": "step-1",
      "status": "completed",
      "started_at": "2026-05-05T21:17:01Z",
      "completed_at": "2026-05-05T21:18:15Z",
      "exit_code": 0,
      "session_id": "devin-session-12345"
    },
    {
      "node": "step-2",
      "status": "starting",
      "started_at": "2026-05-05T21:18:16Z",
      "completed_at": null,
      "session_id": null
    }
  ],
  "subsagas": [
    {
      "node": "retry-workflow",
      "saga_id": "b7e4c2d9",
      "status": "in_progress",
      "started_at": "2026-05-05T21:18:30Z"
    }
  ]
}
```

### State Object Fields

**Top-level fields:**
- `saga_id` (string): Unique 8-character hash identifier
- `saga_definition` (string): Absolute path to the saga definition file
- `original_input` (string): Path to input file or direct string content
- `created_at` (ISO 8601): Saga creation timestamp
- `updated_at` (ISO 8601): Last state update timestamp
- `status` (enum): `starting`, `in_progress`, `completed`, `failed`
- `current_node` (string): Name of the currently executing node
- `state` (array): Ordered list of node execution records
- `subsagas` (array): List of child saga references

**State entry fields:**
- `node` (string): Node name from saga definition
- `status` (enum): `starting`, `completed`, `failed`, `continued`
- `started_at` (ISO 8601): When node execution began
- `completed_at` (ISO 8601, nullable): When node execution finished
- `exit_code` (int, optional): Exit code from step execution (0=pass, non-zero=fail)
- `session_id` (string, nullable): Devin session ID for resume capability

**Sub-saga entry fields:**
- `node` (string): Node name of the sub-saga in parent saga
- `saga_id` (string): Hash ID of the child saga instance
- `status` (enum): `starting`, `in_progress`, `completed`, `failed`
- `started_at` (ISO 8601): When sub-saga was invoked

### State Lifecycle

**1. Saga Initialization (First Action)**
```python
# On orchestrator invocation:
saga_id = generate_saga_id(saga.name, saga_path)
saga_dir = Path.cwd() / ".process" / f"saga-{saga_id}"
saga_dir.mkdir(parents=True, exist_ok=True)

state = {
    "saga_id": saga_id,
    "saga_definition": str(saga_path.absolute()),
    "original_input": input_content_or_path,
    "created_at": datetime.now().isoformat(),
    "updated_at": datetime.now().isoformat(),
    "status": "starting",
    "current_node": saga.start,
    "state": [
        {
            "node": "start",
            "status": "success",
            "started_at": datetime.now().isoformat(),
            "completed_at": datetime.now().isoformat(),
            "session_id": None
        }
    ],
    "subsagas": []
}

write_saga_state(saga_dir / "saga.json", state)
```

**2. Step Execution**
```python
# Before step execution:
append_state_entry({
    "node": node_name,
    "status": "starting",
    "started_at": datetime.now().isoformat(),
    "completed_at": None,
    "session_id": None
})

# After step execution:
update_last_state_entry({
    "status": "completed" if exit_code == 0 else "failed",
    "completed_at": datetime.now().isoformat(),
    "exit_code": exit_code,
    "session_id": devin_session_id  # Captured from Devin CLI output
})
```

**3. Self-Correction Loop**
```python
# On exit code 2 (self-correction needed):
append_state_entry({
    "node": node_name,
    "status": "continued",
    "started_at": datetime.now().isoformat(),
    "completed_at": None,
    "session_id": previous_session_id  # Reuse for continuation
})
```

**4. Sub-Saga Invocation**
```python
# Before sub-saga execution:
# Use the input being passed to the sub-saga for ID generation
child_input = inputs[0] if inputs else ""
child_saga_id = generate_saga_id(sub_saga.name, child_input)

append_subsaga_entry({
    "node": node_name,
    "saga_id": child_saga_id,
    "status": "in_progress",
    "started_at": datetime.now().isoformat()
})

# Child saga creates its own .process/saga-<child_saga_id>/ directory
# Parent saga tracks reference only
```

**5. Saga Completion**
```python
# On reaching 'end' node:
update_saga_status({
    "status": "completed",
    "updated_at": datetime.now().isoformat()
})

# On failure:
update_saga_status({
    "status": "failed",
    "updated_at": datetime.now().isoformat()
})
```

### Traversal Count Tracking

Each time a step is visited, a new entry is appended to the `state` array. This allows counting how many times a given step has been executed:

```python
def count_node_visits(state: list, node_name: str) -> int:
    """Count how many times a node has been visited."""
    return sum(1 for entry in state if entry["node"] == node_name)
```

**Example:** A retry loop with limit 3:
```json
"state": [
  {"node": "validate", "status": "failed", ...},
  {"node": "validate", "status": "failed", ...},
  {"node": "validate", "status": "completed", ...}
]
```
This shows 3 visits to `validate`, with the third succeeding.

### Session ID Capture

The Devin CLI session ID must be captured from Devin's output and stored in the state entry. This enables resume operations:

```python
# In devin_wrapper.py:
def execute(self, resume_session: bool = False) -> int:
    """Execute step via Devin CLI."""
    # ... existing code ...
    
    # Capture session ID from Devin output
    session_id = self._extract_session_id(stdout)
    
    # Write to session tracking file for executor to read
    if session_id:
        self.session_id_file.write_text(session_id)
    
    return exit_code

def _extract_session_id(self, output: str) -> Optional[str]:
    """Extract Devin session ID from CLI output."""
    # Parse Devin CLI output for session identifier
    # Format depends on Devin CLI version
    match = re.search(r'Session ID: ([a-zA-Z0-9-]+)', output)
    return match.group(1) if match else None
```

## Rationale

**Why file-based storage:**
- Simple, inspectable, debuggable
- No external dependencies (databases, message queues)
- Easy to version control saga state for testing
- Survives process crashes and system restarts
- Human-readable JSON format

**Why hash-based IDs:**
- Unique per invocation (includes timestamp at first invocation)
- Incorporates saga name and input path for traceability
- Short enough for directory names (8 characters)
- Different inputs to same saga produce different IDs
- Collision-resistant (SHA-256 truncated)
- Timestamp ensures re-runs of same input get unique IDs

**Why `.process/` directory:**
- Consistent with existing `.process/saga-logs/` convention
- Clearly indicates transient/runtime state
- Easy to gitignore entire directory
- Scoped to invocation directory (not global)

**Why append-only state array:**
- Complete execution history preserved
- Easy to count node visits for retry limits
- Supports debugging and auditing
- Enables future replay/analysis features

**Why separate sub-saga tracking:**
- Parent saga doesn't need child's full state
- Each saga manages its own state file
- Enables independent resume of parent or child
- Supports future distributed execution

**Why capture session IDs:**
- Enables resume of interrupted Devin sessions
- Supports continuation flows (exit code 2)
- Future support for interactive command injection
- Debugging aid (correlate saga state with Devin logs)

## Trade-offs

**Advantages:**
- Crash recovery - sagas can resume from last successful step
- Execution history - complete audit trail of all steps
- Debugging support - inspect state at any point
- Resume capability - continue from specific step (future)
- Sub-saga tracking - parent knows child saga IDs
- Session continuity - can resume Devin sessions
- Artifact storage - future support for intermediate files

**Disadvantages:**
- Disk I/O overhead - state written after every step
- No atomic transactions - crash during write may corrupt state
- No distributed locking - concurrent saga instances may conflict
- Manual cleanup required - `.process/` directory grows over time
- Session ID extraction fragile - depends on Devin CLI output format
- No state migration - schema changes require manual updates

## Implementation Plan

**Phase 1: Core State Persistence (High Priority)**
1. Implement saga ID generation with hash function
2. Create `.process/saga-<hash>/` directory on orchestrator invocation
3. Write initial `saga.json` with saga metadata
4. Update state before/after each step execution
5. Capture and store Devin session IDs
6. Track sub-saga invocations in parent state
7. Update saga status on completion/failure

**Phase 2: Resume Capability (Medium Priority)**
1. Add `--resume <saga-id>` flag to orchestrator CLI
2. Load existing `saga.json` and determine last successful step
3. Skip completed steps and resume from current node
4. Reuse session IDs for continuation flows
5. Validate state consistency before resume

**Phase 3: Cleanup and Maintenance (Low Priority)**
1. Add `--cleanup` command to remove old saga directories
2. Implement state file rotation (keep last N executions)
3. Add state validation and repair tools
4. Implement state migration utilities

## Future Enhancements

**Intermediate Artifact Storage:**
```
.process/saga-<hash>/
  <step-name>/
    input.json       # Step input parameters
    output.json      # Step output artifacts
    context.md       # Documentation/context for next steps
    session.log      # Full Devin session output
```

**State Snapshots:**
- Periodic snapshots for long-running sagas
- Write-ahead logging for atomic state updates
- State compression for large execution histories

**Distributed Execution:**
- Distributed locking for concurrent saga instances
- State synchronization across machines
- Centralized state storage (S3, database)

## Related Decisions

- [ADR-008: Devin CLI Saga Orchestration](ADR-008-devin-saga-orchestration.md) - This extends the orchestrator with state persistence
- [ADR-004: Skill Output Contracts & Sentinel Files](ADR-004-skill-output-contracts.md) - Artifact storage will follow similar patterns

## Migration Path

**Backward Compatibility:**
- State persistence is opt-in initially (feature flag)
- Existing sagas continue to work without state files
- Gradual migration as resume capability is needed

**Testing Strategy:**
- Unit tests for state file read/write operations
- Integration tests for crash recovery scenarios
- End-to-end tests for resume functionality
- Performance tests for state I/O overhead
