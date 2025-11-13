# Frontend Implementation Guide (atoms.tech)

## Location
`/Users/kooshapari/temp-PRODVERCEL/485/clean/atoms.tech`

## Files to Create

### 1. Create `src/lib/mcp/auth.ts`

```typescript
/**
 * MCP Authentication Helper
 * Handles auth for internal MCPs (Atoms) using AuthKit JWT
 */

import { getSession } from '@workos-inc/authkit-nextjs';

/**
 * Get authentication headers for MCP requests
 * For internal MCPs (Atoms), returns AuthKit JWT
 * For external MCPs, returns empty (they handle their own auth)
 */
export async function getMCPAuthHeaders(mcpId: string): Promise<Record<string, string>> {
  // Check if this is an internal MCP that needs user token
  const isInternalMCP = mcpId === 'atoms' || mcpId === 'atoms-dev';
  
  if (isInternalMCP) {
    try {
      const session = await getSession();
      
      if (session?.accessToken) {
        return {
          'Authorization': `Bearer ${session.accessToken}`
        };
      }
    } catch (error) {
      console.error('Failed to get AuthKit session:', error);
    }
  }
  
  return {};
}

/**
 * Check if MCP requires user authentication
 */
export function mcpRequiresUserAuth(mcpId: string): boolean {
  return mcpId === 'atoms' || mcpId === 'atoms-dev';
}

/**
 * Check if user is authenticated
 */
export async function isUserAuthenticated(): Promise<boolean> {
  try {
    const session = await getSession();
    return !!session?.accessToken;
  } catch {
    return false;
  }
}
```

---

### 2. Create `src/lib/mcp/registry.ts`

```typescript
/**
 * First-party MCP Registry
 * Defines system-level MCPs that are always available
 */

export interface MCPConfig {
  name: string;
  url: string;
  description: string;
  scope: 'system' | 'user' | 'organization';
  auth: {
    type: 'internal' | 'oauth' | 'none';
    requiresUserToken?: boolean;
  };
  capabilities?: string[];
}

export const FIRST_PARTY_MCPS: Record<string, MCPConfig> = {
  "atoms": {
    name: "Atoms MCP",
    url: process.env.NEXT_PUBLIC_ATOMS_MCP_URL || "https://mcp.atoms.tech/api/mcp",
    description: "Atoms workspace management and data operations",
    scope: "system",
    auth: {
      type: "internal", // Uses AuthKit JWT, not OAuth
      requiresUserToken: true
    },
    capabilities: ["workspace", "entities", "relationships", "workflows", "queries"]
  },
  "atoms-dev": {
    name: "Atoms MCP (Dev)",
    url: process.env.NEXT_PUBLIC_ATOMS_MCP_DEV_URL || "https://mcpdev.atoms.tech/api/mcp",
    description: "Atoms workspace management (development)",
    scope: "system",
    auth: {
      type: "internal",
      requiresUserToken: true
    },
    capabilities: ["workspace", "entities", "relationships", "workflows", "queries"]
  }
};

/**
 * Get MCP configuration by ID
 */
export function getMCPConfig(mcpId: string): MCPConfig | undefined {
  return FIRST_PARTY_MCPS[mcpId];
}

/**
 * Get all system-level MCPs
 */
export function getSystemMCPs(): MCPConfig[] {
  return Object.values(FIRST_PARTY_MCPS).filter(mcp => mcp.scope === 'system');
}
```

---

## Files to Modify

### 3. Update `src/app/api/chat/route.ts` (or similar)

Find your chat API route and update it:

```typescript
import { NextRequest, NextResponse } from 'next/server';
import { getMCPAuthHeaders } from '@/lib/mcp/auth';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { message, mcpId, ...rest } = body;
    
    // Get auth headers for this MCP
    const authHeaders = await getMCPAuthHeaders(mcpId);
    
    // Forward to atomsAgent with auth headers
    const response = await fetch(`${process.env.ATOMSAGENT_URL}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...authHeaders  // ADD THIS - passes AuthKit JWT
      },
      body: JSON.stringify({
        message,
        mcpId,
        ...rest
      })
    });
    
    if (!response.ok) {
      throw new Error(`atomsAgent returned ${response.status}`);
    }
    
    const data = await response.json();
    return NextResponse.json(data);
    
  } catch (error) {
    console.error('Chat API error:', error);
    return NextResponse.json(
      { error: 'Failed to process chat request' },
      { status: 500 }
    );
  }
}
```

---

### 4. Update MCP Selector Component (optional but recommended)

If you have a component that lets users select MCPs, update it to show login requirement:

```typescript
import { mcpRequiresUserAuth, isUserAuthenticated } from '@/lib/mcp/auth';
import { FIRST_PARTY_MCPS } from '@/lib/mcp/registry';
import { useEffect, useState } from 'react';

