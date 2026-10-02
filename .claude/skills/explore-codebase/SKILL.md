# Explore Codebase Workflow

## Purpose
Systematically analyze an existing codebase to understand its architecture, patterns, and conventions, producing documentation for consistent development.

## Trigger
- Joining a new project
- Before implementing a significant feature
- Onboarding new team members
- Documenting an undocumented codebase
- Understanding unfamiliar code areas

## Outputs
- Architecture documentation
- Coding standards documentation
- Pattern library
- Dependency map

## Workflow Steps

### Step 1: Project Overview
```
Gather basic information:

PROJECT METADATA:
├── Name: [Project name]
├── Purpose: [What does it do?]
├── Tech stack: [Languages, frameworks, databases]
├── Repository: [Location, structure]
└── Documentation: [Existing docs location]

Commands to run:
$ ls -la                    # Root structure
$ cat README.md             # Project overview
$ cat package.json          # Node.js dependencies
$ cat requirements.txt      # Python dependencies
$ cat *.csproj             # .NET dependencies
```

### Step 2: Analyze Directory Structure
```
Map the codebase organization:

ROOT/
├── src/                    [Source code]
│   ├── controllers/        [Request handlers]
│   ├── services/           [Business logic]
│   ├── models/             [Data structures]
│   ├── repositories/       [Data access]
│   └── utils/              [Utilities]
├── tests/                  [Test files]
├── docs/                   [Documentation]
├── scripts/                [Build/deploy scripts]
├── config/                 [Configuration]
└── infrastructure/         [IaC, Docker, etc.]

Identify patterns:
□ Layered architecture?
□ Feature-based organization?
□ Domain-driven structure?
□ Monorepo or single project?
```

### Step 3: Identify Architecture Pattern
```
Determine the architectural style:

COMMON PATTERNS:
├── Layered/N-Tier
│   └── Presentation → Business → Data
├── Clean Architecture
│   └── Domain → Application → Infrastructure
├── Hexagonal (Ports & Adapters)
│   └── Core with ports, adapters implement
├── Microservices
│   └── Independent deployable services
├── Modular Monolith
│   └── Single deploy, modular internals
└── Event-Driven
    └── Components communicate via events

Document:
- Primary pattern used
- Deviations from pattern
- Boundaries between layers/modules
```

### Step 4: Map Dependencies
```
Analyze external dependencies:

DEPENDENCY CATEGORIES:
├── Web Framework: [Express, ASP.NET, FastAPI, etc.]
├── ORM/Database: [EF Core, Prisma, SQLAlchemy, etc.]
├── Authentication: [Passport, Identity, JWT, etc.]
├── Validation: [Zod, FluentValidation, Pydantic, etc.]
├── Testing: [Jest, xUnit, pytest, etc.]
├── Logging: [Serilog, Winston, structlog, etc.]
└── Other: [List significant dependencies]

Create dependency diagram if complex.
```

### Step 5: Extract Coding Standards
```
Analyze code for conventions:

NAMING CONVENTIONS:
├── Files: [PascalCase, kebab-case, snake_case]
├── Classes: [Pattern observed]
├── Methods: [Pattern observed]
├── Variables: [Pattern observed]
└── Constants: [Pattern observed]

FORMATTING:
├── Indentation: [Spaces/tabs, count]
├── Line length: [Max characters]
├── Braces: [Same line, new line]
└── Quotes: [Single, double]

Check for config files:
- .editorconfig
- .prettierrc
- .eslintrc
- .pylintrc
- .globalconfig (C#)
```

### Step 6: Identify Design Patterns
```
Find recurring patterns in code:

CREATIONAL PATTERNS:
□ Factory (object creation)
□ Builder (complex construction)
□ Singleton (single instance)
□ Dependency Injection (everywhere?)

STRUCTURAL PATTERNS:
□ Repository (data access)
□ Adapter (interface translation)
□ Decorator (add behavior)
□ Facade (simplify interface)

BEHAVIORAL PATTERNS:
□ Strategy (interchangeable algorithms)
□ Observer (event handling)
□ Command (action encapsulation)
□ Mediator (loose coupling)

Document with examples from codebase.
```

### Step 7: Analyze Data Flow
```
Trace how data moves through the system:

REQUEST FLOW (typical web app):
1. Request arrives → [Entry point]
2. Authentication/Authorization → [How?]
3. Validation → [Where, what library?]
4. Business Logic → [Service layer?]
5. Data Access → [Repository pattern?]
6. Response Formation → [DTOs, serialization]
7. Response sent → [Exit point]

EVENT FLOW (if applicable):
1. Event published → [Where, how?]
2. Event routing → [Message broker?]
3. Event handling → [Subscriber pattern?]
4. Side effects → [What happens?]
```

### Step 8: Document Error Handling
```
Understand error patterns:

ERROR STRATEGY:
├── Exception types: [Custom, standard?]
├── Error responses: [Format, structure]
├── Logging: [When, what, where?]
├── Recovery: [Retry, fallback, fail?]
└── User messaging: [How errors presented?]

Find examples:
- Global error handler location
- Custom exception classes
- Error response DTOs
```

