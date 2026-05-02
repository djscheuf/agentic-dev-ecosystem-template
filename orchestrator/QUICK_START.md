# Saga Orchestrator - Quick Start Guide

## Installation

No installation required! The saga orchestrator uses only Python standard library.

## Basic Usage

```bash
python orchestrator/run_saga.py <saga-definition.json> [inputs...]
```

## Creating Your First Saga

### 1. Create a Saga Definition

Create `sagas/my-workflow.json`:

```json
{
  "name": "my-workflow",
  "start": "example",
  "connections": [
    {
      "origin": "example",
      "then": {
        "target": "end"
      }
    }
  ]
}
```

### 2. Run the Saga

```bash
python orchestrator/run_saga.py sagas/my-workflow.json
```

### 3. Check the Logs

Logs are written to `.process/saga-logs/my-workflow_<timestamp>.log`

## Common Patterns

### Simple Linear Workflow

```json
{
  "name": "linear",
  "start": "step1",
  "connections": [
    {"origin": "step1", "then": {"target": "step2"}},
    {"origin": "step2", "then": {"target": "step3"}},
    {"origin": "step3", "then": {"target": "end"}}
  ]
}
```

### Retry on Failure

```json
{
  "name": "retry",
  "start": "task",
  "connections": [
    {
      "origin": "task",
      "pass": {"target": "end"},
      "fail": {"target": "task", "traversal_limit": 3}
    }
  ]
}
```

## Connection Types

### Directed Connection (`then`)

Always routes to the same next step.

### Branching Connection (`pass`/`fail`)

Routes based on step exit code (0=pass, non-zero=fail).

## Exit Codes

- `0` - Saga completed successfully
- `1` - Saga failed

## Examples

See `sagas/` directory for working examples.
