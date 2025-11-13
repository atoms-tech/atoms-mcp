# Local Development Guide

## Quick Start

### 1. Environment Setup

Your `.env` file is already configured for local development. The key settings are:

```bash
# Server Configuration
ATOMS_FASTMCP_HOST=127.0.0.1
ATOMS_FASTMCP_PORT=8000
ATOMS_FASTMCP_TRANSPORT=http

# OAuth Configuration
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN=https://decent-hymn-17-staging.authkit.app

# Base URL - COMMENTED OUT for local dev (auto-detects to http://127.0.0.1:8000)
# FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL=https://mcp.atoms.tech
```

**Important:** The `FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL` line is commented out in `.env` so the server auto-detects the local URL.

### 2. Start the Server

```bash
python server.py
```

You should see:
```
🌐 AUTH BASE URL -> http://127.0.0.1:8000
✅ Hybrid authentication configured: OAuth + Bearer tokens
```

### 3. Verify OAuth Endpoints

```bash
# Test protected resource metadata
curl http://localhost:8000/.well-known/oauth-protected-resource

# Expected response:
{
  "resource": "http://127.0.0.1:8000/",
  "authorization_servers": ["https://decent-hymn-17-staging.authkit.app/"],
  "scopes_supported": ["openid", "profile", "email"],
  "bearer_methods_supported": ["header"]
}
```

**✅ The resource URL should be `http://127.0.0.1:8000/` (local)**

### 4. Test with MCP Client

#### Claude Desktop Configuration

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "atoms-mcp-local": {
      "url": "http://localhost:8000/api/mcp",
      "transport": "http"
    }
  }
}
```

#### Start Claude Desktop

1. Restart Claude Desktop
2. OAuth flow should start automatically
3. Browser will open for authentication
4. After auth, Claude Desktop should connect

## Troubleshooting

### Issue: "Protected resource URL mismatch"

**Error:**
```
Protected resource https://mcp.atoms.tech/ does not match expected http://localhost:8000/api/mcp
```

**Cause:** The `.env` file has `FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL` set to production URL

**Solution:**
1. Open `.env`
2. Comment out or remove the line:
   ```bash
   # FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL=https://mcp.atoms.tech
   ```
3. Restart the server
4. Verify the base URL:
   ```bash
   curl http://localhost:8000/.well-known/oauth-protected-resource | jq .resource
   # Should return: "http://127.0.0.1:8000/"
   ```

### Issue: OAuth endpoints return 404

**Error:**
```
GET /.well-known/oauth-protected-resource → 404 Not Found
```

**Cause:** Server not started or wrong port

**Solution:**
1. Check if server is running: `ps aux | grep "python server.py"`
2. Check the port: `lsof -i :8000`
3. Restart the server

### Issue: Port already in use

**Error:**
```
[Errno 48] error while attempting to bind on address ('127.0.0.1', 8000): address already in use
```

**Solution:**
```bash
# Kill existing server
pkill -f "python server.py"

# Or use a different port
ATOMS_FASTMCP_PORT=8001 python server.py
```

## Testing Both Auth Methods

### Test OAuth (External Clients)

Use Claude Desktop as described above.

### Test Bearer Token (Internal Services)

```bash
# Set an internal token (optional)
export ATOMS_INTERNAL_TOKEN="my-secret-token-123"

# Restart server
python server.py

# Test with Bearer token
curl -X POST http://localhost:8000/api/mcp \
  -H "Authorization: Bearer my-secret-token-123" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'
```

## Environment Variables Reference

### Required for Local Development

```bash
ATOMS_FASTMCP_HOST=127.0.0.1
ATOMS_FASTMCP_PORT=8000
ATOMS_FASTMCP_TRANSPORT=http
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN=https://decent-hymn-17-staging.authkit.app
```

### Optional for Local Development

```bash
# Bearer token for internal services
ATOMS_INTERNAL_TOKEN=your-secret-token

# AuthKit JWT validation
WORKOS_CLIENT_ID=client_01K4CGW2J1FGWZYZJDMVWGQZBD
```

### DO NOT SET for Local Development

```bash
# These will override auto-detection and cause issues
# ATOMS_FASTMCP_BASE_URL
# FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL
# VERCEL_URL
```

## Production vs Local

| Setting | Local | Production |
|---------|-------|------------|
| Base URL | `http://127.0.0.1:8000` | `https://mcp.atoms.tech` |
| Auto-detected from | `ATOMS_FASTMCP_HOST:PORT` | `VERCEL_URL` |
| OAuth resource | `http://127.0.0.1:8000/` | `https://mcp.atoms.tech/` |
| MCP endpoint | `http://localhost:8000/api/mcp` | `https://mcp.atoms.tech/api/mcp` |

## Next Steps

1. ✅ Start server locally
2. ✅ Verify OAuth endpoints
3. ✅ Test with Claude Desktop
4. ✅ Test with Bearer token (if needed)
5. 🚀 Deploy to production (see `DEPLOYMENT_CHECKLIST.md`)

