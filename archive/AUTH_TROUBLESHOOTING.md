# Authentication Troubleshooting Guide

## Common Issues and Solutions

### 1. OAuth Discovery Endpoints Return 404

**Symptoms**:
```
INFO: 127.0.0.1:54010 - "GET /.well-known/oauth-protected-resource HTTP/1.1" 404 Not Found
INFO: 127.0.0.1:54010 - "GET /.well-known/oauth-authorization-server HTTP/1.1" 404 Not Found
```

**Cause**: `HybridAuthProvider` not exposing OAuth routes

**Solution**: ✅ **FIXED** - Updated `HybridAuthProvider.get_routes()` to delegate to `AuthKitProvider`

**Verify**:
```bash
curl https://mcp.atoms.tech/.well-known/oauth-protected-resource
# Should return JSON with "resource", "authorization_servers", etc.
```

---

### 2. Bearer Token Authentication Fails

**Symptoms**:
```
INFO: Auth error returned: invalid_token (status=401)
```

**Possible Causes**:

#### A. Wrong Token Format
```python
# ❌ Wrong
headers = {"Authorization": "your-token"}

# ✅ Correct
headers = {"Authorization": "Bearer your-token"}
```

#### B. Token Not Configured
Check environment variables:
```bash
echo $ATOMS_INTERNAL_TOKEN
echo $WORKOS_CLIENT_ID
```

#### C. JWT Verification Failing
Check JWKS URI is correct:
```bash
# Should be constructed from authkit_domain
echo $FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN
# JWKS URI = {authkit_domain}/.well-known/jwks.json
```

**Debug**:
```python
# In HybridAuthProvider.authenticate()
logger.info(f"Bearer token: {token[:30]}...")
logger.info(f"Internal verifier: {self.internal_token_verifier is not None}")
logger.info(f"JWT verifier: {self.authkit_jwt_verifier is not None}")
```

---

### 3. OAuth Flow Fails at Authorization

**Symptoms**:
```
ERROR: Failed to fetch authorization server metadata
```

**Cause**: Incorrect AuthKit domain

**Solution**:
1. Check WorkOS Dashboard for correct domain
2. Test the domain:
   ```bash
   curl https://YOUR-AUTHKIT-DOMAIN/.well-known/openid-configuration
   ```
3. Update `.env`:
   ```bash
   FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN=https://correct-domain.authkit.app
   ```

---

### 4. Dynamic Client Registration (DCR) Fails

**Symptoms**:
```
ERROR: registration_endpoint not found
```

**Cause**: DCR not enabled in WorkOS

**Solution**:
1. Go to WorkOS Dashboard
2. Applications → Configuration → OAuth 2.0
3. Enable **Dynamic Client Registration**
4. Add allowed redirect URIs:
   - `http://localhost:*`
   - `http://127.0.0.1:*`
   - `https://your-domain.com/oauth/callback`

---

### 5. Protected Resource URL Mismatch

**Symptoms**:
```
Failed to start OAuth flow: Protected resource https://mcp.atoms.tech/ does not match expected http://localhost:8000/api/mcp
```

**Cause**: The OAuth protected resource URL doesn't match the actual server URL

**Solution**: ✅ **FIXED** - The server now auto-detects the correct base URL

**For local development**:
```bash
# DO NOT set these for local development:
# unset ATOMS_FASTMCP_BASE_URL
# unset FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL

# Only set these:
export ATOMS_FASTMCP_HOST=127.0.0.1  # or localhost
export ATOMS_FASTMCP_PORT=8000
export ATOMS_FASTMCP_TRANSPORT=http
```

**Verify the resource URL**:
```bash
curl http://localhost:8000/.well-known/oauth-protected-resource | jq .resource
# Should return: "http://127.0.0.1:8000/" or "http://localhost:8000/"
```

**For production**:
```bash
# Let VERCEL_URL auto-detect, or set explicitly:
export ATOMS_FASTMCP_BASE_URL=https://mcp.atoms.tech
```

---

### 6. CORS Errors

**Symptoms**:
```
Access to fetch at '...' from origin '...' has been blocked by CORS policy
```

**Cause**: Missing CORS headers on OAuth endpoints

**Solution**: FastMCP's `AuthKitProvider` should handle CORS automatically. If not:

```python
# In custom route handler
response.headers["Access-Control-Allow-Origin"] = "*"
response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
```

---

## Debugging Tools

### 1. Test OAuth Endpoints

```bash
# Test protected resource metadata
curl -v https://mcp.atoms.tech/.well-known/oauth-protected-resource

# Test authorization server metadata  
curl -v https://mcp.atoms.tech/.well-known/oauth-authorization-server

# Test with Bearer token
curl -v https://mcp.atoms.tech/api/mcp \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"ping","id":1}'
```

### 2. Check Server Logs

```bash
# Vercel logs
vercel logs --follow

# Local logs
tail -f server.log
```

Look for:
- `✅ Hybrid authentication configured`
- `✅ Authenticated via internal bearer token`
- `✅ Authenticated via AuthKit JWT`
- `❌ Bearer token provided but verification failed`

### 3. Verify Environment Variables

```python
# In server.py
import os
print("Auth Config:")
print(f"  AuthKit Domain: {os.getenv('FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN')}")
print(f"  Base URL: {os.getenv('ATOMS_FASTMCP_BASE_URL')}")
print(f"  Internal Token: {'SET' if os.getenv('ATOMS_INTERNAL_TOKEN') else 'NOT SET'}")
print(f"  WorkOS Client ID: {'SET' if os.getenv('WORKOS_CLIENT_ID') else 'NOT SET'}")
```

---

## Quick Fixes

### Reset Authentication

```bash
# 1. Clear all auth-related env vars
unset ATOMS_INTERNAL_TOKEN
unset WORKOS_CLIENT_ID
unset FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN

# 2. Set only required vars
export FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN=https://your-domain.authkit.app
export ATOMS_FASTMCP_BASE_URL=https://mcp.atoms.tech

# 3. Restart server
vercel --prod
```

### Test Minimal Setup

```python
# Minimal OAuth-only setup
from fastmcp import FastMCP
from fastmcp.server.auth.providers.workos import AuthKitProvider

auth = AuthKitProvider(
    authkit_domain="https://your-domain.authkit.app",
    base_url="https://mcp.atoms.tech"
)

mcp = FastMCP("test-server", auth=auth)
```

---

## Getting Help

If issues persist:

1. **Check FastMCP docs**: https://gofastmcp.com/servers/auth/remote-oauth
2. **Check WorkOS docs**: https://workos.com/docs/authkit
3. **Enable debug logging**:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```
4. **Share logs** with relevant error messages

