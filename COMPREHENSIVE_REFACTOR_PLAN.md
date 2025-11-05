# Atoms-MCP-Prod: Comprehensive Refactor Plan
## Hexagonal Architecture & Optimization Strategy

**Date:** 2025-10-31  
**Current State:** 248 Python files, ~56K LOC (code), ~15K LOC (comments)  
**Goal:** Reduce to ~20-25K LOC, eliminate duplication, hexagonal architecture, optimize pheno-sdk usage

---

## Executive Summary

### Current Issues Identified
1. **Massive Duplication**: 3 separate CLI implementations (`atoms`, `atoms_cli.py`, `atoms_cli_enhanced.py`)
2. **Configuration Chaos**: 4 different config systems (`config/`, `settings/`, `config.yml`, YAML loaders)
3. **Scattered Architecture**: Code split across `server/`, `src/`, `lib/`, `tools/`, `utils/`
4. **Pheno-SDK Misuse**: Direct imports scattered everywhere instead of adapter pattern
5. **Entry Point Confusion**: Multiple entry points with overlapping functionality
6. **Test Bloat**: 100+ test files with significant duplication

### Target Outcomes
- **LOC Reduction**: 56K → 20-25K (55% reduction)
- **File Reduction**: 248 → ~80-100 files (60% reduction)
- **Architecture**: Clean hexagonal/ports-and-adapters
- **Pheno-SDK**: Single adapter layer, optional dependency
- **Maintainability**: Clear separation of concerns, DRY principles

---

## Phase 1: Architecture Foundation (Hexagonal)

### 1.1 New Directory Structure

```
atoms-mcp-prod/
├── pyproject.toml              # Single source of truth for deps
├── fastmcp.json                # FastMCP config
├── README.md
├── .env.example
│
├── src/atoms_mcp/              # Core application (hexagon)
│   ├── __init__.py
│   ├── domain/                 # Business logic (pure Python)
│   │   ├── __init__.py
│   │   ├── models/             # Domain models
│   │   │   ├── workspace.py
│   │   │   ├── entity.py
│   │   │   ├── relationship.py
│   │   │   └── workflow.py
│   │   ├── services/           # Business services
│   │   │   ├── workspace_service.py
│   │   │   ├── entity_service.py
│   │   │   ├── relationship_service.py
│   │   │   └── workflow_service.py
│   │   └── ports/              # Interfaces (abstract)
│   │       ├── repository.py   # Data access interface
│   │       ├── cache.py        # Cache interface
│   │       └── embeddings.py   # Vector interface
│   │
│   ├── application/            # Use cases / orchestration
│   │   ├── __init__.py
│   │   ├── commands/           # Write operations
│   │   │   ├── create_entity.py
│   │   │   ├── update_entity.py
│   │   │   └── delete_entity.py
│   │   ├── queries/            # Read operations
│   │   │   ├── get_entity.py
│   │   │   ├── search_entities.py
│   │   │   └── rag_query.py
│   │   └── workflows/          # Complex operations
│   │       ├── project_setup.py
│   │       └── bulk_import.py
│   │
│   ├── adapters/               # External integrations (ports impl)
│   │   ├── __init__.py
│   │   ├── primary/            # Inbound adapters
│   │   │   ├── mcp/            # MCP server adapter
│   │   │   │   ├── server.py
│   │   │   │   ├── tools.py
│   │   │   │   └── auth.py
│   │   │   └── cli/            # CLI adapter
│   │   │       └── commands.py
│   │   │
│   │   └── secondary/          # Outbound adapters
│   │       ├── supabase/       # Database adapter
│   │       │   ├── repository.py
│   │       │   └── client.py
│   │       ├── vertex/         # Embeddings adapter
│   │       │   └── embeddings.py
│   │       ├── pheno/          # Pheno-SDK adapter (OPTIONAL)
│   │       │   ├── __init__.py
│   │       │   ├── config.py
│   │       │   ├── tunnel.py
│   │       │   └── observability.py
│   │       └── cache/          # Cache adapter
│   │           └── memory.py
│   │
│   └── infrastructure/         # Cross-cutting concerns
│       ├── __init__.py
│       ├── config/             # Configuration management
│       │   ├── settings.py     # Pydantic settings (SINGLE)
│       │   └── loader.py
│       ├── logging/            # Logging setup
│       │   └── setup.py
│       └── errors/             # Error handling
│           └── exceptions.py
│
├── tests/                      # Consolidated tests
│   ├── unit/                   # Unit tests (domain/application)
│   ├── integration/            # Integration tests (adapters)
│   └── e2e/                    # End-to-end tests
│
├── scripts/                    # Utility scripts
│   ├── backfill_embeddings.py
│   └── schema_sync.py
│
└── docs/                       # Documentation
    ├── ARCHITECTURE.md
    ├── API_REFERENCE.md
    └── DEPLOYMENT.md
```

---

## Phase 2: Consolidation & Elimination

### 2.1 Configuration Consolidation

**ELIMINATE:**
- ❌ `config/settings.py` (old YAML loader)
- ❌ `settings/app.py` (duplicate)
- ❌ `settings/secrets.py` (duplicate)
- ❌ `settings/combined.py` (overcomplicated)
- ❌ `settings/config.py` (duplicate)
- ❌ `config.yml` (root level)
- ❌ `config/atoms.config.yaml` (duplicate)
- ❌ `config/atoms.secrets.yaml` (duplicate)

**CONSOLIDATE TO:**
```python
# src/atoms_mcp/infrastructure/config/settings.py
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

    # Database (Supabase)
    supabase_url: SecretStr
    supabase_anon_key: SecretStr
    supabase_service_key: SecretStr | None = None

    # Auth (WorkOS)
    workos_client_id: str | None = None
    workos_api_key: SecretStr | None = None

    # AI (Vertex)
    google_project_id: str | None = None
    google_location: str = "us-central1"

    # Features
    enable_auth: bool = True
    enable_embeddings: bool = True

    # Logging
    log_level: str = "INFO"

    @classmethod
    def load(cls) -> "AtomsSettings":
        """Load settings with environment detection."""
        return cls()
```

