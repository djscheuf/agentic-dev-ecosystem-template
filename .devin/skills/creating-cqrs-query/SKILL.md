---
name: creating-cqrs-query
description: How to create a new CQRS Query in the .NET backend API. Use this skill when implementing new read operations (GET endpoints), retrieving data without modifying state, creating query handlers, or working with MediatR queries. This includes creating the query class, handler, response DTO, authorization checks, and wiring up the controller endpoint. Make sure to use this skill whenever implementing any read operation in the backend API, even if the user just says "add a GET endpoint" or "retrieve data" - if it reads data without modifying it, it needs a query.
---

# Creating a New CQRS Query

## Overview

This skill guides you through creating a new CQRS Query in the Tactic Management API. Queries represent **read operations** that retrieve data without modifying system state (GET endpoints).

**When to use this skill:**
- Adding a new GET endpoint that retrieves data
- Implementing list/search operations with filtering and pagination
- Creating detail views for entities
- Retrieving reference data or lookup tables
- Any operation that reads from the database without changes

**Architecture Context:**
- **Pattern:** CQRS (Command Query Responsibility Segregation) with MediatR
- **Stack:** .NET 8, Entity Framework Core
- **Layers:** API → Application → Domain → Infrastructure
- **Testing:** BDD/GWT pattern with xUnit
- **Authorization:** Read-based authorization service

---

## Complete Implementation Checklist

### Phase 1: Define Domain Models

#### 1.1 Create Query Class
**Location:** `src/api/src/TacticManagement.Application/Tactics/Queries/`

Queries use the **record** pattern and implement `IRequest<TResponse>`:

```csharp
using MediatR;
using TacticManagement.Application.Tactics.DTOs;

namespace TacticManagement.Application.Tactics.Queries;

/// <summary>
/// Query to retrieve [describe what data is retrieved].
/// </summary>
public record GetSomethingQuery(
    Guid Id,
    string UserId
) : IRequest<SomethingDto>;
```

**Naming Convention:**
- Pattern: `Get{Noun}Query` or `Get{Noun}{Qualifier}Query`
- Examples: `GetTacticByIdQuery`, `GetUserTacticsQuery`, `GetTacticTypesQuery`
- Always include `UserId` for authorization
- Include filter/pagination parameters as needed

**Query Types:**

**Single entity retrieval:**
```csharp
public record GetTacticByIdQuery(
    Guid TacticId,
    string UserId
) : IRequest<TacticDetailDto>;
```

**List with filtering and pagination:**
```csharp
public record GetUserTacticsQuery(
    string UserId,
    string? Term,              // Search term
    string? Status,            // Filter by status
    List<int>? TacticTypeIds,  // Filter by types
    int Page,                  // Page number (1-based)
    int PageSize,              // Items per page
    string SortBy,             // Sort field
    string SortOrder           // "asc" or "desc"
) : IRequest<PaginatedResponseDto<TacticListItemDto>>;
```

**Reference data (cached):**
```csharp
public record GetTacticTypesQuery() : IRequest<List<TacticTypeDto>>;
```

#### 1.2 Create Response DTO
**Location:** `src/api/src/TacticManagement.Application/Tactics/DTOs/`

DTOs should match the data shape needed by the client:

```csharp
namespace TacticManagement.Application.Tactics.DTOs;

/// <summary>
/// Detailed view of a tactic entity.
/// </summary>
public class TacticDetailDto
{
    public Guid Id { get; set; }
    public string Description { get; set; } = string.Empty;
    public int OfferCode { get; set; }
    public string Status { get; set; } = string.Empty;
    
    // Use nullable types for optional fields
    public string? Comments { get; set; }
    public decimal? FaceValue { get; set; }
    
    // Navigation properties as nested DTOs
    public List<TacticAllocationDto> Allocations { get; set; } = new();
    
    // Audit fields
    public DateTime Created { get; set; }
    public DateTime LastModified { get; set; }
    public string LastModifiedBy { get; set; } = string.Empty;
}
```

**DTO Patterns:**

