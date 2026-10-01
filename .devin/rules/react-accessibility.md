---
trigger: glob
globs: ["**/*.tsx", "**/*.jsx"]
---

# React Accessibility Conventions

React-specific accessibility patterns that complement core accessibility rules. Auto-activated when working with React components.

## JSX Attribute Differences

### Key Differences from HTML
```jsx
// ✅ React JSX
<label htmlFor="name">Name</label>
<input id="name" className="input" />

// ❌ HTML attributes (don't work in JSX)
<label for="name">Name</label>
<input id="name" class="input" />
```

### ARIA Attributes (Same as HTML)
```jsx
// ✅ ARIA attributes work identically
<button aria-label="Close dialog">×</button>
<div role="dialog" aria-modal="true">...</div>
<input aria-describedby="error-message" />
```

### Event Handlers
```jsx
// ✅ Synthetic events work with keyboard
<button onClick={handleClick}>Click</button>
// Automatically handles Enter and Space keys

// ⚠️ Custom keyboard handling when needed
<div 
  role="button"
  tabIndex={0}
  onClick={handleClick}
  onKeyDown={(e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleClick();
    }
  }}
>
  Custom Button
</div>
```

## Semantic HTML Preservation with Fragments

### Problem: Wrapper Divs Break Semantics
```jsx
// ❌ NEVER - Breaks list semantics
<ul>
  {items.map(item => (
    <div key={item.id}>
      <li>{item.name}</li>
    </div>
  ))}
</ul>

// ❌ NEVER - Breaks table semantics
<table>
  <tbody>
    {rows.map(row => (
      <div key={row.id}>
        <tr><td>{row.data}</td></tr>
      </div>
    ))}
  </tbody>
</table>

// ❌ NEVER - Breaks definition list semantics
<dl>
  {terms.map(term => (
    <div key={term.id}>
      <dt>{term.name}</dt>
      <dd>{term.definition}</dd>
    </div>
  ))}
</dl>
```

### Solution: Use React Fragments
```jsx
// ✅ ALWAYS - Preserves list semantics
import { Fragment } from 'react';

<ul>
  {items.map(item => (
    <Fragment key={item.id}>
      <li>{item.name}</li>
    </Fragment>
  ))}
</ul>

// ✅ ALWAYS - Short syntax when no key needed
<ul>
  <li>Item 1</li>
  <>
    <li>Item 2</li>
    <li>Item 3</li>
  </>
</ul>

// ✅ ALWAYS - Preserves table semantics
<table>
  <tbody>
    {rows.map(row => (
      <Fragment key={row.id}>
        <tr><td>{row.data}</td></tr>
      </Fragment>
    ))}
  </tbody>
</table>

// ✅ ALWAYS - Preserves definition list semantics
<dl>
  {terms.map(term => (
    <Fragment key={term.id}>
      <dt>{term.name}</dt>
      <dd>{term.definition}</dd>
    </Fragment>
  ))}
</dl>
```

## Focus Management Patterns

### Basic Focus Management with useRef
```jsx
import { useRef, useEffect } from 'react';

function Component() {
  const inputRef = useRef(null);

  useEffect(() => {
    // Focus input when component mounts
    inputRef.current?.focus();
  }, []);

  return <input ref={inputRef} type="text" />;
}
```

### Focus After State Changes
```jsx
function SearchResults({ results, isLoading }) {
  const resultsRef = useRef(null);

  useEffect(() => {
    if (!isLoading && results.length > 0) {
      // Move focus to results after search completes
      resultsRef.current?.focus();
    }
  }, [isLoading, results]);

  return (
    <div ref={resultsRef} tabIndex={-1}>
      <h2>Search Results</h2>
      {results.map(result => <ResultItem key={result.id} {...result} />)}
    </div>
  );
}
```

### Modal Focus Management
```jsx
function Modal({ isOpen, onClose, children }) {
  const modalRef = useRef(null);
  const triggerRef = useRef(null);

  useEffect(() => {
    if (isOpen) {
      // Store trigger element
      triggerRef.current = document.activeElement;
      // Move focus inside modal
      modalRef.current?.focus();
    } else if (triggerRef.current) {
      // Restore focus to trigger when modal closes
      triggerRef.current.focus();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div
      ref={modalRef}
      role="dialog"
      aria-modal="true"
      tabIndex={-1}
      onKeyDown={(e) => e.key === 'Escape' && onClose()}
    >
      {children}
      <button onClick={onClose}>Close</button>
    </div>
  );
}
```

