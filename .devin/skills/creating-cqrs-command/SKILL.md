---
name: creating-cqrs-command
description: How to create a new CQRS Command in the .NET backend API. Use this skill when implementing new write operations (POST, PATCH, DELETE endpoints), adding business logic that modifies state, creating command handlers, or working with MediatR commands. This includes creating the command class, handler, validator, response DTO, and wiring up the controller endpoint. Make sure to use this skill whenever implementing any write operation in the backend API, even if the user just says "add an endpoint" or "implement this feature" - if it modifies data, it needs a command.
---

# Creating a New CQRS Command

## Overview

This skill guides you through creating a new CQRS Command in the Tactic Management API. Commands represent **write operations** that modify system state (POST, PATCH, DELETE, or state-changing POST operations).

**When to use this skill:**
- Adding a new POST endpoint that creates or modifies data
- Implementing PATCH operations for updates
- Creating DELETE endpoints
- Adding business logic that changes tactic status or state
- Implementing any operation that writes to the database

**Architecture Context:**
- **Pattern:** CQRS (Command Query Responsibility Segregation) with MediatR
- **Stack:** .NET 8, Entity Framework Core, FluentValidation
- **Layers:** API → Application → Domain → Infrastructure
- **Testing:** BDD/GWT pattern with xUnit

---

## Complete Implementation Checklist

### Phase 1: Define Domain Models

#### 1.1 Create Command Class
**Location:** `src/api/src/TacticManagement.Application/Tactics/Commands/`

Commands use the **record** pattern and implement `IRequest<TResponse>`:

```csharp
using MediatR;
using TacticManagement.Application.Tactics.DTOs;

namespace TacticManagement.Application.Tactics.Commands;

/// <summary>
/// Command to [describe what this command does].
/// The handler will [describe key responsibilities].
/// </summary>
public record YourCommand(
    Guid TacticId,
    string UserId,
    // Add other parameters as needed
    YourRequest Request
) : IRequest<YourResponse>;
```

**Naming Convention:**
- Pattern: `{Verb}{Noun}Command` (e.g., `CreateTacticCommand`, `MarkTacticProofReadyCommand`)
- Use descriptive verbs: Create, Update, Delete, Mark, Submit, Approve, Reject, Request, Complete
- Always include `UserId` for audit trail
- Include `TacticId` if operating on existing entity

**File Organization:**
- Simple commands: Single file `YourCommand.cs`
- Complex commands: Folder with `YourCommand.cs`, `YourCommandHandler.cs`, `YourCommandValidator.cs`

#### 1.2 Create Request DTO (if needed)
**Location:** `src/api/src/TacticManagement.Application/Tactics/Commands/`

For commands with multiple parameters, create a separate request object:

```csharp
namespace TacticManagement.Application.Tactics.Commands;

public record YourRequest
{
    public string? Description { get; init; }
    public DateTime? StartDate { get; init; }
    public int? SomeReferenceId { get; init; }
    // Use init-only properties
    // Use nullable types for optional fields
}
```

