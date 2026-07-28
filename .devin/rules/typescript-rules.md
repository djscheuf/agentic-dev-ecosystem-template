---
applies_to:
  - "**/*.ts"
  - "**/*.tsx"
---

# TypeScript Coding Standards

## General Principles

- Enable strict mode in all TypeScript projects
- Prefer type inference where types are obvious
- Use explicit types for function signatures and exports
- Never use `any`; use `unknown` when type is truly unknown
- Follow "Intent Over Implementation" - name things by what they do, not how they work

## TypeScript Configuration

```json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "exactOptionalPropertyTypes": true,
    "forceConsistentCasingInFileNames": true
  }
}
```

## Naming Conventions

| Item | Format | Example |
|------|--------|---------|
| Interface/Type | PascalCase | `UserProfile`, `TacticStatus` |
| Variable/Function | camelCase | `getUserProfile`, `isFormValid` |
| True Constants | SCREAMING_SNAKE_CASE | `MAX_UPLOAD_SIZE`, `API_VERSION` |
| Configuration | camelCase | `apiBaseUrl`, `featureFlags` |
| Enum | PascalCase | `TacticStatus.Draft` |
| Boolean | is/has/can/should | `isLoading`, `hasPermission` |
| Generic | T, U or PascalCase | `T`, `State`, `Action` |

### Examples

```typescript
// Interfaces - no I prefix
interface UserProfile {
  id: string;
  name: string;
  email: string;
}

// Types for unions
type TacticStatus = 'draft' | 'active' | 'archived';
type ApiResponse<T> = { data: T; status: number };

// Constants
const MAX_UPLOAD_SIZE = 5_000_000;
const apiBaseUrl = process.env.API_URL;

// Enums
enum TacticStatus {
  Draft = 'draft',
  Active = 'active',
  Archived = 'archived',
}

// Booleans
const isLoading = false;
const hasPermission = true;
```

## Type Definitions

### Interface vs Type

- **Interface:** Object shapes, component props, domain models
- **Type:** Unions, intersections, mapped types, utilities

```typescript
// Interface for objects
interface UserProfile {
  id: string;
  name: string;
}

// Type for unions and utilities
type TacticStatus = 'draft' | 'active' | 'archived';
type Nullable<T> = T | null;
```

### Utility Types

```typescript
type PartialUser = Partial<User>;
type RequiredUser = Required<User>;
type UserKeys = keyof User;
type PickedUser = Pick<User, "id" | "name">;
type OmittedUser = Omit<User, "password">;

type NonNullableFields<T> = {
  [K in keyof T]: NonNullable<T[K]>;
};
```

### Discriminated Unions

```typescript
type LoadingState = { status: "loading" };
type SuccessState<T> = { status: "success"; data: T };
type ErrorState = { status: "error"; error: string };
type AsyncState<T> = LoadingState | SuccessState<T> | ErrorState;

function handleState<T>(state: AsyncState<T>): void {
  switch (state.status) {
    case "loading": break;
    case "success": console.log(state.data); break;
    case "error": console.error(state.error); break;
  }
}
```

### Type File Organization

```typescript
// domain.types.ts
export enum TacticStatus { Draft = 'draft', Active = 'active' }
export type TacticId = string;
export interface Tactic { id: TacticId; name: string; status: TacticStatus; }
export interface CreateTacticRequest { name: string; description: string; }
export type PartialTactic = Partial<Tactic>;
```

## Functions

```typescript
// Explicit types for exported functions
export function calculateTotal(items: CartItem[]): number {
  return items.reduce((sum, item) => sum + item.price * item.quantity, 0);
}

// Arrow functions
const isAdult = (age: number): boolean => age >= 18;

// Optional parameters with defaults
function greet(name: string, greeting: string = "Hello"): string {
  return `${greeting}, ${name}!`;
}

// Rest parameters
function merge<T extends object>(...objects: T[]): T {
  return Object.assign({}, ...objects);
}

// Async functions - explicit Promise<T>
async function fetchUser(id: string): Promise<User> {
  const response = await fetch(`/api/users/${id}`);
  if (!response.ok) throw new ApiError(`Failed: ${response.status}`);
  return response.json();
}
```

