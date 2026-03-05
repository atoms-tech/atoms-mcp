# Frontend Bearer Token Authentication

This guide explains how to pass AuthKit JWT tokens from authenticated frontend clients directly to the MCP server via HTTP Authorization headers.

## Overview

The Atoms MCP server leverages FastMCP's token verification capabilities to support multiple authentication methods:

1. **HTTP Authorization Header** (Bearer token) - For frontend clients
2. **FastMCP AuthKitProvider OAuth** - For MCP clients
3. **Claims dict fallback** - For backward compatibility

This implementation follows FastMCP's [Token Verification](https://gofastmcp.com/servers/auth/token-verification) pattern, treating the MCP server as a resource server that validates bearer tokens issued by AuthKit. Your frontend application authenticates users with AuthKit and passes the JWT token directly to the MCP server without requiring a separate OAuth flow.

### Token Verification Model

Following FastMCP's token verification model:

- **Token Issuance**: AuthKit handles user authentication and creates signed JWT tokens
- **Token Validation**: The MCP server validates tokens using AuthKit's public keys (via Supabase)
- **Access Control**: Based on token claims, the server enforces Row Level Security (RLS) and permissions

This separation allows the MCP server to focus on its core functionality while leveraging existing AuthKit authentication infrastructure.

## How It Works

The MCP server's `extract_bearer_token()` function checks for tokens in the following priority order:

1. **HTTP Authorization header** - Checks for `Authorization: Bearer <token>` header
2. **FastMCP OAuth context** - Uses FastMCP's built-in AuthKitProvider
3. **Claims dict** - Fallback for legacy token formats

When a frontend client includes an `Authorization: Bearer <token>` header in their HTTP request, the MCP server will automatically extract and validate the token.

## Frontend Integration

### JavaScript/TypeScript Example

```typescript
import { createClient } from '@supabase/supabase-js';
import { createClient as createAuthKitClient } from '@workos-inc/authkit-js';

// Initialize AuthKit client
const authkit = await createAuthKitClient('<WORKOS_CLIENT_ID>', {
  apiHostname: '<WORKOS_AUTH_DOMAIN>',
});

// Get the access token from AuthKit
const accessToken = await authkit.getAccessToken();

// Call MCP server with Bearer token
async function callMCPTool(toolName: string, params: any) {
  const response = await fetch('https://your-mcp-server.com/api/mcp', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${accessToken}`,
    },
    body: JSON.stringify({
      jsonrpc: '2.0',
      id: 1,
      method: 'tools/call',
      params: {
        name: toolName,
        arguments: params,
      },
    }),
  });

  return await response.json();
}

// Example: Create an entity
const result = await callMCPTool('entity_tool', {
  entity_type: 'project',
  operation: 'create',
  data: {
    name: 'My Project',
    description: 'A new project',
  },
});
```

### React Example with AuthKit

```typescript
import { useAuth } from '@workos-inc/authkit-react';

