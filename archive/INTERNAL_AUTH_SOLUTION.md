# Internal Authentication Solution for Atoms MCP

## Problem Statement

**Current State**:
- Atoms MCP uses OAuth (AuthKit) for public client authentication
- OAuth requires user-driven login flow
- Tokens can expire, requiring re-authentication

**Requirement**:
- Internal chatbot (agentApi/atomsAgent) needs to load Atoms MCP as a system-level MCP
- Should NOT require manual OAuth login for internal use
- Frontend auth status should be transient to the MCP
- Public clients should still use OAuth

**Solution**: Dual authentication mode
1. **Public clients**: OAuth (AuthKit) - existing behavior
2. **Internal clients**: Bearer token verification - new behavior

---

## Architecture

### Dual Authentication Strategy

```
Request arrives
  ↓
Check Authorization header
  ↓
  ├─ Has "Bearer <token>" → Token Verification Path
  │   ↓
  │   ├─ Internal token? → Validate against internal secret
  │   └─ Frontend token? → Validate against Supabase JWT
  │
  └─ No Bearer token → OAuth Path (existing)
      ↓
      Redirect to AuthKit login
```

### Token Types

**1. Internal Service Token** (for agentApi/atomsAgent)
- Long-lived token shared between services
- Stored in environment variables
- No expiration (or very long expiration)
- Used for system-to-system communication

**2. Frontend User Token** (for transient auth)
- Supabase JWT from frontend authentication
- Short-lived (follows Supabase session)
- Contains user identity and permissions
- Passed from frontend → agentApi → Atoms MCP

---

## Implementation Plan

### Step 1: Add Token Verification Provider

Create a new auth provider that supports both internal and frontend tokens:

```python
# services/auth/dual_token_verifier.py
from fastmcp.server.auth import TokenVerifier
from supabase import Client
import os
import jwt

class DualTokenVerifier(TokenVerifier):
    """Verifies both internal service tokens and Supabase JWTs."""
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        self.internal_secret = os.getenv("ATOMS_INTERNAL_AUTH_SECRET")
        self.supabase_jwt_secret = os.getenv("SUPABASE_JWT_SECRET")
        
    async def verify_token(self, token: str) -> dict:
        """Verify token and return claims."""
        
        # Try internal token first
        if self._is_internal_token(token):
            return await self._verify_internal_token(token)
        
        # Try Supabase JWT
        return await self._verify_supabase_jwt(token)
    
    def _is_internal_token(self, token: str) -> bool:
        """Check if token is internal service token."""
        return token.startswith("atoms_internal_")
    
    async def _verify_internal_token(self, token: str) -> dict:
        """Verify internal service token."""
        expected = f"atoms_internal_{self.internal_secret}"
        if token != expected:
            raise ValueError("Invalid internal token")
        
        return {
            "client_id": "internal-service",
            "scopes": ["admin", "read", "write"],
            "type": "internal"
        }
    
    async def _verify_supabase_jwt(self, token: str) -> dict:
        """Verify Supabase JWT from frontend."""
        try:
            # Decode and verify JWT
            payload = jwt.decode(
                token,
                self.supabase_jwt_secret,
                algorithms=["HS256"],
                audience="authenticated"
            )
            
            return {
                "client_id": payload.get("sub"),
                "email": payload.get("email"),
                "scopes": payload.get("role", "authenticated").split(","),
                "type": "frontend"
            }
        except jwt.ExpiredSignatureError:
            raise ValueError("Token expired")
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid token: {e}")
```

### Step 2: Update Server Configuration

```python
# server.py
def create_consolidated_server():
    # ... existing code ...
    
    # Check if we should use dual auth mode
    use_dual_auth = os.getenv("ATOMS_ENABLE_INTERNAL_AUTH", "false").lower() == "true"
    
    if use_dual_auth:
        # Use dual token verifier for internal + frontend auth
        from services.auth.dual_token_verifier import DualTokenVerifier
        auth_provider = DualTokenVerifier(supabase_client)
        logger.info("✅ Dual authentication enabled (internal + frontend tokens)")
    else:
        # Use OAuth (AuthKit) for public clients
        from fastmcp.server.auth.providers.workos import AuthKitProvider
        auth_provider = AuthKitProvider(
            authkit_domain=os.getenv("FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN"),
            base_url=base_url
        )
        logger.info("✅ OAuth authentication enabled (AuthKit)")
    
    # Create server with auth provider
    mcp = FastMCP(
        name="atoms-fastmcp-consolidated",
        auth=auth_provider,
        dependencies=[supabase_client]
    )
    
    return mcp
```

