# Complete Auth System Walkthrough: Secondary Token Verifier & Bearer Auth

## Quick Start: Your Frontend to MCP Auth Flow

### Your Frontend Pattern (Next.js + AuthKit)

```javascript
// 1. Frontend gets authenticated user via AuthKit
import { withAuth, getSignUpUrl } from '@workos-inc/authkit-nextjs';

export default async function HomePage() {
  const { user } = await withAuth(); // Gets user from AuthKit session
  if (!user) {
    const signUpUrl = await getSignUpUrl();
    return redirect(signUpUrl);
  }
  return <div>Welcome, {user.email}</div>;
}
```

### 2. Frontend Creates Supabase Client with AuthKit Token

```javascript
import { createClient } from '@supabase/supabase-js';
import { createClient as createAuthKitClient } from '@workos-inc/authkit-js';

const authkit = await createAuthKitClient('<WORKOS_CLIENT_ID>', {
  apiHostname: '<WORKOS_AUTH_DOMAIN>',
});

// Supabase auto-refreshes token and uses it for RLS
const supabase = createClient(
  'https://<project>.supabase.co',
  '<ANON_KEY>',
  {
    accessToken: async () => authkit.getAccessToken(),
  },
);
```

### 3. Frontend Calls MCP Server with Bearer Token

```javascript
// Get token from AuthKit
const token = await authkit.getAccessToken();

// Send to MCP server with Bearer header
const response = await fetch('https://mcp.atoms.tech/api/mcp', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,  // ← KEY
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    jsonrpc: '2.0',
    method: 'resources/call_tool',
    params: {
      name: 'entity_tool',
      arguments: {
        operation: 'create',
        entity_type: 'project',
        data: { name: 'My Project' }
      }
    }
  })
});
```

### 4. MCP Server Receives & Verifies Token

```
REQUEST arrives with: Authorization: Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6ImtpZF8xMjM...

🔐[a3b2f1c4] ════════════════════════════════════════════════════════
🔐[a3b2f1c4] TOKEN VERIFICATION STARTED
🔐[a3b2f1c4] Step 1: Checking JWT format... ✅ Valid
🔐[a3b2f1c4] Step 2: Decoding JWT claims...
  ├─ issuer: https://auth.atoms.tech
  ├─ subject: user_123abc
  ├─ email: alice@example.com
  ├─ expires in: 25 minutes ✅
🔐[a3b2f1c4] Step 4: Checking WorkOS User Management JWT... ❌
🔐[a3b2f1c4] Step 5: Checking AuthKit JWT... ✅
✅[a3b2f1c4] Token verification SUCCESS - auth method: authkit_oauth
✅[a3b2f1c4] User ID: user_123abc
🔐[a3b2f1c4] ════════════════════════════════════════════════════════

Tool operation starts:
✅ User authenticated as user_123abc
✅ RLS context set on database
✅ Query runs: WHERE user_id = 'user_123abc'
✅ Only user's data visible (RLS enforced)
```

### 5. Database Uses RLS to Filter Data

```sql
-- Database RLS policy
CREATE POLICY "users_see_own_data" ON entities
  USING (user_id = auth.uid());

-- When query runs with RLS context:
-- auth.uid() returns 'user_123abc' (from JWT)
-- Query automatically filtered to user's data only
```

---

## Architecture: 4-Layer Auth System

### Layer 1: Frontend Auth (AuthKit)

**What happens**:
- User logs in via AuthKit (WorkOS)
- AuthKit returns JWT token signed by WorkOS
- Frontend stores token in browser (or server session)

**Token structure**:
```
{
  "iss": "https://auth.atoms.tech",     # Issuer
  "sub": "user_123abc",                 # User ID
  "email": "alice@example.com",
  "aud": "mcp_client_id",               # Audience
  "exp": 1732350600,                    # Expires
  "iat": 1732346445                     # Issued at
}
```

**Where implemented**:
- Frontend: `authkit.getAccessToken()`
- No MCP server code needed

---

### Layer 2: Token Transfer (Bearer Header)

**What happens**:
- Frontend includes token in Authorization header
- `Authorization: Bearer <JWT>`
- MCP server's HTTP middleware extracts it

