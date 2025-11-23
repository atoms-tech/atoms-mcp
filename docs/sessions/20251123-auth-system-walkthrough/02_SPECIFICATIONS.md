# Auth System Specifications & Requirements

## Functional Requirements

### FR1: Support Multiple Auth Methods
**The system MUST accept tokens from 4 distinct authentication sources:**

1. **AuthKit OAuth (Frontend)**
   - Source: Browser OAuth flow, frontend forwards JWT
   - Token format: JWT with issuer matching AuthKit domain
   - Verification: JWKS endpoint + RS256 signature + audience + issuer validation
   - Use case: End users from browser clients

2. **WorkOS User Management (System-to-System)**
   - Source: `authenticate_with_password` API call
   - Token format: JWT with issuer `https://api.workos.com/user_management/client_<ID>`
   - Verification: JWKS endpoint + RS256 + lenient issuer validation (already signed by WorkOS)
   - Use case: System services (atoms agent, internal API clients)

3. **Static Bearer Token (Internal Service)**
   - Source: Configuration (env var `INTERNAL_BEARER_TOKEN`)
   - Token format: Random string (opaque)
   - Verification: Direct string comparison
   - Use case: Service-to-service auth, CI/CD

4. **RemoteOAuth (Third-Party)**
   - Source: External OAuth provider (GitHub, Google, etc)
   - Token format: JWT per provider
   - Verification: Provider-specific JWKS + validation
   - Use case: Future extension for federated auth

### FR2: Comprehensive Logging for Debugging
**Every step of token verification MUST log for troubleshooting:**

#### Entry Point Logging
```
🔐 HYBRID AUTH: authenticate() called with Bearer token (length: 150)
   - Header: "Authorization: Bearer eyJhbGc..."
   - Timestamp: 2025-11-23T10:30:45.123Z
```

#### Token Parsing Logging
```
🔐 Token parsed:
   - Format: JWT (3 parts: header.payload.signature)
   - Algorithm: RS256 (expected)
   - Issuer: https://auth.atoms.tech
   - Subject (sub): user_123abc
   - Email: user@example.com
   - Audience: mcp_server_client_id
   - Issued at (iat): 2025-11-23T10:00:00Z
   - Expires at (exp): 2025-11-23T11:00:00Z
   - Time until expiry: 25 minutes
```

#### Verification Step Logging
```
🔐 Verification step 1: Check token format
   ✅ Valid JWT structure (3 parts)

🔐 Verification step 2: Detect token issuer
   ✅ Issuer "https://auth.atoms.tech" matches AuthKit domain
   ✅ Token type: AuthKit OAuth JWT

🔐 Verification step 3: Check token expiry
   ✅ exp: 1732350600 >= now: 1732346445 (valid)
   ⏱ Token expires in: 25 minutes

🔐 Verification step 4: Fetch JWKS
   🔐 JWKS URI: https://auth.atoms.tech/.well-known/jwks.json
   ✅ Fetched 3 signing keys
   ✅ Key ID from token: kid_abc123
   ✅ Key found in JWKS

🔐 Verification step 5: Verify signature
   🔐 Algorithm: RS256
   ✅ Signature valid (public key matched)

🔐 Verification step 6: Validate claims
   ✅ audience: "mcp_client_id" (expected: "mcp_client_id")
   ✅ issuer: "https://auth.atoms.tech" (expected)
   ✅ sub present: user_123abc
   ✅ email present: user@example.com

🔐 Verification complete:
   ✅ All checks passed
   - User ID: user_123abc
   - Auth method: AuthKit OAuth JWT
```

#### RLS Context Setup Logging
```
🔐 Setting RLS context on database adapter:
   - User ID: user_123abc
   - Token forwarded to: supabase_db_adapter
   🔐 Supabase.auth.setSession() with JWT
   ✅ RLS context set (auth.uid() will return user_123abc)
```

#### Tool Operation Logging
```
🔐 Tool operation starting:
   - Tool: entity_tool
   - Operation: create
   - User: user_123abc (from auth context)
   🔐 Checking user permissions...
   ✅ User has permission
   🔐 Executing query with RLS: WHERE user_id = user_123abc
   ✅ Operation complete
```

### FR3: Token Caching
**Token verification MUST be cached to reduce latency:**

- **Cache layer**: Upstash Redis (with in-memory fallback)
- **Cache key**: Token string (hashed for security)
- **Cache value**: User info (user_id, email, claims)
- **TTL**: Token expiry time or 1 hour (whichever is shorter)
- **Logging**:
  ```
  🔐 Token cache check:
     Cache key: sha256(token_string)
     ✅ Cache hit (user_123abc)
     ⏱ Cache TTL remaining: 45 minutes
  ```

### FR4: Error Handling & Clear Messages
**When token verification fails, MUST provide actionable error message:**

| Scenario | Error Message | Action |
|----------|---------------|--------|
| No Authorization header | `"Authentication required: no Authorization header"` | Client should send Bearer token |
| Malformed token | `"Invalid token format: expected 3 JWT parts (header.payload.signature)"` | Check token is complete |
| Expired token | `"Token expired at 2025-11-23T11:00:00Z (was valid for 1 hour from 2025-11-23T10:00:00Z)"` | Refresh token from provider |
| Invalid signature | `"Signature verification failed: public key didn't match"` | Token may be tampered with |
| Missing required claim | `"Token missing required claim: sub (user_id)"` | Provider should include claim |
| Unsupported issuer | `"Token issuer not supported: https://unknown.provider.com (accepted: https://auth.atoms.tech)"` | Use correct auth provider |

