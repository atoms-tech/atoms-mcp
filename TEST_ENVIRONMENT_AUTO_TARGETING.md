# Test Environment Auto-Targeting

## Overview

The Atoms MCP CLI now automatically targets the correct deployment environment based on test scope:

- **Unit Tests** → Local (`http://127.0.0.1:8000`)
- **Integration Tests** → Dev (`https://mcpdev.atoms.tech`) - can override
- **E2E Tests** → Dev (`https://mcpdev.atoms.tech`) - can override

## Quick Start

### Run Unit Tests (Local)
```bash
atoms test                    # Default: unit tests on local
atoms test:unit              # Shorthand for unit tests
atoms test:cov               # Coverage report (unit tests)
```

### Run Integration Tests (Dev by Default)
```bash
atoms test:int                # Auto-targets dev (mcpdev.atoms.tech)
atoms test --scope integration  # Explicit scope specification
```

### Run E2E Tests (Dev by Default)
```bash
atoms test:e2e                # Auto-targets dev (mcpdev.atoms.tech)
atoms test --scope e2e        # Explicit scope specification
```

### Override Target Environment
```bash
# Override integration to local
atoms test:int --env local

# Override integration to production
atoms test:int --env prod

# Override e2e to local
atoms test:e2e --env local

# Override e2e to production
atoms test:e2e --env prod
```

## Environment Configurations

### Local Development
- **URL**: `http://127.0.0.1:8000/api/mcp`
- **Database**: Local Supabase (from `.env`)
- **Timeout**: 10 seconds
- **Retries**: 3 attempts
- **Use Case**: Fast development iteration, in-memory client

### Development (mcpdev.atoms.tech)
- **URL**: `https://mcpdev.atoms.tech/api/mcp`
- **Database**: Live Supabase (from environment)
- **Timeout**: 30 seconds
- **Retries**: 5 attempts
- **Use Case**: Test deployed instance, validate integration

### Production (mcp.atoms.tech)
- **URL**: `https://mcp.atoms.tech/api/mcp`
- **Database**: Live Supabase (from environment)
- **Timeout**: 60 seconds
- **Retries**: 5 attempts
- **Use Case**: Final validation before release

## Implementation Details

### TestEnvManager Class
Located in `cli_modules/test_env_manager.py`

**Key Methods:**
- `get_environment_for_scope(scope)` - Auto-detect environment from test scope
- `get_config(environment)` - Get configuration for an environment
- `setup_environment(environment)` - Set environment variables for tests
- `print_environment_info(environment)` - Display environment details
- `verify_environment(environment)` - Health check environment

**Example Usage:**
```python
from cli_modules.test_env_manager import TestEnvManager, TestEnvironment

# Auto-detect environment
env = TestEnvManager.get_environment_for_scope("integration")

# Set up environment
TestEnvManager.setup_environment(env)

# Show info
TestEnvManager.print_environment_info(env)

# Verify it's accessible
is_healthy = TestEnvManager.verify_environment(env)
```

### CLI Integration

**Updated Commands:**
```python
@app.command()
def test(scope: str = "unit", env: Optional[str] = None):
    # Auto-detect or use explicit environment
    environment = TestEnvManager.get_environment_for_scope(scope) if not env else TestEnvironment(env)
    TestEnvManager.setup_environment(environment)
    # Run pytest...

@app.command("test:unit")
def test_unit():
    # Always local
    TestEnvManager.setup_environment(TestEnvironment.LOCAL)
    # Run pytest...

@app.command("test:int")
def test_integration(env: Optional[str] = None):
    # Default dev, allow override
    environment = TestEnvironment(env) if env else TestEnvironment.DEV
    TestEnvManager.setup_environment(environment)
    # Run pytest...

@app.command("test:e2e")
def test_e2e(env: Optional[str] = None):
    # Default dev, allow override
    environment = TestEnvironment(env) if env else TestEnvironment.DEV
    TestEnvManager.setup_environment(environment)
    # Run pytest...
```

## Environment Variables

The manager sets the following environment variables for each test scope:

