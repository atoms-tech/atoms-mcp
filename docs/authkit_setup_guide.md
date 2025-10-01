# AuthKit Setup Guide for FastMCP - CORS & OAuth Troubleshooting

## Overview

Your MCP server uses FastMCP's built-in AuthKit integration for OAuth 2.0 PKCE + DCR compliance. This guide helps you resolve CORS and authentication issues.

## 🚨 Current Issues & Solutions

### Issue 1: AuthKit Domain Returns 404 ❌

**Error**: `https://authkit-01k4cgw2j1fgwzyzjdmvwgqzbd.authkit.app/.well-known/openid-configuration` returns `{"error":"not_found"}`

**Root Cause**: The AuthKit domain format is incorrect. WorkOS AuthKit uses a different domain structure.

**Solution**:

1. **Find Your Correct AuthKit Domain**:
   - Go to [WorkOS Dashboard](https://dashboard.workos.com)
   - Navigate to **Authentication** → **AuthKit** → **Configuration**
   - Look for your **AuthKit URL** - it should be in one of these formats:
     - `https://auth.{your-app-name}.com` (custom domain)
     - `https://{environment-name}.authkit.app` (staging/production)
     - Example: `https://decent-hymn-17-staging.authkit.app`

2. **Verify the Domain Works**:
   ```bash
   # Test from your terminal (not from the sandbox)
   curl https://YOUR-AUTHKIT-DOMAIN/.well-known/openid-configuration

   # Should return JSON with issuer, authorization_endpoint, etc.
   # NOT a 404 error
   ```

3. **Update Your .env File**:
   ```bash
   # Replace the AUTHKIT_DOMAIN with your actual domain
   FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN=https://decent-hymn-17-staging.authkit.app
   ```

### Issue 2: CORS Headers Missing ✅ FIXED

**Status**: Already fixed in `server.py` with the `_set_cors_headers()` function.

The server now adds:
- `Access-Control-Allow-Origin: *`
- `Access-Control-Allow-Methods: GET,OPTIONS`
- `Access-Control-Allow-Headers: Authorization, Content-Type, MCP-Protocol-Version`

### Issue 3: Dynamic Client Registration Not Enabled

**Error**: "Cannot transition from step: client_registration"

**Solution**:

1. Go to [WorkOS Dashboard](https://dashboard.workos.com)
2. Navigate to **Applications** → **Configuration**
3. Find **OAuth 2.0** settings
4. Enable **Dynamic Client Registration (DCR)**
5. Save changes

### Issue 4: Redirect URIs Not Configured

**Solution**:

In AuthKit configuration, add these redirect URIs:
- **Local Development**: `http://127.0.0.1:3000/oauth/callback`
- **Production**: `https://atomcp.kooshapari.com/oauth/callback`
- **Claude Desktop**: `http://127.0.0.1:*/oauth/callback` (wildcard port)

## 📝 Environment Configuration

### Current Configuration (in your .env file):

```bash
# FastMCP AuthKit Configuration
FASTMCP_SERVER_AUTH=fastmcp.server.auth.providers.workos.AuthKitProvider
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN=https://authkit-01k4cgw2j1fgwzyzjdmvwgqzbd.authkit.app
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL=https://atomcp.kooshapari.com
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_REQUIRED_SCOPES=openid,profile,email
WORKOS_API_KEY=sk_test_a2V5XzAxSzRDR1cyMjJXSlFXQlI1RDdDUFczUUM3LGxDdWJmN2tNTDBjaHlRNjhUaEtsalQ0ZTMu
WORKOS_CLIENT_ID=client_01K4CGW2J1FGWZYZJDMVWGQZBD
```

### ⚠️ CRITICAL: Update Your AuthKit Domain

**The current domain `https://authkit-01k4cgw2j1fgwzyzjdmvwgqzbd.authkit.app` returns 404!**

You need to:

1. **Find your actual AuthKit domain** in the WorkOS Dashboard
2. **Update the .env file** with the correct domain:

```bash
# Example with staging domain you mentioned:
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN=https://decent-hymn-17-staging.authkit.app
```

3. **Verify it works** before proceeding:

```bash
# From your terminal (not sandbox):
curl https://decent-hymn-17-staging.authkit.app/.well-known/openid-configuration

# Should return JSON, not 404
```

## 🚀 Testing Your Server

### Start the Server

```bash
cd /path/to/your/project
python -m atoms_mcp-old.server
```

The server should start with AuthKit authentication enabled.

### Test with MCP Client

```python
from fastmcp import Client
import asyncio

async def test_oauth():
    async with Client("http://localhost:8000/api/mcp", auth="oauth") as client:
        # This will trigger the OAuth flow
        tools = await client.list_tools()
        print(f"Available tools: {len(tools)}")

asyncio.run(test_oauth())
```

## 🔍 Detailed Troubleshooting

### Step-by-Step Diagnosis

#### 1. Verify AuthKit Domain

```bash
# Test your AuthKit domain
curl -v https://YOUR-AUTHKIT-DOMAIN/.well-known/openid-configuration

# Expected: JSON response with OAuth endpoints
# If 404: Domain is wrong - check WorkOS Dashboard
```

#### 2. Check CORS Headers

```bash
# Test your MCP server's protected resource endpoint
curl -v https://atomcp.kooshapari.com/.well-known/oauth-protected-resource

# Should include:
# Access-Control-Allow-Origin: *
# Access-Control-Allow-Headers: Authorization, Content-Type, MCP-Protocol-Version
```

#### 3. Verify Dynamic Client Registration

```bash
# Test DCR endpoint
curl -X POST https://YOUR-AUTHKIT-DOMAIN/oauth/register \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "Test Client",
    "redirect_uris": ["http://127.0.0.1:3000/oauth/callback"],
    "grant_types": ["authorization_code"],
    "response_types": ["code"],
    "token_endpoint_auth_method": "client_secret_basic"
  }'

# Expected: JSON with client_id and client_secret
# If 404 or error: DCR not enabled in WorkOS
```

#### 4. Check Cloudflare/Tunnel Configuration

The errors show requests being blocked by CORS policy. Ensure:

1. **Cloudflare Tunnel** is not rewriting HTTPS to HTTP
2. **Cloudflare Workers** (if any) preserve CORS headers
3. **SSL/TLS mode** is set to "Full" or "Full (strict)"

```bash
# Check if Cloudflare is causing redirects
curl -v https://atomcp.kooshapari.com/.well-known/oauth-protected-resource 2>&1 | grep -i location

# Should NOT show HTTP redirects
```

### Common Error Messages & Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `No 'Access-Control-Allow-Origin' header` | CORS not configured | ✅ Already fixed in server.py |
| `Request header field mcp-protocol-version is not allowed` | Missing CORS header | ✅ Already fixed in server.py |
| `404 on /.well-known/openid-configuration` | Wrong AuthKit domain | Update AUTHKIT_DOMAIN in .env |
| `Cannot transition from step: client_registration` | DCR not enabled | Enable DCR in WorkOS Dashboard |
| `Redirect is not allowed for a preflight request` | HTTP→HTTPS redirect | Fix Cloudflare SSL settings |
| `The response redirected too many times` | Redirect loop | Check Cloudflare SSL mode |

### Debug Mode

Enable detailed logging:

```bash
# Set log level
export LOG_LEVEL=DEBUG

# Run server
python -m atoms_mcp-old.server

# Watch for AuthKit-related logs
```

### Testing from Claude Desktop

1. **Update your Claude config** (`~/.claude.json` or similar):

```json
{
  "mcpServers": {
    "atoms": {
      "url": "https://atomcp.kooshapari.com/api/mcp",
      "auth": "oauth"
    }
  }
}
```

2. **Restart Claude Desktop**

3. **Check Claude's logs** for detailed error messages

## 🛠️ Quick Fix Checklist

Based on your current errors, follow these steps **in order**:

### ✅ Step 1: Fix AuthKit Domain (CRITICAL)

```bash
# 1. Find your actual AuthKit domain in WorkOS Dashboard
# 2. Test it works:
curl https://YOUR-ACTUAL-AUTHKIT-DOMAIN/.well-known/openid-configuration

# 3. Update .env file:
# Replace this line:
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN=https://authkit-01k4cgw2j1fgwzyzjdmvwgqzbd.authkit.app

# With your actual domain (example):
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN=https://decent-hymn-17-staging.authkit.app
```

### ✅ Step 2: Enable DCR in WorkOS

1. Go to https://dashboard.workos.com
2. Navigate to **Applications** → **Configuration**
3. Find **OAuth 2.0 Settings**
4. Enable **Dynamic Client Registration**
5. Click **Save**

### ✅ Step 3: Configure Redirect URIs

In WorkOS AuthKit settings, add:

```
http://127.0.0.1:3000/oauth/callback
http://localhost:3000/oauth/callback
https://atomcp.kooshapari.com/oauth/callback
```

### ✅ Step 4: Fix Cloudflare SSL Settings

1. Go to Cloudflare Dashboard
2. Select your domain `kooshapari.com`
3. Navigate to **SSL/TLS** → **Overview**
4. Set encryption mode to **Full** or **Full (strict)**
5. Navigate to **SSL/TLS** → **Edge Certificates**
6. Enable **Always Use HTTPS**

### ✅ Step 5: Restart Your MCP Server

```bash
# Kill existing server
pkill -f "python -m atoms_mcp-old"

# Restart with new config
cd /Users/kooshapari/temp-PRODVERCEL/485/clean
python -m atoms_mcp-old.server
```

### ✅ Step 6: Test the Connection

```bash
# From your terminal (not sandbox):

# 1. Test AuthKit domain
curl https://YOUR-AUTHKIT-DOMAIN/.well-known/openid-configuration

# 2. Test MCP server protected resource
curl https://atomcp.kooshapari.com/.well-known/oauth-protected-resource

# 3. Test CORS headers
curl -X OPTIONS https://atomcp.kooshapari.com/.well-known/oauth-protected-resource \
  -H "Origin: http://127.0.0.1:3000" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: mcp-protocol-version" \
  -v

# Should see Access-Control-Allow-Origin: * in response
```

## ✅ What This Provides

With FastMCP AuthKit integration, you automatically get:

- ✅ **OAuth 2.0 PKCE** compliance for MCP
- ✅ **Dynamic Client Registration** (DCR)
- ✅ **Automatic token validation**
- ✅ **Session management**
- ✅ **User authentication via AuthKit**

No more custom OAuth endpoints needed - FastMCP handles everything! 🎉

## 🔄 Migration from Custom Implementation

The server has been updated to:
- ❌ Remove custom OAuth endpoints
- ❌ Remove WorkOS proxy implementation  
- ✅ Use FastMCP's built-in AuthKitProvider
- ✅ Automatic configuration via environment variables

Your existing tools and functionality remain exactly the same - only the authentication mechanism changed to use the standard FastMCP approach.