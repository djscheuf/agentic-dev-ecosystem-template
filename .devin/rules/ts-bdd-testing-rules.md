---
applies_to:
  - "**/*.test.ts"
  - "**/*.test.tsx"
---

# TypeScript BDD Testing Standards

## Core Principles

- Write tests first (TDD)
- Each test verifies one behavior
- Tests are independent, isolated, fast, deterministic
- **Test behavior, not implementation** - _"Would test break if CSS changed but behavior stayed same?"_ YES = bad test
- Use GWT for complex tests, simple describe/it for straightforward tests

## What to Test

**✅ Test:**
- Content rendering, user interactions, state changes
- Conditional rendering, accessibility (ARIA, roles, keyboard)
- Data validation, error messages, API calls, side effects

**❌ Never Test:**
- CSS classes (`toHaveClass`), colors, fonts, spacing
- Component internal structure, styling library specifics
- **Use Storybook for visual testing**

## Test Patterns

### Simple Pattern (Single Assertion)

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';

describe('ComponentName', () => {
  const defaultProps = { title: 'Test', onSubmit: vi.fn() };
  
  describe('when rendered with title', () => {
    it('displays the title', () => {
      render(<ComponentName {...defaultProps} />);
      expect(screen.getByText('Test')).toBeInTheDocument();
    });
  });
  
  describe('when submit clicked', () => {
    it('calls onSubmit', () => {
      render(<ComponentName {...defaultProps} />);
      fireEvent.click(screen.getByRole('button', { name: /submit/i }));
      expect(defaultProps.onSubmit).toHaveBeenCalled();
    });
  });
});
```

### Enhanced GWT Pattern (Multiple Assertions)

```typescript
describe('apiClient', () => {
  beforeEach(() => { vi.clearAllMocks(); });
  
  describe('GIVEN token available', () => {
    beforeEach(() => { localStorage.setItem('auth_token', 'test-token'); });
    
    describe('WHEN request made', () => {
      let response: Response;
      
      beforeEach(async () => {
        response = await apiClient('https://api.example.com');
      });
      
      it('THEN adds Authorization header', () => {
        const headers = vi.mocked(fetch).mock.calls[0][1]?.headers as Headers;
        expect(headers.get('Authorization')).toBe('Bearer test-token');
      });
      
      it('THEN returns response', () => {
        expect(response).toBeDefined();
      });
    });
  });
});
```

## Naming

```typescript
describe('ComponentName', () => {})           // Top level
describe('GIVEN user logged in', () => {})    // GWT context
describe('WHEN button clicked', () => {})     // GWT action
describe('when form invalid', () => {})       // Natural language

it('THEN displays user name', () => {})       // GWT
it('displays user name', () => {})            // Natural language
```

**Avoid:** `it('should...')`, `it('test...')`, `it('works correctly')`, mixing GWT and natural language

## File Structure

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ComponentName } from './ComponentName';

describe('ComponentName', () => {
  const defaultProps = { title: 'Test', onSubmit: vi.fn() };
  
  beforeEach(() => { vi.clearAllMocks(); });
  
  describe('rendering', () => {});
  describe('user interactions', () => {});
  describe('error handling', () => {});
});
```

## Mocking

```typescript
// Functions
const mockOnClick = vi.fn();
expect(mockOnClick).toHaveBeenCalled();
expect(mockOnClick).toHaveBeenCalledTimes(1);
expect(mockOnClick).toHaveBeenCalledWith(expectedArg);
beforeEach(() => { vi.clearAllMocks(); });

// Modules
vi.mock('./api-client', () => ({ apiClient: vi.fn() }));
import { apiClient } from './api-client';
const mockedApiClient = vi.mocked(apiClient);

// Return values
mockFn.mockReturnValue('result');
mockFn.mockResolvedValue({ data: 'result' });
mockFn.mockRejectedValue(new Error('Failed'));
mockFn.mockReturnValueOnce('first').mockReturnValueOnce('second');
```

## Async Tests

```typescript
it('fetches user data', async () => {
  const result = await fetchUser('123');
  expect(result).toBeDefined();
});

it('throws error', async () => {
  await expect(fetchUser('invalid')).rejects.toThrow(NotFoundError);
});

it('displays user after loading', async () => {
  render(<UserProfile userId="123" />);
  expect(await screen.findByText('John Doe')).toBeInTheDocument();
});

it('hides loading spinner', async () => {
  render(<UserProfile userId="123" />);
  await waitFor(() => {
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });
});
```

