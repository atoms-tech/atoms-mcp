# Quick Fix Guide - CORS & OAuth Issues

## 🎯 TL;DR - Do These 3 Things

### 1. Fix AuthKit Domain (5 minutes)

```bash
# Find your actual AuthKit domain in WorkOS Dashboard
# Test it works:
curl https://YOUR-AUTHKIT-DOMAIN/.well-known/openid-configuration

# If you get JSON (not 404), update .env:
nano .env

# Change this line to your actual domain:
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN=https://YOUR-ACTUAL-DOMAIN
```

### 2. Enable DCR in WorkOS (2 minutes)

1. Go to https://dashboard.workos.com
2. **Applications** → **Configuration**
3. Enable **Dynamic Client Registration**
4. Add redirect URI: `http://127.0.0.1:3000/oauth/callback`
5. Save

### 3. Restart Server (1 minute)

```bash
# Kill old server
pkill -f "python -m atoms_mcp-old"

# Start new server
cd /Users/kooshapari/temp-PRODVERCEL/485/clean
python -m atoms_mcp-old.server
```

---

## 🔍 What's Wrong?

Your errors show:

1. ❌ **AuthKit domain returns 404** → Wrong domain in .env
2. ✅ **CORS headers missing** → Already fixed in code
3. ❌ **Client registration fails** → DCR not enabled
4. ⚠️ **HTTP redirects** → Cloudflare SSL issue

---

## 📋 Detailed Steps

### Step 1: Find Your AuthKit Domain

**Current domain (WRONG)**:
```
https://authkit-01k4cgw2j1fgwzyzjdmvwgqzbd.authkit.app
```

**How to find the right one**:

1. Login to https://dashboard.workos.com
2. Go to **Authentication** → **AuthKit**
3. Look for **AuthKit URL** or **Environment URL**
4. Copy the full URL (e.g., `https://decent-hymn-17-staging.authkit.app`)

**Important**: Per WorkOS MCP docs, test the **OAuth Authorization Server** endpoint (not OpenID):
```bash
# Replace with your domain
curl https://decent-hymn-17-staging.authkit.app/.well-known/oauth-authorization-server

# ✅ Good: Returns JSON with "issuer", "authorization_endpoint", "registration_endpoint", etc.
# ❌ Bad: Returns 404 or error
```

**Note**: MCP uses OAuth 2.0 metadata, not OpenID Connect. The correct endpoint is:
- ✅ `/.well-known/oauth-authorization-server` (OAuth 2.0 - for MCP)
- ❌ `/.well-known/openid-configuration` (OpenID Connect - not used by MCP)

**Update .env**:
```bash
# Edit the file
nano .env

# Find this line:
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN=https://authkit-01k4cgw2j1fgwzyzjdmvwgqzbd.authkit.app

# Replace with your actual domain:
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN=https://decent-hymn-17-staging.authkit.app

# Save: Ctrl+O, Enter, Ctrl+X
```

### Step 2: Enable Dynamic Client Registration

1. Go to https://dashboard.workos.com
2. Click **Applications** in sidebar
3. Click **Configuration** tab
4. Scroll to **OAuth 2.0** section
5. Find **Dynamic Client Registration (DCR)**
6. Toggle it **ON** (if not already)
7. Click **Save Changes**

**Verify it worked**:
```bash
curl -X POST https://YOUR-AUTHKIT-DOMAIN/oauth/register \
  -H "Content-Type: application/json" \
  -d '{"client_name":"Test","redirect_uris":["http://127.0.0.1:3000/oauth/callback"],"grant_types":["authorization_code"],"response_types":["code"]}'

# ✅ Good: Returns JSON with client_id
# ❌ Bad: Returns 404 or error
```

### Step 3: Add Redirect URIs

In WorkOS Dashboard:

1. **Authentication** → **AuthKit** → **Configuration**
2. Find **Redirect URIs** section
3. Add these (one per line):
   ```
   http://127.0.0.1:3000/oauth/callback
   http://localhost:3000/oauth/callback
   https://atomcp.kooshapari.com/oauth/callback
   ```
4. Click **Save**

### Step 4: Fix Cloudflare SSL (Optional but Recommended)

1. Go to Cloudflare Dashboard
2. Select domain `kooshapari.com`
3. **SSL/TLS** → **Overview**
4. Set to **Full (strict)**
5. **SSL/TLS** → **Edge Certificates**
6. Enable **Always Use HTTPS**

### Step 5: Restart MCP Server

```bash
# Kill existing server
pkill -f "python -m atoms_mcp-old"

# Or if that doesn't work:
ps aux | grep "python -m atoms_mcp-old"
# Note the PID and:
kill -9 <PID>

# Start server with new config
cd /Users/kooshapari/temp-PRODVERCEL/485/clean
python -m atoms_mcp-old.server
```

---

## ✅ Verify Everything Works

### Test 1: AuthKit Metadata
```bash
curl https://YOUR-AUTHKIT-DOMAIN/.well-known/openid-configuration | jq .issuer

# Should print: "https://YOUR-AUTHKIT-DOMAIN"
```

### Test 2: MCP Server
```bash
curl https://atomcp.kooshapari.com/.well-known/oauth-protected-resource | jq .resource

# Should print: "https://atomcp.kooshapari.com/api/mcp"
```

### Test 3: CORS Headers
```bash
curl -X OPTIONS https://atomcp.kooshapari.com/.well-known/oauth-protected-resource \
  -H "Origin: http://127.0.0.1:3000" \
  -v 2>&1 | grep "Access-Control-Allow-Origin"

# Should print: Access-Control-Allow-Origin: *
```

---

## 🎉 Test with Claude Desktop

1. **Update Claude config** (`~/.claude.json` or similar):
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

3. **Try to connect** to the Atoms MCP server

4. **Expected flow**:
   - Claude opens browser for OAuth
   - You login via AuthKit
   - Claude receives token
   - Connection succeeds ✅

---

## 🐛 Still Not Working?

### Check Logs

```bash
# Server logs
python -m atoms_mcp-old.server 2>&1 | tee server.log

# Look for errors containing:
# - "AuthKit"
# - "OAuth"
# - "CORS"
```

### Check Browser Console

1. Open Claude Desktop
2. Press `Cmd+Option+I` (Mac) or `Ctrl+Shift+I` (Windows)
3. Go to **Console** tab
4. Look for red errors

### Common Issues

| Error | Fix |
|-------|-----|
| `404 on openid-configuration` | Wrong AuthKit domain in .env |
| `Cannot transition from step: client_registration` | DCR not enabled in WorkOS |
| `No 'Access-Control-Allow-Origin' header` | Restart server (already fixed in code) |
| `Redirect is not allowed for a preflight request` | Fix Cloudflare SSL settings |
| `The response redirected too many times` | Check Cloudflare SSL mode |

---

## 📚 More Help

- **Detailed troubleshooting**: See `CORS_TROUBLESHOOTING.md`
- **Full setup guide**: See `authkit_setup_guide.md`
- **WorkOS docs**: https://workos.com/docs/authkit
- **FastMCP docs**: https://github.com/jlowin/fastmcp

---

## 🔑 Key Points

1. **The CORS fixes are already in the code** - you just need to restart the server
2. **The main blocker is the AuthKit domain** - it must return valid metadata
3. **DCR must be enabled** - check WorkOS Dashboard
4. **Cloudflare can interfere** - make sure SSL is configured correctly

**Once you fix the AuthKit domain, everything else should work!**

