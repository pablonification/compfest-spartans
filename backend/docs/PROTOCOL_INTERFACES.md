# Protocol-Based Interfaces in SmartBin Backend

## Overview

This document explains the modern approach to defining interfaces in the SmartBin backend using Python's `typing.Protocol` instead of traditional Abstract Base Classes (ABCs).

## Why Protocol Over ABC?

### Traditional ABC Approach (Old Way)

```python
from abc import ABC, abstractmethod

class UserRepository(ABC):
    @abstractmethod
    async def create_user(self, user: User) -> User:
        pass

    @abstractmethod
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        pass
```

### Modern Protocol Approach (New Way)

```python
from typing import Protocol

class UserRepository(Protocol):
    async def create_user(self, user: User) -> User:
        ...

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        ...
```

## Benefits of Protocol-Based Interfaces

### 1. **Structural Typing**

- Protocols focus on **what** an object can do, not **what** it inherits from
- Any class that implements the required methods automatically satisfies the Protocol
- No need to explicitly inherit or register

### 2. **Better Performance**

- No runtime overhead from ABC machinery
- No `@abstractmethod` decorators to process
- Direct method calls without indirection

### 3. **More Pythonic**

- Follows Python's "duck typing" philosophy
- Easier to understand and implement
- Less boilerplate code

### 4. **Better IDE Support**

- Modern IDEs provide excellent autocomplete and type checking
- Better static analysis tools support
- Clearer error messages

## Current Protocol Interfaces

### UserRepository Protocol

```python
class UserRepository(Protocol):
    """Protocol interface for user data operations."""

    async def create_user(self, user: User) -> User:
        """Create a new user in the database."""
        ...

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Retrieve a user by their ID."""
        ...

    # ... other methods
```

**Purpose**: Defines the contract for user data persistence operations.

**Implementations**:

- `MongoDBUserRepository`: MongoDB-based implementation
- `MockUserRepository`: In-memory implementation for testing

### AuthService Protocol

```python
class AuthService(Protocol):
    """Protocol interface for authentication operations."""

    def create_access_token(self, user_id: str, email: str) -> str:
        """Create a JWT access token for a user."""
        ...

    def verify_token(self, token: str, token_type: str = "access") -> JWTPayload:
        """Verify and decode a JWT token."""
        ...

    # ... other methods
```

**Purpose**: Defines the contract for JWT token operations.

**Implementations**:

- `JWTAuthService`: JWT-based authentication service

### OAuthService Protocol

```python
class OAuthService(Protocol):
    """Protocol interface for OAuth operations."""

    def generate_authorization_url(self) -> Tuple[str, str]:
        """Generate OAuth authorization URL with state parameter."""
        ...

    async def exchange_code_for_tokens(self, code: str, state: str) -> OAuthToken:
        """Exchange authorization code for access and refresh tokens."""
        ...

    # ... other methods
```

**Purpose**: Defines the contract for OAuth provider operations.

**Implementations**:

- `GoogleOAuthService`: Google OAuth 2.0 implementation

## Usage Examples

### 1. **Service Factory Pattern (Best Practice)**

```python
from __future__ import annotations
from typing import TYPE_CHECKING

from src.backend.domain.interfaces import UserRepository, AuthService
from src.backend.services.service_factory import ServiceFactory

if TYPE_CHECKING:
    from src.backend.services.user_service import UserService

# Get services through factory
factory = ServiceFactory()
user_repo: UserRepository = factory.user_repository
auth_service: AuthService = factory.auth_service

# Use services
user = await user_repo.get_user_by_id("123")
token = auth_service.create_access_token("123", "user@example.com")
```

**Key Benefits**:

- ✅ **Perfect type safety** without runtime cost
- ✅ **Zero circular import issues** using TYPE_CHECKING
- ✅ **Full IDE support** and autocomplete
- ✅ **Clean, maintainable code**

### 2. **Dependency Injection**

```python
class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def get_user(self, user_id: str) -> Optional[User]:
        return await self.user_repository.get_user_by_id(user_id)

# Usage with different implementations
user_service = UserService(MongoDBUserRepository())  # Production
user_service = UserService(MockUserRepository())     # Testing
```

### 3. **Testing with Mocks**

```python
class MockUserRepository:
    """Mock implementation that satisfies UserRepository Protocol."""

    def __init__(self):
        self.users = {}

    async def create_user(self, user: User) -> User:
        user.id = "mock_id"
        self.users[user.id] = user
        return user

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        return self.users.get(user_id)

# Type checker knows this is valid
repository: UserRepository = MockUserRepository()
```

## Creating New Protocol Interfaces

### Step 1: Define the Protocol

