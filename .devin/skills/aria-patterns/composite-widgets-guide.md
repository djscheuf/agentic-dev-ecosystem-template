# Composite Widgets Implementation Guide

Detailed guide for implementing composite widgets that require roving tabindex and arrow key navigation.

## What is a Composite Widget?

**Composite Widget:** A UI component containing multiple interactive elements that function as a single unit. Users navigate between elements with arrow keys, not Tab.

**Examples:** Tabs, menus, toolbars, radio groups, listboxes, tree views, grids

**Key Characteristic:** Only ONE element in tab sequence at a time (roving tabindex pattern)

## Common Composite Widget Patterns

### Tabs

**Use for:** Layered sections of content, only one visible at a time

**Structure:**
```jsx
<div role="tablist" aria-label="Settings">
  <button role="tab" aria-selected="true" aria-controls="panel-1" tabIndex={0}>
    Profile
  </button>
  <button role="tab" aria-selected="false" aria-controls="panel-2" tabIndex={-1}>
    Security
  </button>
</div>
<div role="tabpanel" id="panel-1" aria-labelledby="tab-1">
  Profile content
</div>
<div role="tabpanel" id="panel-2" aria-labelledby="tab-2" hidden>
  Security content
</div>
```

**Keyboard:**
- Arrow Left/Right: Navigate tabs (horizontal)
- Arrow Up/Down: Navigate tabs (vertical)
- Home: First tab
- End: Last tab
- Tab: Move to panel content

**Focus Management:** Roving tabindex (only selected tab has `tabIndex={0}`)

**See:** `roving-tabindex-implementation.md` for complete implementation

---

### Menu

**Use for:** Application menu with keyboard shortcuts (NOT site navigation)

**Structure:**
```jsx
<div role="menu" aria-label="Edit">
  <div role="menuitem" tabIndex={0}>Cut</div>
  <div role="menuitem" tabIndex={-1}>Copy</div>
  <div role="menuitem" tabIndex={-1}>Paste</div>
  <div role="separator"></div>
  <div role="menuitem" aria-haspopup="true" aria-expanded="false" tabIndex={-1}>
    More Options
  </div>
</div>
```

**Keyboard:**
- Arrow Up/Down: Navigate items
- Home: First item
- End: Last item
- Enter/Space: Activate item
- Escape: Close menu
- Arrow Right: Open submenu
- Arrow Left: Close submenu, return to parent
- Type-ahead: Jump to item starting with typed character

**Focus Management:** Roving tabindex (only focused item has `tabIndex={0}`)

---

### Menubar

**Use for:** Horizontal menu bar (like application menu bar)

**Structure:**
```jsx
<div role="menubar" aria-label="Main menu">
  <div role="menuitem" aria-haspopup="true" tabIndex={0}>File</div>
  <div role="menuitem" aria-haspopup="true" tabIndex={-1}>Edit</div>
  <div role="menuitem" aria-haspopup="true" tabIndex={-1}>View</div>
</div>
```

**Keyboard:**
- Arrow Left/Right: Navigate menubar items
- Arrow Down: Open submenu
- Enter/Space: Open submenu
- Escape: Close submenu

**Focus Management:** Roving tabindex

---

### Radio Group

**Use for:** Mutually exclusive options

**Structure:**
```jsx
<div role="radiogroup" aria-label="Size">
  <div role="radio" aria-checked="true" tabIndex={0}>Small</div>
  <div role="radio" aria-checked="false" tabIndex={-1}>Medium</div>
  <div role="radio" aria-checked="false" tabIndex={-1}>Large</div>
</div>
```

**Keyboard:**
- Arrow Up/Down or Left/Right: Select option (automatically unselects others)
- Space: Select focused option

**Focus Management:** Roving tabindex (only selected option has `tabIndex={0}`)

**Note:** Prefer native `<input type="radio">` when possible

---

### Listbox

**Use for:** Selectable list of options (alternative to native select)

**Structure:**
```jsx
<div role="listbox" aria-label="Countries">
  <div role="option" aria-selected="false" tabIndex={0}>United States</div>
  <div role="option" aria-selected="true" tabIndex={-1}>Canada</div>
  <div role="option" aria-selected="false" tabIndex={-1}>Mexico</div>
</div>
```

**Keyboard:**
- Arrow Up/Down: Navigate options
- Home: First option
- End: Last option
- Space: Toggle selection (multi-select) or select (single-select)
- Enter: Select and close (if in popup)
- Ctrl+A: Select all (multi-select)
- Type-ahead: Jump to option

**Focus Management:** Roving tabindex (only focused option has `tabIndex={0}`)