**List item DTO (minimal fields for lists):**
```csharp
public class TacticListItemDto
{
    public Guid Id { get; set; }
    public string Description { get; set; } = string.Empty;
    public string Status { get; set; } = string.Empty;
    public DateTime CampaignStartDate { get; set; }
    // Only include fields needed for list view
}
```

**Paginated response wrapper:**
```csharp
public class PaginatedResponseDto<T>
{
    public List<T> Items { get; set; } = new();
    public int TotalCount { get; set; }
    public int Page { get; set; }
    public int PageSize { get; set; }
    public int TotalPages => (int)Math.Ceiling((double)TotalCount / PageSize);
    public bool HasPreviousPage => Page > 1;
    public bool HasNextPage => Page < TotalPages;
}
```

**Reference data DTO:**
```csharp
public class TacticTypeDto
{
    public int Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public string? Description { get; set; }
    public int DisplayOrder { get; set; }
}
```

**Key Principles:**
- Use `class` for DTOs (not `record`) - allows for initialization
- Use nullable types (`?`) for optional fields
- Provide default values for non-nullable fields
- Include only fields needed by the client
- Flatten complex relationships when appropriate
- Use consistent naming with domain model

---

### Phase 2: Create Query Handler

#### 2.1 Handler Class Structure
**Location:** `src/api/src/TacticManagement.Application/Tactics/Queries/`

```csharp
using MediatR;
using Microsoft.Extensions.Logging;
using TacticManagement.Application.Common.Interfaces;
using TacticManagement.Application.Interfaces;
using TacticManagement.Application.Tactics.DTOs;
using TacticManagement.Domain.Exceptions;

namespace TacticManagement.Application.Queries;

/// <summary>
/// Handler for retrieving [describe what].
/// Validates authorization and returns [describe response].
/// </summary>
public class GetSomethingQueryHandler 
    : IRequestHandler<GetSomethingQuery, SomethingDto>
{
    private readonly ITacticRepository _tacticRepository;
    private readonly ITacticReadAuthorizationService _readAuthService;
    private readonly ILogger<GetSomethingQueryHandler> _logger;

    public GetSomethingQueryHandler(
        ITacticRepository tacticRepository,
        ITacticReadAuthorizationService readAuthService,
        ILogger<GetSomethingQueryHandler> logger)
    {
        _tacticRepository = tacticRepository ?? throw new ArgumentNullException(nameof(tacticRepository));
        _readAuthService = readAuthService ?? throw new ArgumentNullException(nameof(readAuthService));
        _logger = logger ?? throw new ArgumentNullException(nameof(logger));
    }

    public async Task<SomethingDto> Handle(
        GetSomethingQuery request,
        CancellationToken cancellationToken)
    {
        var correlationId = $"GetSomething-{Guid.NewGuid()}";
        
        _logger.LogDebug(
            "[{CorrelationId}] GetSomethingQueryHandler started - Id: {Id}, UserId: {UserId}",
            correlationId, request.Id, request.UserId);

        // 1. Load entity from repository
        var entity = await _tacticRepository.GetByIdAsync(request.Id, cancellationToken);
        
        if (entity == null)
        {
            _logger.LogWarning(
                "[{CorrelationId}] Entity not found - Id: {Id}",
                correlationId, request.Id);
            throw new TacticNotFoundException(request.Id);
        }

        // 2. Check read authorization
        var hasAccess = await _readAuthService.HasReadAccessAsync(
            request.UserId,
            entity,
            correlationId,
            cancellationToken);

        if (!hasAccess)
        {
            _logger.LogWarning(
                "[{CorrelationId}] Authorization denied - returning 404. Id: {Id}, UserId: {UserId}",
                correlationId, request.Id, request.UserId);
            // Return 404 instead of 403 for security (don't leak existence)
            throw new TacticNotFoundException(request.Id);
        }

        _logger.LogInformation(
            "[{CorrelationId}] Query completed successfully - Id: {Id}",
            correlationId, request.Id);

        // 3. Map to DTO and return
        return MapToDto(entity);
    }

    private static SomethingDto MapToDto(Entity entity)
    {
        return new SomethingDto
        {
            Id = entity.Id,
            Name = entity.Name,
            Status = entity.Status.ToString(),
            Created = entity.CreatedDate,
            LastModified = entity.LastModified
        };
    }
}
```

