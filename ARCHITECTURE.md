# Atoms MCP Architecture

## Overview

The Atoms MCP project now has a clean, modular architecture with:
1. **Unified CLI** (`atoms-mcp.py`) - Single entry point for all operations
2. **Lightweight Library** (`lib/`) - Reusable utilities with minimal dependencies
3. **Pheno-SDK Integration** - Leverages battle-tested libraries where available
4. **Legacy Compatibility** - Old entry points still work

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                          │
├─────────────────────────────────────────────────────────────────┤
│  ./atoms <command> [options]                                    │
│  ./atoms-mcp.py <command> [options]                             │
│  python -m atoms_mcp                                            │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    atoms-mcp.py (Unified CLI)                   │
├─────────────────────────────────────────────────────────────────┤
│  Commands:                                                      │
│  ├── start      → lib.deployment.start_local_server()          │
│  ├── test       → tests/test_main.py                           │
│  ├── deploy     → lib.deployment.deploy_to_vercel()            │
│  ├── validate   → test_config.py                               │
│  ├── verify     → verify_setup.py                              │
│  ├── vendor     → pheno-vendor CLI (deploy-kit)                │
│  └── config     → Built-in config management                   │
└────────────────────┬────────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        ▼                         ▼
┌──────────────────┐    ┌──────────────────────┐
│  lib/ (Local)    │    │  pheno-sdk (External)│
├──────────────────┤    ├──────────────────────┤
│ deployment.py    │    │ observability-kit    │
│ - deploy_to_     │    │ - StructuredLogger   │
│   vercel()       │    │ - MetricsCollector   │
│ - start_local_   │    │                      │
│   server()       │    │ deploy-kit           │
│                  │    │ - pheno-vendor CLI   │
│ Future:          │    │ - PlatformDetector   │
│ - testing.py     │    │                      │
│ - config.py      │    │ config-kit           │
│ - validation.py  │    │ - Config             │
│ - health.py      │    │ - AppConfig          │
│ - metrics.py     │    │                      │
│                  │    │ mcp-QA               │
│                  │    │ - TestRunner         │
│                  │    │ - CredentialBroker   │
└──────────────────┘    └──────────────────────┘
        │                         │
        └────────────┬────────────┘
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Core Modules (Existing)                      │
├─────────────────────────────────────────────────────────────────┤
│  start_server.py    - Server startup & KInfra integration       │
│  server.py          - MCP server implementation                 │
│  app.py             - FastAPI application                       │
│  tests/test_main.py - Test suite runner                         │
│  test_config.py     - Configuration validation                  │
│  verify_setup.py    - Setup verification                        │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Unified CLI (`atoms-mcp.py`)

**Purpose:** Single entry point for all operations

**Design Principles:**
- Subcommand-based interface (like git, docker)
- Delegates to existing modules (no duplication)
- Graceful fallback when dependencies missing
- Logger-agnostic (works with or without observability-kit)

**Key Features:**
- 7 subcommands: start, test, deploy, validate, verify, vendor, config
- Comprehensive help text
- Production confirmation for critical operations
- Structured logging when available

### 2. Lightweight Library (`lib/`)

**Purpose:** Reusable utilities with minimal dependencies

**Design Principles:**
- **Minimal** - Keep code weight low
- **Reusable** - Can be moved to pheno-sdk
- **Self-contained** - Minimal dependencies
- **Logger-agnostic** - Works with or without logger

**Current Modules:**
- `deployment.py` - Deployment utilities
  - `deploy_to_vercel()` - Vercel deployment
  - `start_local_server()` - Local server with KInfra tunnel

**Future Modules:**
- `testing.py` - Test runner utilities
- `config.py` - Configuration management
- `validation.py` - Setup validation
- `health.py` - Health check utilities
- `metrics.py` - Metrics collection

### 3. Pheno-SDK Integration

**Purpose:** Leverage battle-tested libraries

**Integrated Libraries:**

#### observability-kit (Optional)
```python
from observability import StructuredLogger, LogLevel

logger = StructuredLogger(
    "atoms-mcp",
    service_name="atoms-mcp-cli",
    environment="local"
)
```

**Benefits:**
- JSON structured logging
- Correlation ID tracking
- Metrics collection
- Distributed tracing

#### deploy-kit (Via CLI)
```bash
./atoms vendor setup
```

**Benefits:**
- Pheno-SDK vendoring automation
- Platform-specific configs
- Cross-platform deployment

#### config-kit (Planned)
```python
from config_kit import Config, AppConfig

config = AppConfig.from_env(prefix="ATOMS_")
```

**Benefits:**
- Multi-source configuration
- Pydantic validation
- Secret management

#### mcp-QA (Via test_main.py)
```bash
./atoms test --local --verbose
```

**Benefits:**
- Unified OAuth flow
- Interactive TUI
- Comprehensive reporting

### 4. Core Modules (Existing)

**Purpose:** Existing functionality (unchanged)

