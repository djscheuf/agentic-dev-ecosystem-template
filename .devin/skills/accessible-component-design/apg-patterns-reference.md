# W3C ARIA Authoring Practices Guide (APG) Patterns Reference

Quick reference to established accessibility patterns from the W3C ARIA Authoring Practices Guide.

## Common Widget Patterns

### Accordion
**Use for:** Vertically stacked expandable/collapsible sections

**Structure:**
- Button controls each section (with `aria-expanded`)
- Button has `aria-controls` pointing to section ID
- Section has `id` matching `aria-controls`

**Keyboard:**
- Enter/Space: Toggle section
- Tab: Move to next focusable element

**Link:** https://www.w3.org/WAI/ARIA/apg/patterns/accordion/

---

### Alert and Alert Dialog
**Use for:** Important messages that require immediate attention

**Alert (non-modal):**
- `role="alert"` (automatically has `aria-live="assertive"`)
- Announced immediately by screen readers

**Alert Dialog (modal):**
- `role="alertdialog"`, `aria-modal="true"`
- Focus moves inside, trapped until dismissed
- Escape closes dialog

**Link:** https://www.w3.org/WAI/ARIA/apg/patterns/alert/
**Link:** https://www.w3.org/WAI/ARIA/apg/patterns/alertdialog/

---

### Breadcrumb
**Use for:** Navigation showing current page location in hierarchy

**Structure:**
- `<nav aria-label="Breadcrumb">`
- Ordered list `<ol>`
- Current page: `aria-current="page"`

**Keyboard:**
- Tab: Navigate between links
- Enter: Activate link

**Link:** https://www.w3.org/WAI/ARIA/apg/patterns/breadcrumb/

---

### Button
**Use for:** Triggering actions

**Native HTML Preferred:**
- `<button>` for actions
- `<a href>` for navigation

**Custom Button (if needed):**
- `role="button"`
- `tabIndex={0}`
- Enter and Space activate

**Link:** https://www.w3.org/WAI/ARIA/apg/patterns/button/

---

### Carousel (Rotation Control)
**Use for:** Rotating content with user controls

**Requirements:**
- Pause/play control
- Previous/next buttons
- Optional auto-rotation (must be pausable)
- Keyboard navigation between slides

**Keyboard:**
- Tab: Navigate controls
- Arrow keys: Previous/next slide (optional)

**Link:** https://www.w3.org/WAI/ARIA/apg/patterns/carousel/

---

### Checkbox
**Use for:** Binary or tri-state options

**Native HTML Preferred:**
- `<input type="checkbox">`

**Custom Checkbox (if needed):**
- `role="checkbox"`
- `aria-checked="true|false|mixed"`
- `tabIndex={0}`
- Space toggles

**Link:** https://www.w3.org/WAI/ARIA/apg/patterns/checkbox/

---

### Combobox
**Use for:** Input with autocomplete/search and popup listbox

**Structure:**
- Input: `role="combobox"`, `aria-expanded`, `aria-controls`
- Popup: `role="listbox"`
- Options: `role="option"`

**Keyboard:**
- Arrow Down: Open popup, move to next option
- Arrow Up: Move to previous option
- Enter: Select option, close popup
- Escape: Close popup
- Type-ahead: Filter options

**Link:** https://www.w3.org/WAI/ARIA/apg/patterns/combobox/

---

### Dialog (Modal)
**Use for:** Overlay requiring user interaction before returning to main content

**Structure:**
- Container: `role="dialog"`, `aria-modal="true"`
- Label: `aria-labelledby` (title) or `aria-label`
- Description: `aria-describedby` (optional)

**Focus Management:**
- Move focus inside on open
- Trap focus within dialog
- Restore focus to trigger on close

**Keyboard:**
- Tab/Shift+Tab: Cycle through focusable elements
- Escape: Close dialog

**Link:** https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/

---

### Disclosure (Show/Hide)
**Use for:** Button that shows/hides content

**Structure:**
- Button: `aria-expanded="true|false"`, `aria-controls`
- Content: `id` matching `aria-controls`

**Keyboard:**
- Enter/Space: Toggle content

**Native HTML Alternative:**
- `<details>` and `<summary>` elements

**Link:** https://www.w3.org/WAI/ARIA/apg/patterns/disclosure/