#### 2.2 Common Handler Patterns

**Single entity with navigation properties:**
```csharp
public async Task<TacticDetailDto> Handle(
    GetTacticByIdQuery request,
    CancellationToken cancellationToken)
{
    var correlationId = $"GetTacticById-{Guid.NewGuid()}";
    
    _logger.LogDebug(
        "[{CorrelationId}] GetTacticByIdQueryHandler started - TacticId: {TacticId}, UserId: {UserId}",
        correlationId, request.TacticId, request.UserId);
    
    var tactic = await _tacticRepository.GetByIdAsync(request.TacticId, cancellationToken);
    
    if (tactic == null)
    {
        _logger.LogWarning(
            "[{CorrelationId}] Tactic not found - TacticId: {TacticId}",
            correlationId, request.TacticId);
        throw new TacticNotFoundException(request.TacticId);
    }

    // Authorization check
    var hasAccess = await _readAuthService.HasReadAccessAsync(
        request.UserId,
        tactic,
        correlationId,
        cancellationToken);

    if (!hasAccess)
    {
        _logger.LogWarning(
            "[{CorrelationId}] Authorization denied - TacticId: {TacticId}, UserId: {UserId}",
            correlationId, request.TacticId, request.UserId);
        throw new TacticNotFoundException(request.TacticId);
    }

    // Load related data
    var allocations = await _allocationRepository.GetByTacticIdAsync(
        request.TacticId, 
        cancellationToken);

    _logger.LogInformation(
        "[{CorrelationId}] Retrieved tactic with {AllocationCount} allocations",
        correlationId, allocations.Count());

    return MapToDto(tactic, allocations);
}
```

**List with filtering and pagination:**
```csharp
public async Task<PaginatedResponseDto<TacticListItemDto>> Handle(
    GetUserTacticsQuery request,
    CancellationToken cancellationToken)
{
    var correlationId = $"GetUserTactics-{Guid.NewGuid()}";
    
    _logger.LogDebug(
        "[{CorrelationId}] GetUserTacticsQueryHandler started - UserId: {UserId}, Page: {Page}, PageSize: {PageSize}",
        correlationId, request.UserId, request.Page, request.PageSize);

    // Validate and normalize pagination
    const int DefaultPageSize = 20;
    const int MaxPageSize = 100;
    
    var pageSize = request.PageSize <= 0 || request.PageSize > MaxPageSize 
        ? DefaultPageSize 
        : request.PageSize;
    var pageNumber = request.Page < 1 ? 1 : request.Page;

    // Normalize sort parameters
    var sortBy = string.IsNullOrWhiteSpace(request.SortBy) 
        ? "id" 
        : request.SortBy.Trim().ToLower();
    var sortOrder = request.SortOrder?.ToLower() == "desc" ? "desc" : "asc";

    // Get user context for authorization
    var userContext = await _userContextService.GetUserContextAsync(
        request.UserId, 
        cancellationToken);

    // Build authorization filters based on roles
    var roleFilters = await BuildRoleFiltersAsync(userContext, cancellationToken);

    // Query with filters
    var tactics = await _tacticRepository.GetUserTacticsWithFiltersAsync(
        roleFilters,
        request.Term?.Trim(),
        request.Status,
        request.TacticTypeIds,
        pageNumber,
        pageSize,
        sortBy,
        sortOrder,
        cancellationToken);

    var totalCount = await _tacticRepository.CountUserTacticsAsync(
        roleFilters,
        request.Term?.Trim(),
        request.Status,
        request.TacticTypeIds,
        cancellationToken);

    _logger.LogInformation(
        "[{CorrelationId}] Retrieved {Count} of {Total} tactics",
        correlationId, tactics.Count, totalCount);

    return new PaginatedResponseDto<TacticListItemDto>
    {
        Items = tactics.Select(MapToListItemDto).ToList(),
        TotalCount = totalCount,
        Page = pageNumber,
        PageSize = pageSize
    };
}
```

