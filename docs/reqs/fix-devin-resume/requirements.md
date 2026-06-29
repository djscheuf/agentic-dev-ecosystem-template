# Requirements: Fix Devin Resume/Retry Logic

**Date:** 2026-05-08  
**Status:** Draft  
**Related:** [ADR-008: Devin CLI Saga Orchestration](../../vault/decisions/ADR-008-devin-saga-orchestration.md)

## Problem Statement

The current saga orchestrator's resume/retry logic is broken because the Devon CLI does not provide discoverable session IDs. When a step's verification script fails, the system should resume the previous Devin session and post verification errors back to that same agent for repair. However, session IDs cannot be reliably identified or discovered through CLI means, making session resumption impossible.

## Current Behavior

1. Step executes via Devin CLI
2. Verification script runs and may fail
3. System attempts to resume the Devin session with verification errors
4. **BROKEN**: Session ID is not available or discoverable
5. Retry fails because session cannot be resumed

## Required New Behavior

Since session resumption is not viable, implement a **conversation accumulation pattern** where each retry builds a progressively larger prompt containing the full conversation history:

1. **Initial Execution**
   - Send original prompt to new Devin agent
   - Capture: input prompt, agent output, verification result

2. **First Retry (on verification failure)**
   - Compose new prompt containing:
     - Original input prompt
     - Previous agent output
     - Verification errors/feedback
   - Send to new Devin agent (same configuration)
   - Capture: composed prompt, agent output, verification result

3. **Subsequent Retries**
   - Compose progressively larger prompt containing:
     - Original input prompt
     - Agent output #1
     - Verification errors #1
     - Agent output #2
     - Verification errors #2
     - ... (continue pattern)
   - Send to new Devin agent (same configuration)
   - Continue until retry limit reached

## File Structure Changes

### Current State Files (per step execution)
Currently written to `.sagas/<saga-id>/` or `.process/<step>/`:
- `stdout.txt` - Agent's complete response
- `stderr.txt` - Verification script output
- `session_id.txt` - Session ID (not usable)

### Required New State Files (per step execution)

Rename and restructure files for clarity:

```
.sagas/<saga-id>/
  <node-name>/
    input.txt           # Complete prompt sent to agent
    output.txt          # Agent's complete response (renamed from stdout.txt)
    verification.txt    # Verification script output (renamed from stderr.txt)
```

**File Naming Rationale:**
- `input.txt` - Clear that this is what we sent IN to the agent
- `output.txt` - Clear that this is what came OUT from the agent
- `verification.txt` - Clear that this is verification feedback (not stderr)

### Directory Structure

Each node execution should have its own subdirectory within the saga state directory to isolate retry attempts and maintain history:

```
.sagas/<saga-id>/
  <node-name>/
    attempt_1/
      input.txt
      output.txt
      verification.txt
    attempt_2/
      input.txt          # Accumulated: original + output_1 + verification_1
      output.txt
      verification.txt
    attempt_3/
      input.txt          # Accumulated: original + output_1 + verification_1 + output_2 + verification_2
      output.txt
      verification.txt
```

## Implementation Requirements

### 1. State Capture (Orchestrator)

**Location:** `orchestrator/orchestrator.py`

Modify `_write_session_state()` to:
- Create node-specific subdirectory: `<saga-state-dir>/<node-name>/attempt_<N>/`
- Write three files:
  - `input.txt` - The complete prompt sent to the agent
  - `output.txt` - The agent's complete response
  - `verification.txt` - Verification script output (if verification runs)

**New Method:** `_determine_attempt_number()`
- Check existing attempt directories
- Return next attempt number

### 2. Prompt Composition (DevinWrapper or Orchestrator)

**Location:** `orchestrator/devin_wrapper.py` or `orchestrator/orchestrator.py`

