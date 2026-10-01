---
name: Accessible Component Design
description: Design and implement accessible UI components following WCAG 2.2 AA standards with proper keyboard navigation, focus management, and ARIA attributes. Use when creating modals, forms, custom widgets, or any interactive UI components.
supporting_files:
  - apg-patterns-reference.md
  - keyboard-navigation-checklist.md
  - aria-naming-hierarchy.md
  - component-examples/modal-dialog-example.tsx
  - component-examples/accessible-form-example.tsx
  - component-examples/custom-select-example.tsx
  - component-examples/tabs-example.tsx
---

# Accessible Component Design Workflow

Systematic procedure for designing and implementing accessible UI components that meet WCAG 2.2 Level AA standards.

## Overview

This skill guides you through creating accessible components by:
1. Identifying the appropriate pattern
2. Starting with semantic HTML
3. Implementing keyboard navigation
4. Adding ARIA only when necessary
5. Managing focus properly
6. Providing accessible names
7. Testing thoroughly

## Step 1: Identify Component Type

**Goal:** Determine if component matches an established W3C ARIA Authoring Practices Guide (APG) pattern.

### Check APG Patterns First
Reference `apg-patterns-reference.md` for complete catalog of established patterns.

**Common Patterns:**
- **Modal Dialog** - Overlay that requires user interaction before returning to main content
- **Tabs** - Layered sections of content, only one visible at a time
- **Accordion** - Vertically stacked expandable/collapsible sections
- **Menu/Menubar** - Application menu with keyboard shortcuts
- **Combobox** - Input with autocomplete/search and popup listbox
- **Radio Group** - Set of mutually exclusive options
- **Listbox** - Selectable list of options (alternative to native select)
- **Grid** - Interactive table with cell-by-cell navigation
- **Tree View** - Hierarchical list with expand/collapse

### Decision Tree
```
Does W3C APG have a pattern for this component?
├─ Yes → Follow APG pattern exactly (see apg-patterns-reference.md)
└─ No → Can this be simplified to use an existing pattern?
    ├─ Yes → Simplify design, use existing pattern
    └─ No → Design custom pattern, test extensively
```

### ShadCN/Radix Check
**Before implementing custom component, check if ShadCN/Radix has it:**
- Dialog/Modal
- Select/Combobox
- Tabs
- Accordion
- Dropdown Menu
- Popover
- Tooltip

If available, use ShadCN/Radix component (handles accessibility automatically).

## Step 2: Start with Semantic HTML

**Goal:** Use native HTML elements that provide built-in accessibility.

### Native Elements Provide Free Accessibility
```jsx
// ✅ Native button
<button onClick={handleClick}>Submit</button>
// Gets: keyboard access, role, focus, activation (Enter/Space)

// ✅ Native checkbox
<input type="checkbox" checked={value} onChange={handleChange} />
// Gets: keyboard access, role, state, activation (Space)

// ✅ Native select
<select value={selected} onChange={handleChange}>
  <option value="1">Option 1</option>
</select>
// Gets: keyboard access, role, arrow key navigation, activation
```

### Semantic HTML Checklist
- [ ] Can this use `<button>` instead of `<div onClick>`?
- [ ] Can this use `<input>` instead of custom control?
- [ ] Can this use `<select>` instead of custom dropdown?
- [ ] Can this use `<a href>` instead of `<div onClick>` for navigation?
- [ ] Can this use `<details>`/`<summary>` for disclosure?

### When Native HTML is Insufficient
Only proceed with custom implementation if:
1. Native element doesn't exist (e.g., tabs, tree view)
2. Native element lacks required behavior (e.g., combobox with search)
3. Design requires visual customization impossible with native elements

**If proceeding with custom implementation, continue to Step 3.**

## Step 3: Implement Keyboard Navigation

**Goal:** Ensure all functionality is accessible via keyboard alone.

Reference `keyboard-navigation-checklist.md` for complete requirements.

### Universal Keyboard Requirements

#### Tab/Shift+Tab (Between Components)
```jsx
// ✅ Only ONE element per composite in tab sequence
<div role="tablist">
  <button role="tab" tabIndex={0}>Tab 1</button>      {/* In tab sequence */}
  <button role="tab" tabIndex={-1}>Tab 2</button>     {/* Not in tab sequence */}
  <button role="tab" tabIndex={-1}>Tab 3</button>     {/* Not in tab sequence */}
</div>

// ❌ All elements in tab sequence (wrong)
<div role="tablist">
  <button role="tab" tabIndex={0}>Tab 1</button>
  <button role="tab" tabIndex={0}>Tab 2</button>
  <button role="tab" tabIndex={0}>Tab 3</button>
</div>
```

