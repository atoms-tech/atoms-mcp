# Implementation Guide: Enhanced Auth Logging & Documentation

## Step 1: Enhance Token Verification Logging

### 1.1 Create Enhanced WorkOSTokenVerifier with Detailed Logging

**Location**: `services/auth/workos_token_verifier.py`

**What to add**:
1. Parse and log all JWT claims in readable format
2. Log verification steps as they happen (format check, expiry, signature, claims)
3. Log JWKS fetch attempt and result
4. Add timestamp and latency tracking
5. Color-coded logs for success/failure (✅ ❌ 🔐)

**Key additions**:
```python
async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
    """Verify token with comprehensive logging of each step."""
    
    start_time = time.time()
    log_id = uuid.uuid4().hex[:8]  # Unique ID for this verification
    
    logger.info(f"🔐[{log_id}] Token verification started")
    logger.info(f"🔐[{log_id}] Token length: {len(token)} chars")
    
    # Step 1: Check format
    logger.info(f"🔐[{log_id}] Step 1: Checking JWT format...")
    parts = token.split(".")
    if len(parts) != 3:
        logger.warning(f"❌[{log_id}] Invalid JWT: expected 3 parts, got {len(parts)}")
        return None
    logger.info(f"✅[{log_id}] Valid JWT structure: 3 parts")
    
    # Step 2: Decode and check claims
    logger.info(f"🔐[{log_id}] Step 2: Decoding JWT claims...")
    try:
        import jwt
        unverified = jwt.decode(token, options={"verify_signature": False})
        
        # Log all claims in readable format
        logger.info(f"🔐[{log_id}] JWT Claims:")
        logger.info(f"  issuer (iss): {unverified.get('iss')}")
        logger.info(f"  subject (sub): {unverified.get('sub')}")
        logger.info(f"  email: {unverified.get('email')}")
        logger.info(f"  audience (aud): {unverified.get('aud')}")
        logger.info(f"  issued at (iat): {unverified.get('iat')}")
        logger.info(f"  expires at (exp): {unverified.get('exp')}")
        
        # Log time remaining
        exp_timestamp = unverified.get('exp')
        if exp_timestamp:
            now = time.time()
            remaining = exp_timestamp - now
            if remaining > 0:
                logger.info(f"✅[{log_id}] Token valid for {int(remaining)} seconds")
            else:
                logger.warning(f"❌[{log_id}] Token expired {int(-remaining)} seconds ago")
    except Exception as e:
        logger.error(f"❌[{log_id}] Failed to decode token: {e}")
        return None
    
    # Step 3: Verify signature with JWKS
    logger.info(f"🔐[{log_id}] Step 3: Verifying signature with JWKS...")
    # ... rest of verification ...
    
    elapsed = time.time() - start_time
    logger.info(f"✅[{log_id}] Token verification complete ({elapsed:.2f}ms)")
    
    return verified_claims
```

### 1.2 Enhance HybridAuthProvider Logging

**Location**: `services/auth/hybrid_auth_provider.py`

**Add detailed logs for**:
1. Which auth method is being attempted
2. Fallback chain (internal token → WorkOS → AuthKit)
3. Success/failure reason for each method
4. Total authentication latency

### 1.3 Enhance SupabaseAuthAdapter Token Logging

**Location**: `infrastructure/supabase_auth.py`

**Add**:
1. Cache hit/miss rate logging
2. Token claims extraction logging
3. RLS context logging (which token is being set on database)
4. Session creation/lookup logging

## Step 2: Add RLS Context Logging to Database Adapter

### 2.1 Track Token in Database Adapter

**Location**: `infrastructure/supabase_db.py`

**Add method to log when token is set**:
```python
def set_access_token(self, token: str) -> None:
    """Set user's JWT for RLS context."""
    # Log that we're setting token for RLS
    logger.info(f"🔐 Setting access token on Supabase adapter")
    
    # Decode to show which user
    try:
        import jwt
        decoded = jwt.decode(token, options={"verify_signature": False})
        user_id = decoded.get("sub")
        logger.info(f"🔐 RLS context: user_id = {user_id}")
        logger.info(f"🔐 All future Supabase queries will use: auth.uid() = '{user_id}'")
    except:
        pass  # Silent if can't decode
    
    self._access_token = token
    if self._client:
        self._client.auth.set_session({
            "access_token": token,
            "refresh_token": "",
        })
```

## Step 3: Add Tool Operation Logging

### 3.1 Enhance ToolBase._validate_auth Logging