**Patterns:**
- Use `record` for immutability
- Use `init` for properties (not `set`)
- Use nullable types (`?`) for optional fields
- Use `required` keyword for mandatory fields (C# 11+)

#### 1.3 Create Response DTO
**Location:** `src/api/src/TacticManagement.Application/Tactics/DTOs/`

Responses should be **minimal** - only return what's necessary:

```csharp
namespace TacticManagement.Application.Tactics.DTOs;

/// <summary>
/// Response for [YourCommand].
/// </summary>
public record YourResponse(
    Guid TacticId,
    bool Success,
    string? Message = null
);
```

**Response Patterns:**

**For Create operations:**
```csharp
public record CreateTacticResponse(
    Guid Id,
    string Status,
    string OfferCode
);
```

**For Update operations:**
```csharp
public record UpdateTacticResponseDto(
    Guid TacticId,
    DateTime? CampaignStartDate,
    DateTime? CampaignEndDate,
    DateTime? ExpiryDate,
    DateTime? LastModified
);
```

**For Status transitions:**
```csharp
public record MarkTacticProofReadyResponse(
    Guid TacticId,
    bool Success,
    string? Message = null
);
```

**Key Principles:**
- Don't return entire entity - only changed/relevant fields
- Include ID for reference
- Include timestamp for optimistic concurrency
- Use nullable types for optional fields

---

### Phase 2: Create Command Handler

#### 2.1 Handler Class Structure
**Location:** `src/api/src/TacticManagement.Application/Tactics/Commands/`

```csharp
using MediatR;
using Microsoft.Extensions.Logging;
using TacticManagement.Application.Common.Constants;
using TacticManagement.Application.Common.Interfaces;
using TacticManagement.Application.Interfaces;

namespace TacticManagement.Application.Tactics.Commands;

/// <summary>
/// Handler for [describe purpose].
/// Validates [what], performs [what], and returns [what].
/// </summary>
public class YourCommandHandler 
    : IRequestHandler<YourCommand, YourResponse>
{
    private readonly ITacticRepository _tacticRepository;
    private readonly IUserContextService _userContextService;
    private readonly ILogger<YourCommandHandler> _logger;
    // Inject other services as needed

    public YourCommandHandler(
        ITacticRepository tacticRepository,
        IUserContextService userContextService,
        ILogger<YourCommandHandler> logger)
    {
        _tacticRepository = tacticRepository ?? throw new ArgumentNullException(nameof(tacticRepository));
        _userContextService = userContextService ?? throw new ArgumentNullException(nameof(userContextService));
        _logger = logger ?? throw new ArgumentNullException(nameof(logger));
    }

    public async Task<YourResponse> Handle(
        YourCommand request,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(request);

        var correlationId = $"YourCommand-{Guid.NewGuid()}";
        
        _logger.LogDebug("[{CorrelationId}] Starting YourCommand for TacticId: {TacticId}", 
            correlationId, request.TacticId);

        // 1. Load entity
        var tactic = await _tacticRepository.GetByIdAsync(request.TacticId, cancellationToken);
        
        if (tactic == null)
        {
            _logger.LogWarning("[{CorrelationId}] Tactic {TacticId} not found", 
                correlationId, request.TacticId);
            throw new KeyNotFoundException($"Tactic {request.TacticId} not found");
        }

        // 2. Authorization check (if needed)
        var hasAccess = await CheckAuthorizationAsync(request.UserId, tactic, correlationId, cancellationToken);
        if (!hasAccess)
        {
            // Return 404, not 403 (security pattern - don't leak existence)
            throw new KeyNotFoundException($"Tactic {request.TacticId} not found");
        }

        // 3. Business logic validation
        ValidateBusinessRules(tactic, request);

        // 4. Perform state changes
        tactic.SomeProperty = request.Request.SomeValue;
        tactic.LastModified = DateTime.UtcNow;
        tactic.LastModifiedBy = request.UserId;

        // 5. Persist changes
        await _tacticRepository.UpdateAsync(tactic, cancellationToken);

        _logger.LogInformation(
            "[{CorrelationId}] YourCommand completed successfully for TacticId: {TacticId}",
            correlationId, request.TacticId);

        // 6. Return response
        return new YourResponse(
            TacticId: tactic.Id,
            Success: true
        );
    }

    private async Task<bool> CheckAuthorizationAsync(
        string userId, 
        Tactic tactic, 
        string correlationId,
        CancellationToken cancellationToken)
    {
        // Implement authorization logic
        // Use ITacticReadAuthorizationService or IFieldAuthorizationService
        return true;
    }

    private void ValidateBusinessRules(Tactic tactic, YourCommand request)
    {
        // Implement business rule validation
        // Throw ValidationException with ValidationError for failures
    }
}
```

#### 2.2 Common Handler Patterns

**Loading entities with navigation properties:**
```csharp
var tactic = await _tacticRepository.GetByIdWithNavigationPropertiesAsync(
    request.TacticId, 
    cancellationToken);
```

**Authorization using read service:**
```csharp
var hasAccess = await _readAuthService.HasReadAccessAsync(
    request.UserId,
    tactic,
    correlationId,
    cancellationToken);
```

**Field-level authorization (for PATCH operations):**
```csharp
var userContext = await _userContextService.GetUserContextAsync(
    request.UserId, 
    cancellationToken);

await _fieldAuthorizationService.ValidateFieldChangesAsync(
    request, 
    tactic, 
    userContext, 
    cancellationToken);
```

**Idempotent operations:**
```csharp
// Check if already in target state
if (tactic.Status == TacticStatus.TARGET_STATUS)
{
    _logger.LogInformation(
        "[{CorrelationId}] Tactic {TacticId} is already in target state (idempotent)",
        correlationId, request.TacticId);
    
    return new YourResponse(
        TacticId: request.TacticId,
        Success: true,
        Message: "Already in target state"
    );
}
```

**Status transition validation:**
```csharp
if (tactic.Status != TacticStatus.EXPECTED_STATUS)
{
    _logger.LogWarning(
        "[{CorrelationId}] Invalid status transition: current={Current}, expected={Expected}",
        correlationId, tactic.Status, TacticStatus.EXPECTED_STATUS);
    
    var error = new ValidationError(
        Property: "Status",
        ErrorCode: ValidationErrorCodes.Status.InvalidTransition,
        Parameters: new Dictionary<string, object>
        {
            { "currentStatus", tactic.Status.ToString() },
            { "expectedStatus", TacticStatus.EXPECTED_STATUS.ToString() }
        }
    );
    
    throw new ValidationException(error);
}
```

**UTC DateTime enforcement:**
```csharp
// Always use DateTime.UtcNow, never DateTime.Now
tactic.LastModified = DateTime.UtcNow;

// Validate incoming dates are UTC
if (request.StartDate.HasValue && request.StartDate.Value.Kind != DateTimeKind.Utc)
{
    throw new ValidationException(new ValidationError(
        Property: nameof(request.StartDate),
        ErrorCode: ValidationErrorCodes.DateTime.MustBeUtc,
        Parameters: new Dictionary<string, object> { { "field", "StartDate" } }
    ));
}
```

---

### Phase 3: Create FluentValidation Validator

#### 3.1 Validator Class
**Location:** `src/api/src/TacticManagement.Application/Tactics/Validators/`

```csharp
using FluentValidation;
using TacticManagement.Application.Tactics.Commands;

namespace TacticManagement.Application.Tactics.Validators;

public class YourRequestValidator : AbstractValidator<YourRequest>
{
    public YourRequestValidator()
    {
        // Required fields
        RuleFor(x => x.Description)
            .NotEmpty()
            .WithMessage("Description is required.")
            .MaximumLength(100)
            .WithMessage("Description must not exceed 100 characters.");

        // Conditional validation
        RuleFor(x => x.StartDate)
            .NotEmpty()
            .When(x => x.EndDate.HasValue)
            .WithMessage("StartDate is required when EndDate is provided.");

        // Custom validation
        RuleFor(x => x.StartDate)
            .Must(BeInFuture)
            .When(x => x.StartDate.HasValue)
            .WithMessage("StartDate must be in the future.");

        // Async validation
        RuleFor(x => x.ReferenceId)
            .MustAsync(ExistInDatabase)
            .When(x => x.ReferenceId.HasValue)
            .WithMessage("ReferenceId does not exist.");

        // GUID validation
        RuleFor(x => x.EntityId)
            .NotEqual(Guid.Empty)
            .When(x => x.EntityId.HasValue)
            .WithMessage("EntityId must be a valid GUID when provided.");
    }

    private bool BeInFuture(DateTime? startDate)
    {
        return startDate.HasValue && startDate.Value.Date >= DateTime.UtcNow.Date;
    }

    private async Task<bool> ExistInDatabase(int? referenceId, CancellationToken cancellationToken)
    {
        // Implement async validation
        return true;
    }
}
```

#### 3.2 Common Validation Patterns

**String validation:**
```csharp
RuleFor(x => x.Description)
    .NotEmpty()
    .WithMessage("Description is required.")
    .MaximumLength(25)
    .WithMessage("Description must not exceed 25 characters.");
```

**Numeric validation:**
```csharp
RuleFor(x => x.FaceValue)
    .GreaterThan(0)
    .When(x => x.FaceValue.HasValue)
    .WithMessage("FaceValue must be greater than 0.");
```

**Date validation:**
```csharp
RuleFor(x => x.StartDate)
    .Must(BeUtc)
    .When(x => x.StartDate.HasValue)
    .WithMessage("StartDate must be in UTC.");

RuleFor(x => x.EndDate)
    .GreaterThan(x => x.StartDate)
    .When(x => x.StartDate.HasValue && x.EndDate.HasValue)
    .WithMessage("EndDate must be after StartDate.");
```

**Complex object validation:**
```csharp
RuleFor(x => x.Allocations)
    .NotEmpty()
    .WithMessage("At least one allocation is required.")
    .Must(HaveValidAllocations)
    .WithMessage("All allocations must be valid.");

RuleForEach(x => x.Allocations)
    .SetValidator(new AllocationDtoValidator());
```

**Custom validators (reusable):**
```csharp
// In separate file
public class OpCoConsistencyValidator : AbstractValidator<YourRequest>
{
    public OpCoConsistencyValidator()
    {
        RuleFor(x => x)
            .Must(HaveConsistentOpCos)
            .WithMessage("All OpCos must be consistent.");
    }
}

// Use in main validator
Include(new OpCoConsistencyValidator());
```

---

### Phase 4: Wire Up Controller

#### 4.1 Add Controller Action
**Location:** `src/api/src/TacticManagement.Api/Controllers/TacticsController.cs`

```csharp
/// <summary>
/// [Describe what this endpoint does]
/// </summary>
/// <param name="tacticId">The tactic ID</param>
/// <param name="request">The request payload</param>
/// <param name="cancellationToken">Cancellation token</param>
/// <returns>Response with result</returns>
/// <response code="200">Operation successful</response>
/// <response code="400">Validation failed</response>
/// <response code="401">User not authenticated</response>
/// <response code="404">Tactic not found or user not authorized</response>
[HttpPost("{tacticId:guid}/your-action")]
[Authorize(Roles = "Requester,ProofReader")]
[ProducesResponseType(typeof(YourResponse), StatusCodes.Status200OK)]
[ProducesResponseType(typeof(YourResponse), StatusCodes.Status400BadRequest)]
[ProducesResponseType(StatusCodes.Status404NotFound)]
public async Task<IActionResult> YourAction(
    Guid tacticId,
    [FromBody] YourRequest request,
    CancellationToken cancellationToken = default)
{
    var correlationId = Guid.NewGuid().ToString();
    var userId = User.FindFirst(ClaimTypes.NameIdentifier)?.Value 
        ?? throw new UnauthorizedAccessException("User ID not found in claims");

    _logger.LogDebug(
        "[{CorrelationId}] YourAction started - TacticId: {TacticId}, UserId: {UserId}",
        correlationId, tacticId, userId);

    try
    {
        var command = new YourCommand(tacticId, userId, request);
        var response = await _mediator.Send(command, cancellationToken);

        _logger.LogInformation(
            "[{CorrelationId}] YourAction completed successfully - TacticId: {TacticId}",
            correlationId, tacticId);

        return Ok(response);
    }
    catch (KeyNotFoundException ex)
    {
        _logger.LogWarning(
            "[{CorrelationId}] Tactic not found - TacticId: {TacticId}, Error: {Error}",
            correlationId, tacticId, ex.Message);
        return NotFound();
    }
    catch (ValidationException ex)
    {
        _logger.LogWarning(
            "[{CorrelationId}] Validation failed - TacticId: {TacticId}, Errors: {Errors}",
            correlationId, tacticId, ex.Errors);
        
        return BadRequest(new YourResponse(
            TacticId: tacticId,
            Success: false,
            Message: ex.Message
        ));
    }
}
```

#### 4.2 HTTP Method Selection

**POST - Create new resource:**
```csharp
[HttpPost]
[ProducesResponseType(typeof(CreateResponse), StatusCodes.Status201Created)]
public async Task<IActionResult> Create([FromBody] CreateRequest request)
{
    var response = await _mediator.Send(command);
    return CreatedAtAction(nameof(GetById), new { id = response.Id }, response);
}
```

**POST - State transition (non-idempotent):**
```csharp
[HttpPost("{tacticId:guid}/submit")]
[ProducesResponseType(typeof(SubmitResponse), StatusCodes.Status200OK)]
public async Task<IActionResult> Submit(Guid tacticId)
{
    var response = await _mediator.Send(command);
    return Ok(response);
}
```

**PATCH - Partial update:**
```csharp
[HttpPatch("{tacticId:guid}")]
[ProducesResponseType(typeof(UpdateResponse), StatusCodes.Status200OK)]
public async Task<IActionResult> Update(Guid tacticId, [FromBody] UpdateRequest request)
{
    var response = await _mediator.Send(command);
    return Ok(response);
}
```

**DELETE - Remove resource:**
```csharp
[HttpDelete("{tacticId:guid}")]
[ProducesResponseType(StatusCodes.Status204NoContent)]
public async Task<IActionResult> Delete(Guid tacticId)
{
    await _mediator.Send(command);
    return NoContent();
}
```

#### 4.3 Authorization Attributes

```csharp
// Single role
[Authorize(Roles = "Requester")]

// Multiple roles (OR logic)
[Authorize(Roles = "Requester,ProofReader")]

// Multiple roles (AND logic - requires both)
[Authorize(Roles = "Requester")]
[Authorize(Roles = "Admin")]

// No authorization (public endpoint - rare)
[AllowAnonymous]
```

---

### Phase 5: Testing

#### 5.1 Create BDD/GWT Tests
**Location:** `src/api/tests/TacticManagement.Application.Tests/Tactics/Commands/`

```csharp
using FluentAssertions;
using NSubstitute;
using TacticManagement.Application.Tactics.Commands;
using Xunit;

namespace TacticManagement.Application.Tests.Tactics.Commands;

public class YourCommandHandlerTests : IDisposable
{
    private readonly ITacticRepository _tacticRepository;
    private readonly ILogger<YourCommandHandler> _logger;
    private readonly YourCommandHandler _handler;

    public YourCommandHandlerTests()
    {
        _tacticRepository = Substitute.For<ITacticRepository>();
        _logger = Substitute.For<ILogger<YourCommandHandler>>();
        _handler = new YourCommandHandler(_tacticRepository, _logger);
    }

    [Fact]
    public async Task Given_ValidCommand_When_Handle_Then_ReturnsSuccessResponse()
    {
        // Given
        var tacticId = Guid.NewGuid();
        var tactic = new Tactic { Id = tacticId, Status = TacticStatus.DRAFT };
        _tacticRepository.GetByIdAsync(tacticId, Arg.Any<CancellationToken>())
            .Returns(tactic);

        var command = new YourCommand(tacticId, "user@example.com", new YourRequest());

        // When
        var result = await _handler.Handle(command, CancellationToken.None);

        // Then
        result.Should().NotBeNull();
        result.Success.Should().BeTrue();
        result.TacticId.Should().Be(tacticId);
        
        await _tacticRepository.Received(1).UpdateAsync(
            Arg.Is<Tactic>(t => t.Id == tacticId),
            Arg.Any<CancellationToken>());
    }

    [Fact]
    public async Task Given_TacticNotFound_When_Handle_Then_ThrowsKeyNotFoundException()
    {
        // Given
        var tacticId = Guid.NewGuid();
        _tacticRepository.GetByIdAsync(tacticId, Arg.Any<CancellationToken>())
            .Returns((Tactic?)null);

        var command = new YourCommand(tacticId, "user@example.com", new YourRequest());

        // When
        Func<Task> act = async () => await _handler.Handle(command, CancellationToken.None);

        // Then
        await act.Should().ThrowAsync<KeyNotFoundException>()
            .WithMessage($"Tactic {tacticId} not found");
    }

    public void Dispose()
    {
        // Cleanup if needed
    }
}
```

#### 5.2 Validator Tests

```csharp
public class YourRequestValidatorTests
{
    private readonly YourRequestValidator _validator;

    public YourRequestValidatorTests()
    {
        _validator = new YourRequestValidator();
    }

    [Fact]
    public void Given_ValidRequest_When_Validate_Then_NoErrors()
    {
        // Given
        var request = new YourRequest
        {
            Description = "Valid description",
            StartDate = DateTime.UtcNow.AddDays(1)
        };

        // When
        var result = _validator.Validate(request);

        // Then
        result.IsValid.Should().BeTrue();
        result.Errors.Should().BeEmpty();
    }

    [Fact]
    public void Given_EmptyDescription_When_Validate_Then_ReturnsError()
    {
        // Given
        var request = new YourRequest { Description = "" };

        // When
        var result = _validator.Validate(request);

        // Then
        result.IsValid.Should().BeFalse();
        result.Errors.Should().ContainSingle()
            .Which.ErrorMessage.Should().Be("Description is required.");
    }
}
```

---

## Common Patterns & Best Practices

### Correlation IDs
Always generate correlation IDs for tracing:
```csharp
var correlationId = $"YourCommand-{Guid.NewGuid()}";
_logger.LogDebug("[{CorrelationId}] Starting operation", correlationId);
```

### Structured Logging
Use structured logging with named parameters:
```csharp
_logger.LogInformation(
    "[{CorrelationId}] Operation completed - TacticId: {TacticId}, Status: {Status}",
    correlationId, tacticId, status);
```

### Error Handling
- **404 for unauthorized access** (don't leak existence with 403)
- **400 for validation errors** with structured error response
- **500 for unexpected errors** (handled by middleware)

### Security Pattern
Return 404 instead of 403 to prevent information disclosure:
```csharp
if (!hasAccess)
{
    // Don't reveal that the tactic exists
    throw new KeyNotFoundException($"Tactic {request.TacticId} not found");
}
```

### Audit Trail
Always track who made changes and when:
```csharp
tactic.LastModified = DateTime.UtcNow;
tactic.LastModifiedBy = request.UserId;
```

---

## Verification Checklist

Before considering the command complete:

**Domain Layer:**
- [ ] Command class created with `IRequest<TResponse>`
- [ ] Request DTO created (if needed) with init-only properties
- [ ] Response DTO created with minimal fields
- [ ] All DTOs use appropriate nullability

**Application Layer:**
- [ ] Handler implements `IRequestHandler<TCommand, TResponse>`
- [ ] Constructor validates all dependencies (null checks)
- [ ] Correlation ID generated for tracing
- [ ] Entity loaded from repository
- [ ] Authorization checked (if needed)
- [ ] Business rules validated
- [ ] State changes applied
- [ ] Audit fields updated (LastModified, LastModifiedBy)
- [ ] Changes persisted via repository
- [ ] Structured logging at Debug and Information levels

**Validation:**
- [ ] Validator class created extending `AbstractValidator<TRequest>`
- [ ] Required fields validated with `.NotEmpty()`
- [ ] String lengths validated with `.MaximumLength()`
- [ ] Numeric ranges validated with `.GreaterThan()` / `.LessThan()`
- [ ] Dates validated for UTC and future/past constraints
- [ ] Custom business rules validated
- [ ] Error messages are clear and actionable

**API Layer:**
- [ ] Controller action added with proper HTTP method
- [ ] Route template follows conventions
- [ ] Authorization attribute applied with correct roles
- [ ] XML documentation comments added
- [ ] Response type attributes added
- [ ] Correlation ID extracted or generated
- [ ] UserId extracted from claims
- [ ] Command created and sent via MediatR
- [ ] Exceptions handled (KeyNotFoundException, ValidationException)
- [ ] Appropriate HTTP status codes returned

**Testing:**
- [ ] Handler tests created with BDD/GWT pattern
- [ ] Happy path test (valid command succeeds)
- [ ] Entity not found test
- [ ] Authorization failure test (if applicable)
- [ ] Business rule validation tests
- [ ] Validator tests for all rules
- [ ] All tests use NSubstitute for mocking
- [ ] All tests use FluentAssertions for assertions

**Documentation:**
- [ ] XML comments on command class
- [ ] XML comments on handler class
- [ ] XML comments on controller action
- [ ] Swagger annotations complete

---

## Common Pitfalls

### 1. Forgetting UTC DateTime
**Problem:** Using `DateTime.Now` instead of `DateTime.UtcNow`  
**Solution:** Always use UTC, validate incoming dates

### 2. Returning 403 Instead of 404
**Problem:** Leaking information about resource existence  
**Solution:** Return 404 for both "not found" and "not authorized"

### 3. Missing Audit Trail
**Problem:** Not tracking who made changes  
**Solution:** Always set `LastModified` and `LastModifiedBy`

### 4. Overly Complex Responses
**Problem:** Returning entire entity in response  
**Solution:** Return only ID, status, and changed fields

### 5. Missing Validation
**Problem:** Business rules only in handler, not validator  
**Solution:** Put input validation in FluentValidation, business logic in handler

### 6. Incorrect HTTP Method
**Problem:** Using POST for updates  
**Solution:** POST for create/state-change, PATCH for updates, DELETE for removal

### 7. Missing Correlation IDs
**Problem:** Can't trace requests through logs  
**Solution:** Generate correlation ID at start of handler

---

## Quick Reference

**Command Template:**
```csharp
public record YourCommand(Guid TacticId, string UserId, YourRequest Request) 
    : IRequest<YourResponse>;
```

**Handler Template:**
```csharp
public class YourCommandHandler : IRequestHandler<YourCommand, YourResponse>
{
    public async Task<YourResponse> Handle(YourCommand request, CancellationToken ct)
    {
        // 1. Load, 2. Authorize, 3. Validate, 4. Execute, 5. Persist, 6. Return
    }
}
```

**Validator Template:**
```csharp
public class YourRequestValidator : AbstractValidator<YourRequest>
{
    public YourRequestValidator()
    {
        RuleFor(x => x.Field).NotEmpty().WithMessage("Field is required.");
    }
}
```

**Controller Template:**
```csharp
[HttpPost("{tacticId:guid}/action")]
[Authorize(Roles = "Role")]
public async Task<IActionResult> Action(Guid tacticId, [FromBody] Request request)
{
    var command = new YourCommand(tacticId, userId, request);
    var response = await _mediator.Send(command);
    return Ok(response);
}
```