**Result:** 8 files → 1 file, ~1500 LOC → ~100 LOC

### 2.2 CLI Consolidation

**ELIMINATE:**
- ❌ `atoms` (913 lines, TUI implementation)
- ❌ `atoms_cli.py` (500+ lines, basic CLI)
- ❌ `atoms_cli_enhanced.py` (400+ lines, pheno-sdk CLI)
- ❌ `atoms_server.py` (100 lines, server wrapper)

**CONSOLIDATE TO:**
```python
# src/atoms_mcp/adapters/primary/cli/commands.py
import typer
from rich.console import Console

app = typer.Typer(name="atoms", help="Atoms MCP Server CLI")
console = Console()

@app.command()
def serve(
    host: str = "0.0.0.0",
    port: int = 8000,
    transport: str = "stdio"
):
    """Start the MCP server."""
    from atoms_mcp.adapters.primary.mcp.server import create_server
    server = create_server()
    server.run(transport=transport, host=host, port=port)

@app.command()
def deploy(env: str = "dev"):
    """Deploy to Vercel."""
    # Minimal deployment logic
    pass

if __name__ == "__main__":
    app()
```

**Entry Point (pyproject.toml):**
```toml
[project.scripts]
atoms = "atoms_mcp.adapters.primary.cli.commands:app"
```

**Result:** 4 files (~2000 LOC) → 1 file (~150 LOC)

### 2.3 Server Consolidation

**ELIMINATE:**
- ❌ `server/__init__.py` (300+ lines, complex initialization)
- ❌ `server/__main__.py` (duplicate entry point)
- ❌ `server/app.py` (Vercel-specific, move to adapter)
- ❌ `server/env.py` (duplicate config loading)
- ❌ `server/errors.py` (move to infrastructure)
- ❌ `server/serializers.py` (move to domain)
- ❌ `server/supabase_client.py` (move to adapter)
- ❌ `server/entry_points/` (unnecessary)

**CONSOLIDATE TO:**
```python
# src/atoms_mcp/adapters/primary/mcp/server.py
from fastmcp import FastMCP
from atoms_mcp.infrastructure.config.settings import AtomsSettings
from atoms_mcp.adapters.primary.mcp.tools import register_tools
from atoms_mcp.adapters.primary.mcp.auth import create_auth_provider

def create_server(settings: AtomsSettings | None = None) -> FastMCP:
    """Create FastMCP server instance."""
    settings = settings or AtomsSettings.load()

    mcp = FastMCP(
        name="atoms-mcp",
        auth=create_auth_provider(settings) if settings.enable_auth else None
    )

    register_tools(mcp, settings)
    return mcp
```

**Result:** 8 files (~1500 LOC) → 3 files (~300 LOC)

### 2.4 Tools Consolidation

**CURRENT STATE:**
```
tools/
├── __init__.py
├── base.py
├── query.py
├── entity/
│   ├── entity.py
│   ├── entity_resolver.py
│   ├── relationship.py
│   └── schema.py
└── workflow/
    ├── workflow.py
    └── workspace.py
```

**ELIMINATE & REORGANIZE:**
- ❌ `tools/base.py` (move to domain/models)
- ❌ `tools/entity/entity_resolver.py` (merge into service)
- ❌ `tools/entity/schema.py` (move to domain)

**CONSOLIDATE TO:**
```python
# src/atoms_mcp/adapters/primary/mcp/tools.py
"""MCP tool registration - thin adapter layer."""

from fastmcp import FastMCP
from atoms_mcp.application.commands import CreateEntityCommand, UpdateEntityCommand
from atoms_mcp.application.queries import GetEntityQuery, SearchEntitiesQuery
from atoms_mcp.infrastructure.config.settings import AtomsSettings

def register_tools(mcp: FastMCP, settings: AtomsSettings):
    """Register all MCP tools."""

    @mcp.tool()
    def entity_operation(operation: str, entity_type: str, data: dict):
        """Unified entity CRUD operations."""
        if operation == "create":
            return CreateEntityCommand().execute(entity_type, data)
        elif operation == "get":
            return GetEntityQuery().execute(entity_type, data["id"])
        # ... etc

    @mcp.tool()
    def workspace_operation(operation: str, data: dict):
        """Workspace management operations."""
        # Delegate to application layer
        pass

    @mcp.tool()
    def relationship_operation(operation: str, data: dict):
        """Relationship management operations."""
        # Delegate to application layer
        pass

    @mcp.tool()
    def workflow_execute(workflow_name: str, params: dict):
        """Execute complex workflows."""
        # Delegate to application layer
        pass

    @mcp.tool()
    def data_query(query_type: str, params: dict):
        """Data query and RAG operations."""
        # Delegate to application layer
        pass
```

**Result:** 9 files (~2000 LOC) → 1 file (~200 LOC) + domain/application layers

### 2.5 Pheno-SDK Adapter Pattern

**CURRENT PROBLEM:**
- Direct imports scattered across 50+ files
- Tight coupling to pheno-sdk
- Breaks when pheno-sdk unavailable

**SOLUTION:**
```python
# src/atoms_mcp/adapters/secondary/pheno/__init__.py
"""Optional pheno-sdk integration adapter."""

from typing import Protocol, runtime_checkable

@runtime_checkable
class TunnelProvider(Protocol):
    """Tunnel provider interface."""
    async def start(self, port: int) -> str: ...
    async def stop(self) -> None: ...

@runtime_checkable
class ObservabilityProvider(Protocol):
    """Observability provider interface."""
    def get_logger(self, name: str): ...
    def track_metric(self, name: str, value: float): ...

# Try to import pheno-sdk, fallback to stubs
try:
    from pheno.infra.tunneling import AsyncTunnelManager as _TunnelManager
    from pheno.observability import get_logger as _get_logger
    PHENO_AVAILABLE = True
except ImportError:
    PHENO_AVAILABLE = False
    _TunnelManager = None
    _get_logger = None

def get_tunnel_provider() -> TunnelProvider | None:
    """Get tunnel provider if available."""
    if PHENO_AVAILABLE and _TunnelManager:
        return _TunnelManager()
    return None

def get_logger(name: str):
    """Get logger (pheno-sdk or stdlib)."""
    if PHENO_AVAILABLE and _get_logger:
        return _get_logger(name)
    import logging
    return logging.getLogger(name)
```

