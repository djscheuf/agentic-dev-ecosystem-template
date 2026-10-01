---
name: ARIA Implementation Patterns
description: Implement ARIA roles, states, and properties for custom widgets when native HTML is insufficient. Includes roving tabindex, composite widget patterns, and complete keyboard behavior. Use only after verifying native HTML cannot meet requirements.
supporting_files:
  - roving-tabindex-implementation.md
  - modal-dialog-pattern.md
  - composite-widgets-guide.md
  - aria-attribute-reference.md
---

# ARIA Implementation Patterns

Systematic procedure for implementing ARIA roles, states, and properties when native HTML is insufficient.

## Pre-Implementation Checklist

**CRITICAL: Complete this checklist before proceeding with ARIA implementation.**

- [ ] Verified native HTML element cannot meet requirements
- [ ] Checked if ShadCN/Radix has this component
- [ ] Identified matching W3C APG pattern
- [ ] Understand complete keyboard behavior required for this pattern
- [ ] Ready to implement full accessibility, not just add role attribute

**If any checkbox is unchecked, reconsider whether ARIA is necessary.**

## Step 1: Verify Native HTML Won't Work

### Question: Can this be accomplished with native HTML?

**Native HTML Elements:**
- Button → `<button>`
- Checkbox → `<input type="checkbox">`
- Radio group → `<input type="radio" name="group">`
- Select → `<select>` and `<option>`
- Link → `<a href>`
- Text input → `<input type="text">`
- Number input → `<input type="number">`
- Range slider → `<input type="range">`
- Date picker → `<input type="date">`
- Details/summary → `<details>` and `<summary>`

### Only Proceed with ARIA If:

1. **Native element doesn't exist**
   - Examples: tabs, tree view, breadcrumb, toolbar
   
