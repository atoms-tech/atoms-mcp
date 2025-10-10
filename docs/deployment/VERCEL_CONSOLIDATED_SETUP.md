# Consolidated Vercel Configuration - Quick Reference

## Overview

The Atoms MCP project now uses a **single, consolidated Vercel configuration** that automatically handles both preview and production deployments based on Git branches.

## Key Changes

### Before (Old Setup)
- Separate configurations for preview and production
- Manual deployment commands required
- Hardcoded BASE_URL in vercel.json
- Deployment-specific logic in start_local_server.py

### After (New Setup)
- Single `vercel.json` for all environments
- Automatic deployment via git push
- Environment-specific URLs in Vercel dashboard
- Simplified local development script

## How It Works

### Automatic Environment Detection

Vercel automatically sets `VERCEL_ENV` based on the Git branch:

```
Git Branch          VERCEL_ENV        Domain
─────────────────────────────────────────────────────────────────
main                production        atomcp.kooshapari.com
feature/*           preview           devmcp.atoms.tech
bugfix/*            preview           devmcp.atoms.tech
hotfix/*            preview           devmcp.atoms.tech
(any other)         preview           devmcp.atoms.tech
```

### Deployment Workflow

**Production Deployment:**
```bash
git checkout main
git merge feature/my-feature
git push origin main
# → Automatically deploys to atomcp.kooshapari.com
```

**Preview Deployment:**
```bash
git checkout -b feature/my-feature
git add .
git commit -m "Add new feature"
git push origin feature/my-feature
# → Automatically deploys to devmcp.atoms.tech
```

## Configuration Files

### 1. vercel.json (Consolidated)

Location: `/Users/kooshapari/temp-PRODVERCEL/485/kush/atoms_mcp-old/vercel.json`

Key features:
- Both domains in `alias` array: `["atomcp.kooshapari.com", "devmcp.atoms.tech"]`
- No hardcoded BASE_URL
- Single build configuration for all environments

### 2. .env.preview (Documentation)

Location: `/Users/kooshapari/temp-PRODVERCEL/485/kush/atoms_mcp-old/.env.preview`

Purpose:
- Documents preview environment variables
- Serves as template for Vercel dashboard configuration
- NOT used directly by Vercel (values set in dashboard)

Key variables:
- `FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL=https://devmcp.atoms.tech`
- `PUBLIC_URL=https://devmcp.atoms.tech`
- `MCP_ENDPOINT=https://devmcp.atoms.tech/api/mcp`

### 3. .env.production (Documentation)

Location: `/Users/kooshapari/temp-PRODVERCEL/485/kush/atoms_mcp-old/.env.production`

Purpose:
- Documents production environment variables
- Serves as template for Vercel dashboard configuration
- NOT used directly by Vercel (values set in dashboard)

Key variables:
- `FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL=https://atomcp.kooshapari.com`
- `PUBLIC_URL=https://atomcp.kooshapari.com`
- `MCP_ENDPOINT=https://atomcp.kooshapari.com/api/mcp`

### 4. start_local_server.py (Simplified)

Location: `/Users/kooshapari/temp-PRODVERCEL/485/kush/atoms_mcp-old/start_local_server.py`

Changes:
- Removed `--deploy-preview` flag
- Removed deployment functions (deploy_to_vercel_preview, etc.)
- Simplified to only handle local development
- Added note to use git push for deployments

## Vercel Dashboard Configuration

### Step 1: Configure Environment Variables

Go to Vercel Dashboard → Project → Settings → Environment Variables

**For Preview Environment:**
```
Variable Name: FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL
Value: https://devmcp.atoms.tech
Environment: Preview ✓

Variable Name: PUBLIC_URL
Value: https://devmcp.atoms.tech
Environment: Preview ✓

Variable Name: MCP_ENDPOINT
Value: https://devmcp.atoms.tech/api/mcp
Environment: Preview ✓

... (add all other preview variables from .env.preview)
```