## Test Data

```typescript
// Factory
const createUser = (overrides: Partial<User> = {}): User => ({
  id: 'user-123',
  name: 'Default',
  email: 'default@example.com',
  ...overrides,
});

// Fixtures
export const testUsers = {
  active: { id: '1', name: 'Active User', status: 'active' },
  inactive: { id: '2', name: 'Inactive User', status: 'inactive' },
};
```

## React Testing

```typescript
import { render, screen, fireEvent } from '@testing-library/react';

// Render
render(<Button>Click me</Button>);
render(<AuthProvider><UserProfile userId="123" /></AuthProvider>);

// Query (prefer getByRole)
screen.getByRole('button', { name: /submit/i });
screen.getByRole('textbox', { name: /email/i });
screen.getByLabelText('Email address');
screen.getByText('Welcome');
screen.getByTestId('custom-element');

// Query variants
screen.getBy*()     // Throws if not found
screen.queryBy*()   // Returns null if not found
screen.findBy*()    // Async - waits for element

// Interactions
fireEvent.click(screen.getByRole('button'));
fireEvent.change(input, { target: { value: 'test@example.com' } });
fireEvent.submit(form);
fireEvent.keyDown(input, { key: 'Enter' });
```

## TestId Queries

```typescript
// Import constants
import { ComponentTestIds } from './Component.testids';

// Query patterns
const saveButton = screen.getByTestId(ComponentTestIds.SaveButton);
const input = screen.getByTestId(`${ComponentTestIds.Container}-input`);

// Test behavior, NOT testId values
const button = screen.getByTestId(ComponentTestIds.SaveButton);
expect(button).toBeEnabled();
fireEvent.click(button);
expect(mockOnSave).toHaveBeenCalled();

// ❌ Never test testId attribute
expect(button).toHaveAttribute('data-testid', 'save-button'); // FORBIDDEN

// Prefer semantic queries
screen.getByRole('button', { name: /save/i });  // Better than testId
```

## Common Patterns

```typescript
// State changes
it('toggles visibility', () => {
  render(<CollapsibleCard title="Test" />);
  expect(screen.getByText('Content')).toBeVisible();
  fireEvent.click(screen.getByRole('button'));
  expect(screen.getByText('Content')).not.toBeVisible();
});

// Error states
it('displays error message', async () => {
  vi.mocked(apiClient).mockRejectedValue(new Error('Network error'));
  render(<UserProfile userId="123" />);
  expect(await screen.findByText(/failed to load/i)).toBeInTheDocument();
});

// Conditional rendering
it('shows edit button when permitted', () => {
  render(<UserCard user={user} canEdit />);
  expect(screen.getByRole('button', { name: /edit/i })).toBeInTheDocument();
});
```

## Parameterized Tests

```typescript
it.each([
  ['user@example.com', true],
  ['invalid-email', false],
])('validateEmail(%s) returns %s', (email, expected) => {
  expect(validateEmail(email)).toBe(expected);
});

const testCases = [
  { input: 0, expected: 0, description: 'returns 0 for input 0' },
  { input: 10, expected: 55, description: 'calculates correctly' },
];
it.each(testCases)('$description', ({ input, expected }) => {
  expect(fibonacci(input)).toBe(expected);
});
```

## Coverage Targets

- Unit tests: 80% line coverage
- Critical business logic: 100% branch coverage
- Integration tests: All API endpoints and database operations

**Coverage is NOT a goal** - Write tests to verify behavior, not hit percentages.

## Forbidden Practices

- ❌ Test CSS classes, colors, styling (`toHaveClass`, `toHaveStyle`)
- ❌ Test implementation details (internal state, private methods)
- ❌ Test testId attribute values (`toHaveAttribute('data-testid', ...)`)
- ❌ Test interdependence, hardcoded delays (`setTimeout`)
- ❌ Ignore flaky tests, mock external dependencies without wrapping
- ❌ Multiple Acts in single test, share mutable state between tests
- ❌ Use `any` type, mix GWT and natural language naming
- ❌ Hardcode testId strings (import from `.testids.ts`)

## Quick Reference

**Pattern selection:**
- Single assertion → Simple Pattern
- Multiple assertions for same action → Enhanced GWT

**Query priority:**
1. `getByRole` (semantic, accessible)
2. `getByLabelText` (forms)
3. `getByTestId` (last resort)

**Mocking:**
- Own code → `vi.mock()` directly
- External dependency → Wrap first, mock wrapper