**Reference data with caching:**
```csharp
public async Task<List<TacticTypeDto>> Handle(
    GetTacticTypesQuery request,
    CancellationToken cancellationToken)
{
    var correlationId = $"GetTacticTypes-{Guid.NewGuid()}";
    
    _logger.LogDebug("[{CorrelationId}] GetTacticTypesQueryHandler started", correlationId);

    // Check cache first
    var cacheKey = "TacticTypes";
    if (_cache.TryGetValue(cacheKey, out List<TacticTypeDto>? cachedTypes) && cachedTypes != null)
    {
        _logger.LogDebug("[{CorrelationId}] Returning cached tactic types", correlationId);
        return cachedTypes;
    }

    // Load from database
    var tacticTypes = await _tacticTypeRepository.GetAllAsync(cancellationToken);
    
    var dtos = tacticTypes
        .OrderBy(t => t.DisplayOrder)
        .Select(t => new TacticTypeDto
        {
            Id = t.Id,
            Name = t.Name,
            Description = t.Description,
            DisplayOrder = t.DisplayOrder
        })
        .ToList();

    // Cache for 15 minutes
    _cache.Set(cacheKey, dtos, TimeSpan.FromMinutes(15));

    _logger.LogInformation(
        "[{CorrelationId}] Retrieved {Count} tactic types",
        correlationId, dtos.Count);

    return dtos;
}
```

#### 2.3 Authorization Patterns

**Using ITacticReadAuthorizationService:**
```csharp
var hasAccess = await _readAuthService.HasReadAccessAsync(
    request.UserId,
    tactic,
    correlationId,
    cancellationToken);

if (!hasAccess)
{
    // Return 404, not 403 (security pattern)
    throw new TacticNotFoundException(request.TacticId);
}
```

**Role-based filtering for lists:**
```csharp
private async Task<List<Expression<Func<Tactic, bool>>>> BuildRoleFiltersAsync(
    UserContext userContext,
    CancellationToken cancellationToken)
{
    var filters = new List<Expression<Func<Tactic, bool>>>();
    var roles = userContext.Roles;

    // Admin sees all
    if (roles.Contains("Admin", StringComparer.OrdinalIgnoreCase))
    {
        return filters; // Empty filters = no restrictions
    }

    // Requester sees owned and requested tactics
    if (roles.Contains("Requester", StringComparer.OrdinalIgnoreCase))
    {
        filters.Add(t => t.OwnerId == userContext.UserId || t.RequesterId == userContext.UserId);
    }

    // ProofReader sees tactics in specific statuses
    if (roles.Contains("ProofReader", StringComparer.OrdinalIgnoreCase))
    {
        filters.Add(t => t.Status == TacticStatus.PROOF_READY || t.Status == TacticStatus.IN_REVIEW);
    }

    return filters;
}
```

#### 2.4 Mapping Patterns

**Simple mapping:**
```csharp
private static TacticDetailDto MapToDto(Tactic tactic)
{
    return new TacticDetailDto
    {
        Id = tactic.Id,
        Description = tactic.Description ?? string.Empty,
        Status = tactic.Status.ToString(),
        Created = tactic.CreatedDate,
        LastModified = tactic.LastModified
    };
}
```

**Mapping with navigation properties:**
```csharp
private static TacticDetailDto MapToDto(Tactic tactic, IEnumerable<TacticAllocation> allocations)
{
    return new TacticDetailDto
    {
        Id = tactic.Id,
        Description = tactic.Description ?? string.Empty,
        Status = tactic.Status.ToString(),
        Allocations = allocations.Select(a => new TacticAllocationDto
        {
            Id = a.Id,
            GlCodeId = a.GlCodeId,
            AllocationPercent = a.AllocationPercent
        }).ToList()
    };
}
```

**Conditional field inclusion:**
```csharp
private static TacticDetailDto MapToDto(Tactic tactic)
{
    var dto = new TacticDetailDto
    {
        Id = tactic.Id,
        Description = tactic.Description ?? string.Empty
    };

    // Only include budget fields if any are set
    if (tactic.FaceValue.HasValue || tactic.CirculationQuantity.HasValue)
    {
        dto.FaceValue = tactic.FaceValue;
        dto.CirculationQuantity = tactic.CirculationQuantity;
    }

    return dto;
}
```

