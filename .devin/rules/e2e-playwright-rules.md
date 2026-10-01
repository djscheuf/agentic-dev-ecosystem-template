# E2E Playwright Test Rules (*.spec.ts)

**Applies to:** `apps/[app-name]/e2e/**/*.spec.ts`

## File Naming

- Extension: `.spec.ts`
- Location: `e2e/tests/`
- Format: `feature-name.spec.ts`

---

## Test Scope

### ✅ Test Integration Only
- API integration (frontend ↔ backend)
- State persistence across navigation
- Multi-step workflows
- Navigation & routing
- File upload/download persistence

### ❌ Do NOT Test
- Component behavior (dropdowns, buttons, UI state)
- Validation logic
- Calculations
- CSS/styling
- Duplicate workflows

## Three-Layer Architecture

### Layer 1: Page Objects

**Location:** `e2e/page-objects/[PageName]Page.ts`

**Rules:**
- Define locators with `data-testid`
- Basic interactions only: `click`, `fill`, `navigate`
- Return `Locator` objects
- NO assertions, NO orchestration, NO business logic
```typescript
export class CreatePage {
  readonly page: Page;
  readonly descriptionInput: Locator;
  readonly submitButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.descriptionInput = page.getByTestId(`${ItemDetailsTestIds.Container}-field-description-input`);
    this.submitButton = page.getByTestId('submit-button');
  }

  async navigate() { await this.page.goto('/items/create'); }
  async fillDescription(desc: string) { await this.descriptionInput.fill(desc); }
  async clickSubmit() { await this.submitButton.click(); }
}
```

### Layer 2: Contexts

**Location:** `e2e/contexts/[Feature]Context.ts`

**Rules:**
- Extend `BaseContext` for automatic log capture
- Organize into GIVEN/WHEN/THEN sections (JSDoc comments)
- ALL assertions go here
- Orchestrate page objects
- Track test state with `logTestContext()`
- NO direct Page API usage
```typescript
export class CreateItemContext extends BaseContext {
  private createPage: CreatePage;
  private testItemDescription?: string;

  constructor(page: Page) {
    super(page);
    this.createPage = new CreatePage(page);
  }

  // ========== GIVEN ==========
  async givenUserIsOnCreatePage() {
    this.logTestContext("Navigating to create page");
    await this.createPage.navigate();
    await this.page.waitForLoadState('networkidle');
  }

  // ========== WHEN ==========
  async whenUserFillsRequiredFieldsAndSubmits(description: string) {
    this.testItemDescription = description;
    this.logTestContext("Filling form and submitting", { description });
    await this.createPage.fillDescription(description);
    await this.createPage.clickSubmit();
    await this.page.waitForURL(/\/items\/[a-f0-9-]+$/i);
  }

  // ========== THEN ==========
  async thenNavigatedToItemDetailsPage() {
    await expect(this.page).toHaveURL(/\/items\/[a-f0-9-]+$/i);
  }
}
```

### Layer 3: Test Specs

**Location:** `e2e/tests/[feature-name].spec.ts`

**Rules:**
- Nested `describe` blocks for GWT
- Initialize context in `beforeEach`
- One assertion per test
- Add `afterEach` for log dumps
- NO complex logic, NO direct page object calls
```typescript
test.describe("Create Item", () => {
  test.describe("GIVEN user is on the create page", () => {
    let context: CreateItemContext;

    test.beforeEach(async ({ page }) => {
      context = new CreateItemContext(page);
      await context.givenUserIsOnCreatePage();
    });

    test.afterEach(async ({}, testInfo) => {
      if (testInfo.status === "failed" || testInfo.status === "timedOut") {
        await context.dumpLogsToFiles(testInfo.outputDir);
      }
    });

    test.describe("WHEN user fills required fields and submits", () => {
      test.beforeEach(async () => {
        await context.whenUserFillsRequiredFieldsAndSubmits(`E2E Test ${Date.now()}`);
      });

      test("THEN navigates to item details page", async () => {
        await context.thenNavigatedToItemDetailsPage();
      });
    });
  });
});
```

## TestID Patterns

