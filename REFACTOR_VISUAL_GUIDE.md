# Atoms-MCP-Prod: Visual Refactor Guide

## Current vs Target Architecture

### BEFORE: Scattered Architecture (248 files, 56K LOC)

```
┌─────────────────────────────────────────────────────────────────┐
│                    CURRENT CHAOS                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │  atoms   │  │atoms_cli │  │atoms_cli │  │  atoms_  │       │
│  │  (913L)  │  │  (500L)  │  │_enhanced │  │ server   │       │
│  │          │  │          │  │  (400L)  │  │  (100L)  │       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
│       │             │               │             │             │
│       └─────────────┴───────────────┴─────────────┘             │
│                          │                                      │
│                          ▼                                      │
│       ┌──────────────────────────────────────────┐             │
│       │         server/ (8 files, 1500 LOC)      │             │
│       │  ┌────────┐ ┌────────┐ ┌────────┐       │             │
│       │  │ core   │ │  auth  │ │ tools  │       │             │
│       │  └────────┘ └────────┘ └────────┘       │             │
│       └──────────────────┬───────────────────────┘             │
│                          │                                      │
│       ┌──────────────────┴───────────────────────┐             │
│       │                                           │             │
│       ▼                                           ▼             │
│  ┌─────────────────┐                    ┌─────────────────┐   │
│  │ config/ (8 files)│                    │settings/ (5 files)│  │
│  │  - settings.py   │                    │  - app.py        │  │
│  │  - atoms.config  │                    │  - secrets.py    │  │
│  │  - atoms.secrets │                    │  - combined.py   │  │
│  └─────────────────┘                    └─────────────────┘   │
│                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐   │
│  │ tools/ (9 files)│  │ lib/ (10 files) │  │utils/ (3)   │   │
│  │  - entity/      │  │  - atoms/       │  │  - logging  │   │
│  │  - workflow/    │  │  - deployment   │  │  - mcp_adap │   │
│  │  - query.py     │  │  - schema_sync  │  └─────────────┘   │
│  └─────────────────┘  └─────────────────┘                      │
│                                                                  │
│  ┌──────────────────────────────────────────────────────┐      │
│  │  tests/ (100+ files, 15K LOC)                        │      │
│  │  - phase1/, phase2/, ..., phase9/                    │      │
│  │  - comprehensive_test_*.py (duplicates)              │      │
│  │  - unit/, integration/, load/, manual/               │      │
│  └──────────────────────────────────────────────────────┘      │
│                                                                  │
│  Pheno-SDK imports scattered across 50+ files ❌                │
│  Direct coupling to FastMCP internals ❌                        │
│  No clear architecture ❌                                       │
│  Massive duplication ❌                                         │
└─────────────────────────────────────────────────────────────────┘
```

### AFTER: Hexagonal Architecture (80 files, 22K LOC)

```
┌─────────────────────────────────────────────────────────────────┐
│              HEXAGONAL ARCHITECTURE (Clean)                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────┐      │
│  │         PRIMARY ADAPTERS (Inbound)                   │      │
│  │  ┌─────────────────┐      ┌─────────────────┐       │      │
│  │  │   MCP Server    │      │      CLI        │       │      │
│  │  │   (3 files)     │      │   (1 file)      │       │      │
│  │  │  - server.py    │      │  - commands.py  │       │      │
│  │  │  - tools.py     │      └─────────────────┘       │      │
│  │  │  - auth.py      │                                 │      │
│  │  └────────┬────────┘                                 │      │
│  └───────────┼──────────────────────────────────────────┘      │
│              │                                                  │
│              ▼                                                  │
│  ┌──────────────────────────────────────────────────────┐      │
│  │         APPLICATION LAYER (Use Cases)                │      │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────┐    │      │
│  │  │  Commands   │  │   Queries   │  │Workflows │    │      │
│  │  │  (3 files)  │  │  (3 files)  │  │(2 files) │    │      │
│  │  │  - create   │  │  - get      │  │  - setup │    │      │
│  │  │  - update   │  │  - search   │  │  - import│    │      │
│  │  │  - delete   │  │  - rag      │  └──────────┘    │      │
│  │  └─────────────┘  └─────────────┘                   │      │
│  └───────────────────────┬──────────────────────────────┘      │
│                          │                                      │
│                          ▼                                      │
│  ┌──────────────────────────────────────────────────────┐      │
│  │         DOMAIN LAYER (Business Logic)                │      │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────┐    │      │
│  │  │   Models    │  │  Services   │  │  Ports   │    │      │
│  │  │  (4 files)  │  │  (3 files)  │  │(3 files) │    │      │
│  │  │  - entity   │  │  - entity   │  │  - repo  │    │      │
│  │  │  - relation │  │  - relation │  │  - cache │    │      │
│  │  │  - workspace│  │  - workspace│  │  - embed │    │      │
│  │  │  - workflow │  │             │  └──────────┘    │      │
│  │  └─────────────┘  └─────────────┘                   │      │
│  │                                                      │      │
│  │  ✅ Pure Python - No external dependencies          │      │
│  │  ✅ Framework-agnostic                              │      │
│  │  ✅ 100% testable in isolation                      │      │
│  └───────────────────────┬──────────────────────────────┘      │
│                          │                                      │
│                          ▼                                      │
│  ┌──────────────────────────────────────────────────────┐      │
│  │      SECONDARY ADAPTERS (Outbound)                   │      │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │      │
│  │  │ Supabase │  │  Vertex  │  │  Cache   │          │      │
│  │  │(2 files) │  │ (1 file) │  │ (1 file) │          │      │
│  │  └──────────┘  └──────────┘  └──────────┘          │      │
│  │                                                      │      │
│  │  ┌──────────────────────────────────────┐           │      │
│  │  │  Pheno-SDK Adapter (OPTIONAL)        │           │      │
│  │  │  (4 files) - Fallback to stdlib      │           │      │
│  │  └──────────────────────────────────────┘           │      │
│  └──────────────────────────────────────────────────────┘      │
│                                                                  │
│  ┌──────────────────────────────────────────────────────┐      │
│  │      INFRASTRUCTURE (Cross-cutting)                  │      │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │      │
│  │  │  Config  │  │ Logging  │  │   DI     │          │      │
│  │  │(2 files) │  │ (1 file) │  │ (1 file) │          │      │
│  │  └──────────┘  └──────────┘  └──────────┘          │      │
│  └──────────────────────────────────────────────────────┘      │
│                                                                  │
│  ✅ Clear separation of concerns                               │
│  ✅ Dependency inversion (ports/adapters)                      │
│  ✅ Testable (mockable ports)                                  │
│  ✅ Flexible (swap implementations)                            │
└─────────────────────────────────────────────────────────────────┘
```