### Step 3: Environment Configuration

```bash
# .env (production)

# Enable dual authentication mode
ATOMS_ENABLE_INTERNAL_AUTH=true

# Internal service token secret (generate with: openssl rand -hex 32)
ATOMS_INTERNAL_AUTH_SECRET=your-secret-key-here

# Supabase JWT secret (from Supabase dashboard)
SUPABASE_JWT_SECRET=your-supabase-jwt-secret

# OAuth (AuthKit) - still needed for public clients
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN=https://decent-hymn-17-staging.authkit.app
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL=https://mcp.atoms.tech
```

---

## Usage

### Internal Service (agentApi/atomsAgent)

```typescript
// agentApi/atomsAgent MCP client configuration
const mcpClient = new MCPClient({
  serverUrl: "https://mcp.atoms.tech/api/mcp",
  auth: {
    type: "bearer",
    token: `atoms_internal_${process.env.ATOMS_INTERNAL_AUTH_SECRET}`
  }
});
```

### Frontend → agentApi → Atoms MCP

```typescript
// Frontend: Get Supabase session token
const { data: { session } } = await supabase.auth.getSession();
const token = session?.access_token;

// Pass to agentApi
const response = await fetch("/api/chat", {
  headers: {
    "Authorization": `Bearer ${token}`
  }
});

// agentApi: Forward to Atoms MCP
const mcpClient = new MCPClient({
  serverUrl: "https://mcp.atoms.tech/api/mcp",
  auth: {
    type: "bearer",
    token: userToken // Forward frontend token
  }
});
```

### Public Clients (unchanged)

```typescript
// Public clients still use OAuth
const mcpClient = new MCPClient({
  serverUrl: "https://mcp.atoms.tech/api/mcp",
  auth: {
    type: "oauth",
    // OAuth flow handled by AuthKit
  }
});
```

---

## Security Considerations

### Internal Token
- ✅ Long-lived, no expiration
- ✅ Shared secret between services
- ✅ Full admin access
- ⚠️ Must be kept secret (environment variables only)
- ⚠️ Rotate periodically

### Frontend Token
- ✅ Short-lived (Supabase session duration)
- ✅ User-specific permissions
- ✅ Automatic expiration
- ✅ Can be revoked by Supabase
- ⚠️ Must validate signature

### OAuth (Public)
- ✅ User-driven login
- ✅ Managed by AuthKit
- ✅ Secure redirect flow
- ✅ Token refresh handled by AuthKit

---

## Next Steps

1. ✅ Research FastMCP token verification
2. ⏳ Implement `DualTokenVerifier` class
3. ⏳ Update server configuration
4. ⏳ Add environment variables
5. ⏳ Test internal token auth
6. ⏳ Test frontend token forwarding
7. ⏳ Deploy to production
8. ⏳ Update agentApi/atomsAgent to use bearer auth

---

## Alternative: FastMCP Built-in Token Verification

FastMCP provides built-in token verification. We can use it directly:

```python
from fastmcp.server.auth.providers.jwt import JWTVerifier

# For Supabase JWT verification
verifier = JWTVerifier(
    public_key=os.getenv("SUPABASE_JWT_SECRET"),
    issuer="https://your-project.supabase.co/auth/v1",
    audience="authenticated",
    algorithm="HS256"  # Supabase uses HMAC
)

mcp = FastMCP(name="atoms-mcp", auth=verifier)
```

This is simpler but only handles Supabase JWTs. For internal tokens, we'd need custom logic.

---

## Recommendation

**Use Hybrid Approach**:
1. **Internal tokens**: Custom `StaticTokenVerifier` for service-to-service
2. **Frontend tokens**: FastMCP's `JWTVerifier` for Supabase JWTs
3. **Public clients**: Keep existing OAuth (AuthKit)

This provides maximum flexibility while leveraging FastMCP's built-in capabilities.

---

## Discovery: atomsAgent Already Supports Bearer Tokens!

The atomsAgent MCP client already has bearer token support built-in:

