# Implementation Checklist for Atoms MCP Integration

## Summary

This checklist covers all changes needed to integrate Atoms MCP with atoms.tech frontend and atomsAgent backend, enabling seamless authentication without OAuth prompts for internal use.

---

## ✅ Atoms MCP Server (COMPLETE)

- [x] Add hybrid authentication provider
- [x] Support OAuth for public clients
- [x] Support bearer tokens for internal services
- [x] Support Supabase JWT validation
- [x] Deploy to production (mcp.atoms.tech)
- [x] Deploy to dev (mcpdev.atoms.tech) - if needed

**Files Modified**:
- `services/auth/hybrid_auth_provider.py` - New hybrid auth
- `server.py` - Use hybrid auth
- `.env.example` - Document env vars

---

## ⏳ Frontend (atoms.tech)

### 1. MCP Registry Configuration

**File**: `src/lib/mcp/registry.ts` (create if doesn't exist)

```typescript
export const FIRST_PARTY_MCPS = {
  "atoms": {
    name: "Atoms MCP",
    url: process.env.NEXT_PUBLIC_ATOMS_MCP_URL || "https://mcp.atoms.tech/api/mcp",
    scope: "system",
    auth: {
      type: "internal",
      requiresUserToken: true
    }
  },
  "atoms-dev": {
    name: "Atoms MCP (Dev)",
    url: process.env.NEXT_PUBLIC_ATOMS_MCP_DEV_URL || "https://mcpdev.atoms.tech/api/mcp",
    scope: "system",
    auth: {
      type: "internal",
      requiresUserToken: true
    }
  }
};
```

### 2. MCP Auth Helper

**File**: `src/lib/mcp/auth.ts` (create)

```typescript
import { createClient } from '@/lib/supabase/supabaseServer';

export async function getMCPAuthHeaders(mcpId: string): Promise<Record<string, string>> {
  const isInternalMCP = mcpId === 'atoms' || mcpId === 'atoms-dev';
  
  if (isInternalMCP) {
    const supabase = createClient();
    const { data: { session } } = await supabase.auth.getSession();
    
    if (session?.access_token) {
      return { 'Authorization': `Bearer ${session.access_token}` };
    }
  }
  
  return {};
}

export function mcpRequiresUserAuth(mcpId: string): boolean {
  return mcpId === 'atoms' || mcpId === 'atoms-dev';
}
```

### 3. Update Chat API Route

**File**: `src/app/api/chat/route.ts` (modify)

Add:
```typescript
import { getMCPAuthHeaders } from '@/lib/mcp/auth';

// In POST handler:
const authHeaders = await getMCPAuthHeaders(mcpId);

const response = await fetch(`${process.env.ATOMSAGENT_URL}/api/chat`, {
  headers: {
    'Content-Type': 'application/json',
    ...authHeaders  // Add this
  },
  // ... rest
});
```

### 4. Update MCP Selector Component

**File**: `src/components/chat/MCPSelector.tsx` (modify)

Add login check for internal MCPs:
```typescript
import { mcpRequiresUserAuth } from '@/lib/mcp/auth';

const handleMCPSelect = (mcpId: string) => {
  if (mcpRequiresUserAuth(mcpId) && !session) {
    toast.error('Please log in to use Atoms MCP');
    return;
  }
  setSelectedMCP(mcpId);
};
```

### 5. Environment Variables

**File**: `.env.local` (add)

```bash
NEXT_PUBLIC_ATOMS_MCP_URL=https://mcp.atoms.tech/api/mcp
NEXT_PUBLIC_ATOMS_MCP_DEV_URL=https://mcpdev.atoms.tech/api/mcp
ATOMSAGENT_URL=https://api.atoms.tech
```

---

## ⏳ Backend (atomsAgent/agentapi)

### 1. Update MCP Database Module

**File**: `src/atomsAgent/mcp/database.py` (modify)

Update `load_mcp_server` function:
```python
async def load_mcp_server(
    server: dict[str, Any],
    *,
    user_token: str | None = None  # NEW parameter
) -> MCPClient:
    # Check if internal MCP
    is_internal = server.get("is_internal", False)
    
    if is_internal and user_token:
        # Use user token for internal MCPs
        auth_type = "bearer"
        auth_config = {"bearerToken": user_token}
    else:
        # Use configured auth
        auth_type = server.get("auth_type")
        auth_config = server.get("auth_config", {})
    
    # ... rest of function
```

### 2. Update Chat Endpoint

**File**: `src/atomsAgent/api/chat.py` or similar (modify)

```python
from fastapi import Header
from typing import Optional

@router.post("/chat")
async def chat(
    request: Request,
    authorization: Optional[str] = Header(None)  # NEW
):
    body = await request.json()
    mcp_id = body.get("mcpId")
    
    # Extract user token
    user_token = None
    if authorization and authorization.startswith("Bearer "):
        user_token = authorization.replace("Bearer ", "").strip()
    
    # Load MCP with user token
    server_config = await get_mcp_server_config(mcp_id)
    mcp_client = await load_mcp_server(
        server_config,
        user_token=user_token  # Pass token
    )
    
    # ... rest
```

### 3. Update MCP Server Configuration

**File**: `config/mcp_servers.py` or database (modify)

```python
MCP_SERVERS = {
    "atoms": {
        "name": "atoms-mcp",
        "url": "https://mcp.atoms.tech/api/mcp",
        "is_internal": True,  # NEW flag
        "scope": "system",
        "auth_type": "bearer",
        "auth_config": {}
    },
    "atoms-dev": {
        "name": "atoms-mcp-dev",
        "url": "https://mcpdev.atoms.tech/api/mcp",
        "is_internal": True,  # NEW flag
        "scope": "system",
        "auth_type": "bearer",
        "auth_config": {}
    }
}
```

### 4. Database Migration (if using DB)

**File**: `migrations/add_is_internal_to_mcp_servers.sql` (create)

```sql
ALTER TABLE mcp_servers 
ADD COLUMN is_internal BOOLEAN DEFAULT FALSE;

UPDATE mcp_servers 
SET is_internal = TRUE 
WHERE name IN ('atoms-mcp', 'atoms-mcp-dev');

CREATE INDEX idx_mcp_servers_internal ON mcp_servers(is_internal);
```

### 5. Environment Variables

**File**: `.env` (add)

```bash
ATOMS_MCP_URL=https://mcp.atoms.tech/api/mcp
ATOMS_MCP_DEV_URL=https://mcpdev.atoms.tech/api/mcp
```

---

## Testing Checklist

### Unit Tests

- [ ] Frontend: `getMCPAuthHeaders` returns correct headers
- [ ] Frontend: `mcpRequiresUserAuth` identifies internal MCPs
- [ ] Backend: `load_mcp_server` forwards user token
- [ ] Backend: Chat endpoint extracts Authorization header

### Integration Tests

- [ ] Frontend → Backend: Auth header is passed
- [ ] Backend → Atoms MCP: User token is forwarded
- [ ] Atoms MCP: JWT is validated
- [ ] End-to-end: User can use Atoms MCP without OAuth

### Manual Tests

1. [ ] Login to atoms.tech
2. [ ] Open chat
3. [ ] Select "Atoms MCP"
4. [ ] Verify no OAuth prompt appears
5. [ ] Send message: "Show my workspaces"
6. [ ] Verify response is user-specific
7. [ ] Logout
8. [ ] Try to select "Atoms MCP"
9. [ ] Verify "Login Required" message appears

---

## Deployment Checklist

### Atoms MCP Server

- [x] Deploy to production (mcp.atoms.tech)
- [ ] Add `SUPABASE_JWT_SECRET` to Vercel env vars
- [ ] Add `SUPABASE_PROJECT_ID` to Vercel env vars
- [ ] Verify deployment health

### Frontend (atoms.tech)

- [ ] Commit changes
- [ ] Add environment variables to Vercel
- [ ] Deploy to preview
- [ ] Test preview deployment
- [ ] Deploy to production

### Backend (atomsAgent)

- [ ] Commit changes
- [ ] Run database migration (if needed)
- [ ] Deploy to staging
- [ ] Test staging deployment
- [ ] Deploy to production

---

## Rollback Plan

If issues occur:

1. **Frontend**: Remove auth header passing (falls back to no auth)
2. **Backend**: Remove user_token parameter (uses configured auth)
3. **Atoms MCP**: Hybrid auth falls back to OAuth for requests without bearer token

No breaking changes - system degrades gracefully!

---

## Documentation

- [x] `FRONTEND_BACKEND_INTEGRATION.md` - Complete integration guide
- [x] `HYBRID_AUTH_SETUP.md` - Atoms MCP setup
- [x] `IMPLEMENTATION_CHECKLIST.md` - This file

---

## Timeline Estimate

- **Frontend changes**: 2-3 hours
- **Backend changes**: 2-3 hours
- **Testing**: 2 hours
- **Deployment**: 1 hour
- **Total**: ~8 hours

---

## Support

If you encounter issues:

1. Check logs in Vercel (Atoms MCP)
2. Check logs in atomsAgent
3. Verify environment variables are set
4. Test with curl to isolate issues
5. Check JWT is valid with jwt.io

---

## Success Criteria

✅ User can use Atoms MCP without OAuth prompts
✅ User's Supabase session is used for authentication
✅ User sees personalized data from Atoms MCP
✅ System works for both production and dev environments
✅ Graceful degradation if user is not logged in

