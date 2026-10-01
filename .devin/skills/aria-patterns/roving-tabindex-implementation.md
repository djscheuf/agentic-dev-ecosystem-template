# Roving Tabindex Implementation Guide

Complete guide to implementing the roving tabindex pattern for composite widgets.

## What is Roving Tabindex?

**Problem:** Composite widgets (tabs, menus, toolbars) contain multiple interactive elements. If all elements are in the tab sequence, users must Tab through each one.

**Solution:** Only ONE element in the composite has `tabIndex={0}` (in tab sequence). Others have `tabIndex={-1}` (not in tab sequence). Arrow keys navigate within the composite.

**Result:** Tab enters/exits the composite. Arrow keys navigate inside.

## When to Use Roving Tabindex

Use for composite widgets where arrow keys navigate between elements:

- Tabs
- Radio groups
- Menus
- Toolbars
- Listboxes
- Tree views
- Grids

**Do NOT use for:**
- Simple lists of links (use standard tab sequence)
- Form fields (use standard tab sequence)
- Independent buttons (use standard tab sequence)

## Algorithm

### 1. State Management

Track which element should be in the tab sequence:

```jsx
const [focusedIndex, setFocusedIndex] = useState(0);
const itemRefs = useRef<(HTMLElement | null)[]>([]);
```

### 2. Render with Dynamic tabIndex

Only the focused element has `tabIndex={0}`:

```jsx
{items.map((item, index) => (
  <button
    key={item.id}
    ref={(el) => itemRefs.current[index] = el}
    role="tab"
    tabIndex={index === focusedIndex ? 0 : -1}
    onKeyDown={(e) => handleKeyDown(e, index)}
  >
    {item.label}
  </button>
))}
```

### 3. Handle Arrow Key Navigation

Update focused index when arrow keys pressed:

```jsx
const handleKeyDown = (e: React.KeyboardEvent, currentIndex: number) => {
  let nextIndex: number | undefined;
  
  switch (e.key) {
    case 'ArrowRight':
    case 'ArrowDown':
      e.preventDefault();
      nextIndex = (currentIndex + 1) % items.length;
      break;
    case 'ArrowLeft':
    case 'ArrowUp':
      e.preventDefault();
      nextIndex = (currentIndex - 1 + items.length) % items.length;
      break;
    case 'Home':
      e.preventDefault();
      nextIndex = 0;
      break;
    case 'End':
      e.preventDefault();
      nextIndex = items.length - 1;
      break;
    default:
      return;
  }
  
  if (nextIndex !== undefined) {
    setFocusedIndex(nextIndex);
  }
};
```

### 4. Focus Element When Index Changes

Move focus to element when focused index changes:

```jsx
useEffect(() => {
  itemRefs.current[focusedIndex]?.focus();
}, [focusedIndex]);
```

## Complete React Implementation

### Horizontal Tabs

```tsx
import { useState, useRef, useEffect } from 'react';

interface Tab {
  id: string;
  label: string;
  content: React.ReactNode;
}

function Tabs({ tabs }: { tabs: Tab[] }) {
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [focusedIndex, setFocusedIndex] = useState(0);
  const tabRefs = useRef<(HTMLButtonElement | null)[]>([]);

  useEffect(() => {
    tabRefs.current[focusedIndex]?.focus();
  }, [focusedIndex]);

  const handleKeyDown = (e: React.KeyboardEvent, index: number) => {
    let nextIndex: number | undefined;

    switch (e.key) {
      case 'ArrowRight':
        e.preventDefault();
        nextIndex = (index + 1) % tabs.length;
        break;
      case 'ArrowLeft':
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

    if (nextIndex !== undefined) {
      setFocusedIndex(nextIndex);
      setSelectedIndex(nextIndex);
    }
  };

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
          role="tabpanel"
          id={`panel-${tab.id}`}
          hidden={index !== selectedIndex}
        >
          {tab.content}
        </div>
      ))}
    </div>
  );
}
```

### Vertical Menu

