# HybridAuthProvider - Enhanced Logging Examples

## Overview

The `HybridAuthProvider` has been enhanced with comprehensive, step-by-step logging for token verification. Each verification request gets a unique ID (req_id) for tracing through logs.

## Log Flow Examples

### Example 1: Successful AuthKit OAuth JWT Verification

```
🔐[a3b2f1c4] ════════════════════════════════════════════════════════
🔐[a3b2f1c4] TOKEN VERIFICATION STARTED
🔐[a3b2f1c4] Token length: 650 bytes
🔐[a3b2f1c4] Token preview: eyJhbGciOiJSUzI1NiIsImtpZCI6ImtpZF8xMjM...7HFkc2pBb1dqVgA==

🔐[a3b2f1c4] Step 1: Checking JWT format...
✅[a3b2f1c4] Valid JWT structure (3 parts)

🔐[a3b2f1c4] Step 2: Decoding JWT claims (without signature verification)...
🔐[a3b2f1c4] JWT Claims:
  ├─ issuer (iss): https://auth.atoms.tech
  ├─ subject (sub): user_123abc
  ├─ email: alice@example.com
  ├─ audience (aud): mcp_client_id
  ├─ expires at (exp): 1732350600 ✅ Valid for 25 minutes
  └─ issued at (iat): 1732346445

🔐[a3b2f1c4] Step 3: Checking internal bearer token...
🔐[a3b2f1c4] No internal token verifier configured

🔐[a3b2f1c4] Step 4: Checking WorkOS User Management JWT...
🔐[a3b2f1c4] _verify_workos_user_management_jwt() - checking WorkOS token...
🔐[a3b2f1c4] Step 1: Checking JWT format...
✅[a3b2f1c4] Valid JWT format (3 parts)
🔐[a3b2f1c4] Step 2: Decoding token to check issuer...
🔐[a3b2f1c4] Token issuer: https://auth.atoms.tech
🔐[a3b2f1c4] Token subject (sub): user_123abc
🔐[a3b2f1c4] Step 3: Checking if issuer is WorkOS User Management...
❌[a3b2f1c4] Token issuer 'https://auth.atoms.tech' is not a WorkOS User Management token

🔐[a3b2f1c4] Step 5: Checking AuthKit JWT...
🔐[a3b2f1c4] _verify_authkit_jwt() - attempting JWKS verification...
✅[a3b2f1c4] AuthKit OAuth token verified with JWT verifier (45.23ms)

✅[a3b2f1c4] AuthKit JWT VERIFIED (45.23ms)
✅[a3b2f1c4] User ID: user_123abc
✅[a3b2f1c4] Token verification SUCCESS - auth method: authkit_oauth
🔐[a3b2f1c4] ════════════════════════════════════════════════════════
```

**Key observations:**
- Request ID `a3b2f1c4` allows correlation in logs
- Every step logged (format check → claims decode → method attempts)
- Token expiry shown in human-readable format
- JWKS verification latency shown (45.23ms)
- Final success message shows user ID and auth method

---

### Example 2: WorkOS User Management Token (from authenticate_with_password)

```
🔐[b9c3a2e7] ════════════════════════════════════════════════════════
🔐[b9c3a2e7] TOKEN VERIFICATION STARTED
🔐[b9c3a2e7] Token length: 720 bytes
🔐[b9c3a2e7] Token preview: eyJhbGciOiJSUzI1NiIsImtpZCI6ImtpZF8yMz...8jK3L4M5Ow==

🔐[b9c3a2e7] Step 1: Checking JWT format...
✅[b9c3a2e7] Valid JWT structure (3 parts)

🔐[b9c3a2e7] Step 2: Decoding JWT claims (without signature verification)...
🔐[b9c3a2e7] JWT Claims:
  ├─ issuer (iss): https://api.workos.com/user_management/client_abc123def
  ├─ subject (sub): user_456def
  ├─ email: system@atoms.tech
  ├─ audience (aud): N/A
  ├─ expires at (exp): 1732347000 ✅ Valid for 9 minutes
  └─ issued at (iat): 1732346445

🔐[b9c3a2e7] Step 3: Checking internal bearer token...
🔐[b9c3a2e7] No internal token verifier configured

🔐[b9c3a2e7] Step 4: Checking WorkOS User Management JWT...
🔐[b9c3a2e7] _verify_workos_user_management_jwt() - checking WorkOS token...
🔐[b9c3a2e7] Step 1: Checking JWT format...
✅[b9c3a2e7] Valid JWT format (3 parts)
🔐[b9c3a2e7] Step 2: Decoding token to check issuer...
🔐[b9c3a2e7] Token issuer: https://api.workos.com/user_management/client_abc123def
🔐[b9c3a2e7] Token subject (sub): user_456def
🔐[b9c3a2e7] Step 3: Checking if issuer is WorkOS User Management...
✅[b9c3a2e7] Detected WorkOS User Management token with issuer: https://api.workos.com/user_management/client_abc123def
🔐[b9c3a2e7] Step 4: Verifying with JWKS (WorkOS uses same keys as AuthKit)...
✅[b9c3a2e7] Token verified with JWKS (with audience check)
🔐[b9c3a2e7] Step 5: Validating required claims...
✅[b9c3a2e7] WorkOS User Management JWT verified (67.14ms): sub=user_456def, email=system@atoms.tech

✅[b9c3a2e7] WorkOS User Management JWT VERIFIED (67.14ms)
✅[b9c3a2e7] User ID: user_456def
✅[b9c3a2e7] Token verification SUCCESS - auth method: workos_user_management
🔐[b9c3a2e7] ════════════════════════════════════════════════════════
```

