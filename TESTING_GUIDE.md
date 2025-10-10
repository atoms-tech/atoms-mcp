# Atoms MCP Testing Guide

## Overview

This guide documents the test infrastructure, known issues, and recommended practices for testing the Atoms MCP server.

## Test Infrastructure

### Test Types

1. **Unit Tests** (`tests/unit/`) - Fast, isolated tests using FastHTTPClient
2. **Integration Tests** (`tests/integration/`) - Full MCP client tests
3. **E2E Tests** - End-to-end workflow tests

### Authentication

Tests use session-scoped OAuth authentication via `UnifiedCredentialBroker` from the `mcp_qa` package:

- **OAuth happens once per test session** - Credentials are cached and reused
- **Automatic re-authentication** - 401 errors trigger automatic token refresh
- **Playwright automation** - OAuth flow is automated using Playwright

### Fast HTTP Client

The `FastHTTPClient` (from `mcp_qa.adapters.fast_http_client`) provides:

- **20x faster than MCP client** - Direct HTTP POST with JSON-RPC 2.0
- **Real backend validation** - Tests against actual Supabase with RLS policies
- **Automatic retries** - Handles timeouts and transient errors
- **Re-authentication** - Automatically refreshes expired tokens

## Running Tests

### Basic Usage

```bash
# Run all unit tests
pytest tests/unit/ -v

# Run specific test file
pytest tests/unit/test_entity_fast.py -v

# Run with parallel execution (faster)
pytest tests/unit/ -v -n auto

# Run with detailed logging
pytest tests/unit/ -v -s --log-cli-level=DEBUG
```

### Environment Variables

```bash
# MCP endpoint (default: https://atomcp.kooshapari.com/api/mcp)
export MCP_ENDPOINT="https://your-server.com/api/mcp"

# OAuth provider (default: authkit)
export ATOMS_OAUTH_PROVIDER="authkit"

# Test credentials (for OAuth automation)
export ZEN_TEST_EMAIL="your-email@example.com"
export ZEN_TEST_PASSWORD="your-password"
```

### Using Local Server

```bash
# Enable local server for tests
export ATOMS_USE_LOCAL_SERVER=true

# Start local server (in separate terminal)
python start_local_server.py

# Run tests against local server
pytest tests/unit/ -v
```

## Known Issues and Workarounds

### 1. "Unknown tool: data_query" Errors

**Issue**: Production server may not have latest tool registrations

**Affected Tests**: All `test_query_fast.py` tests

**Workaround**:
```bash
# Use local server for testing
export ATOMS_USE_LOCAL_SERVER=true
python start_local_server.py
pytest tests/unit/test_query_fast.py -v
```

**Permanent Fix**: Deploy updated server code to production

### 2. 401 Unauthorized Errors

**Issue**: OAuth tokens expire during long test runs

**Status**: ✅ **FIXED** - Automatic re-authentication is implemented

**How it works**:
- FastHTTPClient detects 401 errors
- Calls `reauthenticate_callback` to get fresh token
- Retries request with new token
- Up to 5 retry attempts with exponential backoff

### 3. Timeout Errors (httpx.ReadTimeout)

**Issue**: Some operations take longer than 120 seconds

**Affected Operations**:
- Large list operations
- Complex workflow executions
- Slow database queries

**Workaround**:
```python
# FastHTTPClient timeout is configured in mcp_qa package
# Cannot be changed without modifying external package

# Alternative: Use local server with faster database
export ATOMS_USE_LOCAL_SERVER=true
```

**Note**: Timeout is set to 120 seconds in FastHTTPClient (external package)

### 4. 500 Internal Server Errors - Organization Type

**Issue**: Database enum type mismatch

**Error**: `invalid input value for enum organization_type: "business"`

**Valid Values**: `"team"` (default), possibly others

**Fix**: Always use `"team"` for organization type:
```python
{
    "name": "Test Org",
    "slug": "test-org",
    "type": "team"  # ✅ Valid enum value
}
```

### 5. RLS Policy Errors

**Issue**: Row Level Security policies blocking access

**Error**: `TABLE_ACCESS_RESTRICTED: Access to test_req table is restricted`

**Cause**: User context not properly set or RLS policy too restrictive

**Workaround**: Ensure proper authentication and user context

**Permanent Fix**: Update RLS policies in Supabase

### 6. Event Loop Closed Errors

**Issue**: Session-scoped fixtures closing event loop prematurely

**Status**: ✅ **FIXED** - Improved event loop management in conftest.py

