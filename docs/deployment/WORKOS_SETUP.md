# WorkOS AuthKit Configuration Guide

This guide explains how to configure WorkOS AuthKit for the Atoms MCP server across all environments.

## Overview

The Atoms MCP server uses WorkOS AuthKit environment `decent-hymn-17-staging` for OAuth authentication across a 3-tier deployment model:

```
Local Development → Dev/Preview → Production
  (CloudFlare tunnel)   (Vercel)     (Vercel)
```

**All three environments share the same WorkOS AuthKit configuration:**
- **Local Development**: `http://localhost:50002` (via CloudFlare tunnel to `https://atomcp.kooshapari.com`)
- **Dev/Preview**: `https://devmcp.atoms.tech` (Vercel auto-deploy on feature branches)
- **Production**: `https://atomcp.kooshapari.com` (Vercel auto-deploy on main branch)

## WorkOS Dashboard Configuration

### Step 1: Access WorkOS Dashboard

1. Go to [WorkOS Dashboard](https://dashboard.workos.com/)
2. Log in with your WorkOS account
3. Select your application/environment
4. Navigate to **Authentication** section

### Step 2: Configure Redirect URIs

Redirect URIs are the callback URLs where users are sent after authentication. **All three environments use the same AuthKit environment** (`decent-hymn-17-staging`).

Go to **Authentication → Redirect URIs** and add **all three** of the following:

#### Production Environment
```
https://atomcp.kooshapari.com/callback
```

#### Dev/Preview Environment
```
https://devmcp.atoms.tech/callback
```

#### Local Development Environment
```
http://localhost:50002/callback
```

**Important Notes:**
- All three URLs must be added to support seamless development → preview → production workflow
- All environments share the same WorkOS AuthKit configuration
- Only the `BASE_URL` differs between environments
- Changes may take 2-5 minutes to propagate

### Step 3: Configure CORS (Allowed Origins)

CORS settings control which domains can make OAuth requests to WorkOS from the browser.

Go to **Authentication → CORS Settings** and add **all three** of the following:

#### Production Environment
```
https://atomcp.kooshapari.com
```

#### Dev/Preview Environment
```
https://devmcp.atoms.tech
```

#### Local Development Environment
```
http://localhost:50002
```

**Important Notes:**
- All three origins must be added
- Origins must match exactly (including protocol and port)
- No trailing slashes
- Case-sensitive

### Step 4: Configure Logout Redirect URLs

Logout redirect URLs specify where users are sent after signing out.

Go to **Authentication → Logout URLs** and add the following:

#### Production Environment
```
https://atomcp.kooshapari.com/
https://atomcp.kooshapari.com/login
```

#### Dev/Preview Environment
```
https://devmcp.atoms.tech/
https://devmcp.atoms.tech/login
```

#### Local Development Environment
```
http://localhost:50002/
http://localhost:50002/login
```

### Step 5: Verify OAuth Settings

1. Go to **Authentication → Configuration**
2. Verify the AuthKit environment is `decent-hymn-17-staging`
3. Ensure the **Client ID** and **API Key** match your environment variables

### Step 6: Save and Test

1. Click **Save** after adding all URLs
2. WorkOS may take a few minutes to propagate changes
3. Test the OAuth flow (see Testing section below)

## Environment Configuration

All three environments use the same WorkOS AuthKit environment (`decent-hymn-17-staging`) but different `BASE_URL` values.

### Production Environment (.env.production)

```env
# WorkOS AuthKit Configuration
WORKOS_API_KEY=sk_test_[your-api-key]
WORKOS_CLIENT_ID=client_[your-client-id]

# FastMCP AuthKit Provider Settings
FASTMCP_SERVER_AUTH=fastmcp.server.auth.providers.workos.AuthKitProvider
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN=https://decent-hymn-17-staging.authkit.app
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL=https://atomcp.kooshapari.com
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_REQUIRED_SCOPES=openid,profile,email

# Server Configuration
ATOMS_FASTMCP_TRANSPORT=http
ATOMS_FASTMCP_PORT=8000
ATOMS_FASTMCP_HOST=0.0.0.0
ATOMS_FASTMCP_HTTP_AUTH_MODE=required
```

### Dev/Preview Environment (.env.development)

```env
# WorkOS AuthKit Configuration (same as production)
WORKOS_API_KEY=sk_test_[your-api-key]
WORKOS_CLIENT_ID=client_[your-client-id]

# FastMCP AuthKit Provider Settings
FASTMCP_SERVER_AUTH=fastmcp.server.auth.providers.workos.AuthKitProvider
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN=https://decent-hymn-17-staging.authkit.app
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL=https://devmcp.atoms.tech
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_REQUIRED_SCOPES=openid,profile,email

# Server Configuration
ATOMS_FASTMCP_TRANSPORT=http
ATOMS_FASTMCP_PORT=8000
ATOMS_FASTMCP_HOST=0.0.0.0
ATOMS_FASTMCP_HTTP_AUTH_MODE=required
```

### Local Development (.env.local)

```env
# WorkOS AuthKit Configuration (same as production)
WORKOS_API_KEY=sk_test_[your-api-key]
WORKOS_CLIENT_ID=client_[your-client-id]

# FastMCP AuthKit Provider Settings
FASTMCP_SERVER_AUTH=fastmcp.server.auth.providers.workos.AuthKitProvider
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN=https://decent-hymn-17-staging.authkit.app
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL=http://localhost:50002
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_REQUIRED_SCOPES=openid,profile,email

# Server Configuration
ATOMS_FASTMCP_TRANSPORT=http
ATOMS_FASTMCP_PORT=50002
ATOMS_FASTMCP_HOST=0.0.0.0
ATOMS_FASTMCP_HTTP_AUTH_MODE=required
```

### Key Environment Variables Explained

| Variable | Description | Value |
|----------|-------------|-------|
| `WORKOS_API_KEY` | WorkOS API key from dashboard | Same for all environments |
| `WORKOS_CLIENT_ID` | WorkOS OAuth client ID | Same for all environments |
| `FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN` | AuthKit environment domain | `https://decent-hymn-17-staging.authkit.app` (same for all) |
| `FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL` | Your server's public URL | **Environment-specific** (see above) |
| `FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_REQUIRED_SCOPES` | OAuth scopes to request | `openid,profile,email` (same for all) |

**Important**: Only `BASE_URL` changes between environments. All other WorkOS settings remain the same.

## Testing the Configuration

### Step 1: Verify WorkOS Configuration

Test that WorkOS AuthKit is accessible:

```bash
# Check OpenID configuration
curl https://decent-hymn-17-staging.authkit.app/.well-known/openid-configuration | jq

# Expected response should include:
# - issuer: "https://decent-hymn-17-staging.authkit.app"
# - authorization_endpoint
# - token_endpoint
# - userinfo_endpoint
```

### Step 2: Test Each Environment

#### Production (atomcp.kooshapari.com)

```bash
# Test authentication endpoint
curl -v https://atomcp.kooshapari.com/auth/authorize

# Expected: 302 redirect to AuthKit
```

Manual browser test:
1. Navigate to: `https://atomcp.kooshapari.com/auth/login`
2. You should be redirected to WorkOS AuthKit
3. After login, verify redirect to: `https://atomcp.kooshapari.com/callback`

#### Dev/Preview (devmcp.atoms.tech)

```bash
# Test authentication endpoint
curl -v https://devmcp.atoms.tech/auth/authorize

# Expected: 302 redirect to AuthKit
```

Manual browser test:
1. Navigate to: `https://devmcp.atoms.tech/auth/login`
2. You should be redirected to WorkOS AuthKit
3. After login, verify redirect to: `https://devmcp.atoms.tech/callback`

#### Local Development (localhost:50002)

```bash
# Start local server first
cd /Users/kooshapari/temp-PRODVERCEL/485/kush/atoms_mcp-old
python server/core.py

# Test authentication endpoint
curl -v http://localhost:50002/auth/authorize

# Expected: 302 redirect to AuthKit
```

Manual browser test:
1. Navigate to: `http://localhost:50002/auth/login`
2. You should be redirected to WorkOS AuthKit
3. After login, verify redirect to: `http://localhost:50002/callback`

## Troubleshooting

### Error: "Invalid redirect URI"

**Problem**: WorkOS rejects the redirect URI during OAuth flow.

**Solution**:
1. Double-check the exact URL in WorkOS Dashboard → Redirect URIs
2. Ensure it matches exactly (including https/http, domain, port, and path)
3. Verify all three redirect URIs are added:
   - `https://atomcp.kooshapari.com/callback`
   - `https://devmcp.atoms.tech/callback`
   - `http://localhost:50002/callback`
4. Wait a few minutes for WorkOS to propagate changes
5. Clear browser cache and try again

### Error: "CORS policy: No 'Access-Control-Allow-Origin' header"

**Problem**: Browser blocks cross-origin requests to WorkOS.

**Solution**:
1. Go to WorkOS Dashboard → CORS Settings
2. Verify all three origins are added (no trailing slash, no path):
   - `https://atomcp.kooshapari.com`
   - `https://devmcp.atoms.tech`
   - `http://localhost:50002`
3. Verify the origin exactly matches your server's URL
4. Check browser console for the exact origin being rejected

### Error: "Token validation failed"

**Problem**: JWT token cannot be verified or is invalid.

**Solution**:
1. Verify `AUTHKIT_DOMAIN` matches WorkOS issuer exactly:
   ```bash
   curl https://decent-hymn-17-staging.authkit.app/.well-known/openid-configuration | jq .issuer
   ```
2. Ensure `AUTHKIT_DOMAIN` in `.env` is `https://decent-hymn-17-staging.authkit.app`
3. Check that `BASE_URL` matches the redirect URI used during OAuth for your environment
4. Verify the token hasn't expired (check `exp` claim)

### Error: "Connection refused" or "DNS resolution failed"

**Problem**: Cannot connect to atomcp.kooshapari.com.

**Solution**:
1. Verify DNS is configured correctly:
   ```bash
   nslookup atomcp.kooshapari.com
   ```
2. Check that your tunnel/reverse proxy is running
3. Verify firewall rules allow traffic on port 443/80
4. For CloudFlare tunnel, ensure `cloudflared` is running

### Error: "Client authentication failed"

**Problem**: WorkOS rejects the client credentials.

**Solution**:
1. Verify `WORKOS_CLIENT_ID` matches WorkOS Dashboard
2. Check `WORKOS_API_KEY` is correct and not expired
3. Ensure API key has necessary permissions
4. Try regenerating the API key in WorkOS Dashboard

### OAuth Flow Hangs or Times Out

**Problem**: OAuth redirect never completes.

**Solution**:
1. Check server logs for errors
2. Verify callback URL is registered in WorkOS
3. Test with curl to isolate browser issues
4. Check that server is listening on the correct port/host
5. Verify SSL certificate is valid (for HTTPS)

## Configuration Checklist

Use this checklist when setting up authentication across all environments:

### WorkOS Dashboard (decent-hymn-17-staging environment)

#### Redirect URIs
- [ ] Add production redirect URI: `https://atomcp.kooshapari.com/callback`
- [ ] Add dev/preview redirect URI: `https://devmcp.atoms.tech/callback`
- [ ] Add local redirect URI: `http://localhost:50002/callback`

#### CORS Origins
- [ ] Add production origin: `https://atomcp.kooshapari.com`
- [ ] Add dev/preview origin: `https://devmcp.atoms.tech`
- [ ] Add local origin: `http://localhost:50002`

#### Logout URLs
- [ ] Add production logout: `https://atomcp.kooshapari.com/` and `https://atomcp.kooshapari.com/login`
- [ ] Add dev/preview logout: `https://devmcp.atoms.tech/` and `https://devmcp.atoms.tech/login`
- [ ] Add local logout: `http://localhost:50002/` and `http://localhost:50002/login`

#### Save & Propagate
- [ ] Save all changes in WorkOS Dashboard
- [ ] Wait 2-5 minutes for propagation

### Environment Variables

#### Common Settings (same for all environments)
- [ ] Set `WORKOS_API_KEY` from WorkOS Dashboard
- [ ] Set `WORKOS_CLIENT_ID` from WorkOS Dashboard
- [ ] Set `FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN=https://decent-hymn-17-staging.authkit.app`
- [ ] Set `FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_REQUIRED_SCOPES=openid,profile,email`

#### Environment-Specific BASE_URL
- [ ] **Production**: `FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL=https://atomcp.kooshapari.com`
- [ ] **Dev/Preview**: `FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL=https://devmcp.atoms.tech`
- [ ] **Local**: `FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL=http://localhost:50002`

### Testing

#### Production Environment
- [ ] Test AuthKit configuration: `curl https://decent-hymn-17-staging.authkit.app/.well-known/openid-configuration`
- [ ] Test OAuth flow: Visit `https://atomcp.kooshapari.com/auth/login`
- [ ] Verify redirect to AuthKit and back to `https://atomcp.kooshapari.com/callback`
- [ ] Verify access token is received
- [ ] Test API endpoints with authenticated token
- [ ] Test logout flow

#### Dev/Preview Environment
- [ ] Test OAuth flow: Visit `https://devmcp.atoms.tech/auth/login`
- [ ] Verify redirect to AuthKit and back to `https://devmcp.atoms.tech/callback`
- [ ] Verify access token is received
- [ ] Test API endpoints with authenticated token
- [ ] Test logout flow

#### Local Environment
- [ ] Start local server on port 50002
- [ ] Test OAuth flow: Visit `http://localhost:50002/auth/login`
- [ ] Verify redirect to AuthKit and back to `http://localhost:50002/callback`
- [ ] Verify access token is received
- [ ] Test API endpoints with authenticated token
- [ ] Test logout flow

### DNS & Infrastructure

#### Production
- [ ] Verify DNS resolves: `nslookup atomcp.kooshapari.com`
- [ ] Check server is accessible: `curl https://atomcp.kooshapari.com/health`
- [ ] Verify SSL certificate is valid
- [ ] Test from different network (not just localhost)

#### Dev/Preview
- [ ] Verify DNS resolves: `nslookup devmcp.atoms.tech`
- [ ] Check server is accessible: `curl https://devmcp.atoms.tech/health`
- [ ] Verify SSL certificate is valid

#### Local
- [ ] Verify server is running on port 50002
- [ ] Check server is accessible: `curl http://localhost:50002/health`

## Multi-Environment Setup Summary

The Atoms MCP server uses a **3-tier deployment model** with consolidated Vercel configuration:

```
Local Development → Dev/Preview → Production
  (CloudFlare tunnel)   (Vercel)     (Vercel)
```

| Environment | Domain | Deployment Method | AuthKit Domain |
|-------------|--------|------------------|----------------|
| **Local** | `http://localhost:50002` | `python start_server.py` | `https://decent-hymn-17-staging.authkit.app` |
| **Dev/Preview** | `https://devmcp.atoms.tech` | `git push origin feature-branch` | `https://decent-hymn-17-staging.authkit.app` |
| **Production** | `https://atomcp.kooshapari.com` | `git push origin main` | `https://decent-hymn-17-staging.authkit.app` |

**All environments share:**
- Same WorkOS Client ID
- Same WorkOS API Key
- Same AuthKit Domain: `https://decent-hymn-17-staging.authkit.app`
- **Different `BASE_URL`** (environment-specific, see table above)

**Key difference:** Only `BASE_URL` changes between environments. All deployments to Vercel are automatic via git push.

### Quick Reference: What Changes Per Environment

| Setting | Production | Dev/Preview | Local |
|---------|-----------|-------------|-------|
| **BASE_URL** | `https://atomcp.kooshapari.com` | `https://devmcp.atoms.tech` | `http://localhost:50002` |
| **Redirect URI** | `https://atomcp.kooshapari.com/callback` | `https://devmcp.atoms.tech/callback` | `http://localhost:50002/callback` |
| **CORS Origin** | `https://atomcp.kooshapari.com` | `https://devmcp.atoms.tech` | `http://localhost:50002` |
| **Port** | 8000 | 8000 | 50002 |
| **All other settings** | Same | Same | Same |

## Best Practices

### Security
1. **Never commit** `.env` files with real credentials to version control
2. Use **environment-specific** API keys (test for development, production for prod)
3. Enable **MFA** on your WorkOS account
4. Regularly **rotate** API keys
5. Use **HTTPS** for all production URLs

### Development
1. Use **separate WorkOS environments** for development/staging/production
2. Test OAuth flows in **incognito/private** browsing mode
3. Clear browser cache when testing configuration changes
4. Keep local `.env` separate from deployed configuration
5. Use CloudFlare tunnel for testing with real OAuth (not localhost)

### Monitoring
1. Monitor OAuth success/failure rates in WorkOS Dashboard
2. Set up alerts for authentication failures
3. Log all authentication attempts (without logging tokens)
4. Track token expiration and refresh patterns

## Additional Resources

- [WorkOS AuthKit Documentation](https://workos.com/docs/authkit)
- [WorkOS Dashboard](https://dashboard.workos.com/)
- [OAuth 2.0 Specification](https://oauth.net/2/)
- [FastMCP Authentication Guide](https://github.com/jlowin/fastmcp)
- [CloudFlare Tunnel Documentation](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)

## Support

For issues specific to:

- **WorkOS Configuration**: [WorkOS Support](https://workos.com/support) or check [WorkOS Status](https://status.workos.com/)
- **Atoms MCP Server**: Open an issue in the repository
- **DNS/Tunnel Issues**: Check your hosting provider or CloudFlare documentation
- **OAuth Protocol**: Refer to [OAuth 2.0 RFC 6749](https://tools.ietf.org/html/rfc6749)

## Revision History

- **2025-10-09**: Added atomcp.kooshapari.com configuration
- **2025-09-XX**: Initial documentation for zen.kooshapari.com
