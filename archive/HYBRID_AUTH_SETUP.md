# Hybrid Authentication Setup Guide

## Overview

Atoms MCP now supports **hybrid authentication**, allowing the same server instance to handle:

1. **OAuth (AuthKit)** - For public clients (Claude Desktop, etc.)
2. **Bearer Tokens** - For internal services (atomsAgent)
3. **Supabase JWTs** - For frontend token forwarding (optional)

## Architecture

```
Request arrives at Atoms MCP
  ↓
Check Authorization header
  ↓
  ├─ Has "Bearer <token>"?
  │   ↓
  │   ├─ Try internal token verification
  │   ├─ Try Supabase JWT verification
  │   └─ If both fail, reject
  │
  └─ No Bearer token?
      ↓
      Use OAuth (AuthKit) flow
```

## Setup Instructions

### Step 1: Generate Internal Token

```bash
# Generate a secure random token
openssl rand -hex 32

# Output example:
# a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2
```

### Step 2: Configure Environment Variables

Add to your `.env` file:

```bash
# OAuth (AuthKit) - Required
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN=https://decent-hymn-17-staging.authkit.app
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL=https://mcp.atoms.tech

# Internal Bearer Token - Optional (for atomsAgent)
ATOMS_INTERNAL_TOKEN=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2

# Supabase JWT - Optional (for frontend token forwarding)
SUPABASE_JWT_SECRET=your-supabase-jwt-secret
SUPABASE_PROJECT_ID=your-project-id
```

### Step 3: Deploy to Vercel

Add environment variables in Vercel dashboard:

1. Go to Project Settings → Environment Variables
2. Add:
   - `ATOMS_INTERNAL_TOKEN` = `<your-generated-token>`
   - `SUPABASE_JWT_SECRET` = `<from-supabase-dashboard>`
   - `SUPABASE_PROJECT_ID` = `<your-project-id>`

### Step 4: Configure atomsAgent

Add Atoms MCP to atomsAgent's MCP configuration:

```json
{
  "mcpServers": {
    "atoms-mcp": {
      "url": "https://mcp.atoms.tech/api/mcp",
      "auth_type": "bearer",
      "auth_config": {
        "bearerToken": "${ATOMS_INTERNAL_TOKEN}"
      }
    }
  }
}
```

Or in atomsAgent's database:

```sql
INSERT INTO mcp_servers (name, url, auth_type, auth_config)
VALUES (
  'atoms-mcp',
  'https://mcp.atoms.tech/api/mcp',
  'bearer',
  '{"bearerToken": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2"}'
);
```

## Usage Examples

### 1. Internal Service (atomsAgent)

```python
# atomsAgent automatically handles this
# Just configure the bearer token in MCP server config
```

### 2. Frontend Token Forwarding

```typescript
// Frontend: Get Supabase session
const { data: { session } } = await supabase.auth.getSession();

// Pass to backend
const response = await fetch("/api/chat", {
  headers: {
    "Authorization": `Bearer ${session.access_token}`
  }
});

// Backend (atomsAgent): Forward to Atoms MCP
const mcpClient = await loadMCPServer({
  name: "atoms-mcp",
  url: "https://mcp.atoms.tech/api/mcp",
  auth_type: "bearer",
  auth_config: {
    bearerToken: request.headers.get("Authorization")?.replace("Bearer ", "")
  }
});
```

### 3. Public Clients (Claude Desktop)

```json
{
  "mcpServers": {
    "atoms": {
      "url": "https://mcp.atoms.tech/api/mcp",
      "auth": {
        "type": "oauth"
      }
    }
  }
}
```

## Testing

### Test Internal Token

```bash
# Test with internal token
curl -H "Authorization: Bearer ${ATOMS_INTERNAL_TOKEN}" \
  https://mcp.atoms.tech/api/mcp

# Should return MCP protocol response
```

### Test Supabase JWT

```bash
# Get a Supabase JWT from your frontend
# Then test:
curl -H "Authorization: Bearer <supabase-jwt>" \
  https://mcp.atoms.tech/api/mcp
```

### Test OAuth

```bash
# Visit in browser (will redirect to AuthKit)
open https://mcp.atoms.tech/auth/start
```

## Security Considerations

### Internal Token
- ✅ Long-lived, no expiration
- ✅ Full admin access
- ⚠️ **Keep secret** - never commit to git
- ⚠️ Rotate periodically (every 90 days recommended)
- ⚠️ Use different tokens for dev/staging/prod

### Supabase JWT
- ✅ Short-lived (1 hour default)
- ✅ User-specific permissions
- ✅ Automatic expiration
- ✅ Can be revoked by Supabase

### OAuth (AuthKit)
- ✅ User-driven login
- ✅ Managed by WorkOS
- ✅ Secure redirect flow
- ✅ Token refresh handled automatically

## Troubleshooting

### "Bearer token provided but verification failed"

**Cause**: Token doesn't match internal token or isn't a valid Supabase JWT

**Solution**:
1. Check `ATOMS_INTERNAL_TOKEN` matches in both services
2. Verify `SUPABASE_JWT_SECRET` is correct
3. Check token hasn't expired (for Supabase JWTs)

### "OAuth authentication required"

**Cause**: No bearer token provided and OAuth flow not completed

**Solution**:
1. For internal services: Add `Authorization: Bearer <token>` header
2. For public clients: Complete OAuth flow in browser

### atomsAgent can't connect

**Cause**: Bearer token not configured or incorrect

**Solution**:
1. Check atomsAgent MCP config has `auth_type: "bearer"`
2. Verify `bearerToken` matches `ATOMS_INTERNAL_TOKEN`
3. Check atomsAgent logs for auth errors

## Next Steps

1. ✅ Generate internal token
2. ✅ Configure environment variables
3. ✅ Deploy to Vercel
4. ✅ Configure atomsAgent
5. ✅ Test all auth methods
6. ⏳ Monitor logs for auth issues
7. ⏳ Set up token rotation schedule

## Files Modified

- `services/auth/hybrid_auth_provider.py` - New hybrid auth provider
- `server.py` - Updated to use hybrid auth
- `.env.example` - Added new environment variables
- `HYBRID_AUTH_SETUP.md` - This guide

