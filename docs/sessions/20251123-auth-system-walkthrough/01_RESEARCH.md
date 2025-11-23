# Auth System Research

## Current Architecture

### Token Verification Flow

**Your Frontend (Next.js + AuthKit) → Your Atoms Agent → MCP Server**

```
1. Frontend:
   - Uses `withAuth()` from '@workos-inc/authkit-nextjs' to get authenticated user
   - Calls `authkit.getAccessToken()` to get JWT token (WorkOS-signed)
   - Creates Supabase client with `accessToken: async () => { return authkit.getAccessToken(); }`
   - Passes token to atoms agent (via HTTP request or SDK)

2. Atoms Agent:
   - Receives user token from frontend
   - Verifies token is legitimate (matches user)
   - Passes token to MCP tools for operation

3. MCP Server:
   - Receives Bearer token in Authorization header: `Authorization: Bearer <JWT>`
   - Hybrid auth provider checks:
     a. Is it an internal bearer token? (static token for system services)
     b. Is it a WorkOS User Management token? (from authenticate_with_password)
     c. Is it an AuthKit OAuth JWT? (from frontend OAuth flow)
   - Extracts user_id and other claims from verified token
   - Sets token on database adapter for RLS context
   - Database queries use auth.uid() to filter by user
```

### Auth System Components

#### 1. **HybridAuthProvider** (`services/auth/hybrid_auth_provider.py`)
- **Purpose**: Accepts multiple auth methods simultaneously
- **Methods**:
  - `authenticate(request)` - Primary entry point, checks for Bearer token or falls back to OAuth
  - `verify_token(token)` - Verifies bearer token via multiple methods
  - `_verify_workos_user_management_jwt()` - Handles tokens from `authenticate_with_password`
  - `_verify_authkit_jwt()` - Handles tokens from OAuth flow
- **Current state**: Fully implemented with manual JWT verification

#### 2. **WorkOSTokenVerifier** (`services/auth/workos_token_verifier.py`)
- **Purpose**: Extends FastMCP's JWTVerifier to support multiple token issuers
- **Methods**:
  - `verify_token(token)` - Detects and verifies both AuthKit OAuth and WorkOS User Management tokens
- **Current state**: Full JWT handling with JWKS verification

#### 3. **SupabaseAuthAdapter** (`infrastructure/supabase_auth.py`)
- **Purpose**: Validates tokens and extracts user info for database RLS
- **Methods**:
  - `validate_token(token)` - Validates JWT, caches result, returns user info with access_token
  - `create_session()` - Creates persistent session token (for later reuse)
  - `verify_credentials()` - Fallback for username/password auth
- **Current state**: Supports AuthKit JWT validation, caching, and session persistence

#### 4. **SessionManager** (`auth/session_manager.py`)
- **Purpose**: Persists OAuth sessions in Supabase (stateless serverless)
- **Methods**:
  - `create_session()` - Store session in Supabase mcp_sessions table
  - `get_session()` - Retrieve session with expiry check
  - `update_session()` - Update OAuth data or MCP state
- **Current state**: Full implementation for stateless servers

#### 5. **Tool Base Auth** (`tools/base.py`)
- **Purpose**: Validates auth token in tool operations
- **Methods**:
  - `_validate_auth(auth_token)` - Validates token, gets user info, sets RLS context on database
  - `_get_user_id()` - Gets user_id from cached context
- **Current state**: Calls SupabaseAuthAdapter.validate_token(), caches result

### Token Types Your System Supports

| Token Type | Source | Issuer | Verification | Use Case |
|-----------|--------|--------|--------------|----------|
| **AuthKit OAuth JWT** | Frontend OAuth flow | `https://auth.atoms.tech` (example) | JWKS with audience/issuer validation | Frontend browsers, CLI with OAuth |
| **WorkOS User Mgmt JWT** | `authenticate_with_password` API | `https://api.workos.com/user_management/client_<ID>` | JWKS, lenient issuer/audience | Internal services, passwordless auth |
| **Internal Bearer Token** | Static config | None (static) | Direct string comparison | System-to-system (atoms agent → MCP) |
| **Session Token** | `SupabaseAuthAdapter.create_session()` | None (opaque) | Supabase table lookup | Stateless serverless (store → retrieve) |

### Current Logging State

**Good:**
- ✅ `HybridAuthProvider.authenticate()` and `verify_token()` have debug logs
- ✅ `SupabaseAuthAdapter.validate_token()` has token cache logging
- ✅ `ToolBase._validate_auth()` has logging