---

### Feed
**Use for:** Scrollable list of articles (like social media feed)

**Structure:**
- Container: `role="feed"`
- Articles: `role="article"`, `aria-posinset`, `aria-setsize`
- Each article: `aria-labelledby` (title)

**Keyboard:**
- Page Down/Page Up: Load more content
- Tab: Navigate interactive elements

**Link:** https://www.w3.org/WAI/ARIA/apg/patterns/feed/

---

### Grid (Interactive Table)
**Use for:** Interactive table with cell-by-cell navigation

**Structure:**
- Container: `role="grid"`
- Rows: `role="row"`
- Cells: `role="gridcell"` (editable) or `role="columnheader"`/`role="rowheader"`

**Keyboard:**
- Arrow keys: Navigate cells
- Tab: Exit grid to next component
- Home/End: First/last cell in row
- Ctrl+Home/End: First/last cell in grid
- Enter/Space: Activate cell (if interactive)

**Link:** https://www.w3.org/WAI/ARIA/apg/patterns/grid/

---

### Link
**Use for:** Navigation to another page or location

**Native HTML Preferred:**
- `<a href="url">` for navigation

**Custom Link (avoid if possible):**
- `role="link"`
- `tabIndex={0}`
- Enter activates

**Link:** https://www.w3.org/WAI/ARIA/apg/patterns/link/

---

### Listbox
**Use for:** Selectable list of options (alternative to native select)

**Structure:**
- Container: `role="listbox"`
- Options: `role="option"`, `aria-selected="true|false"`
- Label: `aria-labelledby` or `aria-label`

**Keyboard:**
- Arrow Up/Down: Navigate options
- Space: Select option (multi-select)
- Enter: Select option, close (single-select)
- Home/End: First/last option
- Type-ahead: Jump to option starting with typed character

**Roving Tabindex:**
- Only selected option has `tabIndex={0}`
- Others have `tabIndex={-1}`

**Link:** https://www.w3.org/WAI/ARIA/apg/patterns/listbox/

---

### Menu and Menubar
**Use for:** Application menu with keyboard shortcuts (not site navigation)

**Structure:**
- Container: `role="menu"` or `role="menubar"`
- Items: `role="menuitem"`, `role="menuitemcheckbox"`, `role="menuitemradio"`
- Submenus: `role="menu"`, `aria-expanded` on parent

**Keyboard:**
- Arrow Up/Down: Navigate items (vertical menu)
- Arrow Left/Right: Navigate items (horizontal menubar), open/close submenus
- Enter/Space: Activate item
- Escape: Close menu
- Home/End: First/last item
- Type-ahead: Jump to item

**Link:** https://www.w3.org/WAI/ARIA/apg/patterns/menu/
**Link:** https://www.w3.org/WAI/ARIA/apg/patterns/menubar/

---

### Radio Group
**Use for:** Mutually exclusive options

**Native HTML Preferred:**
- `<input type="radio" name="group">`
- Wrapped in `<fieldset>` with `<legend>`

**Custom Radio Group (if needed):**
- Container: `role="radiogroup"`, `aria-labelledby` or `aria-label`
- Options: `role="radio"`, `aria-checked="true|false"`

**Keyboard:**
- Arrow keys: Select option (automatically unselects others)
- Tab: Enter/exit group
- Space: Select focused option

**Link:** https://www.w3.org/WAI/ARIA/apg/patterns/radio/

---

### Slider
**Use for:** Selecting value from range

**Native HTML Preferred:**
- `<input type="range">`

**Custom Slider (if needed):**
- `role="slider"`
- `aria-valuemin`, `aria-valuemax`, `aria-valuenow`
- `aria-valuetext` (for non-numeric values)
- `aria-labelledby` or `aria-label`

**Keyboard:**
- Arrow Right/Up: Increase value
- Arrow Left/Down: Decrease value
- Home: Minimum value
- End: Maximum value
- Page Up/Down: Large increment/decrement

**Link:** https://www.w3.org/WAI/ARIA/apg/patterns/slider/

---

### Spinbutton
**Use for:** Numeric input with increment/decrement buttons

**Native HTML Preferred:**
- `<input type="number">`

