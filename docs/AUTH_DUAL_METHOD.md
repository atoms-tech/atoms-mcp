# Dual Authentication on Single FastMCP Server

## Overview

Your FastMCP server now supports **both Bearer tokens AND OAuth** on the **same endpoint** using `CompositeAuthProvider`.

```
POST /api/mcp (single endpoint)
├── Bearer Token (Internal Clients) → Direct JWT validation
└── OAuth (External Clients) → OAuth flow + JWT validation
```

## Use Cases

### Internal Clients (Bearer Tokens)
These clients have access to JWT tokens and don't need OAuth flow:
- **Frontend** (web app) - has JWT from login
- **Backend services** - has JWT from auth service
- **Atoms Agent** - has JWT from WorkOS User Management
- **Private integrations** - have pre-shared JWT

### External Clients (OAuth)
These clients need OAuth to obtain JWT:
- **Claude Desktop** - uses OAuth flow
- **Cursor IDE** - uses OAuth flow
- **VS Code extensions** - uses OAuth flow
- **Public integrations** - use OAuth to get JWT

## How It Works

### Flow Diagram

```
Request arrives
    ↓
Authorization: Bearer <JWT> header present?
    ├─ YES: Extract token
    │   └─ Validate via AuthKitProvider
    │       └─ Return AccessToken
    │
    └─ NO: Try OAuth flow
        ├─ Check for OAuth code/state
        │   └─ Exchange code for token
        │       └─ Return AccessToken
        └─ Not an OAuth flow
            └─ Reject (no auth)
```

### Code

```python
# server.py
from infrastructure.auth_composite import CompositeAuthProvider

auth_provider = CompositeAuthProvider(
    authkit_domain="https://your-app.authkit.app",
    client_id=WORKOS_CLIENT_ID,
    base_url="https://your-server.com"
)

mcp = FastMCP(name="Atoms MCP", auth=auth_provider)
```

## JWT Format (Same for Both Methods)

Whether obtained via Bearer or OAuth, JWTs have identical format:

```json
{
  "user_id": "user_79355ae7-3b97...",
  "email": "user@example.com",
  "role": "authenticated",
  "org_id": "org_ab9150ab-efad...",
  "email_verified": true
}
```

## Implications

### RLS (Row-Level Security)
Same JWT format means **RLS policies work identically**:
```sql
-- Same policy for Bearer and OAuth users
CREATE POLICY "Users see their org data"
ON entities
FOR SELECT
USING (organization_id = (
    SELECT organization_id FROM users 
    WHERE id = auth.uid()  -- Same for both
));
```

### Claims Extraction
In `tools/base.py`, both auth methods return identical claims:
```python
user_info = {
    "user_id": claims.get("user_id"),
    "email": claims.get("email"),
    "org_id": claims.get("org_id"),
    "role": claims.get("role")
}
```

## Testing

### Test Bearer Token (Internal)
```bash
curl -H "Authorization: Bearer eyJhbGc..." \
  http://localhost:8000/api/mcp/...
```

### Test OAuth (External)
1. Visit OAuth discovery endpoint: `http://localhost:8000/.well-known/oauth-protected-resource`
2. Follow OAuth flow to get JWT
3. Use JWT as Bearer token (same as internal)

## Environment Variables

```bash
# Server URL for OAuth callbacks
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL=https://your-server.com

# AuthKit domain
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN=https://your-app.authkit.app

# WorkOS Client ID
WORKOS_CLIENT_ID=sk_...
```

## Architecture

### CompositeAuthProvider

```
CompositeAuthProvider
├── Wraps FastMCP's AuthKitProvider
│   └── Handles OAuth flow, routes, metadata
│
├── Adds Bearer token support
│   └── Extracts & validates Bearer tokens
│
└── Exports all OAuth routes
    ├── /.well-known/oauth-protected-resource
    ├── /.well-known/oauth-authorization-server
    ├── /register (Dynamic Client Registration)
    └── /callback
```

### Key Methods

```python
class CompositeAuthProvider:
    async def authenticate(request):
        # 1. Try Bearer token
        # 2. Fall back to OAuth
        # 3. Return AccessToken
    
    def get_routes():
        # Return OAuth discovery routes
        # External clients use these
    
    def get_resource_metadata_url():
        # Return OAuth protected resource metadata
```

## Security

Both Bearer and OAuth use:
- ✅ Same JWT issuer (WorkOS AuthKit)
- ✅ Same signature verification
- ✅ Same expiration handling
- ✅ Same RLS enforcement
- ✅ Same Supabase access control

No difference in security posture between the two methods.

## Limitations

- **Only WorkOS AuthKit**: Both methods require AuthKit-compatible JWTs
- **Single issuer**: Can't mix multiple auth providers (e.g., Auth0 + AuthKit)
- **Same audience**: OAuth and Bearer must accept same token format

## Next Steps

1. **Test both methods** on development
2. **Enable OAuth clients** (IDEs, integrations)
3. **Monitor usage** to ensure Bearer and OAuth requests work identically
4. **Update documentation** for external client OAuth flow

## Related Files

- `infrastructure/auth_composite.py` - Composite provider implementation
- `server.py` - Server initialization
- `tools/base.py` - Claims extraction
- `supabase_client.py` - RLS token passing
