# CORS & OAuth Troubleshooting Guide

## 🚨 Current Error Analysis

Based on your browser console errors, here's what's happening:

### Error 1: CORS Preflight Failures

```
Access to fetch at 'https://atomcp.kooshapari.com/.well-known/oauth-protected-resource/api/mcp' 
from origin 'http://127.0.0.1:3000' has been blocked by CORS policy: 
Response to preflight request doesn't pass access control check: 
No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

**Status**: ✅ **FIXED** in `server.py` (lines 572-582)

The server now adds proper CORS headers to all discovery endpoints.

### Error 2: AuthKit Domain Returns 404

```
https://authkit-01k4cgw2j1fgwzyzjdmvwgqzbd.authkit.app/.well-known/openid-configuration
Failed to load resource: the server responded with a status of 404 ()
```

**Status**: ❌ **NEEDS FIX**

**Root Cause**: The AuthKit domain in your `.env` file is incorrect or not provisioned.

**Solution**: Update `FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN` with your actual AuthKit domain from WorkOS Dashboard.

### Error 3: MCP Protocol Version Header Not Allowed

```
Request header field mcp-protocol-version is not allowed by Access-Control-Allow-Headers 
in preflight response.
```

**Status**: ✅ **FIXED** in `server.py`

The `_set_cors_headers()` function now includes `MCP-Protocol-Version` in allowed headers.

### Error 4: HTTP to HTTPS Redirects

```
Access to fetch at 'http://atomcp.kooshapari.com/.well-known/oauth-protected-resource/api/mcp' 
from origin 'http://127.0.0.1:3000' has been blocked by CORS policy: 
Response to preflight request doesn't pass access control check: 
Redirect is not allowed for a preflight request.
```

**Status**: ⚠️ **CLOUDFLARE CONFIGURATION ISSUE**

**Root Cause**: Cloudflare is redirecting HTTP to HTTPS, which breaks CORS preflight requests.

**Solution**: Configure Cloudflare to handle HTTPS properly (see below).

### Error 5: Client Registration Stuck

```
Cannot transition from step: client_registration
```

**Status**: ❌ **BLOCKED BY AUTHKIT 404**

**Root Cause**: Claude Desktop can't complete OAuth flow because AuthKit metadata is unavailable.

**Solution**: Fix AuthKit domain first, then enable DCR.

---

## 🔧 Step-by-Step Fixes

### Fix 1: Update AuthKit Domain

**Current (WRONG)**:
```bash
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN=https://authkit-01k4cgw2j1fgwzyzjdmvwgqzbd.authkit.app
```

**How to find the correct domain**:

1. Go to https://dashboard.workos.com
2. Navigate to **Authentication** → **AuthKit**
3. Look for **AuthKit URL** or **Environment URL**
4. It might be:
   - `https://decent-hymn-17-staging.authkit.app` (staging)
   - `https://decent-hymn-17.authkit.app` (production)
   - `https://auth.yourdomain.com` (custom domain)

**Test the domain**:
```bash
# Replace with your actual domain
curl https://decent-hymn-17-staging.authkit.app/.well-known/openid-configuration

# Expected: JSON response with OAuth endpoints
# If 404: Domain is still wrong
```

**Update .env**:
```bash
# Edit .env file
nano .env

# Update this line:
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN=https://YOUR-ACTUAL-DOMAIN
```

### Fix 2: Enable Dynamic Client Registration

1. Go to https://dashboard.workos.com
2. Navigate to **Applications** → **Configuration**
3. Scroll to **OAuth 2.0** section
4. Find **Dynamic Client Registration (DCR)**
5. Toggle it **ON**
6. Click **Save Changes**

**Verify DCR is enabled**:
```bash
curl -X POST https://YOUR-AUTHKIT-DOMAIN/oauth/register \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "Test Client",
    "redirect_uris": ["http://127.0.0.1:3000/oauth/callback"],
    "grant_types": ["authorization_code"],
    "response_types": ["code"]
  }'

# Expected: JSON with client_id and client_secret
# If error: DCR not properly enabled
```

### Fix 3: Configure Cloudflare for CORS

#### Option A: Cloudflare Dashboard

1. Go to Cloudflare Dashboard
2. Select domain `kooshapari.com`
3. Navigate to **SSL/TLS** → **Overview**
4. Set encryption mode to **Full (strict)**
5. Navigate to **SSL/TLS** → **Edge Certificates**
6. Enable **Always Use HTTPS**
7. Navigate to **Rules** → **Transform Rules**
8. Create a new **Modify Response Header** rule:
   - **Rule name**: Add CORS Headers
   - **When incoming requests match**: Custom filter expression
   - **Field**: Hostname, **Operator**: equals, **Value**: `atomcp.kooshapari.com`
   - **Then**: Set dynamic header
   - **Header name**: `Access-Control-Allow-Origin`
   - **Value**: `*`
   - Add another header:
   - **Header name**: `Access-Control-Allow-Headers`
   - **Value**: `Authorization, Content-Type, MCP-Protocol-Version`