---

### Phase 3: Wire Up Controller

#### 3.1 Add Controller Action
**Location:** `src/api/src/TacticManagement.Api/Controllers/TacticsController.cs`

```csharp
/// <summary>
/// Retrieves a tactic by ID
/// </summary>
/// <param name="tacticId">The tactic ID</param>
/// <param name="cancellationToken">Cancellation token</param>
/// <returns>Tactic details</returns>
/// <response code="200">Tactic retrieved successfully</response>
/// <response code="401">User not authenticated</response>
/// <response code="404">Tactic not found or user not authorized</response>
[HttpGet("{tacticId:guid}")]
[Authorize]
[ProducesResponseType(typeof(TacticDetailDto), StatusCodes.Status200OK)]
[ProducesResponseType(StatusCodes.Status404NotFound)]
public async Task<IActionResult> GetTacticById(
    Guid tacticId,
    CancellationToken cancellationToken = default)
{
    var correlationId = Guid.NewGuid().ToString();
    var userId = User.FindFirst(ClaimTypes.NameIdentifier)?.Value 
        ?? throw new UnauthorizedAccessException("User ID not found in claims");

    _logger.LogDebug(
        "[{CorrelationId}] GetTacticById started - TacticId: {TacticId}, UserId: {UserId}",
        correlationId, tacticId, userId);

    try
    {
        var query = new GetTacticByIdQuery(tacticId, userId);
        var result = await _mediator.Send(query, cancellationToken);

        _logger.LogInformation(
            "[{CorrelationId}] GetTacticById completed - TacticId: {TacticId}",
            correlationId, tacticId);

        return Ok(result);
    }
    catch (TacticNotFoundException)
    {
        _logger.LogWarning(
            "[{CorrelationId}] Tactic not found - TacticId: {TacticId}",
            correlationId, tacticId);
        return NotFound();
    }
}
```

#### 3.2 List Endpoint with Query Parameters

```csharp
/// <summary>
/// Retrieves tactics for the current user with filtering and pagination
/// </summary>
/// <param name="term">Search term (optional)</param>
/// <param name="status">Filter by status (optional)</param>
/// <param name="tacticTypeIds">Filter by tactic type IDs (optional)</param>
/// <param name="page">Page number (default: 1)</param>
/// <param name="pageSize">Page size (default: 20, max: 100)</param>
/// <param name="sortBy">Sort field (default: id)</param>
/// <param name="sortOrder">Sort order: asc or desc (default: asc)</param>
/// <param name="cancellationToken">Cancellation token</param>
/// <returns>Paginated list of tactics</returns>
/// <response code="200">Tactics retrieved successfully</response>
/// <response code="401">User not authenticated</response>
[HttpGet]
[Authorize]
[ProducesResponseType(typeof(PaginatedResponseDto<TacticListItemDto>), StatusCodes.Status200OK)]
public async Task<IActionResult> GetUserTactics(
    [FromQuery] string? term = null,
    [FromQuery] string? status = null,
    [FromQuery] List<int>? tacticTypeIds = null,
    [FromQuery] int page = 1,
    [FromQuery] int pageSize = 20,
    [FromQuery] string sortBy = "id",
    [FromQuery] string sortOrder = "asc",
    CancellationToken cancellationToken = default)
{
    var correlationId = Guid.NewGuid().ToString();
    var userId = User.FindFirst(ClaimTypes.NameIdentifier)?.Value 
        ?? throw new UnauthorizedAccessException("User ID not found in claims");

    _logger.LogDebug(
        "[{CorrelationId}] GetUserTactics started - UserId: {UserId}, Page: {Page}, PageSize: {PageSize}",
        correlationId, userId, page, pageSize);

    var query = new GetUserTacticsQuery(
        userId,
        term,
        status,
        tacticTypeIds,
        page,
        pageSize,
        sortBy,
        sortOrder);

    var result = await _mediator.Send(query, cancellationToken);

    _logger.LogInformation(
        "[{CorrelationId}] GetUserTactics completed - Retrieved {Count} of {Total} tactics",
        correlationId, result.Items.Count, result.TotalCount);

    return Ok(result);
}
```