**Usage:**
```python
# Anywhere in the codebase
from atoms_mcp.adapters.secondary.pheno import get_logger, get_tunnel_provider

logger = get_logger(__name__)  # Works with or without pheno-sdk
tunnel = get_tunnel_provider()  # Returns None if unavailable
```

**Result:** 50+ scattered imports → 1 adapter module (~150 LOC)

### 2.6 Test Consolidation

**CURRENT STATE:**
- 100+ test files
- Massive duplication in fixtures
- Tests for deleted/archived code

**ELIMINATE:**
- ❌ All tests in `tests/phase*/` (phase-based testing artifacts)
- ❌ `tests/comprehensive_test_*.py` (duplicates)
- ❌ `tests/load/` (move to separate performance suite)
- ❌ `tests/manual/` (not automated)
- ❌ Duplicate fixtures across multiple files

**CONSOLIDATE TO:**
```
tests/
├── conftest.py                 # Shared fixtures
├── unit/
│   ├── domain/                 # Domain model tests
│   ├── application/            # Use case tests
│   └── infrastructure/         # Config/logging tests
├── integration/
│   ├── adapters/               # Adapter tests
│   │   ├── test_supabase.py
│   │   ├── test_mcp_server.py
│   │   └── test_pheno_adapter.py
│   └── test_end_to_end.py
└── performance/
    └── test_load.py
```

**Result:** 100+ files (~15K LOC) → ~20 files (~3K LOC)

---

## Phase 3: Hexagonal Architecture Implementation

### 3.1 Domain Layer (Pure Business Logic)

**Principles:**
- No external dependencies
- Pure Python
- Framework-agnostic
- Testable in isolation

**Example:**
```python
# src/atoms_mcp/domain/models/entity.py
from dataclasses import dataclass
from datetime import datetime
from typing import Any

@dataclass
class Entity:
    """Core entity domain model."""
    id: str
    type: str
    data: dict[str, Any]
    workspace_id: str
    created_at: datetime
    updated_at: datetime

    def update(self, data: dict[str, Any]) -> None:
        """Update entity data."""
        self.data.update(data)
        self.updated_at = datetime.utcnow()

    def validate(self) -> bool:
        """Validate entity data."""
        # Business rules here
        return True

# src/atoms_mcp/domain/services/entity_service.py
from atoms_mcp.domain.models.entity import Entity
from atoms_mcp.domain.ports.repository import EntityRepository

class EntityService:
    """Entity business logic."""

    def __init__(self, repository: EntityRepository):
        self._repository = repository

    async def create_entity(self, entity_type: str, data: dict) -> Entity:
        """Create new entity with business rules."""
        entity = Entity(
            id=self._generate_id(),
            type=entity_type,
            data=data,
            workspace_id=self._get_current_workspace(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        if not entity.validate():
            raise ValueError("Invalid entity data")

        await self._repository.save(entity)
        return entity
```

### 3.2 Application Layer (Use Cases)

**Principles:**
- Orchestrates domain services
- Implements use cases
- Transaction boundaries
- No infrastructure details

**Example:**
```python
# src/atoms_mcp/application/commands/create_entity.py
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

    async def execute(self, entity_type: str, data: dict) -> dict:
        """Execute create entity command."""
        # 1. Create entity (domain logic)
        entity = await self.entity_service.create_entity(entity_type, data)

        # 2. Generate embeddings if enabled
        if self.embeddings and data.get("content"):
            embedding = await self.embeddings.generate(data["content"])
            await self.embeddings.store(entity.id, embedding)

        # 3. Invalidate cache
        await self.cache.invalidate(f"entity:{entity_type}")

        # 4. Return result
        return {
            "id": entity.id,
            "type": entity.type,
            "data": entity.data,
            "created_at": entity.created_at.isoformat()
        }
```

### 3.3 Adapter Layer (External Integration)

**Primary Adapters (Inbound):**
```python
# src/atoms_mcp/adapters/primary/mcp/server.py
"""MCP server adapter - converts MCP calls to application commands."""

from fastmcp import FastMCP
from atoms_mcp.application.commands.create_entity import CreateEntityCommand
from atoms_mcp.infrastructure.di import get_container

def create_server() -> FastMCP:
    """Create MCP server with dependency injection."""
    container = get_container()
    mcp = FastMCP(name="atoms-mcp")

    @mcp.tool()
    async def entity_operation(operation: str, entity_type: str, data: dict):
        """MCP tool adapter."""
        if operation == "create":
            command = container.resolve(CreateEntityCommand)
            return await command.execute(entity_type, data)
        # ... other operations

    return mcp
```

**Secondary Adapters (Outbound):**
```python
# src/atoms_mcp/adapters/secondary/supabase/repository.py
"""Supabase repository adapter - implements domain port."""

from atoms_mcp.domain.models.entity import Entity
from atoms_mcp.domain.ports.repository import EntityRepository
from supabase import Client

class SupabaseEntityRepository(EntityRepository):
    """Supabase implementation of entity repository."""

    def __init__(self, client: Client):
        self._client = client

    async def save(self, entity: Entity) -> None:
        """Save entity to Supabase."""
        await self._client.table("entities").insert({
            "id": entity.id,
            "type": entity.type,
            "data": entity.data,
            "workspace_id": entity.workspace_id,
            "created_at": entity.created_at.isoformat(),
            "updated_at": entity.updated_at.isoformat()
        }).execute()

    async def get(self, entity_id: str) -> Entity | None:
        """Get entity from Supabase."""
        result = await self._client.table("entities")\
            .select("*")\
            .eq("id", entity_id)\
            .single()\
            .execute()

        if not result.data:
            return None

        return Entity(**result.data)
```

### 3.4 Dependency Injection

