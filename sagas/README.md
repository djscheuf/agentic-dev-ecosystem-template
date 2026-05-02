# Saga Definitions

This directory contains saga workflow definitions for orchestrating multi-step processes.

## What is a Saga?

A saga is a workflow that executes a series of steps with conditional routing based on step outcomes. Each step is executed via the Devin wrapper, and the saga orchestrator manages the flow between steps.

## Saga Structure

A saga definition is a JSON file with the following structure:

```json
{
  "name": "saga-name",
  "start": "first-step",
  "connections": [
    {
      "origin": "step-name",
      "then": {
        "target": "next-step",
        "traversal_limit": 5
      }
    },
    {
      "origin": "another-step",
      "pass": {
        "target": "success-step"
      },
      "fail": {
        "target": "retry-step",
        "traversal_limit": 3
      }
    }
  ]
}
```

### Fields

- **name**: Unique identifier for the saga
- **start**: Name of the first step to execute
- **connections**: Array of connection objects defining the workflow graph

### Connection Types

#### 1. Directed Connection (`then`)
Simple unconditional routing to the next step.

```json
{
  "origin": "step-a",
  "then": {
    "target": "step-b",
    "traversal_limit": 10
  }
}
```

#### 2. Branching Connection (`pass`/`fail`)
Conditional routing based on step exit code (0 = pass, non-zero = fail).

```json
{
  "origin": "step-b",
  "pass": {
    "target": "end"
  },
  "fail": {
    "target": "step-c",
    "traversal_limit": 3
  }
}
```

**Important**: If a connection has `pass`, it MUST also have `fail`.

### Traversal Limits

Each connection target can optionally specify a `traversal_limit`. This prevents infinite loops by limiting how many times a connection can be traversed during saga execution.

- If omitted, the connection can be traversed unlimited times
- If the limit is exceeded, the saga exits with failure
- Traversal counts persist for the entire saga execution

### Special Nodes

- **start**: Must be specified in the saga definition
- **end**: Terminal node indicating successful completion

## Validation Rules

The saga orchestrator validates the following before execution:

1. ✓ Start step exists in `steps/` directory
2. ✓ All referenced steps exist in `steps/` directory
3. ✓ Graph is closed (all paths lead to `end`)
4. ✓ No dead-end nodes (except `end`)
5. ✓ Branching connections have both `pass` and `fail`

## Running a Saga

```bash
python orchestrator/run_saga.py sagas/example-saga.json [input-files...]
```

### Execution Flow

1. Saga definition is loaded and validated
2. Initial inputs are passed to the first step
3. Each step executes via `devin_wrapper.py`
4. Step outputs are passed to the next step
5. Routing decisions are made based on exit codes
6. Execution continues until reaching `end` or hitting a limit
7. Full execution trace is logged to `.process/saga-logs/`

### Step Outputs

Steps can define outputs by creating an `outputs.json` file:

```json
{
  "outputs": [
    "path/to/output1.txt",
    "path/to/output2.json"
  ]
}
```

These outputs become inputs to the next step in the saga.

## Examples

### Simple Linear Saga
```json
{
  "name": "simple",
  "start": "step-a",
  "connections": [
    {"origin": "step-a", "then": {"target": "step-b"}},
    {"origin": "step-b", "then": {"target": "end"}}
  ]
}
```

### Retry with Limit
```json
{
  "name": "retry",
  "start": "validate",
  "connections": [
    {
      "origin": "validate",
      "pass": {"target": "end"},
      "fail": {"target": "validate", "traversal_limit": 3}
    }
  ]
}
```

### Complex Workflow
```json
{
  "name": "complex",
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

## Logs

Execution logs are written to `.process/saga-logs/<saga-name>_<timestamp>.log`

Log entries include:
- Step execution start/completion
- Exit codes and pass/fail status
- Routing decisions
- Traversal counts
- Errors and limit violations
- Final saga outcome
