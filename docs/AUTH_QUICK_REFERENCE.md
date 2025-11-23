# Auth System - Quick Reference

## Your Frontend to MCP Token Flow (30 seconds)

```
┌──────────────────────────────────────────────────────────────────┐
│ 1. FRONTEND (Next.js + AuthKit)                                  │
│    const token = await authkit.getAccessToken()                  │
│    → Returns JWT signed by WorkOS                                │
└────────────────┬─────────────────────────────────────────────────┘
                 │
                 │ Authorization: Bearer <JWT>
                 ▼
┌──────────────────────────────────────────────────────────────────┐
│ 2. MCP SERVER (HybridAuthProvider)                               │
│    🔐[req_id] TOKEN VERIFICATION STARTED                         │
│    ✅ Verify JWT signature with JWKS                            │
│    ✅ Check issuer, expiry, audience                            │
│    ✅ Extract user_id from "sub" claim                          │
└────────────────┬─────────────────────────────────────────────────┘
                 │
                 │ User context: { user_id, email, claims }
                 ▼
┌──────────────────────────────────────────────────────────────────┐
│ 3. DATABASE (Supabase with RLS)                                  │
│    SupabaseAuthAdapter sets access_token on adapter             │
│    All queries: WHERE user_id = auth.uid()                      │
│    ✅ User sees only their data                                 │
└──────────────────────────────────────────────────────────────────┘
```

## 4 Auth Methods Supported

| # | Method | Source | Token Format | Status |
|---|--------|--------|--------------|--------|
| 1 | **AuthKit OAuth** | Frontend users | JWT (issuer: `https://auth.atoms.tech`) | ✅ Full support |
| 2 | **WorkOS User Mgmt** | System services | JWT (issuer: `https://api.workos.com/user_management/...`) | ✅ Full support |
| 3 | **Static Bearer** | CI/CD, service-to-service | Opaque string | ✅ Full support |
| 4 | **RemoteOAuth** | Future: federated | TBD | ⊘ Ready |

## Log Entry Point: When Bearer Token Arrives

```javascript
// Frontend sends:
fetch('https://mcp.atoms.tech/api/mcp', {
  headers: {
    'Authorization': `Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6ImtpZF8xMjM...`
  }
})
```

```
🔐[a3b2f1c4] HYBRID AUTH: Bearer token detected (length: 650)
🔐[a3b2f1c4] TOKEN VERIFICATION STARTED
🔐[a3b2f1c4] Step 1: Checking JWT format... ✅
🔐[a3b2f1c4] Step 2: Decoding JWT claims...
  ├─ issuer: https://auth.atoms.tech
  ├─ subject: user_123abc
  ├─ email: alice@example.com
  ├─ expires in: 25 minutes ✅
🔐[a3b2f1c4] Step 3-5: Checking auth methods...
✅[a3b2f1c4] AuthKit JWT VERIFIED
✅[a3b2f1c4] User ID: user_123abc
✅[a3b2f1c4] SUCCESS
```

## JWT Claims Reference

### AuthKit OAuth Token

```json
{
  "iss": "https://auth.atoms.tech",          // Issuer (always check this!)
  "sub": "user_123abc",                       // User ID
  "email": "alice@example.com",               // Email
  "name": "Alice",                            // Optional: User name
  "aud": "mcp_client_id",                     // Audience (MCP client ID)
  "exp": 1732350600,                          // Expires (Unix timestamp)
  "iat": 1732346445,                          // Issued at
  "email_verified": true                      // Email verified?
}
```

### WorkOS User Management Token

```json
{
  "iss": "https://api.workos.com/user_management/client_abc123def",
  "sub": "user_456def",
  "email": "system@atoms.tech",
  "exp": 1732347000,
  "iat": 1732346445
  // Note: No "aud" claim (that's OK!)
}
```

## Common Issues & Solutions

### Issue: "No Bearer token found"
```
🔐[req_id] No Bearer token found in Authorization header
🔐[req_id] Falling back to OAuth flow...
```

**Fix**:
```javascript
// Make sure to send Authorization header
const token = await authkit.getAccessToken();
const response = await fetch(url, {
  headers: {
    'Authorization': `Bearer ${token}`  // ← Add this!
  }
});
```

---

### Issue: "Token expired"
```
❌[req_id] expires at (exp): 1732340000 ❌ EXPIRED 6445 seconds ago
❌[req_id] Token verification FAILED - expired
```

**Fix**:
```javascript
// Refresh token from AuthKit
const newToken = await authkit.getAccessToken();
// getAccessToken() automatically refreshes if needed
```

---

### Issue: "Token audience doesn't match"
```
❌[req_id] InvalidAudienceError: Token audience (wrong_id) doesn't match expected (mcp_client_id)
```

**Fix**: Verify environment variables match
```bash
# Frontend token should have:
decoded.aud === "mcp_client_id"

# MCP server should have:
echo $AUTHKIT_CLIENT_ID  # Should be: mcp_client_id
```

---

### Issue: "All verification methods failed"
```
❌[req_id] Token issuer 'https://unknown-provider.com' not recognized
❌[req_id] Attempted methods:
  ├─ ❌ Internal bearer token
  ├─ ❌ WorkOS User Management JWT
  └─ ❌ AuthKit OAuth JWT
```

**Fix**: Check token issuer
```javascript
const decoded = jwt_decode(token);
console.log("Issuer:", decoded.iss);
// Should be one of:
// - https://auth.atoms.tech (AuthKit)
// - https://api.workos.com/user_management/... (WorkOS)
```

---

## Configuration

### Environment Variables

