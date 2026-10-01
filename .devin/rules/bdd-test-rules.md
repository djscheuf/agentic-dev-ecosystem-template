---
trigger: glob
globs: src/tests/**/*.cs
---
# BDD + Given-When-Then Testing Standards

> **⚠️ MANDATORY:** All test files MUST follow this pattern

**Reference:** `tests/[ProjectName].Tests/Repositories/[ClassName].Tests.cs`

---

## Test Class Structure

```csharp
public class [ClassName]Tests : IDisposable
{
    // Dependencies
    private readonly [DbContext] _context;
    private readonly [Repository/Handler/Service] _systemUnderTest;
    
    // State Management
    private List<[Entity]> _known[Entities];
    private [ResultType] _result;
    private CancellationTokenSource _cancellationToken;
    private Exception? _exception;
    
    // Constructor
    public [ClassName]Tests()
    {
        _context = [DbContextFactory].CreateInMemoryContext();
        _systemUnderTest = new [Type](_context);
        _result = default([ResultType])!;
        _known[Entities] = new List<[Entity]>();
        _cancellationToken = new CancellationTokenSource();
        _exception = null;
    }
    
    public void Dispose()
    {
        _context.Database.EnsureDeleted();
        _context.Dispose();
    }
    
    // TESTS FIRST
    #region [MethodName] Tests
    
    [Fact]
    public async Task [Method]_[Scenario]_[ExpectedBehavior]()
    {
        await Given_[Setup]();
        
        await When_[Operation]();
        
        Then_[Assertion]();
    }
    
    #endregion
    
    // When Method - ALWAYS use try-catch
    private async Task When_[OperationName]()
    {
        try
        {
            _result = await _systemUnderTest.[Method](_cancellationToken.Token);
        }
        catch (Exception ex)
        {
            _result = [safe_default];
            _exception = ex;
        }
    }
    
    #region Given
    
    private async Task Given_[ScenarioDescription]()
    {
        // Setup test data, populate _known[Entities], save to context
    }
    
    #endregion
    
    #region Then
    
    private void Then_[ExpectedOutcome]()
    {
        // FluentAssertions-based assertions
    }
    
    #endregion
}
```

---

## Naming Conventions

### Test Class
`[ClassName]Tests` - e.g., `EntityRepositoryGetAllTests`

### Given Methods
`Given_[State_Description]()` - Use underscores, UPPERCASE for emphasis
- `Given_Some_[Entities]()`
- `Given_NO_[Entities]()`
- `Given_WILL_Cancel_Request()`
- `Given_Search_Name(string name)`

### When Methods
`When_[Operation_Description]()` - Use present participle (-ing)
- `When_Getting_All_[Entities]()`
- `When_Creating_[Entity]()`
- `When_Searching_By_Name()`

### Then Methods
`Then_[Expected_Outcome]()` - Be declarative
- `Then_Get_All_Known_[Entities]()`
- `Then_Get_Empty_List()`
- `Then_Result_Is_Null()`
- `Then_Throws<TException>()`
- `Then_Result_Matches_Known_Entity(int index)`

### Test Methods
`[MethodName]_[Scenario]_[ExpectedBehavior]`
- `GetAllAsync_When[Entities]Exist_ReturnsAll[Entities]OrderedBy[SortProperty]`
- `GetByIdAsync_WhenNotFound_ReturnsNull`
- `Update[Entity]_When[InvalidStatus]_ThrowsInvalidOperationException`

---

## State Management Fields

```csharp
// System Under Test
private readonly [Repository/Handler/Service] _systemUnderTest;

// Test Data Tracking
private List<[Entity]> _known[Entities];
private [Entity]? _knownEntity;

// Result Capture
private [ResultType] _result;
private List<[Entity]> _resultList;

// Infrastructure
private CancellationTokenSource _cancellationToken;
private Exception? _exception;
```

---

## Given Methods

```csharp
// Setup with data
private async Task Given_Some_[Entities]()
{
    _known[Entities] = new List<[Entity]>
    {
        new [Entity] { Id = 1, Name = "Test 1", [SortProperty] = 1 },
        new [Entity] { Id = 2, Name = "Test 2", [SortProperty] = 2 }
    };
    await _context.[Entities].AddRangeAsync(_known[Entities]);
    await _context.SaveChangesAsync();
}

// Empty state
private async Task Given_NO_[Entities]()
{
    _known[Entities].Clear();
    _context.[Entities].RemoveRange(_context.[Entities]);
    await _context.SaveChangesAsync();
}

// Cancellation
private void Given_WILL_Cancel_Request()
{
    _cancellationToken.Cancel();
}

// Parameter setup
private void Given_Search_Parameter(string value)
{
    _searchParameter = value;
}
```

---

## When Methods

**ALWAYS use try-catch pattern:**

```csharp
private async Task When_[OperationName]()
{
    try
    {
        _result = await _systemUnderTest.[MethodName]([parameters], _cancellationToken.Token);
    }
    catch (Exception ex)
    {
        _result = [safe_default];  // Prevent null reference
        _exception = ex;
    }
}
```