### Focus After Deletion
```jsx
function ItemList({ items, onDelete }) {
  const itemRefs = useRef({});

  const handleDelete = (id, index) => {
    onDelete(id);
    
    // Move focus to next item, or previous if last item
    const nextIndex = index < items.length - 1 ? index : index - 1;
    const nextItem = items[nextIndex];
    
    if (nextItem) {
      setTimeout(() => {
        itemRefs.current[nextItem.id]?.focus();
      }, 0);
    }
  };

  return (
    <ul>
      {items.map((item, index) => (
        <li key={item.id}>
          {item.name}
          <button
            ref={(el) => itemRefs.current[item.id] = el}
            onClick={() => handleDelete(item.id, index)}
          >
            Delete
          </button>
        </li>
      ))}
    </ul>
  );
}
```

### Forwarding Refs for Parent Control
```jsx
import { forwardRef } from 'react';

const CustomInput = forwardRef((props, ref) => {
  return (
    <div className="custom-input-wrapper">
      <input ref={ref} {...props} />
    </div>
  );
});

// Parent can now control focus
function Parent() {
  const inputRef = useRef(null);

  const focusInput = () => {
    inputRef.current?.focus();
  };

  return (
    <>
      <CustomInput ref={inputRef} />
      <button onClick={focusInput}>Focus Input</button>
    </>
  );
}
```

## Roving Tabindex Pattern (Composite Widgets)

### Implementation for Tab List
```jsx
function Tabs({ tabs }) {
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [focusedIndex, setFocusedIndex] = useState(0);
  const tabRefs = useRef([]);

  const handleKeyDown = (e, index) => {
    let nextIndex;

    switch (e.key) {
      case 'ArrowRight':
      case 'ArrowDown':
        e.preventDefault();
        nextIndex = (index + 1) % tabs.length;
        break;
      case 'ArrowLeft':
      case 'ArrowUp':
        e.preventDefault();
        nextIndex = (index - 1 + tabs.length) % tabs.length;
        break;
      case 'Home':
        e.preventDefault();
        nextIndex = 0;
        break;
      case 'End':
        e.preventDefault();
        nextIndex = tabs.length - 1;
        break;
      default:
        return;
    }

    setFocusedIndex(nextIndex);
  };

  useEffect(() => {
    tabRefs.current[focusedIndex]?.focus();
  }, [focusedIndex]);

  return (
    <div>
      <div role="tablist">
        {tabs.map((tab, index) => (
          <button
            key={tab.id}
            ref={(el) => tabRefs.current[index] = el}
            role="tab"
            aria-selected={index === selectedIndex}
            aria-controls={`panel-${tab.id}`}
            tabIndex={index === focusedIndex ? 0 : -1}
            onClick={() => {
              setSelectedIndex(index);
              setFocusedIndex(index);
            }}
            onKeyDown={(e) => handleKeyDown(e, index)}
          >
            {tab.label}
          </button>
        ))}
      </div>
      {tabs.map((tab, index) => (
        <div
          key={tab.id}
          id={`panel-${tab.id}`}
          role="tabpanel"
          hidden={index !== selectedIndex}
        >
          {tab.content}
        </div>
      ))}
    </div>
  );
}
```

## Testing Conventions

### Prefer Accessible Queries
```jsx
import { render, screen } from '@testing-library/react';

// ✅ ALWAYS - Query by role (most accessible)
const button = screen.getByRole('button', { name: 'Submit' });
const heading = screen.getByRole('heading', { name: 'Page Title' });
const textbox = screen.getByRole('textbox', { name: 'Email' });

// ✅ ALWAYS - Query by label (for form controls)
const input = screen.getByLabelText('Email address');

// ✅ GOOD - Query by text content
const element = screen.getByText('Welcome message');

// ⚠️ ACCEPTABLE - Query by test ID (last resort)
const element = screen.getByTestId('custom-component');

// ❌ AVOID - Query by class or element type
const element = container.querySelector('.button');
```

### Query Priority Order
1. **`getByRole`** - Matches how assistive technology sees elements
2. **`getByLabelText`** - For form controls with labels
3. **`getByPlaceholderText`** - For inputs (if no label)
4. **`getByText`** - For non-interactive content
5. **`getByDisplayValue`** - For form elements with values
6. **`getByAltText`** - For images
7. **`getByTitle`** - For elements with title attribute
8. **`getByTestId`** - Last resort when nothing else works

### Testing Keyboard Interaction
```jsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

test('button is keyboard accessible', async () => {
  const user = userEvent.setup();
  const handleClick = jest.fn();
  
  render(<button onClick={handleClick}>Submit</button>);
  
  const button = screen.getByRole('button', { name: 'Submit' });
  
  // Tab to button
  await user.tab();
  expect(button).toHaveFocus();
  
  // Activate with Enter
  await user.keyboard('{Enter}');
  expect(handleClick).toHaveBeenCalledTimes(1);
  
  // Activate with Space
  await user.keyboard(' ');
  expect(handleClick).toHaveBeenCalledTimes(2);
});
```