**Simple DI Container:**
```python
# src/atoms_mcp/infrastructure/di.py
"""Dependency injection container."""

from typing import TypeVar, Type
from atoms_mcp.infrastructure.config.settings import AtomsSettings

T = TypeVar('T')

class Container:
    """Simple DI container."""

    def __init__(self, settings: AtomsSettings):
        self._settings = settings
        self._singletons = {}

    def resolve(self, cls: Type[T]) -> T:
        """Resolve dependency."""
        if cls in self._singletons:
            return self._singletons[cls]

        # Auto-wire dependencies
        instance = self._create_instance(cls)
        self._singletons[cls] = instance
        return instance

    def _create_instance(self, cls: Type[T]) -> T:
        """Create instance with dependencies."""
        # Simple constructor injection
        # In production, use dependency-injector or similar
        pass

_container: Container | None = None

def get_container() -> Container:
    """Get global container."""
    global _container
    if _container is None:
        settings = AtomsSettings.load()
        _container = Container(settings)
    return _container
```

---

## Phase 4: File-by-File Migration Plan

### 4.1 Files to DELETE (Archive)

**Configuration (8 files):**
- `config/settings.py`
- `config/__init__.py`
- `settings/app.py`
- `settings/secrets.py`
- `settings/combined.py`
- `settings/config.py`
- `settings/__init__.py`
- `config.yml`

**CLI (4 files):**
- `atoms` (executable)
- `atoms_cli.py`
- `atoms_cli_enhanced.py`
- `atoms_server.py`

**Server (8 files):**
- `server/__init__.py`
- `server/__main__.py`
- `server/app.py` (move logic to adapter)
- `server/env.py`
- `server/errors.py` (move to infrastructure)
- `server/serializers.py` (move to domain)
- `server/supabase_client.py` (move to adapter)
- `server/entry_points/main.py`

**Tools (partial, 4 files):**
- `tools/base.py`
- `tools/entity/entity_resolver.py`
- `tools/entity/schema.py`
- `tools/__init__.py`

**Lib (entire directory, ~10 files):**
- `lib/atoms/` (move to src/atoms_mcp)
- `lib/deployment_checker.py` (move to scripts)
- `lib/schema_sync.py` (move to scripts)
- `lib/server_manager.py` (delete, use pheno-sdk adapter)

**Utils (3 files):**
- `utils/mcp_adapter.py` (obsolete with new architecture)
- `utils/setup/sitecustomize.py` (obsolete)
- `utils/__init__.py`

**Infrastructure (2 files):**
- `infrastructure/factory.py` (replace with DI)
- `infrastructure/supabase_auth.py` (move to adapter)

**Tests (80+ files):**
- All `tests/phase*/` directories
- `tests/comprehensive_test_*.py`
- `tests/load/` (move to performance/)
- `tests/manual/`
- Duplicate test files

**Total to DELETE: ~120 files**

### 4.2 Files to MIGRATE

**Domain Models:**
```
tools/entity/entity.py → src/atoms_mcp/domain/models/entity.py
tools/entity/relationship.py → src/atoms_mcp/domain/models/relationship.py
tools/workflow/workspace.py → src/atoms_mcp/domain/models/workspace.py
tools/workflow/workflow.py → src/atoms_mcp/domain/models/workflow.py
```

**Application Layer:**
```
tools/query.py → src/atoms_mcp/application/queries/
server/tools.py → src/atoms_mcp/adapters/primary/mcp/tools.py
```

**Adapters:**
```
server/core.py → src/atoms_mcp/adapters/primary/mcp/server.py
server/auth.py → src/atoms_mcp/adapters/primary/mcp/auth.py
server/supabase_client.py → src/atoms_mcp/adapters/secondary/supabase/client.py
```

**Infrastructure:**
```
utils/logging_setup.py → src/atoms_mcp/infrastructure/logging/setup.py
server/errors.py → src/atoms_mcp/infrastructure/errors/exceptions.py
```

**Scripts (keep as-is):**
```
scripts/backfill_embeddings.py
scripts/schema_sync.py
scripts/check_embedding_status.py
```

### 4.3 Files to CREATE

**Domain Layer (10 files):**
- `src/atoms_mcp/domain/models/entity.py`
- `src/atoms_mcp/domain/models/relationship.py`
- `src/atoms_mcp/domain/models/workspace.py`
- `src/atoms_mcp/domain/models/workflow.py`
- `src/atoms_mcp/domain/services/entity_service.py`
- `src/atoms_mcp/domain/services/relationship_service.py`
- `src/atoms_mcp/domain/services/workspace_service.py`
- `src/atoms_mcp/domain/ports/repository.py`
- `src/atoms_mcp/domain/ports/cache.py`
- `src/atoms_mcp/domain/ports/embeddings.py`

**Application Layer (8 files):**
- `src/atoms_mcp/application/commands/create_entity.py`
- `src/atoms_mcp/application/commands/update_entity.py`
- `src/atoms_mcp/application/commands/delete_entity.py`
- `src/atoms_mcp/application/queries/get_entity.py`
- `src/atoms_mcp/application/queries/search_entities.py`
- `src/atoms_mcp/application/queries/rag_query.py`
- `src/atoms_mcp/application/workflows/project_setup.py`
- `src/atoms_mcp/application/workflows/bulk_import.py`

**Adapters (12 files):**
- `src/atoms_mcp/adapters/primary/mcp/server.py`
- `src/atoms_mcp/adapters/primary/mcp/tools.py`
- `src/atoms_mcp/adapters/primary/mcp/auth.py`
- `src/atoms_mcp/adapters/primary/cli/commands.py`
- `src/atoms_mcp/adapters/secondary/supabase/repository.py`
- `src/atoms_mcp/adapters/secondary/supabase/client.py`
- `src/atoms_mcp/adapters/secondary/vertex/embeddings.py`
- `src/atoms_mcp/adapters/secondary/pheno/__init__.py`
- `src/atoms_mcp/adapters/secondary/pheno/config.py`
- `src/atoms_mcp/adapters/secondary/pheno/tunnel.py`
- `src/atoms_mcp/adapters/secondary/pheno/observability.py`
- `src/atoms_mcp/adapters/secondary/cache/memory.py`