export function MCPSelector() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  
  useEffect(() => {
    isUserAuthenticated().then(setIsAuthenticated);
  }, []);
  
  const handleMCPSelect = async (mcpId: string) => {
    // Check if MCP requires user auth
    if (mcpRequiresUserAuth(mcpId)) {
      const authenticated = await isUserAuthenticated();
      
      if (!authenticated) {
        // Show login prompt or redirect to login
        alert('Please log in to use Atoms MCP');
        // Or: router.push('/login');
        return;
      }
    }
    
    // Proceed with MCP selection
    setSelectedMCP(mcpId);
  };
  
  return (
    <div>
      {Object.entries(FIRST_PARTY_MCPS).map(([id, mcp]) => (
        <button
          key={id}
          onClick={() => handleMCPSelect(id)}
          disabled={mcpRequiresUserAuth(id) && !isAuthenticated}
        >
          {mcp.name}
          {mcpRequiresUserAuth(id) && !isAuthenticated && (
            <span className="text-yellow-500"> (Login Required)</span>
          )}
        </button>
      ))}
    </div>
  );
}
```

---

### 5. Add Environment Variables

Create or update `.env.local`:

```bash
# Atoms MCP URLs
NEXT_PUBLIC_ATOMS_MCP_URL=https://mcp.atoms.tech/api/mcp
NEXT_PUBLIC_ATOMS_MCP_DEV_URL=https://mcpdev.atoms.tech/api/mcp

# atomsAgent API URL
ATOMSAGENT_URL=https://api.atoms.tech

# Or for local development:
# ATOMSAGENT_URL=http://localhost:8000
```

---

## Step-by-Step Implementation

### Step 1: Create auth helper

```bash
cd /Users/kooshapari/temp-PRODVERCEL/485/clean/atoms.tech
mkdir -p src/lib/mcp
touch src/lib/mcp/auth.ts
# Copy the code from section 1 above
```

### Step 2: Create registry

```bash
touch src/lib/mcp/registry.ts
# Copy the code from section 2 above
```

### Step 3: Update chat API route

```bash
# Find your chat route
find src/app -name "route.ts" -path "*/chat/*"

# Edit it and add the getMCPAuthHeaders call
```

### Step 4: Add environment variables

```bash
echo "NEXT_PUBLIC_ATOMS_MCP_URL=https://mcp.atoms.tech/api/mcp" >> .env.local
echo "NEXT_PUBLIC_ATOMS_MCP_DEV_URL=https://mcpdev.atoms.tech/api/mcp" >> .env.local
echo "ATOMSAGENT_URL=https://api.atoms.tech" >> .env.local
```

### Step 5: Test locally

```bash
npm run dev

# Test in browser:
# 1. Login to atoms.tech
# 2. Open chat
# 3. Select "Atoms MCP"
# 4. Send a message
# 5. Check browser devtools → Network → chat request → Headers
#    Should see: Authorization: Bearer <authkit-jwt>
```

---

## Verification Checklist

- [ ] `src/lib/mcp/auth.ts` created
- [ ] `src/lib/mcp/registry.ts` created
- [ ] Chat API route updated to call `getMCPAuthHeaders`
- [ ] Environment variables added
- [ ] Local testing shows Authorization header in requests
- [ ] Atoms MCP works without OAuth prompts
- [ ] User sees login requirement when not authenticated

---

## Testing

### Test 1: Check auth headers

```typescript
// In browser console after login:
const headers = await getMCPAuthHeaders('atoms');
console.log(headers);
// Should show: { Authorization: 'Bearer eyJ...' }
```

### Test 2: End-to-end

1. Login to atoms.tech
2. Open chat
3. Select "Atoms MCP"
4. Send message: "Show my workspaces"
5. Should work without OAuth prompt
6. Check Network tab for Authorization header

---

## Next: Deploy

After testing locally, deploy to Vercel:

```bash
vercel --prod
```

Add environment variables in Vercel dashboard.

