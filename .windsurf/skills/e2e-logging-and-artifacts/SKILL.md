---
name: e2e-logging-and-artifacts
description: How to set up comprehensive logging and artifact extraction for Playwright e2e test suites. Use this skill when creating new e2e test suites, setting up Playwright from scratch, implementing BaseContext logging infrastructure, configuring test failure diagnostics, or adding custom test context logging. Essential for debugging e2e test failures with console logs, network logs, page errors, and Playwright artifacts (screenshots, videos, traces).
---

# E2E Test Logging and Artifacts Setup

This skill guides you through setting up comprehensive logging and artifact extraction for Playwright e2e test suites.

## When to Use This Skill

- Creating new e2e test suites from scratch
- Setting up Playwright logging infrastructure
- Implementing BaseContext for test contexts
- Configuring test failure diagnostics
- Adding custom test context logging
- Debugging e2e test failures

## Overview

E2E tests should capture multiple types of diagnostic information to aid debugging:

1. **Console logs** - Browser console messages (log, warn, error, etc.)
2. **Network logs** - HTTP requests/responses (API calls only)
3. **Page errors** - JavaScript errors and stack traces
4. **Test context logs** - Custom events logged from test code
5. **Playwright artifacts** - Screenshots, videos, and traces (configured in playwright.config.ts)

## Architecture

### BaseContext Logging Infrastructure

All test contexts should extend `BaseContext`, which provides automatic logging collection through Playwright page event listeners.

**Key files:**
- `e2e/contexts/BaseContext.ts` - Core logging infrastructure
- `playwright.config.ts` - Playwright artifact configuration
- Test specs - Call `dumpLogsToFiles()` on failure

## Implementation Guide

### Step 1: Configure Playwright Artifacts

In `playwright.config.ts`, configure automatic artifact collection:

```typescript
export default defineConfig({
  use: {
    // Collect trace on first retry
    trace: "on-first-retry",
    
    // Screenshot on failure
    screenshot: "only-on-failure",
    
    // Video on failure
    video: "retain-on-failure",
  },
});
```

**Artifact types:**
- **trace**: Interactive timeline with DOM snapshots, network, console (`on-first-retry` | `on` | `off`)
- **screenshot**: PNG screenshot (`only-on-failure` | `on` | `off`)
- **video**: WebM video recording (`retain-on-failure` | `on` | `off`)

### Step 2: Create BaseContext with Logging

Create a base context class that all test contexts extend:

