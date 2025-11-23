# Auth System - Architecture Diagrams

## Complete Flow: Frontend to Database

```
┌────────────────────────────────────────────────────────────────────────────┐
│                       FRONTEND (Next.js + AuthKit)                         │
│                                                                             │
│  1. User logs in via AuthKit                                               │
│     ↓                                                                       │
│  2. authkit.getAccessToken()                                               │
│     ↓                                                                       │
│  3. Returns JWT: eyJhbGciOiJSUzI1NiI...                                    │
│     (issued by WorkOS, signed, expires in 1 hour)                          │
│                                                                             │
└────────────────┬──────────────────────────────────────────────────────────┘
                 │
                 │ const token = await authkit.getAccessToken()
                 │
                 ├─→ Use in Supabase:
                 │   const supabase = createClient(..., {
                 │     accessToken: async () => token
                 │   })
                 │
                 └─→ Send to MCP Server:
                     fetch('https://mcp.atoms.tech/api/mcp', {
                       headers: {
                         'Authorization': `Bearer ${token}`
                       }
                     })
                     
┌────────────────────────────────────────────────────────────────────────────┐
│               MCP SERVER (HybridAuthProvider - Enhanced Logging)            │
│                                                                             │
│  Request arrives: Authorization: Bearer eyJhbGciOiJSUzI1NiI...             │
│                                                                             │
│  🔐[a3b2f1c4] TOKEN VERIFICATION STARTED                                   │
│  ├─ Extract Bearer token from Authorization header                         │
│  │  HybridAuthProvider.authenticate(request)                               │
│  │                                                                          │
│  └─→ verify_token(token)                                                   │
│      ├─ Step 1: Check JWT format (3 parts separated by dots)               │
│      │  ✅ eyJhbGc... . ...payload... . ...signature...                   │
│      │                                                                      │
│      ├─ Step 2: Decode JWT claims (without verifying signature yet)        │
│      │  Claims extracted:                                                  │
│      │  ├─ iss (issuer): https://auth.atoms.tech                          │
│      │  ├─ sub (subject/user_id): user_123abc                             │
│      │  ├─ email: alice@example.com                                       │
│      │  ├─ aud (audience): mcp_client_id                                  │
│      │  ├─ exp (expiry): 1732350600 ✅ Valid for 25 minutes               │
│      │  └─ iat (issued at): 1732346445                                    │
│      │                                                                      │
│      ├─ Step 3: Try Internal Static Token?                                │
│      │  ❌ Not a static token                                             │
│      │                                                                      │
│      ├─ Step 4: Try WorkOS User Management JWT?                           │
│      │  Check if issuer contains "workos" or "user_management"             │
│      │  ❌ Issuer is "https://auth.atoms.tech" (not WorkOS UM)           │
│      │                                                                      │
│      └─ Step 5: Try AuthKit OAuth JWT?                                    │
│         Check if issuer matches AuthKit domain                             │
│         ✅ Issuer matches https://auth.atoms.tech                         │
│         ├─ Fetch JWKS from: https://auth.atoms.tech/.well-known/...      │
│         ├─ Verify signature using public key                              │
│         ├─ Validate audience: "mcp_client_id" ✅ matches                 │
│         ├─ Validate issuer: ✅ matches                                   │
│         ├─ Check expiry: ✅ not expired                                  │
│         └─ JWKS verification took 45.23ms                                 │
│                                                                             │
│  ✅[a3b2f1c4] SUCCESS                                                      │
│  └─ Return user context:                                                   │
│     {                                                                       │
│       sub: "user_123abc",                                                  │
│       email: "alice@example.com",                                          │
│       auth_type: "authkit_jwt",                                            │
│       access_token: "eyJhbGc..."  ← Passed to database for RLS           │
│     }                                                                       │
│                                                                             │
└────────────────┬──────────────────────────────────────────────────────────┘
                 │
                 │ User context dict with access_token
                 │
                 ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                      TOOL EXECUTION (tools/base.py)                        │
│                                                                             │
│  class ToolBase:                                                           │
│    async def _validate_auth(self, auth_token):                             │
│      # 1. Validate token via adapter                                       │
│      user_info = await adapters["auth"].validate_token(auth_token)         │
│                                                                             │
│      # 2. Extract access_token for RLS                                     │
│      if access_token := user_info.get("access_token"):                     │
│        # 3. Set on database adapter                                        │
│        adapters["database"].set_access_token(access_token)                 │
│        🔐 Now all queries will be filtered by auth.uid()                   │
│                                                                             │
│      # 4. Cache user context for tool operations                           │
│      self._user_context = user_info                                        │
│      return user_info                                                      │
│                                                                             │
└────────────────┬──────────────────────────────────────────────────────────┘
                 │
                 │ RLS context set with JWT
                 │
                 ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                    DATABASE (Supabase with RLS Policies)                   │
│                                                                             │
│  -- Supabase auth.uid() returns current user from JWT context              │
│  -- All tables have RLS policies filtering by user_id                      │
│                                                                             │
│  RLS Policy Example:                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐      │
│  │ CREATE POLICY "users_see_own_data" ON entities                  │      │
│  │   USING (user_id = auth.uid());                                 │      │
│  └─────────────────────────────────────────────────────────────────┘      │
│                                                                             │
│  When tool runs query:                                                     │
│  ┌─────────────────────────────────────────────────────────────────┐      │
│  │ SELECT * FROM entities WHERE ...                                │      │
│  │                                                                  │      │
│  │ Supabase automatically adds RLS filter:                         │      │
│  │ ... AND user_id = auth.uid()  ← = "user_123abc"               │      │
│  │                                                                  │      │
│  │ Result: Only user's entities returned                          │      │
│  └─────────────────────────────────────────────────────────────────┘      │
│                                                                             │
│  ✅ user_123abc sees only their data                                       │
│  ✅ user_456def sees only their data                                       │
│  ✅ No cross-user data leakage                                             │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Token Verification Decision Tree

```
REQUEST arrives with Authorization header
│
├─ Has "Bearer " prefix?
│  │
│  ├─ YES: Extract token, call verify_token(token)
│  │
│  │   🔐[req_id] TOKEN VERIFICATION STARTED
│  │   │
│  │   ├─ Step 1: JWT format check (3 parts?)
│  │   │  ├─ NO: ❌ Return None
│  │   │  └─ YES: Continue
│  │   │
│  │   ├─ Step 2: Decode claims
│  │   │  ├─ Can't decode: ❌ Return None
│  │   │  ├─ Decode success: Log issuer, expiry, etc.
│  │   │  └─ YES: Continue
│  │   │
│  │   ├─ Step 3: Try internal static token
│  │   │  ├─ Matches: ✅ Return user context
│  │   │  └─ No match: Continue
│  │   │
│  │   ├─ Step 4: Try WorkOS User Management JWT
│  │   │  ├─ Issuer contains "workos" or "user_management"?
│  │   │  │  ├─ YES: Verify signature, return context
│  │   │  │  └─ NO: Continue
│  │   │
│  │   └─ Step 5: Try AuthKit OAuth JWT
│  │      ├─ Issuer matches AuthKit domain?
│  │      │  ├─ NO: ❌ Return None (no auth method matched)
│  │      │  └─ YES: Verify signature
│  │      │       ├─ Signature invalid: ❌ Return None
│  │      │       ├─ Signature valid: Check audience
│  │      │       │  ├─ Audience mismatch: ❌ Return None
│  │      │       │  └─ Audience matches: Check expiry
│  │      │       │     ├─ Expired: ❌ Return None
│  │      │       │     └─ Valid: ✅ Return user context
│  │
│  └─ NO Bearer prefix: Fall back to OAuth
│     │
│     └─ AuthKitProvider.authenticate(request)
│        ├─ Redirect to login
│        ├─ User logs in
│        └─ OAuth callback → user context
│
└─ Result: User context dict or None
   │
   └─ If user context: Tool can execute with RLS filtering
      └─ If None: Request fails with 401 Unauthorized
