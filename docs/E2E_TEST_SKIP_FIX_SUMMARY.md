# E2E Test Skip Issue - FIXED

## Problem
32 E2E tests were being skipped because the `e2e_auth_token` fixture was incorrectly trying to authenticate with **Supabase auth** instead of using **AuthKit** (our actual OAuth provider).

## Root Cause
- System uses: **AuthKit (WorkOS)** for authentication + **Supabase** for database
- Fixture was calling: Supabase `auth.sign_in_with_password()` ❌
- Should have been: Generating AuthKit JWT token locally ✅

## The Fix
Updated `tests/e2e/conftest.py` - `e2e_auth_token()` fixture with 3-tier strategy:

### 1️⃣ Use Internal Bearer Token (if available)
```bash
export ATOMS_INTERNAL_TOKEN="your-token"
```
- Fastest
- No JWKS validation needed
- **Recommended for CI/CD**

### 2️⃣ Generate Signed AuthKit JWT (if key available)
```bash
export AUTHKIT_PRIVATE_KEY="..."
export WORKOS_CLIENT_ID="..."
```
- Cryptographically valid
- Full production simulation

### 3️⃣ Generate Mock JWT (default, local-only)
- Works without any config
- No external service calls
- Perfect for local development

## Result
✅ **NO MORE EXTERNAL SERVICE CALLS** - Token generation is entirely local
✅ **NO MORE SKIPPED TESTS** - Fixture generates token successfully every time
✅ **CI/CD FRIENDLY** - Set one env var (`ATOMS_INTERNAL_TOKEN`) and tests run

## How to Run E2E Tests

### Local (Development)
```bash
python -m pytest tests/e2e/ -v
# Uses mock JWT, works without any config
```

### CI/CD (Recommended)
```bash
export ATOMS_INTERNAL_TOKEN="test-secret-token"
python -m pytest tests/e2e/ -v
# Uses internal token, fast and deterministic
```

### Production Testing
```bash
export AUTHKIT_PRIVATE_KEY="your-key"
export WORKOS_CLIENT_ID="your-id"
python -m pytest tests/e2e/ -v
# Uses signed JWT, production-grade auth
```

## Files Modified
- `tests/e2e/conftest.py` - Updated `e2e_auth_token()` fixture
- `docs/E2E_AUTH_TOKEN_FIXTURE_FIX.md` - Full technical documentation

## Key Insight
**Never use Supabase auth to get a token for the MCP server.**
- Supabase = Database backend
- AuthKit = OAuth provider
- Use AuthKit tokens (or internal tokens) to authenticate with the MCP server

The fixture now correctly generates AuthKit-compatible tokens without any external service dependencies.