**Gaps:**
- ❌ No detailed token parsing logs (issuer, claims, sub, exp)
- ❌ No step-by-step verification flow logs
- ❌ No RLS context setting logs in database adapter
- ❌ No token cache hit/miss stats
- ❌ No frontend integration examples or debug guides

### Key Files & Line Counts

| File | Lines | Status |
|------|-------|--------|
| `services/auth/hybrid_auth_provider.py` | ~400 | ✅ Complete, needs logging enhancement |
| `services/auth/workos_token_verifier.py` | ~200 | ✅ Complete, needs logging enhancement |
| `infrastructure/supabase_auth.py` | ~200 | ✅ Complete, needs token parsing logs |
| `auth/session_manager.py` | ~200 | ✅ Complete, working well |
| `tools/base.py` | ~500+ | ✅ Has auth validation, needs context logs |

## Frontend Integration Pattern (Your Use Case)

### Next.js + AuthKit Pattern

```javascript
// Your frontend pattern:
import { getSignUpUrl, withAuth } from '@workos-inc/authkit-nextjs';
import { createClient } from '@supabase/supabase-js';
import { createClient as createAuthKitClient } from '@workos-inc/authkit-js';

const authkit = await createAuthKitClient('<WORKOS_CLIENT_ID>', {
  apiHostname: '<WORKOS_AUTH_DOMAIN>',
});

const supabase = createClient(
  'https://<supabase-project>.supabase.co',
  '<SUPABASE_ANON_KEY>',
  {
    accessToken: async () => {
      return authkit.getAccessToken(); // Returns JWT token
    },
  },
);

// In your page:
const { user } = await withAuth(); // Gets user from AuthKit session
const data = await supabase.from('table').select('*'); // Uses JWT in accessToken
```

### How This Connects to MCP Server

```
Frontend Browser
  ↓
AuthKit OAuth Flow (on frontend)
  ↓
authkit.getAccessToken() → Returns JWT (e.g., eyJhbGc...)
  ↓
Pass to Supabase as accessToken (RLS context)
  ↓
Supabase queries filtered by auth.uid()
  ↓
Also: Pass same token to atoms agent as Bearer token:
  Authorization: Bearer eyJhbGc...
  ↓
atoms agent → MCP server
  ↓
HybridAuthProvider.authenticate() receives Bearer token
  ↓
Verifies token is valid AuthKit JWT (JWKS + signature check)
  ↓
Extracts user_id from "sub" claim
  ↓
ToolBase._validate_auth() sets token on database for RLS
  ↓
Tool operations run with proper user context
```

## WorkOS User Management Flow (System-to-System)

```
atoms agent (system service)
  ↓
Calls WorkOS API: authenticate_with_password(email, password)
  ↓
WorkOS returns JWT with issuer: https://api.workos.com/user_management/client_<ID>
  ↓
atoms agent forwards token to MCP server as Bearer token
  ↓
WorkOSTokenVerifier detects issuer pattern
  ↓
Accepts token (already signed by WorkOS, trusted)
  ↓
Extracts user_id and passes to tools
```

## Auth Provider Chain (Fast MCP Integration)

```
FastMCP Server Creation
  ↓
server.py calls create_auth_provider(base_url)
  ↓
infrastructure_modules/server_auth.py:
  - Checks FASTMCP_SERVER_AUTH env var
  - If HybridAuthProvider: creates hybrid provider (OAuth + Bearer)
  - If RemoteAuthProvider: creates with WorkOSTokenVerifier
  ↓
Server.auth = provider
  ↓
FastMCP middleware intercepts requests:
  - If Authorization: Bearer token → calls provider.verify_token()
  - If no Bearer → calls provider.authenticate() (OAuth flow)
  ↓
Result: user context available to tools
```

## Assumptions & Risks

| Assumption | Risk | Mitigation |
|-----------|------|-----------|
| Frontend always sends valid AuthKit JWT | Token expired or malformed | Add exp claim validation, detailed error messages |
| JWKS endpoint is always reachable | Network failure, token verification fails | Cache JWKS keys, graceful fallback for testing |
| Token claims follow WorkOS schema (sub, email, etc) | Missing claims cause tool failures | Validate required claims early, provide helpful errors |
| Database adapter receives token correctly | RLS context not set, user data leaks | Add logs showing token passed to database adapter |
| atoms agent is trusted (can pass any token) | Unauthorized access if agent is compromised | Verify token signature, log token acceptance |

## References

- **WorkOS Docs**: https://workos.com/docs
- **FastMCP Auth**: Check `llms-full.txt` section on auth
- **Supabase RLS**: Uses `auth.uid()` function, requires JWT in context
- **JWT Format**: Header.Payload.Signature (3 parts, base64url-encoded)