```typescript
// e2e/contexts/BaseContext.ts
import { Page } from "@playwright/test";
import * as fs from "fs";
import * as path from "path";

interface ConsoleLogEntry {
  timestamp: string;
  type: string;
  text: string;
  location?: string;
}

interface NetworkLogEntry {
  timestamp: string;
  type: "request" | "response";
  method?: string;
  url: string;
  status?: number;
  statusText?: string;
  headers?: Record<string, string>;
  body?: string;
}

interface PageErrorEntry {
  timestamp: string;
  message: string;
  stack?: string;
}

interface TestContextEntry {
  timestamp: string;
  event: string;
  data?: any;
}

export class BaseContext {
  protected page: Page;
  
  // Log collection arrays
  private consoleLogs: ConsoleLogEntry[] = [];
  private networkLogs: NetworkLogEntry[] = [];
  private pageErrors: PageErrorEntry[] = [];
  private testContextLogs: TestContextEntry[] = [];

  constructor(page: Page) {
    this.page = page;
    this.setupLogging();
  }

  /**
   * Set up page event listeners for comprehensive logging
   */
  private setupLogging(): void {
    // Capture all console messages from the browser
    this.page.on("console", (msg) => {
      const timestamp = new Date().toISOString();
      const type = msg.type();
      const text = msg.text();
      const location = msg.location();

      this.consoleLogs.push({
        timestamp,
        type,
        text,
        location: location.url
          ? `${location.url}:${location.lineNumber}:${location.columnNumber}`
          : undefined,
      });
    });

    // Capture all network requests
    this.page.on("request", async (request) => {
      const timestamp = new Date().toISOString();
      const url = request.url();

      // Only capture detailed info for API calls (not static assets)
      const isApiCall = url.includes("/api/");

      let headers: Record<string, string> | undefined;
      let body: string | undefined;

      if (isApiCall) {
        headers = request.headers();
        const postData = request.postData();
        if (postData) {
          body = postData;
        }
      }

      this.networkLogs.push({
        timestamp,
        type: "request",
        method: request.method(),
        url,
        headers,
        body,
      });
    });

    // Capture all network responses
    this.page.on("response", async (response) => {
      const timestamp = new Date().toISOString();
      const url = response.url();

      // Only capture detailed info for API calls (not static assets)
      const isApiCall = url.includes("/api/");

      let headers: Record<string, string> | undefined;
      let body: string | undefined;

      if (isApiCall) {
        headers = response.headers();
        try {
          const responseBody = await response.text();
          body = responseBody;
        } catch (error) {
          body = "[Unable to read response body]";
        }
      }

      this.networkLogs.push({
        timestamp,
        type: "response",
        url,
        status: response.status(),
        statusText: response.statusText(),
        headers,
        body,
      });
    });

    // Capture page errors (JavaScript errors)
    this.page.on("pageerror", (error) => {
      const timestamp = new Date().toISOString();
      this.pageErrors.push({
        timestamp,
        message: error.message,
        stack: error.stack,
      });
    });
  }

  /**
   * Log a test context event (custom logging from test code)
   * Use this to mark important state transitions or actions
   */
  protected logTestContext(event: string, data?: any): void {
    const timestamp = new Date().toISOString();
    this.testContextLogs.push({
      timestamp,
      event,
      data,
    });
  }

  /**
   * Dump all collected logs to files in the test results directory
   * Called automatically on test failure via afterEach hook
   */
  public async dumpLogsToFiles(outputDir: string): Promise<void> {
    // Create logs subdirectory
    const logsDir = path.join(outputDir, "logs");
    if (!fs.existsSync(logsDir)) {
      fs.mkdirSync(logsDir, { recursive: true });
    }

    // Write console logs
    if (this.consoleLogs.length > 0) {
      const consoleLogPath = path.join(logsDir, "console.log");
      const consoleContent = this.consoleLogs
        .map((entry) => {
          const location = entry.location ? ` [${entry.location}]` : "";
          return `[${entry.timestamp}] [${entry.type.toUpperCase()}]${location} ${entry.text}`;
        })
        .join("\n");
      fs.writeFileSync(consoleLogPath, consoleContent, "utf-8");
    }

    // Write network logs
    if (this.networkLogs.length > 0) {
      const networkLogPath = path.join(logsDir, "network.log");
      const networkContent = this.networkLogs
        .map((entry) => {
          let content = "";
          if (entry.type === "request") {
            content = `[${entry.timestamp}] [REQUEST] ${entry.method} ${entry.url}`;
            if (entry.headers) {
              content += `\n  Headers: ${JSON.stringify(entry.headers, null, 2)}`;
            }
            if (entry.body) {
              content += `\n  Body: ${entry.body}`;
            }
          } else {
            content = `[${entry.timestamp}] [RESPONSE] ${entry.status} ${entry.statusText} ${entry.url}`;
            if (entry.headers) {
              content += `\n  Headers: ${JSON.stringify(entry.headers, null, 2)}`;
            }
            if (entry.body) {
              content += `\n  Body: ${entry.body}`;
            }
          }
          return content;
        })
        .join("\n\n");
      fs.writeFileSync(networkLogPath, networkContent, "utf-8");
    }

    // Write page errors
    if (this.pageErrors.length > 0) {
      const errorLogPath = path.join(logsDir, "page-errors.log");
      const errorContent = this.pageErrors
        .map((entry) => {
          let content = `[${entry.timestamp}] ${entry.message}`;
          if (entry.stack) {
            content += `\n${entry.stack}`;
          }
          return content;
        })
        .join("\n\n");
      fs.writeFileSync(errorLogPath, errorContent, "utf-8");
    }

    // Write test context logs
    if (this.testContextLogs.length > 0) {
      const contextLogPath = path.join(logsDir, "test-context.log");
      const contextContent = this.testContextLogs
        .map((entry) => {
          let content = `[${entry.timestamp}] ${entry.event}`;
          if (entry.data) {
            content += `\n  Data: ${JSON.stringify(entry.data, null, 2)}`;
          }
          return content;
        })
        .join("\n\n");
      fs.writeFileSync(contextLogPath, contextContent, "utf-8");
    }
  }

  /**
   * Get all collected logs (for programmatic access)
   */
  public getConsoleLogs(): ConsoleLogEntry[] {
    return [...this.consoleLogs];
  }

  public getNetworkLogs(): NetworkLogEntry[] {
    return [...this.networkLogs];
  }

  public getPageErrors(): PageErrorEntry[] {
    return [...this.pageErrors];
  }

  public getTestContextLogs(): TestContextEntry[] {
    return [...this.testContextLogs];
  }

  /**
   * Clear all collected logs
   * Useful if you want to reset logging between test phases
   */
  public clearLogs(): void {
    this.consoleLogs = [];
    this.networkLogs = [];
    this.pageErrors = [];
    this.testContextLogs = [];
  }
}
```