```

---

## 4 Auth Methods - Comparison

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ METHOD 1: AuthKit OAuth JWT (Frontend Users)                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Source:   Browser OAuth flow → authkit.getAccessToken()                    │
│  Issuer:   https://auth.atoms.tech                                          │
│  Token:    JWT with claims: iss, sub, email, aud, exp, iat                 │
│  Verify:   JWKS endpoint + signature check + audience check                │
│  Latency:  45-100ms (includes JWKS fetch)                                  │
│  Status:   ✅ Full support with detailed logging                           │
│                                                                              │
│  Log output:                                                                │
│  ✅[req_id] AuthKit OAuth token verified (45.23ms)                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ METHOD 2: WorkOS User Management JWT (System Services)                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Source:   WorkOS API → authenticate_with_password(email, password)         │
│  Issuer:   https://api.workos.com/user_management/client_<ID>             │
│  Token:    JWT with claims: iss, sub, email, exp, iat (no aud)            │
│  Verify:   JWKS endpoint + signature check (lenient on audience)           │
│  Latency:  50-150ms (includes JWKS fetch)                                  │
│  Status:   ✅ Full support with detailed logging                           │
│                                                                              │
│  Use case:                                                                  │
│  atoms_agent calls WorkOS API:                                             │
│    user_obj = workos.user_management.authenticate_with_password(...)       │
│    token = user_obj.access_token                                           │
│    → Forward to MCP server as Bearer token                                 │
│                                                                              │
│  Log output:                                                                │
│  ✅[req_id] WorkOS User Management JWT verified (67.14ms)                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ METHOD 3: Static Bearer Token (CI/CD, Service-to-Service)                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Source:   Environment variable: INTERNAL_BEARER_TOKEN=dev_token_xyz...    │
│  Format:   Opaque string (not a JWT)                                       │
│  Token:    Random string, e.g., "dev_token_abc123def456"                  │
│  Verify:   Direct string comparison (no signature checks)                  │
│  Latency:  < 1ms (fastest - no network calls)                              │
│  Status:   ✅ Full support with logging                                    │
│                                                                              │
│  Use case:                                                                  │
│  CI/CD pipeline, admin tools, internal API calls                           │
│  curl -H "Authorization: Bearer $INTERNAL_TOKEN" https://mcp.atoms.tech   │
│                                                                              │
│  Log output:                                                                │
│  ✅[req_id] Internal bearer token VERIFIED (0.34ms)                        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ METHOD 4: RemoteOAuth (GitHub, Google, etc - Future)                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Source:   External OAuth provider (GitHub, Google, etc)                   │
│  Issuer:   https://github.com (or provider-specific)                       │
│  Token:    JWT per provider                                                │
│  Verify:   Provider-specific JWKS + validation                             │
│  Latency:  100-200ms (includes provider JWKS fetch)                        │
│  Status:   ⊘ Infrastructure ready, not yet configured                      │
│                                                                              │
│  Note: HybridAuthProvider can be extended for additional OAuth providers    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Logging Flow - Detailed Timeline

```
┌────────────────────────────────────────────────────────────────────────────┐
│ REQUEST TIMELINE WITH DETAILED LOGGING                                     │
└────────────────────────────────────────────────────────────────────────────┘

