# Orchestrator

This directory contains tools for orchestrating Devin agent execution, including individual step execution and saga workflow orchestration.

## Components

1. **Devin CLI Wrapper** (`devin_wrapper.py`) - Execute individual steps
2. **Saga Orchestrator** (`run_saga.py`) - Execute multi-step workflows

---

# Devin CLI Wrapper

A Python wrapper for orchestrating Devin agent execution with verification scripts.

## Usage

```bash
python devin_wrapper.py <step_definition.json> [input_files...]
```

### Arguments

- `step_definition.json`: JSON file defining the execution step
- `input_files...`: Optional input files to pass to the agent

## Step Definition Format

The step definition is a JSON file with the following properties:

```json
{
  "prompt": "Your prompt text or path/to/prompt.md",
  "model": "model-name",
  "budget": 100,
  "timeout": 300,
  "verify": "path/to/verify.sh"
}
```

### Properties

- **prompt** (required): Either a direct string prompt or a path to a markdown file containing the prompt. Relative paths are resolved from the step definition file's directory.
- **model** (required): The Devin model to use (e.g., "claude-sonnet-4", "claude-opus-4.6", "opus", "haiku")
- **budget** (optional): Budget limit in ACUs (Agent Compute Units) - **Note**: This is informational only; the Devin CLI does not enforce budget limits at invocation time. ACU limits are managed at the account/organization level.
- **timeout** (optional): Maximum execution time in seconds. The Devin process will be forcibly terminated if it exceeds this limit. If not specified, no timeout is enforced.
- **verify** (optional): Path to a shell script for verification after execution. Relative paths are resolved from the step definition file's directory.

## Example

### Step Definition (`example-step.json`)

```json
{
  "prompt": "prompts/analyze-code.md",
  "model": "haiku",
  "budget": 50,
  "timeout": 300,
  "verify": "scripts/verify-analysis.sh"
}
```

### Verification Script (`scripts/verify-analysis.sh`)

```bash
#!/bin/bash
# Simple verification script
# Exit 0 for success, non-zero for failure

if [ -f "output/analysis.md" ]; then
  echo "Analysis file found"
  exit 0
else
  echo "Analysis file missing"
  exit 1
fi
```

### Execution

```bash
python devin_wrapper.py example-step.json src/main.py src/utils.py
```

## Workflow

1. Load step definition from JSON file
2. Build Devin CLI command with model and prompt in non-interactive mode (`-p`)
3. Append input files to the prompt context
4. Execute Devin CLI: `devin --model <model> -p -- "<prompt>"`
5. If Devin succeeds, run verification script
6. Return verification script exit code

## Implementation Details

The wrapper uses Devin's non-interactive print mode (`-p` flag) which:
- Processes the prompt and exits (no interactive session)
- Returns exit code 0 on success, non-zero on failure
- Uses the `--` separator before the prompt text

### Timeout Behavior

When a `timeout` is specified:
- The wrapper monitors the Devin process execution time
- If execution exceeds the timeout limit, the process is forcibly terminated (SIGTERM)
- Returns exit code `124` to indicate timeout
- Verification script is **not** executed after a timeout

## Exit Codes

- `0`: Success (both Devin and verification passed)
- `1`: General error
- `124`: Timeout - Devin process exceeded timeout limit and was terminated
- `127`: Devin CLI not found
- Other: Devin or verification script exit code

---

# Saga Orchestrator

A workflow orchestration system for executing multi-step processes with conditional routing and cycle management.

## Usage

```bash
python orchestrator/run_saga.py <saga_definition.json> [input_files...]
```

### Arguments

- `saga_definition.json`: JSON file defining the saga workflow
- `input_files...`: Optional initial inputs passed to the first step

## Architecture

The saga orchestrator consists of four main components:

### 1. Saga Models (`saga_models.py`)
Defines the data structures for saga workflows:
- **ConnectionTarget**: Target step with optional traversal limit
- **DirectedConnection**: Simple `then` connection
- **BranchingConnection**: Conditional `pass`/`fail` routing
- **SagaDefinition**: Complete saga specification

### 2. Saga Validator (`saga_validator.py`)
Validates saga definitions before execution:
- ✓ Start step exists in `steps/` directory
- ✓ All referenced steps exist
- ✓ Graph is closed (all paths lead to `end`)
- ✓ No dead-end nodes
- ✓ Branching connections have both `pass` and `fail`

### 3. Saga Executor (`saga_executor.py`)
Executes the saga workflow:
- Loads saga definition
- Executes steps via `devin_wrapper.py`
- Routes based on exit codes (0=pass, non-zero=fail)
- Tracks traversal counts per connection
- Enforces traversal limits
- Logs execution trace to file

### 4. CLI Entry Point (`run_saga.py`)
Main command-line interface for running sagas.

## Saga Definition Format

See `sagas/README.md` for detailed documentation on saga definitions.

### Quick Example

```json
{
  "name": "example-workflow",
  "start": "analyze",
  "connections": [
    {
      "origin": "analyze",
      "pass": {"target": "implement"},
      "fail": {"target": "refine", "traversal_limit": 2}
    },
    {
      "origin": "refine",
      "then": {"target": "analyze"}
    },
    {
      "origin": "implement",
      "pass": {"target": "end"},
      "fail": {"target": "debug", "traversal_limit": 5}
    },
    {
      "origin": "debug",
      "then": {"target": "implement"}
    }
  ]
}
```

## Key Features

### Connection Types

1. **Directed (`then`)**: Unconditional routing
2. **Branching (`pass`/`fail`)**: Conditional routing based on step exit code

### Traversal Limits

Prevent infinite loops by limiting how many times a connection can be traversed:
- Optional per-connection setting
- Counts persist for entire saga execution
- If limit exceeded, saga exits with failure

### Execution Flow

1. Validate saga definition
2. Execute first step with initial inputs
3. Route to next step based on exit code
4. Pass step outputs as inputs to next step
5. Continue until reaching `end` or hitting a limit
6. Log full execution trace

### Logging

All executions are logged to `.process/saga-logs/<saga-name>_<timestamp>.log`

Log entries include:
- Step execution start/completion
- Exit codes and pass/fail status
- Routing decisions with traversal counts
- Errors and limit violations
- Final saga outcome

## Example Sagas

See `sagas/` directory for example saga definitions:
- `example-saga.json`: Simple linear workflow
- `retry-saga.json`: Retry with traversal limit

## Exit Codes

- `0`: Saga completed successfully (reached `end`)
- `1`: Saga failed (validation error, step error, or traversal limit exceeded)
