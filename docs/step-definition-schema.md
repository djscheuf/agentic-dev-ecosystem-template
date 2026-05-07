# Step Definition Schema

This document describes the structure of `step.json` files used to define steps in the agentic software factory.

## Overview

A step definition is a JSON file that specifies how a Devin agent should execute a particular task. Each step has a required prompt and model, with optional configuration for timeouts, budgets, verification, and agent permissions.

## Schema

```json
{
  "prompt": "string (required)",
  "model": "string (required)",
  "budget": "number (optional)",
  "timeout": "number (optional)",
  "verify": "string (optional)",
  "agent_config": "string (optional)"
}
```

## Field Descriptions

### `prompt` (required)
**Type:** string  
**Description:** The prompt to send to the Devin agent. Can be either:
- A direct string containing the prompt text
- A path to a file (relative to the step directory) containing the prompt

**Example:**
```json
{
  "prompt": "Analyze the provided code and suggest improvements"
}
```

Or with external file:
```json
{
  "prompt": "prompt.md"
}
```

### `model` (required)
**Type:** string  
**Description:** The Claude model to use for this step. Specifies which model variant the Devin agent should use.

**Valid values:** `claude-opus-4.1`, `claude-sonnet-4`, `claude-haiku-4.5`, etc.

**Example:**
```json
{
  "model": "claude-opus-4.1"
}
```

### `budget` (optional)
**Type:** number  
**Description:** The maximum ACU (Agent Compute Unit) budget for this step. This is informational only; actual ACU limits are managed at the account level.

**Default:** Not enforced  
**Unit:** ACUs

**Example:**
```json
{
  "budget": 100
}
```

### `timeout` (optional)
**Type:** number  
**Description:** The maximum execution time for this step in seconds. If the step exceeds this time, it will be terminated.

**Default:** No timeout  
**Unit:** Seconds

**Example:**
```json
{
  "timeout": 300
}
```

### `verify` (optional)
**Type:** string  
**Description:** Path to a verification script (relative to the step directory) that validates the step's output. The script should:
- Exit with code 0 for success
- Exit with code 1 for hard failure (stop saga)
- Exit with code 2 for soft failure (self-correction needed)

**Default:** No verification

**Example:**
```json
{
  "verify": "scripts/verify.sh"
}
```

### `agent_config` (optional)
**Type:** string  
**Description:** Path to a step-specific agent configuration file that defines permissions for the Devin agent. This allows fine-grained permission control at the step level.

The path can be:
- **Relative:** Resolved relative to the step directory (e.g., `"agent-config.json"`)
- **Absolute:** Used as-is (e.g., `"/path/to/config.json"`)
- **With traversal:** Supports relative path traversal (e.g., `"../shared/agent-config.json"`)

If not specified, the step falls back to the global `.devin/agent-config.json`.

**Default:** Falls back to global `.devin/agent-config.json`

**Example with relative path:**
```json
{
  "agent_config": "agent-config.json"
}
```

**Example with absolute path:**
```json
{
  "agent_config": "/etc/devin/restricted-config.json"
}
```

## Complete Example

### Basic Step (no agent config)
```json
{
  "prompt": "Review the code and suggest improvements",
  "model": "claude-opus-4.1",
  "timeout": 300,
  "verify": "scripts/verify.sh"
}
```

### Step with Step-Specific Agent Config
```json
{
  "prompt": "Deploy the application to production",
  "model": "claude-opus-4.1",
  "budget": 200,
  "timeout": 600,
  "verify": "scripts/verify-deployment.sh",
  "agent_config": "agent-config.json"
}
```

### Step with Shared Agent Config
```json
{
  "prompt": "Run security audit",
  "model": "claude-opus-4.1",
  "agent_config": "../shared/security-config.json"
}
```

## Agent Configuration

### Overview
The agent configuration file (referenced by `agent_config`) is a JSON file that specifies which files and directories the Devin agent can read and write.

### Schema
```json
{
  "permissions": {
    "allow": ["string"],
    "deny": ["string"]
  }
}
```

### Permission Patterns
Permissions use glob patterns to specify file paths:

- `Write(src/**)` - Allow writing to any file under `src/`
- `Read(docs/**)` - Allow reading any file under `docs/`
- `Write(*.lock)` - Allow writing any `.lock` file
- `Deny(orchestrator/**)` - Deny access to `orchestrator/` directory

### Example Agent Config
```json
{
  "permissions": {
    "allow": [
      "Write(src/**)",
      "Write(tests/**)",
      "Read(docs/**)"
    ],
    "deny": [
      "Write(*.lock)",
      "Write(.env*)",
      "Write(.git*)"
    ]
  }
}
```

## Path Resolution

### Relative Paths
Relative paths in `agent_config` are resolved relative to the step directory:

```
steps/
  my-step/
    step.json                 # Contains: "agent_config": "agent-config.json"
    agent-config.json         # Resolved to: steps/my-step/agent-config.json
```

### Absolute Paths
Absolute paths are used as-is:

```json
{
  "agent_config": "/etc/devin/agent-config.json"
}
```

### Relative Traversal
You can traverse up the directory tree:

```
steps/
  my-step/
    step.json                 # Contains: "agent_config": "../shared/agent-config.json"
  shared/
    agent-config.json         # Resolved to: steps/shared/agent-config.json
```

## Fallback Behavior

If a step does not specify `agent_config`, the DevinWrapper falls back to the global configuration:

```
Global config location: .devin/agent-config.json
```

This ensures backward compatibility with existing steps that don't specify a step-specific configuration.

## Validation

During saga validation, the following checks are performed:

1. **File Existence:** If `agent_config` is specified, the file must exist
2. **File Type:** The path must point to a file, not a directory
3. **Readability:** The file must be readable by the process

If validation fails, the saga will not execute and a clear error message will be displayed.

## Best Practices

1. **Principle of Least Privilege:** Only grant permissions that the step actually needs
2. **Shared Configs:** Use shared agent configs for common permission patterns
3. **Documentation:** Document why each permission is needed in a comment
4. **Testing:** Test steps with restrictive configs to ensure they work correctly
5. **Version Control:** Commit agent configs to version control for auditability

## Migration Guide

### From Global Config Only
If you currently rely on the global `.devin/agent-config.json`:

1. No changes required - steps will continue to work
2. Optionally, create step-specific configs for steps with different permission needs
3. Update `step.json` to reference the step-specific config

### Example Migration
**Before:**
```json
{
  "prompt": "Deploy application",
  "model": "claude-opus-4.1"
}
```

**After (with step-specific config):**
```json
{
  "prompt": "Deploy application",
  "model": "claude-opus-4.1",
  "agent_config": "agent-config.json"
}
```

Then create `steps/deploy/agent-config.json` with appropriate permissions.