#### 3.3 Reference Data Endpoint

```csharp
/// <summary>
/// Retrieves all tactic types (cached)
/// </summary>
/// <param name="cancellationToken">Cancellation token</param>
/// <returns>List of tactic types</returns>
/// <response code="200">Tactic types retrieved successfully</response>
[HttpGet("types")]
[Authorize]
[ProducesResponseType(typeof(List<TacticTypeDto>), StatusCodes.Status200OK)]
public async Task<IActionResult> GetTacticTypes(
    CancellationToken cancellationToken = default)
{
    var correlationId = Guid.NewGuid().ToString();
    
    _logger.LogDebug("[{CorrelationId}] GetTacticTypes started", correlationId);

    var query = new GetTacticTypesQuery();
    var result = await _mediator.Send(query, cancellationToken);

    _logger.LogInformation(
        "[{CorrelationId}] GetTacticTypes completed - Retrieved {Count} types",
        correlationId, result.Count);

    return Ok(result);
}
```

#### 3.4 Route Patterns

**Single entity by ID:**
```csharp
[HttpGet("{tacticId:guid}")]
```

**List with query parameters:**
```csharp
[HttpGet]
```

**Nested resource:**
```csharp
[HttpGet("{tacticId:guid}/allocations")]
```

**Reference data:**
```csharp
[HttpGet("types")]
[HttpGet("statuses")]
```

---

### Phase 4: Testing

#### 4.1 Create BDD/GWT Tests
**Location:** `src/api/tests/TacticManagement.Application.Tests/Tactics/Queries/`

```csharp
using FluentAssertions;
using NSubstitute;
using TacticManagement.Application.Tactics.Queries;
using TacticManagement.Domain.Exceptions;
using Xunit;

namespace TacticManagement.Application.Tests.Tactics.Queries;

public class GetTacticByIdQueryHandlerTests : IDisposable
{
    private readonly ITacticRepository _tacticRepository;
    private readonly ITacticReadAuthorizationService _readAuthService;
    private readonly ILogger<GetTacticByIdQueryHandler> _logger;
    private readonly GetTacticByIdQueryHandler _handler;

    public GetTacticByIdQueryHandlerTests()
    {
        _tacticRepository = Substitute.For<ITacticRepository>();
        _readAuthService = Substitute.For<ITacticReadAuthorizationService>();
        _logger = Substitute.For<ILogger<GetTacticByIdQueryHandler>>();
        
        _handler = new GetTacticByIdQueryHandler(
            _tacticRepository,
            _readAuthService,
            _logger);
    }

    [Fact]
    public async Task Given_ValidQuery_When_Handle_Then_ReturnsTacticDto()
    {
        // Given
        var tacticId = Guid.NewGuid();
        var userId = "user@example.com";
        var tactic = new Tactic 
        { 
            Id = tacticId, 
            Description = "Test Tactic",
            Status = TacticStatus.DRAFT
        };

        _tacticRepository.GetByIdAsync(tacticId, Arg.Any<CancellationToken>())
            .Returns(tactic);
        _readAuthService.HasReadAccessAsync(
                userId, 
                tactic, 
                Arg.Any<string>(), 
                Arg.Any<CancellationToken>())
            .Returns(true);

        var query = new GetTacticByIdQuery(tacticId, userId);

        // When
        var result = await _handler.Handle(query, CancellationToken.None);

        // Then
        result.Should().NotBeNull();
        result.Id.Should().Be(tacticId);
        result.Description.Should().Be("Test Tactic");
        result.Status.Should().Be("DRAFT");
    }

    [Fact]
    public async Task Given_TacticNotFound_When_Handle_Then_ThrowsTacticNotFoundException()
    {
        // Given
        var tacticId = Guid.NewGuid();
        _tacticRepository.GetByIdAsync(tacticId, Arg.Any<CancellationToken>())
            .Returns((Tactic?)null);

        var query = new GetTacticByIdQuery(tacticId, "user@example.com");

        // When
        Func<Task> act = async () => await _handler.Handle(query, CancellationToken.None);

        // Then
        await act.Should().ThrowAsync<TacticNotFoundException>()
            .WithMessage($"*{tacticId}*");
    }

    [Fact]
    public async Task Given_UserNotAuthorized_When_Handle_Then_ThrowsTacticNotFoundException()
    {
        // Given
        var tacticId = Guid.NewGuid();
        var tactic = new Tactic { Id = tacticId };
        
        _tacticRepository.GetByIdAsync(tacticId, Arg.Any<CancellationToken>())
            .Returns(tactic);
        _readAuthService.HasReadAccessAsync(
                Arg.Any<string>(), 
                tactic, 
                Arg.Any<string>(), 
                Arg.Any<CancellationToken>())
            .Returns(false);

        var query = new GetTacticByIdQuery(tacticId, "unauthorized@example.com");

        // When
        Func<Task> act = async () => await _handler.Handle(query, CancellationToken.None);

        // Then
        await act.Should().ThrowAsync<TacticNotFoundException>();
    }

    public void Dispose()
    {
        // Cleanup if needed
    }
}
```

