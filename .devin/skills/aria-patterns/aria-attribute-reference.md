# ARIA Attribute Reference

Quick reference for when to use each ARIA attribute.

## Roles

### Widget Roles

**`role="button"`** - Interactive element that triggers action
- Use when: Custom button needed (prefer native `<button>`)
- Requires: Keyboard support (Enter/Space), `tabIndex={0}`

**`role="checkbox"`** - Binary or tri-state option
- Use when: Custom checkbox needed (prefer native `<input type="checkbox">`)
- Requires: `aria-checked`, keyboard support (Space), `tabIndex={0}`

**`role="radio"`** - Mutually exclusive option in group
- Use when: Custom radio button needed (prefer native `<input type="radio">`)
- Requires: `aria-checked`, keyboard support (arrow keys), `tabIndex` management

**`role="switch"`** - On/off toggle
- Use when: Toggle switch (not checkbox)
- Requires: `aria-checked`, keyboard support (Space), `tabIndex={0}`

**`role="tab"`** - Tab in tablist
- Use when: Implementing tabs pattern
- Requires: `aria-selected`, `aria-controls`, roving tabindex

**`role="tabpanel"`** - Content panel for tab
- Use when: Implementing tabs pattern
- Requires: `aria-labelledby` (referencing tab)

**`role="menu"`** - Application menu
- Use when: Application menu with keyboard shortcuts (NOT site navigation)
- Requires: Roving tabindex, arrow key navigation

**`role="menuitem"`** - Item in menu
- Use when: Inside `role="menu"`
- Requires: Roving tabindex, Enter/Space activation

**`role="listbox"`** - Selectable list of options
- Use when: Custom select needed (prefer native `<select>`)
- Requires: `role="option"` children, roving tabindex

**`role="option"`** - Option in listbox or combobox
- Use when: Inside `role="listbox"` or combobox
- Requires: `aria-selected`, roving tabindex

**`role="combobox"`** - Input with popup listbox
- Use when: Autocomplete/search with dropdown
- Requires: `aria-expanded`, `aria-controls`, `aria-autocomplete`

**`role="dialog"`** - Modal or non-modal dialog
- Use when: Overlay requiring user interaction
- Requires: `aria-labelledby` or `aria-label`, focus management

**`role="alertdialog"`** - Dialog with important message
- Use when: Critical message requiring immediate attention
- Requires: Same as dialog + `aria-describedby`

**`role="tree"`** - Hierarchical list
- Use when: File explorer, org chart, etc.
- Requires: `role="treeitem"` children, roving tabindex

**`role="grid"`** - Interactive table
- Use when: Table with cell-by-cell navigation (prefer native `<table>` for static data)
- Requires: `role="row"`, `role="gridcell"`, roving tabindex

### Document Structure Roles

**`role="main"`** - Primary content
- Use when: Native `<main>` not available
- Note: Only one per page

**`role="navigation"`** - Navigation links
- Use when: Native `<nav>` not available
- Best practice: Use `aria-label` to distinguish multiple navigation regions

**`role="banner"`** - Site header
- Use when: Native `<header>` not available (or `<header>` inside `<article>`)
- Note: Only one per page

**`role="contentinfo"`** - Site footer
- Use when: Native `<footer>` not available (or `<footer>` inside `<article>`)
- Note: Only one per page

**`role="complementary"`** - Supporting content
- Use when: Native `<aside>` not available

**`role="search"`** - Search functionality
- Use when: Marking search region
- Best practice: Contains form with search input

**`role="form"`** - Form landmark
- Use when: Native `<form>` not available
- Requires: `aria-labelledby` or `aria-label`

**`role="region"`** - Important content area
- Use when: Significant content that should be in landmark list
- Requires: `aria-labelledby` or `aria-label`

### Live Region Roles

**`role="alert"`** - Important message
- Use when: Error, warning, or important notification
- Automatically: `aria-live="assertive"` (interrupts screen reader)

**`role="status"`** - Status message
- Use when: Non-critical status update
- Automatically: `aria-live="polite"` (waits for screen reader to finish)

**`role="log"`** - Chat log, error log, game log
- Use when: New messages appended to list
- Automatically: `aria-live="polite"`

