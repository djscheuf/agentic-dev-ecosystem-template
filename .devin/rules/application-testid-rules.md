---
applies_to:
  - "apps/**/*.tsx"
---

# Application Component TestID Standards

Components own their testIds and ignore any testId prop from parent.

## File Structure

```
ComponentName.tsx
ComponentName.testids.ts
ComponentName.test.tsx
```

## TestIds File

```typescript
/**
 * FormField auto-appends: `-field-{name}-{element}`
 * Example: "card-field-productsAtPos-input"
 */
export const ComponentNameTestIds = {
  Container: "component-name-card",
  FieldNameInput: "component-name-card-field-fieldName-input",
  ActionButton: "component-name-card-action-button",
  NestedDrawer: {
    Container: "component-name-card-nested-drawer",
    SaveButton: "component-name-card-nested-drawer-save-button",
  },
} as const;
```

## Component Implementation

```typescript
import { ComponentNameTestIds } from './ComponentName.testids';

export function ComponentName({ testId, form }: Props) {
  const componentTestId = ComponentNameTestIds.Container; // Ignore prop
  
  return (
    <div data-testid={componentTestId}>
      <FormField testId={componentTestId} name="fieldName" />
      <button data-testid={`${componentTestId}-action-button`}>Action</button>
    </div>
  );
}
```

## Naming

Format: `{component-name}-{element-name}` (kebab-case)

Suffixes: `-input`, `-button`, `-section`, `-drawer`, `-dialog`, `-card`

FormField always uses `-input` (not `-textarea` or `-select`)

## E2E Usage

```typescript
import { OfferDetailsTestIds } from '@/components/OfferDetailsCard/OfferDetailsCard.testids';

const input = screen.getByTestId(OfferDetailsTestIds.ProductsAtPosInput);
```

## Rules

- ✅ Component owns testIds (ignores prop)
- ✅ Pre-compose full testIds in constants
- ✅ Use kebab-case
- ✅ Co-locate testIds file
- ✅ Use `as const`
- ❌ No page-specific prefixes
- ❌ No camelCase/PascalCase in values
- ❌ No hardcoded strings
- ❌ No manual composition in E2E
