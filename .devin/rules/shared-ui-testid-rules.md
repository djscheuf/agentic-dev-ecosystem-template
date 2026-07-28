---
applies_to:
  - "packages/**/*.tsx"
---

# Shared UI Component TestID Standards

Components accept optional `testId` prop and compose child element testIds.

## File Structure

```
ComponentName.tsx
ComponentName.testids.ts
ComponentName.test.tsx
ComponentName.stories.tsx
```

## TestIds File

```typescript
/**
 * Appends suffixes to provided testId.
 * Structure: {testId}-{element}
 */
export const ComponentNameTestIds = {
  container: (testId: string) => testId,
  title: (testId: string) => `${testId}-title`,
  actionButton: (testId: string) => `${testId}-action-button`,
} as const;
```

## Component Implementation

```typescript
import { ComponentNameTestIds } from './ComponentName.testids';

export function ComponentName({ title, testId }: Props) {
  return (
    <div data-testid={testId ? ComponentNameTestIds.container(testId) : undefined}>
      <h1 data-testid={testId ? ComponentNameTestIds.title(testId) : undefined}>
        {title}
      </h1>
      <button data-testid={testId ? ComponentNameTestIds.actionButton(testId) : undefined}>
        Action
      </button>
    </div>
  );
}
```

## Usage

```typescript
<ComponentName title="Example" testId="details-header" />

// Renders: details-header, details-header-title, details-header-action-button
```

## Nested Composition

```typescript
<ChildComponent testId={testId ? `${testId}-child` : undefined} />
```

## Naming

Format: `{testId}-{element-name}` (kebab-case)

Suffixes: `-input`, `-button`, `-section`, `-drawer`, `-dialog`, `-card`

## E2E Usage

```typescript
import { ComponentNameTestIds } from "@coupon-builder/ui/src/components/.../ComponentName.testids";

const button = screen.getByTestId(ComponentNameTestIds.actionButton("details-header"));
```

## Rules

- ✅ Accept optional `testId` prop
- ✅ Function-based testIds
- ✅ Conditional: `testId ? ComponentTestIds.element(testId) : undefined`
- ✅ Use kebab-case
- ✅ Co-locate testIds file
- ✅ Use `as const`
- ❌ No hardcoded strings
- ❌ No camelCase/PascalCase in values
- ❌ TestIds NOT exported from package index
