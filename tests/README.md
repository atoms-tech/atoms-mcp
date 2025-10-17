# Atoms MCP Testing Guide

## Overview

This test suite provides comprehensive testing for the Atoms MCP server with a focus on **fast unit tests** and **thorough integration tests**.

### Test Philosophy

- **Unit Tests**: Fast (<1s), no external dependencies, test individual components
- **Integration Tests**: Require server running, test full workflows with real API calls
- **Session-Scoped Auth**: OAuth performed once per session, shared across all tests
- **Parallel Execution**: Tests can run in parallel using pytest-xdist

---

## Quick Start

### Run Fast Tests (Unit Tests Only)

```bash
# Run unit tests only (default, <1s per test)
pytest

# Or explicitly
pytest -m unit
```

**Expected**: Tests complete in seconds, no server required.

### Run Full Test Suite

```bash
# Run all tests (unit + integration)
pytest -m "unit or integration"

# Or run integration tests only
pytest -m integration
```

**Expected**: Full suite takes longer, requires MCP server running.

---

## Test Structure

```
tests/
├── unit/                    # Fast unit tests (<1s)
│   └── tools/              # Tool-specific unit tests
├── integration/            # Integration tests (require server)
│   ├── test_atoms_tools.py
│   ├── test_entity_tool_comprehensive_live.py
│   └── ...
├── fixtures/               # Shared fixtures
│   ├── auth.py            # Authentication fixtures
│   ├── tools.py           # Tool fixtures
│   └── data.py            # Test data fixtures
├── framework/             # Test framework utilities
│   └── auth_session.py    # Session-scoped auth broker
├── conftest.py           # Pytest configuration
└── README.md            # This file
```

---

## Running Tests

### Basic Commands

```bash
# Run unit tests only (default)
pytest

# Run integration tests
pytest -m integration

# Run all tests
pytest -m "unit or integration"

# Run tests in parallel (faster)
pytest -n auto

# Run specific test file
pytest tests/integration/test_entity_tool.py

# Run specific test function
pytest tests/integration/test_entity_tool.py::test_create_entity

# Stop after first failure
pytest --maxfail=1

# Show test collection without running
pytest --co
```

### Advanced Commands

```bash
# Run tests with verbose output
pytest -v

# Run tests with extra verbose output
pytest -vv

# Run tests and show print statements
pytest -s

# Run tests with coverage
pytest --cov=. --cov-report=html

# Run only slow tests
pytest -m slow

# Run all tests except slow ones
pytest -m "not slow"

# Run auth-related tests
pytest -m auth

# Run specific tool tests
pytest -m entity
pytest -m workspace
pytest -m workflow
```

### Parallel Testing

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel (auto-detect CPU cores)
pytest -n auto

# Run with specific number of workers
pytest -n 4
```

---

## Test Markers

Mark your tests with appropriate markers:

```python
import pytest

@pytest.mark.unit
def test_entity_validation():
    """Fast unit test, no external dependencies."""
    pass

@pytest.mark.integration
@pytest.mark.entity
async def test_create_entity(authenticated_client):
    """Integration test requiring server."""
    pass

@pytest.mark.slow
@pytest.mark.e2e
async def test_full_workflow(authenticated_client):
    """Slow end-to-end test."""
    pass
```

### Available Markers

- `unit` - Unit tests (fast, no external dependencies, <1s)
- `integration` - Integration tests (require server)
- `http` - Tests that call MCP via HTTP
- `e2e` - End-to-end tests (full workflows)
- `auth` - Tests requiring OAuth authentication
- `tool` - Tests for specific MCP tools
- `provider` - Tests for specific OAuth providers
- `parallel` - Tests that can run in parallel
- `slow` - Tests taking longer than 5 seconds
- `workspace` - Workspace tool tests
- `entity` - Entity tool tests
- `relationship` - Relationship tool tests
- `workflow` - Workflow tool tests
- `query` - Query tool tests

---

## Writing Tests

### Unit Tests

Unit tests are **fast** (<1s), have **no external dependencies**, and test individual components.

```python
import pytest

@pytest.mark.unit
def test_entity_validation():
    """Test entity validation logic."""
    from tools.entity import validate_entity_data

    # Test valid data
    valid_data = {"name": "Test", "type": "document"}
    assert validate_entity_data(valid_data) == True

    # Test invalid data
    invalid_data = {"name": ""}
    assert validate_entity_data(invalid_data) == False