**Where implemented**:
```python
# server.py: _extract_bearer_token()
def _extract_bearer_token() -> Optional[str]:
    """Return the bearer token from HTTP Authorization header."""
    access_token = get_access_token()  # FastMCP provides this
    if not access_token:
        return None
    
    token = getattr(access_token, "token", None)
    if token:
        return str(token)
    
    # Fallback: check claims dict
    claims = getattr(access_token, "claims", None)
    if isinstance(claims, dict):
        for key in ("access_token", "token"):
            if candidate := claims.get(key):
                return str(candidate)
    
    return None
```

**Log output**:
```
🔐[a3b2f1c4] HYBRID AUTH: Bearer token detected (length: 650)
```

---

### Layer 3: Token Verification (HybridAuthProvider)

**What happens**:
1. `HybridAuthProvider.authenticate(request)` receives request
2. Extracts Bearer token from Authorization header
3. Calls `verify_token(token)` with detailed logging
4. Tries auth methods in order:
   - Internal static token (if configured)
   - WorkOS User Management JWT (system services)
   - AuthKit OAuth JWT (frontend users)
5. Returns user context dict on success

**Where implemented**:
```python
# services/auth/hybrid_auth_provider.py

class HybridAuthProvider(AuthProvider):
    async def authenticate(self, request):
        """Check for Bearer token or fall back to OAuth."""
        auth_header = request.headers.get("Authorization", "")
        
        if auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "").strip()
            return await self.verify_token(token)
        
        # No bearer token, use OAuth
        return await self.oauth_provider.authenticate(request)
    
    async def verify_token(self, token: str):
        """Verify bearer token with comprehensive logging."""
        # Generate unique request ID for tracing
        req_id = uuid.uuid4().hex[:8]
        
        # Step 1: Check format
        logger.info(f"🔐[{req_id}] TOKEN VERIFICATION STARTED")
        parts = token.split(".")
        if len(parts) != 3:
            logger.warning(f"❌[{req_id}] Invalid JWT: expected 3 parts, got {len(parts)}")
            return None
        
        # Step 2: Decode and inspect claims
        unverified = jwt.decode(token, options={"verify_signature": False})
        issuer = unverified.get("iss", "")
        logger.info(f"🔐[{req_id}] Token issuer: {issuer}")
        
        # Step 3-5: Try auth methods
        # ... (see enhanced logging examples)
        
        # Return user context on success
        return {
            "sub": user_id,
            "email": email,
            "claims": decoded
        }
```

**Log output**:
```
✅[a3b2f1c4] Token verification SUCCESS - auth method: authkit_oauth
✅[a3b2f1c4] User ID: user_123abc
```

---

### Layer 4: RLS Context & Database (SupabaseAuthAdapter)

**What happens**:
1. `SupabaseAuthAdapter.validate_token(token)` extracts user info
2. Returns dict with `access_token` for RLS context
3. Tool calls `ToolBase._validate_auth(token)` 
4. Database adapter receives token via `set_access_token()`
5. All queries now filtered by user via `auth.uid()`

**Where implemented**:
```python
# infrastructure/supabase_auth.py

class SupabaseAuthAdapter(AuthAdapter):
    async def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate AuthKit JWT and return user info."""
        # Decode JWT (signature already verified by HybridAuthProvider)
        decoded = jwt.decode(token, options={"verify_signature": False})
        
        user_id = decoded.get('sub')
        email = decoded.get('email')
        
        logger.info(f"✅ AuthKit JWT validated for: {email} (user_id: {user_id})")
        
        return {
            "user_id": user_id,
            "username": email,
            "auth_type": "authkit_jwt",
            "access_token": token  # Pass token to database for RLS
        }

# tools/base.py

class ToolBase:
    async def _validate_auth(self, auth_token: str) -> Dict[str, Any]:
        """Validate auth token and set RLS context."""
        # Validate token
        user_info = await adapters["auth"].validate_token(auth_token)
        
        # Set RLS context on database
        if access_token := user_info.get("access_token"):
            adapters["database"].set_access_token(access_token)
            logger.info(f"✅ RLS context set for user {user_info.get('user_id')}")
        
        return user_info
```

**Log output**:
```
🔐 Setting RLS context on database adapter
🔐 User ID: user_123abc
✅ RLS context set (auth.uid() will return user_123abc)
```

---

## Supported Auth Methods (Priority Order)

### Method 1: AuthKit OAuth JWT (Frontend)

**Used by**: Browser users, frontend SDKs

**Token source**:
```
Frontend AuthKit login → AuthKit returns JWT → authkit.getAccessToken()
```

**Issuer pattern**:
```
https://auth.atoms.tech  (or your AuthKit domain)
```

