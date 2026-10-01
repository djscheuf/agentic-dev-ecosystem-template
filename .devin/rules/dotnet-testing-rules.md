---
trigger: model_decision
description: when you are about to test .NET code, attempting to reproduce a bug, or running any .NET verification script
---
# .NET Testing and Verification Rules

## Running dotnet test Commands

**CRITICAL**: When running `dotnet test` commands, ALWAYS check for BOTH compilation errors AND test failures.

### The Problem

Compilation errors (e.g., `error CS1503`) occur during the build phase and won't appear in test result lines (`Passed!` or `Failed!`). They cause exit code 1 but can be missed by grep filters.

### Correct Approaches

**Option 1: Check exit code directly (PREFERRED)**
```bash
dotnet test tests/Project.Tests/Project.Tests.csproj
# Let command fail naturally - don't pipe to grep
```

**Option 2: Include compilation errors in grep pattern**
```bash
dotnet test tests/Project.Tests/Project.Tests.csproj 2>&1 | grep -E "error CS|Passed!|Failed!"
```

**Option 3: Use a comprehensive test runner script (BEST for full verification)**
```bash
./scripts/run-all-tests.sh
```
*Replace `./scripts/run-all-tests.sh` with your project's comprehensive test runner script. The script should use `set -e` so it catches all failures immediately.*

### WRONG Approach (DO NOT USE)

```bash
# ❌ This misses compilation errors!
dotnet test ... | grep -E "Passed!|Failed!"

# ❌ This also misses errors!
dotnet test ... 2>&1 | tail -5
```

## Verification Strategy

1. **During development**: Run individual test projects directly
   ```bash
   dotnet test tests/[ProjectName].Tests/[ProjectName].Tests.csproj
   ```

2. **Before commits**: Run full test suite
   ```bash
   ./scripts/run-all-tests.sh
   ```

3. **When filtering output**: Include compilation errors
   ```bash
   dotnet test ... 2>&1 | grep -E "error CS|warning CS|Passed!|Failed!"
   ```

## Why run-all-tests.sh is Superior

The `run-all-tests.sh` script:
- Has `set -e` which exits immediately on any failure
- Runs all test suites in sequence
- Provides clear visual progress with emoji markers
- Catches both compilation AND test failures
- Is what CI/CD pipelines should use

## Exit Code Behavior

- **Exit 0**: All tests passed, no compilation errors
- **Exit 1**: Compilation errors OR test failures OR both
- **Always check the actual output** - don't rely solely on exit code

## Common Mistakes to Avoid

1. ❌ Using grep without including compilation error patterns
2. ❌ Ignoring exit codes when piping to grep
3. ❌ Only running individual test projects (missing cross-project issues)
4. ❌ Using `tail` or `head` which can truncate error messages
5. ❌ Not running the full test suite before committing

## Best Practice Workflow

```bash
# 1. Make code changes
# 2. Run affected test project
dotnet test tests/Affected.Tests/Affected.Tests.csproj

# 3. If tests pass, run full suite
./scripts/run-all-tests.sh

# 4. Only commit if full suite passes
git add -A
git commit -m "..."
```

## Integration with Hooks

When implementing pre-commit or post-edit hooks:
- Use `run-all-tests.sh` for comprehensive verification
- Check exit codes directly: `if ! ./scripts/run-all-tests.sh; then exit 1; fi`
- Don't suppress output - developers need to see errors
- Consider using `--verbosity minimal` for faster feedback
