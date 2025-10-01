# Supabase Setup for WorkOS Integration

## Overview

This guide walks you through setting up your Supabase database to work with the WorkOS AuthKit integration. The setup maintains your existing user data while adding WorkOS compatibility.

## 🗄️ Database Setup

### Step 1: Run the Setup SQL Script

1. Go to your [Supabase Dashboard](https://supabase.com/dashboard)
2. Navigate to your project
3. Go to **SQL Editor**
4. Copy and paste the contents of `infrastructure/sql/supabase_workos_setup.sql`
5. Click **Run** to execute the script

This script will:
- ✅ Create triggers to sync WorkOS users with your existing profiles
- ✅ Add WorkOS-specific columns to your profiles table
- ✅ Set up RLS policies for WorkOS service access
- ✅ Create helper functions for user validation and linking
- ✅ Set up audit logging for WorkOS events

### Step 2: Verify Your Current Schema

The setup script assumes you have a `profiles` table. If your user table has a different name, update the script accordingly:

```sql
-- If your table is named 'users' instead of 'profiles'
-- Replace all instances of 'profiles' with 'users' in the setup script
```

Common table structures we support:
- `profiles` (standard Supabase pattern)
- `users` 
- `user_profiles`
- Custom table names

### Step 3: Configure Service Role Access

The WorkOS proxy needs access to your database. In your Supabase settings:

1. Go to **Settings** → **API**
2. Copy your **service_role** key (keep it secret!)
3. Add it to your `.env` file:

```bash
# Add to your .env file
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## 🔐 Authentication Flow Setup

### Existing User Migration

Your existing users continue to work exactly as before. The integration adds WorkOS compatibility without breaking changes:

1. **Email/Password Users**: Continue signing in normally
2. **GitHub Users**: Continue using GitHub OAuth through Supabase
3. **Google Users**: Continue using Google OAuth through Supabase

### New WorkOS Features

Once set up, your system gains:

1. **OAuth 2.0 PKCE Compliance**: MCP servers can authenticate using standard OAuth
2. **Dynamic Client Registration**: New clients can register automatically
3. **Unified Token Management**: WorkOS handles token lifecycle
4. **Audit Trail**: All authentication events are logged

## 🔧 Configuration Steps

### 1. Update Your Environment Variables

```bash
# Supabase Configuration (existing)
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Add WorkOS Integration
WORKOS_API_KEY=sk_test_a2V5XzAxSzRDR1cyMjJXSlFXQlI1RDdDUFczUUM3LGxDdWJmN2tNTDBjaHlRNjhUaEtsalQ0ZTMu
WORKOS_CLIENT_ID=client_01K4CGW2J1FGWZYZJDMVWGQZBD
WORKOS_API_URL=https://api.workos.com

# Add Service Role Key (for WorkOS proxy)
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here
```

### 2. Test the Database Setup

Run this test query in your Supabase SQL Editor to verify everything is working:

```sql
-- Test the validation function
SELECT public.validate_user_credentials('test@example.com', NULL);

-- Check if profiles table has WorkOS columns
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'profiles' 
AND column_name IN ('workos_user_id', 'auth_provider');

-- Verify RLS policies
SELECT schemaname, tablename, policyname, roles 
FROM pg_policies 
WHERE tablename = 'profiles';
```

### 3. Test Authentication Flow

After setup, test with a real user:

```python
# Test script to verify Supabase integration
import asyncio
from auth.workos_supabase_proxy import WorkOSSupabaseAuthProxy

async def test_supabase_integration():
    proxy = WorkOSSupabaseAuthProxy()
    
    # Test with real user credentials
    result = await proxy.validate_supabase_credentials(
        "your-test-user@example.com", 
        "your-password"
    )
    
    print(f"Auth result: {result}")

asyncio.run(test_supabase_integration())
```

## 🔍 Troubleshooting

### Common Issues

1. **"relation profiles does not exist"**
   - Update the table name in the SQL script to match your schema
   - Common alternatives: `users`, `user_profiles`

2. **"permission denied for function"**
   - Ensure the service role key is correctly set
   - Verify RLS policies are applied correctly

3. **"user not found"**
   - Check that your users have `email_confirmed_at` set
   - Verify the user exists in `auth.users` table

4. **WorkOS API errors**
   - Verify your WorkOS credentials are correct
   - Check that redirect URIs are configured in WorkOS Dashboard

### Debug Queries

```sql
-- Check user structure
SELECT id, email, email_confirmed_at, created_at 
FROM auth.users 
WHERE email = 'your-test-email@example.com';

-- Check profile linkage
SELECT p.*, au.email 
FROM profiles p 
JOIN auth.users au ON p.id = au.id 
WHERE au.email = 'your-test-email@example.com';

-- View audit log
SELECT * FROM workos_audit_log 
ORDER BY created_at DESC 
LIMIT 10;
```

## 📊 Monitoring

### Audit Trail

The setup includes comprehensive logging:

```sql
-- View recent WorkOS authentication events
SELECT 
  wal.event_type,
  wal.event_data,
  au.email,
  wal.created_at
FROM workos_audit_log wal
JOIN auth.users au ON wal.user_id = au.id
ORDER BY wal.created_at DESC;
```

### User Sync Status

Check which users are linked with WorkOS:

```sql
-- View WorkOS integration status
SELECT 
  email,
  auth_provider,
  workos_user_id,
  CASE WHEN workos_user_id IS NOT NULL THEN 'Linked' ELSE 'Not Linked' END as workos_status
FROM workos_users
ORDER BY created_at DESC;
```

## 🚀 Next Steps

Once Supabase is configured:

1. ✅ **Test Authentication**: Use the MCP server OAuth endpoints
2. ✅ **Configure WorkOS Dashboard**: Set up redirect URIs
3. ✅ **Deploy**: Your OAuth 2.0 compliant MCP server is ready!

## 🔄 Migration Notes

- **Zero Downtime**: All existing authentication continues to work
- **Gradual Rollout**: Enable WorkOS OAuth alongside existing methods
- **Data Preservation**: No user data is modified or lost
- **Backward Compatible**: Existing integrations remain functional

Your Supabase database is now ready for WorkOS AuthKit integration! 🎉