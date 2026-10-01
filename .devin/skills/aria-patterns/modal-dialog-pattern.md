# Modal Dialog Pattern

Complete implementation guide for accessible modal dialogs following W3C APG pattern.

## Pattern Overview

**Modal Dialog:** An overlay that requires user interaction before returning to main content. Focus is trapped inside the dialog until dismissed.

**Use when:**
- Requiring user decision before proceeding
- Displaying critical information
- Collecting input that interrupts workflow

**Do NOT use for:**
- Non-critical notifications (use toast/alert instead)
- Content that doesn't require interruption (use popover instead)

## Required ARIA Attributes

### Container

```jsx
<div 
  role="dialog"
  aria-modal="true"
  aria-labelledby="dialog-title"
  aria-describedby="dialog-description"
>
  <h2 id="dialog-title">Dialog Title</h2>
  <p id="dialog-description">Dialog description</p>
</div>
```

**`role="dialog"`** - Identifies element as dialog
**`aria-modal="true"`** - Indicates modal behavior (background inert)
**`aria-labelledby`** - References title element by ID
**`aria-describedby`** - References description element by ID (optional)

## Required Keyboard Behavior

### Tab/Shift+Tab
- Cycles through focusable elements inside dialog
- Wraps from last to first element
- Wraps from first to last element

### Escape
- Closes dialog
- Returns focus to trigger element

### Enter/Space
- Activates buttons inside dialog
- Does NOT close dialog (unless button explicitly closes)

## Focus Management

### On Open
1. Store reference to trigger element
2. Move focus inside dialog (to first focusable element or dialog itself)
3. Trap focus within dialog

### On Close
1. Close dialog
2. Restore focus to trigger element

### Focus Trap Implementation

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

