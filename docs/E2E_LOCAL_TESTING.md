# E2E Testing Against Local Server

This guide explains how to run E2E tests against your local MCP server instead of the deployed server.

## Quick Start

1. **Start the local server** (in one terminal):
   ```bash
   source .venv/bin/activate
   
   # Set environment variables for local testing
   export ATOMS_FASTMCP_TRANSPORT=http
   export ATOMS_FASTMCP_HOST=0.0.0.0
   export ATOMS_FASTMCP_PORT=8000
   export ATOMS_FASTMCP_HTTP_PATH=/api/mcp
   export ATOMS_TEST_MODE=true  # Enable test mode for unsigned JWT support
   
   # Start the server
   python server.py
   # OR use the CLI:
   # python cli.py run --port 8000
   ```

2. **Run E2E tests against localhost** (in another terminal):
   ```bash
   source .venv/bin/activate
   
   # Point tests to local server
   export MCP_E2E_BASE_URL=http://localhost:8000/api/mcp
   
   # Run E2E tests
   pytest -q -n 8 tests/e2e/test_data_management.py
   ```

## Environment Variables

### For the Local Server

| Variable | Default | Description |
|----------|---------|-------------|
| `ATOMS_FASTMCP_TRANSPORT` | `stdio` | Set to `http` for HTTP transport |
| `ATOMS_FASTMCP_HOST` | `127.0.0.1` | Host to bind to |
| `ATOMS_FASTMCP_PORT` | `8000` | Port to run on |
| `ATOMS_FASTMCP_HTTP_PATH` | `/api/mcp` | MCP endpoint path |
| `ATOMS_TEST_MODE` | `false` | Set to `true` to enable test mode (accepts unsigned JWTs) |
| `SUPABASE_URL` | - | Your Supabase URL (required for Supabase JWT auth) |
| `SUPABASE_ANON_KEY` | - | Your Supabase anon key (required for Supabase JWT auth) |

### For E2E Tests

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_E2E_BASE_URL` | `https://mcpdev.atoms.tech/api/mcp` | MCP server URL to test against |
| `ATOMS_TEST_EMAIL` | `kooshapari@kooshapari.com` | Email for Supabase authentication |
| `ATOMS_TEST_PASSWORD` | `ASD3on54_Pax90` | Password for Supabase authentication |
| `USE_MOCK_HARNESS` | `false` | Set to `true` to use mock client instead of HTTP |

## Authentication Options

### Option 1: Supabase JWT (Recommended)

The tests will automatically authenticate with Supabase using your credentials and use the Supabase JWT token. Make sure:

1. Your local server has `SUPABASE_URL` and `SUPABASE_ANON_KEY` set
2. The server has been updated with Supabase JWT support (in `HybridAuthProvider`)

### Option 2: Test Mode (Unsigned JWT)

If you want to use unsigned JWTs for testing:

1. Set `ATOMS_TEST_MODE=true` on the server
2. The tests will automatically generate unsigned JWTs

### Option 3: Internal Token

If you want to use an internal bearer token:

1. Set `ATOMS_INTERNAL_TOKEN` on both server and test environment
2. The tests will use this token for authentication

## Example: Complete Local Testing Setup

```bash
# Terminal 1: Start local server
source .venv/bin/activate
export ATOMS_FASTMCP_TRANSPORT=http
export ATOMS_FASTMCP_PORT=8000
export ATOMS_TEST_MODE=true
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_ANON_KEY="your-anon-key"
python server.py

# Terminal 2: Run tests
source .venv/bin/activate
export MCP_E2E_BASE_URL=http://localhost:8000/api/mcp
export ATOMS_TEST_EMAIL="kooshapari@kooshapari.com"
export ATOMS_TEST_PASSWORD="ASD3on54_Pax90"
pytest -q -n 8 tests/e2e/test_data_management.py
```

## Troubleshooting

### Server not responding

- Check that the server is running: `curl http://localhost:8000/health`
- Verify the port is correct: `lsof -i :8000`
- Check server logs for errors

### Authentication failures

- Verify `ATOMS_TEST_MODE=true` is set on the server
- Check that `SUPABASE_URL` and `SUPABASE_ANON_KEY` are set correctly
- Ensure your Supabase credentials are correct

### Connection refused

- Make sure the server is running before starting tests
- Check firewall settings
- Verify `MCP_E2E_BASE_URL` points to the correct URL

## Using Mock Harness Instead

If you want to skip the server entirely and use mocks:

```bash
export USE_MOCK_HARNESS=true
pytest -q -n 8 tests/e2e/test_data_management.py
```

This uses the mock client which doesn't require a running server.
