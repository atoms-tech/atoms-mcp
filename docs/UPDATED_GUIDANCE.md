# Updated Guidance Based on Official WorkOS MCP Documentation

## 🎯 Key Updates

Based on the [official WorkOS MCP documentation](https://workos.com/docs/mcp), here are the important clarifications:

---

## 1. Correct Metadata Endpoint ✅

### What Changed

**Previous guidance**: Test with `/.well-known/openid-configuration`

**Correct for MCP**: Test with `/.well-known/oauth-authorization-server`

### Why This Matters

MCP uses **OAuth 2.0** metadata, not OpenID Connect:

- ✅ **OAuth 2.0**: `/.well-known/oauth-authorization-server` (MCP standard)
- ❌ **OpenID Connect**: `/.well-known/openid-configuration` (not primary for MCP)

### Updated Test Command

```bash
# Correct test for MCP
curl https://YOUR-AUTHKIT-DOMAIN/.well-known/oauth-authorization-server | jq

# Should return OAuth 2.0 metadata with:
{
  "authorization_endpoint": "...",
  "token_endpoint": "...",
  "registration_endpoint": "...",  # Required for DCR
  "issuer": "...",
  ...
}
```

### Compatibility Note

Some MCP clients may still request `/.well-known/openid-configuration`. Your server handles both:

1. **Primary**: `/.well-known/oauth-authorization-server` (OAuth 2.0)
2. **Compatibility**: `/.well-known/openid-configuration` (OpenID Connect)

Both endpoints are implemented in your `server.py` (lines 584-616).

---

## 2. Dynamic Client Registration (DCR) 🔑

### What It Is

OAuth 2.0 Dynamic Client Registration ([RFC 7591](https://datatracker.ietf.org/doc/html/rfc7591)) allows MCP clients to self-register without prior configuration.

### Why It's Required

Per the WorkOS MCP docs:

> The MCP protocol requires authorization servers (AuthKit) to implement OAuth 2.0 Dynamic Client Registration. This allows MCP clients to discover and self-register without prior knowledge of the MCP server.

### How to Enable

1. Go to https://dashboard.workos.com
2. Navigate to **Applications** → **Configuration**
3. Find **OAuth 2.0** section
4. Enable **Dynamic Client Registration**
5. Click **Save**

### What It Enables

Once enabled, AuthKit exposes the `/oauth2/register` endpoint:

```bash
# Test DCR endpoint
curl -X POST https://YOUR-AUTHKIT-DOMAIN/oauth2/register \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "Claude Desktop",
    "redirect_uris": ["http://127.0.0.1:3000/oauth/callback"],
    "grant_types": ["authorization_code"],
    "response_types": ["code"],
    "token_endpoint_auth_method": "client_secret_basic"
  }'

# Returns:
{
  "client_id": "client_...",
  "client_secret": "...",
  "client_name": "Claude Desktop",
  ...
}
```

---

## 3. Protected Resource Metadata 📋

### What It Is

Your MCP server must implement `/.well-known/oauth-protected-resource` to tell clients:

1. Where your MCP server is located
2. Which authorization server to use (AuthKit)
3. What scopes are supported

### Your Implementation

Already implemented in `server.py` (lines 618-655):

```python
async def _build_resource_metadata(request=None):
    authkit_domain = os.getenv("FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN")
    resource_path = os.getenv("ATOMS_FASTMCP_HTTP_PATH", "/api/mcp")
    
    metadata = {
        "resource": f"{base_url}{resource_path}",
        "scopes_supported": ["openid", "profile", "email"],
        "token_endpoint_auth_methods_supported": [
            "client_secret_post",
            "client_secret_basic",
        ],
    }
    
    if authkit_domain:
        metadata["authorization_servers"] = [authkit_domain.rstrip("/")]
    
    return metadata
```

### What It Returns

```json
{
  "resource": "https://atomcp.kooshapari.com/api/mcp",
  "authorization_servers": ["https://YOUR-AUTHKIT-DOMAIN"],
  "scopes_supported": ["openid", "profile", "email"],
  "token_endpoint_auth_methods_supported": [
    "client_secret_post",
    "client_secret_basic"
  ]
}
```

### Why It's Important

This metadata enables **zero-config** MCP client connections:

1. Client tries to connect to your MCP server
2. Gets `401 Unauthorized` with `WWW-Authenticate` header
3. Fetches `/.well-known/oauth-protected-resource`
4. Discovers AuthKit as the authorization server
5. Automatically initiates OAuth flow

---

## 4. WWW-Authenticate Header 🔐

### What It Is

When your MCP server receives an unauthenticated request, it must return:

```http
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Bearer error="unauthorized",
                  error_description="Authorization needed",
                  resource_metadata="https://atomcp.kooshapari.com/.well-known/oauth-protected-resource"
```

### Why It's Important

The `resource_metadata` parameter tells the client where to find your protected resource metadata, enabling automatic discovery of the authorization server.

### Your Implementation

This is handled by FastMCP's AuthKit provider automatically when you configure:

```bash
FASTMCP_SERVER_AUTH=fastmcp.server.auth.providers.workos.AuthKitProvider
```

---

## 5. CORS Headers ✅

### What Changed

**Status**: Already fixed in your code (lines 572-582)

### Implementation

```python
def _set_cors_headers(resp):
    try:
        resp.headers.setdefault("Access-Control-Allow-Origin", "*")
        resp.headers.setdefault("Access-Control-Allow-Methods", "GET,OPTIONS")
        resp.headers.setdefault(
            "Access-Control-Allow-Headers",
            "Authorization, Content-Type, MCP-Protocol-Version"
        )
    except Exception:
        pass
    return resp
```

### Applied To

All discovery endpoints:
- `/.well-known/openid-configuration`
- `/.well-known/oauth-authorization-server`
- `/.well-known/oauth-protected-resource`

### Action Required

Just restart the server to apply these fixes.

---

## 6. Complete OAuth Flow 🔄

Based on the WorkOS MCP documentation, here's the complete flow:

```
1. Client → MCP Server: GET /api/mcp
   ↓
2. MCP Server → Client: 401 Unauthorized
   WWW-Authenticate: Bearer resource_metadata="..."
   ↓
3. Client → MCP Server: GET /.well-known/oauth-protected-resource
   ↓
4. MCP Server → Client: JSON with authorization_servers: ["https://authkit..."]
   ↓
5. Client → AuthKit: GET /.well-known/oauth-authorization-server
   ↓
6. AuthKit → Client: OAuth 2.0 metadata (endpoints, capabilities)
   ↓
7. Client → AuthKit: POST /oauth2/register (Dynamic Client Registration)
   ↓
8. AuthKit → Client: client_id, client_secret
   ↓
9. Client → User: Open browser to AuthKit login
   ↓
10. User → AuthKit: Authenticate
   ↓
11. AuthKit → Client: Redirect with authorization code
   ↓
12. Client → AuthKit: POST /oauth2/token (exchange code for token)
   ↓
13. AuthKit → Client: access_token
   ↓
14. Client → MCP Server: GET /api/mcp
    Authorization: Bearer <access_token>
   ↓
15. MCP Server → Client: MCP response (tools, resources, etc.)
```

---

## 7. Updated Testing Commands 🧪

### Test 1: AuthKit OAuth Metadata

```bash
# Use OAuth endpoint (not OpenID)
curl https://YOUR-AUTHKIT-DOMAIN/.well-known/oauth-authorization-server | jq

# Should return:
{
  "issuer": "https://YOUR-AUTHKIT-DOMAIN",
  "authorization_endpoint": "https://YOUR-AUTHKIT-DOMAIN/oauth2/authorize",
  "token_endpoint": "https://YOUR-AUTHKIT-DOMAIN/oauth2/token",
  "registration_endpoint": "https://YOUR-AUTHKIT-DOMAIN/oauth2/register",
  ...
}
```

### Test 2: Protected Resource Metadata

```bash
curl https://atomcp.kooshapari.com/.well-known/oauth-protected-resource | jq

# Should return:
{
  "resource": "https://atomcp.kooshapari.com/api/mcp",
  "authorization_servers": ["https://YOUR-AUTHKIT-DOMAIN"],
  ...
}
```

### Test 3: Dynamic Client Registration

```bash
curl -X POST https://YOUR-AUTHKIT-DOMAIN/oauth2/register \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "Test Client",
    "redirect_uris": ["http://127.0.0.1:3000/oauth/callback"],
    "grant_types": ["authorization_code"],
    "response_types": ["code"]
  }' | jq

# Should return:
{
  "client_id": "client_...",
  "client_secret": "...",
  ...
}
```

### Test 4: CORS Headers

```bash
curl -X OPTIONS https://atomcp.kooshapari.com/.well-known/oauth-protected-resource \
  -H "Origin: http://127.0.0.1:3000" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: mcp-protocol-version" \
  -v 2>&1 | grep -i "access-control"

# Should show:
# Access-Control-Allow-Origin: *
# Access-Control-Allow-Headers: Authorization, Content-Type, MCP-Protocol-Version
```

---

## 8. Updated Checklist ✅

### Critical (Must Fix)

- [ ] **Find correct AuthKit domain** in WorkOS Dashboard
- [ ] **Test OAuth endpoint**: `curl https://YOUR-DOMAIN/.well-known/oauth-authorization-server`
- [ ] **Update `.env`** with correct `AUTHKIT_DOMAIN`
- [ ] **Enable DCR** in WorkOS Dashboard (Applications → Configuration)
- [ ] **Add redirect URIs** in WorkOS Dashboard
- [ ] **Restart server** to apply CORS fixes

### Verification

- [ ] AuthKit OAuth metadata returns JSON (not 404)
- [ ] Protected resource metadata returns JSON
- [ ] DCR endpoint works (returns client credentials)
- [ ] CORS headers present in OPTIONS responses
- [ ] Claude Desktop can connect

---

## 9. Key Differences Summary

| Aspect | Previous Understanding | Correct (per WorkOS docs) |
|--------|----------------------|---------------------------|
| Metadata endpoint | `/.well-known/openid-configuration` | `/.well-known/oauth-authorization-server` |
| Protocol | OpenID Connect | OAuth 2.0 (with OIDC compatibility) |
| DCR requirement | Optional | **Required** for MCP |
| Discovery method | Manual configuration | Automatic via `WWW-Authenticate` header |
| Client registration | Pre-configured | Dynamic (self-registration) |

---

## 10. Next Steps

1. **Read**: [WORKOS_MCP_INTEGRATION.md](WORKOS_MCP_INTEGRATION.md) for complete WorkOS integration details
2. **Fix**: AuthKit domain using updated test commands
3. **Enable**: DCR in WorkOS Dashboard
4. **Verify**: Using updated testing commands
5. **Test**: With Claude Desktop

---

## References

- **WorkOS MCP Documentation**: https://workos.com/docs/mcp
- **OAuth 2.0 RFC**: https://datatracker.ietf.org/doc/html/rfc6749
- **Dynamic Client Registration**: https://datatracker.ietf.org/doc/html/rfc7591
- **Protected Resource Metadata**: https://datatracker.ietf.org/doc/html/draft-ietf-oauth-resource-metadata-13
- **MCP Specification**: https://modelcontextprotocol.io/

