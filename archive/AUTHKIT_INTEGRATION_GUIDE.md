# AuthKit Integration Guide - Corrected Architecture

## Corrected Understanding

**Auth System**: WorkOS AuthKit (unified across all systems)
- Frontend (atoms.tech) → AuthKit JWT
- Backend (atomsAgent) → AuthKit JWT
- Atoms MCP → Validates AuthKit JWT
- Supabase → Database only, accepts AuthKit JWTs via RLS

## Architecture

```
User logs in via AuthKit
  ↓
Frontend gets AuthKit JWT
  ↓
Frontend → Backend (Authorization: Bearer <authkit-jwt>)
  ↓
Backend → Atoms MCP (Authorization: Bearer <authkit-jwt>)
  ↓
Atoms MCP validates JWT via AuthKit JWKS
  ↓
✅ Authenticated!
```

---

## Part 1: Atoms MCP Server (COMPLETE)

### What's Configured

```python
# Hybrid auth provider validates:
1. OAuth flow (for public clients like Claude Desktop)
2. Internal static token (for system services)
3. AuthKit JWTs (from frontend/backend) ← NEW
```

### Environment Variables Needed

```bash
# Vercel Environment Variables
WORKOS_CLIENT_ID=client_xxx
WORKOS_API_KEY=sk_xxx
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN=https://your-domain.authkit.app
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL=https://mcp.atoms.tech

# Optional: Internal token for system services
ATOMS_INTERNAL_TOKEN=<generate-with-openssl-rand-hex-32>
```

### How It Works

```python
# When request arrives with Authorization: Bearer <token>
1. Try internal static token → if matches, authenticate
2. Try AuthKit JWT → validate via JWKS endpoint
3. If no bearer token → use OAuth flow
```

---

## Part 2: Frontend (atoms.tech)

### Step 1: Get AuthKit Session Token

```typescript
// src/lib/auth/session.ts
import { getSession } from '@workos-inc/authkit-nextjs';

export async function getAuthKitToken(): Promise<string | null> {
  const session = await getSession();
  return session?.accessToken || null;
}
```

### Step 2: Create MCP Auth Helper

```typescript
// src/lib/mcp/auth.ts
import { getAuthKitToken } from '@/lib/auth/session';

export async function getMCPAuthHeaders(mcpId: string): Promise<Record<string, string>> {
  // Check if this is an internal MCP (Atoms)
  const isInternalMCP = mcpId === 'atoms' || mcpId === 'atoms-dev';
  
  if (isInternalMCP) {
    const token = await getAuthKitToken();
    
    if (token) {
      return {
        'Authorization': `Bearer ${token}`
      };
    }
  }
  
  return {};
}

export function mcpRequiresUserAuth(mcpId: string): boolean {
  return mcpId === 'atoms' || mcpId === 'atoms-dev';
}
```

### Step 3: Update Chat API Route

```typescript
// src/app/api/chat/route.ts
import { getMCPAuthHeaders } from '@/lib/mcp/auth';
import { NextRequest } from 'next/server';

export async function POST(request: NextRequest) {
  const { message, mcpId } = await request.json();
  
  // Get auth headers for this MCP
  const authHeaders = await getMCPAuthHeaders(mcpId);
  
  // Forward to atomsAgent with auth headers
  const response = await fetch(`${process.env.ATOMSAGENT_URL}/api/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders // Pass AuthKit JWT
    },
    body: JSON.stringify({
      message,
      mcpId
    })
  });
  
  return response;
}
```

### Step 4: MCP Registry

```typescript
// src/lib/mcp/registry.ts
export const FIRST_PARTY_MCPS = {
  "atoms": {
    name: "Atoms MCP",
    url: process.env.NEXT_PUBLIC_ATOMS_MCP_URL || "https://mcp.atoms.tech/api/mcp",
    description: "Atoms workspace management",
    scope: "system",
    auth: {
      type: "internal", // Uses AuthKit JWT, not OAuth
      requiresUserToken: true
    }
  },
  "atoms-dev": {
    name: "Atoms MCP (Dev)",
    url: process.env.NEXT_PUBLIC_ATOMS_MCP_DEV_URL || "https://mcpdev.atoms.tech/api/mcp",
    description: "Atoms workspace (dev)",
    scope: "system",
    auth: {
      type: "internal",
      requiresUserToken: true
    }
  }
};
```

---

## Part 3: Backend (atomsAgent)

### Step 1: Update MCP Client

```python
# src/atomsAgent/mcp/client.py (or database.py)