## Pheno-SDK Adapter Pattern

### BEFORE: Direct Imports Everywhere (50+ files)

```
❌ atoms_cli.py:
    from pheno.infra.tunneling import AsyncTunnelManager
    from pheno.infra.port_allocator import PortAllocator

❌ server/__init__.py:
    from pheno.infra.tunneling import TunnelConfig, TunnelInfo

❌ utils/mcp_adapter.py:
    from pheno.testing.mcp_qa.core import create_enhanced_adapter

❌ tests/fixtures/__init__.py:
    from pheno.testing.mcp_qa.core.data_generators import DataGenerator

❌ 50+ other files with direct pheno-sdk imports
```

### AFTER: Single Adapter Layer

```python
# src/atoms_mcp/adapters/secondary/pheno/__init__.py

"""Optional pheno-sdk integration - graceful fallback."""

from typing import Protocol

# Define interfaces (ports)
class TunnelProvider(Protocol):
    async def start(self, port: int) -> str: ...
    async def stop(self) -> None: ...

class LoggerProvider(Protocol):
    def info(self, msg: str) -> None: ...
    def error(self, msg: str) -> None: ...

# Try to import pheno-sdk
try:
    from pheno.infra.tunneling import AsyncTunnelManager
    from pheno.observability import get_logger as pheno_logger
    PHENO_AVAILABLE = True
except ImportError:
    PHENO_AVAILABLE = False

# Provide adapters with fallbacks
def get_tunnel_provider() -> TunnelProvider | None:
    if PHENO_AVAILABLE:
        return AsyncTunnelManager()
    return None  # Graceful degradation

def get_logger(name: str) -> LoggerProvider:
    if PHENO_AVAILABLE:
        return pheno_logger(name)
    import logging
    return logging.getLogger(name)  # Stdlib fallback
```

**Usage everywhere:**
```python
from atoms_mcp.adapters.secondary.pheno import get_logger

logger = get_logger(__name__)  # Works with or without pheno-sdk!
```

**Result:** 50+ scattered imports → 1 adapter module

## Test Consolidation

### BEFORE: 100+ Test Files (15K LOC)

```
tests/
├── phase1/ (10 files)
├── phase2/ (10 files)
├── phase3/ (10 files)
├── phase4/ (10 files)
├── phase5/ (10 files)
├── phase6/ (10 files)
├── phase7/ (10 files)
├── phase8/ (10 files)
├── phase9/ (10 files)
├── comprehensive_test_evolution.py
├── comprehensive_test_matrix.py
├── unit/ (20 files with duplicates)
├── integration/ (10 files)
├── load/ (5 files)
├── manual/ (5 files)
└── ... (many duplicates)

Total: 100+ files, ~15K LOC
```

### AFTER: 15 Focused Test Files (3K LOC)

```
tests/
├── conftest.py                      # Shared fixtures (200 LOC)
│
├── unit/                            # Pure domain/application tests
│   ├── domain/
│   │   ├── test_entity.py          (200 LOC)
│   │   ├── test_relationship.py    (150 LOC)
│   │   └── test_workspace.py       (150 LOC)
│   ├── application/
│   │   ├── test_commands.py        (300 LOC)
│   │   └── test_queries.py         (300 LOC)
│   └── infrastructure/
│       └── test_config.py          (100 LOC)
│
├── integration/                     # Adapter integration tests
│   ├── adapters/
│   │   ├── test_supabase.py        (300 LOC)
│   │   ├── test_mcp_server.py      (400 LOC)
│   │   └── test_pheno_adapter.py   (200 LOC)
│   └── test_end_to_end.py          (500 LOC)
│
└── performance/                     # Performance benchmarks
    └── test_load.py                (200 LOC)

Total: 15 files, ~3K LOC
```