**Modules:**
- `start_server.py` - Server startup, KInfra integration
- `server.py` - MCP server implementation
- `app.py` - FastAPI application
- `tests/test_main.py` - Test suite runner
- `test_config.py` - Configuration validation
- `verify_setup.py` - Setup verification

## Data Flow

### Start Local Server

```
User: ./atoms start --port 50003
  │
  ├─> atoms-mcp.py (parse args)
  │
  ├─> lib.deployment.start_local_server()
  │     │
  │     └─> subprocess.run(["python", "start_server.py", "--port", "50003"])
  │           │
  │           ├─> KInfra (port allocation)
  │           ├─> CloudFlare tunnel (HTTPS)
  │           └─> server.py (MCP server)
  │
  └─> Server running at https://atomcp.kooshapari.com
```

### Deploy to Vercel

```
User: ./atoms deploy --preview
  │
  ├─> atoms-mcp.py (parse args)
  │
  ├─> lib.deployment.deploy_to_vercel("preview")
  │     │
  │     ├─> Check .env.preview exists
  │     ├─> Verify Vercel CLI installed
  │     ├─> Run: vercel --yes
  │     ├─> Health check: https://devmcp.atoms.tech/health
  │     └─> Display deployment summary
  │
  └─> Deployed to https://devmcp.atoms.tech
```

### Run Tests

```
User: ./atoms test --local --verbose
  │
  ├─> atoms-mcp.py (parse args)
  │
  ├─> tests/test_main.py (delegate)
  │     │
  │     ├─> mcp-QA (test framework)
  │     ├─> OAuth credential broker
  │     ├─> Test runner with TUI
  │     └─> Test results reporter
  │
  └─> Test results displayed
```

### Vendor Packages

```
User: ./atoms vendor setup
  │
  ├─> atoms-mcp.py (parse args)
  │
  ├─> subprocess.run(["pheno-vendor", "setup"])
  │     │
  │     ├─> deploy-kit (pheno-vendor CLI)
  │     ├─> Auto-detect used packages
  │     ├─> Copy to pheno_vendor/
  │     ├─> Generate requirements-prod.txt
  │     ├─> Create sitecustomize.py
  │     └─> Validate imports
  │
  └─> Packages vendored successfully
```

## Migration Path to Pheno-SDK

### Current State

```
atoms_mcp-old/
├── lib/deployment.py          # Local utilities
└── atoms-mcp.py               # Uses lib.deployment
```

### Future State

```
pheno-sdk/
└── deploy-kit/
    └── deploy_kit/
        ├── vercel.py          # Moved from lib/deployment.py
        ├── local.py           # Moved from lib/deployment.py
        └── cli.py             # Enhanced CLI

atoms_mcp-old/
└── atoms-mcp.py               # Uses deploy_kit
```

### Migration Steps

1. **Extract to pheno-sdk:**
   ```bash
   # Copy deployment utilities
   cp lib/deployment.py ../pheno-sdk/deploy-kit/deploy_kit/vercel.py
   
   # Enhance with additional features
   # - Platform detection
   # - Multi-cloud support
   # - Advanced health checks
   ```

2. **Update atoms-mcp.py:**
   ```python
   # Before
   from lib.deployment import deploy_to_vercel
   
   # After
   from deploy_kit import deploy_to_vercel
   ```

3. **Remove lib/ directory:**
   ```bash
   rm -rf lib/
   ```

4. **Update documentation:**
   - Remove lib/ references
   - Add deploy-kit dependency
   - Update installation instructions

## Benefits of This Architecture

### ✅ Separation of Concerns
- CLI layer (atoms-mcp.py)
- Library layer (lib/)
- Integration layer (pheno-sdk)
- Core layer (existing modules)

### ✅ Minimal Code Weight
- lib/ contains only essential utilities
- Delegates to existing tools
- No code duplication

### ✅ Easy to Maintain
- Clear module boundaries
- Self-contained functions
- Comprehensive documentation

### ✅ Future-Proof
- Easy to migrate to pheno-sdk
- Minimal refactoring needed
- Clear upgrade path

### ✅ Developer Experience
- Single entry point (./atoms)
- Consistent interface
- Helpful error messages
- Comprehensive help text

## Testing Strategy

### Unit Tests
```python
# Test lib/deployment.py functions
from lib.deployment import deploy_to_vercel

def test_deploy_to_vercel():
    result = deploy_to_vercel("preview")
    assert result == 0
```

### Integration Tests
```bash
# Test CLI commands
./atoms start --port 50003
./atoms test --local
./atoms deploy --preview
```

### End-to-End Tests
```bash
# Full workflow
./atoms verify
./atoms vendor setup
./atoms start
./atoms test --local
./atoms deploy --preview
```

## Conclusion

The new architecture provides:
- **Clean separation** between CLI, library, and core modules
- **Minimal code weight** through delegation and reuse
- **Easy migration path** to pheno-sdk
- **Excellent developer experience** with unified CLI
- **Production-ready** with observability and deployment tools

This architecture sets a solid foundation for future enhancements while maintaining backward compatibility and minimizing code duplication.