### Testing Focus Management
```jsx
test('modal traps focus and restores on close', async () => {
  const user = userEvent.setup();
  
  render(
    <>
      <button>Trigger</button>
      <Modal isOpen={true} onClose={handleClose}>
        <button>Inside Modal</button>
      </Modal>
    </>
  );
  
  const trigger = screen.getByRole('button', { name: 'Trigger' });
  const modalButton = screen.getByRole('button', { name: 'Inside Modal' });
  
  // Focus should be inside modal
  expect(modalButton).toHaveFocus();
  
  // Close modal
  await user.keyboard('{Escape}');
  
  // Focus should return to trigger
  expect(trigger).toHaveFocus();
});
```

## Component Library Recommendations

### ShadCN/Radix UI (Repository Standard)
```jsx
// ✅ PREFERRED - Use ShadCN/Radix components
import { Dialog, DialogContent, DialogTitle } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem } from '@/components/ui/select';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';

// These handle:
// - Keyboard navigation automatically
// - Focus management automatically
// - ARIA attributes automatically
// - Screen reader announcements automatically

function Component() {
  return (
    <Dialog>
      <DialogContent>
        <DialogTitle>Dialog Title</DialogTitle>
        {/* Content automatically accessible */}
      </DialogContent>
    </Dialog>
  );
}
```

### When to Build Custom
Only build custom components when:
1. ShadCN/Radix doesn't have the pattern
2. Design requirements cannot be met with styling
3. Specific behavior not supported by library

When building custom:
- Follow W3C ARIA Authoring Practices Guide patterns
- Use `accessible-component-design` skill for guidance
- Test thoroughly with keyboard and screen readers

## Common React Accessibility Patterns

### Skip to Main Content
```jsx
function Layout({ children }) {
  return (
    <>
      <a href="#main-content" className="sr-only focus:not-sr-only">
        Skip to main content
      </a>
      <header>
        <nav>...</nav>
      </header>
      <main id="main-content" tabIndex={-1}>
        {children}
      </main>
    </>
  );
}
```

### Screen Reader Only Text
```jsx
// Utility class (Tailwind)
<button>
  <TrashIcon />
  <span className="sr-only">Delete item</span>
</button>

// Or custom CSS
<style>
  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border-width: 0;
  }
</style>
```

### Live Regions for Dynamic Content
```jsx
function SearchResults({ results, isLoading }) {
  return (
    <div>
      <div aria-live="polite" aria-atomic="true" className="sr-only">
        {isLoading ? 'Loading results...' : `${results.length} results found`}
      </div>
      <ul>
        {results.map(result => <li key={result.id}>{result.name}</li>)}
      </ul>
    </div>
  );
}
```

### Error Announcements
```jsx
function Form() {
  const [error, setError] = useState('');

  return (
    <form>
      <label htmlFor="email">Email</label>
      <input
        id="email"
        type="email"
        aria-invalid={!!error}
        aria-describedby={error ? 'email-error' : undefined}
      />
      {error && (
        <div id="email-error" role="alert">
          {error}
        </div>
      )}
    </form>
  );
}
```

## Integration with Existing Patterns

### TypeScript Types for Accessibility
```tsx
interface AccessibleButtonProps {
  children: React.ReactNode;
  onClick: () => void;
  'aria-label'?: string;
  'aria-labelledby'?: string;
  'aria-describedby'?: string;
  disabled?: boolean;
}

const AccessibleButton: React.FC<AccessibleButtonProps> = ({
  children,
  onClick,
  'aria-label': ariaLabel,
  'aria-labelledby': ariaLabelledby,
  'aria-describedby': ariaDescribedby,
  disabled = false,
}) => {
  return (
    <button
      onClick={onClick}
      aria-label={ariaLabel}
      aria-labelledby={ariaLabelledby}
      aria-describedby={ariaDescribedby}
      disabled={disabled}
    >
      {children}
    </button>
  );
};
```

### Vite/React 18 Considerations
```jsx
// React 18 automatic batching helps with focus management
// Multiple state updates batch together, reducing focus jumps

function Component() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const resultRef = useRef(null);

  const fetchData = async () => {
    setLoading(true);
    const result = await api.fetch();
    // These batch together in React 18
    setData(result);
    setLoading(false);
    // Focus management happens after batch
    resultRef.current?.focus();
  };

  return (
    <div ref={resultRef} tabIndex={-1}>
      {loading ? 'Loading...' : data}
    </div>
  );
}
```

## Resources

- **React Accessibility Docs**: https://react.dev/learn/accessibility
- **Testing Library Queries**: https://testing-library.com/docs/queries/about
- **ShadCN/Radix UI**: https://ui.shadcn.com/
- **ARIA Authoring Practices**: https://www.w3.org/WAI/ARIA/apg/