**Import component testIds:**
```typescript
import { ItemDetailsTestIds } from '@/components/ItemDetailsCard/ItemDetailsCard.testids';
page.getByTestId(`${ItemDetailsTestIds.Container}-field-description-input`);
```

**FormField pattern:** `{componentTestId}-field-{fieldName}-input` (always `-input`)

**URL matching:** Use GUID pattern `/\/items\/[a-f0-9-]+$/i` (not `\d+`)

## Waiting Strategy

**NO arbitrary timeouts:**
```typescript
// ❌ BAD
await button.click();
await this.page.waitForTimeout(500);
```

**Use deterministic waits:**
```typescript
// ✅ Wait for element
await button.click();
await newRow.waitFor({ state: 'visible' });

// ✅ Trust Playwright auto-wait
await dropdown.click();
await this.page.getByRole('option', { name: 'Value' }).click();

// ⚠️ CAUTION: waitForResponse - Check timing first!
// Only use if the API call happens AFTER your action
// If API call happens at page load, use network logs instead
const responsePromise = this.page.waitForResponse(resp => 
  resp.url().includes('/api/items')
);
await button.click(); // Action that triggers the API call
await responsePromise;

// ✅ PREFERRED: Verify via network logs (works for any timing)
await button.click();
await this.page.waitForLoadState('networkidle'); // Wait for network activity to settle
const networkLogs = this.getNetworkLogs();
const response = networkLogs.find(log => 
  log.type === "response" && 
  log.url.includes('/api/items')
);
expect(response).toBeDefined();
expect(response?.status).toBe(200);

// ✅ Wait for navigation
await this.page.waitForLoadState('networkidle');
```

**Performance targets:** < 1s page load, < 2s form, < 5s workflow, max 12s

## Test Data

- Use pre-seeded database data
- Identify by descriptions (NOT hardcoded IDs)
- Throw errors if test data missing

```typescript
async givenItemExistsWithDescription(description: string) {
  const itemCard = this.landingPage.getItemCardByDescription(description);
  if (!(await itemCard.isVisible())) {
    throw new Error(`Test data missing: Item "${description}" not found`);
  }
}
```

## API Verification

**Use API for:** Timestamps, precise values, data integrity, timing-sensitive checks

**Use UI for:** Visibility, interactions, navigation, client-side state

```typescript
async thenLastModifiedDateHasChanged(originalTimestamp: Date): Promise<void> {
  const item = await getItemFromApi(this.currentItemId, getAuthToken());
  expect(item.lastModified.getTime()).toBeGreaterThan(originalTimestamp.getTime());
}
```

## Debugging

**Extend BaseContext** for automatic log capture:
- Browser console logs
- Network requests/responses
- Page errors (JavaScript exceptions)
- Test context (state transitions)

**Add strategic logging:**
```typescript
// In GIVEN/WHEN/THEN methods
this.logTestContext("Creating item", { itemId, startDate });
this.logTestContext("Submitting item");
```

**Dump logs on failure (required):**
```typescript
test.afterEach(async ({}, testInfo) => {
  if (testInfo.status === "failed" || testInfo.status === "timedOut") {
    await context.dumpLogsToFiles(testInfo.outputDir);
  }
});
```

**Log files:** `test-results/{test-name}/logs/` (console.log, network.log, page-errors.log, test-context.log)

## Naming

**Files:**
- Page Objects: `[PageName]Page.ts`
- Contexts: `[Feature]Context.ts`
- Tests: `[feature-name].spec.ts`

**Methods:**
- Page Objects: Action verbs (`clickSubmit`, `fillDescription`)
- Contexts: `givenUserIsOn...`, `whenUserClicks...`, `thenNavigatedTo...`

**Test descriptions:** "GIVEN [context]" → "WHEN [action]" → "THEN [outcome]"

## Anti-Patterns

- Testing component behavior (dropdown states, button visibility)
- Testing validation logic (field validation rules)
- Testing calculations (budget totals, sums)
- Duplicate workflows (one comprehensive test, not many narrow tests)
- Arbitrary timeouts (`waitForTimeout`)
- Hardcoded entity IDs
- Direct Page API usage in contexts
- Multiple assertions per test
- Complex logic in test specs