**Note:** Prefer native `<select>` when possible

---

### Combobox

**Use for:** Input with autocomplete/search and popup listbox

**Structure:**
```jsx
<label htmlFor="country">Country</label>
<input
  type="text"
  id="country"
  role="combobox"
  aria-expanded={isOpen}
  aria-controls="listbox-1"
  aria-autocomplete="list"
  aria-activedescendant={activeOptionId}
/>
<ul id="listbox-1" role="listbox">
  <li role="option" id="option-1">United States</li>
  <li role="option" id="option-2">Canada</li>
</ul>
```

**Keyboard:**
- Arrow Down: Open popup, move to next option
- Arrow Up: Move to previous option
- Home: First option
- End: Last option
- Enter: Select option, close popup
- Escape: Close popup
- Type: Filter options

**Focus Management:** Input keeps focus, `aria-activedescendant` indicates highlighted option

---

### Toolbar

**Use for:** Collection of commonly used function buttons

**Structure:**
```jsx
<div role="toolbar" aria-label="Text formatting">
  <button aria-label="Bold" tabIndex={0}>B</button>
  <button aria-label="Italic" tabIndex={-1}>I</button>
  <button aria-label="Underline" tabIndex={-1}>U</button>
</div>
```

**Keyboard:**
- Arrow Left/Right: Navigate buttons
- Home: First button
- End: Last button
- Enter/Space: Activate button

**Focus Management:** Roving tabindex

---

### Tree View

**Use for:** Hierarchical list with expand/collapse

**Structure:**
```jsx
<div role="tree" aria-label="File explorer">
  <div role="treeitem" aria-expanded="true" aria-level="1" tabIndex={0}>
    Documents
  </div>
  <div role="group">
    <div role="treeitem" aria-level="2" tabIndex={-1}>
      Report.pdf
    </div>
    <div role="treeitem" aria-level="2" tabIndex={-1}>
      Presentation.pptx
    </div>
  </div>
</div>
```

**Keyboard:**
- Arrow Up/Down: Navigate items
- Arrow Right: Expand node, move to first child
- Arrow Left: Collapse node, move to parent
- Home: First visible item
- End: Last visible item
- Enter/Space: Activate item
- Type-ahead: Jump to item

**Focus Management:** Roving tabindex

---

### Grid (Interactive Table)

**Use for:** Interactive table with cell-by-cell navigation

**Structure:**
```jsx
<div role="grid" aria-label="Data table">
  <div role="row">
    <div role="columnheader">Name</div>
    <div role="columnheader">Email</div>
  </div>
  <div role="row">
    <div role="gridcell" tabIndex={0}>John Doe</div>
    <div role="gridcell" tabIndex={-1}>john@example.com</div>
  </div>
</div>
```

**Keyboard:**
- Arrow keys: Navigate cells
- Home: First cell in row
- End: Last cell in row
- Ctrl+Home: First cell in grid
- Ctrl+End: Last cell in grid
- Page Down/Up: Scroll (optional)
- Tab: Exit grid

**Focus Management:** Roving tabindex (only one cell has `tabIndex={0}`)

**Note:** Prefer native `<table>` for static data

---

## Implementation Patterns

### Basic Composite Widget Template

```tsx
import { useState, useRef, useEffect } from 'react';

interface Item {
  id: string;
  label: string;
}

function CompositeWidget({ items }: { items: Item[] }) {
  const [focusedIndex, setFocusedIndex] = useState(0);
  const itemRefs = useRef<(HTMLElement | null)[]>([]);

  // Focus element when index changes
  useEffect(() => {
    itemRefs.current[focusedIndex]?.focus();
  }, [focusedIndex]);

  // Handle arrow key navigation
  const handleKeyDown = (e: React.KeyboardEvent, index: number) => {
    let nextIndex: number | undefined;

    switch (e.key) {
      case 'ArrowDown':
      case 'ArrowRight':
        e.preventDefault();
        nextIndex = (index + 1) % items.length;
        break;
      case 'ArrowUp':
      case 'ArrowLeft':
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
      default:
        return;
    }

    if (nextIndex !== undefined) {
      setFocusedIndex(nextIndex);
    }
  };

  return (
    <div role="[widget-role]">
      {items.map((item, index) => (
        <div
          key={item.id}
          ref={(el) => itemRefs.current[index] = el}
          role="[item-role]"
          tabIndex={index === focusedIndex ? 0 : -1}
          onKeyDown={(e) => handleKeyDown(e, index)}
        >
          {item.label}
        </div>
      ))}
    </div>
  );
}
```

### With Selection State

