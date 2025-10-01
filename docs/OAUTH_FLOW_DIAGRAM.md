# OAuth Flow Diagram - What's Happening

## 🔄 The Complete OAuth Flow

This diagram shows what happens when Claude Desktop tries to connect to your MCP server.

```
┌─────────────────┐
│ Claude Desktop  │
│ (Client)        │
└────────┬────────┘
         │
         │ 1. Connect to MCP server
         │    GET https://atomcp.kooshapari.com/api/mcp
         ▼
┌─────────────────────────────────────────────────────────┐
│ Your MCP Server (atomcp.kooshapari.com)                 │
│                                                          │
│ Returns: 401 Unauthorized                               │
│ WWW-Authenticate: Bearer realm="..."                    │
│                   resource="/.well-known/oauth-..."     │
└────────┬────────────────────────────────────────────────┘
         │
         │ 2. Fetch OAuth metadata
         │    GET https://atomcp.kooshapari.com/.well-known/oauth-protected-resource
         ▼
┌─────────────────────────────────────────────────────────┐
│ Your MCP Server                                         │
│                                                          │
│ ✅ CORS headers added (FIXED)                           │
│ Returns:                                                │
│ {                                                       │
│   "resource": "https://atomcp.kooshapari.com/api/mcp", │
│   "authorization_servers": [                            │
│     "https://authkit-...authkit.app"  ← YOUR DOMAIN    │
│   ],                                                    │
│   "scopes_supported": ["openid", "profile", "email"]   │
│ }                                                       │
└────────┬────────────────────────────────────────────────┘
         │
         │ 3. Fetch AuthKit metadata
         │    GET https://authkit-...authkit.app/.well-known/openid-configuration
         ▼
┌─────────────────────────────────────────────────────────┐
│ WorkOS AuthKit Server                                   │
│                                                          │
│ ❌ CURRENT ISSUE: Returns 404                           │
│                                                          │
│ Should return:                                          │
│ {                                                       │
│   "issuer": "https://authkit-...authkit.app",          │
│   "authorization_endpoint": ".../oauth/authorize",      │
│   "token_endpoint": ".../oauth/token",                  │
│   "registration_endpoint": ".../oauth/register",        │
│   ...                                                   │
│ }                                                       │
└────────┬────────────────────────────────────────────────┘
         │
         │ ❌ BLOCKED HERE - Can't proceed without metadata
         │
         │ 4. Register as OAuth client (DCR)
         │    POST https://authkit-...authkit.app/oauth/register
         │    {
         │      "client_name": "Claude Desktop",
         │      "redirect_uris": ["http://127.0.0.1:3000/oauth/callback"],
         │      ...
         │    }
         ▼
┌─────────────────────────────────────────────────────────┐
│ WorkOS AuthKit Server                                   │
│                                                          │
│ ❌ CURRENT ISSUE: DCR might not be enabled              │
│                                                          │
│ Should return:                                          │
│ {                                                       │
│   "client_id": "client_...",                            │
│   "client_secret": "...",                               │
│   ...                                                   │
│ }                                                       │
└────────┬────────────────────────────────────────────────┘
         │
         │ 5. Start OAuth flow
         │    Open browser to:
         │    https://authkit-...authkit.app/oauth/authorize?
         │      client_id=...&
         │      redirect_uri=http://127.0.0.1:3000/oauth/callback&
         │      response_type=code&
         │      code_challenge=...&
         │      code_challenge_method=S256
         ▼
┌─────────────────────────────────────────────────────────┐
│ User's Browser                                          │
│                                                          │
│ Shows AuthKit login page                                │
│ User enters credentials                                 │
└────────┬────────────────────────────────────────────────┘
         │
         │ 6. User logs in
         ▼
┌─────────────────────────────────────────────────────────┐
│ WorkOS AuthKit Server                                   │
│                                                          │
│ Validates credentials                                   │
│ Redirects to:                                           │
│   http://127.0.0.1:3000/oauth/callback?code=...         │
└────────┬────────────────────────────────────────────────┘
         │
         │ 7. Exchange code for token
         │    POST https://authkit-...authkit.app/oauth/token
         │    {
         │      "grant_type": "authorization_code",
         │      "code": "...",
         │      "redirect_uri": "http://127.0.0.1:3000/oauth/callback",
         │      "code_verifier": "...",
         │      "client_id": "...",
         │      "client_secret": "..."
         │    }
         ▼
┌─────────────────────────────────────────────────────────┐
│ WorkOS AuthKit Server                                   │
│                                                          │
│ Returns:                                                │
│ {                                                       │
│   "access_token": "...",                                │
│   "token_type": "Bearer",                               │
│   "expires_in": 3600,                                   │
│   "refresh_token": "...",                               │
│   "id_token": "..."                                     │
│ }                                                       │
└────────┬────────────────────────────────────────────────┘
         │
         │ 8. Connect to MCP server with token
         │    GET https://atomcp.kooshapari.com/api/mcp
         │    Authorization: Bearer <access_token>
         ▼
┌─────────────────────────────────────────────────────────┐
│ Your MCP Server                                         │
│                                                          │
│ Validates token with AuthKit                            │
│ Returns: 200 OK                                         │
│ Establishes MCP connection                              │
└────────┬────────────────────────────────────────────────┘
         │
         │ 9. MCP communication
         ▼
┌─────────────────┐
│ Claude Desktop  │
│ ✅ Connected!   │
└─────────────────┘
```

