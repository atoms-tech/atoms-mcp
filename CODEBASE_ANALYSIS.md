# Atoms MCP Prod - Comprehensive Codebase Analysis

## 1. DIRECTORY STRUCTURE (Depth=2)

```
atoms-mcp-prod/
├── src/atoms_mcp/           # Main package (new MCP server implementation)
│   ├── core/               # MCP server core
│   ├── models/             # Data models (enums, base classes)
│   └── services/           # Service layer
├── lib/                     # Core library modules
│   ├── atoms/              # Atoms-specific implementations
│   │   ├── infrastructure/ # Infrastructure management
│   │   ├── observability/  # Logging, metrics, health
│   │   ├── core/           # Core server implementation
│   │   └── cli_helpers.py  # CLI utilities
│   ├── schema_sync.py      # Schema synchronization
│   └── deployment_checker.py, server_manager.py
├── server/                  # Server implementations
│   ├── entry_points/       # CLI entry points
│   └── core.py, app.py, auth.py, etc.
├── config/                  # Configuration management
│   ├── settings.py         # Pydantic settings
│   ├── atoms.config.yaml   # Application config
│   └── atoms.secrets.yaml  # Secrets (git-ignored)
├── settings/               # Alternative config module
│   ├── config.py           # YAML-based config
│   ├── app.py              # App settings
│   ├── secrets.py          # Secret management
│   └── combined.py         # Combined settings
├── tools/                   # MCP tools implementation
│   ├── entity/             # Entity CRUD operations
│   ├── workflow/           # Workflow management
│   ├── base.py             # Base tool class
│   └── query.py            # Query tool
├── schemas/                 # Schema definitions
│   ├── sync/               # Schema synchronization
│   └── generated/          # Generated API schemas
├── tests/                   # Comprehensive test suite
│   ├── unit/               # Unit tests (50+ test files)
│   ├── integration/        # Integration tests
│   ├── framework/          # Test framework & fixtures
│   ├── phase3/             # Phase 3 specific tests
│   ├── fixtures/           # Test fixtures
│   └── conftest.py         # Pytest configuration
├── utils/                   # Utilities
│   ├── logging_setup.py    # Logging configuration
│   ├── mcp_adapter.py      # MCP adapter utilities
│   └── setup/              # Setup utilities
├── scripts/                 # Utility scripts
│   └── sync_schema.py
├── infrastructure/          # Infrastructure code
│   └── factory.py
├── docs/                    # Documentation
├── examples/                # Example code
├── atoms_cli.py            # Main CLI (typer-based)
├── atoms_cli_enhanced.py   # Enhanced CLI variant
├── atoms_server.py         # Server launcher
├── atoms                   # Executable CLI script
├── pyproject.toml          # Project configuration
└── config.yml              # Default config file
```

---

## 2. PYTHON FILES IN src/atoms_mcp/ AND THEIR PURPOSE

```
src/atoms_mcp/
├── __init__.py              # Package init, exports AtomsServer
├── core/
│   └── mcp_server.py       # Main AtomsServer class
│                            # - Implements FastMCP server
│                            # - Registers tools (entity, query, workflow)
│                            # - Handles CRUD operations
│                            # - Error handling & logging
├── models/
│   ├── __init__.py         # Package init
│   ├── base.py             # Base model classes
│   └── enums.py            # Enumeration definitions
└── api/                    # API layer (minimal)
    └── services/           # Service implementations
```

**Key Purpose**: `src/atoms_mcp/` is the new modular MCP server package built on FastMCP, providing:
- Model Context Protocol server implementation
- Tool registration (entity, query, workflow)
- Data model definitions
- Service layer abstraction

---

## 3. PHENO-SDK IMPORTS ACROSS CODEBASE

### Files Directly Importing pheno-sdk (28 files total):