#### Option B: Cloudflare Worker (Advanced)

Create a worker to handle CORS:

```javascript
addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})

async function handleRequest(request) {
  // Handle OPTIONS preflight
  if (request.method === 'OPTIONS') {
    return new Response(null, {
      status: 204,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Authorization, Content-Type, MCP-Protocol-Version',
        'Access-Control-Max-Age': '86400',
      }
    })
  }

  // Forward request to origin
  const response = await fetch(request)
  
  // Add CORS headers to response
  const newResponse = new Response(response.body, response)
  newResponse.headers.set('Access-Control-Allow-Origin', '*')
  newResponse.headers.set('Access-Control-Allow-Headers', 'Authorization, Content-Type, MCP-Protocol-Version')
  
  return newResponse
}
```

### Fix 4: Configure Redirect URIs in WorkOS

1. Go to https://dashboard.workos.com
2. Navigate to **Authentication** → **AuthKit** → **Configuration**
3. Find **Redirect URIs** section
4. Add these URIs:
   ```
   http://127.0.0.1:3000/oauth/callback
   http://localhost:3000/oauth/callback
   https://atomcp.kooshapari.com/oauth/callback
   ```
5. Click **Save**

---

## 🧪 Testing Your Fixes

### Test 1: AuthKit Metadata

```bash
# Should return JSON with OAuth endpoints
curl https://YOUR-AUTHKIT-DOMAIN/.well-known/openid-configuration | jq

# Expected fields:
# - issuer
# - authorization_endpoint
# - token_endpoint
# - registration_endpoint
```

### Test 2: MCP Server Protected Resource

```bash
# Should return JSON with resource metadata
curl https://atomcp.kooshapari.com/.well-known/oauth-protected-resource | jq

# Expected:
# {
#   "resource": "https://atomcp.kooshapari.com/api/mcp",
#   "authorization_servers": ["https://YOUR-AUTHKIT-DOMAIN"],
#   "scopes_supported": ["openid", "profile", "email"]
# }
```

### Test 3: CORS Preflight

```bash
# Test OPTIONS request with CORS headers
curl -X OPTIONS https://atomcp.kooshapari.com/.well-known/oauth-protected-resource \
  -H "Origin: http://127.0.0.1:3000" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: mcp-protocol-version" \
  -v 2>&1 | grep -i "access-control"

# Expected:
# Access-Control-Allow-Origin: *
# Access-Control-Allow-Headers: Authorization, Content-Type, MCP-Protocol-Version
```

### Test 4: Dynamic Client Registration

```bash
# Test DCR endpoint
curl -X POST https://YOUR-AUTHKIT-DOMAIN/oauth/register \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "Claude Desktop Test",
    "redirect_uris": ["http://127.0.0.1:3000/oauth/callback"],
    "grant_types": ["authorization_code"],
    "response_types": ["code"],
    "token_endpoint_auth_method": "client_secret_basic"
  }' | jq

# Expected: JSON with client_id and client_secret
```

---

## 📊 Verification Checklist

Before testing with Claude Desktop, verify:

- [ ] AuthKit domain returns valid OpenID configuration (not 404)
- [ ] MCP server returns protected resource metadata
- [ ] CORS headers are present in OPTIONS responses
- [ ] Dynamic Client Registration is enabled in WorkOS
- [ ] Redirect URIs are configured in WorkOS
- [ ] Cloudflare SSL mode is set to Full (strict)
- [ ] No HTTP→HTTPS redirects on preflight requests

---

## 🐛 Still Having Issues?

### Enable Debug Logging

```bash
# Set environment variable
export LOG_LEVEL=DEBUG

# Run server
python -m atoms_mcp-old.server

# Watch for errors related to:
# - AuthKit domain
# - CORS headers
# - OAuth endpoints
```

### Check Browser Console

1. Open Claude Desktop
2. Open Developer Tools (Cmd+Option+I on Mac)
3. Go to **Console** tab
4. Look for errors containing:
   - "CORS policy"
   - "Access-Control-Allow-Origin"
   - "preflight"
   - "404"

### Test with curl

```bash
# Test each endpoint individually
curl -v https://atomcp.kooshapari.com/.well-known/oauth-protected-resource
curl -v https://YOUR-AUTHKIT-DOMAIN/.well-known/openid-configuration
curl -v https://YOUR-AUTHKIT-DOMAIN/.well-known/oauth-authorization-server
```

### Common Mistakes

1. **Wrong AuthKit domain format**: Must match exactly what's in WorkOS Dashboard
2. **DCR not enabled**: Check WorkOS Dashboard settings
3. **Cloudflare caching**: Purge cache after making changes
4. **Redirect URIs missing**: Must include all origins that will connect
5. **SSL mode wrong**: Must be Full or Full (strict), not Flexible

---

## 📞 Need More Help?

If you're still stuck after following this guide:

1. **Check WorkOS Documentation**: https://workos.com/docs/authkit
2. **Check FastMCP Documentation**: https://github.com/jlowin/fastmcp
3. **Verify your setup matches the examples** in `atoms_mcp-old/examples/`

