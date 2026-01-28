---
applies_to:
  - "**/*.tsx"
---

# React TypeScript Standards

## General Principles

- Follow all TypeScript standards from typescript-rules.md
- Use function components (not class components)
- Always define explicit prop interfaces
- Name by intent, not implementation
- Co-locate logic with custom hooks when complex

## Component Naming

**Format:** `PascalCase.tsx` - Name describes what it represents/does

```typescript
// Pages: LandingPage.tsx, DashboardPage.tsx
// Forms: CreateTacticForm.tsx, EditUserForm.tsx
// Cards: TacticCard.tsx, UserCard.tsx
// Lists: TacticList.tsx, UserList.tsx
// Modals: ConfirmDeleteModal.tsx, SettingsModal.tsx
// Layouts: MainLayout.tsx, AuthLayout.tsx
```

## Component Structure

```typescript
// 1. Imports (grouped: React → External → Internal)
import { useState, useEffect } from 'react';
import { ExternalLibrary } from 'external-library';
import { SharedComponent } from '@/shared/components';

// 2. Types
interface ComponentProps {
  title: string;
  onSubmit: (data: FormData) => void;
  isLoading?: boolean;
}

// 3. Component
export function ComponentName({ title, onSubmit, isLoading = false }: ComponentProps) {
  // 3a. Hooks
  const [state, setState] = useState('');
  
  // 3b. Event handlers
  const handleSubmit = () => onSubmit(data);
  
  // 3c. Effects
  useEffect(() => {
    // Effect logic
  }, []);
  
  // 3d. JSX
  return (
    <div>
      <h1>{title}</h1>
    </div>
  );
}
```

## Props Naming

**Interface:** `{ComponentName}Props`

```typescript
interface ButtonProps { }           // ✅ Good
interface Props { }                  // ❌ Too generic
interface IButtonProps { }           // ❌ No I prefix
```

**Boolean Props:** `is`, `has`, `should`, `can` prefix

```typescript
interface ComponentProps {
  isVisible?: boolean;
  isLoading?: boolean;
  hasError?: boolean;
  canEdit?: boolean;
  shouldAutoFocus?: boolean;
}
```

**Event Handlers:** `on` prefix

```typescript
interface ComponentProps {
  onClick?: () => void;
  onChange?: (value: string) => void;
  onSubmit?: (data: FormData) => void;
  onUserSelect?: (user: User) => void;
}
```

**Render Props:** `render` prefix

```typescript
interface ComponentProps {
  renderHeader?: () => React.ReactNode;
  renderFooter?: () => React.ReactNode;
}
```

## Component Definition

```typescript
// Preferred: Named function export
export function Button({ label, onClick, variant = "primary" }: ButtonProps) {
  return <button onClick={onClick}>{label}</button>;
}

// Alternative: Arrow function
export const Button: React.FC<ButtonProps> = ({ label, onClick }) => {
  return <button onClick={onClick}>{label}</button>;
};
```

## Hooks Typing

```typescript
// useState - Type inference
const [count, setCount] = useState(0);
const [name, setName] = useState('');

// useState - Explicit type
const [user, setUser] = useState<User | null>(null);
const [items, setItems] = useState<Item[]>([]);

// useRef - DOM refs
const inputRef = useRef<HTMLInputElement>(null);
const divRef = useRef<HTMLDivElement>(null);

// useRef - Mutable values
const countRef = useRef<number>(0);
const timerRef = useRef<NodeJS.Timeout | null>(null);

// useEffect - With cleanup
useEffect(() => {
  const subscription = subscribe();
  return () => subscription.unsubscribe();
}, [dependency]);

// Custom hooks - Explicit return type
function useUserData(userId: string): {
  user: User | null;
  isLoading: boolean;
  error: Error | null;
} {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  return { user, isLoading, error };
}
```

## Event Handlers

**Event Types:**

```typescript
const handleSubmit = (event: React.FormEvent<HTMLFormElement>): void => {
  event.preventDefault();
};

const handleChange = (event: React.ChangeEvent<HTMLInputElement>): void => {
  setValue(event.target.value);
};

const handleClick = (event: React.MouseEvent<HTMLButtonElement>): void => {
  console.log('Clicked');
};

const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>): void => {
  if (event.key === 'Enter') handleSubmit();
};
```

**Naming:** Prefix with `handle`

```typescript
const handleSubmit = () => { };      // ✅ Good
const handleUserSelect = (user: User) => { };
const submit = () => { };            // ❌ Use handleSubmit
const onSubmit = () => { };          // ❌ on is for props
```

## Composition Patterns

**Children:**

```typescript
interface ContainerProps {
  children: React.ReactNode;
  title: string;
}

export function Container({ children, title }: ContainerProps) {
  return (
    <div>
      <h1>{title}</h1>
      {children}
    </div>
  );
}
```

**Render Props:**

```typescript
interface ListProps<T> {
  items: T[];
  renderItem: (item: T) => React.ReactNode;
}

export function List<T>({ items, renderItem }: ListProps<T>) {
  return (
    <ul>
      {items.map((item, index) => (
        <li key={index}>{renderItem(item)}</li>
      ))}
    </ul>
  );
}
```

**Generic Components:**