**CLI & Server Entry Points:**
- `atoms_cli.py` - RichCLI, ProcessCleanupManager, TunnelManager
- `atoms_cli_enhanced.py` - RichCLI, AsyncTunnelManager, PortAllocator, ProcessCleanupManager
- `atoms_server.py` - (minimal, no direct pheno imports)

**Core Libraries:**
- `lib/__init__.py` - DeploymentConfig, DeploymentState, DeploymentStatus, VercelClient
- `lib/atoms/core/server.py` - Pheno infra imports
- `lib/atoms/infrastructure/infrastructure_bootstrap.py` - GenericServiceOrchestrator
- `lib/atoms/infrastructure/port_manager.py` - AsyncUtils, SmartPortAllocator, PortRegistry, ProcessCleanupConfig
- `lib/atoms/infrastructure/deployment.py` - DeploymentConfig

**Utils & Logging:**
- `utils/logging_setup.py` - LogConfig, get_logger, configure_logging
- `utils/mcp_adapter.py` - MCP adapter utilities

**Server Module:**
- `server/__init__.py` - Server initialization

**Test Framework:**
- `tests/conftest.py` - Test fixtures & configuration
- `tests/test_main.py` - Main test module
- `tests/test_auth_validation.py` - Auth validation tests
- `tests/test_infrastructure.py` - Infrastructure tests
- `tests/framework/atoms_unified_runner.py` - Test runner
- `tests/framework/adapters.py` - Test adapters
- `tests/framework/fixtures.py` - Test fixtures
- `tests/fixtures/fastmcp_mocks.py` - FastMCP mocks
- `tests/fixtures/auth.py` - Auth fixtures
- `tests/plugins/atoms_pytest_plugin.py` - Pytest plugin
- `tests/pytest_support/fixtures.py` - Pytest fixtures

**Phase 3 Tests:**
- `tests/phase3/migrations/test_*.py` - Migration tests (4 files)

**Infrastructure:**
- `infrastructure/factory.py` - Infrastructure factory

---

## 4. CONFIGURATION FILES

### Pydantic Settings:
- **`config/settings.py`** - Main Pydantic settings (DatabaseConfig, TunnelConfig, ServerConfig, FastMCPConfig)
- **`settings/config.py`** - YAML-based configuration (YamlAppSettings, YamlSecrets)
- **`settings/app.py`** - App-specific settings
- **`settings/secrets.py`** - Secret management
- **`settings/combined.py`** - Combined settings module

### YAML Configuration Files:
- **`config.yml`** - Default application configuration
- **`config/atoms.config.yaml`** - Atoms configuration (with history)
- **`config/atoms.secrets.yaml`** - Secrets file (git-ignored)
- **`config/.history/`** - Configuration history files

### Tool Configuration:
- **`pyproject.toml`** - Project metadata, dependencies, tool configs
- **`.pre-commit-config.yaml`** - Pre-commit hooks
- **`prospector.yaml`** - Code analysis config
- **`.yamllint.yaml`** - YAML linting
- **`.markdownlint.yaml`** - Markdown linting

---

## 5. CLI ENTRY POINTS

### Primary Entry Points:

1. **`atoms_cli.py`** (34KB, Main CLI)
   - Entry point: `atoms` command
   - Framework: Typer + Rich
   - Commands:
     - `server` - Server operations
     - `deploy` - Deployment pipeline
     - `monitor` - Observability
     - `schema` - Schema evolution
     - `vector` - Vector database
     - `tunnel` - Network tunneling
     - `config` - Configuration
     - `status` - System health
   - Features:
     - Rich TUI with status display
     - Health monitoring
     - Server management
     - Tunnel setup & management
   - Pheno-SDK Dependencies:
     - `pheno.cli.framework.RichCLI, CommandResult`
     - `pheno.infra.process_cleanup.ProcessCleanupManager`
     - `pheno.infra.tunneling.TunnelManager`

