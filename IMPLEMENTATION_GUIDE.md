# Atoms-MCP-Prod: Implementation Guide

## Step-by-Step Refactor Instructions

### Phase 1: Setup New Structure (Day 1)

#### 1.1 Create Directory Structure

```bash
cd atoms-mcp-prod

# Create new hexagonal structure
mkdir -p src/atoms_mcp/{domain,application,adapters,infrastructure}
mkdir -p src/atoms_mcp/domain/{models,services,ports}
mkdir -p src/atoms_mcp/application/{commands,queries,workflows}
mkdir -p src/atoms_mcp/adapters/{primary,secondary}
mkdir -p src/atoms_mcp/adapters/primary/{mcp,cli}
mkdir -p src/atoms_mcp/adapters/secondary/{supabase,vertex,pheno,cache}
mkdir -p src/atoms_mcp/infrastructure/{config,logging,errors}

# Create new test structure
mkdir -p tests/{unit,integration,performance}
mkdir -p tests/unit/{domain,application,infrastructure}
mkdir -p tests/integration/adapters
```

#### 1.2 Create __init__.py Files

```bash
# Create all __init__.py files
find src/atoms_mcp -type d -exec touch {}/__init__.py \;
find tests -type d -exec touch {}/__init__.py \;
```

### Phase 2: Domain Layer (Days 2-3)

#### 2.1 Create Domain Models

**File: `src/atoms_mcp/domain/models/entity.py`**

```python
"""Entity domain model - pure Python, no external dependencies."""

from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Any

@dataclass
class Entity:
    """Core entity domain model."""
    
    id: str
    type: str
    data: dict[str, Any]
    workspace_id: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    
    def update(self, data: dict[str, Any]) -> None:
        """Update entity data with business rules."""
        # Business rule: Don't allow empty updates
        if not data:
            raise ValueError("Cannot update with empty data")
        
        self.data.update(data)
        self.updated_at = datetime.now(UTC)
    
    def validate(self) -> bool:
        """Validate entity according to business rules."""
        # Business rule: Entity must have required fields
        if not self.id or not self.type or not self.workspace_id:
            return False
        
        # Business rule: Type-specific validation
        if self.type == "project" and "name" not in self.data:
            return False
        
        return True
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "type": self.type,
            "data": self.data,
            "workspace_id": self.workspace_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
```

#### 2.2 Create Domain Ports (Interfaces)

**File: `src/atoms_mcp/domain/ports/repository.py`**

```python
"""Repository port - interface for data access."""

from abc import ABC, abstractmethod
from typing import Protocol
from atoms_mcp.domain.models.entity import Entity

class EntityRepository(Protocol):
    """Entity repository interface (port)."""
    
    async def save(self, entity: Entity) -> None:
        """Save entity to storage."""
        ...
    
    async def get(self, entity_id: str) -> Entity | None:
        """Get entity by ID."""
        ...
    
    async def delete(self, entity_id: str) -> None:
        """Delete entity by ID."""
        ...
    
    async def list_by_type(self, entity_type: str, workspace_id: str) -> list[Entity]:
        """List entities by type in workspace."""
        ...
    
    async def search(self, query: str, workspace_id: str) -> list[Entity]:
        """Search entities by query."""
        ...
```

#### 2.3 Create Domain Services

**File: `src/atoms_mcp/domain/services/entity_service.py`**

```python
"""Entity service - business logic."""

from atoms_mcp.domain.models.entity import Entity
from atoms_mcp.domain.ports.repository import EntityRepository
import uuid

class EntityService:
    """Entity business logic service."""
    
    def __init__(self, repository: EntityRepository):
        """Initialize with repository dependency."""
        self._repository = repository
    
    async def create_entity(
        self,
        entity_type: str,
        data: dict,
        workspace_id: str
    ) -> Entity:
        """Create new entity with business rules."""
        # Business rule: Generate unique ID
        entity_id = str(uuid.uuid4())
        
        # Create entity
        entity = Entity(
            id=entity_id,
            type=entity_type,
            data=data,
            workspace_id=workspace_id
        )
        
        # Business rule: Validate before saving
        if not entity.validate():
            raise ValueError(f"Invalid entity data for type {entity_type}")
        
        # Save to repository
        await self._repository.save(entity)
        
        return entity
    
    async def update_entity(
        self,
        entity_id: str,
        data: dict
    ) -> Entity:
        """Update entity with business rules."""
        # Get existing entity
        entity = await self._repository.get(entity_id)
        if not entity:
            raise ValueError(f"Entity {entity_id} not found")
        
        # Update with business rules
        entity.update(data)
        
        # Validate after update
        if not entity.validate():
            raise ValueError("Invalid entity data after update")
        
        # Save updated entity
        await self._repository.save(entity)
        
        return entity
```

### Phase 3: Application Layer (Days 4-5)

#### 3.1 Create Commands (Write Operations)

**File: `src/atoms_mcp/application/commands/create_entity.py`**

