# Scripts Directory

This directory contains utility scripts for running and managing steps in the agentic software factory.

## Available Scripts

### `run-step.sh`
Simple wrapper script for executing individual steps through the Devin wrapper.

**Usage:**
```bash
./scripts/run-step.sh <step_name> <input_file>
```

**Example:**
```bash
./scripts/run-step.sh extract-story-intent docs/example.md
```

**Features:**
- Validates step directory exists
- Validates input file exists
- Resolves relative and absolute paths
- Provides colored output
- Clear error messages
- Exit codes for scripting

**See:** [Run Step Guide](RUN_STEP_GUIDE.md)

---

### `test-orchestrator.sh`
Runs the full test suite for the orchestrator module.

**Usage:**
```bash
./scripts/test-orchestrator.sh
```

**What it does:**
- Runs all unit tests
- Generates coverage reports
- Validates code quality

---

## Quick Start

### Run a Single Step

```bash
./scripts/run-step.sh extract-story-intent docs/my-requirement.md
```

### Run Tests

```bash
./scripts/test-orchestrator.sh
```

### Run Multiple Steps

```bash
for file in docs/*.md; do
    ./scripts/run-step.sh extract-story-intent "$file"
done
```

---

## Script Development

When adding new scripts:

1. Use `#!/usr/bin/env bash` shebang for portability
2. Make scripts executable: `chmod +x script.sh`
3. Add usage documentation at the top
4. Include error handling and validation
5. Use colored output for clarity
6. Provide clear error messages
7. Document in this README

---

## See Also

- [Run Step Guide](RUN_STEP_GUIDE.md)
- [Step Definition Schema](../docs/step-definition-schema.md)
- [Agent Configuration Guide](../docs/agent-config-guide.md)
