# TDD-Refactor Workflow

## Purpose
Improve code quality, remove duplication, and enhance design while keeping all tests green.

## Trigger
- After `tdd-green` with all tests passing
- Code smells detected
- Duplication exists
- Design can be improved

## Prerequisites
- All tests passing (green)
- Code successfully implements required behavior
- Understanding of refactoring techniques

## Workflow Steps

### Step 1: Identify Refactoring Opportunities
```
Review code for:

DUPLICATION:
- [ ] Repeated code blocks
- [ ] Similar methods that could be unified
- [ ] Copy-pasted logic

NAMING:
- [ ] Unclear variable names
- [ ] Method names that don't describe behavior
- [ ] Magic numbers without constants

STRUCTURE:
- [ ] Long methods (>20 lines)
- [ ] Deep nesting (>3 levels)
- [ ] Large classes (>200 lines)
- [ ] Missing abstractions

SOLID VIOLATIONS:
- [ ] Class doing too much (SRP)
- [ ] Rigid dependencies (DIP)
- [ ] Large interfaces (ISP)
```

### Step 2: Prioritize Refactorings
```
Order by impact and safety:

HIGH PRIORITY (Safe, high impact):
1. Rename for clarity
2. Extract constants
3. Remove dead code
4. Simplify conditionals

MEDIUM PRIORITY (Moderate risk):
5. Extract methods
6. Extract classes
7. Introduce parameters

LOW PRIORITY (Higher risk, do carefully):
8. Change method signatures
9. Restructure inheritance
10. Modify public APIs
```

### Step 3: Apply ONE Refactoring
```
IMPORTANT: One change at a time!

1. Make a single, focused change
2. Run all tests immediately
3. Verify tests still pass
4. Commit if green
5. Repeat for next refactoring
```

### Step 4: Run Tests After Each Change
```
After EVERY refactoring step:

$ dotnet test        # C#
$ pytest            # Python
$ npm test          # TypeScript

If ANY test fails:
- STOP immediately
- Undo the change
- Understand why it broke
- Try a smaller step
```

### Step 5: Review Refactored Code
```
Verify improvements:
- [ ] Code is more readable
- [ ] Duplication is reduced
- [ ] Names are clearer
- [ ] Structure is simpler
- [ ] All tests still pass
- [ ] No new functionality added
```

### Step 6: Decide Next Action
```
Choose one:
A) More refactoring needed → Repeat from Step 1
B) Code is clean enough → Continue to next test
C) All tests implemented → Feature complete
```

## Common Refactoring Patterns

### Extract Method
```csharp
// Before
public void ProcessOrder(Order order)
{
    // Validate
    if (order.Items.Count == 0) throw new Exception("Empty");
    if (order.Total < 0) throw new Exception("Invalid total");
    
    // Process
    // ... more code
}

// After
public void ProcessOrder(Order order)
{
    ValidateOrder(order);
    // Process
}

private void ValidateOrder(Order order)
{
    if (order.Items.Count == 0) throw new Exception("Empty");
    if (order.Total < 0) throw new Exception("Invalid total");
}
```

### Replace Magic Numbers
```python
# Before
def calculate_shipping(weight):
    if weight > 50:
        return weight * 2.5
    return weight * 1.5

# After
MAX_STANDARD_WEIGHT = 50
HEAVY_RATE_PER_KG = 2.5
STANDARD_RATE_PER_KG = 1.5

def calculate_shipping(weight):
    if weight > MAX_STANDARD_WEIGHT:
        return weight * HEAVY_RATE_PER_KG
    return weight * STANDARD_RATE_PER_KG
```

### Simplify Conditional
```typescript
// Before
function getDiscount(customer: Customer): number {
    if (customer.type === "premium") {
        if (customer.years > 5) {
            return 0.2;
        } else {
            return 0.1;
        }
    } else {
        if (customer.years > 5) {
            return 0.05;
        } else {
            return 0;
        }
    }
}

// After
function getDiscount(customer: Customer): number {
    const isPremium = customer.type === "premium";
    const isLoyal = customer.years > 5;
    
    if (isPremium && isLoyal) return 0.2;
    if (isPremium) return 0.1;
    if (isLoyal) return 0.05;
    return 0;
}
```

### Extract Class
```csharp
// Before: Order doing too much
public class Order
{
    public List<Item> Items { get; set; }
    public decimal CalculateSubtotal() { }
    public decimal CalculateTax() { }
    public decimal CalculateShipping() { }
    public decimal CalculateTotal() { }
    public void SendConfirmationEmail() { }
    public void GenerateInvoicePdf() { }
}

// After: Separated concerns
public class Order
{
    public List<Item> Items { get; set; }
}

public class OrderPricingService
{
    public decimal CalculateSubtotal(Order order) { }
    public decimal CalculateTax(Order order) { }
    public decimal CalculateShipping(Order order) { }
    public decimal CalculateTotal(Order order) { }
}

public class OrderNotificationService
{
    public void SendConfirmationEmail(Order order) { }
    public void GenerateInvoicePdf(Order order) { }
}
```

## Quality Checks
- [ ] All tests pass after each change
- [ ] No new functionality introduced
- [ ] Code is measurably cleaner
- [ ] Refactoring improves readability
- [ ] Changes are committed incrementally

## Output
- Cleaner, more maintainable code
- All tests still passing
- Ready for next TDD cycle or completion

## Next Workflow
→ `tdd-red`: Start next test case from plan
→ OR complete if all tests implemented

## Anti-Patterns to Avoid
```
❌ Refactoring and adding features simultaneously
❌ Making multiple changes before testing
❌ Skipping tests during refactoring
❌ Refactoring code that doesn't have tests
❌ Premature abstraction
❌ Over-engineering for future requirements
```

## When to Stop Refactoring
```
Stop when:
✓ Code clearly expresses intent
✓ No obvious duplication remains
✓ Methods are reasonably sized
✓ Names are descriptive
✓ Further changes have diminishing returns

Continue if:
✗ Code smells are obvious
✗ Duplication exists
✗ Understanding requires effort
✗ Changes in one place require changes elsewhere
```
