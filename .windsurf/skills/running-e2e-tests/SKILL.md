---
name: running-e2e-tests
description: How to run Playwright e2e tests. Use this skill when running e2e tests, executing playwright tests, verifying test fixes, debugging test failures, running specific test files or patterns, or need to know test execution commands. Make sure to use this skill whenever you need to execute tests, even if the user just says "run the tests" or "verify this works" - all test execution should follow proper patterns.
---

# Running E2E Tests

This skill guides you through running Playwright e2e tests.

## When to Use This Skill

- Running e2e tests (full suite or specific tests)
- Executing Playwright tests
- Verifying test fixes after implementation
- Debugging test failures
- Running specific test files or patterns
- Need to know test execution commands

## Repository-Specific Context

**Test Framework**: Playwright with TypeScript  
**Test Location**: `e2e/tests/`  
**Configuration**: `playwright.config.ts`

## Command Patterns

### Run Full Test Suite
```bash
# Standard execution
npx playwright test

# Or using package.json script (if defined)
npm run test:e2e
```

### Run Specific Test File
```bash
# Pattern: npx playwright test [relative-path-to-spec]
# Path is relative to project root or e2e directory

npx playwright test e2e/tests/feature/test.spec.ts
npx playwright test tests/auth/login.spec.ts
```

### Run Specific Test by Name Pattern
```bash
# Use -g flag with test name pattern (supports regex)

npx playwright test -g "should login successfully"
npx playwright test e2e/tests/feature/test.spec.ts -g "critical workflow"

# Multiple words - use quotes
npx playwright test -g "user can submit form"
```

### Run Multiple Specific Files
```bash
# Space-separated file paths
npx playwright test tests/auth/login.spec.ts tests/auth/logout.spec.ts
```

### Run Tests in Directory
```bash
# Run all tests in a directory
npx playwright test e2e/tests/auth/
npx playwright test tests/feature/
```

### Run with UI Mode (Headed)
```bash
# Interactive mode with browser visible
npx playwright test --headed

# Or use UI mode for debugging
npx playwright test --ui
```

### Run in Debug Mode
```bash
# Step through tests with debugger
npx playwright test --debug

# Debug specific test
npx playwright test e2e/tests/feature/test.spec.ts --debug
```

## Test Results Location

After running tests, results are typically in:
```
test-results/
playwright-report/
```

Each failed test creates a directory with:
- `logs/console.log` - Browser console output (if BaseContext used)
- `logs/network.log` - Network requests/responses (if BaseContext used)
- `logs/page-errors.log` - JavaScript errors (if BaseContext used)
- `logs/test-context.log` - Test state transitions (if BaseContext used)
- `test-failed-*.png` - Screenshots at failure
- `video.webm` - Video recording
- `trace.zip` - Playwright trace

## Common Use Cases

### Debugging Single Failing Test
```bash
# 1. Identify test file and name from test-results or error output
# 2. Run just that test
npx playwright test e2e/tests/feature/test.spec.ts -g "specific test name"
```

### Verifying Fix for Multiple Related Tests
```bash
# Run all tests in the file
npx playwright test e2e/tests/feature/test.spec.ts
```

### Regression Check After Fix
```bash
# Run full suite to ensure no new failures
npx playwright test
```

### Testing Specific Feature Area
```bash
# Run all tests in a directory
npx playwright test e2e/tests/feature/
```

## Viewing Test Reports

### HTML Report
```bash
# Generate and open HTML report
npx playwright show-report

# Or if report already exists
npx playwright show-report playwright-report
```

### Trace Viewer
```bash
# View specific trace
npx playwright show-trace test-results/my-test-chromium/trace.zip

# Or open from HTML report (click on trace link)
```

Trace viewer features:
- Timeline of all actions
- DOM snapshots at each step
- Network activity
- Console logs
- Source code
- Screenshots

## Configuration Options

### playwright.config.ts
```typescript
export default defineConfig({
  // Test directory
  testDir: './e2e/tests',
  
  // Timeout per test
  timeout: 30000,
  
  // Retries on failure
  retries: process.env.CI ? 2 : 0,
  
  // Parallel execution
  workers: process.env.CI ? 1 : undefined,
  
  // Reporter
  reporter: [
    ['html'],
    ['list']
  ],
  
  use: {
    // Base URL
    baseURL: 'http://localhost:3000',
    
    // Screenshot on failure
    screenshot: 'only-on-failure',
    
    // Video on failure
    video: 'retain-on-failure',
    
    // Trace on first retry
    trace: 'on-first-retry',
  },
});
```

## Troubleshooting

### Tests pass locally but fail in CI
**Possible causes:**
- Environment variables not set in CI
- Backend API version mismatch
- Seed data inconsistency
- Timing issues (CI may be slower)

**Solution:** 
- Verify environment variables
- Check CI logs for specific errors
- Add appropriate waits for slower environments

### "Cannot find module" errors
**Cause:** TypeScript paths not resolved  
**Solution:** Check `tsconfig.json` and ensure paths are configured correctly

### Browser not found
**Cause:** Playwright browsers not installed  
**Solution:** 
```bash
npx playwright install
```

### Permission denied on test-results
**Cause:** Previous test run created files with different permissions  
**Solution:** 
```bash
rm -rf test-results playwright-report
npx playwright test
```

## Integration with Debugging Workflow

### During Review Phase
If test-results already exist, you don't need to run tests - just analyze existing results:
```bash
ls test-results/
```

### During Fix Phase - Verification
After implementing fix:
```bash
# Run the specific test
npx playwright test [test-file] -g "[test-name]"

# If passes, run full suite for regression check
npx playwright test
```

## Quick Reference

| Goal | Command |
|------|---------|
| Full suite | `npx playwright test` |
| One file | `npx playwright test path/to/file.spec.ts` |
| One test | `npx playwright test path/to/file.spec.ts -g "test name"` |
| Multiple files | `npx playwright test file1.spec.ts file2.spec.ts` |
| Directory | `npx playwright test directory-name/` |
| With UI | `npx playwright test --ui` |
| Debug mode | `npx playwright test --debug` |
| Show report | `npx playwright show-report` |

## Key Principles

1. **Use npx playwright test** - Standard Playwright command
2. **Run from project root** - Working directory matters
3. **Use -g for specific tests** - Faster debugging cycles
4. **Check test-results for logs** - Comprehensive debugging info
5. **Use --ui or --debug for interactive debugging** - Visual feedback

## When in Doubt

- Use `npx playwright test` for everything
- Run from project root directory
- Check `playwright.config.ts` for project-specific settings
- Review test-results directory for failure diagnostics