#### Arrow Keys (Within Composites)
```jsx
// ✅ Arrow keys navigate within composite
const handleKeyDown = (e) => {
  if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
    moveToNextItem();
  } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
    moveToPreviousItem();
  }
};
```

#### Enter/Space (Activation)
```jsx
// ✅ Both Enter and Space should activate buttons
const handleKeyDown = (e) => {
  if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault();
    handleActivation();
  }
};
```

#### Escape (Cancel/Close)
```jsx
// ✅ Escape closes dialogs and menus
const handleKeyDown = (e) => {
  if (e.key === 'Escape') {
    closeDialog();
  }
};
```

### Pattern-Specific Keyboard Behavior

**Modal Dialog:**
- Tab/Shift+Tab: Cycle through focusable elements inside modal
- Escape: Close modal

**Tabs:**
- Arrow Left/Right: Navigate between tabs
- Home/End: Jump to first/last tab
- Tab: Move from tab to panel content

**Menu:**
- Arrow Up/Down: Navigate menu items
- Enter/Space: Activate menu item
- Escape: Close menu

**Listbox:**
- Arrow Up/Down: Navigate options
- Space: Select option
- Home/End: Jump to first/last option

See `keyboard-navigation-checklist.md` for complete pattern-specific requirements.

## Step 4: Add ARIA Only If Native HTML Insufficient

**Goal:** Use ARIA to communicate semantics that native HTML cannot provide.

### Five Rules of ARIA (Review Before Adding)
1. Use native HTML first
2. Don't override native semantics
3. All interactive ARIA controls must be keyboard accessible
4. Never hide focusable elements with aria-hidden="true"
5. No ARIA is better than bad ARIA

### When to Add ARIA

#### Add Role When Native Element Doesn't Exist
```jsx
// ✅ Tabs require ARIA (no native HTML equivalent)
<div role="tablist">
  <button role="tab" aria-selected="true">Tab 1</button>
</div>

// ✅ Dialog requires ARIA
<div role="dialog" aria-modal="true">
  <h2>Dialog Title</h2>
</div>
```

#### Add States to Communicate Dynamic Changes
```jsx
// ✅ Communicate selection state
<button role="tab" aria-selected={isSelected}>Tab</button>

// ✅ Communicate expanded state
<button aria-expanded={isExpanded}>Section</button>

// ✅ Communicate checked state (if not using native checkbox)
<div role="checkbox" aria-checked={isChecked}>Option</div>
```

#### Add Properties for Relationships
```jsx
// ✅ Connect tab to its panel
<button role="tab" aria-controls="panel-1">Tab 1</button>
<div role="tabpanel" id="panel-1">Content</div>

// ✅ Connect input to error message
<input aria-describedby="error-message" />
<div id="error-message">Error text</div>
```

### A Role is a Promise

**Critical:** Adding a role means you MUST implement the complete keyboard behavior for that role.

```jsx
// ❌ NEVER - Role without keyboard behavior
<div role="button" onClick={handleClick}>Click</div>

// ✅ ALWAYS - Complete implementation
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
  Click
</div>

// ✅ BETTER - Use native element
<button onClick={handleClick}>Click</button>
```

## Step 5: Implement Focus Management

**Goal:** Ensure focus moves logically and is always visible.

### React Focus Management Pattern
```jsx
import { useRef, useEffect } from 'react';

const elementRef = useRef(null);

useEffect(() => {
  if (shouldFocus) {
    elementRef.current?.focus();
  }
}, [shouldFocus]);

return <button ref={elementRef}>Button</button>;
```

### For Composite Widgets: Roving Tabindex

**Pattern:** Only one element in composite has `tabIndex={0}`, others have `tabIndex={-1}`. Arrow keys move focus and update tabindex.

```jsx
const [focusedIndex, setFocusedIndex] = useState(0);
const itemRefs = useRef([]);

const handleKeyDown = (e, index) => {
  let nextIndex;
  
  if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
    nextIndex = (index + 1) % items.length;
  } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
    nextIndex = (index - 1 + items.length) % items.length;
  }
  
  if (nextIndex !== undefined) {
    e.preventDefault();
    setFocusedIndex(nextIndex);
  }
};

useEffect(() => {
  itemRefs.current[focusedIndex]?.focus();
}, [focusedIndex]);

return items.map((item, index) => (
  <button
    key={item.id}
    ref={(el) => itemRefs.current[index] = el}
    tabIndex={index === focusedIndex ? 0 : -1}
    onKeyDown={(e) => handleKeyDown(e, index)}
  >
    {item.label}
  </button>
));
```

### For Modals: Focus Trap

**Pattern:** Move focus inside modal on open, trap Tab within modal, restore focus on close.

