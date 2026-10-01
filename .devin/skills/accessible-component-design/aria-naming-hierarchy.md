# ARIA Accessible Naming Hierarchy

Complete guide to providing accessible names for interactive elements.

## Accessible Name Priority Order

When multiple naming methods exist, assistive technology uses this priority order:

1. **`aria-labelledby`** (highest precedence)
2. **`aria-label`**
3. **Native HTML** (`<label>`, `<caption>`, `<legend>`, `<figcaption>`)
4. **Child content** (text content of element)
5. **Fallback** (`title`, `placeholder`)

## 1. aria-labelledby (Highest Precedence)

### When to Use
- Reference visible text by ID
- Combine multiple text elements into single accessible name
- Override other naming methods

### Basic Usage
```jsx
// ✅ Reference visible heading
<div role="dialog" aria-labelledby="dialog-title">
  <h2 id="dialog-title">Confirm Deletion</h2>
  <p>Are you sure you want to delete this item?</p>
</div>
```

### Multiple References
```jsx
// ✅ Combine multiple text elements
<button aria-labelledby="action-label item-name">
  <span id="action-label">Delete</span>
  <span id="item-name">Report Q4 2025</span>
</button>
// Accessible name: "Delete Report Q4 2025"
```

### Tab Panel Labeling
```jsx
// ✅ Panel labeled by its tab
<button 
  role="tab" 
  id="settings-tab"
  aria-controls="settings-panel"
>
  Settings
</button>
<div 
  role="tabpanel" 
  id="settings-panel"
  aria-labelledby="settings-tab"
>
  Settings content
</div>
```

### Advantages
- References visible text (no duplication)
- Keeps accessible name in sync with visible text
- Can combine multiple text sources

### Disadvantages
- Requires managing IDs
- More complex than `aria-label`

## 2. aria-label

### When to Use
- No visible text appropriate for accessible name
- Icon-only buttons
- Visible text insufficient or unclear

### Icon Buttons
```jsx
// ✅ Icon button with aria-label
<button aria-label="Close dialog" onClick={closeDialog}>
  <XIcon />
</button>

// ✅ Icon button with action and context
<button aria-label="Delete Report Q4 2025" onClick={handleDelete}>
  <TrashIcon />
</button>
```

### Supplementing Visible Text
```jsx
// ✅ Add context to generic text
<button aria-label="Edit user profile">
  Edit
</button>

// ✅ Clarify ambiguous link
<a href="/learn-more" aria-label="Learn more about accessibility features">
  Learn More
</a>
```

### Navigation Regions
```jsx
// ✅ Distinguish multiple navigation regions
<nav aria-label="Main navigation">
  <ul>...</ul>
</nav>

<nav aria-label="Footer navigation">
  <ul>...</ul>
</nav>
```

### Advantages
- Simple to implement
- No ID management needed
- Works when no visible text exists

### Disadvantages
- Creates invisible text (can get out of sync with visible text)
- Duplication if visible text exists
- Harder to maintain

## 3. Native HTML Labels

### Form Controls: <label>

#### Explicit Association (Preferred)
```jsx
// ✅ PREFERRED - Works even if label/input separated
<label htmlFor="email">Email Address</label>
<input type="email" id="email" />
```

#### Implicit Association
```jsx
// ✅ ACCEPTABLE - Label wraps input
<label>
  Email Address
  <input type="email" />
</label>
```

#### Multiple Labels
```jsx
// ✅ Multiple labels for single input
<label htmlFor="search">Search</label>
<input 
  type="search" 
  id="search"
  aria-labelledby="search-label region-label"
/>
<span id="region-label">in Products</span>
// Accessible name: "Search in Products"
```

### Fieldset and Legend

#### Radio Groups
```jsx
// ✅ Radio group with legend
<fieldset>
  <legend>Choose size</legend>
  <label><input type="radio" name="size" value="s" /> Small</label>
  <label><input type="radio" name="size" value="m" /> Medium</label>
  <label><input type="radio" name="size" value="l" /> Large</label>
</fieldset>
// Each radio announced as: "Choose size, Small, radio button"
```

#### Checkbox Groups
```jsx
// ✅ Checkbox group with legend
<fieldset>
  <legend>Select toppings</legend>
  <label><input type="checkbox" name="toppings" value="cheese" /> Cheese</label>
  <label><input type="checkbox" name="toppings" value="pepperoni" /> Pepperoni</label>
</fieldset>
```

### Tables: <caption>

```jsx
// ✅ Table with caption
<table>
  <caption>Quarterly Sales Report 2025</caption>
  <thead>
    <tr>
      <th scope="col">Quarter</th>
      <th scope="col">Sales</th>
    </tr>
  </thead>
  <tbody>...</tbody>
</table>
```

