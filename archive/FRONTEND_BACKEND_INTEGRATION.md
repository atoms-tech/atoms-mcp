# Frontend/Backend Integration for Atoms MCP Auth

## Overview

This guide shows how to integrate Atoms MCP with the frontend (atoms.tech) and backend (atomsAgent/agentapi) so that:

1. **Frontend** passes its Supabase auth token to backend
2. **Backend** forwards the token to Atoms MCP
3. **Atoms MCP** validates the token (no OAuth needed for internal use)
4. **User** never sees OAuth prompts for Atoms MCP

---

## Architecture

```
Frontend (atoms.tech)
  ↓ Supabase JWT in Authorization header
Backend (atomsAgent/agentapi)
  ↓ Forward JWT to Atoms MCP
Atoms MCP (mcp.atoms.tech)
  ↓ Validate JWT
  ✅ Authenticated!
```

---

## Part 1: MCP Registry Configuration

### Add Atoms MCP to First-Party Registry

Add both production and dev instances to the system-level MCP registry:

```typescript
// atoms.tech/src/lib/mcp/registry.ts (or similar)

export const FIRST_PARTY_MCPS = {
  "atoms": {
    name: "Atoms MCP",
    url: "https://mcp.atoms.tech/api/mcp",
    description: "Atoms workspace management and data operations",
    scope: "system", // System-level, always loaded
    auth: {
      type: "internal", // Special flag for internal auth
      requiresUserToken: true // Frontend must pass user token
    },
    capabilities: ["workspace", "entities", "relationships", "workflows", "queries"]
  },
  "atoms-dev": {
    name: "Atoms MCP (Dev)",
    url: "https://mcpdev.atoms.tech/api/mcp",
    description: "Atoms workspace management (development)",
    scope: "system",
    auth: {
      type: "internal",
      requiresUserToken: true
    },
    capabilities: ["workspace", "entities", "relationships", "workflows", "queries"]
  }
};
```

---

## Part 2: Frontend Changes (atoms.tech)

### Step 1: Create MCP Auth Helper

```typescript
// atoms.tech/src/lib/mcp/auth.ts

import { createClient } from '@/lib/supabase/supabaseServer';

/**
 * Get auth headers for MCP requests
 * For internal MCPs (like Atoms), pass Supabase JWT
 * For external MCPs, handle OAuth separately
 */
export async function getMCPAuthHeaders(mcpId: string): Promise<Record<string, string>> {
  const supabase = createClient();
  const { data: { session } } = await supabase.auth.getSession();
  
  // Check if this is an internal MCP that needs user token
  const isInternalMCP = mcpId === 'atoms' || mcpId === 'atoms-dev';
  
  if (isInternalMCP && session?.access_token) {
    return {
      'Authorization': `Bearer ${session.access_token}`
    };
  }
  
  return {};
}

/**
 * Check if MCP requires user authentication
 */
export function mcpRequiresUserAuth(mcpId: string): boolean {
  return mcpId === 'atoms' || mcpId === 'atoms-dev';
}
```

### Step 2: Update Chat/API Route to Pass Auth

```typescript
// atoms.tech/src/app/api/chat/route.ts

import { getMCPAuthHeaders } from '@/lib/mcp/auth';

export async function POST(request: Request) {
  const { message, mcpId } = await request.json();
  
  // Get auth headers for this MCP
  const authHeaders = await getMCPAuthHeaders(mcpId);
  
  // Forward to atomsAgent with auth headers
  const response = await fetch(`${process.env.ATOMSAGENT_URL}/api/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders // Pass auth headers
    },
    body: JSON.stringify({
      message,
      mcpId,
      // ... other params
    })
  });
  
  return response;
}
```

### Step 3: Update MCP Client Component

```typescript
// atoms.tech/src/components/chat/MCPSelector.tsx

import { mcpRequiresUserAuth } from '@/lib/mcp/auth';
import { useSession } from '@/hooks/useSession';

