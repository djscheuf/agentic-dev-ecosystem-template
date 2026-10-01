---
trigger: glob
globs: src/**/*.cs
---
# CQRS REST API Standards

## Naming Conventions

- **Commands:** `{Verb}{Entity}Command` (Create[Entity]Command, Update[Entity]Command)
- **Queries:** `Get{Entity/Entities}{ByFilter}Query` (Get[Entity]ByIdQuery, Get[Entity]By[Filter]Query)
- **Handlers:** `{Command/Query}Handler` (Create[Entity]CommandHandler)
- **Responses:** `{Command}Response` or DTO for queries
- **DTOs:** `{Entity}Dto` or `{Entity}{Purpose}Dto` ([Entity]Dto, [Entity]SummaryDto)
- **Repositories:** `I{Entity}Repository`, `{Entity}Repository`
- **Validators:** `{Request}Validator`

## CQRS Handler Pattern

```csharp
public class Create[Entity]Command : IRequest<Create[Entity]Response>
{
    public [Entity] Entity { get; set; } = null!;
    public Create[Entity]Command([Entity] entity) => Entity = entity;
}

public class Create[Entity]CommandHandler : IRequestHandler<Create[Entity]Command, Create[Entity]Response>
{
    private readonly I[Entity]Repository _repository;
    private readonly ILogger<Create[Entity]CommandHandler> _logger;

    public Create[Entity]CommandHandler(I[Entity]Repository repository, ILogger<Create[Entity]CommandHandler> logger)
    {
        _repository = repository ?? throw new ArgumentNullException(nameof(repository));
        _logger = logger ?? throw new ArgumentNullException(nameof(logger));
    }

    public async Task<Create[Entity]Response> Handle(Create[Entity]Command request, CancellationToken ct)
    {
        if (request?.Entity == null) throw new ArgumentNullException(nameof(request));
        _logger.LogDebug("Creating entity: {Description}", request.Entity.Description);
        var result = await _repository.AddAsync(request.Entity, ct);
        _logger.LogInformation("[Entity] created: {EntityId}", result.Id);
        return new Create[Entity]Response { EntityId = result.Id };
    }
}
```