**Example token**:
```json
{
  "iss": "https://auth.atoms.tech",
  "sub": "user_123abc",
  "email": "alice@example.com",
  "aud": "mcp_client_id",
  "exp": 1732350600
}
```

**Verification**:
```
1. Check JWT format (3 parts)
2. Decode and check issuer starts with AuthKit domain
3. Fetch JWKS from AuthKit
4. Verify signature with public key
5. Validate audience claim (must match configured client ID)
6. Check expiry (must be in future)
```

---

### Method 2: WorkOS User Management JWT (System)

**Used by**: Internal services, atoms agent

**Token source**:
```
System calls WorkOS API: authenticate_with_password(email, password)
→ WorkOS returns JWT
→ Pass JWT to MCP server as Bearer token
```

**Issuer pattern**:
```
https://api.workos.com/user_management/client_<CLIENT_ID>
```

**Example token**:
```json
{
  "iss": "https://api.workos.com/user_management/client_abc123def",
  "sub": "user_456def",
  "email": "system@atoms.tech",
  "exp": 1732347000
}
```

**Verification**:
```
1. Check JWT format
2. Decode and check issuer contains "workos" or "user_management"
3. Fetch JWKS (same as AuthKit - WorkOS shares keys)
4. Verify signature
5. No audience check needed (User Management tokens often omit it)
6. Check expiry
```

---

### Method 3: Static Bearer Token (Internal)

**Used by**: Service-to-service, CI/CD pipelines

**Token source**:
```
Environment variable: INTERNAL_BEARER_TOKEN=<random-string>
→ Pass in Authorization header
```

**Format**:
```
Opaque string (not a JWT)
Example: dev_token_xyz789...
```

**Verification**:
```
Direct string comparison:
  if token == configured_token:
    return authenticated
```

---

### Method 4: RemoteOAuth (Future)

**Used by**: Federated identity (GitHub, Google, etc)

**Status**: Infrastructure in place, not yet configured

**When to use**: For federated auth from external providers

---

## Token Verification Flow (Detailed)

```
┌─────────────────────────────────────────────────────────────────┐
│ HTTP Request arrives at MCP server                              │
│ Authorization: Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6ImtpZF8xMjM... │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ FastMCP Middleware: Extract Authorization header                │
│ server.py: _extract_bearer_token()                              │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ HybridAuthProvider.authenticate(request)                        │
│ Check: "Authorization: Bearer <token>"?                         │
│   YES → call verify_token(token)                                │
│   NO  → fallback to OAuth                                       │
└──────────────────────┬──────────────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
        ▼                             ▼
    Bearer                          OAuth
    │                               │
    ▼                               ▼
┌──────────────────────┐    ┌──────────────────────┐
│ verify_token()       │    │ OAuth flow           │
│ 1. Check format      │    │ (AuthKitProvider)    │
│ 2. Decode claims     │    │ Redirect to login    │
│ 3. Check methods     │    │                      │
└──────────────────────┘    └──────────────────────┘
        │
        ├─→ Method 1: Internal static token?
        │   YES: StaticTokenVerifier.verify_token()
        │   NO:  continue
        │
        ├─→ Method 2: WorkOS User Management JWT?
        │   Check issuer contains "workos" or "user_management"
        │   Verify with JWKS (same as AuthKit)
        │   YES: return user_info
        │   NO:  continue
        │
        └─→ Method 3: AuthKit OAuth JWT?
            Check issuer matches AuthKit domain
            Verify with JWKS
            Validate audience claim
            Check expiry
            YES: return user_info
            NO:  fail verification
                 return None
```

---

## Logging: What You'll See

### Successful Verification

```
🔐[a3b2f1c4] ════════════════════════════════════════════════════════
🔐[a3b2f1c4] TOKEN VERIFICATION STARTED
🔐[a3b2f1c4] Step 1: Checking JWT format...
✅[a3b2f1c4] Valid JWT structure (3 parts)
🔐[a3b2f1c4] Step 2: Decoding JWT claims...
🔐[a3b2f1c4] Token issuer: https://auth.atoms.tech
🔐[a3b2f1c4] Token subject (sub): user_123abc
...
✅[a3b2f1c4] Token verification SUCCESS - auth method: authkit_oauth
✅[a3b2f1c4] User ID: user_123abc
🔐[a3b2f1c4] ════════════════════════════════════════════════════════
```

### Failed Verification