**`role="timer"`** - Countdown or elapsed time
- Use when: Displaying timer
- Automatically: `aria-live="off"` (don't announce every second)

## States and Properties

### Labeling

**`aria-label`** - Invisible label
- Use when: No visible text appropriate for label
- Example: `<button aria-label="Close dialog">×</button>`

**`aria-labelledby`** - References visible label by ID
- Use when: Visible text should be label
- Example: `<div role="dialog" aria-labelledby="title-id">`
- Priority: Overrides `aria-label` and native labels

**`aria-describedby`** - References description by ID
- Use when: Additional description needed
- Example: `<input aria-describedby="error-id">`

### States

**`aria-checked`** - Checked state
- Values: `"true"`, `"false"`, `"mixed"` (tri-state)
- Use with: `role="checkbox"`, `role="radio"`, `role="switch"`, `role="menuitemcheckbox"`
- Example: `<div role="checkbox" aria-checked="true">`

**`aria-selected`** - Selected state
- Values: `"true"`, `"false"`
- Use with: `role="tab"`, `role="option"`, `role="gridcell"`
- Example: `<button role="tab" aria-selected="true">`

**`aria-expanded`** - Expanded/collapsed state
- Values: `"true"`, `"false"`, `undefined` (not expandable)
- Use with: Accordions, disclosure widgets, comboboxes, tree items
- Example: `<button aria-expanded="false" aria-controls="section-1">`

**`aria-pressed`** - Pressed state (toggle button)
- Values: `"true"`, `"false"`, `"mixed"`
- Use with: Toggle buttons
- Example: `<button aria-pressed="true">Bold</button>`

**`aria-hidden`** - Hidden from assistive technology
- Values: `"true"`, `"false"`
- Use when: Hiding decorative content
- **NEVER** use on focusable elements
- Example: `<div aria-hidden="true"><img src="decorative.png" /></div>`

**`aria-disabled`** - Disabled state
- Values: `"true"`, `"false"`
- Use when: Element disabled but still visible
- Note: Also remove from tab sequence (`tabIndex={-1}`)
- Example: `<button aria-disabled="true" tabIndex={-1}>`

**`aria-invalid`** - Validation state
- Values: `"true"`, `"false"`, `"grammar"`, `"spelling"`
- Use with: Form inputs
- Example: `<input aria-invalid="true" aria-describedby="error-id">`

**`aria-required`** - Required field
- Values: `"true"`, `"false"`
- Use with: Form inputs (in addition to `required` attribute)
- Example: `<input required aria-required="true">`

### Relationships

**`aria-controls`** - Element controlled by this element
- Value: ID of controlled element
- Use with: Buttons that show/hide content, tabs
- Example: `<button aria-controls="panel-1" aria-expanded="false">`

**`aria-owns`** - Defines parent-child relationship
- Value: Space-separated list of IDs
- Use when: DOM structure doesn't reflect relationship
- Example: `<div role="listbox" aria-owns="option-1 option-2">`

**`aria-activedescendant`** - Currently active descendant
- Value: ID of active element
- Use with: Comboboxes, grids (when container has focus)
- Example: `<input role="combobox" aria-activedescendant="option-2">`

**`aria-flowto`** - Next element in reading order
- Value: ID of next element
- Use when: Reading order differs from DOM order
- Rarely needed

### Widget Attributes

**`aria-autocomplete`** - Autocomplete behavior
- Values: `"none"`, `"inline"`, `"list"`, `"both"`
- Use with: `role="combobox"`
- Example: `<input role="combobox" aria-autocomplete="list">`

**`aria-haspopup`** - Has popup
- Values: `"true"`, `"false"`, `"menu"`, `"listbox"`, `"tree"`, `"grid"`, `"dialog"`
- Use with: Buttons that open popups
- Example: `<button aria-haspopup="menu" aria-expanded="false">`

**`aria-modal`** - Modal dialog
- Values: `"true"`, `"false"`
- Use with: `role="dialog"` or `role="alertdialog"`
- Example: `<div role="dialog" aria-modal="true">`

**`aria-multiselectable`** - Multiple selection allowed
- Values: `"true"`, `"false"`
- Use with: `role="listbox"`, `role="grid"`, `role="tree"`
- Example: `<div role="listbox" aria-multiselectable="true">`

**`aria-orientation`** - Widget orientation
- Values: `"horizontal"`, `"vertical"`
- Use with: Tabs, sliders, scrollbars
- Default: `"horizontal"` for tabs, `"vertical"` for most others
- Example: `<div role="tablist" aria-orientation="vertical">`

**`aria-readonly`** - Read-only state
- Values: `"true"`, `"false"`
- Use with: Form inputs
- Example: `<input aria-readonly="true">`

### Live Region Attributes

**`aria-live`** - Live region politeness
- Values: `"off"`, `"polite"`, `"assertive"`
- `"polite"`: Wait for screen reader to finish
- `"assertive"`: Interrupt screen reader
- Example: `<div aria-live="polite">{statusMessage}</div>`

**`aria-atomic`** - Announce entire region or just changes
- Values: `"true"`, `"false"`
- `"true"`: Announce entire region
- `"false"`: Announce only changes
- Example: `<div aria-live="polite" aria-atomic="true">`

**`aria-relevant`** - What changes to announce
- Values: `"additions"`, `"removals"`, `"text"`, `"all"`
- Default: `"additions text"`
- Example: `<div aria-live="polite" aria-relevant="all">`

### Grid/Table Attributes

**`aria-colcount`** - Total number of columns
- Value: Integer
- Use with: `role="grid"` or `role="table"`
- Example: `<div role="grid" aria-colcount="10">`

**`aria-rowcount`** - Total number of rows
- Value: Integer
- Use with: `role="grid"` or `role="table"`
- Example: `<div role="grid" aria-rowcount="100">`

**`aria-colindex`** - Column index
- Value: Integer (1-indexed)
- Use with: `role="gridcell"` or `role="columnheader"`
- Example: `<div role="gridcell" aria-colindex="3">`

**`aria-rowindex`** - Row index
- Value: Integer (1-indexed)
- Use with: `role="row"`
- Example: `<div role="row" aria-rowindex="5">`

**`aria-colspan`** - Column span
- Value: Integer
- Use with: `role="gridcell"` or `role="columnheader"`
- Example: `<div role="gridcell" aria-colspan="2">`

**`aria-rowspan`** - Row span
- Value: Integer
- Use with: `role="gridcell"` or `role="rowheader"`
- Example: `<div role="gridcell" aria-rowspan="2">`

### Tree Attributes

**`aria-level`** - Level in hierarchy
- Value: Integer (1-indexed)
- Use with: `role="treeitem"`, `role="heading"`
- Example: `<div role="treeitem" aria-level="2">`

**`aria-posinset`** - Position in set
- Value: Integer (1-indexed)
- Use with: `role="treeitem"`, `role="option"`, `role="tab"`
- Example: `<div role="option" aria-posinset="3">`

**`aria-setsize`** - Size of set
- Value: Integer
- Use with: `role="treeitem"`, `role="option"`, `role="tab"`
- Example: `<div role="option" aria-setsize="10">`

## Common Combinations

### Modal Dialog
```jsx
<div 
  role="dialog"
  aria-modal="true"
  aria-labelledby="dialog-title"
  aria-describedby="dialog-description"
>
  <h2 id="dialog-title">Title</h2>
  <p id="dialog-description">Description</p>
</div>
```

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
</div>
<div role="tabpanel" id="panel-1" aria-labelledby="tab-1">
  Content
</div>
```

### Accordion
```jsx
<button 
  aria-expanded="false"
  aria-controls="section-1"
>
  Section Title
</button>
<div id="section-1" hidden>
  Content
</div>
```

### Form Input with Error
```jsx
<label htmlFor="email">Email</label>
<input
  type="email"
  id="email"
  required
  aria-required="true"
  aria-invalid="true"
  aria-describedby="email-error"
/>
<div id="email-error" role="alert">
  Please enter a valid email address
</div>
```

### Combobox
```jsx
<label htmlFor="country">Country</label>
<input
  type="text"
  id="country"
  role="combobox"
  aria-expanded="false"
  aria-controls="listbox-1"
  aria-autocomplete="list"
  aria-activedescendant="option-2"
/>
<ul id="listbox-1" role="listbox">
  <li role="option" id="option-1">Option 1</li>
  <li role="option" id="option-2">Option 2</li>
</ul>
```

## Resources

- **ARIA Specification**: https://www.w3.org/TR/wai-aria-1.2/
- **ARIA Roles**: https://www.w3.org/TR/wai-aria-1.2/#role_definitions
- **ARIA States and Properties**: https://www.w3.org/TR/wai-aria-1.2/#state_prop_def
- **Using ARIA**: https://www.w3.org/TR/using-aria/