**Infrastructure (5 files):**
- `src/atoms_mcp/infrastructure/config/settings.py`
- `src/atoms_mcp/infrastructure/config/loader.py`
- `src/atoms_mcp/infrastructure/logging/setup.py`
- `src/atoms_mcp/infrastructure/errors/exceptions.py`
- `src/atoms_mcp/infrastructure/di.py`

**Tests (15 files):**
- `tests/conftest.py`
- `tests/unit/domain/test_entity.py`
- `tests/unit/domain/test_relationship.py`
- `tests/unit/application/test_create_entity.py`
- `tests/unit/application/test_queries.py`
- `tests/integration/adapters/test_supabase.py`
- `tests/integration/adapters/test_mcp_server.py`
- `tests/integration/adapters/test_pheno_adapter.py`
- `tests/integration/test_end_to_end.py`
- `tests/performance/test_load.py`
- (5 more test files)

**Total to CREATE: ~50 files**

---

## Phase 5: Dependency Optimization

### 5.1 Current Dependencies (pyproject.toml)

**Core (Required):**
- ✅ `fastmcp>=2.13.0.1` - MCP server framework
- ✅ `pydantic>=2.11.7` - Data validation
- ✅ `pydantic-settings>=2.3.0` - Configuration
- ✅ `supabase>=2.5.0` - Database client
- ✅ `httpx>=0.28.1` - HTTP client
- ✅ `PyYAML>=6.0` - YAML parsing (for .env only)

**Required (Feature-gated):**
- ✅ `google-cloud-aiplatform>=1.49.0` - Vertex AI (REQUIRED for embeddings)
- ✅ `workos>=1.0.0` - Auth (REQUIRED for authentication)

**Optional (Infrastructure):**
- 🔧 `pheno_sdk` - Infrastructure helpers (optional, graceful fallback)
- 🔧 `sst` - SST Python SDK for infrastructure-as-code (if available)

**Remove (Unused/Duplicate):**
- ❌ `py-key-value-aio` - Not used
- ❌ `fastapi` - FastMCP handles HTTP
- ❌ `uvicorn` - FastMCP handles server
- ❌ `psycopg2-binary` - Supabase client handles DB
- ❌ `aiohttp` - Use httpx
- ❌ `PyJWT` - WorkOS handles JWT
- ❌ `cryptography` - WorkOS handles crypto
- ❌ `tqdm` - Not needed
- ❌ `rapidfuzz` - Not used
- ❌ `psutil` - Not needed
- ❌ `typing-extensions` - Python 3.11+ has built-in
- ❌ `playwright` - Not used
- ❌ `sqlalchemy` - Supabase client handles ORM

**Dev Dependencies (Modern Tooling):**
- ✅ `pytest` + plugins (testing)
- ✅ `ruff` (replaces black, isort, flake8, pylint)
- ✅ `pyright` (type checker - faster than mypy)
- ✅ `zuban` (wraps pyright with better UX)
- ❌ Remove: mypy, black, isort, pylint, prospector, bandit, etc.

### 5.2 Optimized pyproject.toml

```toml
[project]
name = "atoms-mcp"
version = "0.1.0"
description = "Atoms MCP Server - Model Context Protocol for workspace management"
requires-python = ">=3.11"
readme = "README.md"
license = {text = "MIT"}

dependencies = [
    # Core MCP & Web Framework
    "fastmcp>=2.13.0.1",

    # Data Validation & Settings
    "pydantic>=2.11.7,<3.0.0",
    "pydantic-settings>=2.3.0",

    # Database & HTTP
    "supabase>=2.5.0",
    "httpx>=0.28.1,<1.0.0",

    # CLI & Display
    "typer>=0.9.0",
    "rich>=13.0.0",

    # Required Services (NOT optional)
    "google-cloud-aiplatform>=1.49.0",  # Vertex AI embeddings
    "workos>=1.0.0",                     # Authentication

    # Config (minimal)
    "PyYAML>=6.0",  # Only for .env parsing if needed
]

[project.optional-dependencies]
# Infrastructure helpers (optional - graceful fallback)
infra = [
    "pheno_sdk @ git+file:///path/to/pheno-sdk",
]

# SST Infrastructure-as-Code (if available)
sst = [
    # "sst>=0.0.1",  # Future: SST Python SDK when available
]

# Development
dev = [
    # Testing
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "pytest-xdist>=3.3.0",
    "pytest-mock>=3.11.0",

    # Linting & Formatting (Ruff replaces: black, isort, flake8, pylint)
    "ruff>=0.8.0",

    # Type Checking (Pyright via Zuban - faster than mypy)
    "pyright>=1.1.0",
    "zuban>=0.1.0",  # Wraps pyright with better UX
]

# All optional features
all = [
    "atoms-mcp[infra,sst]",
]

[project.scripts]
atoms = "atoms_mcp.adapters.primary.cli.commands:app"

[build-system]
requires = ["hatchling>=1.21.0"]
build-backend = "hatchling.build"

[tool.ruff]
line-length = 120
target-version = "py311"
select = ["E", "W", "F", "I", "UP", "B", "SIM", "RUF"]
ignore = ["E501"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
addopts = "-ra -q --strict-markers"

[tool.pyright]
# Pyright configuration (via zuban)
pythonVersion = "3.11"
typeCheckingMode = "standard"
reportMissingImports = true
reportMissingTypeStubs = false
exclude = ["**/node_modules", "**/__pycache__", ".venv"]

[tool.zuban]
# Zuban wraps pyright with better UX
type-checker = "pyright"
strict = false

[tool.coverage.run]
source = ["src"]
omit = ["*/tests/*"]
branch = true

[tool.hatch.build.targets.wheel]
packages = ["src/atoms_mcp"]
```

**Result:** 30+ dependencies → 10 core (including Vertex AI & WorkOS) + 2 optional groups

### 5.3 SST Integration (Future)

**Vision:** Use SST Python SDK for infrastructure definition

