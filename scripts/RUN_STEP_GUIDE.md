# Run Step Script Guide

The `run-step.sh` script provides a simple way to execute individual steps through the Devin wrapper without needing to know the full path to `devin_wrapper.py` or construct the command manually.

## Usage

```bash
./scripts/run-step.sh <step_name> <input_file>
```

## Arguments

- **`step_name`** - Name of the step directory under `steps/` (e.g., `extract-story-intent`)
- **`input_file`** - Path to the input file to process (relative or absolute path)

## Examples

### Basic Usage

Run the extract-story-intent step with a markdown file:
```bash
./scripts/run-step.sh extract-story-intent docs/example.md
```

### With Relative Path

Run a step with an input file in a subdirectory:
```bash
./scripts/run-step.sh my-step path/to/input.txt
```

### With Absolute Path

Run a step with an absolute path:
```bash
./scripts/run-step.sh my-step /absolute/path/to/input.txt
```

## What the Script Does

1. **Validates arguments** - Ensures both step name and input file are provided
2. **Checks step directory** - Verifies the step exists under `steps/`
3. **Checks step.json** - Ensures the step has a valid step.json file
4. **Validates input file** - Confirms the input file exists
5. **Resolves paths** - Converts relative paths to absolute paths
6. **Runs the step** - Executes the step through `devin_wrapper.py`
7. **Reports results** - Shows success or failure with exit code

## Output

The script provides colored output for easy reading:

```
[INFO] Running step: extract-story-intent
[INFO] Input file: /absolute/path/to/docs/example.md
[INFO] Step directory: /path/to/steps/extract-story-intent

[INFO] Executing devin_wrapper...
[Devin Wrapper] Executing Devin with model: claude-sonnet-4
...

[INFO] Step completed successfully
```

## Error Handling

The script validates inputs and provides clear error messages:

```bash
$ ./scripts/run-step.sh nonexistent-step input.txt
ERROR: Step directory not found: /path/to/steps/nonexistent-step

$ ./scripts/run-step.sh extract-story-intent nonexistent.txt
ERROR: Input file not found: nonexistent.txt

$ ./scripts/run-step.sh extract-story-intent
Error: Missing required arguments
Usage: run-step.sh <step_name> <input_file>
...
```

## Exit Codes

- **0** - Step executed successfully
- **1** - Error (missing arguments, invalid step, missing input file, etc.)
- **Other** - Exit code from devin_wrapper.py

## Common Use Cases

### Extract Story Intent from a Document

```bash
./scripts/run-step.sh extract-story-intent docs/reqs/my-requirement.md
```

### Run Code Review on a File

```bash
./scripts/run-step.sh code-review src/main.py
```

### Process Multiple Files

```bash
for file in docs/*.md; do
    ./scripts/run-step.sh extract-story-intent "$file"
done
```

### Run with Logging

```bash
./scripts/run-step.sh extract-story-intent input.txt 2>&1 | tee run.log
```

## Troubleshooting

### "Step directory not found"

Ensure the step name matches the directory name under `steps/`:

```bash
# List available steps
ls steps/

# Use the correct step name
./scripts/run-step.sh extract-story-intent input.txt
```

### "step.json not found"

Ensure the step directory contains a `step.json` file:

```bash
ls steps/extract-story-intent/step.json
```

### "Input file not found"

Ensure the input file path is correct (relative or absolute):

```bash
# Check if file exists
ls -la path/to/input.txt

# Use correct path
./scripts/run-step.sh extract-story-intent path/to/input.txt
```

### Script not executable

Make the script executable:

```bash
chmod +x scripts/run-step.sh
```

## Advanced Usage

### Capture Output

```bash
# Capture stdout and stderr
output=$(./scripts/run-step.sh extract-story-intent input.txt 2>&1)
echo "$output"
```

### Run in Background

```bash
# Run in background and capture PID
./scripts/run-step.sh extract-story-intent input.txt &
PID=$!
wait $PID
```

### Conditional Execution

```bash
# Run step only if input file exists
if [[ -f "input.txt" ]]; then
    ./scripts/run-step.sh extract-story-intent input.txt
else
    echo "Input file not found"
fi
```

## Integration with Other Tools

### With Sagas

For running steps as part of a saga, use the saga executor:

```bash
python orchestrator/saga_executor.py sagas/my-saga.json
```

### With CI/CD

```bash
#!/bin/bash
set -e

# Run multiple steps
./scripts/run-step.sh extract-story-intent docs/requirement.md
./scripts/run-step.sh code-review src/main.py
./scripts/run-step.sh generate-tests src/main.py
```

## See Also

- [Step Definition Schema](../docs/step-definition-schema.md)
- [Agent Configuration Guide](../docs/agent-config-guide.md)
- [Devin Wrapper Documentation](../orchestrator/devin_wrapper.py)