**Key observations:**
- WorkOS issuer pattern detected correctly
- No audience claim expected for User Management tokens
- JWKS verification took 67.14ms (includes network fetch)
- System user identified as `system@atoms.tech`

---

### Example 3: Token Expired (Failure Case)

```
🔐[c4d5e6f7] ════════════════════════════════════════════════════════
🔐[c4d5e6f7] TOKEN VERIFICATION STARTED
🔐[c4d5e6f7] Token length: 650 bytes
🔐[c4d5e6f7] Token preview: eyJhbGciOiJSUzI1NiIsImtpZCI6ImtpZF8xMj...3M2T3E8==

🔐[c4d5e6f7] Step 1: Checking JWT format...
✅[c4d5e6f7] Valid JWT structure (3 parts)

🔐[c4d5e6f7] Step 2: Decoding JWT claims (without signature verification)...
🔐[c4d5e6f7] JWT Claims:
  ├─ issuer (iss): https://auth.atoms.tech
  ├─ subject (sub): user_789ghi
  ├─ email: bob@example.com
  ├─ audience (aud): mcp_client_id
  ├─ expires at (exp): 1732340000 ❌ EXPIRED 6445 seconds ago
  └─ issued at (iat): 1732336445

❌[c4d5e6f7] Token verification FAILED - expired

❌[c4d5e6f7] ════════════════════════════════════════════════════════
```

**Key observations:**
- Expiry check catches token immediately
- Shows exactly how long token has been expired (6445 seconds = 1.8 hours)
- No further verification attempts (fast fail)
- User should refresh token from AuthKit

---

### Example 4: Invalid Token Format (Not a JWT)

```
🔐[d7e8f9a0] ════════════════════════════════════════════════════════
🔐[d7e8f9a0] TOKEN VERIFICATION STARTED
🔐[d7e8f9a0] Token length: 32 bytes
🔐[d7e8f9a0] Token preview: not_a_jwt_just_random_string_here

🔐[d7e8f9a0] Step 1: Checking JWT format...
❌[d7e8f9a0] Invalid JWT: expected 3 parts, got 1
❌[d7e8f9a0] Token verification FAILED

❌[d7e8f9a0] ════════════════════════════════════════════════════════
```

**Key observations:**
- Format validation catches immediately
- No decoding attempts on malformed tokens
- Clear error message about JWT structure

---

### Example 5: All Auth Methods Failed

```
🔐[e8f9a0b1] ════════════════════════════════════════════════════════
🔐[e8f9a0b1] TOKEN VERIFICATION STARTED
🔐[e8f9a0b1] Token length: 650 bytes
🔐[e8f9a0b1] Token preview: eyJhbGciOiJSUzI1NiIsImtpZCI6ImtpZF8xMj...8nR9U0==

🔐[e8f9a0b1] Step 1: Checking JWT format...
✅[e8f9a0b1] Valid JWT structure (3 parts)

🔐[e8f9a0b1] Step 2: Decoding JWT claims (without signature verification)...
🔐[e8f9a0b1] JWT Claims:
  ├─ issuer (iss): https://unknown-provider.com
  ├─ subject (sub): user_999xyz
  ├─ email: unknown@example.com
  ├─ audience (aud): different_client_id
  ├─ expires at (exp): 1732350600 ✅ Valid for 25 minutes
  └─ issued at (iat): 1732346445

🔐[e8f9a0b1] Step 3: Checking internal bearer token...
🔐[e8f9a0b1] No internal token verifier configured

🔐[e8f9a0b1] Step 4: Checking WorkOS User Management JWT...
🔐[e8f9a0b1] _verify_workos_user_management_jwt() - checking WorkOS token...
🔐[e8f9a0b1] Step 1: Checking JWT format...
✅[e8f9a0b1] Valid JWT format (3 parts)
🔐[e8f9a0b1] Step 2: Decoding token to check issuer...
🔐[e8f9a0b1] Token issuer: https://unknown-provider.com
🔐[e8f9a0b1] Token subject (sub): user_999xyz
🔐[e8f9a0b1] Step 3: Checking if issuer is WorkOS User Management...
❌[e8f9a0b1] Token issuer 'https://unknown-provider.com' is not a WorkOS User Management token

🔐[e8f9a0b1] Step 5: Checking AuthKit JWT...
🔐[e8f9a0b1] _verify_authkit_jwt() - attempting JWKS verification...
🔐[e8f9a0b1] AuthKit JWT verifier failed: InvalidAudienceError: Token audience (different_client_id) doesn't match expected (mcp_client_id)

❌[e8f9a0b1] ════════════════════════════════════════════════════════
❌[e8f9a0b1] Token verification FAILED - NO VALID AUTH METHOD
❌[e8f9a0b1] Issuer: https://unknown-provider.com
❌[e8f9a0b1] Attempted methods:
  ├─ ❌ Internal bearer token
  ├─ ❌ WorkOS User Management JWT
  └─ ❌ AuthKit OAuth JWT
❌[e8f9a0b1] Verification took 123.45ms
❌[e8f9a0b1] ════════════════════════════════════════════════════════
```