```jsx
const modalRef = useRef(null);
const triggerRef = useRef(null);

useEffect(() => {
  if (isOpen) {
    // Store trigger element
    triggerRef.current = document.activeElement;
    // Move focus inside modal
    modalRef.current?.focus();
  } else if (triggerRef.current) {
    // Restore focus to trigger
    triggerRef.current.focus();
  }
}, [isOpen]);

const handleKeyDown = (e) => {
  if (e.key === 'Escape') {
    closeModal();
    return;
  }
  
  if (e.key === 'Tab') {
    const focusableElements = modalRef.current.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];
    
    if (e.shiftKey && document.activeElement === firstElement) {
      e.preventDefault();
      lastElement.focus();
    } else if (!e.shiftKey && document.activeElement === lastElement) {
      e.preventDefault();
      firstElement.focus();
    }
  }
};

return (
  <div
    ref={modalRef}
    role="dialog"
    aria-modal="true"
    tabIndex={-1}
    onKeyDown={handleKeyDown}
  >
    {children}
  </div>
);
```

### For Deletions: Move Focus Logically

```jsx
const handleDelete = (id, index) => {
  deleteItem(id);
  
  // Move focus to next item, or previous if last item
  const nextIndex = index < items.length - 1 ? index : index - 1;
  const nextItem = items[nextIndex];
  
  if (nextItem) {
    setTimeout(() => {
      itemRefs.current[nextItem.id]?.focus();
    }, 0);
  }
};
```

## Step 6: Provide Accessible Names

**Goal:** Ensure all interactive elements have clear, concise accessible names.

Reference `aria-naming-hierarchy.md` for complete guidance.

### Accessible Naming Priority

1. **`aria-labelledby`** (highest precedence) - References visible text by ID
2. **`aria-label`** - Invisible label when no visible text appropriate
3. **Native HTML** - `<label>`, `<caption>`, `<legend>`, `<figcaption>`
4. **Child content** - Text content of element
5. **Fallback** - `title`, `placeholder` (avoid as primary label)

### Form Controls: Always Use Labels
```jsx
// ✅ ALWAYS - Explicit label association
<label htmlFor="email">Email Address</label>
<input type="email" id="email" />

// ✅ ALWAYS - Implicit label association
<label>
  Email Address
  <input type="email" />
</label>

// ❌ NEVER - Placeholder as only label
<input type="email" placeholder="Email Address" />
```

### Icon Buttons: Provide Text Alternative
```jsx
// ✅ aria-label for icon-only buttons
<button aria-label="Delete item" onClick={handleDelete}>
  <TrashIcon />
</button>

// ✅ aria-labelledby referencing visible text
<button aria-labelledby="delete-label" onClick={handleDelete}>
  <TrashIcon />
  <span id="delete-label">Delete</span>
</button>

// ✅ Screen reader only text
<button onClick={handleDelete}>
  <TrashIcon />
  <span className="sr-only">Delete item</span>
</button>
```

### Complex Widgets: Use aria-labelledby
```jsx
// ✅ Dialog labeled by title
<div role="dialog" aria-labelledby="dialog-title">
  <h2 id="dialog-title">Confirm Deletion</h2>
  <p>Are you sure?</p>
</div>

// ✅ Tab panel labeled by tab
<button 
  role="tab" 
  id="tab-1"
  aria-controls="panel-1"
>
  Settings
</button>
<div 
  role="tabpanel" 
  id="panel-1"
  aria-labelledby="tab-1"
>
  Settings content
</div>
```

## Step 7: Test Implementation

**Goal:** Verify component is fully accessible before considering complete.

### Automated Testing
```jsx
import { render, screen } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';

expect.extend(toHaveNoViolations);

test('component has no accessibility violations', async () => {
  const { container } = render(<Component />);
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
```

### Manual Keyboard Testing
**Disconnect mouse or commit to not using it.**

- [ ] Tab through entire component
- [ ] All interactive elements reachable
- [ ] Tab order matches visual/reading order
- [ ] Focus indicators clearly visible
- [ ] Arrow keys work in composites
- [ ] Enter/Space activates controls
- [ ] Escape closes modals/menus
- [ ] No keyboard traps

### Screen Reader Testing
**Test with at least one screen reader:**
- Windows: NVDA (free) or JAWS
- macOS: VoiceOver (built-in)
- Linux: Orca (built-in)

**Verification:**
- [ ] All elements have accessible names
- [ ] Roles announced correctly
- [ ] States announced (selected, expanded, etc.)
- [ ] Reading order matches visual order
- [ ] Form labels announced with inputs
- [ ] Error messages announced

### React Testing Library Queries
```jsx
// ✅ Use accessible queries to verify structure
const button = screen.getByRole('button', { name: 'Submit' });
const heading = screen.getByRole('heading', { name: 'Page Title' });
const input = screen.getByLabelText('Email address');

// If query fails, component likely has accessibility issue
```

