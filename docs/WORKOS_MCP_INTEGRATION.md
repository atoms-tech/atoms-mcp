# WorkOS MCP Integration Guide

## Overview

This guide explains how your MCP server integrates with WorkOS AuthKit for authentication, based on the [official WorkOS MCP documentation](https://workos.com/docs/mcp).

## Key Concepts

### MCP Authorization Flow

The Model Context Protocol (MCP) uses OAuth 2.0 for authentication with these components:

- **Resource Server**: Your MCP server (`https://atomcp.kooshapari.com/api/mcp`)
- **Authorization Server**: WorkOS AuthKit (`https://YOUR-AUTHKIT-DOMAIN`)
- **Client**: Claude Desktop or other MCP clients

### Important Endpoints

WorkOS AuthKit provides these OAuth 2.0 endpoints for MCP:

1. **OAuth Authorization Server Metadata** (Primary for MCP):
   ```
   https://YOUR-AUTHKIT-DOMAIN/.well-known/oauth-authorization-server
   ```

2. **OpenID Configuration** (Compatibility):
   ```
   https://YOUR-AUTHKIT-DOMAIN/.well-known/openid-configuration
   ```

**Note**: MCP primarily uses OAuth 2.0 metadata, not OpenID Connect. However, some clients may request either endpoint.

---

## Current Implementation

Your MCP server (`atoms_mcp-old/server.py`) implements the WorkOS MCP integration pattern:

### 1. Protected Resource Metadata

**Endpoint**: `/.well-known/oauth-protected-resource`

**Implementation** (lines 618-655):
```python
async def _build_resource_metadata(request=None):
    authkit_domain = os.getenv("FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN")
    resource_path = os.getenv("ATOMS_FASTMCP_HTTP_PATH", "/api/mcp")
    
    # Build resource URL
    resource_url = f"{base_url}{resource_path}"
    
    metadata = {
        "resource": resource_url,
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

**What it returns**:
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

This tells MCP clients:
- Where your MCP server is located
- Which authorization server to use (AuthKit)
- What scopes are supported
- How to authenticate with the token endpoint

---

### 2. WWW-Authenticate Header

When your MCP server receives an unauthenticated request, it returns a `401 Unauthorized` with a `WWW-Authenticate` header:

```http
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Bearer error="unauthorized", 
                  error_description="Authorization needed",
                  resource_metadata="https://atomcp.kooshapari.com/.well-known/oauth-protected-resource"
```

This header tells the MCP client:
1. Authentication is required
2. Where to find the protected resource metadata
3. Which authorization server to use (discovered from metadata)

---

### 3. Compatibility Endpoints

Your server also implements compatibility endpoints for clients that don't support the latest MCP spec:

**OpenID Configuration** (lines 584-595):
```python
async def _openid_configuration_handler(request):
    if request.method == "OPTIONS":
        return _set_cors_headers(Response(status_code=204))
    
    metadata = await _build_oidc_metadata()
    if metadata is None:
        return _set_cors_headers(
            JSONResponse({"error": "OpenID configuration not available"}, status_code=404)
        )
    return _set_cors_headers(JSONResponse(metadata))
```

**OAuth Authorization Server** (lines 597-616):
```python
async def _oauth_authorization_server_handler(request):
    if request.method == "OPTIONS":
        return _set_cors_headers(Response(status_code=204))
    
    metadata = await _build_oidc_metadata()
    if metadata is None:
        return _set_cors_headers(
            JSONResponse(
                {"error": "OAuth authorization server metadata not available"},
                status_code=404,
            )
        )
    # Remove OIDC-only fields for OAuth metadata
    oauth_metadata = metadata.copy()
    oauth_metadata.pop("userinfo_endpoint", None)
    oauth_metadata.pop("id_token_signing_alg_values_supported", None)
    oauth_metadata.pop("subject_types_supported", None)
    return _set_cors_headers(JSONResponse(oauth_metadata))
```

---

## WorkOS Dashboard Configuration

### 1. Enable Dynamic Client Registration

**Required**: MCP requires OAuth 2.0 Dynamic Client Registration (RFC 7591).

**Steps**:
1. Go to https://dashboard.workos.com
2. Navigate to **Applications** → **Configuration**
3. Find **OAuth 2.0** section
4. Enable **Dynamic Client Registration**
5. Click **Save**

**What this does**:
- Allows MCP clients to self-register without prior configuration
- Enables the `/oauth2/register` endpoint
- Required for zero-config MCP client support

---

### 2. Find Your AuthKit Domain

**Location**: WorkOS Dashboard → **Authentication** → **AuthKit**

**Format**: `https://YOUR-ENVIRONMENT.authkit.app`

**Examples**:
- Staging: `https://decent-hymn-17-staging.authkit.app`
- Production: `https://decent-hymn-17.authkit.app`
- Custom: `https://auth.yourdomain.com`

**Verify it works**:
```bash
# Test OAuth 2.0 metadata (primary for MCP)
curl https://YOUR-AUTHKIT-DOMAIN/.well-known/oauth-authorization-server | jq

# Should return:
{
  "authorization_endpoint": "https://YOUR-AUTHKIT-DOMAIN/oauth2/authorize",
  "code_challenge_methods_supported": ["S256"],
  "grant_types_supported": ["authorization_code", "refresh_token"],
  "introspection_endpoint": "https://YOUR-AUTHKIT-DOMAIN/oauth2/introspection",
  "issuer": "https://YOUR-AUTHKIT-DOMAIN",
  "registration_endpoint": "https://YOUR-AUTHKIT-DOMAIN/oauth2/register",
  "scopes_supported": ["email", "offline_access", "openid", "profile"],
  "response_modes_supported": ["query"],
  "response_types_supported": ["code"],
  "token_endpoint": "https://YOUR-AUTHKIT-DOMAIN/oauth2/token",
  "token_endpoint_auth_methods_supported": [
    "none",
    "client_secret_post",
    "client_secret_basic"
  ]
}
```

---

### 3. Configure Redirect URIs

**Location**: WorkOS Dashboard → **Authentication** → **AuthKit** → **Configuration**

**Add these URIs**:
```
http://127.0.0.1:3000/oauth/callback
http://localhost:3000/oauth/callback
https://atomcp.kooshapari.com/oauth/callback
```

**Why**:
- MCP clients need to redirect back after authentication
- Different clients use different ports and protocols
- Wildcard ports may be supported: `http://127.0.0.1:*/oauth/callback`

---

## Environment Configuration

Your `.env` file should have:

```bash
# WorkOS Credentials
WORKOS_API_KEY=sk_test_...
WORKOS_CLIENT_ID=client_...

# FastMCP AuthKit Configuration
FASTMCP_SERVER_AUTH=fastmcp.server.auth.providers.workos.AuthKitProvider
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN=https://YOUR-AUTHKIT-DOMAIN
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL=https://atomcp.kooshapari.com
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_REQUIRED_SCOPES=openid,profile,email
```

**Critical**: The `AUTHKIT_DOMAIN` must match exactly what's in the WorkOS Dashboard.

---

## OAuth Flow Diagram

```
┌─────────────────┐
│ Claude Desktop  │
└────────┬────────┘
         │
         │ 1. GET /api/mcp (no auth)
         ▼
┌─────────────────────────────────────────────────────────┐
│ Your MCP Server                                         │
│ Returns: 401 Unauthorized                               │
│ WWW-Authenticate: Bearer                                │
│   resource_metadata=".../.well-known/oauth-protected-   │
│   resource"                                             │
└────────┬────────────────────────────────────────────────┘
         │
         │ 2. GET /.well-known/oauth-protected-resource
         ▼
┌─────────────────────────────────────────────────────────┐
│ Your MCP Server                                         │
│ Returns:                                                │
│ {                                                       │
│   "resource": "https://atomcp.kooshapari.com/api/mcp", │
│   "authorization_servers": [                            │
│     "https://YOUR-AUTHKIT-DOMAIN"                       │
│   ]                                                     │
│ }                                                       │
└────────┬────────────────────────────────────────────────┘
         │
         │ 3. GET /.well-known/oauth-authorization-server
         ▼
┌─────────────────────────────────────────────────────────┐
│ WorkOS AuthKit                                          │
│ Returns OAuth 2.0 metadata with:                        │
│ - authorization_endpoint                                │
│ - token_endpoint                                        │
│ - registration_endpoint (for DCR)                       │
└────────┬────────────────────────────────────────────────┘
         │
         │ 4. POST /oauth2/register (Dynamic Client Registration)
         ▼
┌─────────────────────────────────────────────────────────┐
│ WorkOS AuthKit                                          │
│ Returns:                                                │
│ {                                                       │
│   "client_id": "...",                                   │
│   "client_secret": "..."                                │
│ }                                                       │
└────────┬────────────────────────────────────────────────┘
         │
         │ 5. Redirect to /oauth2/authorize
         ▼
┌─────────────────────────────────────────────────────────┐
│ WorkOS AuthKit Login Page                               │
│ User authenticates                                      │
└────────┬────────────────────────────────────────────────┘
         │
         │ 6. Redirect to callback with code
         │ 7. POST /oauth2/token (exchange code for token)
         ▼
┌─────────────────────────────────────────────────────────┐
│ WorkOS AuthKit                                          │
│ Returns:                                                │
│ {                                                       │
│   "access_token": "...",                                │
│   "token_type": "Bearer",                               │
│   "expires_in": 3600                                    │
│ }                                                       │
└────────┬────────────────────────────────────────────────┘
         │
         │ 8. GET /api/mcp
         │    Authorization: Bearer <access_token>
         ▼
┌─────────────────────────────────────────────────────────┐
│ Your MCP Server                                         │
│ Validates token, returns MCP response                   │
└─────────────────────────────────────────────────────────┘
```

---

## Troubleshooting

### Issue: AuthKit Domain Returns 404

**Error**: `https://authkit-.../.well-known/oauth-authorization-server` returns 404

**Causes**:
1. Wrong domain in `.env` file
2. AuthKit not fully provisioned
3. Using wrong endpoint format

**Fix**:
1. Verify domain in WorkOS Dashboard
2. Test with curl: `curl https://YOUR-DOMAIN/.well-known/oauth-authorization-server`
3. Update `.env` with correct domain
4. Restart server

---

### Issue: Dynamic Client Registration Fails

**Error**: `POST /oauth2/register` returns 404 or error

**Causes**:
1. DCR not enabled in WorkOS Dashboard
2. Wrong AuthKit domain
3. Invalid registration request

**Fix**:
1. Enable DCR in WorkOS Dashboard (Applications → Configuration)
2. Verify AuthKit domain is correct
3. Test with curl:
   ```bash
   curl -X POST https://YOUR-AUTHKIT-DOMAIN/oauth2/register \
     -H "Content-Type: application/json" \
     -d '{
       "client_name": "Test Client",
       "redirect_uris": ["http://127.0.0.1:3000/oauth/callback"],
       "grant_types": ["authorization_code"],
       "response_types": ["code"]
     }'
   ```

---

## References

- **WorkOS MCP Documentation**: https://workos.com/docs/mcp
- **MCP Specification**: https://modelcontextprotocol.io/
- **OAuth 2.0 RFC**: https://datatracker.ietf.org/doc/html/rfc6749
- **Dynamic Client Registration**: https://datatracker.ietf.org/doc/html/rfc7591
- **Protected Resource Metadata**: https://datatracker.ietf.org/doc/html/draft-ietf-oauth-resource-metadata-13