2. **Native element lacks required behavior**
   - Example: Combobox with search/autocomplete (native `<select>` doesn't support)
   - Example: Multi-level menu with keyboard shortcuts
   
3. **Design requires visual customization impossible with native elements**
   - Example: Custom-styled select that must match brand guidelines
   - **Note:** Try CSS styling of native elements first

### Decision Tree

```
Can native HTML do this?
├─ Yes → Use native HTML (STOP, do not use ARIA)
└─ No → Does ShadCN/Radix have this?
    ├─ Yes → Use ShadCN/Radix component (STOP, do not use ARIA)
    └─ No → Continue to Step 2
```

## Step 2: Select Appropriate APG Pattern

### Common Patterns Requiring ARIA

Reference `composite-widgets-guide.md` for detailed implementation of each pattern.

**Modal Dialog** - See `modal-dialog-pattern.md`
- Use when: Overlay requiring user interaction before returning to main content
- Key ARIA: `role="dialog"`, `aria-modal="true"`, `aria-labelledby`

**Tabs**
- Use when: Layered sections of content, only one visible at a time
- Key ARIA: `role="tablist"`, `role="tab"`, `role="tabpanel"`, `aria-selected`

**Accordion**
- Use when: Vertically stacked expandable/collapsible sections
- Key ARIA: `aria-expanded`, `aria-controls` on buttons

**Menu/Menubar**
- Use when: Application menu with keyboard shortcuts (NOT site navigation)
- Key ARIA: `role="menu"`, `role="menuitem"`, `aria-haspopup`

**Combobox**
- Use when: Input with autocomplete/search and popup listbox
- Key ARIA: `role="combobox"`, `role="listbox"`, `role="option"`, `aria-expanded`

**Listbox**
- Use when: Selectable list of options (alternative to native select)
- Key ARIA: `role="listbox"`, `role="option"`, `aria-selected`

**Tree View**
- Use when: Hierarchical list with expand/collapse
- Key ARIA: `role="tree"`, `role="treeitem"`, `aria-expanded`

**Grid**
- Use when: Interactive table with cell-by-cell navigation
- Key ARIA: `role="grid"`, `role="row"`, `role="gridcell"`

### Pattern Selection Resources

**Full pattern catalog:** https://www.w3.org/WAI/ARIA/apg/patterns/

**Pattern examples:** See `composite-widgets-guide.md` for detailed implementations

## Step 3: Implement Required ARIA Attributes

### Roles (Define Semantic Meaning)

```jsx
// ✅ Dialog
<div role="dialog" aria-modal="true">
  <h2>Dialog Title</h2>
</div>

// ✅ Tabs
<div role="tablist">
  <button role="tab" aria-selected="true">Tab 1</button>
  <button role="tab" aria-selected="false">Tab 2</button>
</div>
<div role="tabpanel">Content</div>

// ✅ Menu
<div role="menu">
  <div role="menuitem">Cut</div>
  <div role="menuitem">Copy</div>
  <div role="menuitem">Paste</div>
</div>
```

### States (Communicate Dynamic Changes)

**Selection State:**
```jsx
// Tabs, options, menu items
<button role="tab" aria-selected={isSelected}>
  Tab Label
</button>
```

**Expanded State:**
```jsx
// Accordions, disclosure widgets, comboboxes
<button aria-expanded={isExpanded} aria-controls="section-1">
  Section Title
</button>
<div id="section-1" hidden={!isExpanded}>
  Content
</div>
```

**Checked State:**
```jsx
// Custom checkboxes, switches, menu items
<div role="checkbox" aria-checked={isChecked}>
  Option
</div>

<div role="switch" aria-checked={isOn}>
  Toggle
</div>

<div role="menuitemcheckbox" aria-checked={isChecked}>
  Show Toolbar
</div>
```

**Pressed State:**
```jsx
// Toggle buttons
<button aria-pressed={isPressed}>
  Bold
</button>
```

**Hidden State:**
```jsx
// Hide from assistive technology (use carefully)
<div aria-hidden="true">
  Decorative content
</div>
```

**Invalid State:**
```jsx
// Form validation
<input 
  aria-invalid={hasError}
  aria-describedby={hasError ? "error-message" : undefined}
/>
{hasError && <div id="error-message">Error text</div>}
```

### Properties (Provide Additional Semantics)

**Labeling:**
```jsx
// Invisible label
<button aria-label="Close dialog">×</button>

// Reference visible label
<button aria-labelledby="delete-label">
  <span id="delete-label">Delete</span>
</button>

// Description
<input aria-describedby="password-requirements" />
<div id="password-requirements">
  Password must be at least 8 characters
</div>
```

**Relationships:**
```jsx
// Control relationship
<button aria-controls="panel-1" aria-expanded={isExpanded}>
  Toggle Panel
</button>
<div id="panel-1">Panel content</div>

// Ownership (parent-child)
<div role="listbox" aria-owns="option-1 option-2">
  <div role="option" id="option-1">Option 1</div>
  <div role="option" id="option-2">Option 2</div>
</div>
```

**Required:**
```jsx
// Required form field
<input required aria-required="true" />
```

**Live Regions:**
```jsx
// Polite announcement
<div role="status" aria-live="polite">
  {statusMessage}
</div>

// Assertive announcement (interrupts)
<div role="alert" aria-live="assertive">
  {errorMessage}
</div>
```

See `aria-attribute-reference.md` for complete reference of all ARIA attributes.

## Step 4: Implement Complete Keyboard Behavior

### Universal Requirements

**Tab/Shift+Tab:**
- Navigate BETWEEN components
- Only ONE element per composite in tab sequence

**Enter/Space:**
- Activate buttons and controls
- Both keys should work for button-like elements

**Escape:**
- Close dialogs, menus, popups
- Cancel operations

### Pattern-Specific Keyboard Behavior

See `composite-widgets-guide.md` for detailed keyboard requirements for each pattern.

**Tabs:**
- Arrow Left/Right: Navigate tabs
- Home/End: First/last tab
- Tab: Move to panel content

**Menu:**
- Arrow Up/Down: Navigate items
- Enter/Space: Activate item
- Escape: Close menu
- Arrow Right: Open submenu
- Arrow Left: Close submenu

**Listbox:**
- Arrow Up/Down: Navigate options
- Space: Select option (multi-select)
- Enter: Select and close (single-select)
- Home/End: First/last option
- Type-ahead: Jump to option

**Combobox:**
- Arrow Down: Open popup, next option
- Arrow Up: Previous option
- Enter: Select option, close
- Escape: Close popup
- Type: Filter options

**Grid:**
- Arrow keys: Navigate cells
- Home/End: First/last cell in row
- Ctrl+Home/End: First/last cell in grid
- Tab: Exit grid

### Implementation Example

```jsx
const handleKeyDown = (e: React.KeyboardEvent) => {
  switch (e.key) {
    case 'ArrowDown':
      e.preventDefault();
      moveToNext();
      break;
    case 'ArrowUp':
      e.preventDefault();
      moveToPrevious();
      break;
    case 'Home':
      e.preventDefault();
      moveToFirst();
      break;
    case 'End':
      e.preventDefault();
      moveToLast();
      break;
    case 'Enter':
    case ' ':
      e.preventDefault();
      activate();
      break;
    case 'Escape':
      close();
      break;
  }
};
```

## Step 5: Implement Focus Management

### For Composite Widgets: Roving Tabindex

See `roving-tabindex-implementation.md` for complete implementation guide.

**Algorithm Summary:**

1. **Initialize:** One element has `tabIndex={0}`, others have `tabIndex={-1}`
2. **Render:** Dynamic tabIndex based on focused index
3. **Navigate:** Arrow keys update focused index
4. **Focus:** Element receives focus when index changes

**React Implementation:**

```jsx
const [focusedIndex, setFocusedIndex] = useState(0);
const itemRefs = useRef<(HTMLElement | null)[]>([]);

// Render with dynamic tabIndex
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

// Handle arrow keys
const handleKeyDown = (e: React.KeyboardEvent, currentIndex: number) => {
  let nextIndex: number | undefined;
  
  if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
    nextIndex = (currentIndex + 1) % items.length;
  } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
    nextIndex = (currentIndex - 1 + items.length) % items.length;
  }
  
  if (nextIndex !== undefined) {
    e.preventDefault();
    setFocusedIndex(nextIndex);
  }
};

// Focus element when index changes
useEffect(() => {
  itemRefs.current[focusedIndex]?.focus();
}, [focusedIndex]);
```

### For Modals: Focus Trap

See `modal-dialog-pattern.md` for complete implementation.

**Requirements:**
1. Move focus inside modal on open
2. Trap Tab within modal (wrap from last to first)
3. Restore focus to trigger on close
4. Escape closes modal

**React Implementation:**

```jsx
const modalRef = useRef<HTMLDivElement>(null);
const triggerRef = useRef<HTMLElement | null>(null);

// On open: store trigger, move focus inside
useEffect(() => {
  if (isOpen) {
    triggerRef.current = document.activeElement as HTMLElement;
    modalRef.current?.focus();
  } else if (triggerRef.current) {
    triggerRef.current.focus();
  }
}, [isOpen]);

// Trap Tab within modal
const handleKeyDown = (e: React.KeyboardEvent) => {
  if (e.key === 'Escape') {
    closeModal();
    return;
  }
  
  if (e.key === 'Tab') {
    const focusableElements = modalRef.current?.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    
    if (!focusableElements || focusableElements.length === 0) return;
    
    const firstElement = focusableElements[0] as HTMLElement;
    const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;
    
    if (e.shiftKey && document.activeElement === firstElement) {
      e.preventDefault();
      lastElement.focus();
    } else if (!e.shiftKey && document.activeElement === lastElement) {
      e.preventDefault();
      firstElement.focus();
    }
  }
};
```

## Step 6: Test with Screen Readers

### Verification Points

- [ ] Role announced correctly
- [ ] State changes announced (selected, expanded, checked, etc.)
- [ ] Accessible names clear and concise
- [ ] Keyboard navigation works as expected
- [ ] Focus visible throughout interaction
- [ ] No confusion or unexpected behavior

### Screen Readers to Test With

**Windows:**
- NVDA (free): https://www.nvaccess.org/
- JAWS (commercial): https://www.freedomscientific.com/products/software/jaws/

**macOS:**
- VoiceOver (built-in): Cmd+F5 to enable

**Linux:**
- Orca (built-in): Super+Alt+S to enable

### Testing Procedure

1. **Start screen reader**
2. **Navigate to component** (Tab or arrow keys)
3. **Verify role announcement** ("dialog", "tab", "menu item", etc.)
4. **Interact with component** (arrow keys, Enter/Space)
5. **Verify state changes announced** ("selected", "expanded", etc.)
6. **Check accessible names** (clear, concise, match visible text)
7. **Test all keyboard interactions**
8. **Verify no unexpected behavior**

## Common ARIA Patterns Quick Reference

### Modal Dialog

```jsx
<div 
  role="dialog" 
  aria-modal="true"
  aria-labelledby="dialog-title"
>
  <h2 id="dialog-title">Dialog Title</h2>
  <button onClick={closeDialog}>Close</button>
</div>
```

**Keyboard:** Tab cycles within, Escape closes
**Focus:** Move inside on open, restore to trigger on close

### Tabs

```jsx
<div role="tablist">
  <button 
    role="tab" 
    aria-selected="true"
    aria-controls="panel-1"
    tabIndex={0}
  >
    Tab 1
  </button>
  <button 
    role="tab" 
    aria-selected="false"
    aria-controls="panel-2"
    tabIndex={-1}
  >
    Tab 2
  </button>
</div>
<div role="tabpanel" id="panel-1">Content 1</div>
<div role="tabpanel" id="panel-2" hidden>Content 2</div>
```

**Keyboard:** Arrow keys navigate tabs, Tab moves to panel
**Focus:** Roving tabindex (only selected tab in sequence)

### Accordion

```jsx
<button 
  aria-expanded={isExpanded}
  aria-controls="section-1"
>
  Section Title
</button>
<div id="section-1" hidden={!isExpanded}>
  Content
</div>
```

**Keyboard:** Enter/Space toggles
**Focus:** Standard button focus

### Menu

```jsx
<div role="menu">
  <div role="menuitem" tabIndex={0}>Cut</div>
  <div role="menuitem" tabIndex={-1}>Copy</div>
  <div role="menuitem" tabIndex={-1}>Paste</div>
</div>
```

**Keyboard:** Arrow Up/Down navigate, Enter/Space activate, Escape closes
**Focus:** Roving tabindex

### Combobox

```jsx
<input
  type="text"
  role="combobox"
  aria-expanded={isOpen}
  aria-controls="listbox-1"
  aria-autocomplete="list"
/>
<ul id="listbox-1" role="listbox">
  <li role="option" aria-selected="false">Option 1</li>
  <li role="option" aria-selected="true">Option 2</li>
</ul>
```

**Keyboard:** Arrow Down opens/navigates, Enter selects, Escape closes
**Focus:** Input keeps focus, options highlighted

## Pitfalls to Avoid

### Adding Role Without Keyboard Behavior

```jsx
// ❌ NEVER - Role without keyboard support
<div role="button" onClick={handleClick}>
  Click me
</div>

// ✅ ALWAYS - Complete implementation or use native element
<button onClick={handleClick}>Click me</button>

// ✅ IF CUSTOM NEEDED - Role + keyboard + focus
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
  Click me
</div>
```

### Using aria-hidden on Focusable Elements

```jsx
// ❌ NEVER - Creates invisible keyboard trap
<div aria-hidden="true">
  <button>Click me</button>
</div>

// ✅ CORRECT - Hide non-interactive content only
<div aria-hidden="true">
  <img src="decorative.png" />
</div>
```

### Overriding Native Semantics

```jsx
// ❌ NEVER - Breaks native button semantics
<button role="link">Navigate</button>

// ✅ CORRECT - Use appropriate native element
<a href="/page">Navigate</a>
```

### Forgetting to Update States Dynamically

```jsx
// ❌ WRONG - State never updates
<button role="tab" aria-selected="false">
  Tab 1
</button>

// ✅ CORRECT - State updates with interaction
<button role="tab" aria-selected={isSelected}>
  Tab 1
</button>
```

### Not Testing with Actual Screen Readers

Automated tools cannot verify:
- Announcement quality
- Interaction flow
- User experience

**Always test with real screen readers.**

### Implementing Custom Pattern When APG Pattern Exists

```jsx
// ❌ WRONG - Inventing custom tab pattern
<div className="custom-tabs">
  <div className="tab" data-selected="true">Tab 1</div>
</div>

// ✅ CORRECT - Following APG tab pattern
<div role="tablist">
  <button role="tab" aria-selected="true">Tab 1</button>
</div>
```

## Resources

- **W3C APG Patterns**: https://www.w3.org/WAI/ARIA/apg/patterns/
- **Using ARIA**: https://www.w3.org/TR/using-aria/
- **ARIA Specification**: https://www.w3.org/TR/wai-aria-1.2/
- **Roving Tabindex**: `roving-tabindex-implementation.md`
- **Modal Dialog**: `modal-dialog-pattern.md`
- **Composite Widgets**: `composite-widgets-guide.md`
- **ARIA Attributes**: `aria-attribute-reference.md`