**Result:** 100+ files (15K LOC) → 15 files (3K LOC) = **80% reduction**

## Dependency Flow

### BEFORE: Tangled Dependencies

```
┌─────────────────────────────────────────────────────────┐
│                    DEPENDENCY HELL                       │
└─────────────────────────────────────────────────────────┘

atoms_cli.py ──────────┐
                       ├──> pheno-sdk (direct import)
atoms_cli_enhanced.py ─┤
                       │
server/core.py ────────┤
                       │
server/auth.py ────────┤
                       │
tools/entity.py ───────┤
                       │
lib/atoms/server.py ───┤
                       │
utils/mcp_adapter.py ──┘

❌ 50+ files directly import pheno-sdk
❌ Tight coupling - can't run without pheno-sdk
❌ Circular dependencies
❌ Hard to test
```

### AFTER: Clean Dependencies (Dependency Inversion)

```
┌─────────────────────────────────────────────────────────┐
│              DEPENDENCY INVERSION PRINCIPLE              │
└─────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│  Primary Adapters (MCP, CLI)                         │
│         │                                             │
│         ├──> Application Layer (Commands, Queries)   │
│         │           │                                 │
│         │           ├──> Domain Layer (Models)       │
│         │           │           │                     │
│         │           │           ├──> Ports (Interfaces)
│         │           │           │           ▲         │
│         │           │           │           │         │
│         │           │           │           │         │
│         │           │           └───────────┘         │
│         │           │                       │         │
│         │           └───────────────────────┘         │
│         │                                   │         │
│         └───────────────────────────────────┘         │
│                                             │         │
│                                             ▼         │
│  Secondary Adapters (Supabase, Vertex, Pheno)       │
│         │                                             │
│         └──> Implements Ports                        │
└──────────────────────────────────────────────────────┘

✅ Dependencies point INWARD (toward domain)
✅ Domain has ZERO external dependencies
✅ Adapters depend on domain (not vice versa)
✅ Easy to test (mock ports)
✅ Easy to swap implementations
```

## Configuration Consolidation

### BEFORE: 8 Config Files

```
config/
├── settings.py          (YAML loader, 200 LOC)
├── atoms.config.yaml    (App config, 100 LOC)
└── atoms.secrets.yaml   (Secrets, 50 LOC)

settings/
├── app.py               (App settings, 150 LOC)
├── secrets.py           (Secrets, 100 LOC)
├── combined.py          (Merger, 200 LOC)
├── config.py            (Loader, 100 LOC)
└── __init__.py

config.yml               (Root config, 100 LOC)

Total: 8 files, ~1000 LOC
```

### AFTER: 1 Config File

```python
# src/atoms_mcp/infrastructure/config/settings.py (100 LOC)

from pydantic_settings import BaseSettings

class AtomsSettings(BaseSettings):
    """Single source of truth."""

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Database
    supabase_url: SecretStr
    supabase_anon_key: SecretStr

    # Auth
    workos_api_key: SecretStr | None = None

    # Features
    enable_auth: bool = True
    enable_embeddings: bool = True

    class Config:
        env_prefix = 'ATOMS_'
        env_file = '.env'

# Usage
settings = AtomsSettings()
```

**Result:** 8 files (1000 LOC) → 1 file (100 LOC) = **90% reduction**

## CLI Consolidation

### BEFORE: 4 CLI Implementations

```
atoms (913 LOC)
├── ServerTUI class (200 LOC)
├── Health monitoring (150 LOC)
├── Tunnel management (100 LOC)
├── Process management (100 LOC)
├── Server commands (200 LOC)
└── Status commands (163 LOC)

atoms_cli.py (500 LOC)
├── Basic CLI (200 LOC)
├── Deploy commands (150 LOC)
├── Test commands (100 LOC)
└── Schema commands (50 LOC)

atoms_cli_enhanced.py (400 LOC)
├── Pheno-SDK integration (200 LOC)
├── Advanced deployment (150 LOC)
└── TUI dashboard (50 LOC)

atoms_server.py (100 LOC)
└── Server wrapper

Total: 4 files, ~1900 LOC
```

### AFTER: 1 CLI File

```python
# src/atoms_mcp/adapters/primary/cli/commands.py (150 LOC)

import typer
from rich.console import Console

app = typer.Typer()
console = Console()

@app.command()
def serve(transport: str = "stdio", port: int = 8000):
    """Start MCP server."""
    from atoms_mcp.adapters.primary.mcp.server import create_server
    server = create_server()
    server.run(transport=transport, port=port)

@app.command()
def deploy(env: str = "dev"):
    """Deploy to Vercel."""
    console.print(f"[green]Deploying to {env}...[/green]")
    # Minimal deployment logic

if __name__ == "__main__":
    app()
```

**Result:** 4 files (1900 LOC) → 1 file (150 LOC) = **92% reduction**