### Figures: <figcaption>

```jsx
// ✅ Figure with caption
<figure>
  <img src="chart.png" alt="Sales trend chart" />
  <figcaption>
    Sales increased 25% from Q3 to Q4 2025
  </figcaption>
</figure>
```

## 4. Child Content (Text Content)

### Buttons
```jsx
// ✅ Text content provides accessible name
<button onClick={handleSubmit}>Submit Form</button>
// Accessible name: "Submit Form"

// ✅ Nested elements contribute to name
<button onClick={handleSave}>
  <SaveIcon />
  <span>Save Changes</span>
</button>
// Accessible name: "Save Changes"
```

### Links
```jsx
// ✅ Link text provides accessible name
<a href="/about">About Our Company</a>
// Accessible name: "About Our Company"
```

### Headings
```jsx
// ✅ Heading text provides accessible name
<h1>Welcome to Our Site</h1>
// Accessible name: "Welcome to Our Site"
```

### When Child Content is Insufficient
```jsx
// ❌ WRONG - Generic text, unclear context
<button onClick={handleDelete}>Delete</button>

// ✅ CORRECT - Add context with aria-label
<button aria-label="Delete Report Q4 2025" onClick={handleDelete}>
  Delete
</button>

// ✅ CORRECT - Add context with aria-labelledby
<button aria-labelledby="delete-action item-name" onClick={handleDelete}>
  <span id="delete-action">Delete</span>
  <span id="item-name" className="sr-only">Report Q4 2025</span>
</button>
```

## 5. Fallback Methods (Avoid as Primary)

### title Attribute
```jsx
// ⚠️ AVOID - Not reliably announced by screen readers
<button title="Close dialog" onClick={closeDialog}>
  <XIcon />
</button>

// ✅ BETTER - Use aria-label
<button aria-label="Close dialog" onClick={closeDialog}>
  <XIcon />
</button>
```

### placeholder Attribute
```jsx
// ❌ NEVER - Placeholder disappears when typing
<input type="email" placeholder="Email address" />

// ✅ ALWAYS - Use persistent label
<label htmlFor="email">Email address</label>
<input type="email" id="email" placeholder="name@example.com" />
```

## Special Cases

### Screen Reader Only Text

#### CSS Class Approach
```jsx
// ✅ Visually hidden, announced by screen readers
<button onClick={handleDelete}>
  <TrashIcon />
  <span className="sr-only">Delete item</span>
</button>

// CSS for .sr-only
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
```

#### When to Use
- Icon buttons need text alternative
- Generic visible text needs context
- Additional information for screen reader users

### Combining Visible and Hidden Text
```jsx
// ✅ Visible text + hidden context
<a href="/report.pdf">
  Download Report
  <span className="sr-only">(PDF, 2.5 MB)</span>
</a>
// Visible: "Download Report"
// Announced: "Download Report (PDF, 2.5 MB)"
```

### Decorative Images
```jsx
// ✅ Empty alt for decorative images
<img src="decorative-border.png" alt="" />

// ✅ Hide from screen readers with aria-hidden
<img src="decorative-icon.png" aria-hidden="true" />
```

### Complex Widgets
```jsx
// ✅ Combobox with label
<label htmlFor="country">Country</label>
<input 
  type="text"
  id="country"
  role="combobox"
  aria-expanded={isOpen}
  aria-controls="country-listbox"
  aria-autocomplete="list"
/>
<ul id="country-listbox" role="listbox">
  <li role="option">United States</li>
  <li role="option">Canada</li>
</ul>
```

## Common Patterns

### Modal Dialog
```jsx
// ✅ Dialog labeled by title
<div 
  role="dialog" 
  aria-modal="true"
  aria-labelledby="dialog-title"
  aria-describedby="dialog-description"
>
  <h2 id="dialog-title">Confirm Deletion</h2>
  <p id="dialog-description">
    This action cannot be undone. Are you sure?
  </p>
  <button onClick={confirmDelete}>Delete</button>
  <button onClick={cancelDelete}>Cancel</button>
</div>
```

### Form with Sections
```jsx
// ✅ Form sections with fieldset/legend
<form>
  <fieldset>
    <legend>Personal Information</legend>
    <label htmlFor="name">Name</label>
    <input type="text" id="name" />
    
    <label htmlFor="email">Email</label>
    <input type="email" id="email" />
  </fieldset>
  
  <fieldset>
    <legend>Shipping Address</legend>
    <label htmlFor="street">Street</label>
    <input type="text" id="street" />
    
    <label htmlFor="city">City</label>
    <input type="text" id="city" />
  </fieldset>
</form>
```

### Search Landmark
```jsx
// ✅ Search region with label
<div role="search">
  <label htmlFor="site-search">Search site</label>
  <input type="search" id="site-search" />
  <button type="submit">Search</button>
</div>
```

