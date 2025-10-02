# Session-Based Authentication for Stateless MCP Deployment

This document explains how OAuth sessions are persisted in Supabase for stateless serverless deployments.

## Overview

The MCP server uses Supabase-backed session persistence to enable OAuth authentication in serverless environments like Vercel, where traditional in-memory sessions don't work.

## How It Works

### 1. OAuth Flow & Session Creation

When a user completes OAuth authentication via `/auth/complete`:

```
User authenticates → WorkOS OAuth → Session created in mcp_sessions table
```

The response includes a `session_id`:

```json
{
  "success": true,
  "session_id": "uuid-here",
  "redirect_uri": "..."
}
```

### 2. Using Sessions in MCP Requests

Clients must include the session_id in subsequent MCP requests using **one of these methods**:

#### Option A: Custom Header (Recommended)
```
X-MCP-Session-ID: <session_id>
```

#### Option B: Cookie
```
Cookie: mcp_session_id=<session_id>
```

#### Option C: Authorization Header (if session_id is UUID format)
```
Authorization: Bearer <session_id>
```

### 3. Session Lifecycle

```
┌─────────────────────────────────────────────────┐
│ 1. OAuth completes                              │
│    → session_id created in mcp_sessions         │
│    → expires_at = now() + 24 hours              │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│ 2. Client makes MCP request with session_id     │
│    → Middleware loads OAuth data from Supabase  │
│    → Tools execute with user's auth token       │
│    → Session expires_at extended on activity    │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│ 3. Session expires after TTL (default 24h)      │
│    → Automatic cleanup on next access           │
│    → Client must re-authenticate                │
└─────────────────────────────────────────────────┘
```

## Database Schema

The `mcp_sessions` table stores:

```sql
CREATE TABLE mcp_sessions (
  session_id TEXT PRIMARY KEY,        -- Unique session identifier
  user_id UUID NOT NULL,              -- Supabase user ID
  oauth_data JSONB NOT NULL,          -- Access tokens, user info
  mcp_state JSONB DEFAULT '{}',       -- MCP connection state
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  expires_at TIMESTAMPTZ NOT NULL     -- Auto-cleanup after this
);
```

## Configuration

Environment variables:

```bash
# Required for Supabase connection
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...

# Optional: Service role key for session management (bypasses RLS)
SUPABASE_SERVICE_ROLE_KEY=eyJ...

# Optional: Session TTL in hours (default: 24)
MCP_SESSION_TTL_HOURS=24
```

## Security Considerations

### Row Level Security (RLS)

If you enable RLS on `mcp_sessions`, add these policies:

```sql
-- Allow users to manage their own sessions
CREATE POLICY "Users can manage own sessions"
  ON mcp_sessions
  FOR ALL
  TO authenticated
  USING (user_id = auth.uid());

-- Allow service role full access
CREATE POLICY "Service role has full access"
  ON mcp_sessions
  FOR ALL
  TO service_role
  USING (true);
```

### Session Security Best Practices

1. **HTTPS Only**: Always use HTTPS in production
2. **HttpOnly Cookies**: Cookies are set with `httponly=true`
3. **Short TTL**: Default 24h, adjust based on security requirements
4. **Token Storage**: OAuth tokens stored encrypted in Supabase
5. **Automatic Cleanup**: Expired sessions deleted on access

## Testing

Run the test suite:

```bash
python3 test_session_persistence.py
```

This tests:
- Session creation
- Session retrieval
- Session updates
- Session expiry
- Automatic cleanup

## Troubleshooting

### "Could not find table 'mcp_sessions' in schema cache"

**Solution**: Reload Supabase schema cache
- Go to Supabase Dashboard → Settings → API
- Click "Reload schema cache" or wait a few minutes

### Session not found after creation

**Possible causes**:
1. Session expired (check `expires_at`)
2. RLS policy blocking access (disable RLS or add policy)
3. Wrong Supabase credentials

### Tools return "Not connected"

**Possible causes**:
1. No session_id in request headers/cookies
2. Session expired
3. OAuth token in session is invalid

Check logs for:
```
✅ Loaded session for user <user_id>
```

If you see this, session loading is working.

## MCP Client Configuration

Example configuration for Claude Code or other MCP clients:

```json
{
  "mcpServers": {
    "atoms": {
      "url": "https://your-domain.vercel.app/api/mcp",
      "headers": {
        "X-MCP-Session-ID": "your-session-id-after-oauth"
      }
    }
  }
}
```

Or use the OAuth flow to get a session_id automatically.

## Migration from Direct OAuth

If you were previously using direct OAuth (non-stateless):

1. The system now **falls back to direct OAuth** if no session_id is provided
2. Sessions are **optional** but recommended for serverless
3. Existing OAuth flows continue to work

The `_extract_bearer_token()` function tries session context first, then falls back to FastMCP OAuth tokens.
