---
trigger: glob
globs: ["**/*.tsx", "**/*.jsx"]
---

# Accessibility Core Requirements

Auto-activated when working with React components. Provides critical accessibility constraints following WCAG 2.2 Level AA standards.

## Five Rules of ARIA

1. **Use native HTML first** - Prefer `<button>` over `<div role="button">`
2. **Don't override native semantics** - Wrap instead of replacing (e.g., don't put `role="button"` on a `<button>`)
3. **All interactive ARIA controls must be keyboard accessible** - A role is a promise to implement expected keyboard behavior
4. **Never hide focusable elements with aria-hidden="true"** - Creates invisible keyboard traps
5. **No ARIA is better than bad ARIA** - Incorrect ARIA creates worse experiences than no ARIA

## Three-Tier Boundaries

### ✅ Always Do

- Use semantic HTML elements (`<button>`, `<nav>`, `<main>`, `<article>`, `<section>`, `<header>`, `<footer>`)
- Provide alt text for meaningful images, use `alt=""` for decorative images
- Maintain visible focus indicators (never remove without visible replacement)
- Use `<label>` elements for all form controls (associated via `htmlFor` in React)
- Ensure 4.5:1 color contrast for normal text, 3:1 for large text (18pt+)
- Include only one element per composite widget in tab sequence (use roving tabindex for others)
- Preserve semantic HTML structure (don't break lists, tables, headings with wrapper divs)

### ⚠️ Ask First

- Custom ARIA implementations beyond native HTML capabilities
- Removing or customizing default focus styles
- Creating custom composite widgets (tabs, menus, grids, trees)
- Implementing roving tabindex patterns
- Using `aria-live` regions for dynamic content
- Creating custom form controls that deviate from native behavior

### 🚫 Never Do

- Use `<div onClick>` or `<span onClick>` instead of `<button>`
- Remove focus indicators without providing visible replacement
- Use `aria-hidden="true"` on focusable elements
- Create keyboard traps without escape mechanism (Escape key must work)
- Use placeholder as only form label
- Override native semantics unnecessarily (e.g., `<button role="link">`)
- Skip heading levels (h1 → h3 without h2)
- Use color alone to convey information

## Critical Anti-Patterns

### Div/Span Buttons
```jsx
// ❌ NEVER - No keyboard access, no semantic meaning
<div onClick={handleClick}>Click me</div>

// ✅ ALWAYS - Keyboard accessible, semantic, announced correctly
<button onClick={handleClick}>Click me</button>
```

### Missing Alt Text
```jsx
// ❌ NEVER - Screen readers cannot describe image
<img src="chart.png" />

// ✅ ALWAYS - Meaningful alt text
<img src="chart.png" alt="Sales increased 25% in Q4" />

// ✅ ALWAYS - Empty alt for decorative images
<img src="decorative-border.png" alt="" />
```

### Poor Color Contrast
```jsx
// ❌ NEVER - Insufficient contrast (2.5:1)
<p className="text-gray-400">Important text</p>

// ✅ ALWAYS - Sufficient contrast (4.5:1+)
<p className="text-gray-900">Important text</p>
```

### Keyboard Traps
```jsx
// ❌ NEVER - User cannot escape modal
<div role="dialog">
  <button onClick={close}>Close</button>
  {/* Missing Escape key handler */}
</div>

// ✅ ALWAYS - Escape key closes modal
<div role="dialog" onKeyDown={(e) => e.key === 'Escape' && close()}>
  <button onClick={close}>Close</button>
</div>
```

### Missing Form Labels
```jsx
// ❌ NEVER - No label association
<input type="text" placeholder="Enter name" />

// ✅ ALWAYS - Explicit label association
<label htmlFor="name">Name</label>
<input type="text" id="name" />
```

### Incorrect ARIA
```jsx
// ❌ NEVER - Role without keyboard behavior
<div role="button" onClick={handleClick}>Click</div>

// ✅ ALWAYS - Complete implementation or use native element
<button onClick={handleClick}>Click</button>

// ✅ IF CUSTOM NEEDED - Role + keyboard + focus
<div 
  role="button" 
  tabIndex={0}
  onClick={handleClick}
  onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && handleClick()}
>
  Click
</div>
```

### Inaccessible Custom Components
```jsx
// ❌ NEVER - Custom select without keyboard support
<div className="custom-select" onClick={toggle}>
  {selectedOption}
</div>

// ✅ ALWAYS - Use native first
<select value={selected} onChange={handleChange}>
  <option value="1">Option 1</option>
</select>

// ✅ IF CUSTOM NEEDED - Follow APG pattern completely
// See accessible-component-design skill for complete implementation
```

### Focus Indicator Removal
```css
/* ❌ NEVER - Removes focus indicators */
button:focus {
  outline: none;
}

/* ✅ ALWAYS - Provide visible alternative */
button:focus {
  outline: 2px solid blue;
  outline-offset: 2px;
}

/* ✅ ACCEPTABLE - Custom focus style */
button:focus-visible {
  box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.5);
}
```

## Keyboard Navigation Conventions

### Tab Sequence
- **Tab**: Move forward to next focusable element
- **Shift+Tab**: Move backward to previous focusable element
- **Rule**: Only ONE element per composite widget in tab sequence

### Within Composites (Arrow Keys)
- **Arrow keys**: Navigate INSIDE composite widgets (tabs, menus, radio groups)
- **Tab/Shift+Tab**: EXIT composite to next/previous component
- **Pattern**: Roving tabindex (only focused element has `tabIndex={0}`, others have `tabIndex={-1}`)

### Activation
- **Enter**: Activate buttons, links, submit forms
- **Space**: Activate buttons, toggle checkboxes
- **Enter/Space**: Both should work for buttons

### Escape
- **Escape**: Close dialogs, dismiss menus, cancel operations
- **Rule**: ALWAYS provide Escape key handler for modals and popups

## Accessible Naming Priority Hierarchy

When multiple naming methods exist, assistive technology uses this priority order:

1. **`aria-labelledby`** (highest precedence) - References visible text by ID
   ```jsx
   <button aria-labelledby="delete-label">
     <span id="delete-label">Delete</span>
   </button>
   ```

2. **`aria-label`** - Invisible label when no visible text appropriate
   ```jsx
   <button aria-label="Close dialog">
     <XIcon />
   </button>
   ```

3. **Native HTML** - `<label>`, `<caption>`, `<legend>`, `<figcaption>`
   ```jsx
   <label htmlFor="email">Email</label>
   <input type="email" id="email" />
   ```

4. **Child content** - Text content of element
   ```jsx
   <button>Submit Form</button>
   ```

5. **Fallback** - `title`, `placeholder` (avoid as primary label)
   ```jsx
   {/* ⚠️ Acceptable only as supplementary, not primary label */}
   <input type="text" title="Enter your email address" />
   ```

## Quick Reference: Common Patterns

### Buttons
```jsx
// Native button (preferred)
<button onClick={handleClick}>Action</button>

// Icon button (needs accessible name)
<button aria-label="Delete item" onClick={handleDelete}>
  <TrashIcon />
</button>
```

### Form Controls
```jsx
// Text input
<label htmlFor="email">Email</label>
<input type="email" id="email" required aria-required="true" />

// Checkbox
<label>
  <input type="checkbox" checked={agreed} onChange={handleChange} />
  I agree to terms
</label>

// Radio group
<fieldset>
  <legend>Choose size</legend>
  <label><input type="radio" name="size" value="s" /> Small</label>
  <label><input type="radio" name="size" value="m" /> Medium</label>
  <label><input type="radio" name="size" value="l" /> Large</label>
</fieldset>
```

### Links
```jsx
// Descriptive link text
<a href="/about">About our company</a>

// Link with context
<a href="/report.pdf">
  Download Q4 report <span className="sr-only">(PDF, 2MB)</span>
</a>
```

### Images
```jsx
// Informative image
<img src="chart.png" alt="Sales increased 25% in Q4 2025" />

// Decorative image
<img src="border.png" alt="" />

// Complex image (use longdesc or adjacent text)
<figure>
  <img src="complex-chart.png" alt="Quarterly sales comparison" />
  <figcaption>
    Detailed description: Q1 sales were $1M, Q2 increased to $1.2M...
  </figcaption>
</figure>
```

### Headings
```jsx
// Proper hierarchy
<h1>Page Title</h1>
<h2>Section Title</h2>
<h3>Subsection Title</h3>
{/* Never skip levels: h1 → h3 */}
```

### Landmarks
```jsx
// Page structure
<header>
  <nav aria-label="Main navigation">...</nav>
</header>
<main>
  <article>...</article>
  <aside>...</aside>
</main>
<footer>...</footer>
```

## Component Library Guidance

### ShadCN/Radix UI (Repository Standard)
- These components handle keyboard navigation, focus management, and ARIA automatically
- Use for complex interactive components: Dialog, Combobox, Select, Tabs, Accordion
- No additional ARIA needed when using these components correctly
- Focus on providing proper labels and content

### When Building Custom Components
- Start with semantic HTML
- Check if ShadCN/Radix has a component first
- If custom needed, follow W3C ARIA Authoring Practices Guide (APG) patterns
- Use `accessible-component-design` skill for complete implementation guidance

## Testing Requirements

Before submitting PR:
- [ ] Manual keyboard test (Tab through interface, verify all interactive elements reachable)
- [ ] Focus indicators visible throughout
- [ ] Screen reader test (verify announcements make sense)
- [ ] Color contrast check (use browser DevTools)
- [ ] Use accessible queries in tests (`getByRole`, `getByLabelText`)

## When to Use Skills

- **Complex component design**: Use `accessible-component-design` skill
- **Custom ARIA implementation**: Use `aria-patterns` skill
- **Comprehensive audit**: Use `/accessibility-audit` workflow
- **PR review**: Use `/component-a11y-review` workflow

## Resources

- **WCAG 2.2**: https://www.w3.org/TR/WCAG22/
- **ARIA Authoring Practices Guide**: https://www.w3.org/WAI/ARIA/apg/
- **Using ARIA**: https://www.w3.org/TR/using-aria/
- **WebAIM**: https://webaim.org/