**Location**: `tools/base.py`

**Add**:
```python
async def _validate_auth(self, auth_token: str) -> Dict[str, Any]:
    """Validate auth token with detailed logging."""
    
    import uuid
    
    tool_request_id = uuid.uuid4().hex[:8]
    
    logger.info(f"🔐[{tool_request_id}] Tool auth validation started")
    logger.info(f"🔐[{tool_request_id}] Tool: {self.__class__.__name__}")
    logger.info(f"🔐[{tool_request_id}] Token length: {len(auth_token) if auth_token else 0}")
    
    # Validate via adapter
    start = time.time()
    user_info = await adapters["auth"].validate_token(auth_token)
    elapsed = time.time() - start
    
    logger.info(f"✅[{tool_request_id}] User {user_info.get('user_id')} authenticated ({elapsed:.2f}ms)")
    
    # Set RLS context
    if access_token := user_info.get("access_token"):
        logger.info(f"🔐[{tool_request_id}] Setting RLS context for {user_info.get('user_id')}")
        adapters["database"].set_access_token(access_token)
        logger.info(f"✅[{tool_request_id}] RLS context set")
    
    self._user_context = user_info
    return user_info
```

## Step 4: Create Frontend Integration Guide

### 4.1 Create Next.js Integration Example

**File**: `docs/FRONTEND_AUTH_INTEGRATION.md`

```markdown
# Frontend Auth Integration with MCP Server

## Your Pattern: Next.js + AuthKit + Supabase

### 1. Setup AuthKit on Frontend

```javascript
import { getSignUpUrl, withAuth, signOut } from '@workos-inc/authkit-nextjs';
import { createClient } from '@supabase/supabase-js';
import { createClient as createAuthKitClient } from '@workos-inc/authkit-js';

// Initialize AuthKit client
const authkit = await createAuthKitClient('<WORKOS_CLIENT_ID>', {
  apiHostname: '<WORKOS_AUTH_DOMAIN>', // e.g., https://auth.atoms.tech
});

// Create Supabase client with AuthKit token
const supabase = createClient(
  'https://<supabase-project>.supabase.co',
  '<SUPABASE_ANON_KEY>',
  {
    accessToken: async () => {
      // This automatically refreshes the token if needed
      return authkit.getAccessToken();
    },
  },
);
```

### 2. Get User Info

```javascript
export default async function HomePage() {
  // Retrieves the user from the session or returns `null` if no user is signed in
  const { user } = await withAuth();
  
  if (!user) {
    // Redirect to sign up
    const signUpUrl = await getSignUpUrl();
    return redirect(signUpUrl);
  }
  
  // User is authenticated
  console.log('Logged in as:', user.id);
  return <div>Welcome, {user.email}</div>;
}
```

### 3. Pass Token to MCP Server

```javascript
// When calling MCP tools from your frontend:

async function callMcpTool(toolName, parameters) {
  const token = await authkit.getAccessToken(); // Get fresh token
  
  const response = await fetch('https://mcp.atoms.tech/api/mcp', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`, // ← KEY: Pass token as Bearer
    },
    body: JSON.stringify({
      jsonrpc: '2.0',
      id: '1',
      method: 'resources/call_tool',
      params: {
        name: toolName,
        arguments: parameters,
      },
    }),
  });
  
  return response.json();
}

// Usage
const result = await callMcpTool('entity_tool', {
  operation: 'create',
  entity_type: 'project',
  data: { name: 'My Project' },
});
```

### 4. Debug Token Issues

If you're not seeing your data, check:

```javascript
// 1. Check if user is authenticated
const { user } = await withAuth();
console.log('User:', user?.id);

// 2. Check if token is being sent
const token = await authkit.getAccessToken();
console.log('Token length:', token?.length);
console.log('Token preview:', token?.substring(0, 50) + '...');

// 3. Decode token to see claims
import jwt from 'jsonwebtoken';
const decoded = jwt.decode(token);
console.log('Token claims:', {
  sub: decoded.sub,      // User ID
  email: decoded.email,
  aud: decoded.aud,      // Audience
  iss: decoded.iss,      // Issuer
  exp: decoded.exp,      // Expiry (Unix timestamp)
});

// 4. Check time until expiry
const now = Math.floor(Date.now() / 1000);
const expiresIn = decoded.exp - now;
console.log('Token expires in:', expiresIn, 'seconds');
```

### 5. Frontend Request Logging

Add this to see what's being sent:

```javascript
// Intercept all fetch requests to log headers
const originalFetch = window.fetch;
window.fetch = async (...args) => {
  const [url, options] = args;
  
  if (url.includes('mcp') && options?.headers?.Authorization) {
    console.log('🔐 Sending MCP request:');
    console.log('  URL:', url);
    console.log('  Auth header:', options.headers.Authorization.substring(0, 50) + '...');
    console.log('  Method:', options.method || 'GET');
  }
  
  return originalFetch(...args);
};
```
```

## Step 5: Create Debug Guide

### 5.1 Create `docs/AUTH_TROUBLESHOOTING.md`

**Sections**:
1. "I'm getting 'Authentication required'" → Check Bearer token in header
2. "Token is expired" → Check `exp` claim, refresh from AuthKit
3. "I see my data but other users' data too" → RLS context not set, check logs
4. "Slow token verification" → Check token cache, JWKS latency
5. "JWKS endpoint not reachable" → Check network, fallback working?

## Step 6: Test Auth Flows

### 6.1 Create Auth Integration Tests

**File**: `tests/integration/test_auth_flows.py`

```python
@pytest.mark.asyncio
async def test_authkit_oauth_token_verification(auth_adapter):
    """Test AuthKit OAuth token verification with detailed logging."""
    # Create a valid AuthKit OAuth JWT (mocked)
    token = create_test_authkit_jwt(
        sub="user_123",
        email="user@example.com",
        issuer="https://auth.atoms.tech"
    )
    
    # Verify token
    user_info = await auth_adapter.validate_token(token)
    
    # Check result
    assert user_info["user_id"] == "user_123"
    assert user_info["auth_type"] == "authkit_jwt"
    # Check logs show all claims were parsed
    # (logs should show issuer, sub, email, exp, etc)

@pytest.mark.asyncio
async def test_workos_user_management_token(auth_adapter):
    """Test WorkOS User Management JWT verification."""
    token = create_test_workos_jwt(
        sub="user_456",
        email="system@example.com",
        issuer="https://api.workos.com/user_management/client_abc123"
    )
    
    user_info = await auth_adapter.validate_token(token)
    assert user_info["user_id"] == "user_456"
    # Check logs show WorkOS token was detected and verified

@pytest.mark.asyncio
async def test_token_caching(auth_adapter):
    """Test that tokens are cached correctly."""
    token = create_test_authkit_jwt(sub="user_789")
    
    # First call - cache miss
    start = time.time()
    result1 = await auth_adapter.validate_token(token)
    first_latency = time.time() - start
    
    # Second call - cache hit (should be faster)
    start = time.time()
    result2 = await auth_adapter.validate_token(token)
    second_latency = time.time() - start
    
    assert result1 == result2
    assert second_latency < first_latency / 2  # Cache hit should be faster
    # Check logs show cache hit in second call

@pytest.mark.asyncio
async def test_expired_token_rejection(auth_adapter):
    """Test that expired tokens are rejected."""
    # Create token with exp in the past
    token = create_test_authkit_jwt(
        sub="user_999",
        exp=int(time.time()) - 3600  # Expired 1 hour ago
    )
    
    # Should raise ValueError
    with pytest.raises(ValueError, match="expired"):
        await auth_adapter.validate_token(token)
    # Check logs show expiry was detected and token rejected
```

## Implementation Order

1. **Phase 1: Logging Enhancement** (Days 1-2)
   - Enhance WorkOSTokenVerifier with detailed logs
   - Enhance HybridAuthProvider logging
   - Add RLS context logging to database adapter
   - Add tool operation logging

2. **Phase 2: Frontend Integration Guide** (Day 3)
   - Create FRONTEND_AUTH_INTEGRATION.md with Next.js example
   - Create AUTH_TROUBLESHOOTING.md debug guide
   - Add code examples for token passing

3. **Phase 3: Testing & Validation** (Day 4)
   - Create auth integration tests
   - Test all 4 auth methods
   - Validate logging is working
   - Measure token cache effectiveness

4. **Phase 4: Documentation & Polish** (Day 5)
   - Review all logs are clear and actionable
   - Update README with auth overview
   - Create architecture diagram
   - Test with real frontend requests

## Success Metrics

- ✅ Every token verification logged with unique ID
- ✅ All JWT claims logged in readable format
- ✅ RLS context setting logged
- ✅ Frontend integration example working
- ✅ Debug guide solves 80% of common issues
- ✅ Token cache latency < 50ms (vs 500ms without)
- ✅ No regression in existing tests
