# Verification Checklist - OAuth & CORS Setup

Use this checklist to verify your MCP server is properly configured for OAuth authentication.

## 📋 Pre-Flight Checklist

### ✅ 1. WorkOS Dashboard Configuration

- [ ] **AuthKit is enabled** for your application
- [ ] **Dynamic Client Registration (DCR) is enabled**
  - Path: Applications → Configuration → OAuth 2.0 → DCR toggle
- [ ] **Redirect URIs are configured**:
  - [ ] `http://127.0.0.1:3000/oauth/callback`
  - [ ] `http://localhost:3000/oauth/callback`
  - [ ] `https://atomcp.kooshapari.com/oauth/callback`
- [ ] **You have your AuthKit domain** (e.g., `https://decent-hymn-17-staging.authkit.app`)
- [ ] **You have your WorkOS API key** (starts with `sk_test_` or `sk_live_`)
- [ ] **You have your WorkOS Client ID** (starts with `client_`)

### ✅ 2. Environment Variables

Check your `.env` file has these variables:

```bash
# Supabase (required)
- [ ] NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
- [ ] NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...

# WorkOS (required for OAuth)
- [ ] WORKOS_API_KEY=sk_test_...
- [ ] WORKOS_CLIENT_ID=client_...

# FastMCP AuthKit (required for OAuth)
- [ ] FASTMCP_SERVER_AUTH=fastmcp.server.auth.providers.workos.AuthKitProvider
- [ ] FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN=https://YOUR-AUTHKIT-DOMAIN
- [ ] FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL=https://atomcp.kooshapari.com
- [ ] FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_REQUIRED_SCOPES=openid,profile,email

# Optional (for development)
- [ ] ATOMS_FASTMCP_TRANSPORT=http
- [ ] ATOMS_FASTMCP_HOST=0.0.0.0
- [ ] ATOMS_FASTMCP_PORT=8000
```

### ✅ 3. Cloudflare Configuration

- [ ] **SSL/TLS mode** is set to **Full** or **Full (strict)**
  - Path: SSL/TLS → Overview
- [ ] **Always Use HTTPS** is enabled
  - Path: SSL/TLS → Edge Certificates
- [ ] **Cloudflare Tunnel** is configured for `atomcp.kooshapari.com`
- [ ] **No HTTP→HTTPS redirects** on OPTIONS requests (test below)

---

## 🧪 Testing Checklist

Run these tests **in order** to verify your setup.

### Test 1: AuthKit Domain

```bash
curl https://YOUR-AUTHKIT-DOMAIN/.well-known/openid-configuration
```

**Expected**:
```json
{
  "issuer": "https://YOUR-AUTHKIT-DOMAIN",
  "authorization_endpoint": "https://YOUR-AUTHKIT-DOMAIN/oauth/authorize",
  "token_endpoint": "https://YOUR-AUTHKIT-DOMAIN/oauth/token",
  "registration_endpoint": "https://YOUR-AUTHKIT-DOMAIN/oauth/register",
  ...
}
```

**Result**:
- [ ] ✅ Returns JSON with OAuth endpoints
- [ ] ❌ Returns 404 → **STOP**: Fix AuthKit domain in `.env`
- [ ] ❌ Returns error → **STOP**: Check WorkOS Dashboard

---

### Test 2: MCP Server Protected Resource

```bash
curl https://atomcp.kooshapari.com/.well-known/oauth-protected-resource
```

**Expected**:
```json
{
  "resource": "https://atomcp.kooshapari.com/api/mcp",
  "authorization_servers": ["https://YOUR-AUTHKIT-DOMAIN"],
  "scopes_supported": ["openid", "profile", "email"],
  ...
}
```

**Result**:
- [ ] ✅ Returns JSON with resource metadata
- [ ] ❌ Returns 404 → **STOP**: Server not running or wrong URL
- [ ] ❌ Returns error → **STOP**: Check server logs

---

### Test 3: CORS Headers (OPTIONS Request)

```bash
curl -X OPTIONS https://atomcp.kooshapari.com/.well-known/oauth-protected-resource \
  -H "Origin: http://127.0.0.1:3000" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: mcp-protocol-version" \
  -v 2>&1 | grep -i "access-control"
```

**Expected**:
```
< Access-Control-Allow-Origin: *
< Access-Control-Allow-Methods: GET,OPTIONS
< Access-Control-Allow-Headers: Authorization, Content-Type, MCP-Protocol-Version
```

**Result**:
- [ ] ✅ All three headers present
- [ ] ❌ Missing headers → **STOP**: Restart server (CORS fix already in code)
- [ ] ❌ HTTP redirect → **STOP**: Fix Cloudflare SSL settings

---

### Test 4: Dynamic Client Registration