```tsx
import { useState, useRef, useEffect } from 'react';

interface MenuItem {
  id: string;
  label: string;
  onSelect: () => void;
}

function Menu({ items }: { items: MenuItem[] }) {
  const [focusedIndex, setFocusedIndex] = useState(0);
  const itemRefs = useRef<(HTMLDivElement | null)[]>([]);

  useEffect(() => {
    itemRefs.current[focusedIndex]?.focus();
  }, [focusedIndex]);

  const handleKeyDown = (e: React.KeyboardEvent, index: number) => {
    let nextIndex: number | undefined;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        nextIndex = (index + 1) % items.length;
        break;
      case 'ArrowUp':
        e.preventDefault();
        nextIndex = (index - 1 + items.length) % items.length;
        break;
      case 'Home':
        e.preventDefault();
        nextIndex = 0;
        break;
      case 'End':
        e.preventDefault();
        nextIndex = items.length - 1;
        break;
      case 'Enter':
      case ' ':
        e.preventDefault();
        items[index].onSelect();
        return;
      default:
        return;
    }

    if (nextIndex !== undefined) {
      setFocusedIndex(nextIndex);
    }
  };

  return (
    <div role="menu">
      {items.map((item, index) => (
        <div
          key={item.id}
          ref={(el) => itemRefs.current[index] = el}
          role="menuitem"
          tabIndex={index === focusedIndex ? 0 : -1}
          onClick={item.onSelect}
          onKeyDown={(e) => handleKeyDown(e, index)}
        >
          {item.label}
        </div>
      ))}
    </div>
  );
}
```

### Radio Group

```tsx
import { useState, useRef, useEffect } from 'react';

interface RadioOption {
  id: string;
  label: string;
  value: string;
}

function RadioGroup({ 
  options, 
  value, 
  onChange,
  label 
}: { 
  options: RadioOption[];
  value: string;
  onChange: (value: string) => void;
  label: string;
}) {
  const selectedIndex = options.findIndex(opt => opt.value === value);
  const [focusedIndex, setFocusedIndex] = useState(selectedIndex !== -1 ? selectedIndex : 0);
  const optionRefs = useRef<(HTMLDivElement | null)[]>([]);

  useEffect(() => {
    optionRefs.current[focusedIndex]?.focus();
  }, [focusedIndex]);

  const handleKeyDown = (e: React.KeyboardEvent, index: number) => {
    let nextIndex: number | undefined;

    switch (e.key) {
      case 'ArrowDown':
      case 'ArrowRight':
        e.preventDefault();
        nextIndex = (index + 1) % options.length;
        break;
      case 'ArrowUp':
      case 'ArrowLeft':
        e.preventDefault();
        nextIndex = (index - 1 + options.length) % options.length;
        break;
      case ' ':
        e.preventDefault();
        onChange(options[index].value);
        return;
      default:
        return;
    }

    if (nextIndex !== undefined) {
      setFocusedIndex(nextIndex);
      onChange(options[nextIndex].value);
    }
  };

  return (
    <div role="radiogroup" aria-label={label}>
      {options.map((option, index) => (
        <div
          key={option.id}
          ref={(el) => optionRefs.current[index] = el}
          role="radio"
          aria-checked={option.value === value}
          tabIndex={index === focusedIndex ? 0 : -1}
          onClick={() => {
            onChange(option.value);
            setFocusedIndex(index);
          }}
          onKeyDown={(e) => handleKeyDown(e, index)}
        >
          {option.label}
        </div>
      ))}
    </div>
  );
}
```

### Toolbar

```tsx
import { useState, useRef, useEffect } from 'react';

interface ToolbarButton {
  id: string;
  label: string;
  icon: React.ReactNode;
  onClick: () => void;
}

function Toolbar({ buttons }: { buttons: ToolbarButton[] }) {
  const [focusedIndex, setFocusedIndex] = useState(0);
  const buttonRefs = useRef<(HTMLButtonElement | null)[]>([]);

  useEffect(() => {
    buttonRefs.current[focusedIndex]?.focus();
  }, [focusedIndex]);

  const handleKeyDown = (e: React.KeyboardEvent, index: number) => {
    let nextIndex: number | undefined;

    switch (e.key) {
      case 'ArrowRight':
        e.preventDefault();
        nextIndex = (index + 1) % buttons.length;
        break;
      case 'ArrowLeft':
        e.preventDefault();
        nextIndex = (index - 1 + buttons.length) % buttons.length;
        break;
      case 'Home':
        e.preventDefault();
        nextIndex = 0;
        break;
      case 'End':
        e.preventDefault();
        nextIndex = buttons.length - 1;
        break;
      default:
        return;
    }

    if (nextIndex !== undefined) {
      setFocusedIndex(nextIndex);
    }
  };

  return (
    <div role="toolbar" aria-label="Text formatting">
      {buttons.map((button, index) => (
        <button
          key={button.id}
          ref={(el) => buttonRefs.current[index] = el}
          aria-label={button.label}
          tabIndex={index === focusedIndex ? 0 : -1}
          onClick={button.onClick}
          onKeyDown={(e) => handleKeyDown(e, index)}
        >
          {button.icon}
        </button>
      ))}
    </div>
  );
}
```

## Advanced Patterns

### Separate Focus and Selection

Some patterns (like tabs) separate focus from selection:

```tsx
const [selectedIndex, setSelectedIndex] = useState(0);
const [focusedIndex, setFocusedIndex] = useState(0);

// Arrow keys move focus only
const handleKeyDown = (e: React.KeyboardEvent, index: number) => {
  if (e.key === 'ArrowRight') {
    e.preventDefault();
    setFocusedIndex((index + 1) % items.length);
  }
  // Enter/Space selects focused item
  else if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault();
    setSelectedIndex(focusedIndex);
  }
};
```

### Automatic Selection on Focus

Other patterns (like radio groups) select automatically when focused:

```tsx
const handleKeyDown = (e: React.KeyboardEvent, index: number) => {
  let nextIndex: number | undefined;
  
  if (e.key === 'ArrowRight') {
    nextIndex = (index + 1) % items.length;
  }
  
  if (nextIndex !== undefined) {
    setFocusedIndex(nextIndex);
    setSelectedIndex(nextIndex); // Auto-select
  }
};
```

### Type-Ahead Search

Allow users to jump to items by typing:

```tsx
const [searchQuery, setSearchQuery] = useState('');
const [searchTimeout, setSearchTimeout] = useState<NodeJS.Timeout | null>(null);

const handleTypeAhead = (key: string) => {
  if (key.length !== 1) return;

  if (searchTimeout) {
    clearTimeout(searchTimeout);
  }

  const newQuery = searchQuery + key.toLowerCase();
  setSearchQuery(newQuery);

  const matchIndex = items.findIndex(item =>
    item.label.toLowerCase().startsWith(newQuery)
  );

  if (matchIndex !== -1) {
    setFocusedIndex(matchIndex);
  }

  setSearchTimeout(
    setTimeout(() => {
      setSearchQuery('');
    }, 500)
  );
};

const handleKeyDown = (e: React.KeyboardEvent, index: number) => {
  // Handle arrow keys...
  
  // Handle type-ahead
  if (e.key.length === 1 && !e.ctrlKey && !e.altKey && !e.metaKey) {
    handleTypeAhead(e.key);
  }
};
```

## Common Mistakes

### All Elements in Tab Sequence

```tsx
// ❌ WRONG - User must Tab through every item
{items.map((item) => (
  <button role="tab" tabIndex={0}>
    {item.label}
  </button>
))}

// ✅ CORRECT - Only focused item in tab sequence
{items.map((item, index) => (
  <button role="tab" tabIndex={index === focusedIndex ? 0 : -1}>
    {item.label}
  </button>
))}
```

### Not Preventing Default on Arrow Keys

```tsx
// ❌ WRONG - Page scrolls when using arrow keys
const handleKeyDown = (e: React.KeyboardEvent) => {
  if (e.key === 'ArrowDown') {
    moveToNext();
  }
};

// ✅ CORRECT - Prevent default behavior
const handleKeyDown = (e: React.KeyboardEvent) => {
  if (e.key === 'ArrowDown') {
    e.preventDefault();
    moveToNext();
  }
};
```

### Not Moving Focus When Index Changes

```tsx
// ❌ WRONG - Focus doesn't move
const handleKeyDown = (e: React.KeyboardEvent) => {
  if (e.key === 'ArrowRight') {
    setFocusedIndex(focusedIndex + 1);
  }
};

// ✅ CORRECT - Focus moves to element
useEffect(() => {
  itemRefs.current[focusedIndex]?.focus();
}, [focusedIndex]);
```

### Using Wrong Arrow Keys for Orientation

```tsx
// ❌ WRONG - Horizontal tabs using vertical arrow keys
case 'ArrowDown':
  nextIndex = (index + 1) % tabs.length;
  break;

// ✅ CORRECT - Horizontal tabs using horizontal arrow keys
case 'ArrowRight':
  nextIndex = (index + 1) % tabs.length;
  break;
```

## Testing Checklist

- [ ] Tab enters composite (focuses first or selected item)
- [ ] Arrow keys navigate between items
- [ ] Only one item has `tabIndex={0}` at a time
- [ ] Focus visible on current item
- [ ] Tab exits composite to next component
- [ ] Shift+Tab exits composite to previous component
- [ ] Home/End keys work (if implemented)
- [ ] Type-ahead works (if implemented)
- [ ] Arrow navigation wraps (last → first, first → last)
- [ ] Screen reader announces current item

## Resources

- **WCAG 2.4.3 Focus Order**: https://www.w3.org/WAI/WCAG22/Understanding/focus-order
- **APG Keyboard Navigation**: https://www.w3.org/WAI/ARIA/apg/practices/keyboard-interface/
- **Managing Focus**: https://www.w3.org/WAI/ARIA/apg/practices/keyboard-interface/#kbd_roving_tabindex