```tsx
function SelectableWidget({ items }: { items: Item[] }) {
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [focusedIndex, setFocusedIndex] = useState(0);
  const itemRefs = useRef<(HTMLElement | null)[]>([]);

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
      case 'Enter':
      case ' ':
        e.preventDefault();
        setSelectedIndex(index);
        return;
      default:
        return;
    }

    if (nextIndex !== undefined) {
      setFocusedIndex(nextIndex);
    }
  };

  return (
    <div role="listbox">
      {items.map((item, index) => (
        <div
          key={item.id}
          ref={(el) => itemRefs.current[index] = el}
          role="option"
          aria-selected={index === selectedIndex}
          tabIndex={index === focusedIndex ? 0 : -1}
          onKeyDown={(e) => handleKeyDown(e, index)}
          onClick={() => {
            setSelectedIndex(index);
            setFocusedIndex(index);
          }}
        >
          {item.label}
        </div>
      ))}
    </div>
  );
}
```

### With Type-Ahead Search

```tsx
function SearchableWidget({ items }: { items: Item[] }) {
  const [focusedIndex, setFocusedIndex] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchTimeout, setSearchTimeout] = useState<NodeJS.Timeout | null>(null);
  const itemRefs = useRef<(HTMLElement | null)[]>([]);

  useEffect(() => {
    itemRefs.current[focusedIndex]?.focus();
  }, [focusedIndex]);

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

  return (
    <div role="menu">
      {items.map((item, index) => (
        <div
          key={item.id}
          ref={(el) => itemRefs.current[index] = el}
          role="menuitem"
          tabIndex={index === focusedIndex ? 0 : -1}
          onKeyDown={(e) => handleKeyDown(e, index)}
        >
          {item.label}
        </div>
      ))}
    </div>
  );
}
```

## Common Mistakes

### All Elements in Tab Sequence

```tsx
// ❌ WRONG - User must Tab through every item
<div role="tablist">
  <button role="tab" tabIndex={0}>Tab 1</button>
  <button role="tab" tabIndex={0}>Tab 2</button>
  <button role="tab" tabIndex={0}>Tab 3</button>
</div>

// ✅ CORRECT - Only focused item in sequence
<div role="tablist">
  <button role="tab" tabIndex={0}>Tab 1</button>
  <button role="tab" tabIndex={-1}>Tab 2</button>
  <button role="tab" tabIndex={-1}>Tab 3</button>
</div>
```

### Using Wrong Arrow Keys

```tsx
// ❌ WRONG - Horizontal tabs using vertical arrows
case 'ArrowDown':
  nextIndex = (index + 1) % tabs.length;

// ✅ CORRECT - Horizontal tabs using horizontal arrows
case 'ArrowRight':
  nextIndex = (index + 1) % tabs.length;
```

### Missing Home/End Keys

```tsx
// ⚠️ INCOMPLETE - Should include Home/End
const handleKeyDown = (e: React.KeyboardEvent) => {
  if (e.key === 'ArrowDown') {
    moveToNext();
  }
};

// ✅ COMPLETE - Includes Home/End
const handleKeyDown = (e: React.KeyboardEvent) => {
  switch (e.key) {
    case 'ArrowDown':
      moveToNext();
      break;
    case 'Home':
      moveToFirst();
      break;
    case 'End':
      moveToLast();
      break;
  }
};
```

### Not Preventing Default

```tsx
// ❌ WRONG - Page scrolls with arrow keys
const handleKeyDown = (e: React.KeyboardEvent) => {
  if (e.key === 'ArrowDown') {
    moveToNext();
  }
};

// ✅ CORRECT - Prevents page scroll
const handleKeyDown = (e: React.KeyboardEvent) => {
  if (e.key === 'ArrowDown') {
    e.preventDefault();
    moveToNext();
  }
};
```

## Testing Checklist

- [ ] Tab enters composite (focuses first or selected item)
- [ ] Arrow keys navigate between items
- [ ] Only one item has `tabIndex={0}` at a time
- [ ] Focus visible on current item
- [ ] Tab exits composite to next component
- [ ] Shift+Tab exits composite to previous component
- [ ] Home/End keys work
- [ ] Enter/Space activate items (where appropriate)
- [ ] Escape closes menus/popups (where appropriate)
- [ ] Type-ahead works (if implemented)
- [ ] Screen reader announces role and state
- [ ] Arrow navigation wraps (last → first, first → last)

## Resources

- **W3C APG Patterns**: https://www.w3.org/WAI/ARIA/apg/patterns/
- **Keyboard Navigation**: https://www.w3.org/WAI/ARIA/apg/practices/keyboard-interface/
- **Roving Tabindex**: `roving-tabindex-implementation.md`