export function MCPSelector() {
  const { session } = useSession();
  
  const handleMCPSelect = (mcpId: string) => {
    // Check if MCP requires user auth
    if (mcpRequiresUserAuth(mcpId)) {
      if (!session) {
        // User must be logged in to use internal MCPs
        toast.error('Please log in to use Atoms MCP');
        return;
      }
      // No OAuth needed - token will be passed automatically
    } else {
      // External MCP - may need OAuth
      // Handle OAuth flow if needed
    }
    
    setSelectedMCP(mcpId);
  };
  
  return (
    <Select onValueChange={handleMCPSelect}>
      {Object.entries(FIRST_PARTY_MCPS).map(([id, mcp]) => (
        <SelectItem key={id} value={id}>
          {mcp.name}
          {mcpRequiresUserAuth(id) && !session && (
            <Badge variant="warning">Login Required</Badge>
          )}
        </SelectItem>
      ))}
    </Select>
  );
}
```

---

## Part 3: Backend Changes (atomsAgent/agentapi)

### Step 1: Update MCP Client to Forward Auth

```python
# atomsAgent/src/atomsAgent/mcp/database.py

async def load_mcp_server(
    server: dict[str, Any],
    *,
    user_token: str | None = None  # NEW: Accept user token from frontend
) -> MCPClient:
    """Load MCP server with authentication.
    
    Args:
        server: MCP server configuration
        user_token: User's auth token from frontend (for internal MCPs)
    """
    # Check if this is an internal MCP
    is_internal = server.get("is_internal", False) or server.get("name") in ["atoms-mcp", "atoms-mcp-dev"]
    
    # Add authentication
    auth_type = server.get("auth_type")
    auth_config = server.get("auth_config") or {}
    
    if is_internal and user_token:
        # Internal MCP: Use user token from frontend
        auth_type = "bearer"
        auth_config = {"bearerToken": user_token}
        logger.info(f"Using user token for internal MCP: {server.get('name')}")
    
    elif auth_type == "bearer":
        # External bearer token (from config)
        bearer_token = auth_config.get("bearerToken") or auth_config.get("apiKey")
        if bearer_token:
            headers["Authorization"] = f"Bearer {bearer_token}"
    
    # ... rest of the function
```

### Step 2: Update Chat Endpoint to Extract Token

```python
# atomsAgent/src/atomsAgent/api/chat.py (or similar)

from fastapi import Request, Header
from typing import Optional

@router.post("/chat")
async def chat(
    request: Request,
    authorization: Optional[str] = Header(None)
):
    """Handle chat request with MCP integration."""
    
    body = await request.json()
    message = body.get("message")
    mcp_id = body.get("mcpId")
    
    # Extract user token from Authorization header
    user_token = None
    if authorization and authorization.startswith("Bearer "):
        user_token = authorization.replace("Bearer ", "").strip()
    
    # Load MCP server configuration
    server_config = await get_mcp_server_config(mcp_id)
    
    # Load MCP client with user token
    mcp_client = await load_mcp_server(
        server_config,
        user_token=user_token  # Pass user token
    )
    
    # Use MCP client
    response = await mcp_client.call_tool("workspace_tool", {
        "operation": "get_context"
    })
    
    return {"response": response}
```

### Step 3: Update MCP Server Configuration

```python
# atomsAgent/config/mcp_servers.py

MCP_SERVERS = {
    "atoms": {
        "name": "atoms-mcp",
        "url": "https://mcp.atoms.tech/api/mcp",
        "is_internal": True,  # Mark as internal
        "scope": "system",
        "auth_type": "bearer",  # Will be set dynamically
        "auth_config": {}  # Will be populated with user token
    },
    "atoms-dev": {
        "name": "atoms-mcp-dev",
        "url": "https://mcpdev.atoms.tech/api/mcp",
        "is_internal": True,
        "scope": "system",
        "auth_type": "bearer",
        "auth_config": {}
    }
}
```

---

## Part 4: Database Schema (Optional)

If storing MCP configs in database:

```sql
-- Add is_internal flag to mcp_servers table
ALTER TABLE mcp_servers 
ADD COLUMN is_internal BOOLEAN DEFAULT FALSE;

-- Mark Atoms MCPs as internal
UPDATE mcp_servers 
SET is_internal = TRUE 
WHERE name IN ('atoms-mcp', 'atoms-mcp-dev');

