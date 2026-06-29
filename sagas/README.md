# Saga Definitions

This directory contains saga workflow definitions for orchestrating multi-step processes.

## What is a Saga?

A saga is a workflow that executes a series of steps with conditional routing based on step outcomes. Each step is executed via the Devin wrapper, and the saga orchestrator manages the flow between steps.

## Saga Structure

A saga definition is a JSON file with the following structure:

```json
{
  "name": "saga-name",
  "max_recursion_depth": 50,
  "start": "first-node",
  "nodes": {
    "node-name": {
      "type": "step",
      "reference": "step-folder-name",
      "timeout": 300
    },
    "sub-workflow": {
      "type": "saga",
      "reference": "sub-saga.json",
      "timeout": 600
    }
  },
  "connections": [
    {
      "node": "node-name",
      "then": {
        "target": "next-node",
        "traversal_limit": 5
      }
    },
    {
      "node": "another-node",
      "pass": {
        "target": "success-node"
      },
      "fail": {
        "target": "retry-node",
        "traversal_limit": 3
      }
    }
  ]
}
```

### Fields

- **name**: Unique identifier for the saga
- **max_recursion_depth** (optional, default: 50): Maximum nesting depth for sub-sagas
- **start**: Name of the first node to execute
- **nodes**: Dictionary of node definitions (steps or sub-sagas)
- **connections**: Array of connection objects defining the workflow graph

### Node Definition

Each node must be defined in the `nodes` section:

- **type** (required): Either `"step"` or `"saga"`
- **reference** (required): 
  - For steps: name of folder in `steps/` directory
  - For sagas: path to saga JSON file (relative to `sagas/` or absolute)
- **timeout** (optional): Maximum execution time in seconds

### Connection Types

#### 1. Directed Connection (`then`)
Simple unconditional routing to the next node.

```json
{
  "node": "node-a",
  "then": {
    "target": "node-b",
    "traversal_limit": 10
  }
}
```

#### 2. Branching Connection (`pass`/`fail`)
Conditional routing based on node exit code (0 = pass, non-zero = fail).

```json
{
  "node": "node-b",
  "pass": {
    "target": "end"
  },
  "fail": {
    "target": "node-c",
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

1. ✓ Start node is defined in `nodes` section
2. ✓ All node references exist (steps in `steps/`, sagas in `sagas/`)
3. ✓ All connections reference defined nodes or `end`
4. ✓ Graph is closed (all paths lead to `end`)
5. ✓ No dead-end nodes (except `end`)
6. ✓ Branching connections have both `pass` and `fail`
7. ✓ Recursion depth doesn't exceed `max_recursion_depth`
8. ⚠ Circular references generate warnings (not errors)

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

## Composable Sagas

Sagas can now contain both **steps** and **sub-sagas** as nodes, enabling modular workflow composition.

### Example: Composite Workflow

```json
{
  "name": "deployment-pipeline",
  "max_recursion_depth": 10,
  "start": "validate",
  "nodes": {
    "validate": {
      "type": "step",
      "reference": "validate-config",
      "timeout": 60
    },
    "build-and-test": {
      "type": "saga",
      "reference": "build-test-saga.json",
      "timeout": 1800
    },
    "deploy": {
      "type": "step",
      "reference": "deploy-to-prod"
    }
  },
  "connections": [
    {
      "node": "validate",
      "pass": {"target": "build-and-test"},
      "fail": {"target": "end"}
    },
    {
      "node": "build-and-test",
      "then": {"target": "deploy"}
    },
    {
      "node": "deploy",
      "then": {"target": "end"}
    }
  ]
}
```

See `orchestrator/COMPOSABLE_SAGAS.md` for detailed documentation on composable sagas.

## Examples

### Simple Linear Saga
```json
{
  "name": "simple",
  "start": "step-a",
  "nodes": {
    "step-a": {"type": "step", "reference": "step-a"},
    "step-b": {"type": "step", "reference": "step-b"}
  },
  "connections": [
    {"node": "step-a", "then": {"target": "step-b"}},
    {"node": "step-b", "then": {"target": "end"}}
  ]
}
```

### Retry with Limit
```json
{
  "name": "retry",
  "start": "task",
  "nodes": {
    "task": {"type": "step", "reference": "task", "timeout": 300}
  },
  "connections": [
    {
      "node": "task",
      "pass": {"target": "end"},
      "fail": {"target": "task", "traversal_limit": 3}
    }
  ]
}
```

### Complex Workflow
```json
{
  "name": "complex",
  "start": "analyze",
  "nodes": {
    "analyze": {"type": "step", "reference": "analyze"},
    "refine": {"type": "step", "reference": "refine"},
    "implement": {"type": "step", "reference": "implement"},
    "debug": {"type": "step", "reference": "debug"}
  },
  "connections": [
    {
      "node": "analyze",
      "pass": {"target": "implement"},
      "fail": {"target": "refine", "traversal_limit": 2}
    },
    {"node": "refine", "then": {"target": "analyze"}},
    {
      "node": "implement",
      "pass": {"target": "end"},
      "fail": {"target": "debug", "traversal_limit": 5}
    },
    {"node": "debug", "then": {"target": "implement"}}
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