#### 4.2 List Query Tests

```csharp
[Fact]
public async Task Given_ValidPaginationParams_When_Handle_Then_ReturnsPaginatedResults()
{
    // Given
    var userId = "user@example.com";
    var tactics = new List<Tactic>
    {
        new() { Id = Guid.NewGuid(), Description = "Tactic 1" },
        new() { Id = Guid.NewGuid(), Description = "Tactic 2" }
    };

    _tacticRepository.GetUserTacticsWithFiltersAsync(
            Arg.Any<List<Expression<Func<Tactic, bool>>>>(),
            Arg.Any<string>(),
            Arg.Any<string>(),
            Arg.Any<List<int>>(),
            1,
            20,
            "id",
            "asc",
            Arg.Any<CancellationToken>())
        .Returns(tactics);

    _tacticRepository.CountUserTacticsAsync(
            Arg.Any<List<Expression<Func<Tactic, bool>>>>(),
            Arg.Any<string>(),
            Arg.Any<string>(),
            Arg.Any<List<int>>(),
            Arg.Any<CancellationToken>())
        .Returns(2);

    var query = new GetUserTacticsQuery(
        userId, null, null, null, 1, 20, "id", "asc");

    // When
    var result = await _handler.Handle(query, CancellationToken.None);

    // Then
    result.Should().NotBeNull();
    result.Items.Should().HaveCount(2);
    result.TotalCount.Should().Be(2);
    result.Page.Should().Be(1);
    result.PageSize.Should().Be(20);
}
```

---

## Common Patterns & Best Practices

### Correlation IDs
Always generate correlation IDs for tracing:
```csharp
var correlationId = $"GetTacticById-{Guid.NewGuid()}";
_logger.LogDebug("[{CorrelationId}] Query started", correlationId);
```

### Structured Logging
Use structured logging with named parameters:
```csharp
_logger.LogInformation(
    "[{CorrelationId}] Retrieved {Count} tactics - UserId: {UserId}",
    correlationId, tactics.Count, userId);
```

### Security Pattern: 404 vs 403
Always return 404 for unauthorized access to prevent information disclosure:
```csharp
if (!hasAccess)
{
    // Don't reveal that the entity exists
    throw new TacticNotFoundException(request.TacticId);
}
```

### Pagination Defaults
Always validate and normalize pagination parameters:
```csharp
const int DefaultPageSize = 20;
const int MaxPageSize = 100;

var pageSize = request.PageSize <= 0 || request.PageSize > MaxPageSize 
    ? DefaultPageSize 
    : request.PageSize;
var pageNumber = request.Page < 1 ? 1 : request.Page;
```

### Caching Reference Data
Cache small, infrequently-changing datasets:
```csharp
var cacheKey = "TacticTypes";
if (_cache.TryGetValue(cacheKey, out List<TacticTypeDto>? cached) && cached != null)
{
    return cached;
}

var data = await LoadFromDatabase();
_cache.Set(cacheKey, data, TimeSpan.FromMinutes(15));
return data;
```