**For Production Environment:**
```
Variable Name: FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL
Value: https://atomcp.kooshapari.com
Environment: Production ✓

Variable Name: PUBLIC_URL
Value: https://atomcp.kooshapari.com
Environment: Production ✓

Variable Name: MCP_ENDPOINT
Value: https://atomcp.kooshapari.com/api/mcp
Environment: Production ✓

... (add all other production variables from .env.production)
```

### Step 2: Configure Domains

**Production Domain:**
- Domain: `atomcp.kooshapari.com`
- Git Branch: `main`
- Environment: Production

**Preview Domain:**
- Domain: `devmcp.atoms.tech`
- Git Branch: All non-production branches
- Environment: Preview

### Step 3: Set Production Branch

Go to Settings → Git → Production Branch
- Select: `main`

## Testing

### Test Production Deployment

```bash
# 1. Push to main
git checkout main
git push origin main

# 2. Wait for deployment (check Vercel dashboard)

# 3. Test health endpoint
curl https://atomcp.kooshapari.com/health

# 4. Expected response:
# {
#   "status": "healthy",
#   "environment": "production",
#   ...
# }
```

### Test Preview Deployment

```bash
# 1. Push to feature branch
git checkout -b test/preview
git push origin test/preview

# 2. Wait for deployment (check Vercel dashboard)

# 3. Test health endpoint
curl https://devmcp.atoms.tech/health

# 4. Expected response:
# {
#   "status": "healthy",
#   "environment": "preview",
#   ...
# }
```

## Migration Checklist

If you're migrating from the old setup to the new consolidated setup:

### Configuration
- [x] Update `vercel.json` with both domains in alias array
- [x] Create `.env.preview` with preview environment variables
- [x] Create `.env.production` with production environment variables
- [x] Remove deployment logic from `start_local_server.py`

### Vercel Dashboard
- [ ] Configure preview environment variables
- [ ] Configure production environment variables
- [ ] Set production branch to `main`
- [ ] Configure domain `atomcp.kooshapari.com` for production
- [ ] Configure domain `devmcp.atoms.tech` for preview

### Testing
- [ ] Test production deployment from main branch
- [ ] Test preview deployment from feature branch
- [ ] Verify correct environment variables in each environment
- [ ] Test OAuth flows in both environments

### Cleanup
- [ ] Remove old deployment scripts (if any)
- [ ] Update documentation
- [ ] Notify team of new workflow

## Benefits

1. **Simplified Workflow:** Just push to Git, no manual commands
2. **Automatic Routing:** Vercel handles domain routing based on branch
3. **Environment Isolation:** Clear separation between preview and production
4. **Single Source of Truth:** One vercel.json for all environments
5. **Better Security:** No hardcoded URLs in code
6. **Easier Maintenance:** Less configuration to manage

## Troubleshooting

### Wrong Domain After Deployment

**Problem:** Deployment goes to wrong domain (e.g., production goes to preview)

**Solution:**
- Check Settings → Git → Production Branch is set to `main`
- Verify domain configuration in Settings → Domains
- Ensure you pushed to correct branch

### Environment Variables Not Applied

**Problem:** Deployment uses wrong environment variables

**Solution:**
- Verify variables are checked for correct environment (Preview/Production)
- Redeploy after adding/changing variables
- Check Vercel logs for which environment was detected

### OAuth Redirect Issues

**Problem:** OAuth redirects to wrong URL

**Solution:**
- Ensure WorkOS has both domains configured:
  - `https://atomcp.kooshapari.com/auth/callback`
  - `https://devmcp.atoms.tech/auth/callback`
- Check `FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL` is correct for each environment
- Verify no trailing slashes in URLs

## Related Documentation

- [VERCEL_ENV_SETUP.md](./VERCEL_ENV_SETUP.md) - Detailed Vercel setup guide
- [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) - Complete deployment workflow
- [.env.preview](./.env.preview) - Preview environment variables template
- [.env.production](./.env.production) - Production environment variables template

## Support

For issues or questions:
1. Check [VERCEL_ENV_SETUP.md](./VERCEL_ENV_SETUP.md) troubleshooting section
2. Review Vercel deployment logs
3. Verify environment variables in Vercel dashboard
4. Check Git branch and production branch settings

---

**Last Updated:** 2025-10-09
**Version:** 1.0.0
**Status:** Active
