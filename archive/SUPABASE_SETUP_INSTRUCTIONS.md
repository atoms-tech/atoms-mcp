# Supabase Setup Instructions for MCP Sessions

## ✅ Deployment Status

- **Vercel**: Deployed to production
- **Environment Variables**: Added to Vercel
  - `MCP_SESSION_TTL_HOURS=24`
  - `SUPABASE_SERVICE_ROLE_KEY`
- **Code**: Committed and pushed to `vecfin-latest`

## 🔧 Database Setup Required

The mcp_sessions table needs to be created in Supabase. Follow these steps:

### Step 1: Open Supabase SQL Editor

1. Go to [Supabase Dashboard](https://app.supabase.com)
2. Select your project: `ydogoylwenufckscqijp`
3. Click **SQL Editor** in the left sidebar
4. Click **New Query**

### Step 2: Run Setup Script

1. Open the file: `infrastructure/sql/setup_all_mcp_sessions.sql`
2. Copy the entire contents
3. Paste into Supabase SQL Editor
4. Click **Run** (or press `Cmd/Ctrl + Enter`)

### Step 3: Verify Setup

The script includes verification queries at the end. You should see:

✅ Table `mcp_sessions` created
✅ Indexes created (user_id, expires_at, created_at)
✅ RLS policies enabled
✅ Helper functions created
✅ Auto-cleanup function ready

### Step 4: Test Deployment

Once the table is created, test the OAuth flow:

```bash
# Get your deployment URL
curl https://atoms-qgk5k961o-atoms-projects-08029836.vercel.app/mcp/v1/

# Test OAuth initialization
curl https://atoms-qgk5k961o-atoms-projects-08029836.vercel.app/auth/init
```

## 🔍 What Was Changed

### Architecture
- **Before**: In-memory sessions (FastMCP default)
- **After**: Supabase-backed persistent sessions

### Files Modified
1. `server.py`
   - Token extraction prioritizes session context
   - Uses PersistentAuthKitProvider
   - SessionMiddleware added to ASGI stack

2. `auth/persistent_authkit_provider.py` (NEW)
   - Extends AuthKitProvider
   - Creates sessions in Supabase after OAuth
   - Returns session_id to clients

3. `.env`
   - Added `MCP_SESSION_TTL_HOURS=24`

### SQL Scripts Created
- `setup_all_mcp_sessions.sql` - Complete setup (run this one!)
- `check_mcp_sessions_table.sql` - Check table status
- `create_mcp_sessions_table.sql` - Table creation
- `create_session_rls_policies.sql` - Security policies
- `test_session_operations.sql` - Testing suite

## 🔄 How Sessions Work Now

### OAuth Flow
1. User initiates OAuth → WorkOS AuthKit
2. OAuth completes → PersistentAuthKitProvider handles callback
3. Session created in Supabase `mcp_sessions` table
4. Client receives `session_id`

### Request Flow
1. Client sends request with `X-MCP-Session-ID` header
2. SessionMiddleware loads OAuth tokens from Supabase
3. Tools execute with user's auth context
4. Session updated with new expiry (24h TTL)

### Stateless Benefits
✅ Works on Vercel, Cloudflare Workers, AWS Lambda
✅ Survives serverless cold starts
✅ Automatic session cleanup via `cleanup_expired_mcp_sessions()`
✅ Secured with Row Level Security (RLS)

## 📊 Monitoring

### Check Sessions
```sql
SELECT session_id, user_id, created_at, expires_at
FROM mcp_sessions
WHERE expires_at > NOW()
ORDER BY created_at DESC;
```

### Cleanup Expired Sessions
```sql
SELECT cleanup_expired_mcp_sessions();
```

### Session Stats
```sql
SELECT
    COUNT(*) AS total_sessions,
    COUNT(*) FILTER (WHERE expires_at > NOW()) AS active_sessions,
    COUNT(*) FILTER (WHERE expires_at <= NOW()) AS expired_sessions
FROM mcp_sessions;
```

## 🚀 Next Steps

1. ✅ Run `setup_all_mcp_sessions.sql` in Supabase SQL Editor
2. ✅ Test OAuth flow with your deployment
3. ✅ Verify sessions are created in `mcp_sessions` table
4. ✅ Monitor logs for session loading/creation
5. Optional: Set up cron job for `cleanup_expired_mcp_sessions()`

## 📚 Documentation

- **Complete Guide**: `STATELESS_MCP_MIGRATION_GUIDE.md`
- **Quick Reference**: `MIGRATION_SUMMARY.md`
- **Session Code**: `auth/session_manager.py`, `auth/session_middleware.py`

## 🐛 Troubleshooting

### Sessions not persisting?
- Check Vercel env vars are set
- Verify `mcp_sessions` table exists
- Check Supabase connection in logs

### OAuth failing?
- Verify WorkOS credentials
- Check CORS headers in responses
- Review `auth/persistent_authkit_provider.py` logs

### RLS blocking queries?
- Verify policies in `pg_policies`
- Check user_id matches auth.uid()
- Use service role key if needed (bypasses RLS)

---

**Status**: Ready to test after running SQL setup! 🎉