**Fix Applied**:
```python
@pytest.fixture(scope="session")
def event_loop():
    """Provide session-scoped event loop for async tests."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    asyncio.set_event_loop(loop)
    
    yield loop
    
    # Safely close loop after all tests
    try:
        if not loop.is_closed():
            loop.close()
    except Exception:
        pass
```

### 7. OAuth Timeout Errors

**Issue**: OAuth flow timing out during authentication

**Error**: `RuntimeError: OAuth URL not received and auth did not complete`

**Causes**:
- MCP server is down or slow
- Network connectivity issues
- Playwright browser automation issues

**Workaround**:
```bash
# Increase timeout (if using local mcp_qa fork)
# Or ensure server is responsive before running tests

# Check server health
curl https://atomcp.kooshapari.com/health
```

## Best Practices

### 1. Use Session-Scoped Fixtures

```python
@pytest.mark.asyncio
async def test_entity_operation(authenticated_client):
    """Use session-scoped authenticated_client fixture."""
    result = await authenticated_client.call_tool("entity_tool", {...})
    assert result["success"]
```

### 2. Handle Known Failures Gracefully

```python
@pytest.mark.asyncio
async def test_with_known_issue(authenticated_client):
    """Test with known RLS issue."""
    result = await authenticated_client.call_tool("entity_tool", {...})
    
    if not result.get("success"):
        error = result.get("error", "")
        if "updated_by" in error:
            pytest.skip("Known RLS issue: updated_by constraint")
        else:
            pytest.fail(f"Unexpected error: {error}")
```

### 3. Use Proper Test Data

```python
# ✅ Good - Uses valid enum values
org_data = {
    "name": "Test Org",
    "slug": "test-org-123",
    "type": "team"  # Valid enum value
}

# ❌ Bad - Invalid enum value
org_data = {
    "name": "Test Org",
    "slug": "test-org-123",
    "type": "business"  # Invalid - will cause 500 error
}
```

### 4. Clean Up Test Data

```python
@pytest.mark.asyncio
async def test_with_cleanup(authenticated_client):
    """Test with proper cleanup."""
    # Create test entity
    create_result = await authenticated_client.call_tool(
        "entity_tool",
        {"entity_type": "project", "operation": "create", "data": {...}}
    )
    
    try:
        # Run test
        assert create_result["success"]
        project_id = create_result["data"]["id"]
        
        # ... test operations ...
        
    finally:
        # Clean up
        if create_result.get("success"):
            await authenticated_client.call_tool(
                "entity_tool",
                {
                    "entity_type": "project",
                    "operation": "delete",
                    "entity_id": project_id
                }
            )
```

## Troubleshooting

### Tests Hanging

**Symptom**: Tests hang indefinitely

**Possible Causes**:
1. OAuth flow waiting for user input
2. Server not responding
3. Event loop deadlock

**Solutions**:
```bash
# Check if server is running
curl https://atomcp.kooshapari.com/health

# Run with timeout
pytest tests/unit/ -v --timeout=300

# Enable debug logging
pytest tests/unit/ -v -s --log-cli-level=DEBUG
```

### Authentication Failures

**Symptom**: OAuth fails or tokens invalid

**Solutions**:
```bash
# Clear OAuth cache
rm -rf ~/.cache/atoms_mcp/oauth_tokens.json

# Check credentials
echo $ZEN_TEST_EMAIL
echo $ZEN_TEST_PASSWORD

# Re-run tests (will trigger fresh OAuth)
pytest tests/unit/ -v
```

### Database Errors

**Symptom**: RLS errors, constraint violations

**Solutions**:
1. Check user has proper permissions
2. Verify RLS policies in Supabase
3. Ensure proper user context is set
4. Use valid enum values for fields

## Performance Tips

### 1. Use Parallel Execution

```bash
# Run tests in parallel (4x faster)
pytest tests/unit/ -v -n auto
```

### 2. Use Local Server

```bash
# Local server is faster than production
export ATOMS_USE_LOCAL_SERVER=true
python start_local_server.py
pytest tests/unit/ -v
```

### 3. Run Specific Tests

```bash
# Run only fast tests
pytest tests/unit/test_entity_fast.py -v

# Skip slow tests
pytest tests/unit/ -v -m "not slow"
```

## Contributing

When adding new tests:

1. Use `authenticated_client` fixture for session-scoped auth
2. Handle known issues gracefully with `pytest.skip()`
3. Use valid test data (check schemas in `tools/entity/schema.py`)
4. Clean up test data in `finally` blocks
5. Document any new known issues in this guide

## Support

For issues or questions:

1. Check this guide for known issues
2. Review test output for specific error messages
3. Enable debug logging: `pytest -v -s --log-cli-level=DEBUG`
4. Check server logs if using local server