**Key observations:**
- Shows all methods attempted
- Clear error for audience mismatch
- Shows total verification time
- Operator can see that issuer is unknown and audience is wrong

---

### Example 6: OAuth Flow (No Bearer Token)

```
🔐[f9a0b1c2] HYBRID AUTH authenticate() - checking Authorization header
🔐[f9a0b1c2] No Bearer token found in Authorization header
🔐[f9a0b1c2] Falling back to OAuth flow...
🔐[f9a0b1c2] HYBRID AUTH: No Bearer token, using OAuth flow

[OAuth provider logs - redirecting to AuthKit login...]

✅[f9a0b1c2] OAuth flow SUCCESS - User: user_newuser (523.14ms)
```

**Key observations:**
- Shows decision to use OAuth (no Bearer token)
- OAuth flow is delegated to underlying AuthKitProvider
- Total OAuth time measured (523.14ms - includes user interaction)

---

## Logging Configuration

### Enable Debug Logging for Auth

```python
import logging

# Set auth modules to DEBUG for detailed token logs
logging.getLogger("services.auth").setLevel(logging.DEBUG)
logging.getLogger("infrastructure.supabase_auth").setLevel(logging.DEBUG)

# Or globally
logging.basicConfig(level=logging.DEBUG)
```

### Production Logging (Security Best Practice)

```python
# Never log full token values in production
# Only log token previews (first 50 chars) and hashed values
# The enhanced logging already does this - shows "Token preview: eyJhbGc..."
# instead of full token
```

## Using Request ID for Tracing

The unique request ID (req_id) in logs enables full tracing:

```bash
# Find all logs for a specific token verification
grep "a3b2f1c4" application.log

# Extract just the verification flow
grep "a3b2f1c4" application.log | grep -E "^🔐|^✅|^❌"
```

## Log Output Fields

Each log line contains:

| Field | Purpose | Example |
|-------|---------|---------|
| `[req_id]` | Unique request ID for tracing | `a3b2f1c4` |
| `Step N` | Verification step number | `Step 1: Checking JWT format...` |
| `✅/❌/🔐` | Status emoji | `✅ Valid`, `❌ Failed`, `🔐 In progress` |
| `Message` | Detailed information | `Token issuer: https://auth.atoms.tech` |
| `(timing)` | Latency for that step | `(45.23ms)` |

## Troubleshooting with Logs

### "Token verification FAILED - expired"

**Action**: User should refresh token from AuthKit
```javascript
const newToken = await authkit.getAccessToken(); // Refresh
```

### "Token issuer '...' is not a WorkOS User Management token"

**Action**: Check token source. If from frontend, should be AuthKit OAuth token, not WorkOS User Management

### "Token audience (X) doesn't match expected (Y)"

**Action**: Check that token client ID matches MCP server's configured client ID
```bash
# Frontend token should have: aud: "mcp_client_id"
# MCP server should be configured with: AUTHKIT_CLIENT_ID=mcp_client_id
```

### "Verification took 523.14ms"

**Action**: Check if JWKS fetch is slow. If > 500ms, may have network latency. Enable JWKS caching.

---

## Summary

The enhanced logging provides:
- ✅ **Visibility**: Every token verification step logged
- ✅ **Traceability**: Request ID ties logs together
- ✅ **Debugging**: Clear error messages show what failed
- ✅ **Performance**: Latency measurements for each step
- ✅ **Security**: Token values not logged (only previews)
- ✅ **User context**: User ID shown on success
