---
trigger: glob
globs: src/**/*.cs
---
# C# Coding Standards

## General Principles

- Follow Microsoft's C# coding conventions and .NET design guidelines
- Prefer clarity over cleverness; code should be self-documenting
- Use the latest stable C# language features appropriate for the target framework
- Apply SOLID principles consistently

## Naming Conventions

**Casing:**
- **PascalCase**: Classes, interfaces, structs, enums, methods, properties, events, namespaces
- **camelCase**: Local variables, parameters, private fields with `_` prefix
- **UPPER_CASE**: Public constants only

**Patterns:**
```csharp
public interface IRepository { }                    // Interfaces: 'I' prefix
public async Task<User> GetUserAsync(int id) { }   // Async: 'Async' suffix
public bool IsActive { get; set; }                  // Booleans: is/has/can/should
private readonly ILogger _logger;                   // Private fields: underscore
```

## File Structure

**Organization:**
- One primary type per file; filename matches type name
- Using directives: System → third-party → project namespaces
- File-scoped namespaces (C# 10+)

**Class Member Order:**
1. Constants/static readonly
2. Private fields
3. Constructors
4. Public properties
5. Public methods
6. Private methods
7. Nested types

## Modern C# Syntax

```csharp
// Target-typed new
private readonly List<string> _items = new();

// Pattern matching
if (obj is string text && text.Length > 0) { }

// Switch expressions
var result = status switch
{
    Status.Active => "Running",
    Status.Inactive => "Stopped",
    _ => "Unknown"
};

// Null operators
var name = user?.Profile?.Name ?? "Anonymous";

// Raw string literals (C# 11+)
var json = """
    {
        "name": "value"
    }
    """;

// Records for DTOs
public record UserDto(int Id, string Name, string Email);

// Init-only properties
public class Config
{
    public required string ConnectionString { get; init; }
    public int MaxRetries { get; init; } = 3;
}
```

## Null Handling

- Enable nullable reference types: `<Nullable>enable</Nullable>`
- Never ignore nullable warnings
- Avoid null-forgiving operator (`!`) without comments

```csharp
public string GetValue(string? input)
{
    ArgumentNullException.ThrowIfNull(input);
    return input.ToUpper();
}
```

## Async/Await

- Return `Task`, `Task<T>`, `ValueTask`, or `ValueTask<T>`
- Never `async void` except event handlers
- Use `ConfigureAwait(false)` in library code
- Always pass `CancellationToken` through call chain

```csharp
public async Task<Data> FetchDataAsync(CancellationToken ct = default)
{
    var response = await _client.GetAsync(url, ct).ConfigureAwait(false);
    return await response.Content.ReadFromJsonAsync<Data>(ct).ConfigureAwait(false);
}
```

## Dependency Injection

```csharp
public class OrderService : IOrderService
{
    private readonly IOrderRepository _repository;
    private readonly ILogger<OrderService> _logger;

    public OrderService(IOrderRepository repository, ILogger<OrderService> logger)
    {
        _repository = repository;
        _logger = logger;
    }
}
```

## Error Handling

```csharp
// Custom exceptions
public class OrderNotFoundException : Exception
{
    public int OrderId { get; }
    public OrderNotFoundException(int orderId)
        : base($"Order with ID {orderId} was not found.")
    {
        OrderId = orderId;
    }
}

// Result pattern for expected failures
public record Result<T>
{
    public T? Value { get; init; }
    public string? Error { get; init; }
    public bool IsSuccess => Error is null;
    
    public static Result<T> Success(T value) => new() { Value = value };
    public static Result<T> Failure(string error) => new() { Error = error };
}
```

## LINQ

- Prefer method syntax
- Use `Any()` not `Count() > 0`
- Materialize once to avoid multiple enumeration

```csharp
var activeUsers = users
    .Where(u => u.IsActive)
    .OrderBy(u => u.LastName)
    .Select(u => new UserDto(u.Id, u.FullName))
    .ToList();
```

## XML Documentation

```csharp
/// <summary>
/// Retrieves a user by their unique identifier.
/// </summary>
/// <param name="userId">The unique identifier of the user.</param>
/// <param name="cancellationToken">Token to cancel the operation.</param>
/// <returns>The user if found; otherwise, null.</returns>
/// <exception cref="ArgumentOutOfRangeException">
/// Thrown when <paramref name="userId"/> is less than or equal to zero.
/// </exception>
public async Task<User?> GetUserByIdAsync(int userId, CancellationToken cancellationToken = default)
```

## Performance

- Use `Span<T>` and `Memory<T>` for high-performance scenarios
- Use `StringBuilder` for string concatenation in loops
- Use `ArrayPool<T>` for temporary arrays
- Consider `struct` for small, frequently allocated value types

## Forbidden

- No `public` fields
- No `goto` statements
- No catching `Exception` without re-throw/logging
- No empty catch blocks
- No `Thread.Sleep` in async code
- No hardcoded secrets