// Trap Tab within dialog
const handleKeyDown = (e: React.KeyboardEvent) => {
  if (e.key === 'Escape') {
    onClose();
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

## Complete React Implementation

```tsx
import { useRef, useEffect } from 'react';

interface ModalDialogProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  children: React.ReactNode;
}

export function ModalDialog({ 
  isOpen, 
  onClose, 
  title, 
  description,
  children 
}: ModalDialogProps) {
  const modalRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLElement | null>(null);

  // Focus management
  useEffect(() => {
    if (isOpen) {
      // Store trigger element
      triggerRef.current = document.activeElement as HTMLElement;
      
      // Move focus inside dialog
      modalRef.current?.focus();
      
      // Prevent body scroll
      document.body.style.overflow = 'hidden';
    } else {
      // Restore focus to trigger
      if (triggerRef.current) {
        triggerRef.current.focus();
      }
      
      // Restore body scroll
      document.body.style.overflow = '';
    }
    
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  // Keyboard handling
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      onClose();
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

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black/50 z-40"
        onClick={onClose}
        aria-hidden="true"
      />
      
      {/* Dialog */}
      <div
        ref={modalRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="dialog-title"
        aria-describedby={description ? "dialog-description" : undefined}
        tabIndex={-1}
        onKeyDown={handleKeyDown}
        className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-white rounded-lg shadow-xl p-6 z-50 max-w-md w-full focus:outline-none"
      >
        {/* Title */}
        <div className="flex items-center justify-between mb-4">
          <h2 id="dialog-title" className="text-xl font-semibold">
            {title}
          </h2>
          <button
            onClick={onClose}
            aria-label="Close dialog"
            className="p-1 rounded hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        {/* Description */}
        {description && (
          <p id="dialog-description" className="text-gray-700 mb-4">
            {description}
          </p>
        )}
        
        {/* Content */}
        <div>
          {children}
        </div>
      </div>
    </>
  );
}
```

## Usage Examples

### Confirmation Dialog

```tsx
function DeleteConfirmation() {
  const [isOpen, setIsOpen] = useState(false);

  const handleDelete = () => {
    // Perform deletion
    setIsOpen(false);
  };

  return (
    <>
      <button onClick={() => setIsOpen(true)}>
        Delete Item
      </button>

      <ModalDialog
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        title="Confirm Deletion"
        description="This action cannot be undone. Are you sure you want to delete this item?"
      >
        <div className="flex gap-3 justify-end">
          <button onClick={() => setIsOpen(false)}>
            Cancel
          </button>
          <button onClick={handleDelete} className="bg-red-600 text-white">
            Delete
          </button>
        </div>
      </ModalDialog>
    </>
  );
}
```

### Form Dialog

```tsx
function AddUserDialog() {
  const [isOpen, setIsOpen] = useState(false);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Submit form
    setIsOpen(false);
  };

  return (
    <>
      <button onClick={() => setIsOpen(true)}>
        Add User
      </button>

      <ModalDialog
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        title="Add New User"
      >
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label htmlFor="name">Name</label>
            <input
              type="text"
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </div>
          
          <div className="mb-4">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          
          <div className="flex gap-3 justify-end">
            <button type="button" onClick={() => setIsOpen(false)}>
              Cancel
            </button>
            <button type="submit" className="bg-blue-600 text-white">
              Add User
            </button>
          </div>
        </form>
      </ModalDialog>
    </>
  );
}
```

### Information Dialog

```tsx
function InfoDialog() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <button onClick={() => setIsOpen(true)}>
        Show Info
      </button>

      <ModalDialog
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        title="Important Information"
        description="Please read the following information carefully."
      >
        <div className="mb-4">
          <p className="text-gray-700">
            Your account will be upgraded to premium status. This includes:
          </p>
          <ul className="list-disc list-inside mt-2 text-gray-700">
            <li>Unlimited storage</li>
            <li>Priority support</li>
            <li>Advanced features</li>
          </ul>
        </div>
        
        <div className="flex justify-end">
          <button onClick={() => setIsOpen(false)} className="bg-blue-600 text-white">
            Got it
          </button>
        </div>
      </ModalDialog>
    </>
  );
}
```

## Advanced Features

### Initial Focus on Specific Element

```tsx
const firstInputRef = useRef<HTMLInputElement>(null);

useEffect(() => {
  if (isOpen) {
    triggerRef.current = document.activeElement as HTMLElement;
    // Focus specific element instead of dialog container
    setTimeout(() => {
      firstInputRef.current?.focus();
    }, 0);
  }
}, [isOpen]);

return (
  <div role="dialog" aria-modal="true">
    <input ref={firstInputRef} type="text" />
  </div>
);
```

### Backdrop Click to Close

```tsx
const handleBackdropClick = (e: React.MouseEvent) => {
  // Only close if clicking backdrop, not dialog content
  if (e.target === e.currentTarget) {
    onClose();
  }
};

return (
  <div 
    className="fixed inset-0 flex items-center justify-center"
    onClick={handleBackdropClick}
  >
    <div role="dialog" aria-modal="true">
      {/* Dialog content */}
    </div>
  </div>
);
```

### Prevent Close on Unsaved Changes

```tsx
const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

const handleClose = () => {
  if (hasUnsavedChanges) {
    if (confirm('You have unsaved changes. Are you sure you want to close?')) {
      onClose();
    }
  } else {
    onClose();
  }
};

const handleKeyDown = (e: React.KeyboardEvent) => {
  if (e.key === 'Escape') {
    handleClose();
    return;
  }
  // ... rest of keyboard handling
};
```

### Nested Dialogs

```tsx
// Parent dialog
function ParentDialog() {
  const [isChildOpen, setIsChildOpen] = useState(false);

  return (
    <ModalDialog isOpen={isOpen} onClose={onClose} title="Parent Dialog">
      <button onClick={() => setIsChildOpen(true)}>
        Open Child Dialog
      </button>
      
      {/* Child dialog */}
      <ModalDialog 
        isOpen={isChildOpen} 
        onClose={() => setIsChildOpen(false)}
        title="Child Dialog"
      >
        <p>This is a nested dialog</p>
      </ModalDialog>
    </ModalDialog>
  );
}
```

## Common Mistakes

### Not Trapping Focus

```tsx
// ❌ WRONG - Focus can escape dialog
<div role="dialog" aria-modal="true">
  <button>Close</button>
</div>

// ✅ CORRECT - Focus trapped inside
<div 
  role="dialog" 
  aria-modal="true"
  onKeyDown={handleKeyDown}
>
  <button>Close</button>
</div>
```

### Not Restoring Focus

```tsx
// ❌ WRONG - Focus lost when dialog closes
const handleClose = () => {
  setIsOpen(false);
};

// ✅ CORRECT - Focus restored to trigger
useEffect(() => {
  if (!isOpen && triggerRef.current) {
    triggerRef.current.focus();
  }
}, [isOpen]);
```

### Missing Escape Key Handler

```tsx
// ❌ WRONG - No keyboard way to close
<div role="dialog" aria-modal="true">
  <button onClick={onClose}>Close</button>
</div>

// ✅ CORRECT - Escape closes dialog
<div 
  role="dialog" 
  aria-modal="true"
  onKeyDown={(e) => e.key === 'Escape' && onClose()}
>
  <button onClick={onClose}>Close</button>
</div>
```

### Missing aria-labelledby

```tsx
// ❌ WRONG - No accessible name
<div role="dialog" aria-modal="true">
  <h2>Dialog Title</h2>
</div>

// ✅ CORRECT - Labeled by title
<div role="dialog" aria-modal="true" aria-labelledby="dialog-title">
  <h2 id="dialog-title">Dialog Title</h2>
</div>
```

### Backdrop Not aria-hidden

```tsx
// ❌ WRONG - Backdrop announced by screen readers
<div className="backdrop">
  <div role="dialog">...</div>
</div>

// ✅ CORRECT - Backdrop hidden from assistive tech
<div className="backdrop" aria-hidden="true">
  <div role="dialog">...</div>
</div>
```

## Testing Checklist

- [ ] Focus moves inside dialog on open
- [ ] Tab cycles through focusable elements
- [ ] Shift+Tab cycles backward
- [ ] Tab wraps from last to first element
- [ ] Shift+Tab wraps from first to last element
- [ ] Escape closes dialog
- [ ] Focus returns to trigger on close
- [ ] Dialog has accessible name (aria-labelledby or aria-label)
- [ ] Screen reader announces dialog role
- [ ] Background content inert (cannot interact with)
- [ ] Body scroll prevented when dialog open

## Resources

- **W3C APG Dialog Pattern**: https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/
- **WCAG 2.4.3 Focus Order**: https://www.w3.org/WAI/WCAG22/Understanding/focus-order
- **ARIA Dialog Role**: https://www.w3.org/TR/wai-aria-1.2/#dialog