T=0ms
  Request arrives:
  POST /api/mcp HTTP/1.1
  Authorization: Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6ImtpZF8xMjM...
  
T=1ms
  🔐[a3b2f1c4] HYBRID AUTH authenticate() - checking Authorization header
  HybridAuthProvider.authenticate() called
  Bearer token detected
  → Delegate to verify_token()

T=2ms
  🔐[a3b2f1c4] ════════════════════════════════════════════════════════
  🔐[a3b2f1c4] TOKEN VERIFICATION STARTED
  🔐[a3b2f1c4] Token length: 650 bytes
  
T=3ms
  🔐[a3b2f1c4] Step 1: Checking JWT format...
  Split by "." → 3 parts ✅
  
T=4ms
  🔐[a3b2f1c4] Step 2: Decoding JWT claims...
  Decode without signature verification
  Extract all claims
  
T=5ms
  🔐[a3b2f1c4] JWT Claims:
    ├─ issuer (iss): https://auth.atoms.tech
    ├─ subject (sub): user_123abc
    ├─ email: alice@example.com
    ├─ audience (aud): mcp_client_id
    ├─ expires at (exp): 1732350600 ✅ Valid for 25 minutes
    └─ issued at (iat): 1732346445
  
T=6ms
  🔐[a3b2f1c4] Step 3: Checking internal bearer token...
  No internal token verifier configured
  → Not a static token, continue
  
T=7ms
  🔐[a3b2f1c4] Step 4: Checking WorkOS User Management JWT...
  Call _verify_workos_user_management_jwt()
  Check issuer pattern → Not WorkOS UM issuer
  → Not WorkOS token, continue
  
T=8ms
  🔐[a3b2f1c4] Step 5: Checking AuthKit JWT...
  Call _verify_authkit_jwt()
  Issuer matches AuthKit domain ✅
  
T=9-45ms
  🔐 Fetch JWKS from https://auth.atoms.tech/.well-known/jwks.json
  🔐 Get signing key from JWT header (kid_abc123)
  🔐 Verify signature with public key
  
T=45ms
  ✅[a3b2f1c4] AuthKit OAuth token verified with JWT verifier (45.23ms)
  ✅[a3b2f1c4] Validated: audience, issuer, signature, expiry
  
T=46ms
  ✅[a3b2f1c4] Token verification SUCCESS - auth method: authkit_oauth
  ✅[a3b2f1c4] User ID: user_123abc
  🔐[a3b2f1c4] ════════════════════════════════════════════════════════
  
T=47ms
  Return user context to ToolBase:
  {
    "sub": "user_123abc",
    "email": "alice@example.com",
    "auth_type": "authkit_jwt",
    "access_token": "eyJhbGc..."
  }
  
T=48ms
  tools/base.py: _validate_auth() receives context
  Set RLS context on database adapter:
  adapters["database"].set_access_token(access_token)
  