### Tabs
```jsx
// ✅ Tabs with proper labeling
<div role="tablist" aria-label="Account settings">
  <button 
    role="tab" 
    id="profile-tab"
    aria-selected="true"
    aria-controls="profile-panel"
  >
    Profile
  </button>
  <button 
    role="tab"
    id="security-tab"
    aria-selected="false"
    aria-controls="security-panel"
  >
    Security
  </button>
</div>

<div 
  role="tabpanel" 
  id="profile-panel"
  aria-labelledby="profile-tab"
>
  Profile settings
</div>

<div 
  role="tabpanel"
  id="security-panel"
  aria-labelledby="security-tab"
  hidden
>
  Security settings
</div>
```

## Testing Accessible Names

### Browser DevTools
```
1. Open browser DevTools
2. Inspect element
3. Check "Accessibility" pane
4. Look for "Computed Properties" → "Name"
```

### React Testing Library
```jsx
import { render, screen } from '@testing-library/react';

test('button has accessible name', () => {
  render(<button aria-label="Close dialog">×</button>);
  
  // Query by accessible name
  const button = screen.getByRole('button', { name: 'Close dialog' });
  expect(button).toBeInTheDocument();
});

test('input has accessible name from label', () => {
  render(
    <>
      <label htmlFor="email">Email</label>
      <input type="email" id="email" />
    </>
  );
  
  // Query by label text
  const input = screen.getByLabelText('Email');
  expect(input).toBeInTheDocument();
});
```

### Screen Reader Testing
Test with actual screen readers:
- **Windows**: NVDA (free) or JAWS
- **macOS**: VoiceOver (built-in)
- **Linux**: Orca (built-in)

Verify:
- [ ] Element announced with correct role
- [ ] Accessible name clear and concise
- [ ] Name matches visible text (when applicable)
- [ ] Context provided for generic text

## Common Mistakes

### Using Placeholder as Only Label
```jsx
// ❌ WRONG - Placeholder disappears, not reliable label
<input type="email" placeholder="Email address" />

// ✅ CORRECT - Persistent label
<label htmlFor="email">Email address</label>
<input type="email" id="email" placeholder="name@example.com" />
```

### Icon Button Without Accessible Name
```jsx
// ❌ WRONG - No accessible name
<button onClick={closeDialog}>
  <XIcon />
</button>

// ✅ CORRECT - aria-label provides name
<button aria-label="Close dialog" onClick={closeDialog}>
  <XIcon />
</button>
```

### Conflicting Naming Methods
```jsx
// ⚠️ CONFUSING - aria-label overrides visible text
<button aria-label="Submit form" onClick={handleSubmit}>
  Save Changes
</button>
// Visible: "Save Changes"
// Announced: "Submit form" (confusing!)

// ✅ CORRECT - Accessible name matches visible text
<button onClick={handleSubmit}>
  Save Changes
</button>
```

### Missing Form Labels
```jsx
// ❌ WRONG - No label association
<div>
  <span>Email</span>
  <input type="email" />
</div>

// ✅ CORRECT - Explicit label association
<label htmlFor="email">Email</label>
<input type="email" id="email" />
```

### Generic Link Text
```jsx
// ❌ WRONG - Generic, no context
<a href="/report.pdf">Click here</a>

// ✅ CORRECT - Descriptive link text
<a href="/report.pdf">Download Q4 2025 Sales Report (PDF)</a>

// ✅ ACCEPTABLE - Generic text with aria-label
<a href="/report.pdf" aria-label="Download Q4 2025 Sales Report">
  Download
</a>
```

## Decision Tree

```
Does element need accessible name?
├─ Yes → Continue
└─ No → Done (e.g., decorative image with alt="")

Is there visible text that should be the accessible name?
├─ Yes → Use aria-labelledby to reference visible text
└─ No → Continue

Is this a form control?
├─ Yes → Use <label htmlFor="id">
└─ No → Continue

Is there appropriate child content?
├─ Yes → Use child content (button text, link text, heading text)
└─ No → Continue

Is this an icon-only button or similar?
├─ Yes → Use aria-label
└─ No → Continue

Can you add visible text?
├─ Yes → Add visible text, use child content or aria-labelledby
└─ No → Use aria-label as last resort
```

## Resources

- **WCAG 2.4.6 Headings and Labels**: https://www.w3.org/WAI/WCAG22/Understanding/headings-and-labels
- **WCAG 4.1.2 Name, Role, Value**: https://www.w3.org/WAI/WCAG22/Understanding/name-role-value
- **ARIA Accessible Name Computation**: https://www.w3.org/TR/accname-1.2/
- **Using ARIA Labels**: https://www.w3.org/TR/using-aria/#label-support
