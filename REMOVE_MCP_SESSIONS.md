# Remove mcp_sessions Table - Use AuthKit Session Management

## Problem

Current implementation tries to manage sessions in Supabase mcp_sessions table, which:
- ❌ Causes RLS violations
- ❌ Requires double JWT validation
- ❌ Adds unnecessary complexity
- ❌ Conflicts with AuthKit's session management

## Solution

**AuthKit already handles sessions via JWTs** - we should use those directly.

## Changes Needed

### 1. Set JWT Template in WorkOS Dashboard

**Location**: WorkOS Dashboard → Authentication → Sessions → JWT Template

**Template**:
```json
{
  "role": "authenticated",
  "user_role": "{{organization_membership.role}}"
}
```

This ensures the JWT has the `role: "authenticated"` claim for Supabase RLS.

### 2. Simplify Session Middleware

Remove mcp_sessions table lookups and just validate JWT claims directly.

**Current (broken)**:
```python
# Tries to create session in mcp_sessions
session_id = await session_manager.create_session(...)

# Tries to validate JWT with Supabase
user_response = supabase.auth.get_user(jwt_token)
```

**Should be**:
```python
# Just decode JWT and extract claims
decoded = jwt.decode(token, options={"verify_signature": False})
user_id = decoded['sub']

# Set in context for RLS
_request_session_context["user_id"] = user_id
_request_session_context["access_token"] = jwt_token
```

### 3. Remove Session Table Dependency

Since AuthKit manages sessions:
- Don't need SessionManager.create_session()
- Don't need SessionManager.get_session()
- Don't need mcp_sessions table at all

JWT expiration is managed by AuthKit/WorkOS.

## Code Changes

### auth/session_middleware.py

**Remove**:
- SessionManager initialization
- session_manager.create_session() calls
- session_manager.get_session() calls
- All mcp_sessions table references

**Keep**:
- JWT extraction from headers
- JWT decoding (without verification)
- Setting user context from JWT claims

### auth/persistent_authkit_provider.py

**Remove**:
- Session creation after OAuth complete
- mcp_sessions table INSERT

**Keep**:
- OAuth flow with WorkOS
- Return JWT to client
- Redirect to callback

## Benefits

✅ No RLS issues with mcp_sessions
✅ No double JWT validation
✅ Simpler code
✅ Faster auth flow
✅ Works with AuthKit's session lifecycle
✅ No manual session cleanup needed

## Migration Path

1. Set JWT template in WorkOS dashboard
2. Deploy simplified session middleware (remove mcp_sessions)
3. Drop mcp_sessions table (or keep for audit log)
4. Test auth flow - should work immediately

## Alternative: Keep mcp_sessions for State Only

If you need to store MCP-specific state (context, preferences, etc.):

**Keep table but make it optional**:
- Auth works without it (pure JWT)
- Create session row only if app state needs to be stored
- Use service_role to bypass RLS for session CRUD
- Don't use it for authentication validation

This gives you both: AuthKit session management + optional state storage.