### Step 3: Use Logging in Test Specs

In your test spec files, call `dumpLogsToFiles()` in the `afterEach` hook on test failure:

```typescript
// e2e/tests/feature/test.spec.ts
import { test } from "@playwright/test";
import { MyContext } from "../../contexts/MyContext";

test.use({ storageState: "./test-results/.auth-user.json" });

test.describe("Feature Tests", () => {
  let context: MyContext;

  test.beforeEach(async ({ page }) => {
    context = new MyContext(page);
  });

  test.afterEach(async ({ page }, testInfo) => {
    // Dump logs only on test failure
    if (testInfo.status !== "passed") {
      await context.dumpLogsToFiles(testInfo.outputDir);
    }
  });

  test("When I perform action, Then expected result", async () => {
    await context.whenIPerformAction();
    await context.thenExpectedResult();
  });
});
```

### Step 4: Use Custom Test Context Logging

In your context methods, use `logTestContext()` to mark important events:

```typescript
// e2e/contexts/MyContext.ts
export class MyContext extends BaseContext {
  async createDataViaAPI(): Promise<string> {
    this.logTestContext("[SETUP] Creating data via API", {
      endpoint: "/api/data",
      method: "POST",
    });

    const response = await this.page.request.post("/api/data", {
      data: { /* ... */ },
    });

    const data = await response.json();

    this.logTestContext("[SETUP] Data created", {
      status: response.status(),
      id: data.id,
    });

    return data.id;
  }
}
```

## Output Structure

When a test fails, logs are written to the test results directory:

```
test-results/
├── <test-name>-<browser>-<retry>/
│   ├── logs/
│   │   ├── console.log          # Browser console messages
│   │   ├── network.log          # API requests/responses
│   │   ├── page-errors.log      # JavaScript errors
│   │   └── test-context.log     # Custom test events
│   ├── test-failed-1.png        # Screenshot (if enabled)
│   ├── video.webm               # Video (if enabled)
│   └── trace.zip                # Trace (if enabled)
└── .auth-user.json              # Storage state files
```

## Best Practices

### 1. Log Important State Transitions
```typescript
this.logTestContext("[ACTION] Performing critical action", { id });
this.logTestContext("[VERIFICATION] Checking state changed", { 
  expectedState: "COMPLETE" 
});
```

### 2. Filter Network Logs
Only capture API calls (not static assets) to reduce noise:
```typescript
const isApiCall = url.includes("/api/");
```

### 3. Include Context in Logs
Add relevant data to help debugging:
```typescript
this.logTestContext("[ERROR] API call failed", {
  endpoint: "/api/data",
  status: response.status(),
  body: await response.text(),
});
```

### 4. Use Consistent Log Prefixes
- `[SETUP]` - Test data creation
- `[ACTION]` - User actions
- `[VERIFICATION]` - Assertions
- `[ERROR]` - Error conditions
- `[SUCCESS]` - Successful operations

### 5. Dump Logs Only on Failure
```typescript
test.afterEach(async ({ page }, testInfo) => {
  if (testInfo.status !== "passed") {
    await context.dumpLogsToFiles(testInfo.outputDir);
  }
});
```

## Troubleshooting

### Logs not appearing
- Verify `setupLogging()` is called in BaseContext constructor
- Check that context extends BaseContext
- Ensure `afterEach` hook calls `dumpLogsToFiles()`

### Network logs missing request/response bodies
- Verify URL contains `/api/` (or adjust filter)
- Check that response hasn't been consumed elsewhere
- Some responses may be binary (not text)

### Trace files too large
- Use `trace: "on-first-retry"` instead of `"on"`
- Limit test duration
- Clean up old traces regularly

## Summary

This logging infrastructure provides comprehensive diagnostic information for debugging e2e test failures:

1. **Automatic collection** - Logs captured via Playwright event listeners
2. **Structured output** - Separate files for different log types
3. **Minimal overhead** - Only dumps logs on test failure
4. **Rich context** - Custom events with structured data
5. **Playwright integration** - Works alongside screenshots, videos, and traces

When creating new e2e test suites, implement this pattern to ensure robust debugging capabilities.