2. **`atoms_cli_enhanced.py`** (15KB, Enhanced Variant)
   - Alternative CLI implementation
   - Pheno-SDK Dependencies:
     - `pheno.cli.framework.RichCLI`
     - `pheno.infra.cloudflare_tunnel.AsyncTunnelManager, TunnelConfig`
     - `pheno.infra.port_allocator.PortAllocator`
     - `pheno.infra.process_cleanup.ProcessCleanupManager`
   - Integrates with `lib.atoms.cli_helpers`

3. **`atoms_server.py`** (100 lines, Minimal Server Launcher)
   - Async server startup
   - FastMCP runner
   - Supports foreground/background modes
   - Environment configuration

4. **`atoms`** (Executable Script, 31KB)
   - Canonical CLI implementation
   - Typer-based command structure
   - Rich TUI support
   - Comprehensive status display
   - Log streaming with live updates

### Server Entry Points:

- **`server/__main__.py`** - Server module entry
- **`server/app.py`** - FastAPI application
- **`server/core.py`** - Core server logic
- **`server/auth.py`** - Authentication
- **`server/tools.py`** - Tool management

---

## 6. TEST DIRECTORIES AND STRUCTURE

### Test Directory Organization:

```
tests/
├── unit/                          # 50+ unit test files
│   ├── test_phase*.py            # Phased coverage targets (Phase 1-9)
│   ├── test_*.py                 # Module-specific tests
│   └── conftest.py               # Fixtures
├── integration/                   # Integration tests
├── framework/                     # Test framework & utilities
│   ├── atoms_helpers.py
│   ├── atoms_unified_runner.py   # Test runner
│   ├── fixtures.py               # Test fixtures
│   ├── adapters.py               # Test adapters
│   ├── auth_session.py           # Auth test utilities
│   ├── cache.py                  # Caching utilities
│   ├── decorators.py             # Test decorators
│   ├── dependencies.py           # Dependency injection
│   ├── data_generators.py        # Test data generation
│   ├── validators.py             # Validation utilities
│   ├── user_story_pattern.py     # User story framework
│   ├── parallel_clients.py       # Parallel testing
│   ├── runner.py                 # Test runner impl
│   ├── harmful.py                # Harmful content detection
│   ├── oauth_session.py          # OAuth testing
│   ├── test_logging_setup.py     # Logging tests
│   └── test_modes.py             # Mode testing
├── fixtures/                      # Shared fixtures
│   ├── __init__.py
│   ├── fastmcp_mocks.py          # FastMCP mocks
│   ├── auth.py                   # Auth fixtures
│   └── *.py                      # Domain-specific fixtures
├── phase3/                        # Phase 3 specific tests
│   ├── migrations/               # Migration tests (4 files)
│   └── rls_policies/             # RLS policy tests
├── plugins/                       # Pytest plugins
│   ├── atoms_pytest_plugin.py
│   └── __init__.py
├── pytest_support/                # Pytest support
│   └── fixtures.py
├── diagnostics/                   # Diagnostic tests
├── performance/                   # Performance tests
├── load/                          # Load testing
├── manual/                        # Manual tests
├── examples/                      # Example tests
├── test_*.py                      # Root test files
│   ├── test_end_to_end.py
│   ├── test_http_adapter_refactoring.py
│   ├── test_workspace_comprehensive.py
│   ├── test_all_workflows_live.py
│   ├── test_query_rag.py
│   ├── test_integration_*.py
│   └── 30+ more
└── conftest.py                    # Root pytest config
```

### Test Configuration (conftest.py):

- Session-scoped fixtures for database, server, auth
- AsyncIO event loop setup
- Mock factory & builder patterns
- Dependency injection
- Performance tracking
- Pheno-SDK integration

### Test Coverage Areas:

1. **Unit Tests** (50+ files)
   - Module-level functionality
   - Phased coverage: Phase 1 (10%), Phase 2 (20%), ... Phase 9 (100%)
   - Quick-win tests, dry runs, hot tests

