# Keyboard Navigation Checklist

Comprehensive checklist for implementing keyboard navigation in accessible components.

## Universal Keyboard Requirements

### Tab Sequence Management

#### Rule: Only ONE Element Per Composite in Tab Sequence
```jsx
// ✅ CORRECT - Only selected tab in tab sequence
<div role="tablist">
  <button role="tab" tabIndex={0}>Tab 1</button>      {/* In sequence */}
  <button role="tab" tabIndex={-1}>Tab 2</button>     {/* Not in sequence */}
  <button role="tab" tabIndex={-1}>Tab 3</button>     {/* Not in sequence */}
</div>

// ❌ WRONG - All tabs in sequence (user must Tab through each)
<div role="tablist">
  <button role="tab" tabIndex={0}>Tab 1</button>
  <button role="tab" tabIndex={0}>Tab 2</button>
  <button role="tab" tabIndex={0}>Tab 3</button>
</div>
```

#### Tab Sequence Checklist
- [ ] Tab moves BETWEEN components (not within composites)
- [ ] Shift+Tab moves backward through tab sequence
- [ ] Tab order matches visual/reading order
- [ ] No elements unexpectedly in tab sequence
- [ ] No elements unexpectedly missing from tab sequence
- [ ] Only one element per composite widget in sequence

### Focus Visibility

#### Requirements
- [ ] Focus indicator visible on all focusable elements
- [ ] Focus indicator has sufficient contrast (3:1 minimum)
- [ ] Focus indicator not obscured by other elements
- [ ] Focus indicator persists while element has focus
- [ ] Custom focus styles meet or exceed browser defaults

#### Implementation
```css
/* ✅ CORRECT - Visible focus indicator */
button:focus-visible {
  outline: 2px solid #0066cc;
  outline-offset: 2px;
}

/* ✅ CORRECT - Custom focus style */
button:focus-visible {
  box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.5);
}

/* ❌ WRONG - Removes focus indicator */
button:focus {
  outline: none;
}
```

### Activation Keys

#### Enter Key
- [ ] Activates buttons
- [ ] Activates links
- [ ] Submits forms
- [ ] Activates custom interactive elements with `role="button"`

#### Space Key
- [ ] Activates buttons
- [ ] Toggles checkboxes
- [ ] Toggles switches
- [ ] Selects radio buttons
- [ ] Activates custom interactive elements with `role="button"`

#### Both Enter and Space
```jsx
// ✅ CORRECT - Both keys activate custom button
const handleKeyDown = (e) => {
  if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault();
    handleActivation();
  }
};
```

### Escape Key

#### Requirements
- [ ] Closes modal dialogs
- [ ] Closes menus and popups
- [ ] Cancels drag operations
- [ ] Clears search/filter inputs (optional)
- [ ] Does NOT prevent browser default (e.g., exit fullscreen)

#### Implementation
```jsx
// ✅ CORRECT - Escape closes dialog
const handleKeyDown = (e) => {
  if (e.key === 'Escape') {
    closeDialog();
  }
};
```

## Roving Tabindex Pattern

### When to Use
Use roving tabindex for composite widgets where arrow keys navigate between elements:
- Tabs
- Radio groups
- Menus
- Toolbars
- Listboxes
- Tree views
- Grids

### Algorithm

#### 1. Initialize State
```jsx
const [focusedIndex, setFocusedIndex] = useState(0);
const itemRefs = useRef([]);
```

#### 2. Render with Dynamic tabIndex
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