```python
"""Create entity command - application use case."""

from dataclasses import dataclass
from atoms_mcp.domain.services.entity_service import EntityService
from atoms_mcp.domain.ports.cache import CachePort
from atoms_mcp.domain.ports.embeddings import EmbeddingsPort

@dataclass
class CreateEntityCommand:
    """Create entity use case."""

    entity_service: EntityService
    cache: CachePort
    embeddings: EmbeddingsPort | None = None

    async def execute(
        self,
        entity_type: str,
        data: dict,
        workspace_id: str
    ) -> dict:
        """Execute create entity command."""
        # 1. Create entity (domain logic)
        entity = await self.entity_service.create_entity(
            entity_type=entity_type,
            data=data,
            workspace_id=workspace_id
        )

        # 2. Generate embeddings if enabled and content exists
        if self.embeddings and data.get("content"):
            embedding = await self.embeddings.generate(data["content"])
            await self.embeddings.store(entity.id, embedding)

        # 3. Invalidate cache
        cache_key = f"entities:{entity_type}:{workspace_id}"
        await self.cache.invalidate(cache_key)

        # 4. Return result
        return entity.to_dict()
```

#### 3.2 Create Queries (Read Operations)

**File: `src/atoms_mcp/application/queries/get_entity.py`**

```python
"""Get entity query - application use case."""

from dataclasses import dataclass
from atoms_mcp.domain.ports.repository import EntityRepository
from atoms_mcp.domain.ports.cache import CachePort

@dataclass
class GetEntityQuery:
    """Get entity use case."""

    repository: EntityRepository
    cache: CachePort

    async def execute(self, entity_id: str) -> dict | None:
        """Execute get entity query with caching."""
        # 1. Check cache
        cache_key = f"entity:{entity_id}"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        # 2. Get from repository
        entity = await self.repository.get(entity_id)
        if not entity:
            return None

        # 3. Cache result
        result = entity.to_dict()
        await self.cache.set(cache_key, result, ttl=300)  # 5 min TTL

        return result
```

### Phase 4: Adapters (Days 6-8)

#### 4.1 Configuration (Single Source of Truth)

**File: `src/atoms_mcp/infrastructure/config/settings.py`**

```python
"""Single configuration file - replaces 8 old config files."""

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class AtomsSettings(BaseSettings):
    """Single source of truth for all configuration."""

    model_config = SettingsConfigDict(
        env_prefix='ATOMS_',
        env_file='.env',
        env_file_encoding='utf-8',
        env_nested_delimiter='__',
        case_sensitive=False,
        extra='ignore'
    )

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Database (Supabase) - REQUIRED
    supabase_url: SecretStr
    supabase_anon_key: SecretStr
    supabase_service_key: SecretStr | None = None

    # Auth (WorkOS) - REQUIRED
    workos_client_id: str
    workos_api_key: SecretStr

    # AI (Vertex) - REQUIRED
    google_project_id: str
    google_location: str = "us-central1"
    google_credentials_json: SecretStr | None = None

    # Features
    enable_embeddings: bool = True
    enable_cache: bool = True

    # Logging
    log_level: str = "INFO"

    @classmethod
    def load(cls) -> "AtomsSettings":
        """Load settings with environment detection."""
        return cls()

    def get_supabase_url(self) -> str:
        """Get Supabase URL as plain string."""
        return self.supabase_url.get_secret_value()

    def get_supabase_anon_key(self) -> str:
        """Get Supabase anon key as plain string."""
        return self.supabase_anon_key.get_secret_value()
```

#### 4.2 Pheno-SDK Adapter (Optional with Fallback)

**File: `src/atoms_mcp/adapters/secondary/pheno/__init__.py`**

```python
"""Pheno-SDK adapter - optional dependency with graceful fallback."""

from typing import Protocol
import logging

# Define interfaces (ports)
class TunnelProvider(Protocol):
    """Tunnel provider interface."""
    async def start(self, port: int) -> str: ...
    async def stop(self) -> None: ...

class LoggerProvider(Protocol):
    """Logger provider interface."""
    def info(self, msg: str) -> None: ...
    def error(self, msg: str) -> None: ...
    def debug(self, msg: str) -> None: ...

# Try to import pheno-sdk
try:
    from pheno.infra.tunneling import AsyncTunnelManager
    from pheno.observability import get_logger as pheno_get_logger
    PHENO_AVAILABLE = True
except ImportError:
    PHENO_AVAILABLE = False
    AsyncTunnelManager = None
    pheno_get_logger = None

def get_tunnel_provider() -> TunnelProvider | None:
    """Get tunnel provider if available."""
    if PHENO_AVAILABLE and AsyncTunnelManager:
        return AsyncTunnelManager()
    return None  # Graceful degradation

def get_logger(name: str) -> LoggerProvider:
    """Get logger (pheno-sdk or stdlib fallback)."""
    if PHENO_AVAILABLE and pheno_get_logger:
        return pheno_get_logger(name)
    # Fallback to stdlib logging
    return logging.getLogger(name)

# Export availability flag
__all__ = ['get_tunnel_provider', 'get_logger', 'PHENO_AVAILABLE']
```


