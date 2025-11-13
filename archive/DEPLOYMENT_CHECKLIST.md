# Deployment Checklist - Dual Authentication Fix

## Pre-Deployment

### 1. Review Changes

- [ ] Review `services/auth/hybrid_auth_provider.py` changes
- [ ] Review `server.py` base URL resolution changes
- [ ] Verify no unintended changes were made

### 2. Local Testing

- [ ] Start server locally: `python server.py`
- [ ] Verify startup logs show correct base URL:
  ```
  🌐 AUTH BASE URL -> http://127.0.0.1:8000
  ✅ Hybrid authentication configured: OAuth + Bearer tokens
  ```
- [ ] Test OAuth discovery endpoints:
  ```bash
  curl http://localhost:8000/.well-known/oauth-protected-resource
  curl http://localhost:8000/.well-known/oauth-authorization-server
  ```
- [ ] Verify resource URL matches local server:
  ```json
  {"resource": "http://127.0.0.1:8000/", ...}
  ```

### 3. Environment Variables

#### Local (.env.local)
- [ ] `FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN` is set
- [ ] `ATOMS_FASTMCP_HOST=127.0.0.1` or `localhost`
- [ ] `ATOMS_FASTMCP_PORT=8000`
- [ ] `ATOMS_FASTMCP_TRANSPORT=http`
- [ ] **NOT SET**: `ATOMS_FASTMCP_BASE_URL`
- [ ] **NOT SET**: `FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL` (for local)

#### Production (Vercel)
- [ ] `FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN` is set
- [ ] `VERCEL_URL` is auto-set by Vercel
- [ ] Optional: `ATOMS_FASTMCP_BASE_URL=https://mcp.atoms.tech`
- [ ] Optional: `ATOMS_INTERNAL_TOKEN` for Bearer auth
- [ ] Optional: `WORKOS_CLIENT_ID` for AuthKit JWT validation

## Deployment

### 1. Commit Changes

```bash
git add services/auth/hybrid_auth_provider.py
git add server.py
git commit -m "fix: expose OAuth discovery routes and fix base URL resolution

- Add get_routes() method to HybridAuthProvider to expose OAuth discovery endpoints
- Add get_resource_metadata_url(), get_middleware(), _get_resource_url() helper methods
- Fix base URL resolution to use local URL for local dev, production URL for Vercel
- Expose resource_server_url and authorization_servers attributes from OAuth provider

Fixes:
- 404 errors on /.well-known/oauth-protected-resource
- 404 errors on /.well-known/oauth-authorization-server  
- Protected resource URL mismatch in local development
"
```

### 2. Push to Deployment Branch

```bash
git push origin working-deployment
```

### 3. Monitor Vercel Deployment

- [ ] Check Vercel dashboard for deployment status
- [ ] Wait for deployment to complete
- [ ] Check deployment logs for errors

## Post-Deployment Verification

### 1. Production OAuth Endpoints

```bash
# Test protected resource metadata
curl https://mcp.atoms.tech/.well-known/oauth-protected-resource

# Expected response:
# {
#   "resource": "https://mcp.atoms.tech/",
#   "authorization_servers": ["https://your-domain.authkit.app/"],
#   "scopes_supported": ["openid", "profile", "email"],
#   "bearer_methods_supported": ["header"]
# }

# Test authorization server metadata
curl https://mcp.atoms.tech/.well-known/oauth-authorization-server

# Expected: AuthKit metadata with issuer, authorization_endpoint, etc.
```

### 2. Test OAuth Flow with MCP Client

- [ ] Configure Claude Desktop with production MCP server URL
- [ ] Start Claude Desktop
- [ ] Verify OAuth flow initiates automatically
- [ ] Browser should open for authentication
- [ ] Complete authentication in browser
- [ ] Verify Claude Desktop connects successfully
- [ ] Test a few MCP tool calls to verify functionality

### 3. Test Bearer Token Authentication

```bash
# Test with internal bearer token
curl -X POST https://mcp.atoms.tech/api/mcp \
  -H "Authorization: Bearer YOUR_INTERNAL_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'

# Expected: 200 OK with tools list (if token is valid)
# Expected: 401 Unauthorized (if token is invalid)
```

### 4. Test atomsAgent Integration

- [ ] Deploy atomsAgent with Bearer token configured
- [ ] Verify atomsAgent can connect to MCP server
- [ ] Test atomsAgent MCP tool calls
- [ ] Check logs for successful Bearer token authentication

## Rollback Plan

If issues occur:

```bash
# Revert the commit
git revert HEAD

# Push to trigger new deployment
git push origin working-deployment
```

Or manually revert in Vercel dashboard to previous deployment.

## Success Criteria

- ✅ OAuth discovery endpoints return 200 OK
- ✅ Protected resource URL matches actual server URL
- ✅ Claude Desktop can authenticate via OAuth
- ✅ atomsAgent can authenticate via Bearer token
- ✅ Both auth methods work simultaneously
- ✅ No 404 errors in logs for OAuth endpoints
- ✅ No "resource URL mismatch" errors

## Monitoring

After deployment, monitor for:

- [ ] 404 errors on `/.well-known/*` endpoints
- [ ] OAuth flow failures
- [ ] Bearer token authentication failures
- [ ] "Protected resource URL mismatch" errors
- [ ] Increased error rates in general

Check logs:
```bash
vercel logs --follow
```

## Documentation

- [ ] Update README with OAuth setup instructions
- [ ] Document environment variables for local vs production
- [ ] Add troubleshooting guide link to main docs
- [ ] Update API documentation if needed

## Files to Review

1. `services/auth/hybrid_auth_provider.py` - OAuth route exposure
2. `server.py` - Base URL resolution logic
3. `DUAL_AUTH_SOLUTION.md` - Architecture documentation
4. `AUTH_TROUBLESHOOTING.md` - Troubleshooting guide
5. `OAUTH_FIX_SUMMARY.md` - Quick reference

## Support

If issues arise:
1. Check `AUTH_TROUBLESHOOTING.md`
2. Review Vercel logs
3. Test OAuth endpoints manually
4. Verify environment variables
5. Check WorkOS/AuthKit dashboard for OAuth errors