#### 3. Handle Arrow Key Navigation
```jsx
const handleKeyDown = (e, currentIndex) => {
  let nextIndex;
  
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

#### 4. Focus Element When Index Changes
```jsx
useEffect(() => {
  itemRefs.current[focusedIndex]?.focus();
}, [focusedIndex]);
```

### Roving Tabindex Checklist
- [ ] Only one element has `tabIndex={0}` at a time
- [ ] All other elements have `tabIndex={-1}`
- [ ] Arrow keys update focused index
- [ ] Focus moves to element when index changes
- [ ] Tab exits composite to next component
- [ ] Shift+Tab exits composite to previous component

## Pattern-Specific Keyboard Behavior

### Modal Dialog

#### Required Keys
- **Tab/Shift+Tab**: Cycle through focusable elements inside modal
- **Escape**: Close modal

#### Focus Trap Implementation
```jsx
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
```

#### Checklist
- [ ] Focus moves inside modal on open
- [ ] Tab cycles through elements inside modal
- [ ] Shift+Tab cycles backward through elements
- [ ] Tab wraps from last to first element
- [ ] Shift+Tab wraps from first to last element
- [ ] Escape closes modal
- [ ] Focus returns to trigger on close

### Tabs

#### Required Keys
- **Arrow Left/Right**: Navigate between tabs (horizontal)
- **Arrow Up/Down**: Navigate between tabs (vertical)
- **Home**: First tab
- **End**: Last tab
- **Tab**: Move from tablist to panel content

#### Implementation
```jsx
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
  setSelectedIndex(nextIndex); // Optional: auto-select on focus
};
```

#### Checklist
- [ ] Arrow keys navigate between tabs
- [ ] Home/End jump to first/last tab
- [ ] Tab moves from tablist to panel
- [ ] Only selected tab in tab sequence
- [ ] Arrow navigation wraps (last → first, first → last)

### Menu

#### Required Keys
- **Arrow Up/Down**: Navigate menu items
- **Home**: First item
- **End**: Last item
- **Enter/Space**: Activate item
- **Escape**: Close menu
- **Type-ahead**: Jump to item starting with typed character

#### Submenu Keys
- **Arrow Right**: Open submenu
- **Arrow Left**: Close submenu, return to parent

#### Checklist
- [ ] Arrow Up/Down navigate items
- [ ] Home/End jump to first/last item
- [ ] Enter/Space activate item
- [ ] Escape closes menu
- [ ] Arrow Right opens submenu
- [ ] Arrow Left closes submenu
- [ ] Type-ahead implemented (optional but recommended)

### Listbox

#### Required Keys
- **Arrow Up/Down**: Navigate options
- **Home**: First option
- **End**: Last option
- **Space**: Select option (multi-select) or toggle selection
- **Enter**: Select option and close (single-select)
- **Type-ahead**: Jump to option starting with typed character

#### Multi-Select Additional Keys
- **Ctrl+A**: Select all (optional)
- **Shift+Arrow**: Extend selection (optional)

#### Checklist
- [ ] Arrow Up/Down navigate options
- [ ] Home/End jump to first/last option
- [ ] Space selects/toggles option
- [ ] Enter selects and closes (single-select)
- [ ] Type-ahead implemented
- [ ] Only selected option in tab sequence

### Combobox

#### Required Keys
- **Arrow Down**: Open popup, move to next option
- **Arrow Up**: Move to previous option
- **Home**: First option
- **End**: Last option
- **Enter**: Select option, close popup
- **Escape**: Close popup
- **Type**: Filter options

#### Checklist
- [ ] Arrow Down opens popup
- [ ] Arrow keys navigate options
- [ ] Home/End jump to first/last option
- [ ] Enter selects option
- [ ] Escape closes popup
- [ ] Typing filters options
- [ ] Selected option highlighted

### Accordion

#### Required Keys
- **Enter/Space**: Toggle section
- **Tab**: Move to next focusable element

#### Optional Keys
- **Arrow Down**: Next accordion header
- **Arrow Up**: Previous accordion header
- **Home**: First accordion header
- **End**: Last accordion header

#### Checklist
- [ ] Enter/Space toggle section
- [ ] Tab moves to next element (not next header)
- [ ] Optional arrow key navigation implemented

### Radio Group

#### Required Keys
- **Arrow Up/Down** or **Arrow Left/Right**: Select option
- **Space**: Select focused option
- **Tab**: Enter/exit group

#### Checklist
- [ ] Arrow keys select option (automatically unselect others)
- [ ] Space selects focused option
- [ ] Tab enters group (focuses selected or first option)
- [ ] Tab exits group to next component
- [ ] Only selected option in tab sequence

### Grid (Interactive Table)

#### Required Keys
- **Arrow keys**: Navigate cells
- **Home**: First cell in row
- **End**: Last cell in row
- **Ctrl+Home**: First cell in grid
- **Ctrl+End**: Last cell in grid
- **Page Down**: Scroll down (optional)
- **Page Up**: Scroll up (optional)
- **Tab**: Exit grid to next component

#### Checklist
- [ ] Arrow keys navigate cells
- [ ] Home/End navigate within row
- [ ] Ctrl+Home/End navigate to grid boundaries
- [ ] Tab exits grid
- [ ] Only one cell in tab sequence
- [ ] Focus visible on current cell

### Tree View

#### Required Keys
- **Arrow Up/Down**: Navigate items
- **Arrow Right**: Expand node, move to first child
- **Arrow Left**: Collapse node, move to parent
- **Home**: First visible item
- **End**: Last visible item
- **Enter/Space**: Activate item
- **Type-ahead**: Jump to item

#### Checklist
- [ ] Arrow Up/Down navigate items
- [ ] Arrow Right expands node
- [ ] Arrow Left collapses node
- [ ] Home/End jump to first/last visible item
- [ ] Enter/Space activate item
- [ ] Type-ahead implemented
- [ ] Only one item in tab sequence

## Focus Management Patterns

### Focus on Mount
```jsx
const elementRef = useRef(null);

