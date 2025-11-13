# OAuth Discovery Fix - Quick Summary

## Problem

MCP clients (like Claude Desktop) were getting 404 errors when trying to discover OAuth endpoints:

```
GET /.well-known/oauth-protected-resource → 404 Not Found
GET /.well-known/oauth-authorization-server → 404 Not Found
```

Additionally, when running locally, the protected resource URL was set to the production URL (`https://mcp.atoms.tech/`) instead of the local URL (`http://localhost:8000/`), causing OAuth flow failures.

## Root Causes

1. **Missing OAuth routes**: `HybridAuthProvider` wasn't exposing the `get_routes()` method
2. **Missing helper methods**: `HybridAuthProvider` wasn't exposing `get_resource_metadata_url()`, `get_middleware()`, and `_get_resource_url()`
3. **Wrong base URL for local dev**: Server was using production URL even when running locally

## Fixes Applied

### 1. Updated `services/auth/hybrid_auth_provider.py`

Added methods to expose OAuth discovery routes:

```python
def get_routes(self, mcp_path: Optional[str] = None):
    """Expose OAuth discovery routes from AuthKitProvider."""
    return self.oauth_provider.get_routes()

def get_resource_metadata_url(self):
    """Get the resource metadata URL."""
    return self.oauth_provider.get_resource_metadata_url()

def get_middleware(self):
    """Get middleware from OAuth provider."""
    if hasattr(self.oauth_provider, 'get_middleware'):
        return self.oauth_provider.get_middleware()
    return []

def _get_resource_url(self, mcp_path: str):
    """Get the resource URL for the given MCP path."""
    if hasattr(self.oauth_provider, '_get_resource_url'):
        return self.oauth_provider._get_resource_url(mcp_path)
    return f"{self.base_url.rstrip('/')}{mcp_path}"
```

Also exposed required OAuth attributes:

```python
self.resource_server_url = getattr(oauth_provider, 'resource_server_url', None)
self.authorization_servers = getattr(oauth_provider, 'authorization_servers', [])
```

### 2. Updated `server.py`

Fixed base URL resolution to use local URL for local development:

```python
# Priority:
# 1. ATOMS_FASTMCP_BASE_URL (explicit override)
# 2. Local URL (http://host:port) for local development
# 3. VERCEL_URL for production deployments
# 4. Public URL from env (fallback)

if not base_url:
    host = os.getenv("ATOMS_FASTMCP_HOST", "127.0.0.1")
    port = os.getenv("ATOMS_FASTMCP_PORT", "8000")
    
    vercel_url = os.getenv("VERCEL_URL")
    if vercel_url:
        # Production: use Vercel URL
        base_url = f"https://{vercel_url}"
    else:
        # Local development: use local URL
        base_url = f"http://{host}:{port}"
```

## Verification

### Test OAuth Discovery Endpoints

```bash
# Local
curl http://localhost:8000/.well-known/oauth-protected-resource
# Should return: {"resource": "http://127.0.0.1:8000/", ...}

# Production
curl https://mcp.atoms.tech/.well-known/oauth-protected-resource
# Should return: {"resource": "https://mcp.atoms.tech/", ...}
```

### Test Authorization Server Metadata

```bash
curl http://localhost:8000/.well-known/oauth-authorization-server
# Should return AuthKit metadata
```

## Configuration

### Local Development

```bash
# .env.local
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN=https://your-domain.authkit.app
ATOMS_FASTMCP_HOST=127.0.0.1
ATOMS_FASTMCP_PORT=8000
ATOMS_FASTMCP_TRANSPORT=http

# DO NOT set these for local dev:
# ATOMS_FASTMCP_BASE_URL
# FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL
```

### Production (Vercel)

```bash
# Vercel Environment Variables
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN=https://your-domain.authkit.app
# VERCEL_URL is auto-set by Vercel

# Optional explicit override:
# ATOMS_FASTMCP_BASE_URL=https://mcp.atoms.tech
```

## Files Changed

1. ✅ `services/auth/hybrid_auth_provider.py` - Added OAuth route exposure
2. ✅ `server.py` - Fixed base URL resolution logic

## Testing

Run the server locally:

```bash
python server.py
```

Check the logs for:
```
🌐 AUTH BASE URL -> http://127.0.0.1:8000
✅ Hybrid authentication configured: OAuth + Bearer tokens
```

Test with MCP client (Claude Desktop):
1. Add server to Claude Desktop config
2. OAuth flow should start automatically
3. Browser should open for authentication
4. After auth, Claude Desktop should connect successfully

## Next Steps

1. ✅ Deploy to Vercel
2. ✅ Test with Claude Desktop (OAuth)
3. ✅ Test with atomsAgent (Bearer token)
4. ✅ Verify both auth methods work simultaneously