```python
# sst.config.py (Future - when SST Python SDK is available)
from sst import App, Stack
from sst.components import Function, Bucket, Database

app = App("atoms-mcp")

@app.stack
def main(stack: Stack):
    # Database
    db = Database(
        "atoms-db",
        engine="postgres",
        version="15"
    )

    # Storage
    storage = Bucket("atoms-storage")

    # MCP Server Function
    server = Function(
        "atoms-mcp-server",
        handler="src/atoms_mcp/adapters/primary/mcp/server.create_server",
        environment={
            "SUPABASE_URL": db.url,
            "STORAGE_BUCKET": storage.name,
        }
    )

    return {
        "server_url": server.url,
        "db_url": db.url,
    }
```

**Current State:** SST Python SDK not yet available, use Vercel deployment

**Migration Path:**
1. Phase 1-4: Use current Vercel deployment
2. Phase 5: Monitor SST Python SDK development
3. Phase 6: Migrate to SST when SDK is stable

---

## Phase 6: Implementation Roadmap

### Week 1: Foundation
- [ ] Create new directory structure
- [ ] Implement domain models (pure Python)
- [ ] Implement domain services
- [ ] Define ports (interfaces)
- [ ] Write unit tests for domain layer

### Week 2: Application Layer
- [ ] Implement commands (write operations)
- [ ] Implement queries (read operations)
- [ ] Implement workflows
- [ ] Write unit tests for application layer

### Week 3: Adapters
- [ ] Implement Supabase adapter
- [ ] Implement Vertex AI adapter (optional)
- [ ] Implement pheno-sdk adapter (optional)
- [ ] Implement MCP server adapter
- [ ] Write integration tests

### Week 4: Migration & Cleanup
- [ ] Migrate existing code to new structure
- [ ] Update tests
- [ ] Delete old files
- [ ] Update documentation
- [ ] Final testing

### Week 5: Polish & Deploy
- [ ] Performance testing
- [ ] Security audit
- [ ] Documentation review
- [ ] Deploy to staging
- [ ] Production deployment

---

## Phase 7: Metrics & Success Criteria

### Code Metrics

**Before:**
- Files: 248 Python files
- LOC: 55,946 (code) + 14,616 (comments) = 70,562 total
- Complexity: High (scattered, duplicated)
- Test Coverage: ~60%
- Dependencies: 30+ required

**After (Target):**
- Files: ~80-100 Python files (60% reduction)
- LOC: 20,000-25,000 (code) + 5,000 (comments) = 25,000-30,000 total (58% reduction)
- Complexity: Low (hexagonal, DRY)
- Test Coverage: >80%
- Dependencies: 7 core + 3 optional groups

### Architecture Metrics

**Before:**
- Layers: Unclear separation
- Coupling: High (tight coupling to pheno-sdk, FastMCP internals)
- Testability: Medium (mocking required)
- Maintainability: Low (duplication, scattered code)

**After:**
- Layers: Clear hexagonal architecture
- Coupling: Low (dependency inversion, ports/adapters)
- Testability: High (pure domain, mockable ports)
- Maintainability: High (DRY, SOLID principles)

### Performance Metrics

**Before:**
- Startup time: ~2-3s
- Memory usage: ~150MB
- Import time: ~1s

**After (Target):**
- Startup time: <1s (lazy loading)
- Memory usage: <100MB (fewer dependencies)
- Import time: <500ms (cleaner imports)

---

## Phase 8: Codebase Atlas

### Current State (BEFORE)

```
atoms-mcp-prod/
├── 📁 config/                  [DELETE] - 2 files, ~500 LOC
├── 📁 settings/                [DELETE] - 5 files, ~800 LOC
├── 📁 server/                  [MIGRATE] - 8 files, ~1500 LOC
├── 📁 tools/                   [MIGRATE] - 9 files, ~2000 LOC
├── 📁 lib/                     [DELETE/MIGRATE] - 10 files, ~1500 LOC
├── 📁 utils/                   [DELETE] - 3 files, ~200 LOC
├── 📁 infrastructure/          [MIGRATE] - 2 files, ~300 LOC
├── 📁 src/atoms_mcp/           [EXPAND] - 4 files, ~500 LOC
├── 📁 tests/                   [CONSOLIDATE] - 100+ files, ~15K LOC
├── 📁 scripts/                 [KEEP] - 7 files, ~1000 LOC
├── 📁 schemas/                 [KEEP] - 10 files, ~2000 LOC
├── 📁 docs/                    [UPDATE] - 32 files, ~13K LOC
├── 📄 atoms                    [DELETE] - 913 LOC
├── 📄 atoms_cli.py             [DELETE] - 500 LOC
├── 📄 atoms_cli_enhanced.py    [DELETE] - 400 LOC
├── 📄 atoms_server.py          [DELETE] - 100 LOC
├── 📄 pyproject.toml           [SIMPLIFY]
├── 📄 fastmcp.json             [UPDATE]
└── 📄 README.md                [UPDATE]

Total: 248 files, ~56K LOC (code)
```

### Target State (AFTER)