```

### Integration Tests

Integration tests require the **MCP server running** and test full workflows.

```python
import pytest

@pytest.mark.integration
@pytest.mark.entity
async def test_create_and_get_entity(authenticated_client):
    """Test entity creation and retrieval."""
    # Create entity
    create_result = await authenticated_client.call_tool("create_entity", {
        "name": "Test Document",
        "type": "document",
        "data": {"content": "Test content"}
    })
    assert create_result["success"] == True
    entity_id = create_result["entity_id"]

    # Get entity
    get_result = await authenticated_client.call_tool("get_entity", {
        "entity_id": entity_id
    })
    assert get_result["success"] == True
    assert get_result["entity"]["name"] == "Test Document"
```

### Using Fixtures

#### Fast HTTP Client (Session-Scoped)

The `authenticated_client` fixture provides a **session-scoped authenticated HTTP client** that:
- Authenticates **once** per test session (reuses credentials)
- Provides direct HTTP access to MCP tools (no MCP client overhead)
- Supports parallel test execution

```python
import pytest

@pytest.mark.integration
async def test_workspace_tool(authenticated_client):
    """Test using session-scoped authenticated client."""
    result = await authenticated_client.call_tool("workspace_operation", {
        "operation": "list_projects",
        "params": {}
    })
    assert result["success"] == True
```

#### Fresh Credentials

Use `fresh_authenticated_client` when you need **fresh credentials** (e.g., testing auth refresh):

```python
import pytest

@pytest.mark.integration
@pytest.mark.auth
async def test_auth_refresh(fresh_authenticated_client):
    """Test auth refresh with fresh credentials."""
    result = await fresh_authenticated_client.call_tool("get_entity", {
        "entity_id": "test-id"
    })
    assert result["success"] == True
```

#### Mock Credentials

Use `mock_authenticated_client` for **unit tests** (no real OAuth):

```python
import pytest

@pytest.mark.unit
async def test_client_headers(mock_authenticated_client):
    """Test client header construction."""
    headers = mock_authenticated_client._build_headers()
    assert "Content-Type" in headers
```

---

## Authentication

### How It Works

1. **Session-Scoped OAuth**: Authentication is performed **once per pytest session**
2. **Credential Caching**: Credentials are cached to `~/.atoms_mcp_test_cache/`
3. **Automatic Reuse**: Cached credentials are reused across test runs
4. **Parallel-Safe**: Shared credentials work across parallel test workers

### Environment Variables

```bash
# WorkOS AuthKit (Required for integration tests)
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN=https://your-domain.authkit.app
WORKOS_CLIENT_ID=client_YOUR_CLIENT_ID
WORKOS_API_KEY=sk_test_YOUR_API_KEY

# MCP Server
MCP_ENDPOINT=https://mcp.atoms.tech/api/mcp

# Optional: Demo credentials for automated testing
FASTMCP_DEMO_USER=demo@example.com
FASTMCP_DEMO_PASS=demo_password
```

### Clearing Auth Cache

```bash
# Remove cached credentials
rm -rf ~/.atoms_mcp_test_cache/

# Or clear in Python
python -c "from tests.framework.auth_session import get_auth_broker; import asyncio; asyncio.run(get_auth_broker().get_authenticated_credentials(force_refresh=True))"
```

---

## Troubleshooting

### Tests Are Slow

**Problem**: Tests taking longer than expected.

**Solution**:
```bash
# Run unit tests only (fast)
pytest -m unit

# Skip slow tests
pytest -m "not slow"

# Run tests in parallel
pytest -n auto
```

### Integration Tests Failing

**Problem**: Integration tests fail with connection errors.

**Solution**:
1. Ensure MCP server is running:
   ```bash
   # Start server
   uvicorn app:app --reload --port 8000

   # Or using FastMCP
   python -m fastmcp run server:mcp
   ```

2. Check server health:
   ```bash
   curl http://localhost:8000/health
   ```

3. Verify environment variables:
   ```bash
   # Check required vars are set
   echo $WORKOS_CLIENT_ID
   echo $WORKOS_API_KEY
   echo $MCP_ENDPOINT
   ```

### Authentication Issues

**Problem**: Tests fail with authentication errors.

**Solution**:
1. Clear auth cache:
   ```bash
   rm -rf ~/.atoms_mcp_test_cache/
   ```

2. Verify OAuth configuration:
   ```bash
   # Check AuthKit domain
   echo $FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN

   # Check client ID
   echo $WORKOS_CLIENT_ID
   ```

3. Run auth test explicitly:
   ```bash
   pytest tests/integration/test_oauth_flow.py -v
   ```

### Import Errors

**Problem**: Tests fail with import errors.

**Solution**:
```bash
# Install test dependencies
uv sync