T=49ms
  🔐 RLS context set (auth.uid() = user_123abc)
  Tool operation can now execute
  Database queries will be filtered by user_id
  
T=50ms+
  Tool executes with RLS filtering
  Database returns only user's data
  Response sent back to client
  
Total latency: 50ms (mostly JWKS fetch time)
With caching: 5-10ms (cache hit)
```

---

## File Interaction Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         HTTP Request                                        │
│                          ↓                                                  │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ server.py: _extract_bearer_token()                                  │  │
│  │ - Get token from Authorization header                               │  │
│  │ - Return bearer token string                                        │  │
│  └──────────────────────┬───────────────────────────────────────────────┘  │
│                         │                                                   │
│                         ▼                                                   │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ services/auth/hybrid_auth_provider.py: HybridAuthProvider            │  │
│  │                                                                       │  │
│  │  authenticate(request)                                               │  │
│  │  ├─ Check for Bearer token                                           │  │
│  │  ├─ If found: call verify_token(token)                              │  │
│  │  └─ If not: fallback to OAuth                                       │  │
│  │                                                                       │  │
│  │  verify_token(token)  ← Comprehensive logging here                  │  │
│  │  ├─ Step 1: Check format                                            │  │
│  │  ├─ Step 2: Decode claims                                           │  │
│  │  ├─ Step 3: Try internal token                                      │  │
│  │  ├─ Step 4: Try WorkOS JWT                                          │  │
│  │  │  └─ Call _verify_workos_user_management_jwt(token)             │  │
│  │  │     ├─ Detect issuer pattern                                    │  │
│  │  │     ├─ Fetch JWKS                                              │  │
│  │  │     └─ Verify signature                                        │  │
│  │  │                                                                  │  │
│  │  └─ Step 5: Try AuthKit JWT                                         │  │
│  │     └─ Call _verify_authkit_jwt(token)                             │  │
│  │        ├─ Detect issuer pattern                                    │  │
│  │        ├─ Fetch JWKS                                              │  │
│  │        └─ Verify signature                                        │  │
│  │                                                                       │  │
│  │  Return: user context dict or None                                   │  │
│  └──────────────────────┬──────────────────────────────────────────────┘  │
│                         │                                                   │
│                         ▼                                                   │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ infrastructure/supabase_auth.py: SupabaseAuthAdapter                 │  │
│  │                                                                       │  │
│  │  validate_token(token)  ← Called by tool base                       │  │
│  │  ├─ Decode JWT (signature already verified)                        │  │
│  │  ├─ Extract user_id, email, claims                                 │  │
│  │  ├─ Check token cache (Redis or in-memory)                         │  │
│  │  └─ Return user info with access_token                             │  │
│  └──────────────────────┬──────────────────────────────────────────────┘  │
│                         │                                                   │
│                         ▼                                                   │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ tools/base.py: ToolBase                                              │  │
│  │                                                                       │  │
│  │  _validate_auth(auth_token)                                          │  │
│  │  ├─ Call adapters["auth"].validate_token(token)                    │  │
│  │  ├─ Get access_token from user info                                │  │
│  │  ├─ Pass to database adapter:                                       │  │
│  │  │  adapters["database"].set_access_token(access_token)            │  │
│  │  └─ Cache user context for tool                                    │  │
│  │                                                                       │  │
│  │  Tool execution now runs with RLS context                           │  │
│  └──────────────────────┬──────────────────────────────────────────────┘  │
│                         │                                                   │
│                         ▼                                                   │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ infrastructure/supabase_db.py: SupabaseDatabaseAdapter               │  │
│  │                                                                       │  │
│  │  set_access_token(token)  ← Called from tool base                   │  │
│  │  └─ Set JWT on Supabase client for RLS context                     │  │
│  │     (auth.uid() now returns user_id from token)                    │  │
│  │                                                                       │  │
│  │  All queries now filtered by user_id automatically                  │  │
│  └──────────────────────┬──────────────────────────────────────────────┘  │
│                         │                                                   │
│                         ▼                                                   │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ Supabase Database with RLS                                           │  │
│  │                                                                       │  │
│  │  SELECT * FROM entities WHERE user_id = auth.uid()                 │  │
│  │  Result: Only user_123abc's data                                   │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Summary

The auth system is a **clean, well-logged pipeline**:

1. **Bearer token arrives** → HybridAuthProvider extracts it
2. **Token verification** → 5 steps with comprehensive logging  
3. **User context** → Passed to tools with access_token
4. **RLS filtering** → Database enforces data isolation
5. **Logging** → Full request ID tracing throughout

**Every step is logged with the same `[req_id]` for easy tracing.**