```
atoms-mcp-prod/
├── 📁 src/atoms_mcp/           # Core application (hexagon)
│   ├── 📁 domain/              # Business logic (pure Python)
│   │   ├── 📁 models/          # 4 files, ~400 LOC
│   │   ├── 📁 services/        # 3 files, ~600 LOC
│   │   └── 📁 ports/           # 3 files, ~200 LOC
│   │
│   ├── 📁 application/         # Use cases / orchestration
│   │   ├── 📁 commands/        # 3 files, ~400 LOC
│   │   ├── 📁 queries/         # 3 files, ~400 LOC
│   │   └── 📁 workflows/       # 2 files, ~300 LOC
│   │
│   ├── 📁 adapters/            # External integrations
│   │   ├── 📁 primary/         # Inbound
│   │   │   ├── 📁 mcp/         # 3 files, ~500 LOC
│   │   │   └── 📁 cli/         # 1 file, ~150 LOC
│   │   │
│   │   └── 📁 secondary/       # Outbound
│   │       ├── 📁 supabase/    # 2 files, ~400 LOC
│   │       ├── 📁 vertex/      # 1 file, ~200 LOC
│   │       ├── 📁 pheno/       # 4 files, ~300 LOC (optional)
│   │       └── 📁 cache/       # 1 file, ~100 LOC
│   │
│   └── 📁 infrastructure/      # Cross-cutting
│       ├── 📁 config/          # 2 files, ~200 LOC
│       ├── 📁 logging/         # 1 file, ~100 LOC
│       ├── 📁 errors/          # 1 file, ~100 LOC
│       └── 📄 di.py            # 1 file, ~150 LOC
│
├── 📁 tests/                   # Consolidated tests
│   ├── 📄 conftest.py          # Shared fixtures
│   ├── 📁 unit/                # 8 files, ~1500 LOC
│   ├── 📁 integration/         # 5 files, ~1000 LOC
│   └── 📁 performance/         # 2 files, ~500 LOC
│
├── 📁 scripts/                 # Utility scripts (keep)
│   ├── 📄 backfill_embeddings.py
│   ├── 📄 schema_sync.py
│   └── 📄 check_embedding_status.py
│
├── 📁 schemas/                 # Database schemas (keep)
│   ├── 📁 generated/
│   └── 📁 sync/
│
├── 📁 docs/                    # Documentation (updated)
│   ├── 📄 ARCHITECTURE.md      # Hexagonal architecture guide
│   ├── 📄 API_REFERENCE.md     # API documentation
│   ├── 📄 DEPLOYMENT.md        # Deployment guide
│   └── 📄 DEVELOPER_GUIDE.md   # Development guide
│
├── 📄 pyproject.toml           # Simplified dependencies
├── 📄 fastmcp.json             # FastMCP config
├── 📄 .env.example             # Environment template
├── 📄 README.md                # Updated README
└── 📄 Makefile                 # Build commands

Total: ~80-100 files, ~20-25K LOC (code)
```

### File Tree Comparison

| Category | Before | After | Change |
|----------|--------|-------|--------|
| **Domain** | 0 files | 10 files (~1200 LOC) | +10 files |
| **Application** | 0 files | 8 files (~1100 LOC) | +8 files |
| **Adapters** | 20 files (~3000 LOC) | 12 files (~1650 LOC) | -8 files, -45% LOC |
| **Infrastructure** | 15 files (~2500 LOC) | 5 files (~550 LOC) | -10 files, -78% LOC |
| **Configuration** | 13 files (~1800 LOC) | 2 files (~200 LOC) | -11 files, -89% LOC |
| **CLI** | 4 files (~1900 LOC) | 1 file (~150 LOC) | -3 files, -92% LOC |
| **Tests** | 100+ files (~15K LOC) | 15 files (~3K LOC) | -85 files, -80% LOC |
| **Scripts** | 7 files (~1K LOC) | 7 files (~1K LOC) | No change |
| **Schemas** | 10 files (~2K LOC) | 10 files (~2K LOC) | No change |
| **Docs** | 32 files (~13K LOC) | 10 files (~5K LOC) | -22 files, -62% LOC |
| **Root Files** | 4 files (~1900 LOC) | 0 files | -4 files |
| **TOTAL** | **248 files, 56K LOC** | **80 files, 22K LOC** | **-68% files, -61% LOC** |

---

## Phase 9: Migration Checklist

### Pre-Migration
- [ ] Backup current codebase
- [ ] Create feature branch: `refactor/hexagonal-architecture`
- [ ] Set up new directory structure
- [ ] Document current behavior (integration tests)

### Domain Layer
- [ ] Create domain models (Entity, Relationship, Workspace, Workflow)
- [ ] Create domain services (business logic)
- [ ] Define ports (repository, cache, embeddings interfaces)
- [ ] Write unit tests (100% coverage for domain)

### Application Layer
- [ ] Implement commands (CreateEntity, UpdateEntity, DeleteEntity)
- [ ] Implement queries (GetEntity, SearchEntities, RAGQuery)
- [ ] Implement workflows (ProjectSetup, BulkImport)
- [ ] Write unit tests (>90% coverage)

### Adapters
- [ ] Implement MCP server adapter
- [ ] Implement MCP tools adapter
- [ ] Implement CLI adapter
- [ ] Implement Supabase repository adapter
- [ ] Implement Vertex AI embeddings adapter (optional)
- [ ] Implement pheno-sdk adapter (optional)
- [ ] Implement cache adapter
- [ ] Write integration tests

### Infrastructure
- [ ] Consolidate configuration (single settings.py)
- [ ] Set up logging
- [ ] Define custom exceptions
- [ ] Implement DI container
- [ ] Write infrastructure tests

### Testing
- [ ] Migrate existing tests to new structure
- [ ] Remove duplicate tests
- [ ] Achieve >80% coverage
- [ ] Set up performance benchmarks

### Documentation
- [ ] Update README.md
- [ ] Write ARCHITECTURE.md (hexagonal guide)
- [ ] Update API_REFERENCE.md
- [ ] Update DEPLOYMENT.md
- [ ] Write migration guide

### Cleanup
- [ ] Delete old files (120+ files)
- [ ] Remove unused dependencies
- [ ] Update pyproject.toml
- [ ] Update fastmcp.json
- [ ] Clean up .gitignore

### Validation
- [ ] All tests pass
- [ ] Coverage >80%
- [ ] No regressions (integration tests)
- [ ] Performance benchmarks meet targets
- [ ] Security audit passes
- [ ] Documentation complete

### Deployment
- [ ] Deploy to staging
- [ ] Smoke tests on staging
- [ ] Performance tests on staging
- [ ] Deploy to production
- [ ] Monitor for issues

---

## Phase 10: Risk Mitigation

### Risks & Mitigation Strategies

**Risk 1: Breaking Changes**
- **Mitigation:** Comprehensive integration tests before refactor
- **Mitigation:** Feature flags for gradual rollout
- **Mitigation:** Parallel run old/new code during transition

**Risk 2: Pheno-SDK Dependency**
- **Mitigation:** Adapter pattern with fallbacks
- **Mitigation:** Make pheno-sdk optional dependency
- **Mitigation:** Document standalone operation

