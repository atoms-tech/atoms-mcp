# Quick Start: Local Server for E2E Testing

## Problem
Tests are failing with "All connection attempts failed" because the local server isn't running.

## Solution

### Option 1: Use the CLI (Recommended)

```bash
# Start server with HTTP transport
atoms run --http

# Or with custom port
atoms run --http --port 8001
```

### Option 2: Use the Script

```bash
# Start server using the helper script
./scripts/start_local_server.sh
```

### Option 3: Manual Start

```bash
source .venv/bin/activate

# Set environment variables
export ATOMS_FASTMCP_TRANSPORT=http
export ATOMS_FASTMCP_HOST=0.0.0.0
export ATOMS_FASTMCP_PORT=8000
export ATOMS_FASTMCP_HTTP_PATH=/api/mcp
export ATOMS_TEST_MODE=true

# Start server
python server.py
```

## Verify Server is Running

```bash
# Check if server is listening
curl http://localhost:8000/health

# Should return: OK
```

## Run Tests

Once the server is running, in another terminal:

```bash
source .venv/bin/activate
atoms test --env local
```

Or:

```bash
export MCP_E2E_BASE_URL=http://localhost:8000/api/mcp
pytest -q -n 8 tests/e2e/test_data_management.py
```

## Troubleshooting

### Port already in use
```bash
# Find what's using port 8000
lsof -i :8000

# Kill the process or use a different port
atoms run --http --port 8001
```

### Server not responding
- Check server logs for errors
- Verify environment variables are set
- Make sure `ATOMS_FASTMCP_TRANSPORT=http` is set

### Authentication issues
- Set `ATOMS_TEST_MODE=true` to enable test mode
- Or configure Supabase credentials for Supabase JWT auth