**Rules:**
- Validate constructor dependencies with `ArgumentNullException`
- Validate request in Handle method
- Include `CancellationToken` parameter
- Log entry (Debug), success (Information), failures (Warning/Error)
- Throw exceptions (don't return null/false)

## Repository Pattern

```csharp
public interface I[Entity]Repository
{
    Task<[Entity]?> GetByIdAsync(int id, CancellationToken ct = default);
    Task<[Entity]> AddAsync([Entity] entity, CancellationToken ct = default);
    Task UpdateAsync([Entity] entity, CancellationToken ct = default);
}

public class [Entity]Repository : I[Entity]Repository
{
    private readonly [DbContext] _context;
    public [Entity]Repository([DbContext] context)
        => _context = context ?? throw new ArgumentNullException(nameof(context));

    public async Task<[Entity]?> GetByIdAsync(int id, CancellationToken ct = default)
        => await _context.[Entities].Include(t => t.[EntityType]).FirstOrDefaultAsync(t => t.Id == id, ct);
}
```

**Rules:**
- One repository per aggregate root
- Return domain entities (not DTOs)
- Use `Include()` for navigation properties
- Query methods return entity/null or List<Entity>
- Command methods return entity or void

## DbContext Configuration

```csharp
protected override void OnModelCreating(ModelBuilder modelBuilder)
{
    modelBuilder.Entity<[Entity]>(entity =>
    {
        entity.Property(e => e.Description).HasMaxLength(25).IsRequired();
        entity.Property(e => e.CreatedDate).HasConversion(UtcConverter);
        entity.HasOne(e => e.[EntityType]).WithMany().HasForeignKey(e => e.EntityTypeId);
    });
}

private static readonly ValueConverter<DateTime, DateTime> UtcConverter = 
    new ValueConverter<DateTime, DateTime>(
        v => v.Kind == DateTimeKind.Unspecified ? DateTime.SpecifyKind(v, DateTimeKind.Utc) : v,
        v => DateTime.SpecifyKind(v, DateTimeKind.Utc));
```

**Rules:**
- Configure entities in `OnModelCreating`
- Apply UTC ValueConverter to all DateTime properties
- Use `null!` for DbSet properties

## FluentValidation

```csharp
public class Create[Entity]RequestValidator : AbstractValidator<Create[Entity]Request>
{
    public Create[Entity]RequestValidator()
    {
        RuleFor(x => x.Description).NotEmpty().MaximumLength(25);
        RuleFor(x => x.StartDate).Must(d => d.Date >= DateTime.UtcNow.Date.AddDays(15));
        RuleFor(x => x.EndDate).GreaterThan(x => x.StartDate);
        When(x => x.ExpiryDate.HasValue, () =>
            RuleFor(x => x.ExpiryDate!.Value).GreaterThanOrEqualTo(x => x.EndDate));
    }
}
```

**Rules:**
- Create validator for each request DTO
- Use `When()` for conditional validation
- Register with `AddValidatorsFromAssemblyContaining<T>()`

## Validation Strategy

**Enforcement:**
- Database: structural integrity (foreign keys, unique constraints, data types)
- Application: business rules (date ranges, status transitions, workflows)

**Status-Dependent:**
- Pending: Lenient (allow partial/incomplete data)
- Status transitions: Strict (enforce all business rules)

```csharp
public class Approve[Entity]CommandHandler
{
    public async Task<Unit> Handle(Approve[Entity]Command request, CancellationToken ct)
    {
        var entity = await _repository.GetByIdAsync(request.Id, ct);
        ValidateDateRanges(entity);
        ValidateRequiredFields(entity);
        entity.Status = [EntityStatus].Active;
        await _repository.UpdateAsync(entity, ct);
        return Unit.Value;
    }
    
    private void ValidateDateRanges([Entity] entity)
    {
        if (entity.EndDate <= entity.StartDate)
            throw new InvalidOperationException("End date must be after start date");
    }
}
```

## DateTime Handling

**Always UTC:**
```csharp
entity.CreatedDate = DateTime.UtcNow;
entity.ExpiryDate = DateTime.SpecifyKind(userDate, DateTimeKind.Utc);
```

**Never Local/Unspecified:**
```csharp
DateTime.Now                      // ❌ Throws
new DateTime(2025, 12, 31)        // ❌ Throws
```

**Enforcement:**
- DbContext ValueConverter marks all DateTime as UTC
- SaveChanges throws if non-UTC detected
- API responses include "Z" suffix

## Structured Logging

```csharp
_logger.LogDebug("Creating entity: {Description}", entity.Description);
_logger.LogInformation("[Entity] {EntityId} created by {UserId}", id, userId);
_logger.LogWarning("[Entity] {EntityId} not found", id);
_logger.LogError(ex, "Failed to create entity for {UserId}", userId);
```

**Log Levels:**
- **Debug:** Entry/exit, parameters, cache hits/misses
- **Information:** Business events, successful operations
- **Warning:** Validation failures, not found, unauthorized
- **Error:** Unexpected exceptions, retry failures

**Rules:**
- Use named parameters `{PropertyName}`
- Include correlation IDs in controllers
- Don't log passwords, tokens, PII, large payloads

## Reference Data Caching

**Pattern:** `IMemoryCache` with 1-hour sliding expiration for reference data.

**When:** Read-heavy, small datasets (< 1000 items), infrequently updated

```csharp
public async Task<IEnumerable<[ReferenceData]Dto>> Handle(Get[ReferenceData]Query request, CancellationToken ct)
{
    var cacheKey = request.EntityTypeId.HasValue ? $"[ReferenceData]:{request.EntityTypeId}" : "[ReferenceData]:All";

    if (_cache.TryGetValue(cacheKey, out IEnumerable<[ReferenceData]Dto>? cached) && cached != null)
    {
        _logger.LogDebug("Cache hit: {CacheKey}", cacheKey);
        return cached;
    }

    var data = await _repository.GetAllAsync(ct);
    var dtos = data.OrderBy(d => d.DisplayOrder).Select(d => new [ReferenceData]Dto { ... }).ToList();
    
    _cache.Set(cacheKey, dtos, new MemoryCacheEntryOptions { SlidingExpiration = TimeSpan.FromHours(1) });
    return dtos;
}
```

**Cache Key Formats:**
```
[EntityType]s
[ReferenceData]:All
[ReferenceData]:{entityTypeId}
[ReferenceCodes]:{yyyy-MM-dd}
[CompositeCodes]:{code}:{yyyy-MM-dd}
```

## Exception Handling

| Exception | Status | Use Case |
|-----------|--------|----------|
| `KeyNotFoundException` | 404 | Entity not found |
| `UnauthorizedAccessException` | 404 | Unauthorized |
| `ArgumentException` | 400 | Invalid input |
| `InvalidOperationException` | 400 | Business rule violation |
| `DbUpdateException` (547) | 400 | Foreign key constraint |
| `DbUpdateException` (2627/2601) | 409 | Unique constraint |

```csharp
if (request == null) throw new ArgumentNullException(nameof(request));
var entity = await _repository.GetByIdAsync(id, ct) ?? throw new KeyNotFoundException($"Entity {id} not found");
if (!HasAccess(entity, userId)) throw new UnauthorizedAccessException();
if (entity.Status != "Pending") throw new InvalidOperationException("Only Pending can be edited");
```

## Error Response Format

**Use error codes for i18n:**

```csharp
public record ValidationError(
    string Property,                        // "StartDate" or "Allocations[0].Percentage"
    string ErrorCode,                       // "VALIDATION.START_DATE.TOO_SOON"
    Dictionary<string, object>? Parameters = null
);

public class Mark[Entity]ReadyCommandHandler
{
    public async Task<Result<Unit>> Handle(Mark[Entity]ReadyCommand request, CancellationToken ct)
    {
        var entity = await _repository.GetByIdAsync(request.EntityId, ct);
        var errors = new List<ValidationError>();
        
        var daysFromNow = (entity.StartDate.Date - DateTime.UtcNow.Date).Days;
        if (daysFromNow < 15)
        {
            errors.Add(new ValidationError(
                Property: "StartDate",
                ErrorCode: "VALIDATION.START_DATE.TOO_SOON",
                Parameters: new Dictionary<string, object> { ["minimumDays"] = 15, ["currentDays"] = daysFromNow }
            ));
        }
        
        if (errors.Any()) return Result<Unit>.Failure(errors);
        entity.Status = [EntityStatus].Active;
        await _repository.UpdateAsync(entity, ct);
        return Result<Unit>.Success(Unit.Value);
    }
}
```

**Error Code Format:** `CATEGORY.ENTITY.SPECIFIC_ERROR`

**Categories:** `VALIDATION.*`, `AUTHORIZATION.*`, `CONCURRENCY.*`, `DATABASE.*`, `SYSTEM.*`

**Examples:**
```
VALIDATION.START_DATE.TOO_SOON
VALIDATION.DATE_RANGE.END_BEFORE_START
AUTHORIZATION.[ENTITY].NOT_OWNER_OR_REQUESTER
DATABASE.FOREIGN_KEY.INVALID_REFERENCE
```

**Response:**
```json
{
  "errors": [
    {
      "property": "StartDate",
      "errorCode": "VALIDATION.START_DATE.TOO_SOON",
      "parameters": { "minimumDays": 15, "currentDays": 10 }
    }
  ]
}
```

**Registry:** Document error codes in `[project-docs]/error-codes/`

## File Organization

**Namespaces:**
```
[ProjectName].Domain.Entities
[ProjectName].Application.[Entities].Commands
[ProjectName].Application.[Entities].Queries
[ProjectName].Application.Reference.DTOs
[ProjectName].Infrastructure.Repositories
[ProjectName].Api.Controllers
```

**Rules:**
- One class per file
- File name = Class name
- Namespace = Folder path
- Group by feature