**Custom Spinbutton (if needed):**
- `role="spinbutton"`
- `aria-valuemin`, `aria-valuemax`, `aria-valuenow`
- `aria-labelledby` or `aria-label`

**Keyboard:**
- Arrow Up: Increase value
- Arrow Down: Decrease value
- Home: Minimum value
- End: Maximum value
- Page Up/Down: Large increment/decrement

**Link:** https://www.w3.org/WAI/ARIA/apg/patterns/spinbutton/

---

### Switch
**Use for:** On/off toggle (not checkbox)

**Structure:**
- `role="switch"`
- `aria-checked="true|false"`
- `aria-labelledby` or `aria-label`

**Keyboard:**
- Space: Toggle state
- Enter: Toggle state (optional)

**Link:** https://www.w3.org/WAI/ARIA/apg/patterns/switch/

---

### Table
**Use for:** Static data table (not interactive)

**Native HTML Preferred:**
- `<table>`, `<thead>`, `<tbody>`, `<tr>`, `<th>`, `<td>`
- `<caption>` for table title
- `scope="col|row"` on `<th>` elements

**Custom Table (avoid if possible):**
- `role="table"`
- `role="rowgroup"`, `role="row"`, `role="columnheader"`, `role="cell"`

**Link:** https://www.w3.org/WAI/ARIA/apg/patterns/table/

---

### Tabs
**Use for:** Layered sections of content, only one visible at a time

**Structure:**
- Tablist: `role="tablist"`
- Tabs: `role="tab"`, `aria-selected="true|false"`, `aria-controls`
- Panels: `role="tabpanel"`, `aria-labelledby`

**Keyboard:**
- Arrow Left/Right: Navigate tabs (horizontal)
- Arrow Up/Down: Navigate tabs (vertical)
- Tab: Move from tablist to panel content
- Home/End: First/last tab

**Roving Tabindex:**
- Only selected tab has `tabIndex={0}`
- Other tabs have `tabIndex={-1}`

**Link:** https://www.w3.org/WAI/ARIA/apg/patterns/tabs/

---

### Toolbar
**Use for:** Collection of commonly used function buttons

**Structure:**
- Container: `role="toolbar"`, `aria-label`
- Buttons: Native `<button>` elements

**Keyboard:**
- Tab: Enter/exit toolbar
- Arrow Left/Right: Navigate buttons
- Home/End: First/last button
- Enter/Space: Activate button

**Link:** https://www.w3.org/WAI/ARIA/apg/patterns/toolbar/

---

### Tooltip
**Use for:** Contextual information popup on hover/focus

**Structure:**
- Trigger: `aria-describedby` pointing to tooltip ID
- Tooltip: `role="tooltip"`, `id` matching `aria-describedby`

**Behavior:**
- Appears on hover and focus
- Dismisses on Escape or when trigger loses focus
- Does not receive focus itself

**Link:** https://www.w3.org/WAI/ARIA/apg/patterns/tooltip/

---

### Tree View
**Use for:** Hierarchical list with expand/collapse

**Structure:**
- Container: `role="tree"`, `aria-labelledby` or `aria-label`
- Groups: `role="group"`
- Items: `role="treeitem"`, `aria-expanded` (if has children)

**Keyboard:**
- Arrow Up/Down: Navigate items
- Arrow Right: Expand node, move to first child
- Arrow Left: Collapse node, move to parent
- Enter/Space: Activate item
- Home/End: First/last visible item
- Type-ahead: Jump to item

**Link:** https://www.w3.org/WAI/ARIA/apg/patterns/treeview/

---

## Landmark Patterns

### Banner
**Use for:** Site header with logo, site title, navigation

**Native HTML Preferred:**
- `<header>` (when not inside `<article>` or `<section>`)

**Custom:**
- `role="banner"`

**Link:** https://www.w3.org/WAI/ARIA/apg/practices/landmark-regions/

---

### Complementary
**Use for:** Supporting content related to main content

**Native HTML Preferred:**
- `<aside>`

**Custom:**
- `role="complementary"`

---

### Content Info
**Use for:** Site footer with copyright, privacy, contact

**Native HTML Preferred:**
- `<footer>` (when not inside `<article>` or `<section>`)

**Custom:**
- `role="contentinfo"`

---

### Form
**Use for:** Collection of form controls

**Native HTML Preferred:**
- `<form>`