```bash
curl -X POST https://YOUR-AUTHKIT-DOMAIN/oauth/register \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "Test Client",
    "redirect_uris": ["http://127.0.0.1:3000/oauth/callback"],
    "grant_types": ["authorization_code"],
    "response_types": ["code"],
    "token_endpoint_auth_method": "client_secret_basic"
  }'
```

**Expected**:
```json
{
  "client_id": "client_...",
  "client_secret": "...",
  "client_name": "Test Client",
  ...
}
```

**Result**:
- [ ] ✅ Returns client credentials
- [ ] ❌ Returns 404 → **STOP**: DCR not enabled in WorkOS
- [ ] ❌ Returns error → **STOP**: Check redirect URIs in WorkOS

---

### Test 5: No HTTP Redirects on Preflight

```bash
curl -X OPTIONS http://atomcp.kooshapari.com/.well-known/oauth-protected-resource \
  -H "Origin: http://127.0.0.1:3000" \
  -v 2>&1 | grep -i "location"
```

**Expected**:
```
(no output - no redirects)
```

**Result**:
- [ ] ✅ No Location header (no redirect)
- [ ] ❌ Shows `Location: https://...` → **STOP**: Fix Cloudflare to allow HTTP OPTIONS

---

### Test 6: MCP Server Health

```bash
curl https://atomcp.kooshapari.com/health
```

**Expected**:
```json
{
  "status": "ok",
  ...
}
```

**Result**:
- [ ] ✅ Returns health status
- [ ] ❌ Returns error → **STOP**: Server not running

---

## 🎯 Final Integration Test

### Test with Claude Desktop

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

3. **Try to connect** to Atoms MCP server

4. **Expected behavior**:
   - [ ] Claude opens browser for OAuth login
   - [ ] AuthKit login page loads
   - [ ] After login, redirects back to Claude
   - [ ] Claude shows "Connected" status
   - [ ] Can list tools from Atoms server

5. **If it fails**:
   - [ ] Check browser console for errors (Cmd+Option+I)
   - [ ] Check server logs for errors
   - [ ] Verify all tests above passed

---

## 🐛 Troubleshooting

### If Test 1 Fails (AuthKit Domain 404)

**Problem**: Wrong AuthKit domain in `.env`

**Fix**:
1. Go to https://dashboard.workos.com
2. Authentication → AuthKit → Configuration
3. Copy the **AuthKit URL** (e.g., `https://decent-hymn-17-staging.authkit.app`)
4. Update `.env`:
   ```bash
   FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN=https://YOUR-ACTUAL-DOMAIN
   ```
5. Restart server

### If Test 2 Fails (Protected Resource 404)

**Problem**: Server not running or wrong URL

**Fix**:
1. Check server is running:
   ```bash
   ps aux | grep "python -m atoms_mcp-old"
   ```
2. If not running, start it:
   ```bash
   cd /Users/kooshapari/temp-PRODVERCEL/485/clean
   python -m atoms_mcp-old.server
   ```
3. Check logs for errors

### If Test 3 Fails (CORS Headers Missing)

**Problem**: Server needs restart (CORS fix already in code)

**Fix**:
1. Kill server:
   ```bash
   pkill -f "python -m atoms_mcp-old"
   ```
2. Restart:
   ```bash
   python -m atoms_mcp-old.server
   ```
3. Re-run test

### If Test 4 Fails (DCR Not Working)

**Problem**: DCR not enabled in WorkOS

**Fix**:
1. Go to https://dashboard.workos.com
2. Applications → Configuration
3. Find **OAuth 2.0** section
4. Enable **Dynamic Client Registration**
5. Save changes
6. Re-run test

### If Test 5 Fails (HTTP Redirects)

**Problem**: Cloudflare redirecting HTTP to HTTPS on OPTIONS

**Fix**:
1. Go to Cloudflare Dashboard
2. Select domain `kooshapari.com`
3. SSL/TLS → Overview
4. Set to **Full (strict)**
5. Rules → Page Rules
6. Add rule to allow OPTIONS requests without redirect
7. Re-run test

---

## ✅ Success Criteria

All tests should pass:

- [x] Test 1: AuthKit metadata returns JSON
- [x] Test 2: Protected resource returns JSON
- [x] Test 3: CORS headers present
- [x] Test 4: DCR works
- [x] Test 5: No HTTP redirects
- [x] Test 6: Health check works
- [x] Claude Desktop connects successfully

**If all tests pass, your setup is correct!** 🎉

---

## 📚 Additional Resources

- **Quick Fix Guide**: `docs/QUICK_FIX.md`
- **CORS Troubleshooting**: `docs/CORS_TROUBLESHOOTING.md`
- **AuthKit Setup**: `docs/authkit_setup_guide.md`
- **WorkOS Docs**: https://workos.com/docs/authkit
- **FastMCP Docs**: https://github.com/jlowin/fastmcp