```python
# From atomsAgent/src/atomsAgent/mcp/database.py
if auth_type == "bearer":
    bearer_token = auth_config.get("bearerToken") or auth_config.get("apiKey")
    if bearer_token:
        headers["Authorization"] = f"Bearer {bearer_token}"
```

**This means we only need to**:
1. ✅ Add bearer token verification to Atoms MCP server
2. ✅ Configure atomsAgent to use bearer auth for Atoms MCP
3. ✅ No changes needed to atomsAgent code!

---

## Simplified Implementation

### Step 1: Add Bearer Token Support to Atoms MCP

Use FastMCP's built-in `StaticTokenVerifier` for internal tokens:

```python
# server.py
from fastmcp.server.auth.providers.jwt import StaticTokenVerifier

# Check if we should use bearer token auth
use_bearer_auth = os.getenv("ATOMS_ENABLE_BEARER_AUTH", "false").lower() == "true"

if use_bearer_auth:
    # Use static token verifier for internal service tokens
    internal_token = os.getenv("ATOMS_INTERNAL_TOKEN")

    verifier = StaticTokenVerifier(
        tokens={
            internal_token: {
                "client_id": "internal-service",
                "scopes": ["read:data", "write:data", "admin:users"]
            }
        },
        required_scopes=["read:data"]
    )

    mcp = FastMCP(name="atoms-mcp", auth=verifier)
    logger.info("✅ Bearer token authentication enabled")
else:
    # Use OAuth (AuthKit) for public clients
    from fastmcp.server.auth.providers.workos import AuthKitProvider
    auth_provider = AuthKitProvider(...)
    mcp = FastMCP(name="atoms-mcp", auth=auth_provider)
    logger.info("✅ OAuth authentication enabled")
```

### Step 2: Configure Environment Variables

```bash
# .env (for internal deployment)
ATOMS_ENABLE_BEARER_AUTH=true
ATOMS_INTERNAL_TOKEN=atoms_internal_$(openssl rand -hex 32)
```

### Step 3: Configure atomsAgent

Add Atoms MCP to atomsAgent's MCP server configuration:

```json
// atomsAgent MCP configuration
{
  "name": "atoms-mcp",
  "url": "https://mcp.atoms.tech/api/mcp",
  "auth_type": "bearer",
  "auth_config": {
    "bearerToken": "${ATOMS_INTERNAL_TOKEN}"
  }
}
```

**That's it!** No code changes needed to atomsAgent.

---

## For Frontend Token Forwarding

If you want to forward frontend Supabase tokens:

### Step 1: Add Supabase JWT Verification

```python
# server.py
from fastmcp.server.auth.providers.jwt import JWTVerifier

# For Supabase JWT verification
verifier = JWTVerifier(
    public_key=os.getenv("SUPABASE_JWT_SECRET"),
    issuer=f"https://{os.getenv('SUPABASE_PROJECT_ID')}.supabase.co/auth/v1",
    audience="authenticated",
    algorithm="HS256"  # Supabase uses HMAC
)

mcp = FastMCP(name="atoms-mcp", auth=verifier)
```

### Step 2: Frontend → agentApi → Atoms MCP

```typescript
// Frontend: Get Supabase session
const { data: { session } } = await supabase.auth.getSession();

// Pass to agentApi
const response = await fetch("/api/chat", {
  headers: {
    "Authorization": `Bearer ${session.access_token}`
  },
  body: JSON.stringify({ message: "Hello" })
});

// agentApi: Forward to Atoms MCP
const mcpClient = await loadMCPServer({
  name: "atoms-mcp",
  url: "https://mcp.atoms.tech/api/mcp",
  auth_type: "bearer",
  auth_config: {
    bearerToken: request.headers.get("Authorization")?.replace("Bearer ", "")
  }
});
```

---

## Final Recommendation

**For Internal Use (atomsAgent)**:
- Use `StaticTokenVerifier` with a shared secret token
- Simple, secure, no expiration issues
- Already supported by atomsAgent!

**For Frontend Token Forwarding**:
- Use `JWTVerifier` with Supabase JWT validation
- User-specific permissions
- Automatic expiration handling

**For Public Clients**:
- Keep existing OAuth (AuthKit)
- User-driven login flow
- Managed by WorkOS

This provides maximum flexibility with minimal code changes!

