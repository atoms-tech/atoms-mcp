# Dual Authentication Solution for Atoms MCP Server

## Problem Statement

The Atoms MCP server needs to support **two different authentication methods simultaneously**:

1. **Bearer Token Authentication** - For internal backend services (atomsAgent)
   - Uses static bearer tokens or AuthKit JWTs
   - No OAuth flow required
   - Direct API access

2. **OAuth Authentication** - For external MCP clients (Claude Desktop, etc.)
   - Full OAuth 2.0 flow with Dynamic Client Registration (DCR)
   - Requires browser-based authentication
   - MCP protocol discovery endpoints

## The Challenge

The original `HybridAuthProvider` wrapped `AuthKitProvider` but **didn't expose the OAuth discovery routes** that MCP clients need. This caused 404 errors when clients tried to discover OAuth endpoints:

```
INFO:     127.0.0.1:54010 - "GET /.well-known/oauth-protected-resource HTTP/1.1" 404 Not Found
INFO:     127.0.0.1:54010 - "GET /.well-known/oauth-authorization-server HTTP/1.1" 404 Not Found
```

## The Solution

### 1. Updated `HybridAuthProvider` to Expose OAuth Routes

**File**: `services/auth/hybrid_auth_provider.py`

**Key Changes**:

```python
class HybridAuthProvider(AuthProvider):
    def __init__(self, oauth_provider: AuthKitProvider, ...):
        self.oauth_provider = oauth_provider
        
        # Expose ALL attributes from OAuth provider for FastMCP compatibility
        self.base_url = oauth_provider.base_url
        self.required_scopes = getattr(oauth_provider, 'required_scopes', [])
        self.authkit_domain = getattr(oauth_provider, 'authkit_domain', None)
        self.resource_server_url = getattr(oauth_provider, 'resource_server_url', None)
        self.authorization_servers = getattr(oauth_provider, 'authorization_servers', [])
        
        # ... bearer token setup ...
    
    def get_routes(self):
        """Get OAuth discovery routes from the underlying OAuth provider.
        
        This is CRITICAL for MCP clients to discover OAuth endpoints.
        """
        return self.oauth_provider.get_routes()
```

### 2. How It Works

#### For Internal Services (Bearer Token)

```
atomsAgent → Atoms MCP Server
Headers: Authorization: Bearer <authkit-jwt>

HybridAuthProvider.authenticate():
1. Detects Bearer token in Authorization header
2. Tries internal_token_verifier (static token)
3. Tries authkit_jwt_verifier (AuthKit JWT)
4. Returns auth context if valid
```

#### For External MCP Clients (OAuth)

```
MCP Client → Atoms MCP Server

1. Client: GET /.well-known/oauth-protected-resource
   Server: Returns OAuth metadata (via HybridAuthProvider.get_routes())

2. Client: GET /.well-known/oauth-authorization-server  
   Server: Returns AuthKit metadata (via HybridAuthProvider.get_routes())

3. Client: Initiates OAuth flow
   Server: Delegates to AuthKitProvider

4. Client: Sends requests with OAuth token
   Server: Validates via AuthKitProvider
```

## Configuration

### Environment Variables

#### Production (Vercel)

```bash
# OAuth (AuthKit) - Required for external clients
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN=https://your-authkit-domain.authkit.app

# Base URL - Auto-detected from VERCEL_URL, or set explicitly
# ATOMS_FASTMCP_BASE_URL=https://mcp.atoms.tech  # Optional override

# Bearer Token - Optional for internal services
ATOMS_INTERNAL_TOKEN=your-internal-token-here

# AuthKit JWT Validation - Optional for frontend/backend tokens
WORKOS_CLIENT_ID=your-workos-client-id
# JWKS URI is auto-constructed from authkit_domain
```

#### Local Development

```bash
# OAuth (AuthKit) - Required for external clients
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN=https://your-authkit-domain.authkit.app

# Server configuration
ATOMS_FASTMCP_HOST=127.0.0.1  # or localhost
ATOMS_FASTMCP_PORT=8000
ATOMS_FASTMCP_TRANSPORT=http

# Base URL - Auto-detected as http://127.0.0.1:8000
# DO NOT set ATOMS_FASTMCP_BASE_URL or FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL
# for local development - let it auto-detect!

# Bearer Token - Optional for internal services
ATOMS_INTERNAL_TOKEN=your-internal-token-here

# AuthKit JWT Validation - Optional for frontend/backend tokens
WORKOS_CLIENT_ID=your-workos-client-id
```

### Base URL Resolution Logic

The server automatically determines the correct base URL:

1. **Explicit override**: `ATOMS_FASTMCP_BASE_URL` (if set)
2. **Production**: `https://{VERCEL_URL}` (if VERCEL_URL is set)
3. **Local development**: `http://{ATOMS_FASTMCP_HOST}:{ATOMS_FASTMCP_PORT}`
4. **Fallback**: `FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL`

This ensures:
- ✅ Local MCP clients see `http://localhost:8000/` or `http://127.0.0.1:8000/`
- ✅ Production MCP clients see `https://mcp.atoms.tech/`
- ✅ OAuth protected resource URL matches the actual server URL

### Server Setup

```python
from services.auth.hybrid_auth_provider import create_hybrid_auth_provider

auth_provider = create_hybrid_auth_provider(
    authkit_domain=os.getenv("FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN"),
    base_url=base_url,
    internal_token=os.getenv("ATOMS_INTERNAL_TOKEN"),
    authkit_client_id=os.getenv("WORKOS_CLIENT_ID"),
    authkit_jwks_uri=f"{authkit_domain}/.well-known/jwks.json"
)

mcp = FastMCP(
    name="atoms-fastmcp-consolidated",
    auth=auth_provider
)
```

## Testing

Run the test script to verify OAuth routes are exposed:

```bash
python test_hybrid_auth_simple.py
```

Expected output:
```
✅ HybridAuthProvider successfully exposes OAuth routes
✅ MCP clients should be able to discover OAuth endpoints
```

## Deployment

1. **Commit the changes**:
   ```bash
   git add services/auth/hybrid_auth_provider.py
   git commit -m "fix: expose OAuth discovery routes in HybridAuthProvider"
   ```

2. **Deploy to Vercel**:
   ```bash
   git push origin working-deployment
   ```

3. **Verify endpoints are accessible**:
   ```bash
   curl https://mcp.atoms.tech/.well-known/oauth-protected-resource
   curl https://mcp.atoms.tech/.well-known/oauth-authorization-server
   ```

## Benefits

✅ **Single Server** - One MCP server handles both auth methods
✅ **No Code Duplication** - Reuses AuthKitProvider for OAuth
✅ **Backward Compatible** - Existing bearer token auth still works
✅ **MCP Compliant** - Exposes required OAuth discovery endpoints
✅ **Flexible** - Can enable/disable each auth method independently

## Next Steps

1. Deploy the updated code
2. Test with Claude Desktop (OAuth flow)
3. Test with atomsAgent (Bearer token flow)
4. Monitor logs for any auth errors
5. Update documentation with auth flow diagrams