## Error Handling

```typescript
// Custom error classes
class AppError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly statusCode: number = 500
  ) {
    super(message);
    this.name = this.constructor.name;
    Error.captureStackTrace(this, this.constructor);
  }
}

class NotFoundError extends AppError {
  constructor(resource: string, id: string) {
    super(`${resource} with ID ${id} not found`, "NOT_FOUND", 404);
  }
}

// Result type pattern
type Result<T, E = Error> =
  | { success: true; data: T }
  | { success: false; error: E };

function parseJson<T>(json: string): Result<T> {
  try {
    return { success: true, data: JSON.parse(json) };
  } catch (error) {
    return { success: false, error: error as Error };
  }
}
```

## Null/Undefined Handling

```typescript
// Optional chaining
const userName = user?.profile?.name;

// Nullish coalescing
const displayName = user.name ?? "Anonymous";

// Type guards
function isUser(value: unknown): value is User {
  return typeof value === "object" && value !== null && "id" in value;
}

// Non-null assertion (use sparingly with comment)
const element = document.getElementById("app")!; // Known to exist
```

## Avoid `any`

```typescript
// Use unknown with type guards
function processData(data: unknown) {
  if (isValidData(data)) return data.value;
  throw new Error('Invalid data');
}

function isValidData(data: unknown): data is { value: string } {
  return typeof data === 'object' && data !== null && 'value' in data;
}

// Or use generics
function processData<T extends { value: string }>(data: T) {
  return data.value;
}
```

## Imports/Exports

```typescript
// Named exports (preferred)
export function calculateTax(amount: number): number {}
export interface TaxConfig {}
export const TAX_RATE = 0.1;

// Default exports (only for main entry points)
export default class UserService {}

// Import order: Node → External → Internal → Relative
import { readFile } from "fs/promises";
import express from "express";
import { config } from "@/core/config";
import { UserRepository } from "./repositories/UserRepository";
import type { User } from "./types";
```

## Classes

```typescript
class UserService {
  readonly #repository: UserRepository;
  readonly #logger: Logger;

  constructor(repository: UserRepository, logger: Logger) {
    this.#repository = repository;
    this.#logger = logger;
  }

  async getUser(id: string): Promise<User | null> {
    return this.#repository.findById(id);
  }

  #validateUserData(data: CreateUserDto): void {
    if (!data.email.includes("@")) {
      throw new ValidationError("Invalid email");
    }
  }
}
```

## Zod Validation

```typescript
import { z } from "zod";

const userSchema = z.object({
  id: z.string().uuid(),
  email: z.string().email(),
  name: z.string().min(1).max(100),
  role: z.enum(["user", "admin"]),
});

type User = z.infer<typeof userSchema>;

function validateUser(data: unknown): User {
  return userSchema.parse(data);
}

function safeValidateUser(data: unknown): Result<User> {
  const result = userSchema.safeParse(data);
  return result.success
    ? { success: true, data: result.data }
    : { success: false, error: new ValidationError(result.error.message) };
}
```

## Forbidden Practices

- ❌ Never use `any` (use `unknown` + type guards)
- ❌ Never use `@ts-ignore` (use `@ts-expect-error` with comment if required)
- ❌ Never use non-null assertion without justification
- ❌ Never use `var` (use `const` or `let`)
- ❌ Never mutate function parameters
- ❌ Never use `==` or `!=` (use `===` and `!==`)
- ❌ Never leave unused imports or variables
- ❌ Never use `String`, `Number`, `Boolean` constructors
- ❌ Never use `Object` or `Function` as types
- ❌ Never prefix interfaces with `I`