### Null Handling
Use null-coalescing for safe string handling:
```csharp
Description = tactic.Description ?? string.Empty,
Comments = tactic.Comments  // Keep null if null
```

---

## Verification Checklist

Before considering the query complete:

**Domain Layer:**
- [ ] Query class created with `IRequest<TResponse>`
- [ ] Response DTO created with appropriate fields
- [ ] All DTOs use appropriate nullability
- [ ] Pagination DTO created (if needed)

**Application Layer:**
- [ ] Handler implements `IRequestHandler<TQuery, TResponse>`
- [ ] Constructor validates all dependencies (null checks)
- [ ] Correlation ID generated for tracing
- [ ] Entity loaded from repository
- [ ] Authorization checked via `ITacticReadAuthorizationService`
- [ ] 404 returned for unauthorized access (not 403)
- [ ] Mapping method created (private static)
- [ ] Structured logging at Debug and Information levels
- [ ] Pagination validated and normalized (if applicable)
- [ ] Caching implemented (if reference data)

**API Layer:**
- [ ] Controller action added with `[HttpGet]`
- [ ] Route template follows conventions
- [ ] Authorization attribute applied
- [ ] XML documentation comments added
- [ ] Response type attributes added
- [ ] Correlation ID generated
- [ ] UserId extracted from claims
- [ ] Query created and sent via MediatR
- [ ] Exceptions handled (TacticNotFoundException)
- [ ] Appropriate HTTP status codes returned (200, 404)

**Testing:**
- [ ] Handler tests created with BDD/GWT pattern
- [ ] Happy path test (valid query returns data)
- [ ] Entity not found test
- [ ] Authorization failure test
- [ ] Pagination tests (if applicable)
- [ ] All tests use NSubstitute for mocking
- [ ] All tests use FluentAssertions for assertions

**Documentation:**
- [ ] XML comments on query class
- [ ] XML comments on handler class
- [ ] XML comments on controller action
- [ ] Swagger annotations complete

---

## Common Pitfalls

### 1. Returning 403 Instead of 404
**Problem:** Leaking information about resource existence  
**Solution:** Always return 404 for both "not found" and "not authorized"

### 2. Missing Authorization Check
**Problem:** Exposing data to unauthorized users  
**Solution:** Always use `ITacticReadAuthorizationService.HasReadAccessAsync()`

### 3. Over-fetching Data
**Problem:** Including unnecessary fields in DTOs  
**Solution:** Create separate DTOs for list vs detail views

### 4. Missing Pagination Validation
**Problem:** Allowing unbounded page sizes  
**Solution:** Enforce max page size and default values

### 5. Not Caching Reference Data
**Problem:** Repeated database queries for static data  
**Solution:** Cache with appropriate expiration (15 minutes for reference data)

### 6. Incorrect DTO Types
**Problem:** Using `record` for DTOs  
**Solution:** Use `class` for DTOs to allow proper initialization

### 7. Missing Correlation IDs
**Problem:** Can't trace requests through logs  
**Solution:** Generate correlation ID at start of handler

---

## Quick Reference

**Query Template:**
```csharp
public record GetSomethingQuery(Guid Id, string UserId) 
    : IRequest<SomethingDto>;
```

**Handler Template:**
```csharp
public class GetSomethingQueryHandler : IRequestHandler<GetSomethingQuery, SomethingDto>
{
    public async Task<SomethingDto> Handle(GetSomethingQuery request, CancellationToken ct)
    {
        // 1. Load, 2. Authorize, 3. Map, 4. Return
    }
}
```

**DTO Template:**
```csharp
public class SomethingDto
{
    public Guid Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public string? OptionalField { get; set; }
}
```

**Controller Template:**
```csharp
[HttpGet("{id:guid}")]
[Authorize]
public async Task<IActionResult> GetById(Guid id)
{
    var query = new GetSomethingQuery(id, userId);
    var result = await _mediator.Send(query);
    return Ok(result);
}
```
