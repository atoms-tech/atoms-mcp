# Stateless MCP Migration - Quick Reference

## ✅ Migration Complete

Your MCP server has been migrated from in-memory sessions to Supabase-backed persistent sessions for stateless serverless deployments.

## 📁 Files Created

### SQL Scripts (`infrastructure/sql/`)
1. **check_mcp_sessions_table.sql** - Verify table schema and status
2. **create_mcp_sessions_table.sql** - Create mcp_sessions table
3. **create_session_rls_policies.sql** - Add Row Level Security policies
4. **test_session_operations.sql** - Test CRUD operations

### Python Files
5. **auth/persistent_authkit_provider.py** - Session-aware AuthKit provider

### Documentation
6. **STATELESS_MCP_MIGRATION_GUIDE.md** - Complete migration guide
7. **MIGRATION_SUMMARY.md** - This quick reference

## 📝 Files Modified

### server.py
- ✅ Updated `_extract_bearer_token()` to prioritize session context
- ✅ Replaced `AuthKitProvider` with `PersistentAuthKitProvider`
- ✅ Added `SessionMiddleware` for session persistence
- ✅ Removed duplicate `/auth/complete` handler

### .env
- ✅ Added `MCP_SESSION_TTL_HOURS=24`

## 🚀 Next Steps

### 1. Run SQL Scripts

Connect to your Supabase database and run:

```bash
# Via psql
psql -h <supabase-host> -U postgres -d postgres \
  -f infrastructure/sql/check_mcp_sessions_table.sql

psql -h <supabase-host> -U postgres -d postgres \
  -f infrastructure/sql/create_mcp_sessions_table.sql

psql -h <supabase-host> -U postgres -d postgres \
  -f infrastructure/sql/create_session_rls_policies.sql

psql -h <supabase-host> -U postgres -d postgres \
  -f infrastructure/sql/test_session_operations.sql
```

**OR via Supabase Dashboard:**
1. Go to SQL Editor
2. Copy/paste each script
3. Run in order

### 2. Verify Configuration

Check your `.env` has:
```bash
# Supabase (required)
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...

# Session config (required)
MCP_SESSION_TTL_HOURS=24

# WorkOS (required)
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN=https://xxx.authkit.app
```

### 3. Deploy

```bash
# Vercel
vercel deploy

# Or local testing
python server.py
```

### 4. Test OAuth Flow

1. Complete OAuth authentication
2. Verify session created:
   ```sql
   SELECT session_id, user_id, expires_at, created_at
   FROM mcp_sessions
   ORDER BY created_at DESC
   LIMIT 5;
   ```

3. Make MCP request with session:
   ```http
   X-MCP-Session-ID: <session_id>
   ```

4. Check logs for:
   ```
   "Using token from session context (Supabase-backed)"
   ```

## 🔍 How It Works

```
┌─────────────────────────────────────────────┐
│ 1. Client OAuth → WorkOS AuthKit            │
│                                             │
│ 2. PersistentAuthKitProvider                │
│    - Verifies Supabase JWT                  │
│    - Completes WorkOS OAuth                 │
│    - Creates session in mcp_sessions        │
│    - Returns session_id                     │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ 3. Client sends session_id in requests      │
│    (X-MCP-Session-ID header or cookie)      │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ 4. SessionMiddleware                        │
│    - Loads OAuth data from Supabase         │
│    - Extends session expiry on activity     │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ 5. Tools execute with user's auth token     │
│    (_extract_bearer_token checks session)   │
└─────────────────────────────────────────────┘
```

## 📊 Architecture Changes

### Before (In-Memory)
- ❌ Sessions in FastMCP process memory
- ❌ Lost on serverless cold starts
- ✅ Works on persistent servers only

### After (Persistent)
- ✅ Sessions in Supabase mcp_sessions
- ✅ Survives serverless cold starts
- ✅ Works on Vercel, Cloudflare, AWS Lambda
- ✅ Backward compatible with in-memory mode

## 🔐 Security

- ✅ RLS policies: users access own sessions only
- ✅ Service role has admin access
- ✅ HttpOnly cookies prevent XSS
- ✅ 24-hour TTL (configurable)
- ✅ OAuth tokens encrypted at rest

## 🐛 Troubleshooting

### Session not found
```sql
-- Check if table exists
SELECT * FROM pg_tables WHERE tablename = 'mcp_sessions';

-- Check RLS policies
SELECT * FROM pg_policies WHERE tablename = 'mcp_sessions';

-- View active sessions
SELECT * FROM active_mcp_sessions;
```

### Token not extracted
- Check logs for "Using token from session context"
- Verify `X-MCP-Session-ID` header present
- Check session not expired: `SELECT expires_at FROM mcp_sessions WHERE session_id = '...'`

### Rollback (if needed)
1. Replace `PersistentAuthKitProvider` with `AuthKitProvider` in server.py
2. Remove `SessionMiddleware` wrapper
3. Redeploy

## 📚 Resources

- **Full Guide:** `STATELESS_MCP_MIGRATION_GUIDE.md`
- **Session Docs:** `docs/SESSION_AUTH.md`
- **FastMCP:** https://github.com/jlowin/fastmcp
- **WorkOS AuthKit:** https://workos.com/docs/authkit
- **Supabase RLS:** https://supabase.com/docs/guides/auth/row-level-security

## ✨ Key Benefits

1. **Stateless Deployments** - Works on serverless platforms
2. **Session Persistence** - Survives cold starts
3. **Backward Compatible** - Existing OAuth flows work
4. **Secure** - RLS policies + encrypted storage
5. **Automatic Cleanup** - Expired sessions auto-deleted

---

**Status:** ✅ Ready to deploy
**Next:** Run SQL scripts → Deploy → Test OAuth flow
