# Fix: 401 Unauthorized - invalid_token

## Problem
Server is running but returning `401 Unauthorized` with `invalid_token` error.

## Root Cause
The server needs environment variables to verify tokens:
- **Supabase JWT verification**: Requires `SUPABASE_URL` and `SUPABASE_ANON_KEY`
- **Unsigned JWT (test mode)**: Requires `ATOMS_TEST_MODE=true`

## Solution

### Option 1: Enable Supabase JWT Verification (Recommended)

Set Supabase credentials when starting the server:

```bash
source .venv/bin/activate

# Set Supabase credentials
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_ANON_KEY="your-anon-key"

# Or use NEXT_PUBLIC_ prefix
export NEXT_PUBLIC_SUPABASE_URL="https://your-project.supabase.co"
export NEXT_PUBLIC_SUPABASE_ANON_KEY="your-anon-key"

# Start server
atoms run --http
```

### Option 2: Use Test Mode (Unsigned JWTs)

If you don't have Supabase credentials, enable test mode:

```bash
source .venv/bin/activate

# Enable test mode
export ATOMS_TEST_MODE=true

# Start server
atoms run --http
```

### Option 3: Use the Updated Script

The `scripts/start_local_server.sh` script now automatically:
1. Loads `.env` file if it exists
2. Sets `ATOMS_TEST_MODE=true`
3. Uses Supabase credentials if available

```bash
./scripts/start_local_server.sh
```

## Verify Configuration

Check server startup logs for:
```
✅ Hybrid authentication configured:
  - OAuth (AuthKit): ...
  - Supabase JWT: enabled (https://...)
```

Or with test mode:
```
✅ Hybrid authentication configured:
  - OAuth (AuthKit): ...
  - Test mode: enabled
```

## Quick Fix

If you have a `.env` file with Supabase credentials:

```bash
# The script will auto-load .env
./scripts/start_local_server.sh
```

If you don't have Supabase credentials:

```bash
export ATOMS_TEST_MODE=true
atoms run --http
```

## Debugging

To see what's happening during authentication, check server logs. The server will now log:
- Which verification methods are available
- Why token verification failed
- Token preview (first 50 chars)

Look for lines like:
```
Bearer token provided but verification failed. Token preview: eyJ...
Token verification attempts: internal=False, authkit=True, supabase=False, test_mode=false
```