```python
from typing import Protocol, List

class ScanRepository(Protocol):
    """Protocol interface for scan data operations."""

    async def create_scan(self, scan: Scan) -> Scan:
        """Create a new scan."""
        ...

    async def get_scans_by_user(self, user_id: str) -> List[Scan]:
        """Get all scans for a user."""
        ...
```

### Step 2: Implement the Protocol

```python
class MongoDBScanRepository:
    """MongoDB implementation of ScanRepository Protocol."""

    async def create_scan(self, scan: Scan) -> Scan:
        # Implementation here
        pass

    async def get_scans_by_user(self, user_id: str) -> List[Scan]:
        # Implementation here
        pass

# Type checker automatically recognizes this as valid
repository: ScanRepository = MongoDBScanRepository()
```

### Step 3: Use in Services

```python
class ScanService:
    def __init__(self, scan_repository: ScanRepository):
        self.scan_repository = scan_repository

    async def create_user_scan(self, user_id: str, scan_data: dict) -> Scan:
        scan = Scan(user_id=user_id, **scan_data)
        return await self.scan_repository.create_scan(scan)
```

## Best Practices

### 1. **Use `...` for Method Bodies**

```python
class MyProtocol(Protocol):
    def my_method(self) -> str:
        ...  # Use ... not pass
```

### 2. **Keep Protocols Focused**

```python
# Good: Single responsibility
class UserReader(Protocol):
    async def get_user(self, user_id: str) -> Optional[User]:
        ...

# Avoid: Too many responsibilities
class UserManager(Protocol):
    async def get_user(self, user_id: str) -> Optional[User]:
        ...
    async def create_user(self, user: User) -> User:
        ...
    async def update_user(self, user: User) -> User:
        ...
    async def delete_user(self, user_id: str) -> bool:
        ...
```

### 3. **Document Protocol Methods**

```python
class UserRepository(Protocol):
    """Protocol interface for user data operations."""

    async def create_user(self, user: User) -> User:
        """Create a new user in the database.

        Args:
            user: User instance to create

        Returns:
            Created user with assigned ID

        Raises:
            UserAlreadyExistsError: If user with same email exists
        """
        ...
```

### 4. **Use Type Hints Consistently**

```python
from typing import Protocol, Optional, List, Dict, Any

class DataProcessor(Protocol):
    def process(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        ...

    def validate(self, item: Dict[str, Any]) -> bool:
        ...
```

### 5. **Handle Circular Imports with TYPE_CHECKING (Best Practice)**

```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .user_service import UserService

class ServiceFactory:
    def create_user_service(self) -> UserService:  # ✅ Perfect type hint
        from .user_service import UserService      # ✅ Runtime import only when needed
        return UserService(user_repository=self.user_repository)
```

## Migration from ABC to Protocol

### Before (ABC)

```python
from abc import ABC, abstractmethod

class UserRepository(ABC):
    @abstractmethod
    async def create_user(self, user: User) -> User:
        pass
```

### After (Protocol)

```python
from typing import Protocol

class UserRepository(Protocol):
    async def create_user(self, user: User) -> User:
        ...
```

### Key Changes

1. Replace `ABC` with `Protocol`
2. Remove `@abstractmethod` decorators
3. Replace `pass` with `...`
4. Remove explicit inheritance requirements

## Testing Protocol Compliance

### Runtime Type Checking

```python
from typing import runtime_checkable

@runtime_checkable
class UserRepository(Protocol):
    async def create_user(self, user: User) -> User:
        ...

# Runtime check
repository = MongoDBUserRepository()
isinstance(repository, UserRepository)  # True
```

### Static Type Checking

```python
# MyPy will catch this at type-checking time
def process_user(repository: UserRepository, user: User) -> User:
    return repository.create_user(user)  # Type checker validates this

# This would cause a type error if MockUserRepository doesn't implement the Protocol
mock_repo = MockUserRepository()
process_user(mock_repo, user)  # Type checker validates compliance
```

## Conclusion

Protocol-based interfaces provide a modern, Pythonic approach to defining contracts in your codebase. They offer:

- **Better performance** than ABCs
- **Cleaner syntax** with less boilerplate
- **Better IDE support** and type checking
- **More flexible** implementation requirements
- **Easier testing** and mocking

By adopting Protocol-based interfaces with proper TYPE_CHECKING imports for circular dependencies, the SmartBin backend becomes more maintainable, testable, and follows modern Python best practices.

## References

- [Python Typing Documentation](https://docs.python.org/3/library/typing.html#protocols)
- [PEP 544 - Protocols](https://www.python.org/dev/peps/pep-0544/)
- [MyPy Protocol Documentation](https://mypy.readthedocs.io/en/stable/protocols.html)
- [Python TYPE_CHECKING Best Practices](https://docs.python.org/3/library/typing.html#typing.TYPE_CHECKING)