```typescript
interface SelectProps<T extends { id: string; name: string }> {
  items: T[];
  onSelect: (item: T) => void;
  renderItem?: (item: T) => React.ReactNode;
}

export function Select<T extends { id: string; name: string }>({
  items,
  onSelect,
  renderItem = (item) => item.name,
}: SelectProps<T>) {
  return (
    <select onChange={(e) => {
      const item = items.find(i => i.id === e.target.value);
      if (item) onSelect(item);
    }}>
      {items.map(item => (
        <option key={item.id} value={item.id}>{renderItem(item)}</option>
      ))}
    </select>
  );
}
```

## TestId Attributes

**See separate rules files:**
- Application components: `application-testid-rules.md`
- Shared UI components: `shared-ui-testid-rules.md`

## React Context Patterns

```typescript
// Single provider per domain
const TacticContext = createContext<TacticContextValue | undefined>(undefined);

export function TacticProvider({ tacticId, children }: Props) {
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  return (
    <TacticContext.Provider value={{ tacticId, attachments }}>
      {children}
    </TacticContext.Provider>
  );
}

// Specialized hooks slice context
export function useTactic() {
  const context = useContext(TacticContext);
  if (!context) throw new Error('useTactic must be used within TacticProvider');
  return { tacticId: context.tacticId, tacticStatus: context.tacticStatus };
}

// Page-level placement
<TacticProvider tacticId={tactic?.id}>
  <TacticForm ... />
</TacticProvider>
```

- ✅ Single provider per domain
- ✅ Specialized hooks for slicing
- ✅ Page-level placement
- ✅ Throw errors when used outside provider
- ❌ No nested providers for same domain

## Collapsible Form Content

```typescript
const [isExpanded, setIsExpanded] = useState(true);

<div
  style={{
    visibility: isExpanded ? 'visible' : 'hidden',
    height: isExpanded ? 'auto' : '0',
    overflow: 'hidden',
  }}
>
  <FormField name="field1" />
  <FormField name="field2" />
</div>
```

- ✅ Use `visibility: hidden` + `height: 0` + `overflow: hidden`
- ❌ No conditional rendering for form fields
- ❌ No `display: none`

## Component Selection

**ShadCN/Radix:** Complex interactive (Combobox, Select, Dialog), advanced accessibility, state management

**Custom:** Simple (Button, Input, Badge), domain-specific (FileUploadManager, FormField), business logic

```
packages/ui/src/components/
  ui/         # ShadCN/Radix
  atoms/      # Simple custom
  molecules/  # Domain-specific
```

## Cascading Dropdowns

```typescript
useEffect(() => {
  const fetchFilteredData = async () => {
    if (!parentValue) return setFilteredOptions([]);

    const options = await api.getFilteredOptions(parentValue);
    setFilteredOptions(options);

    // Validate current value
    if (currentValue && !options.some(opt => opt.id === currentValue)) {
      form.setFieldValue(fieldName, null);
    }

    // Auto-select if only one option and no current value
    if (options.length === 1 && !currentValue) {
      form.setFieldValue(fieldName, options[0].id);
    }
  };
  fetchFilteredData();
}, [parentValue]);
```

- ✅ Auto-select when exactly one option and no current value
- ✅ Validate current value against filtered options
- ❌ No auto-select when field has value or during initial load

## Error Handling

```typescript
// Critical: no data
if (error && !data) {
  return (
    <>
      <PageHeader {...minimalHeaderProps} />
      <AlertBanner severity="error" message={error.message} />
    </>
  );
}

// Non-critical: operation failed
return (
  <>
    <PageHeader {...fullHeaderProps} />
    {error && data && <AlertBanner severity="warning" message={error.message} />}
    <div>{/* Functional content */}</div>
  </>
);
```

AlertBanner: After header, before content, within container

- ✅ Classify: critical (no data) vs non-critical (operation failed)
- ✅ Use AlertBanner for API errors
- ✅ Preserve cached data when possible
- ✅ Auto-clear on success
- ❌ No error boundaries blocking page for non-critical errors

## Forbidden Practices

- ❌ No class components
- ❌ No `any` for props or state
- ❌ No missing prop interfaces
- ❌ No inline object/array literals in JSX
- ❌ No components defined inside other components
- ❌ No array index as key (unless list never changes)
- ❌ No direct prop/state mutation
- ❌ No `var` (use `const` or `let`)
- ❌ No missing effect cleanup functions
- ❌ No boolean props without `is/has/can/should` prefix
- ❌ No conditional rendering for form fields (use CSS visibility)
- ❌ No nested providers for same domain context

## Quick Reference

| Item | Format | Example |
|------|--------|---------|
| Component File | PascalCase.tsx | `UserProfile.tsx` |
| Component | Named function | `export function Button() {}` |
| Props Interface | {Component}Props | `ButtonProps` |
| Boolean Prop | is/has/can/should | `isLoading`, `hasError` |
| Event Handler Prop | on{Action} | `onClick`, `onSubmit` |
| Event Handler Function | handle{Action} | `handleClick`, `handleSubmit` |
| Render Prop | render{What} | `renderHeader`, `renderItem` |
| Hook Return | Explicit type | `: UseDataReturn` |
