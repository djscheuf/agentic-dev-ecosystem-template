# Saga Storage Structure Reference

**Last Updated**: May 8, 2026

This document provides a concrete reference for the actual shape of saga storage directories, with real examples from running sagas.

## Directory Layout

```
.process/
  saga-<8-char-hash>/
    saga.json                    # Saga execution state and history
    enrichment.json              # Enrichment context for variable substitution
    <step-name>_stderr.txt       # Verification script stderr (if step failed)
    <step-name>/
      attempt_1/
        input.txt                # Enriched step prompt
        output.txt               # Agent output
        verification.txt         # Verification script stdout
      attempt_2/
        input.txt
        output.txt
        verification.txt
      attempt_N/
        ...
```

## Real Example

From saga execution `saga-c13128b7`:

```
.process/saga-c13128b7/
├── saga.json
├── enrichment.json
├── extract_stderr.txt
├── analyze_stderr.txt
├── extract/
│   └── attempt_1/
│       ├── input.txt
│       ├── output.txt
│       └── verification.txt
└── analyze/
    ├── attempt_1/
    │   ├── input.txt
    │   ├── output.txt
    │   └── verification.txt
    └── attempt_2/
        ├── input.txt
        ├── output.txt
        └── verification.txt
```

## File Contents

### saga.json

Tracks saga execution state and history:

```json
{
  "saga_id": "c13128b7",
  "saga_definition": "/path/to/sagas/sdlc-analysis.json",
  "original_input": "./docs/ex/story.md",
  "created_at": "2026-05-08T15:34:09.906306",
  "updated_at": "2026-05-08T15:36:27.003563",
  "status": "failed",
  "current_node": "analyze",
  "state": [
    {
      "node": "start",
      "status": "success",
      "started_at": "2026-05-08T15:34:09.906306",
      "completed_at": "2026-05-08T15:34:09.906306",
      "exit_code": null,
      "session_id": null
    },
    {
      "node": "extract",
      "status": "completed",
      "started_at": "2026-05-08T15:34:09.906563",
      "completed_at": "2026-05-08T15:34:41.948881",
      "exit_code": 0,
      "session_id": null
    },
    {
      "node": "analyze",
      "status": "failed",
      "started_at": "2026-05-08T15:34:41.949159",
      "completed_at": "2026-05-08T15:36:27.003550",
      "exit_code": 1,
      "session_id": null
    }
  ],
  "subsagas": []
}
```

**Key fields:**
- `saga_id`: Unique 8-character hash identifier
- `status`: Overall saga status (starting, in_progress, completed, failed)
- `state`: Array of node execution records (append-only, preserves full history)
- Each state entry tracks: node name, status, timestamps, exit code, session ID

### enrichment.json

Contains context variables for step prompts and verification scripts:

```json
{
  "saga_id": "c13128b7",
  "state_storage_location": "/mnt/data/0_repo/agentic-dev-ecosystem-template/.process/saga-c13128b7",
  "initial_prompt_path": "./docs/ex/story.md",
  "custom_variables": {},
  "previous_step_output": "/mnt/data/0_repo/agentic-dev-ecosystem-template/docs/reqs/refactor devin wrapper/refactor-wrapper-orchestrator-responsibilities.intent.json",
  "previous_step_error": ""
}
```

**Key fields:**
- `initial_prompt_path`: Available as `{{initial_prompt_path}}` in step prompts
- `previous_step_output`: Available as `{{previous_step_output}}` in step prompts (populated from previous step's verification script stdout)
- `custom_variables`: User-defined variables from saga definition
- Updated after each successful step with new `previous_step_output`

### Step Attempt Artifacts

#### input.txt

The enriched step prompt with all `{{variable}}` substitutions applied:

```markdown
# Extract Story Intent

Extract a user story from the provided document or text into a structured JSON format.

**Input Document**: ./docs/ex/story.md

## Steps

### 1. Read the Provided Document/Text
- Read the document at ./docs/ex/story.md. You will be extracting information from this document to create the user story JSON.

[... rest of prompt ...]
```

On retries, this contains an accumulated prompt with:
1. Original prompt
2. Previous attempt's output
3. Verification feedback
4. (Repeat for each attempt)

#### output.txt

Raw stdout from the agent (Devin CLI output):

```
[Agent output and generated code/files...]
```

#### verification.txt

Stdout from the verification script. On success, this becomes the next step's `previous_step_output`:

```
/mnt/data/0_repo/agentic-dev-ecosystem-template/docs/reqs/refactor devin wrapper/refactor-wrapper-orchestrator-responsibilities.intent.json
```

### Step Stderr Files

`<step-name>_stderr.txt` at saga root contains verification script stderr (diagnostic output):

```
[Verify] Searching for generated intent file...
[Verify] Using saga state path: /mnt/data/0_repo/agentic-dev-ecosystem-template/.process/saga-c13128b7
[Verify] Found intent file: /path/to/file.intent.json
[Verify] ✓ Verification passed
```

## Retry Logic

When a step fails with exit code 2 (self-correction needed):

1. A new `attempt_N+1/` directory is created
2. The new `input.txt` contains accumulated context from all previous attempts
3. The agent can see what it tried before and why it failed
4. Process repeats up to max_attempts limit

Example progression:
```
extract/attempt_1/  → exit code 0 (success)
analyze/attempt_1/  → exit code 2 (needs correction)
analyze/attempt_2/  → exit code 2 (still needs correction)
analyze/attempt_3/  → exit code 0 (success) or exit code 1 (failure)
```

## Enrichment Flow

The enrichment context flows through the saga execution:

```
Saga Start
  ↓
enrichment.json created with:
  - saga_id
  - state_storage_location
  - initial_prompt_path (from saga input)
  - custom_variables (from saga definition)
  ↓
Step 1 (extract) executes
  - Receives enrichment with {{initial_prompt_path}}
  - Verify script outputs file path to stdout
  ↓
enrichment.json updated with:
  - previous_step_output = verify script stdout
  ↓
Step 2 (analyze) executes
  - Receives enrichment with {{previous_step_output}}
  - Can read intent file from previous step
  ↓
(Repeat for each step)
```

## Verification Script Interface

Verification scripts receive saga context as arguments:

```bash
verify.sh <saga_state_dir> [enrichment_json_path]
```

Example:
```bash
verify.sh /mnt/data/0_repo/agentic-dev-ecosystem-template/.process/saga-c13128b7 \
          /mnt/data/0_repo/agentic-dev-ecosystem-template/.process/saga-c13128b7/enrichment.json
```

Scripts can:
- Read enrichment.json to access previous step outputs
- Access attempt directories to find step artifacts
- Output to stdout (becomes next step's previous_step_output)
- Output to stderr (written to step_stderr.txt for debugging)

## Related Documentation

- [ADR-009: Saga State Persistence](../decisions/ADR-009-saga-state-persistence.md) - Design decision and architecture
- [ADR-010: Verification Script Saga Context Access](../decisions/ADR-010-verification-script-saga-context.md) - How verification scripts access saga state
- [Saga State Enrichment](saga-enrichment.md) - Variable substitution mechanism