function MyComponent() {
  const { getAccessToken } = useAuth();

  const createProject = async (name: string, description: string) => {
    const accessToken = await getAccessToken();
    
    const response = await fetch('https://your-mcp-server.com/api/mcp', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`,
      },
      body: JSON.stringify({
        jsonrpc: '2.0',
        id: Date.now(),
        method: 'tools/call',
        params: {
          name: 'entity_tool',
          arguments: {
            entity_type: 'project',
            operation: 'create',
            data: { name, description },
          },
        },
      }),
    });

    const result = await response.json();
    return result.result;
  };

  return (
    <button onClick={() => createProject('New Project', 'Description')}>
      Create Project
    </button>
  );
}
```

### Python Example

```python
import httpx
import asyncio

async def call_mcp_tool(access_token: str, tool_name: str, params: dict):
    """Call MCP tool with Bearer token authentication."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            'https://your-mcp-server.com/api/mcp',
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {access_token}',
            },
            json={
                'jsonrpc': '2.0',
                'id': 1,
                'method': 'tools/call',
                'params': {
                    'name': tool_name,
                    'arguments': params,
                },
            },
        )
        return response.json()

# Example usage
async def main():
    # Get access token from your auth provider
    access_token = "your-authkit-jwt-token"
    
    result = await call_mcp_tool(
        access_token,
        'entity_tool',
        {
            'entity_type': 'project',
            'operation': 'create',
            'data': {
                'name': 'My Project',
                'description': 'A new project',
            },
        },
    )
    print(result)

asyncio.run(main())
```

## Token Validation

The MCP server validates the Bearer token using the same AuthKit configuration:

1. Token is extracted from the `Authorization` header
2. Token is validated against Supabase using the configured AuthKit settings
3. User context is established for Row Level Security (RLS)
4. Tool operations are executed with proper user permissions

## Security Considerations

### HTTPS Required

Always use HTTPS in production to protect tokens in transit:

```typescript
// ✅ Good - HTTPS
const MCP_ENDPOINT = 'https://mcp.atoms.tech/api/mcp';

// ❌ Bad - HTTP (only for local development)
const MCP_ENDPOINT = 'http://localhost:8000/api/mcp';
```

### Token Expiration

AuthKit tokens expire after a certain period. Handle token refresh in your frontend:

```typescript
import { useAuth } from '@workos-inc/authkit-react';

function useMCPClient() {
  const { getAccessToken } = useAuth();

  const callTool = async (toolName: string, params: any) => {
    // getAccessToken() automatically refreshes if needed
    const accessToken = await getAccessToken();
    
    const response = await fetch(MCP_ENDPOINT, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        jsonrpc: '2.0',
        id: Date.now(),
        method: 'tools/call',
        params: { name: toolName, arguments: params },
      }),
    });

    if (response.status === 401) {
      // Token expired or invalid - trigger re-authentication
      throw new Error('Authentication required');
    }

    return await response.json();
  };

  return { callTool };
}
```

### CORS Configuration

Ensure your MCP server allows requests from your frontend domain:

```python
# In your server configuration
from starlette.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=['https://your-frontend.com'],
    allow_credentials=True,
    allow_methods=['POST', 'GET'],
    allow_headers=['Authorization', 'Content-Type'],
)
```

## Debugging

Enable debug logging to see token extraction:

```python
# In your server logs, you'll see:
# DEBUG: Using Bearer token from Authorization header
# DEBUG: Token source: http.authorization.bearer
```

To verify token extraction in your frontend:

```typescript
const response = await fetch(MCP_ENDPOINT, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    jsonrpc: '2.0',
    id: 1,
    method: 'tools/call',
    params: {
      name: 'workspace_tool',
      arguments: { operation: 'get_context' },
    },
  }),
});

const result = await response.json();
console.log('User context:', result);
```

## Compatibility

This feature is fully compatible with:

- ✅ AuthKit JWT tokens
- ✅ Supabase authentication
- ✅ FastMCP OAuth flow (fallback)
- ✅ HTTP and HTTPS transports
- ✅ Vercel serverless deployment

Not compatible with:

- ❌ stdio transport (no HTTP headers available)
- ❌ Non-JWT token formats (unless configured in Supabase)

## Migration Guide

If you're currently using a different authentication method, here's how to migrate:

### From Session-Based Auth

```typescript
// Before: Session-based
const response = await fetch(MCP_ENDPOINT, {
  credentials: 'include', // Send cookies
  // ...
});

// After: Bearer token
const accessToken = await authkit.getAccessToken();
const response = await fetch(MCP_ENDPOINT, {
  headers: {
    'Authorization': `Bearer ${accessToken}`,
  },
  // ...
});
```

### From API Key Auth

```typescript
// Before: API key
const response = await fetch(MCP_ENDPOINT, {
  headers: {
    'X-API-Key': apiKey,
  },
  // ...
});

// After: Bearer token
const accessToken = await authkit.getAccessToken();
const response = await fetch(MCP_ENDPOINT, {
  headers: {
    'Authorization': `Bearer ${accessToken}`,
  },
  // ...
});
```

## FastMCP Token Verification Integration

The Atoms MCP server's bearer token support is built on top of FastMCP's token verification capabilities. While FastMCP provides several token verification providers (JWTVerifier, IntrospectionTokenVerifier, etc.), our implementation uses a hybrid approach:

### Hybrid Authentication Strategy

```python
# server/auth.py - Token extraction with priority
def extract_bearer_token() -> BearerToken | None:
    # 1. HTTP Authorization header (for frontend clients)
    # 2. FastMCP OAuth context (for MCP clients)
    # 3. Claims dict fallback (for compatibility)
```

This approach combines:

- **FastMCP's AuthKitProvider**: For MCP client OAuth flows
- **HTTP Bearer Token Extraction**: For frontend client direct authentication
- **Supabase Token Validation**: For JWT verification and RLS enforcement

### Why This Approach?

FastMCP's token verification providers are excellent for pure resource server scenarios. However, the Atoms MCP server needs to support both:

1. **MCP Clients**: Using FastMCP's OAuth flow with AuthKitProvider
2. **Frontend Clients**: Using direct bearer token authentication

Our implementation provides the best of both worlds:

- MCP clients get the full OAuth discovery and flow
- Frontend clients can pass tokens directly without OAuth complexity
- Both paths validate tokens against the same AuthKit/Supabase backend

### Alternative: Pure FastMCP Token Verification

If you only need to support frontend clients (no MCP client OAuth), you could use FastMCP's JWTVerifier directly:

```python
from fastmcp import FastMCP
from fastmcp.server.auth.providers.jwt import JWTVerifier

# Pure JWT verification approach
verifier = JWTVerifier(
    jwks_uri="https://your-authkit-domain/.well-known/jwks.json",
    issuer="https://your-authkit-domain",
    audience="your-mcp-server"
)

mcp = FastMCP(name="Frontend-Only MCP", auth=verifier)
```

However, this approach doesn't support MCP client OAuth flows. Our hybrid implementation supports both use cases.

## See Also

- [FastMCP Token Verification](https://gofastmcp.com/servers/auth/token-verification) - Official FastMCP documentation
- [AuthKit & FastMCP Integration](./AUTHKIT_FASTMCP.md) - OAuth flow setup
- [Supabase Authentication](../ARCHITECTURE.md#authentication) - Database-level security
- [MCP Server Configuration](../CONFIGURATION_GUIDE.md) - Server setup guide