useEffect(() => {
  elementRef.current?.focus();
}, []);

return <input ref={elementRef} />;
```

### Focus After State Change
```jsx
useEffect(() => {
  if (shouldFocus) {
    elementRef.current?.focus();
  }
}, [shouldFocus]);
```

### Focus After Deletion
```jsx
const handleDelete = (id, index) => {
  deleteItem(id);
  
  // Move focus to next item, or previous if last
  const nextIndex = index < items.length - 1 ? index : index - 1;
  const nextItem = items[nextIndex];
  
  if (nextItem) {
    setTimeout(() => {
      itemRefs.current[nextItem.id]?.focus();
    }, 0);
  }
};
```

### Focus Restoration After Modal
```jsx
const triggerRef = useRef(null);

useEffect(() => {
  if (isOpen) {
    triggerRef.current = document.activeElement;
  } else if (triggerRef.current) {
    triggerRef.current.focus();
  }
}, [isOpen]);
```

## Testing Checklist

### Manual Keyboard Testing
**Disconnect mouse or commit to not using it.**

- [ ] Tab through entire component
- [ ] All interactive elements reachable
- [ ] Tab order matches visual/reading order
- [ ] Focus indicators clearly visible throughout
- [ ] No keyboard traps (can Tab out of everything)
- [ ] Arrow keys work correctly in composites
- [ ] Enter/Space activate controls
- [ ] Escape closes modals/menus
- [ ] Home/End keys work where expected
- [ ] Can complete all tasks without mouse

### Automated Testing
```jsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

test('keyboard navigation works', async () => {
  const user = userEvent.setup();
  render(<Component />);
  
  // Tab to element
  await user.tab();
  expect(screen.getByRole('button')).toHaveFocus();
  
  // Activate with Enter
  await user.keyboard('{Enter}');
  
  // Navigate with arrows
  await user.keyboard('{ArrowRight}');
});
```

## Common Pitfalls

### All Elements in Tab Sequence
```jsx
// ❌ WRONG - User must Tab through every item
<div role="tablist">
  <button role="tab">Tab 1</button>
  <button role="tab">Tab 2</button>
  <button role="tab">Tab 3</button>
</div>

// ✅ CORRECT - Tab enters/exits, arrows navigate
<div role="tablist">
  <button role="tab" tabIndex={0}>Tab 1</button>
  <button role="tab" tabIndex={-1}>Tab 2</button>
  <button role="tab" tabIndex={-1}>Tab 3</button>
</div>
```

### Forgetting preventDefault
```jsx
// ❌ WRONG - Page scrolls when using arrow keys
const handleKeyDown = (e) => {
  if (e.key === 'ArrowDown') {
    moveToNext();
  }
};

// ✅ CORRECT - Prevent default behavior
const handleKeyDown = (e) => {
  if (e.key === 'ArrowDown') {
    e.preventDefault();
    moveToNext();
  }
};
```

### Not Handling Both Enter and Space
```jsx
// ❌ WRONG - Only Enter activates
const handleKeyDown = (e) => {
  if (e.key === 'Enter') {
    activate();
  }
};

// ✅ CORRECT - Both Enter and Space activate
const handleKeyDown = (e) => {
  if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault();
    activate();
  }
};
```

### Keyboard Trap Without Escape
```jsx
// ❌ WRONG - No way to close with keyboard
<div role="dialog">
  <button onClick={close}>Close</button>
</div>

// ✅ CORRECT - Escape closes dialog
<div role="dialog" onKeyDown={(e) => e.key === 'Escape' && close()}>
  <button onClick={close}>Close</button>
</div>
```

## Resources

- **WCAG 2.1.1 Keyboard**: https://www.w3.org/WAI/WCAG22/Understanding/keyboard
- **WCAG 2.1.2 No Keyboard Trap**: https://www.w3.org/WAI/WCAG22/Understanding/no-keyboard-trap
- **WCAG 2.4.3 Focus Order**: https://www.w3.org/WAI/WCAG22/Understanding/focus-order
- **WCAG 2.4.7 Focus Visible**: https://www.w3.org/WAI/WCAG22/Understanding/focus-visible
- **APG Keyboard Navigation**: https://www.w3.org/WAI/ARIA/apg/practices/keyboard-interface/
