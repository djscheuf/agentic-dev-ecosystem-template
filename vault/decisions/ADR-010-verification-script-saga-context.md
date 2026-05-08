# ADR-010: Verification Script Saga Context Access

**Date**: May 8, 2026  
**Status**: Accepted  
**Deciders**: Development Team

## Context

Verification scripts are responsible for validating step outputs and producing enrichment data (via stdout) for downstream steps in a saga. Previously, verification scripts had no access to saga state, making it difficult for them to:

1. Discover output files created by the step
2. Access enrichment data from previous steps
3. Coordinate with other steps in the saga execution context

This forced verification scripts to search the entire project directory, which is inefficient and error-prone.

## Decision

**Verification scripts will receive saga state context as command-line arguments:**

1. **First argument**: Path to saga state directory (e.g., `.process/saga-{saga_id}`)
2. **Second argument** (optional): Path to enrichment.json file (if it exists)

The orchestrator will pass these arguments when invoking the verify script:

```bash
bash verify.sh /path/to/saga-state /path/to/saga-state/enrichment.json
```

Scripts can then:
- Read enrichment.json to access `initial_prompt_path`, `previous_step_output`, etc.
- Access attempt directories to find step outputs
- Coordinate with other steps via shared saga state

## Rationale

1. **Efficiency**: Scripts can directly access saga state instead of searching the project
2. **Coordination**: Enables verification scripts to read enrichment data from previous steps
3. **Consistency**: Aligns with the enrichment pattern already used for step prompts
4. **Backward Compatibility**: Arguments are optional; scripts that don't use them continue to work

## Implementation

### Orchestrator Changes (`orchestrator.py`)

The `_run_verification` method now:
1. Accepts optional `saga_id` parameter
2. Constructs saga state path: `.process/saga-{saga_id}`
3. Passes saga state path as first argument to verify script
4. Passes enrichment.json path as second argument if it exists

```python
cmd = ["bash", str(script_path)]
if saga_id:
    saga_state_path = Path.cwd() / ".process" / f"saga-{saga_id}"
    cmd.append(str(saga_state_path))
    enrichment_path = saga_state_path / "enrichment.json"
    if enrichment_path.exists():
        cmd.append(str(enrichment_path))
```

### Verification Script Interface

Scripts should accept these optional arguments:

```bash
main() {
  local saga_state_path="${1:-}"
  local enrichment_dict_path="${2:-}"
  
  # Use saga context if available
  if [[ -n "$saga_state_path" ]]; then
    # Access enrichment data
    local previous_output=$(jq -r '.previous_step_output' "$enrichment_dict_path")
  fi
}
```

## Consequences

### Positive

- Verification scripts have full access to saga execution context
- Enables more sophisticated validation and coordination patterns
- Reduces need for global project directory searches
- Supports enrichment data flow through verification outputs

### Negative

- Verification scripts must handle optional arguments gracefully
- Scripts that expect specific saga state structure may break if structure changes
- Adds complexity to script interfaces

## Related Decisions

- [ADR-009: Saga State Persistence](ADR-009-saga-state-persistence.md) - Defines enrichment.json structure
- [ADR-008: Devin CLI Saga Orchestration](ADR-008-devin-saga-orchestration.md) - Defines saga execution model

## Examples

### Extract Step Verification

The `extract-story-intent` verify script receives saga state and can:
- Echo the created intent file path to stdout (becomes `previous_step_output`)
- Redirect diagnostic messages to stderr

```bash
main() {
  local saga_state_path="${1:-}"
  
  # Find and validate intent file
  local story_path=$(find_intent_file)
  
  # Validation checks...
  
  # Output only the file path to stdout for enrichment
  echo "$story_path"
}
```

### Analyze Step Verification

The `analyze-story` verify script receives saga state and enrichment, allowing it to:
- Read `initial_prompt_path` from enrichment to locate the original story
- Read `previous_step_output` to find the intent file from extract step
- Validate analysis against the original story context

```bash
main() {
  local saga_state_dir="$1"
  local enrichment_dict_path="$2"
  
  # Read enrichment data
  local initial_prompt=$(jq -r '.initial_prompt_path' "$enrichment_dict_path")
  local intent_file=$(jq -r '.previous_step_output' "$enrichment_dict_path")
  
  # Validate analysis using both files
  verify_analysis_against_intent "$analysis_file" "$intent_file"
}
```

## Verification

- [x] Orchestrator passes saga state to verify scripts
- [x] Enrichment.json is passed when available
- [x] Extract step verify script outputs file path to stdout
- [x] Analyze step verify script reads enrichment data
- [x] Backward compatibility maintained for scripts without saga context