```
❌[c4d5e6f7] Token verification FAILED - NO VALID AUTH METHOD
❌[c4d5e6f7] Issuer: https://unknown-provider.com
❌[c4d5e6f7] Attempted methods:
  ├─ ❌ Internal bearer token
  ├─ ❌ WorkOS User Management JWT
  └─ ❌ AuthKit OAuth JWT
❌[c4d5e6f7] Verification took 123.45ms
```

---

## Troubleshooting

### "No Bearer token found"

**Problem**: Authorization header missing or malformed

**Check**:
```javascript
// Frontend must include header
const token = await authkit.getAccessToken();
const response = await fetch(url, {
  headers: {
    'Authorization': `Bearer ${token}`,  // ← Check this is present
  }
});
```

**Log**:
```
🔐[req_id] No Bearer token found in Authorization header
🔐[req_id] Falling back to OAuth flow...
```

---

### "Token expired"

**Problem**: Token's `exp` claim is in the past

**Check**:
```javascript
const token = await authkit.getAccessToken();
const decoded = jwt_decode(token);
const now = Math.floor(Date.now() / 1000);
const valid = decoded.exp > now;
console.log(valid ? "Token valid" : "Token expired");
```

**Log**:
```
❌[req_id] expires at (exp): 1732340000 ❌ EXPIRED 6445 seconds ago
❌[req_id] Token verification FAILED - expired
```

---

### "Token audience doesn't match"

**Problem**: Token's `aud` claim doesn't match MCP server's configured audience

**Check**:
```bash
# Frontend token audience
decoded.aud  # Should be: "mcp_client_id"

# MCP server configuration
echo $AUTHKIT_CLIENT_ID  # Should be: "mcp_client_id"
```

**Log**:
```
❌[req_id] InvalidAudienceError: Token audience (wrong_id) doesn't match expected (mcp_client_id)
```

---

### "All verification methods failed"

**Problem**: Token format is valid JWT but doesn't match any known issuer

**Check issuer**:
```javascript
const decoded = jwt_decode(token);
console.log("Issuer:", decoded.iss);
// Should be one of:
// - https://auth.atoms.tech (AuthKit)
// - https://api.workos.com/user_management/... (WorkOS)
// - dev_token_... (static token)
```

**Log**:
```
❌[req_id] Token issuer not supported: https://unknown-provider.com (accepted: https://auth.atoms.tech)
```

---

## Configuration

### Environment Variables

```bash
# AuthKit OAuth
WORKOS_CLIENT_ID=sk_live_123...
WORKOS_API_KEY=sk_api_456...
WORKOS_AUTH_DOMAIN=https://auth.atoms.tech

# Optional: Internal static token
INTERNAL_BEARER_TOKEN=dev_token_xyz...

# Optional: Session management
MCP_SESSION_TTL_HOURS=24
SUPABASE_URL=https://...supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...

# Optional: Token caching
UPSTASH_REDIS_URL=https://...upstash.io
CACHE_TTL_TOKEN=3600
```

### Python Code

```python
# Set logging to DEBUG for detailed token verification logs
import logging

logging.getLogger("services.auth").setLevel(logging.DEBUG)
logging.getLogger("infrastructure.supabase_auth").setLevel(logging.DEBUG)

# This will print step-by-step token verification logs to console/logs
```

---

## Key Files & Their Roles

| File | Purpose | Key Function |
|------|---------|--------------|
| `server.py` | FastMCP server setup | `_extract_bearer_token()` - extracts token from HTTP header |
| `services/auth/hybrid_auth_provider.py` | Multi-method auth | `authenticate()`, `verify_token()` - accepts Bearer tokens or OAuth |
| `services/auth/workos_token_verifier.py` | JWT verification | `verify_token()` - validates both AuthKit and WorkOS tokens |
| `infrastructure/supabase_auth.py` | Token→User mapping | `validate_token()` - decodes JWT, returns user info for RLS |
| `infrastructure/supabase_db.py` | Database access | `set_access_token()` - sets JWT on Supabase for RLS filtering |
| `tools/base.py` | Tool execution | `_validate_auth()` - validates token, sets RLS context before tool runs |

---

## Summary

Your auth system is a **4-layer architecture**:

1. **Frontend Auth** (AuthKit) - User logs in, gets JWT
2. **Token Transfer** (Bearer header) - Frontend includes JWT in requests
3. **Token Verification** (HybridAuthProvider) - MCP verifies JWT signature
4. **RLS Context** (Supabase) - Database filters data by authenticated user

**With comprehensive logging at every step** so you can see exactly what's happening when a request comes in.