## Non-Functional Requirements

### NFR1: Performance
- Token verification latency: < 50ms (with cache hit)
- Token verification latency: < 500ms (JWKS fetch, cache miss)
- JWKS cache: Keep keys in memory for 1 hour
- Per-user request latency: < 100ms additional overhead

### NFR2: Security
- Never log full token value (only first 50 chars for debugging)
- Never store tokens in logs (use hashed values)
- Validate signature with JWKS (not pre-shared secrets)
- Reject expired tokens immediately (check exp claim)
- Validate audience claim (token intended for this server)
- Validate issuer claim (token from trusted provider)

### NFR3: Reliability
- Graceful degradation if JWKS endpoint down
- Fallback to in-memory token cache if Redis unavailable
- Clear errors when auth system misconfigured
- Log all configuration at startup

### NFR4: Observability
- Every token acceptance logged with user_id
- Every token rejection logged with reason
- RLS context changes logged
- Tool operations show authenticated user
- Metrics: token cache hit rate, verification latency, auth failures

## ARUs (Assumptions, Risks, Uncertainties)

### Assumptions
- ✅ **Frontend always sends token in Authorization header** - Verified in HybridAuthProvider.authenticate()
- ✅ **JWKS endpoint is publicly accessible** - WorkOS provides JWKS at /.well-known/jwks.json
- ✅ **Tokens follow JWT RFC 7519 format** - WorkOS/AuthKit compliant
- ✅ **Supabase RLS policies use auth.uid()** - Configured in database RLS

### Risks
| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|-----------|
| JWKS endpoint temporarily unavailable | Token verification fails | Medium | Cache keys in memory, graceful fallback |
| Token claims missing (e.g., no `sub`) | Tool execution fails | Low | Validate required claims early, clear error |
| atoms agent sends invalid token | Unauthorized access attempt | Low | Verify signature, log rejected tokens |
| Token expiry not checked | Expired tokens accepted | Low | Always validate `exp` claim with current time |
| Database adapter doesn't receive token | RLS context not set, all user data visible | High | Add logging for token passed to database |
| Frontend doesn't send token | Fall back to OAuth (correct behavior) | Expected | Handle gracefully in HybridAuthProvider |

### Uncertainties
| Uncertainty | Impact | Resolution |
|-------------|--------|-----------|
| What if atoms agent is offline? | Can't verify token, users can't access MCP | Handle with retries, clear error message |
| What if token lifetime is very short (<5 min)? | Cache TTL expires quickly, more JWKS fetches | Use token exp for cache TTL, monitor performance |
| What if multiple auth systems are mixed? | Routing confusion, wrong auth method used | Use issuer detection, clear logging |
| What if user roles/permissions change? | Token still valid, user has stale permissions | Validate permissions on each request, not just token |

## Acceptance Criteria

### AC1: All Auth Methods Work
- [ ] AuthKit OAuth JWT accepted and verified
- [ ] WorkOS User Management JWT accepted and verified
- [ ] Static bearer token accepted and compared
- [ ] RemoteOAuth JWT detected but not required (future work)

### AC2: Comprehensive Logging
- [ ] Token parsing logged (issuer, sub, exp, etc)
- [ ] Verification steps logged (format check, signature, claims)
- [ ] Cache hits/misses logged
- [ ] RLS context setting logged
- [ ] Tool operations show authenticated user
- [ ] All error cases log with actionable message

### AC3: Frontend Integration Working
- [ ] Next.js + AuthKit pattern documented
- [ ] Token flow diagram shown
- [ ] Example code for atoms agent included
- [ ] Debug guide for troubleshooting provided

### AC4: Error Messages Clear
- [ ] No "invalid token" (too vague)
- [ ] Each error includes actionable step for user
- [ ] Error messages help debug (show what was expected vs received)
- [ ] Security sensitive info not in errors (don't leak claims)

### AC5: Performance Acceptable
- [ ] Token verification latency measured
- [ ] Cache hit rate documented
- [ ] JWKS cache working (no repeated fetches)
- [ ] No N+1 queries for token verification

### AC6: No Regression
- [ ] All existing tests pass
- [ ] No changes to tool API or behavior
- [ ] Backward compatible with existing frontends
- [ ] Auth system works in all deployment modes (local, Vercel, etc)

## Configuration

### Environment Variables Required

```bash
# Required for all auth
FASTMCP_SERVER_AUTH=HybridAuthProvider

# Required for AuthKit OAuth
WORKOS_CLIENT_ID=sk_live_123...
WORKOS_API_KEY=sk_api_456...
WORKOS_AUTH_DOMAIN=https://auth.atoms.tech

# Optional: internal bearer token
INTERNAL_BEARER_TOKEN=dev_token_xyz...

# Optional: session persistence
MCP_SESSION_TTL_HOURS=24
SUPABASE_URL=https://...supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...

# Optional: token cache (Upstash Redis)
UPSTASH_REDIS_URL=https://...upstash.io
CACHE_TTL_TOKEN=3600
```

### Logging Configuration

```python
# Set logging level for auth modules
import logging

logging.getLogger("atoms_fastmcp").setLevel(logging.DEBUG)
logging.getLogger("services.auth").setLevel(logging.DEBUG)
logging.getLogger("infrastructure.supabase_auth").setLevel(logging.DEBUG)

# For production: DEBUG only, never log full tokens
# For development: TRACE/DEBUG for detailed flow
```