**Risk 3: Performance Regression**
- **Mitigation:** Benchmark current performance
- **Mitigation:** Performance tests in CI/CD
- **Mitigation:** Lazy loading for optional features

**Risk 4: Team Disruption**
- **Mitigation:** Incremental migration (feature branch)
- **Mitigation:** Clear documentation
- **Mitigation:** Pair programming sessions

**Risk 5: Lost Functionality**
- **Mitigation:** Feature parity checklist
- **Mitigation:** Integration test coverage
- **Mitigation:** User acceptance testing

---

## Appendix A: Key Principles

### Hexagonal Architecture (Ports & Adapters)

**Core Principles:**
1. **Domain Independence:** Business logic has no external dependencies
2. **Dependency Inversion:** Dependencies point inward (toward domain)
3. **Testability:** Pure domain logic, mockable adapters
4. **Flexibility:** Easy to swap implementations (Supabase → PostgreSQL)
5. **Clarity:** Clear separation of concerns

**Layers:**
```
┌─────────────────────────────────────────┐
│         Primary Adapters (In)           │
│  ┌─────────────┐    ┌─────────────┐    │
│  │  MCP Server │    │     CLI     │    │
│  └──────┬──────┘    └──────┬──────┘    │
│         │                  │            │
├─────────┼──────────────────┼────────────┤
│         ▼                  ▼            │
│    ┌──────────────────────────┐        │
│    │   Application Layer      │        │
│    │  (Commands, Queries)     │        │
│    └──────────┬───────────────┘        │
│               ▼                         │
│    ┌──────────────────────────┐        │
│    │     Domain Layer         │        │
│    │  (Models, Services)      │        │
│    └──────────┬───────────────┘        │
│               ▼                         │
│    ┌──────────────────────────┐        │
│    │    Ports (Interfaces)    │        │
│    └──────────┬───────────────┘        │
├───────────────┼─────────────────────────┤
│               ▼                         │
│  ┌─────────────────────────────────┐   │
│  │   Secondary Adapters (Out)      │   │
│  │  ┌──────┐  ┌──────┐  ┌──────┐  │   │
│  │  │ DB   │  │Cache │  │ AI   │  │   │
│  │  └──────┘  └──────┘  └──────┘  │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

### DRY (Don't Repeat Yourself)

**Violations Found:**
- 3 CLI implementations
- 4 configuration systems
- Duplicate test fixtures
- Scattered pheno-sdk imports

**Solutions:**
- Single CLI with typer
- Single configuration class
- Shared test fixtures (conftest.py)
- Pheno-SDK adapter pattern

### SOLID Principles

**S - Single Responsibility:**
- Each class has one reason to change
- Domain models: data + validation
- Services: business logic
- Adapters: external integration

**O - Open/Closed:**
- Open for extension (new adapters)
- Closed for modification (stable domain)

**L - Liskov Substitution:**
- Ports define contracts
- Any implementation can be swapped

**I - Interface Segregation:**
- Small, focused ports
- Clients depend only on what they use

**D - Dependency Inversion:**
- Domain depends on abstractions (ports)
- Adapters depend on domain (implement ports)

---

## Appendix B: Quick Reference

### Command Cheat Sheet

```bash
# Development
atoms serve                    # Start MCP server (stdio)
atoms serve --transport http   # Start HTTP server
atoms deploy dev               # Deploy to dev environment
atoms deploy prod              # Deploy to production

# Testing
pytest tests/unit              # Run unit tests
pytest tests/integration       # Run integration tests
pytest tests/performance       # Run performance tests
pytest --cov                   # Run with coverage

# Code Quality
ruff check .                   # Lint code
ruff format .                  # Format code
mypy src                       # Type check

# Build
python -m build                # Build package
pip install -e .               # Install in editable mode
pip install -e ".[dev]"        # Install with dev dependencies
```

### Import Patterns

```python
# ✅ GOOD: Use adapters
from atoms_mcp.adapters.secondary.pheno import get_logger, get_tunnel_provider

# ❌ BAD: Direct imports
from pheno.infra.tunneling import AsyncTunnelManager

# ✅ GOOD: Dependency injection
class EntityService:
    def __init__(self, repository: EntityRepository):
        self._repository = repository

# ❌ BAD: Direct instantiation
class EntityService:
    def __init__(self):
        self._repository = SupabaseRepository()

# ✅ GOOD: Use ports
from atoms_mcp.domain.ports.repository import EntityRepository

# ❌ BAD: Use concrete implementations
from atoms_mcp.adapters.secondary.supabase.repository import SupabaseRepository
```

### Configuration Patterns

```python
# ✅ GOOD: Single settings class
from atoms_mcp.infrastructure.config.settings import AtomsSettings
settings = AtomsSettings.load()

# ❌ BAD: Multiple config sources
from config.settings import load_config
from settings.combined import get_settings
from server.env import load_env_files

# ✅ GOOD: Environment variables
ATOMS_SUPABASE_URL=https://...
ATOMS_ENABLE_AUTH=true

# ❌ BAD: YAML files
config/atoms.config.yaml
config/atoms.secrets.yaml
```

---

## Summary

This comprehensive refactor plan transforms atoms-mcp-prod from a sprawling, duplicated codebase into a clean, maintainable hexagonal architecture:

**Key Achievements:**
- ✅ **68% reduction in files** (248 → 80)
- ✅ **61% reduction in LOC** (56K → 22K)
- ✅ **Hexagonal architecture** (clear separation of concerns)
- ✅ **Pheno-SDK adapter** (optional, not required)
- ✅ **Single configuration** (one settings class)
- ✅ **Consolidated CLI** (one entry point)
- ✅ **DRY principles** (no duplication)
- ✅ **SOLID principles** (dependency inversion)
- ✅ **Testability** (>80% coverage target)
- ✅ **Maintainability** (clear structure)

**Timeline:** 5 weeks
**Effort:** ~120 hours
**Risk:** Medium (mitigated with comprehensive testing)
**Impact:** High (long-term maintainability, scalability)