### Step 9: Analyze Testing Patterns
```
Review test organization and style:

TEST STRUCTURE:
├── Location: [tests/, __tests__, *.test.ts]
├── Organization: [By feature, by layer, both]
├── Naming: [Convention used]
└── Framework: [Jest, xUnit, pytest, etc.]

TEST PATTERNS:
├── Mocking approach: [Library, style]
├── Test data: [Factories, fixtures, inline]
├── Setup/teardown: [How handled]
└── Coverage: [Tools, thresholds]

Examples to find:
- Unit test example
- Integration test example
- E2E test example (if any)
```

### Step 10: Generate Documentation
```
Compile findings into documentation:
(See Output Templates below)
```

## Output Templates

### Architecture Document
```markdown
# Architecture Documentation: [Project Name]

## Overview
[Brief description of what the system does]

## Tech Stack
| Layer | Technology | Purpose |
|-------|------------|---------|
| Web Framework | [X] | HTTP handling |
| Database | [X] | Data persistence |
| ORM | [X] | Data access |
| Auth | [X] | Authentication |
| Testing | [X] | Automated tests |

## Architecture Pattern
**Style:** [e.g., Clean Architecture]

### Layer Diagram
```
[ASCII diagram or description]
```

### Layer Responsibilities
1. **Presentation/API**: [description]
2. **Application/Services**: [description]
3. **Domain/Core**: [description]
4. **Infrastructure**: [description]

## Directory Structure
```
src/
├── [folder]/ - [purpose]
├── [folder]/ - [purpose]
└── [folder]/ - [purpose]
```

## Key Components
| Component | Location | Responsibility |
|-----------|----------|----------------|
| [Name] | [Path] | [What it does] |

## Data Flow
1. [Step 1]
2. [Step 2]
3. [Step 3]

## External Dependencies
[List of external services/APIs used]

## Deployment
[How the application is deployed]
```

### Coding Standards Document
```markdown
# Coding Standards: [Project Name]

## Naming Conventions

### Files
- **Pattern:** [PascalCase/kebab-case/etc.]
- **Examples:** `UserService.ts`, `order-controller.py`

### Classes/Types
- **Pattern:** [PascalCase]
- **Examples:** `UserRepository`, `OrderDto`

### Functions/Methods
- **Pattern:** [camelCase/snake_case]
- **Examples:** `getUserById`, `calculate_total`

### Variables
- **Pattern:** [camelCase/snake_case]
- **Private fields:** [prefix convention]
- **Constants:** [UPPER_SNAKE_CASE]

## Code Organization

### File Structure
Each file should contain:
1. [Imports organization]
2. [Type definitions]
3. [Implementation]

### Class Structure
Members ordered as:
1. [Constants]
2. [Fields]
3. [Constructor]
4. [Public methods]
5. [Private methods]

## Formatting

### General
- Indentation: [X spaces/tabs]
- Line length: [max characters]
- Trailing commas: [yes/no]

### Tools
- Formatter: [Prettier/Black/etc.]
- Linter: [ESLint/Pylint/etc.]
- Config file: [location]

## Patterns in Use

### Dependency Injection
[How DI is used in this project]
```[language]
// Example from codebase
```

### Repository Pattern
[How repositories are structured]
```[language]
// Example from codebase
```

### Error Handling
[How errors are handled]
```[language]
// Example from codebase
```

## Testing Conventions

### Test Naming
- Pattern: `[Method]_[Scenario]_[Expected]`
- Example: `GetUser_WithInvalidId_ReturnsNull`

### Test Structure
- Arrange-Act-Assert pattern
- [Mocking library used]
- [Test data approach]

## Git Conventions

### Branch Naming
- Feature: `feature/[description]`
- Bugfix: `fix/[description]`
- Release: `release/[version]`

### Commit Messages
[Convention used: Conventional Commits, etc.]
```

### Pattern Library
```markdown
# Pattern Library: [Project Name]

## Creational Patterns

### Factory Example
**Location:** `src/factories/UserFactory.ts`
**Usage:** Creating user instances with defaults
```[language]
// Code example
```

### Builder Example
**Location:** `src/builders/QueryBuilder.ts`
**Usage:** Constructing complex queries
```[language]
// Code example
```

## Structural Patterns

### Repository Example
**Location:** `src/repositories/UserRepository.ts`
**Usage:** Data access abstraction
```[language]
// Code example
```

## Behavioral Patterns

### Service Pattern
**Location:** `src/services/OrderService.ts`
**Usage:** Business logic encapsulation
```[language]
// Code example
```

## Testing Patterns

### Unit Test Example
**Location:** `tests/services/OrderService.test.ts`
```[language]
// Code example
```

### Integration Test Example
**Location:** `tests/integration/api.test.ts`
```[language]
// Code example
```
```

## Quality Checks
- [ ] Architecture pattern identified
- [ ] All layers documented
- [ ] Dependencies mapped
- [ ] Coding standards extracted
- [ ] Patterns catalogued
- [ ] Data flow documented
- [ ] Testing approach understood
- [ ] Documentation generated

## Next Workflows
→ `planning`: Plan implementation with context
→ `analyze-user-story`: Analyze story with codebase knowledge
→ `tdd-workflow`: Start implementation following standards, NOT AVAILABLE
