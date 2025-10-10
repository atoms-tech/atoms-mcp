# Adapter-Kit 🏗️

Architecture patterns for clean, maintainable Python applications: DI Container, Factory, Repository.

## Features

- **🔌 Dependency Injection**: Simple DI container for loose coupling
- **🏭 Factory Pattern**: Registry-based factories for flexible instantiation
- **💾 Repository Pattern**: Abstract data access with in-memory impl
- **🎯 Type-Safe**: Full generic type support

## Quick Start

```python
from adapter_kit import Container, Registry, Repository

# DI Container
container = Container()
container.register(IDatabase, PostgresDatabase, singleton=True)
db = container.resolve(IDatabase)

# Factory Pattern
registry = Registry()
registry.register("postgres", PostgresAdapter)
adapter = registry.create("postgres", dsn="postgresql://...")

# Repository Pattern
class UserRepository(Repository[User, str]):
    async def get_by_id(self, id: str) -> Optional[User]:
        return await self.db.query("users", filters={"id": id})
```

## Examples

### 1. Dependency Injection

```python
from adapter_kit import Container
from abc import ABC, abstractmethod

# Define interfaces
class IEmailService(ABC):
    @abstractmethod
    async def send(self, to: str, subject: str, body: str): pass

class IUserRepository(ABC):
    @abstractmethod
    async def get_by_email(self, email: str): pass

# Implementations
class SendGridEmail(IEmailService):
    async def send(self, to, subject, body):
        print(f"Sending via SendGrid to {to}")

class PostgresUserRepo(IUserRepository):
    async def get_by_email(self, email):
        return {"email": email, "name": "John"}

# Configure container
container = Container()
container.register(IEmailService, SendGridEmail, singleton=True)
container.register(IUserRepository, PostgresUserRepo, singleton=True)

# Resolve dependencies
email_service = container.resolve(IEmailService)
user_repo = container.resolve(IUserRepository)
```

### 2. Factory Pattern with Registry

```python
from adapter_kit import Registry
from abc import ABC, abstractmethod

class StorageBackend(ABC):
    @abstractmethod
    async def upload(self, path: str, data: bytes): pass

class S3Storage(StorageBackend):
    def __init__(self, bucket: str):
        self.bucket = bucket
    
    async def upload(self, path: str, data: bytes):
        print(f"Uploading to S3 bucket {self.bucket}")

class LocalStorage(StorageBackend):
    def __init__(self, base_path: str):
        self.base_path = base_path
    
    async def upload(self, path: str, data: bytes):
        print(f"Uploading to {self.base_path}/{path}")

# Create registry
storage_registry = Registry[StorageBackend]()
storage_registry.register("s3", S3Storage)
storage_registry.register("local", LocalStorage)

# Create instances dynamically
s3 = storage_registry.create("s3", bucket="my-bucket")
local = storage_registry.create("local", base_path="/data")

# List available implementations
print(storage_registry.list_implementations())  # ["s3", "local"]
```

### 3. Repository Pattern

```python
from adapter_kit import Repository
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

@dataclass
class User:
    id: Optional[str]
    email: str
    name: str

class UserRepository(Repository[User, str]):
    def __init__(self, db):
        self.db = db
    
    async def get_by_id(self, id: str) -> Optional[User]:
        data = await self.db.get_single("users", filters={"id": id})
        return User(**data) if data else None
    
    async def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[User]:
        data = await self.db.query("users", filters=filters, limit=limit, offset=offset)
        return [User(**row) for row in data]
    
    async def save(self, user: User) -> User:
        if user.id:
            result = await self.db.update("users", {"email": user.email, "name": user.name}, {"id": user.id})
        else:
            result = await self.db.insert("users", {"email": user.email, "name": user.name})
            user.id = result["id"]
        return user
    
    async def delete(self, id: str) -> bool:
        count = await self.db.delete("users", {"id": id})
        return count > 0
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        return await self.db.count("users", filters)
```

### 4. In-Memory Repository (Testing)

```python
from adapter_kit import InMemoryRepository
from dataclasses import dataclass

@dataclass
class Product:
    id: Optional[int]
    name: str
    price: float

# Use in-memory repo for testing
repo = InMemoryRepository[Product, int]()

# Create
product = Product(id=None, name="Widget", price=9.99)
saved = await repo.save(product)
print(f"Created: {saved.id}")

# Read
found = await repo.get_by_id(saved.id)
print(f"Found: {found.name}")

# List
products = await repo.list(filters={"name": "Widget"})
print(f"Count: {len(products)}")

# Delete
deleted = await repo.delete(saved.id)
```

### 5. Global Container

```python
from adapter_kit import get_container, inject

# Configure global container at startup
container = get_container()
container.register(IDatabase, PostgresDatabase, singleton=True)
container.register(ICache, RedisCache, singleton=True)

# Inject anywhere in your code
def my_function():
    db = inject(IDatabase)
    cache = inject(ICache)
    # Use db and cache
```

### 6. Combined Patterns

```python
from adapter_kit import Container, Registry, Repository

# 1. Factory for creating adapters
adapter_registry = Registry()
adapter_registry.register("postgres", PostgresAdapter)
adapter_registry.register("mysql", MySQLAdapter)

# 2. Use factory to create instance
db_adapter = adapter_registry.create("postgres", dsn="postgresql://...")

# 3. DI for repositories
container = Container()
container.register_instance(IDatabase, db_adapter)
container.register(IUserRepository, UserRepository, singleton=True)

# 4. Repository uses injected database
user_repo = container.resolve(IUserRepository)
users = await user_repo.list(filters={"active": True})
```

## API Reference

### Container

- `register(interface, implementation, singleton=False)` - Register dependency
- `register_instance(interface, instance)` - Register existing instance
- `resolve(interface)` - Resolve dependency
- `clear()` - Clear all registrations

### Registry

- `register(name, implementation)` - Register implementation by name
- `get(name)` - Get implementation class
- `create(name, **kwargs)` - Create instance
- `list_implementations()` - List registered names

### Repository

- `get_by_id(id)` - Get entity by ID
- `list(filters, limit, offset)` - List entities
- `save(entity)` - Save entity (create/update)
- `delete(id)` - Delete entity
- `count(filters)` - Count entities

## Best Practices

1. **Define interfaces** - Use ABC for clean contracts
2. **Singleton for expensive resources** - Database connections, caches
3. **Factory for runtime selection** - Choose implementation at runtime
4. **Repository per aggregate** - One repository per domain entity
5. **Test with InMemoryRepository** - Fast, isolated unit tests

## License

MIT

## Credits

Patterns extracted from Atoms MCP Server and Pheno-SDK projects.
