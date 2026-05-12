# ADR-011: Single Orchestrator Instance per Work Tree

**Date:** 2026-05-12  
**Status:** Accepted  
**Deciders:** Development Team

## Decision

The agentic software factory operates under the assumption that **only one orchestrator instance runs per work tree, and only one saga executes at a given moment**. This means:

1. **Single orchestrator instance** - Only one `run_saga.py` process executes at a time within a given repository
2. **Sequential saga execution** - Sagas run one at a time; no concurrent saga instances
3. **Exclusive step execution** - Only one step runs at a time; no parallel step execution within a saga
4. **No inter-saga conflicts** - Steps and verification scripts can assume they are the only agents modifying the work tree

## Context

The saga orchestrator (ADR-008) and state persistence system (ADR-009) were designed with the assumption of single-instance execution. This assumption simplifies several design decisions:

**Without this assumption, we would need:**
- Distributed locking for concurrent saga instances
- Atomic file operations to prevent state corruption
- Conflict resolution for simultaneous file modifications
- Complex coordination between parallel steps
- Transactional state management

**With this assumption, we can:**
- Use simple file-based state persistence without locking
- Assume any detected output files belong to the current saga
- Simplify verification script logic (no need to filter by saga ID)
- Use sequential traversal without race conditions
- Reduce complexity of the orchestrator implementation

## Rationale

**Expected Use Case:**
- One developer or CI/CD pipeline runs the orchestrator per work tree
- Each work tree is isolated (separate clone, container, or machine)
- Sagas are invoked sequentially, not in parallel
- The orchestrator is the only agent modifying the work tree during execution

**Why This Assumption is Valid:**
1. **Single-developer workflows** - Individual developers run sagas sequentially on their machines
2. **CI/CD pipelines** - Automated workflows run one saga per job/step
3. **Containerized execution** - Each container has its own work tree and orchestrator instance
4. **Deterministic execution** - Sequential execution is easier to debug and reason about

## Implications

### For Verification Scripts

Verification scripts can assume:
- They are the only agent running in the work tree
- Any output files they detect were created by their own step execution
- No need to filter by saga ID or step name when searching for outputs
- Safe to use glob patterns like `find . -name "*.intent.json"` without conflicts

**Example:**
```bash
# Safe because only this saga's extract step is running
intent_file=$(find . -name "*.intent.json" -type f | head -1)
if [[ -z "$intent_file" ]]; then
  echo "Error: No intent file found" >&2
  exit 1
fi
echo "$intent_file"
```

### For Step Execution

Steps can assume:
- No other steps are modifying the work tree simultaneously
- File modifications are atomic at the saga level
- State files (`.process/saga-<hash>/`) are not accessed by other sagas
- Temporary files created during step execution won't conflict with other steps

### For State Persistence

The state persistence system (ADR-009) can:
- Use simple file-based storage without distributed locking
- Assume `.process/saga-<hash>/` directories are exclusive to one saga instance
- Write state files without atomic transaction support
- Use append-only state arrays without conflict resolution

### For Future Enhancements

**Parallel Execution (Future):**
If parallel step execution becomes necessary:
1. Add distributed locking to state persistence
2. Implement atomic file operations with write-ahead logging
3. Add saga ID filtering to verification script output detection
4. Implement conflict resolution for simultaneous file modifications

**Distributed Execution (Future):**
If execution spans multiple machines:
1. Implement centralized state storage (S3, database)
2. Add distributed locking and coordination
3. Implement state synchronization across machines
4. Add network-based saga communication

## Trade-offs

**Advantages:**
- Simpler orchestrator implementation
- Easier to debug and reason about execution flow
- No need for distributed locking or atomic transactions
- Verification scripts can use simple file detection patterns
- Faster execution (no lock contention)
- Reduced complexity of state management

**Disadvantages:**
- Cannot run multiple sagas in parallel (performance limitation)
- Cannot run multiple steps concurrently (scalability limitation)
- Requires sequential orchestration for multi-saga workflows
- Not suitable for distributed execution without major refactoring
- Limits throughput in high-volume scenarios

## Constraints

**Hard Constraints:**
- Only one orchestrator instance per work tree
- Only one saga running at a time
- Only one step executing at a time

**Soft Constraints:**
- Verification scripts should complete quickly (no long-running background tasks)
- Steps should not spawn long-running processes that outlive the saga
- No external coordination between sagas (each saga is independent)

## Future Considerations

**When to Revisit This Decision:**
1. **Parallel step execution needed** - If steps can run independently, implement worker pools
2. **Multiple sagas in parallel** - If multiple workflows need to run concurrently, add distributed locking
3. **Distributed execution** - If execution spans multiple machines, implement centralized coordination
4. **High-volume processing** - If throughput becomes a bottleneck, parallelize at the saga level

**Migration Path:**
1. Keep single-instance assumption for current implementation
2. Add optional `--parallel` flag for future parallel execution
3. Implement distributed locking as opt-in feature
4. Maintain backward compatibility with sequential execution

## Related Decisions

- [ADR-008: Devin CLI Saga Orchestration](ADR-008-devin-saga-orchestration.md) - Orchestrator design assumes single instance
- [ADR-009: Saga State Persistence with File-Based Storage](ADR-009-saga-state-persistence.md) - State persistence uses simple file storage without locking
- [ADR-010: Verification Script Saga Context Access](ADR-010-verification-script-saga-context.md) - Verification scripts receive saga state as context

## Implementation Notes

**Verification Script Pattern:**
```bash
#!/bin/bash
# Verification scripts can safely assume they are the only agent running
# and can detect output files without filtering by saga ID

main() {
  local saga_state_path="${1:-}"
  local enrichment_path="${2:-}"
  
  # Safe to use simple file detection patterns
  local output_file=$(find . -name "*.output" -type f | head -1)
  
  if [[ ! -f "$output_file" ]]; then
    echo "Error: Expected output file not found" >&2
    exit 1
  fi
  
  # Validate output
  validate_output "$output_file"
  
  # Output enrichment data to stdout
  echo "$output_file"
}

main "$@"
```

**Orchestrator Pattern:**
```python
# Orchestrator can safely assume sequential execution
# No need for locking or conflict resolution

def execute_saga(saga_definition, input_path):
    """Execute saga sequentially, one step at a time."""
    saga_id = generate_saga_id(saga_definition.name, input_path)
    saga_dir = Path.cwd() / ".process" / f"saga-{saga_id}"
    saga_dir.mkdir(parents=True, exist_ok=True)
    
    # Execute steps sequentially
    for node in traverse_saga(saga_definition):
        execute_step(node, saga_id)
        # No locking needed - only one saga running
        update_state(saga_dir, node)
```

## Verification

- [x] Orchestrator assumes single instance per work tree
- [x] Verification scripts can detect output files without filtering
- [x] State persistence uses simple file-based storage
- [x] No distributed locking implemented (not needed)
- [x] Sequential execution is the default behavior