# Verify installation
python -c "import pytest; import pytest_asyncio; print('OK')"
```

### Parallel Test Issues

**Problem**: Tests fail when running in parallel but pass individually.

**Solution**:
1. Check if test is properly isolated (no shared state)
2. Use `isolated_client` fixture for parallel tests:
   ```python
   @pytest.mark.parallel
   async def test_with_isolation(isolated_client):
       # This test runs safely in parallel
       pass
   ```

3. Mark tests that can't run in parallel:
   ```python
   @pytest.mark.no_parallel
   async def test_needs_serialization():
       # This test must run alone
       pass
   ```

### Fixture Not Found

**Problem**: Fixture not found error.

**Solution**:
1. Check fixture is imported in `conftest.py`
2. Check fixture scope matches test scope
3. Verify fixture is in correct location (`tests/fixtures/`)

---

## Performance Tips

### Make Tests Faster

1. **Write Unit Tests**: Unit tests are 10-100x faster than integration tests
   ```python
   @pytest.mark.unit  # <1s
   def test_validation():
       pass
   ```

2. **Use Session-Scoped Fixtures**: Reuse expensive setup
   ```python
   @pytest.fixture(scope="session")
   async def authenticated_client():
       # Setup once, use everywhere
       pass
   ```

3. **Run Tests in Parallel**:
   ```bash
   pytest -n auto
   ```

4. **Skip Slow Tests During Development**:
   ```bash
   pytest -m "not slow"
   ```

5. **Use Mock Clients for Unit Tests**:
   ```python
   @pytest.mark.unit
   async def test_fast(mock_authenticated_client):
       # No real OAuth, instant
       pass
   ```

---

## Adding New Tests

### 1. Choose Test Type

**Unit Test**: If testing individual functions/classes without external dependencies
- Location: `tests/unit/`
- Marker: `@pytest.mark.unit`
- Speed: <1s per test

**Integration Test**: If testing full workflows with real API calls
- Location: `tests/integration/`
- Marker: `@pytest.mark.integration`
- Speed: May be slower

### 2. Create Test File

```python
# tests/integration/test_my_feature.py

import pytest

@pytest.mark.integration
@pytest.mark.entity  # Add relevant markers
async def test_my_feature(authenticated_client):
    """Test description."""
    result = await authenticated_client.call_tool("my_tool", {
        "param": "value"
    })
    assert result["success"] == True
```

### 3. Add Test Data (Optional)

```python
# tests/fixtures/data.py

import pytest

@pytest.fixture
def sample_entity_data():
    """Sample entity data for tests."""
    return {
        "name": "Test Entity",
        "type": "document",
        "data": {"content": "Test content"}
    }
```

### 4. Run Your Test

```bash
# Run new test
pytest tests/integration/test_my_feature.py -v

# Run with marker
pytest -m entity -v
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        uv sync

    - name: Run unit tests
      run: |
        pytest -m unit --cov=. --cov-report=xml

    - name: Run integration tests
      run: |
        pytest -m integration
      env:
        WORKOS_CLIENT_ID: ${{ secrets.WORKOS_CLIENT_ID }}
        WORKOS_API_KEY: ${{ secrets.WORKOS_API_KEY }}
        MCP_ENDPOINT: ${{ secrets.MCP_ENDPOINT }}
```

---

## Additional Resources

- **[Main README.md](../README.md)** - Project overview
- **[ARCHITECTURE.md](../ARCHITECTURE.md)** - System architecture
- **[TROUBLESHOOTING.md](../TROUBLESHOOTING.md)** - General troubleshooting
- **[pytest.ini](../pytest.ini)** - Pytest configuration
- **[conftest.py](conftest.py)** - Shared fixtures

---

## Getting Help

1. Check this README first
2. Check [TROUBLESHOOTING.md](../TROUBLESHOOTING.md)
3. Run tests with verbose output: `pytest -vv`
4. Check test logs in `.pytest_cache/`
5. Open an issue on GitHub

---

**Happy Testing!**