2. **Integration Tests**
   - End-to-end workflows
   - Service interactions
   - Database operations
   - API integration

3. **Framework Tests**
   - CLI command execution
   - Auth validation
   - Infrastructure bootstrap
   - Server health checks

---

## 7. DEPENDENCY ANALYSIS

### Declared Dependencies in pyproject.toml (22 direct dependencies):

#### Core Framework:
- **fastmcp** >=2.13.0.1 - MCP server framework
- **fastapi** >=0.104.0 - Web framework (USED: server/app.py)
- **uvicorn** >=0.24.0 - ASGI server (USED: server startup)

#### Database & ORM:
- **psycopg2-binary** >=2.9.9 - PostgreSQL driver (USED: database connections)
- **sqlalchemy** >=2.0.44 - ORM layer (USED: database models)
- **supabase** >=2.5.0 - Supabase client (USED: server/supabase_client.py)

#### Configuration & Settings:
- **pydantic** >=2.11.7, <3.0.0 - Data validation (USED: extensively in config/)
- **pydantic-settings** >=2.3.0 - Settings management (USED: config/settings.py)
- **PyYAML** >=6.0 - YAML parsing (USED: settings/config.py, config files)

#### HTTP & Networking:
- **aiohttp** >=3.8.0 - Async HTTP (USED: HTTP adapter tests)
- **httpx** >=0.28.1, <1.0.0 - HTTP client (USED: CLI, test requests)
- **playwright** >=1.40.0 - Browser automation (USED: integration tests)

#### Auth & Security:
- **PyJWT** >=2.8.0 - JWT tokens (USED: server/auth.py)
- **cryptography** >=41.0.0 - Cryptographic operations (USED: auth, secrets)
- **workos** >=1.0.0 - WorkOS integration (USED: enterprise auth)

#### AI/ML & Analytics:
- **google-cloud-aiplatform** >=1.49.0 - Google AI Platform
- **tqdm** >=4.66.0 - Progress bars (USED: CLI progress display)
- **rapidfuzz** >=3.10.0 - Fuzzy matching (USED: entity resolution, query)

#### Utilities:
- **py-key-value-aio** >=0.2.0 - Async key-value store (USED: caching)
- **psutil** >=5.9.0 - System utilities (USED: performance monitoring)
- **typing-extensions** >=4.12.2 - Type hints backport (USED: type annotations)

#### pheno-sdk (CRITICAL DEPENDENCY):
- **pheno-sdk** (local git reference) - Pheno SDK for infrastructure
  - Used in 28 files across the codebase
  - Provides: CLI framework, tunneling, port allocation, logging, testing utilities

### Development Dependencies (40+ packages):

#### Testing:
- pytest, pytest-asyncio, pytest-cov, pytest-xdist, pytest-mock, pytest-dependency, pytest-benchmark, pytest-watch

#### Code Quality:
- ruff, black, isort, pylint, prospector, bandit, interrogate, vulture, semgrep, safety, pip-audit

#### Documentation & Analysis:
- graphviz, radon, xenon, pydeps, monkeytype, importchecker

#### Performance & Profiling:
- locust, memory-profiler, matplotlib

#### Build & Distribution:
- build, twine, pipdeptree

### Dependency Usage Summary:

| Dependency | Category | Used In | Status |
|-----------|----------|---------|--------|
| fastmcp | Core | src/atoms_mcp/core/mcp_server.py | CRITICAL |
| fastapi | Framework | server/app.py, server/core.py | ACTIVE |
| pydantic | Config | config/, settings/ | HEAVY USE |
| pheno-sdk | Infra | 28 files across project | CRITICAL |
| sqlalchemy | ORM | Database models, queries | ACTIVE |
| supabase | Backend | server/supabase_client.py | ACTIVE |
| PyYAML | Config | Settings, config files | ACTIVE |
| httpx | HTTP | CLI, tests | ACTIVE |
| PyJWT | Auth | server/auth.py | ACTIVE |
| Other | Utility | Variable usage | MODERATE |