## Component-Specific Guidance

### Modal Dialog
See `component-examples/modal-dialog-example.tsx` for complete implementation.

**Requirements:**
- Container: `role="dialog"`, `aria-modal="true"`
- Label: `aria-labelledby` referencing title
- Focus: Move inside on open, trap within, restore on close
- Keyboard: Tab cycles within, Escape closes
- Backdrop: Click closes (optional)

### Form
See `component-examples/accessible-form-example.tsx` for complete implementation.

**Requirements:**
- Labels: `<label htmlFor="id">` for every input
- Required: `required` attribute + `aria-required="true"` + visible indicator
- Validation: `aria-describedby` for error messages, `aria-invalid` when error
- Error messages: Clear, specific, associated with field
- Submit: Disabled during submission, focus on first error or success message

### Custom Select/Combobox
See `component-examples/custom-select-example.tsx` for complete implementation.

**Requirements:**
- Consider using native `<select>` first
- If custom needed: Follow APG Combobox or Listbox pattern
- Implement complete keyboard support (arrow keys, type-ahead, Home/End)
- Use roving tabindex for options
- Announce selection changes to screen readers

### Tabs
See `component-examples/tabs-example.tsx` for complete implementation.

**Requirements:**
- Tablist: `role="tablist"`
- Tabs: `role="tab"`, `aria-selected`, `aria-controls`
- Panels: `role="tabpanel"`, `aria-labelledby`
- Keyboard: Arrow keys navigate tabs, Tab moves to panel
- Roving tabindex: Only selected tab in tab sequence

## Common Pitfalls

### Adding ARIA Without Keyboard Behavior
```jsx
// ❌ NEVER - Role without keyboard support
<div role="button" onClick={handleClick}>Click</div>

// ✅ ALWAYS - Complete implementation or use native element
<button onClick={handleClick}>Click</button>
```

### Breaking Semantic HTML with Wrapper Divs
```jsx
// ❌ NEVER - Breaks list semantics
<ul>
  {items.map(item => (
    <div key={item.id}>
      <li>{item.name}</li>
    </div>
  ))}
</ul>

// ✅ ALWAYS - Use Fragment to preserve semantics
<ul>
  {items.map(item => (
    <Fragment key={item.id}>
      <li>{item.name}</li>
    </Fragment>
  ))}
</ul>
```

### Forgetting to Restore Focus After Modal Closes
```jsx
// ❌ NEVER - Focus lost when modal closes
const closeModal = () => {
  setIsOpen(false);
};

// ✅ ALWAYS - Restore focus to trigger
const closeModal = () => {
  setIsOpen(false);
  triggerRef.current?.focus();
};
```

### Not Testing with Actual Screen Readers
Automated tools catch ~30% of accessibility issues. Manual testing is essential.

### Removing Focus Indicators
```css
/* ❌ NEVER - Removes focus indicators */
button:focus {
  outline: none;
}

/* ✅ ALWAYS - Provide visible alternative */
button:focus-visible {
  outline: 2px solid blue;
  outline-offset: 2px;
}
```

### Using Placeholder as Only Form Label
```jsx
// ❌ NEVER - Placeholder disappears when typing
<input type="text" placeholder="Email address" />

// ✅ ALWAYS - Persistent label
<label htmlFor="email">Email address</label>
<input type="text" id="email" />
```

## Decision Tree Summary

```
Start: Need to create component
│
├─ Does ShadCN/Radix have this component?
│  ├─ Yes → Use ShadCN/Radix component
│  └─ No → Continue
│
├─ Can this use native HTML?
│  ├─ Yes → Use native HTML (button, input, select, etc.)
│  └─ No → Continue
│
├─ Does W3C APG have a pattern?
│  ├─ Yes → Follow APG pattern exactly
│  └─ No → Can design be simplified to use existing pattern?
│     ├─ Yes → Simplify design
│     └─ No → Design custom pattern, test extensively
│
└─ Implement:
   1. Keyboard navigation (Tab, arrows, Enter/Space, Escape)
   2. Focus management (roving tabindex or focus trap)
   3. ARIA (only if needed)
   4. Accessible names (labels, aria-label, aria-labelledby)
   5. Test (keyboard, screen reader, automated)
```

## Resources

- **W3C APG Patterns**: `apg-patterns-reference.md`
- **Keyboard Navigation**: `keyboard-navigation-checklist.md`
- **Accessible Naming**: `aria-naming-hierarchy.md`
- **Component Examples**: `component-examples/` directory
- **ARIA Patterns Skill**: For complex ARIA implementations
- **Accessibility Audit Workflow**: `/accessibility-audit` for comprehensive testing