```
MCP_BASE_URL              # Base URL for MCP server
MCP_HEALTH_URL           # Health check endpoint
MCP_TIMEOUT              # Request timeout in seconds
MCP_RETRY_ATTEMPTS       # Number of retry attempts

# Test fixture-specific URLs
MCP_INTEGRATION_BASE_URL  # Used by integration test fixtures
MCP_E2E_BASE_URL         # Used by E2E test fixtures

# Supabase configuration
NEXT_PUBLIC_SUPABASE_URL     # From environment or local
NEXT_PUBLIC_SUPABASE_ANON_KEY # From environment or local
```

## Test Fixture Configuration

### Integration Test Fixture
```python
@pytest_asyncio.fixture
async def mcp_client_http(test_server):
    """Reads MCP_INTEGRATION_BASE_URL environment variable"""
    base_url = os.getenv("MCP_INTEGRATION_BASE_URL", 
                        "http://127.0.0.1:8000/api/mcp")
    async with Client(base_url, timeout=10.0) as client:
        yield client
```

### E2E Test Fixture
```python
@pytest_asyncio.fixture
async def end_to_end_client(full_deployment):
    """Reads MCP_E2E_BASE_URL environment variable"""
    deployment_url = os.getenv("MCP_E2E_BASE_URL", 
                              "https://mcpdev.atoms.tech/api/mcp")
    async with Client(deployment_url, timeout=30.0) as client:
        yield client
```

## Validation

To validate the auto-targeting is working correctly:

```bash
# Show environment info
python3 << 'EOF'
from cli_modules.test_env_manager import TestEnvManager, TestEnvironment

for scope in ["unit", "integration", "e2e"]:
    env = TestEnvManager.get_environment_for_scope(scope)
    config = TestEnvManager.get_config(env)
    print(f"{scope:13} → {env.value:5} ({config['mcp_base_url']})")
EOF

# Expected output:
# unit            → local (http://127.0.0.1:8000/api/mcp)
# integration     → dev   (https://mcpdev.atoms.tech/api/mcp)
# e2e             → dev   (https://mcpdev.atoms.tech/api/mcp)
```

## Workflow Examples

### Local Development (No Deployment)
```bash
# Just running unit tests locally
atoms test              # Unit tests only
atoms test:cov          # With coverage report
atoms test -v           # Verbose output
```

### Development Against Deployment
```bash
# Test latest changes on dev deployment
atoms test:int          # Integration tests on dev
atoms test:e2e          # E2E tests on dev
atoms test:e2e -v       # Verbose E2E tests
```

### Production Validation
```bash
# Before releasing to production
atoms test:int --env prod    # Integration against prod
atoms test:e2e --env prod    # E2E against prod
```

### Local Testing with Deployed Server (Troubleshooting)
```bash
# If you want to test local fixtures against deployed instance
atoms test:int --env local   # Use local server for integration
atoms test:e2e --env local   # Use local server for E2E
```

## Configuration Files

### Environment Files
- `.env` - Local development configuration
- `.env.integration` - Integration test configuration (points to dev)
- `.env.e2e` - E2E test configuration (points to dev)

### CLI Module
- `cli_modules/test_env_manager.py` - TestEnvManager implementation
- `cli.py` - Updated test commands with environment support

## Health Check

Each environment can be verified:

```bash
# Check if dev deployment is responding
curl https://mcpdev.atoms.tech/health

# Check if production is responding
curl https://mcp.atoms.tech/health

# Check if local server is running
curl http://127.0.0.1:8000/health
```

## Troubleshooting

### Tests fail with "connection refused"
- Check which environment is being used: `atoms test:int` prints environment info
- Verify the server is running for that environment
- Override if needed: `atoms test:int --env local`

### Timeout errors
- Environment-specific timeouts:
  - Local: 10 seconds
  - Dev: 30 seconds
  - Prod: 60 seconds
- Increase timeout for slow networks

### Wrong environment targeted
- Unit tests always use local (correct)
- Integration/E2E default to dev (can override with `--env`)
- Explicitly specify with `--env local|dev|prod`

## Future Enhancements

- [ ] Add `--skip-health-check` flag to skip verification
- [ ] Add `--list-environments` to show all available targets
- [ ] Add configuration file for default environment per scope
- [ ] Add docker support for local supabase validation
- [ ] Add metrics collection for cross-environment testing

## References

- Test configuration: `tests/integration/conftest.py`, `tests/e2e/conftest.py`
- Environment configuration: `.env.integration`, `.env.e2e`
- CLI code: `cli.py` (test commands)
- Manager implementation: `cli_modules/test_env_manager.py`
