# Python Coding Standards for Windsurf

## General Principles

- Follow PEP 8 style guide with minor practical exceptions
- Write code for Python 3.10+ unless project requires otherwise
- Use type hints consistently throughout the codebase
- Prefer explicit over implicit; readability counts

## Code Formatting

- Use a formatter (Black or Ruff) with default settings
- Maximum line length: 88 characters (Black default)
- Use 4 spaces for indentation (never tabs)
- Two blank lines between top-level definitions
- One blank line between method definitions

## Naming Conventions

```python
# Modules and packages: lowercase with underscores
user_service.py
data_processing/

# Classes: PascalCase
class UserRepository:
    pass

# Functions and variables: snake_case
def calculate_total_price(items: list[Item]) -> Decimal:
    total_amount = Decimal("0")
    return total_amount

# Constants: UPPER_SNAKE_CASE
MAX_RETRY_COUNT = 3
DEFAULT_TIMEOUT_SECONDS = 30

# Private attributes: single leading underscore
class Service:
    def __init__(self):
        self._internal_cache = {}
    
    def _helper_method(self):
        pass

# "Protected" by convention: single underscore
# Name mangling (avoid unless necessary): double underscore prefix
```

## Type Hints

- Use type hints for all function signatures
- Use type hints for class attributes
- Import types from `typing` module for complex types
- Use `|` union syntax (Python 3.10+) instead of `Union`

```python
from typing import TypeVar, Generic, Protocol
from collections.abc import Callable, Iterable, Mapping

# Basic type hints
def greet(name: str) -> str:
    return f"Hello, {name}"

# Optional values (use | None, not Optional)
def find_user(user_id: int) -> User | None:
    pass

# Collections
def process_items(items: list[str]) -> dict[str, int]:
    pass

# Callable types
def apply_transform(
    data: list[int],
    transform: Callable[[int], int]
) -> list[int]:
    return [transform(x) for x in data]

# Generic types
T = TypeVar("T")

class Repository(Generic[T]):
    def get(self, id: int) -> T | None:
        pass

# Protocols for structural typing
class Serializable(Protocol):
    def to_dict(self) -> dict[str, any]:
        ...
```

## Imports

- Group imports in order: standard library, third-party, local
- Separate groups with a blank line
- Use absolute imports; avoid relative imports except in packages
- Never use `from module import *`

```python
# Standard library
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Third-party
import httpx
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

# Local application
from app.core.config import settings
from app.models.user import User
from app.services.email import EmailService
```

## Classes and Data Structures

### Dataclasses and Pydantic
```python
from dataclasses import dataclass, field
from pydantic import BaseModel, Field

# Use dataclasses for simple data containers
@dataclass
class Point:
    x: float
    y: float
    
    def distance_from_origin(self) -> float:
        return (self.x ** 2 + self.y ** 2) ** 0.5

# Use frozen dataclasses for immutable data
@dataclass(frozen=True)
class UserId:
    value: int

# Use Pydantic for validation and serialization
class UserCreate(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)
    name: str = Field(..., min_length=1, max_length=100)
    age: int = Field(..., ge=0, le=150)

    class Config:
        str_strip_whitespace = True
```

### Class Design
```python
class UserService:
    """Service for user-related operations."""
    
    def __init__(
        self,
        repository: UserRepository,
        email_service: EmailService,
    ) -> None:
        self._repository = repository
        self._email_service = email_service
    
    def create_user(self, data: UserCreate) -> User:
        """Create a new user and send welcome email."""
        user = self._repository.create(data)
        self._email_service.send_welcome(user.email)
        return user
```

## Functions

- Keep functions small and focused (single responsibility)
- Use keyword-only arguments for clarity when appropriate
- Provide sensible defaults where possible
- Return early to avoid deep nesting

```python
# Use keyword-only arguments (after *)
def create_connection(
    host: str,
    port: int,
    *,
    timeout: float = 30.0,
    ssl: bool = True,
    retry_count: int = 3,
) -> Connection:
    pass

# Return early pattern
def process_order(order: Order) -> Result:
    if not order.items:
        return Result.failure("Order has no items")
    
    if order.is_cancelled:
        return Result.failure("Order is cancelled")
    
    # Main logic here
    return Result.success(processed_order)
```