```bash
# Required: AuthKit OAuth
WORKOS_CLIENT_ID=sk_live_123...
WORKOS_API_KEY=sk_api_456...
WORKOS_AUTH_DOMAIN=https://auth.atoms.tech

# Optional: Internal static token
INTERNAL_BEARER_TOKEN=dev_token_xyz...

# Optional: Session persistence
SUPABASE_URL=https://...supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...
MCP_SESSION_TTL_HOURS=24

# Optional: Token caching
UPSTASH_REDIS_URL=https://...upstash.io
CACHE_TTL_TOKEN=3600
```

### Enable Debug Logging

```python
import logging

logging.getLogger("services.auth").setLevel(logging.DEBUG)
logging.getLogger("infrastructure.supabase_auth").setLevel(logging.DEBUG)

# Now you'll see step-by-step token verification logs
```

---

## API Reference

### HybridAuthProvider Methods

```python
# Called by FastMCP middleware when request arrives
async def authenticate(request) -> Optional[Dict[str, Any]]:
    """
    Check Authorization header for Bearer token.
    If found, verify and return user context.
    If not found, fall back to OAuth.
    """
    
# Called directly with token string (from verify_token())
async def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify bearer token with detailed logging.
    Try auth methods in order:
    1. Internal static token
    2. WorkOS User Management JWT
    3. AuthKit OAuth JWT
    Returns: { sub: user_id, email: ..., claims: {...} }
    """

# Internal: Verify AuthKit OAuth JWT
async def _verify_authkit_jwt(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify JWT from AuthKit OAuth flow.
    Checks: issuer, signature, audience, expiry.
    """

# Internal: Verify WorkOS User Management JWT
async def _verify_workos_user_management_jwt(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify JWT from WorkOS User Management API.
    Checks: issuer, signature, expiry (lenient on audience).
    """
```

### SupabaseAuthAdapter Methods

```python
async def validate_token(token: str) -> Dict[str, Any]:
    """
    Validate JWT token and return user info.
    Returns: {
        user_id: "user_123abc",
        username: "alice@example.com",
        auth_type: "authkit_jwt",
        access_token: token  # For RLS context
    }
    """

async def create_session(user_id, username, access_token, refresh_token) -> str:
    """Create persistent session token (for stateless servers)."""

async def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve session with expiry check."""
```

---

## Token Verification Sequence

```
1. Request arrives with Authorization: Bearer <token>
                        ↓
2. HybridAuthProvider.authenticate() extracts Bearer token
                        ↓
3. verify_token(token) starts (generate req_id for tracing)
                        ↓
4. Check JWT format (split by ".", should be 3 parts)
   ❌ Fail? Return None
   ✅ Pass? Continue
                        ↓
5. Decode JWT without verification (to inspect claims)
   ❌ Can't decode? Return None
   ✅ Decoded? Continue
                        ↓
6. Try Method 1: Static token?
   ✅ Match? Return user context
   ❌ No match? Continue
                        ↓
7. Try Method 2: WorkOS User Management (check issuer pattern)?
   ✅ Match issuer? Verify with JWKS? Return user context
   ❌ Not WorkOS? Continue
                        ↓
8. Try Method 3: AuthKit OAuth (check issuer matches domain)?
   ✅ Match issuer? Verify signature, audience, expiry? Return user context
   ❌ Not AuthKit? Continue
                        ↓
9. All methods failed
   ❌ Log failure with all attempted methods
   ❌ Return None
```

---

## File Location Reference

| What | Where |
|------|-------|
| Main auth provider | `services/auth/hybrid_auth_provider.py` |
| Token verification | `services/auth/workos_token_verifier.py` |
| Token to user mapping | `infrastructure/supabase_auth.py` |
| Bearer token extraction | `server.py` → `_extract_bearer_token()` |
| Tool auth validation | `tools/base.py` → `_validate_auth()` |
| Frontend integration guide | `docs/AUTH_SYSTEM_COMPLETE_GUIDE.md` |
| Logging examples | `docs/sessions/.../05_HYBRID_AUTH_LOGGING_EXAMPLES.md` |

---

## Key Insights

1. **Your frontend uses AuthKit OAuth** - Gets JWT from WorkOS
2. **Your atoms agent uses WorkOS User Management** - Calls API to get JWT
3. **Both are verified by same JWKS** - Same public keys validate both
4. **Request ID (req_id) traces entire flow** - Search logs for `[req_id]` to see everything
5. **Token is never logged (security)** - Only preview shown (first 50 chars)
6. **RLS enforces data isolation** - Database filters by `auth.uid()`

---

## How to Debug

### Step 1: Get token and check claims
```javascript
const token = await authkit.getAccessToken();
const decoded = jwt_decode(token);
console.log({ iss: decoded.iss, sub: decoded.sub, exp: decoded.exp });
```

### Step 2: Send to MCP with Bearer header
```bash
curl -H "Authorization: Bearer $TOKEN" https://mcp.atoms.tech/api/mcp
```

### Step 3: Check logs for req_id
```bash
# Find your request in logs
grep "Bearer token detected" logs.txt | tail -1
# Note the req_id: a3b2f1c4

# See entire flow
grep "a3b2f1c4" logs.txt

# Extract just success/failure
grep "a3b2f1c4" logs.txt | grep "✅\|❌"
```

### Step 4: Check specific failure
```bash
grep "a3b2f1c4" logs.txt | grep "expired\|signature\|audience"
```

---

**For detailed walkthroughs, see**: `docs/AUTH_SYSTEM_COMPLETE_GUIDE.md`

**For logging examples, see**: `docs/sessions/20251123-auth-system-walkthrough/05_HYBRID_AUTH_LOGGING_EXAMPLES.md`