---

## 🚨 Where It's Failing Now

### Step 3: Fetch AuthKit Metadata ❌

**Request**:
```
GET https://authkit-01k4cgw2j1fgwzyzjdmvwgqzbd.authkit.app/.well-known/openid-configuration
```

**Current Response**:
```
404 Not Found
{"error": "not_found"}
```

**Expected Response**:
```json
{
  "issuer": "https://authkit-01k4cgw2j1fgwzyzjdmvwgqzbd.authkit.app",
  "authorization_endpoint": "https://authkit-01k4cgw2j1fgwzyzjdmvwgqzbd.authkit.app/oauth/authorize",
  "token_endpoint": "https://authkit-01k4cgw2j1fgwzyzjdmvwgqzbd.authkit.app/oauth/token",
  "registration_endpoint": "https://authkit-01k4cgw2j1fgwzyzjdmvwgqzbd.authkit.app/oauth/register",
  "jwks_uri": "https://authkit-01k4cgw2j1fgwzyzjdmvwgqzbd.authkit.app/oauth/jwks",
  "scopes_supported": ["openid", "profile", "email"],
  "response_types_supported": ["code"],
  "grant_types_supported": ["authorization_code", "refresh_token"],
  "code_challenge_methods_supported": ["S256"]
}
```

**Why It Fails**:
- The domain `authkit-01k4cgw2j1fgwzyzjdmvwgqzbd.authkit.app` is incorrect
- It should be something like `decent-hymn-17-staging.authkit.app`
- Find the correct domain in WorkOS Dashboard

---

## 🔍 CORS Preflight Flow

Before each request, the browser sends an OPTIONS request to check CORS:

```
┌─────────────────┐
│ Claude Desktop  │
└────────┬────────┘
         │
         │ OPTIONS https://atomcp.kooshapari.com/.well-known/oauth-protected-resource
         │ Origin: http://127.0.0.1:3000
         │ Access-Control-Request-Method: GET
         │ Access-Control-Request-Headers: mcp-protocol-version
         ▼
┌─────────────────────────────────────────────────────────┐
│ Your MCP Server                                         │
│                                                          │
│ ✅ FIXED: Now returns CORS headers                      │
│                                                          │
│ Response:                                               │
│   204 No Content                                        │
│   Access-Control-Allow-Origin: *                        │
│   Access-Control-Allow-Methods: GET,OPTIONS             │
│   Access-Control-Allow-Headers: Authorization,          │
│     Content-Type, MCP-Protocol-Version                  │
└────────┬────────────────────────────────────────────────┘
         │
         │ ✅ CORS check passed
         │
         │ Now send actual request
         │ GET https://atomcp.kooshapari.com/.well-known/oauth-protected-resource
         ▼
┌─────────────────────────────────────────────────────────┐
│ Your MCP Server                                         │
│                                                          │
│ Returns metadata with CORS headers                      │
└─────────────────────────────────────────────────────────┘
```

