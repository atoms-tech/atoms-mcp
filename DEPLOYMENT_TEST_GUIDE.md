# Deployment Testing Guide

## Overview

The Atoms MCP Server has been deployed to Vercel and configured for integration and E2E testing against the `mcpdev.kooshapari.com` deployment target.

## Deployment Target

- **Production Deployment**: `https://mcpdev.atoms.tech`
- **API Endpoint**: `https://mcpdev.atoms.tech/api/mcp`
- **Health Check**: `https://mcpdev.atoms.tech/health`

## Test Configuration

### Environment Variables

Two new environment configuration files have been created:

1. **`.env.integration`** - Configuration for integration tests
   - Points to `MCP_INTEGRATION_BASE_URL=https://mcpdev.atoms.tech/api/mcp`
   - Uses live Supabase connection
   - 30-second timeout
   - 3 retry attempts

2. **`.env.e2e`** - Configuration for E2E tests
   - Points to `MCP_E2E_BASE_URL=https://mcpdev.atoms.tech/api/mcp`
   - Uses live Supabase connection
   - 60-second timeout (longer for full workflows)
   - 5 retry attempts (more resilient)
   - Debug logging enabled

### Test Fixture Updates

#### Integration Tests (`tests/integration/conftest.py`)

The `mcp_client_http` fixture has been updated to:
- Read `MCP_INTEGRATION_BASE_URL` environment variable
- Fall back to local `http://127.0.0.1:8000/api/mcp` for local testing
- Support both local and deployed testing

```python
@pytest_asyncio.fixture
async def mcp_client_http(test_server):
    """Provide HTTP MCP client for integration tests."""
    import os
    base_url = os.getenv("MCP_INTEGRATION_BASE_URL", "http://127.0.0.1:8000/api/mcp")
    async with Client(base_url, timeout=10.0) as client:
        yield client
```

#### E2E Tests (`tests/e2e/conftest.py`)

The `end_to_end_client` fixture has been updated to:
- Connect directly to `https://mcpdev.kooshapari.com/api/mcp`
- Use 30-second timeout for full system interactions
- Support production-like conditions

```python
@pytest_asyncio.fixture
async def end_to_end_client(full_deployment):
    """E2E-ready MCP client with full authentication."""
    import os
    from fastmcp import Client
    
    deployment_url = os.getenv("MCP_E2E_BASE_URL", "https://mcpdev.kooshapari.com/api/mcp")
    async with Client(deployment_url, timeout=30.0) as client:
        yield client
```

## Running Tests

### Local Testing (Against Local Server)

```bash
# Activate environment
source .venv/bin/activate

# Run unit tests (in-memory, no server required)
python cli.py test run --scope unit

# Run integration tests (requires local server running)
python cli.py test run --scope integration
```

### Deployed Testing (Against mcpdev.kooshapari.com)

```bash
# Activate environment and load deployment config
source .venv/bin/activate
export $(cat .env.integration | xargs)  # Load integration config

# Run integration tests against deployed instance
python cli.py test run --scope integration -m integration

# Load E2E config for end-to-end tests
export $(cat .env.e2e | xargs)

# Run E2E tests against deployed instance
python cli.py test run --scope e2e -m e2e
```

### Specific Test Patterns

```bash
# Run only integration tests that call mcpdev
pytest tests/integration/ -v -m integration --durations=10

# Run E2E workflow tests against deployed instance
pytest tests/e2e/test_crud.py -v -m e2e

# Run with verbose logging for debugging
LOGLEVEL=DEBUG pytest tests/e2e/test_auth.py -v -s

# Run performance tests against deployed instance
pytest tests/e2e/test_performance.py -v -m performance
```

## Deployment Health Checks

### Manual Verification

```bash
# Check if deployment is responding
curl -s https://mcpdev.atoms.tech/health | jq .

# Get service info
curl -s https://mcpdev.atoms.tech/ | jq .

# List available tools
curl -s https://mcpdev.atoms.tech/debug/tools | jq .

# Check API endpoint directly
curl -s -X POST https://mcpdev.atoms.tech/api/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "tools/list", "id": 1}' | jq .
```

### Using Pytest Fixtures

```python
# Direct deployment test
@pytest.mark.e2e
async def test_deployed_server_health(end_to_end_client):
    """Verify deployed server responds to requests."""
    # The fixture will automatically connect to mcpdev.kooshapari.com
    tools = await end_to_end_client.list_tools()
    assert len(tools) > 0, "No tools available on deployed server"
```

## Troubleshooting

### 530 Error from Vercel

If you see HTTP 530 errors:
1. Check Vercel deployment logs: `vercel logs --follow`
2. Verify environment variables are set in Vercel dashboard
3. Ensure Python dependencies are installed correctly
4. Check if build completed successfully

### Connection Timeouts

If tests timeout:
1. Increase timeout in `.env.e2e` (default 60 seconds)
2. Check if mcpdev.atoms.tech is responding: `curl https://mcpdev.atoms.tech/health`
3. Verify network connectivity to Vercel endpoints
4. Check if rate limiting is active

### Authentication Failures

If auth fails:
1. Verify Supabase credentials in `.env.integration` and `.env.e2e`
2. Check AuthKit configuration matches deployment
3. Ensure test user has proper permissions in Supabase
4. Verify JWT tokens are valid and not expired

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Test Against Deployed

on: [push, pull_request]

jobs:
  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          source .venv/bin/activate
          pip install -e .
      
      - name: Load E2E config
        run: |
          export $(cat .env.e2e | xargs)
      
      - name: Run E2E tests
        run: |
          python cli.py test run --scope e2e
        env:
          MCP_E2E_BASE_URL: https://mcpdev.atoms.tech/api/mcp
```

## Performance Characteristics

### Expected Response Times

- **Health Check**: < 500ms
- **Tool Listing**: < 1000ms
- **Entity Creation**: < 2000ms
- **Workflow Execution**: < 5000ms

### Rate Limiting

- Default: 120 requests per minute per user
- Distributed rate limiting via Upstash Redis
- Returns HTTP 429 when limit exceeded

## Configuration Reference

| Variable | Integration | E2E | Default |
|----------|-------------|-----|---------|
| `MCP_INTEGRATION_BASE_URL` | `https://mcpdev.kooshapari.com/api/mcp` | - | localhost:8000 |
| `MCP_E2E_BASE_URL` | - | `https://mcpdev.kooshapari.com/api/mcp` | localhost:8000 |
| `MCP_INTEGRATION_TIMEOUT` | 30 | - | 10 |
| `MCP_E2E_TIMEOUT` | - | 60 | 30 |
| `LOG_LEVEL` | INFO | DEBUG | INFO |

## Next Steps

1. **Verify Deployment**: Run health checks to ensure mcpdev is responding
2. **Test Locally First**: Run integration tests against local server
3. **Deploy to Vercel**: Complete `vercel --yes` deployment (if not already done)
4. **Run Against Deployed**: Execute tests with `.env.e2e` configuration
5. **Monitor Performance**: Track response times and error rates
6. **Set Up CI/CD**: Configure GitHub Actions or equivalent

## Contact & Support

For deployment issues:
- Check Vercel dashboard: https://vercel.com/atoms-projects-08029836/atoms-mcp
- Review server logs: `vercel logs --follow`
- Check error metrics in monitoring system

For test failures:
- Enable debug logging: `LOG_LEVEL=DEBUG`
- Check test output for specific errors
- Review Supabase logs for database issues
- Verify network connectivity to mcpdev.kooshapari.com