-- Add index
CREATE INDEX idx_mcp_servers_internal ON mcp_servers(is_internal);
```

---

## Part 5: Environment Variables

### Frontend (.env)

```bash
# atoms.tech/.env
NEXT_PUBLIC_ATOMSAGENT_URL=https://api.atoms.tech
NEXT_PUBLIC_ATOMS_MCP_URL=https://mcp.atoms.tech
NEXT_PUBLIC_ATOMS_MCP_DEV_URL=https://mcpdev.atoms.tech
```

### Backend (.env)

```bash
# atomsAgent/.env
ATOMS_MCP_URL=https://mcp.atoms.tech/api/mcp
ATOMS_MCP_DEV_URL=https://mcpdev.atoms.tech/api/mcp

# No internal token needed - we forward user tokens!
```

---

## How It Works: Step-by-Step

### User Perspective

1. User logs into atoms.tech (Supabase auth)
2. User opens chat and selects "Atoms MCP"
3. **No OAuth prompt!** - Just works
4. User's requests go through atomsAgent to Atoms MCP
5. Atoms MCP validates user's Supabase JWT
6. User gets personalized responses based on their permissions

### Technical Flow

```
1. Frontend: User logged in
   → Supabase session exists
   → session.access_token available

2. Frontend: User sends chat message
   → getMCPAuthHeaders('atoms') called
   → Returns { Authorization: 'Bearer <supabase-jwt>' }

3. Frontend → Backend: POST /api/chat
   → Headers include Authorization: Bearer <supabase-jwt>
   → Body includes { message, mcpId: 'atoms' }

4. Backend: Receives request
   → Extracts user_token from Authorization header
   → Loads MCP config for 'atoms'
   → Sees is_internal = true
   → Creates MCP client with user_token

5. Backend → Atoms MCP: MCP protocol request
   → Headers include Authorization: Bearer <supabase-jwt>
   → Atoms MCP validates JWT against Supabase

6. Atoms MCP: Validates token
   → Checks JWT signature with SUPABASE_JWT_SECRET
   → Extracts user_id from JWT
   → Checks user permissions in Supabase
   → Executes tool with user context

7. Atoms MCP → Backend: Response
   → Returns tool result

8. Backend → Frontend: Response
   → Returns chat response

9. Frontend: Displays response
   → User sees result
```

---

## Key Points

### For Frontend Developers

✅ **DO**:
- Check if user is logged in before using Atoms MCP
- Pass Authorization header to backend
- Show "Login Required" badge for internal MCPs when not logged in

❌ **DON'T**:
- Show OAuth prompts for Atoms MCP
- Store MCP tokens separately
- Handle MCP auth differently from other API calls

### For Backend Developers

✅ **DO**:
- Extract Authorization header from requests
- Forward user token to internal MCPs
- Mark Atoms MCPs as `is_internal: true`

❌ **DON'T**:
- Use static bearer tokens for Atoms MCP
- Cache user tokens
- Share tokens between users

### For MCP Server (Already Done!)

✅ **Atoms MCP**:
- Validates Supabase JWTs
- Extracts user_id from token
- Enforces RLS policies
- Returns user-specific data

---

## Testing

### Test 1: Frontend Auth Flow

```typescript
// Test that auth headers are passed
const headers = await getMCPAuthHeaders('atoms');
console.log(headers); // Should include Authorization: Bearer <jwt>
```

### Test 2: Backend Token Forwarding

```python
# Test that user token is forwarded
user_token = "test-jwt-token"
mcp_client = await load_mcp_server(
    {"name": "atoms-mcp", "is_internal": True},
    user_token=user_token
)
# Check that mcp_client has Authorization header
```

### Test 3: End-to-End

```bash
# 1. Login to atoms.tech
# 2. Open chat
# 3. Select "Atoms MCP"
# 4. Send message: "Show my workspaces"
# 5. Should see your workspaces (no OAuth prompt!)
```

---

## Next Steps

1. ✅ Update frontend MCP registry
2. ✅ Add getMCPAuthHeaders helper
3. ✅ Update chat API route
4. ✅ Update backend MCP client
5. ✅ Update chat endpoint
6. ✅ Mark Atoms MCPs as internal
7. ✅ Test end-to-end
8. ✅ Deploy!