**Custom:**
- `role="form"` (with `aria-labelledby` or `aria-label`)

---

### Main
**Use for:** Primary content of page

**Native HTML Preferred:**
- `<main>`

**Custom:**
- `role="main"`

**Rules:**
- Only one `<main>` per page
- Not nested inside `<article>`, `<aside>`, `<footer>`, `<header>`, `<nav>`

---

### Navigation
**Use for:** Collection of navigation links

**Native HTML Preferred:**
- `<nav>`

**Custom:**
- `role="navigation"`

**Best Practice:**
- Use `aria-label` to distinguish multiple navigation regions
- Example: `<nav aria-label="Main navigation">`, `<nav aria-label="Footer navigation">`

---

### Region
**Use for:** Important content area that should be in landmark list

**Native HTML Preferred:**
- `<section>` (with `aria-labelledby` or `aria-label`)

**Custom:**
- `role="region"` (with `aria-labelledby` or `aria-label`)

**Note:** Only use for sufficiently important content

---

### Search
**Use for:** Search functionality

**Structure:**
- Container: `role="search"`
- Form: `<form>` inside search region
- Input: `<input type="search">` or `<input type="text">`
- Button: `<button type="submit">`

---

## Live Region Patterns

### Alert
**Use for:** Important message requiring immediate attention

**Structure:**
- `role="alert"` (automatically `aria-live="assertive"`)
- Announced immediately, interrupts screen reader

---

### Log
**Use for:** Chat logs, error logs, game logs

**Structure:**
- `role="log"` (automatically `aria-live="polite"`)
- New messages announced when screen reader finishes current announcement

---

### Marquee
**Use for:** Non-essential information that changes frequently

**Structure:**
- `role="marquee"` (automatically `aria-live="off"`)
- Not announced automatically

---

### Status
**Use for:** Status messages, progress updates

**Structure:**
- `role="status"` (automatically `aria-live="polite"`)
- Announced when screen reader finishes current announcement

---

### Timer
**Use for:** Countdown or elapsed time

**Structure:**
- `role="timer"`
- `aria-live="off"` (default, don't announce every second)
- `aria-atomic="true"` (announce entire timer, not just changed digit)

---

## Pattern Selection Decision Tree

```
What type of component are you building?

├─ Navigation/Structure
│  ├─ Site header → <header> or role="banner"
│  ├─ Site footer → <footer> or role="contentinfo"
│  ├─ Main content → <main> or role="main"
│  ├─ Navigation links → <nav> or role="navigation"
│  ├─ Sidebar → <aside> or role="complementary"
│  └─ Search → role="search"
│
├─ Interactive Controls
│  ├─ Action trigger → <button> or role="button"
│  ├─ Navigation → <a href> or role="link"
│  ├─ Binary option → <input type="checkbox"> or role="checkbox"
│  ├─ On/off toggle → role="switch"
│  ├─ Mutually exclusive options → <input type="radio"> or role="radio"
│  ├─ Dropdown selection → <select> or role="listbox"
│  ├─ Search with autocomplete → role="combobox"
│  ├─ Numeric input → <input type="number"> or role="spinbutton"
│  └─ Range selection → <input type="range"> or role="slider"
│
├─ Content Organization
│  ├─ Layered content (one visible) → role="tablist" + role="tab" + role="tabpanel"
│  ├─ Expandable sections → <details>/<summary> or role="button" + aria-expanded
│  ├─ Hierarchical list → role="tree"
│  └─ Data table → <table> or role="table"
│
├─ Overlays
│  ├─ Modal dialog → role="dialog" + aria-modal="true"
│  ├─ Alert dialog → role="alertdialog" + aria-modal="true"
│  ├─ Tooltip → role="tooltip"
│  └─ Non-modal popup → role="dialog" (without aria-modal)
│
└─ Dynamic Content
   ├─ Important message → role="alert"
   ├─ Status update → role="status"
   ├─ Chat/log → role="log"
   └─ Timer → role="timer"
```

## Resources

- **W3C ARIA Authoring Practices Guide**: https://www.w3.org/WAI/ARIA/apg/
- **Pattern Index**: https://www.w3.org/WAI/ARIA/apg/patterns/
- **Example Implementations**: https://www.w3.org/WAI/ARIA/apg/example-index/