## Error Handling

- Use specific exception types, not bare `except:`
- Create custom exceptions for domain errors
- Use context managers for resource management
- Prefer EAFP (Easier to Ask Forgiveness than Permission)

```python
# Custom exceptions
class DomainError(Exception):
    """Base exception for domain errors."""
    pass

class UserNotFoundError(DomainError):
    """Raised when a user cannot be found."""
    def __init__(self, user_id: int) -> None:
        self.user_id = user_id
        super().__init__(f"User with ID {user_id} not found")

# Proper exception handling
def get_user(user_id: int) -> User:
    try:
        return repository.get(user_id)
    except DatabaseError as e:
        logger.error("Database error fetching user %d: %s", user_id, e)
        raise ServiceUnavailableError("Database unavailable") from e

# Context managers for resources
from contextlib import contextmanager

@contextmanager
def database_transaction():
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
```

## Async Programming

- Use `async`/`await` for I/O-bound operations
- Never mix sync and async code without proper handling
- Use `asyncio.gather` for concurrent operations
- Always handle cancellation properly

```python
import asyncio
from typing import AsyncIterator

async def fetch_user(client: httpx.AsyncClient, user_id: int) -> User:
    response = await client.get(f"/users/{user_id}")
    response.raise_for_status()
    return User(**response.json())

async def fetch_all_users(user_ids: list[int]) -> list[User]:
    async with httpx.AsyncClient(base_url=API_URL) as client:
        tasks = [fetch_user(client, uid) for uid in user_ids]
        return await asyncio.gather(*tasks)

# Async generators
async def stream_items(url: str) -> AsyncIterator[Item]:
    async with httpx.AsyncClient() as client:
        async with client.stream("GET", url) as response:
            async for line in response.aiter_lines():
                yield Item.parse(line)
```

## Logging

- Use the `logging` module, never `print()` for production code
- Use lazy formatting with `%` style in log calls
- Include contextual information in log messages

```python
import logging

logger = logging.getLogger(__name__)

def process_order(order_id: int) -> None:
    logger.info("Processing order %d", order_id)
    
    try:
        result = do_processing()
        logger.debug("Order %d processed: %s", order_id, result)
    except ProcessingError as e:
        logger.exception("Failed to process order %d", order_id)
        raise
```

## Documentation

- Write docstrings for all public modules, classes, and functions
- Use Google-style docstrings
- Include type information in docstrings only if not using type hints

```python
def calculate_discount(
    price: Decimal,
    discount_percent: float,
    *,
    max_discount: Decimal | None = None,
) -> Decimal:
    """Calculate the discounted price.
    
    Applies the specified percentage discount to the price,
    optionally capping the discount at a maximum value.
    
    Args:
        price: Original price before discount.
        discount_percent: Discount percentage (0-100).
        max_discount: Maximum discount amount allowed.
    
    Returns:
        The price after applying the discount.
    
    Raises:
        ValueError: If discount_percent is not between 0 and 100.
    
    Example:
        >>> calculate_discount(Decimal("100"), 15.0)
        Decimal("85.00")
    """
```

## Project Structure

```
project/
├── src/
│   └── project_name/
│       ├── __init__.py
│       ├── main.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── config.py
│       │   └── exceptions.py
│       ├── models/
│       │   ├── __init__.py
│       │   └── user.py
│       ├── services/
│       │   ├── __init__.py
│       │   └── user_service.py
│       └── repositories/
│           ├── __init__.py
│           └── user_repository.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── test_user_service.py
├── pyproject.toml
└── README.md
```

## Forbidden Practices

- No mutable default arguments: `def f(items=[]):`
- No bare `except:` clauses
- No `from module import *`
- No global mutable state
- No `eval()` or `exec()` with untrusted input
- No hardcoded secrets or credentials
- No ignoring type checker errors without documented reason