async def load_mcp_server(
    server: dict[str, Any],
    *,
    user_token: str | None = None  # AuthKit JWT from frontend
) -> MCPClient:
    """Load MCP server with authentication."""
    
    # Check if this is an internal MCP
    is_internal = server.get("is_internal", False)
    
    if is_internal and user_token:
        # Internal MCP: Use user's AuthKit JWT
        auth_type = "bearer"
        auth_config = {"bearerToken": user_token}
        logger.info(f"Using AuthKit JWT for internal MCP: {server.get('name')}")
    else:
        # Use configured auth
        auth_type = server.get("auth_type")
        auth_config = server.get("auth_config", {})
    
    # Create MCP client with auth
    # ... rest of implementation
```

### Step 2: Update Chat Endpoint

```python
# src/atomsAgent/api/routes/chat.py

from fastapi import APIRouter, Request, Header
from typing import Optional

router = APIRouter()

@router.post("/chat")
async def chat(
    request: Request,
    authorization: Optional[str] = Header(None)
):
    """Handle chat with MCP integration."""
    
    body = await request.json()
    message = body.get("message")
    mcp_id = body.get("mcpId")
    
    # Extract AuthKit JWT from Authorization header
    user_token = None
    if authorization and authorization.startswith("Bearer "):
        user_token = authorization.replace("Bearer ", "").strip()
        logger.info(f"Received AuthKit JWT for MCP: {mcp_id}")
    
    # Load MCP server
    server_config = await get_mcp_server_config(mcp_id)
    mcp_client = await load_mcp_server(
        server_config,
        user_token=user_token  # Pass AuthKit JWT
    )
    
    # Use MCP
    response = await mcp_client.call_tool("workspace_tool", {
        "operation": "get_context"
    })
    
    return {"response": response}
```

### Step 3: MCP Configuration

```python
# config/mcp_servers.py

MCP_SERVERS = {
    "atoms": {
        "name": "atoms-mcp",
        "url": os.getenv("ATOMS_MCP_URL", "https://mcp.atoms.tech/api/mcp"),
        "is_internal": True,  # Mark as internal
        "scope": "system",
        "auth_type": "bearer",  # Will be set dynamically
        "auth_config": {}  # Will be populated with user token
    },
    "atoms-dev": {
        "name": "atoms-mcp-dev",
        "url": os.getenv("ATOMS_MCP_DEV_URL", "https://mcpdev.atoms.tech/api/mcp"),
        "is_internal": True,
        "scope": "system",
        "auth_type": "bearer",
        "auth_config": {}
    }
}
```

---

## Complete Flow

```
1. User logs in via AuthKit
   → Frontend gets AuthKit JWT (accessToken)

2. User sends chat message
   → Frontend: getMCPAuthHeaders('atoms')
   → Returns { Authorization: 'Bearer <authkit-jwt>' }

3. Frontend → Backend: POST /api/chat
   → Headers: Authorization: Bearer <authkit-jwt>
   → Body: { message, mcpId: 'atoms' }

4. Backend extracts token
   → user_token = request.headers.get("Authorization")
   → Loads MCP with user_token

5. Backend → Atoms MCP: MCP request
   → Headers: Authorization: Bearer <authkit-jwt>

6. Atoms MCP validates JWT
   → Fetches JWKS from AuthKit
   → Validates signature
   → Extracts user_id (sub claim)
   → ✅ Authenticated!

7. Atoms MCP → Backend → Frontend
   → Returns user-specific data
```

---

## Key Differences from Supabase JWT

| Aspect | Supabase JWT | AuthKit JWT |
|--------|--------------|-------------|
| **Issuer** | Supabase | WorkOS AuthKit |
| **Validation** | HMAC with secret | RSA with JWKS |
| **Audience** | `authenticated` | Client ID |
| **Claims** | `sub`, `email`, `role` | `sub`, `email`, `org_id` |
| **Expiration** | 1 hour | Configurable |

---

## Testing

### Test AuthKit JWT Flow

```bash
# 1. Get AuthKit JWT from frontend
# (Login to atoms.tech, check browser devtools → Application → Cookies)

# 2. Test Atoms MCP directly
curl -H "Authorization: Bearer <authkit-jwt>" \
  https://mcp.atoms.tech/api/mcp

# Should return MCP protocol response
```

---

## Next Steps

1. ✅ Add `WORKOS_CLIENT_ID` to Vercel
2. ✅ Deploy Atoms MCP
3. ⏳ Implement frontend changes
4. ⏳ Implement backend changes
5. ⏳ Test end-to-end

