# Authentication Methods Comparison

This guide compares different authentication approaches for the Atoms MCP server and helps you choose the right method for your use case.

## Quick Decision Matrix

| Use Case | Recommended Approach | Why |
|----------|---------------------|-----|
| **Frontend + MCP clients** | Hybrid (current implementation) | Supports both client types |
| **Frontend only** | FastMCP JWTVerifier | Simpler, pure token verification |
| **MCP clients only** | FastMCP AuthKitProvider | Full OAuth discovery |
| **Internal microservices** | FastMCP JWTVerifier (HMAC) | Symmetric keys, simpler setup |
| **Development/Testing** | StaticTokenVerifier | No infrastructure needed |

## Authentication Approaches

### 1. Hybrid Authentication (Current Implementation)

**What it is**: Combines FastMCP's AuthKitProvider OAuth with HTTP bearer token extraction.

**Architecture**:
```python
# server/auth.py
def extract_bearer_token() -> BearerToken | None:
    # 1. Check HTTP Authorization header (frontend clients)
    # 2. Check FastMCP OAuth context (MCP clients)
    # 3. Fallback to claims dict
```

**Pros**:
- ✅ Supports both MCP clients and frontend clients
- ✅ Single codebase for all client types
- ✅ Unified token validation via Supabase
- ✅ Consistent RLS enforcement
- ✅ Backward compatible

**Cons**:
- ❌ More complex than single-method approaches
- ❌ Requires understanding of both OAuth and bearer tokens

**Best for**:
- Applications with both MCP clients (AI assistants) and frontend clients (web/mobile apps)
- Gradual migration from MCP-only to frontend integration
- Maximum flexibility in client types

**Example**:
```typescript
// Frontend client
const response = await fetch('/api/mcp', {
  headers: { 'Authorization': `Bearer ${authkitToken}` }
});

// MCP client (Python)
async with Client("https://mcp-server.com", auth="oauth") as client:
    result = await client.call_tool("entity_tool", {...})
```

---

### 2. FastMCP JWTVerifier (Pure Token Verification)

**What it is**: FastMCP's built-in JWT verification provider for resource server scenarios.

**Architecture**:
```python
from fastmcp import FastMCP
from fastmcp.server.auth.providers.jwt import JWTVerifier

verifier = JWTVerifier(
    jwks_uri="https://auth.company.com/.well-known/jwks.json",
    issuer="https://auth.company.com",
    audience="mcp-server"
)

mcp = FastMCP(name="API", auth=verifier)
```

**Pros**:
- ✅ Simple, focused on token verification
- ✅ Automatic key rotation via JWKS
- ✅ Industry-standard JWT validation
- ✅ No OAuth complexity
- ✅ Works with any JWT issuer

**Cons**:
- ❌ No OAuth discovery for MCP clients
- ❌ Clients must obtain tokens separately
- ❌ No built-in token refresh

**Best for**:
- Frontend-only applications
- Microservices architectures
- Integration with existing JWT infrastructure
- When you control token distribution

**Variants**:

#### Asymmetric Keys (RSA/ECDSA)
```python
# JWKS endpoint (recommended for production)
verifier = JWTVerifier(
    jwks_uri="https://auth.company.com/.well-known/jwks.json",
    issuer="https://auth.company.com",
    audience="mcp-server"
)

# Static public key (development)
verifier = JWTVerifier(
    public_key="-----BEGIN PUBLIC KEY-----\n...",
    issuer="https://auth.company.com",
    audience="mcp-server"
)
```

#### Symmetric Keys (HMAC)
```python
# Shared secret (internal microservices)
verifier = JWTVerifier(
    public_key="your-shared-secret-minimum-32-chars",
    issuer="internal-service",
    audience="mcp-server",
    algorithm="HS256"  # or HS384, HS512
)
```

---

### 3. FastMCP AuthKitProvider (OAuth Flow)

**What it is**: FastMCP's OAuth provider specifically for WorkOS AuthKit.

**Architecture**:
```python
from fastmcp import FastMCP
from fastmcp.server.auth.providers.authkit import AuthKitProvider

auth = AuthKitProvider(
    authkit_domain="https://your-project.authkit.app",
    base_url="https://your-mcp-server.com",
    required_scopes=["read", "write"]
)

mcp = FastMCP(name="MCP Server", auth=auth)
```

**Pros**:
- ✅ Full OAuth 2.0 discovery
- ✅ Built-in token refresh
- ✅ MCP client compatibility
- ✅ AuthKit-specific optimizations

**Cons**:
- ❌ Requires OAuth flow for all clients
- ❌ Frontend clients need OAuth redirect handling
- ❌ More complex for simple token passing

**Best for**:
- MCP client-only applications
- When you want full OAuth compliance
- AuthKit-native integrations

---

### 4. FastMCP IntrospectionTokenVerifier (Opaque Tokens)

**What it is**: Validates opaque tokens via OAuth 2.0 Token Introspection (RFC 7662).