---

## ⚠️ Cloudflare Redirect Issue

If Cloudflare redirects HTTP to HTTPS during preflight:

```
┌─────────────────┐
│ Claude Desktop  │
└────────┬────────┘
         │
         │ OPTIONS http://atomcp.kooshapari.com/...
         ▼
┌─────────────────────────────────────────────────────────┐
│ Cloudflare                                              │
│                                                          │
│ ❌ Redirects to HTTPS                                   │
│   301 Moved Permanently                                 │
│   Location: https://atomcp.kooshapari.com/...           │
└────────┬────────────────────────────────────────────────┘
         │
         │ ❌ Browser blocks: "Redirect is not allowed for a preflight request"
         ▼
┌─────────────────┐
│ Claude Desktop  │
│ ❌ CORS Error   │
└─────────────────┘
```

**Fix**: Configure Cloudflare to use HTTPS from the start, or allow OPTIONS without redirect.

---

## 📊 Request/Response Examples

### Step 2: Fetch Protected Resource Metadata

**Request**:
```http
GET /.well-known/oauth-protected-resource HTTP/1.1
Host: atomcp.kooshapari.com
Origin: http://127.0.0.1:3000
```

**Response** (✅ FIXED):
```http
HTTP/1.1 200 OK
Content-Type: application/json
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET,OPTIONS
Access-Control-Allow-Headers: Authorization, Content-Type, MCP-Protocol-Version

{
  "resource": "https://atomcp.kooshapari.com/api/mcp",
  "authorization_servers": [
    "https://authkit-01k4cgw2j1fgwzyzjdmvwgqzbd.authkit.app"
  ],
  "scopes_supported": ["openid", "profile", "email"],
  "token_endpoint_auth_methods_supported": [
    "client_secret_post",
    "client_secret_basic"
  ]
}
```

### Step 3: Fetch AuthKit Metadata

**Request**:
```http
GET /.well-known/openid-configuration HTTP/1.1
Host: authkit-01k4cgw2j1fgwzyzjdmvwgqzbd.authkit.app
Origin: http://127.0.0.1:3000
MCP-Protocol-Version: 2024-11-05
```

**Current Response** (❌ WRONG):
```http
HTTP/1.1 404 Not Found
Content-Type: application/json

{"error": "not_found"}
```

**Expected Response**:
```http
HTTP/1.1 200 OK
Content-Type: application/json
Access-Control-Allow-Origin: *

{
  "issuer": "https://authkit-01k4cgw2j1fgwzyzjdmvwgqzbd.authkit.app",
  "authorization_endpoint": "https://authkit-01k4cgw2j1fgwzyzjdmvwgqzbd.authkit.app/oauth/authorize",
  "token_endpoint": "https://authkit-01k4cgw2j1fgwzyzjdmvwgqzbd.authkit.app/oauth/token",
  "registration_endpoint": "https://authkit-01k4cgw2j1fgwzyzjdmvwgqzbd.authkit.app/oauth/register",
  ...
}
```

---

## 🎯 What You Need to Fix

1. **Find the correct AuthKit domain** in WorkOS Dashboard
2. **Test it returns metadata**:
   ```bash
   curl https://YOUR-AUTHKIT-DOMAIN/.well-known/openid-configuration
   ```
3. **Update `.env`** with the correct domain
4. **Enable DCR** in WorkOS Dashboard
5. **Restart server** to apply CORS fixes

Once these are fixed, the flow will complete successfully! ✅