**Examples:**

```csharp
// Collection result
private async Task When_Getting_All_[Entities]()
{
    try
    {
        _result = await _repository.GetAllAsync(_cancellationToken.Token);
    }
    catch (Exception ex)
    {
        _result = new List<[Entity]>();
        _exception = ex;
    }
}

// Single entity
private async Task When_Getting_[Entity]_By_Id()
{
    try
    {
        _result = await _repository.GetByIdAsync(_entityId, _cancellationToken.Token);
    }
    catch (Exception ex)
    {
        _result = null;
        _exception = ex;
    }
}
```

---

## Then Methods

```csharp
// Collection validation
private void Then_Get_All_Known_[Entities]()
{
    _result.Should().NotBeNull();
    _result.Should().HaveCount(_known[Entities].Count);
}

// Empty result
private void Then_Get_Empty_List()
{
    _result.Should().NotBeNull();
    _result.Should().BeEmpty();
}

// Exception validation
private void Then_Throws<TException>() where TException : Exception
{
    _exception.Should().BeOfType<TException>();
}

// Ordering validation
private void Then_The_Result_Is_Ordered_By_[SortProperty]()
{
    for (int i = 0; i < _result.Count; i++)
    {
        _result[i].[SortProperty].Should().Be(i + 1);
    }
}

// Entity match
private void Then_Result_Matches_Known_Entity(int index)
{
    _result.Should().NotBeNull();
    _result!.Id.Should().Be(_known[Entities][index].Id);
    _result.Name.Should().Be(_known[Entities][index].Name);
}

// Repository verification (NSubstitute)
private void Then_Repository_Was_Called()
{
    _mockRepository.Received(1).GetAllAsync(Arg.Any<CancellationToken>());
}
```

---

## Region Organization

**TESTS FIRST - Order:**

1. Fields (no region)
2. Constructor (no region)
3. Dispose (no region)
4. **Test methods** in `#region [MethodName] Tests`
5. When method(s) (no region)
6. Given methods in `#region Given`
7. Then methods in `#region Then`

---

## Testing Tools

### Required Libraries
- **xUnit** - Test framework
- **FluentAssertions** - Use `.Should()` syntax
- **NSubstitute** - Mocking (unit tests)
- **EF Core InMemory** - In-memory database (integration tests)

### FluentAssertions

```csharp
// Collections
_result.Should().NotBeNull();
_result.Should().HaveCount(3);
_result.Should().BeEmpty();
_result.Should().Contain(x => x.Id == 1);

// Equality
_result.Id.Should().Be(expectedId);
_result.Name.Should().Be("Expected Name");

// Nullability
_result.Should().BeNull();
_result.Should().NotBeNull();

// Exceptions
_exception.Should().BeOfType<ArgumentNullException>();

// Comparisons
_result.Count.Should().BeGreaterThan(0);

// Booleans
_result.IsActive.Should().BeTrue();
```

### NSubstitute

```csharp
// Setup mock
private readonly IRepository _mockRepository;

public HandlerTests()
{
    _mockRepository = Substitute.For<IRepository>();
}

// Configure return
private void Given_Repository_Returns_Entity()
{
    _mockRepository.GetByIdAsync(Arg.Any<int>(), Arg.Any<CancellationToken>())
        .Returns(_knownEntity);
}

// Verify interaction
private void Then_Repository_Was_Called()
{
    _mockRepository.Received(1).GetByIdAsync(
        Arg.Is<int>(x => x == _knownEntity.Id),
        Arg.Any<CancellationToken>());
}
```

---

## Test Builders

```csharp
public class [EntityBuilder]
{
    private int _id = 1;
    private [EntityStatus] _status = [EntityStatus].Default;
    
    public [EntityBuilder] WithId(int id) { _id = id; return this; }
    public [EntityBuilder] AsActive() { _status = [EntityStatus].Active; return this; }
    public [Entity] Build() => new() { Id = _id, Status = _status };
}

// Usage
private async Task Given_An_Active_[Entity]()
{
    _knownEntity = new [EntityBuilder]().AsActive().Build();
    await _context.[Entities].AddAsync(_knownEntity);
    await _context.SaveChangesAsync();
}
```

---

## Coverage Requirements

- **Unit tests:** 80% line coverage minimum
- **Critical business logic:** 100% branch coverage (validation, authorization, business rules)
- **Command/Query handlers:** 100% coverage

```bash
dotnet test --collect:"XPlat Code Coverage"
reportgenerator -reports:"**/coverage.cobertura.xml" -targetdir:"coveragereport" -reporttypes:Html
```

---

## Forbidden Practices

- No test interdependence
- No `Thread.Sleep()` in async tests
- No testing private methods
- No ignoring flaky tests
- No mocking what you don't own
- No assertions in When methods
- No multiple Acts per test
- No shared mutable state between tests
- No hardcoded dates (use `DateTime.UtcNow.AddDays(30)`)
- No generic assertions (use FluentAssertions)
- No copy-paste test code (use Given/When/Then helpers)
- No complex logic in tests (if/else, loops)
- No meaningless test names