**Architecture**:
```python
from fastmcp.server.auth.providers.introspection import IntrospectionTokenVerifier

verifier = IntrospectionTokenVerifier(
    introspection_url="https://auth.company.com/oauth/introspect",
    client_id="mcp-resource-server",
    client_secret="your-client-secret",
    required_scopes=["api:read", "api:write"]
)

mcp = FastMCP(name="API", auth=verifier)
```

**Pros**:
- ✅ Immediate token revocation
- ✅ Server-side token state
- ✅ Complex authorization logic
- ✅ Detailed audit logs

**Cons**:
- ❌ Network call per validation (latency)
- ❌ Requires introspection endpoint
- ❌ More complex infrastructure

**Best for**:
- Enterprise OAuth providers
- When immediate revocation is critical
- Sensitive operations requiring audit trails

---

### 5. StaticTokenVerifier (Development/Testing)

**What it is**: Accepts predefined tokens with associated claims for development.

**Architecture**:
```python
from fastmcp.server.auth.providers.jwt import StaticTokenVerifier

verifier = StaticTokenVerifier(
    tokens={
        "dev-alice-token": {
            "client_id": "alice@company.com",
            "scopes": ["read", "write", "admin"]
        },
        "dev-guest-token": {
            "client_id": "guest",
            "scopes": ["read"]
        }
    }
)

mcp = FastMCP(name="Dev Server", auth=verifier)
```

**Pros**:
- ✅ Zero infrastructure needed
- ✅ Instant setup
- ✅ Perfect for testing
- ✅ Predictable tokens

**Cons**:
- ❌ **NEVER use in production**
- ❌ Tokens stored as plain text
- ❌ No real security

**Best for**:
- Local development
- Automated testing
- Demos and prototypes

---

## Migration Paths

### From MCP-Only to Hybrid

If you currently use AuthKitProvider and want to add frontend support:

```python
# Before: MCP clients only
from fastmcp.server.auth.providers.authkit import AuthKitProvider

auth = AuthKitProvider(...)
mcp = FastMCP(name="MCP Server", auth=auth)

# After: MCP + Frontend clients
# Use the hybrid approach in server/auth.py
# Frontend clients can now pass Bearer tokens
# MCP clients continue using OAuth
```

### From Frontend-Only to Hybrid

If you currently use JWTVerifier and want to add MCP client support:

```python
# Before: Frontend only
from fastmcp.server.auth.providers.jwt import JWTVerifier

verifier = JWTVerifier(...)
mcp = FastMCP(name="API", auth=verifier)

# After: Frontend + MCP clients
# Implement hybrid approach
# Add AuthKitProvider for MCP clients
# Keep bearer token support for frontend
```

## Comparison Table

| Feature | Hybrid | JWTVerifier | AuthKitProvider | Introspection | Static |
|---------|--------|-------------|-----------------|---------------|--------|
| **Frontend Clients** | ✅ | ✅ | ⚠️ (OAuth) | ✅ | ✅ |
| **MCP Clients** | ✅ | ❌ | ✅ | ❌ | ✅ |
| **OAuth Discovery** | ✅ | ❌ | ✅ | ❌ | ❌ |
| **Bearer Tokens** | ✅ | ✅ | ⚠️ | ✅ | ✅ |
| **Token Refresh** | ✅ | ❌ | ✅ | ❌ | N/A |
| **Immediate Revocation** | ❌ | ❌ | ❌ | ✅ | N/A |
| **Setup Complexity** | Medium | Low | Medium | High | Very Low |
| **Production Ready** | ✅ | ✅ | ✅ | ✅ | ❌ |

## Recommendations by Scenario

### Scenario 1: New Project with Frontend + AI Features

**Recommendation**: Hybrid Authentication

You'll likely have both a web/mobile frontend and AI assistant integrations. The hybrid approach supports both from day one.

### Scenario 2: Microservices Architecture

**Recommendation**: JWTVerifier with HMAC

Internal services can share a symmetric key for fast, simple authentication without external dependencies.

### Scenario 3: Enterprise with Existing OAuth

**Recommendation**: JWTVerifier or IntrospectionTokenVerifier

Integrate with your existing OAuth infrastructure. Use JWTVerifier for JWTs or IntrospectionTokenVerifier for opaque tokens.

### Scenario 4: AI Assistant Only

**Recommendation**: AuthKitProvider

If you only have MCP clients (no frontend), use the pure OAuth approach for full compliance and token refresh.

### Scenario 5: Rapid Prototyping

**Recommendation**: StaticTokenVerifier

Get started immediately without any auth infrastructure. Migrate to a production approach later.

## See Also

- [Frontend Bearer Token Guide](./FRONTEND_BEARER_TOKEN.md) - Hybrid implementation details
- [FastMCP Token Verification](https://gofastmcp.com/servers/auth/token-verification) - Official documentation
- [AuthKit & FastMCP Integration](./AUTHKIT_FASTMCP.md) - OAuth setup
- [Bearer Token Feature Summary](../../BEARER_TOKEN_FEATURE_SUMMARY.md) - Implementation overview