**New Method:** `compose_retry_prompt()`
- Load all previous attempts from node directory
- Build accumulated conversation:
  ```
  Original Request:
  <input from attempt_1>
  
  Previous Attempt #1:
  <output from attempt_1>
  
  Verification Feedback #1:
  <verification from attempt_1>
  
  Previous Attempt #2:
  <output from attempt_2>
  
  Verification Feedback #2:
  <verification from attempt_2>
  
  Please review the verification feedback and fix the issues.
  ```

### 3. Retry Logic (SagaExecutor)

**Location:** `orchestrator/saga_executor.py`

Modify `_execute_step()` to:
- Detect if this is a retry (check for existing attempts)
- If retry:
  - Call `compose_retry_prompt()` to build accumulated prompt
  - Pass accumulated prompt to orchestrator
  - Increment attempt counter
- If initial attempt:
  - Use original prompt
  - Set attempt counter to 1

### 4. Session Management Changes

**Remove/Deprecate:**
- Session ID tracking (not usable)
- Session resumption logic
- `session_id.txt` file

**Keep:**
- Retry limit enforcement (via traversal limits)
- Exit code routing (pass/fail paths)

## Acceptance Criteria

1. ✅ Each step execution creates a node-specific directory
2. ✅ Three files captured per attempt: `input.txt`, `output.txt`, `verification.txt`
3. ✅ Retry attempts compose accumulated conversation history
4. ✅ Each retry creates a new Devin agent (no session resumption)
5. ✅ Retry limit enforced via existing traversal limit mechanism
6. ✅ File naming is clear and self-documenting
7. ✅ Existing saga execution flow preserved (no breaking changes)
8. ✅ Logs clearly show retry attempts and accumulated prompt sizes

## Non-Goals

- Session resumption (not viable with current Devin CLI)
- Intelligent prompt compression (just accumulate everything)
- Parallel retry attempts
- Cross-node conversation history

## Trade-offs

### Advantages
- Works around Devin CLI session ID limitation
- Full conversation context available to agent on retry
- Simple, deterministic behavior
- Easy to debug (all context in files)

### Disadvantages
- Prompt size grows linearly with retry attempts
- May hit token limits on deep retry chains
- Duplicate information sent to agent
- More storage required (full history per attempt)

## Migration Notes

### Backward Compatibility
- Existing sagas will continue to work
- Old file names (`stdout.txt`, `stderr.txt`) will be deprecated but not break
- Gradual migration: new executions use new structure

### Breaking Changes
- None (additive changes only)

## Open Questions

1. **Q:** Should we implement prompt compression/summarization?  
   **A:** No, not in initial implementation. Keep it simple.

2. **Q:** What happens if accumulated prompt exceeds token limits?  
   **A:** Let it fail naturally. Agent will return error, verification will fail, saga will exit.

3. **Q:** Should we preserve old attempt directories or clean them up on success?  
   **A:** Preserve all attempts for debugging. Clean up on saga completion (future enhancement).

4. **Q:** Where should `compose_retry_prompt()` live - DevinWrapper or Orchestrator?  
   **A:** Orchestrator - it's orchestration logic, not agent-specific.

## Implementation Phases

### Phase 1: State Capture (Required)
- Modify `Orchestrator._write_session_state()` to create node directories
- Write `input.txt`, `output.txt`, `verification.txt`
- Add attempt number tracking

### Phase 2: Prompt Composition (Required)
- Implement `Orchestrator.compose_retry_prompt()`
- Load previous attempts from node directory
- Build accumulated conversation

### Phase 3: Integration (Required)
- Modify `SagaExecutor._execute_step()` to detect retries
- Call `compose_retry_prompt()` on retry
- Pass accumulated prompt to orchestrator

### Phase 4: Cleanup (Optional)
- Remove session ID tracking code
- Update documentation
- Add logging for retry attempts

## Success Metrics

- Verification failures successfully trigger retries with full context
- Agents can see and respond to previous verification feedback
- Retry limit prevents infinite loops
- File structure is clear and debuggable