---

## 8. ARCHITECTURE SUMMARY

### Package Structure:

1. **src/atoms_mcp/** - New MCP server (modular, minimal)
   - Pure FastMCP implementation
   - Lightweight models & services
   - Stateless tool implementations

2. **lib/atoms/** - Atoms-specific business logic
   - Infrastructure management (port allocation, tunneling, deployment)
   - Observability (logging, metrics, health checks)
   - Server management & CLI helpers
   - Schema synchronization

3. **server/** - Legacy/production server code
   - FastAPI application
   - Authentication & authorization
   - Tool implementations
   - Database interactions

4. **config/**, **settings/** - Configuration management
   - Dual system: Pydantic + YAML-based
   - Environment variable support
   - Secret management

5. **tools/** - MCP tool implementations
   - Entity CRUD operations
   - Workflow management
   - Query interface

6. **tests/** - Comprehensive test suite
   - 50+ unit tests with phased coverage
   - Integration & framework tests
   - Test utilities & fixtures

### pheno-sdk Integration:

- **CLI Framework**: RichCLI for enhanced terminal UI
- **Infrastructure**: GenericServiceOrchestrator for port allocation, tunneling
- **Logging**: Standardized logging via mcp-qa testing module
- **Process Management**: ProcessCleanupManager for resource cleanup
- **Tunneling**: AsyncTunnelManager for network tunneling
- **Testing**: mcp-qa framework for MCP-specific testing

### Critical Dependencies:

1. **fastmcp** - MCP server protocol implementation
2. **pheno-sdk** - Infrastructure & utilities (28 files depend on it)
3. **fastapi** - Web framework for HTTP API
4. **pydantic** - Configuration & data validation
5. **sqlalchemy** - Database ORM

---

## 9. KEY CONFIGURATION PATTERNS

### Environment Variable Mapping:

- `ATOMS_*` prefix for main settings
- `ATOMS_TUNNEL_*` for tunnel configuration
- `ATOMS_MCP_*` for FastMCP configuration
- Database: `DATABASE_URL`, `ATOMS_DATABASE_URL`

### Settings Hierarchy:

1. Environment variables (highest priority)
2. YAML config files (atoms.config.yaml)
3. Default values in Pydantic models

### Secret Management:

- `atoms.secrets.yaml` (git-ignored)
- Environment variables for sensitive data
- pydantic-settings validation

---

## 10. CRITICAL OBSERVATIONS

### Strengths:

1. **Modular Architecture**: Clear separation between src/atoms_mcp (MCP core), lib/atoms (business logic), and server (legacy)
2. **Comprehensive Testing**: 50+ unit tests with phased coverage tracking (10% → 100%)
3. **Infrastructure Integration**: Heavy use of pheno-sdk for modern infrastructure patterns
4. **Configuration Flexibility**: Dual Pydantic + YAML system with environment variable support
5. **Multiple CLI Variants**: atoms_cli.py (primary), atoms_cli_enhanced.py (alternative), atoms (executable)

### Risks:

1. **pheno-sdk Dependency**: 28 files directly depend on pheno-sdk; missing import creates fallbacks
2. **Dual Configuration Systems**: Both Pydantic settings and YAML-based configs exist (potential confusion)
3. **CLI Variants**: Three different CLI implementations (atoms, atoms_cli.py, atoms_cli_enhanced.py)
4. **Test Complexity**: Extensive test framework with 50+ test files; potential maintenance overhead
5. **Build Artifacts**: Large build/ and dist/ directories in repo; should be in .gitignore

### Recommendations:

1. Consolidate CLI implementations (atoms vs atoms_cli.py)
2. Standardize on single configuration system (prefer Pydantic + environment variables)
3. Document pheno-sdk dependency requirements clearly
4. Clean up build artifacts from version control
5. Add CI/CD integration for test phases and coverage tracking

