# Vercel Environment Variables Setup Guide

This guide walks you through setting up environment variables in Vercel for both production and preview environments, ensuring your application works correctly across different deployment contexts.

## Consolidated Configuration Overview

**The Atoms MCP project now uses a single, consolidated Vercel configuration that automatically handles both production and preview deployments:**

### Key Features:
- **Single `vercel.json`** - One configuration file for all environments
- **Automatic environment detection** - Vercel uses `VERCEL_ENV` to determine the environment
- **Git branch mapping:**
  - `main` branch → production (`atomcp.kooshapari.com`)
  - All other branches → preview (`devmcp.atoms.tech`)
- **No manual deployment commands** - Just push to Git
- **Environment-specific variables** - Configured in Vercel dashboard, not hardcoded

### How It Works:
```
Git Push → Branch Detection → Environment Selection → Domain Routing

main branch          →  VERCEL_ENV=production  →  atomcp.kooshapari.com
feature/* branches   →  VERCEL_ENV=preview     →  devmcp.atoms.tech
```

## Table of Contents

1. [Vercel Dashboard Setup](#vercel-dashboard-setup)
2. [Required Environment Variables](#required-environment-variables)
3. [Git Workflow](#git-workflow)
4. [Domain Setup](#domain-setup)
5. [Testing the Deployment](#testing-the-deployment)
6. [Troubleshooting](#troubleshooting)

---

## 1. Vercel Dashboard Setup

### Accessing Environment Variables

1. **Navigate to your project:**
   - Go to [vercel.com](https://vercel.com)
   - Select your project from the dashboard

2. **Open Settings:**
   - Click on the "Settings" tab at the top of your project page

3. **Find Environment Variables:**
   - In the left sidebar, click on "Environment Variables"
   - This is where you'll configure all variables for different environments

### UI Overview

The Environment Variables page has three main sections:

- **Variable Name field:** Enter the name of your environment variable (e.g., `PUBLIC_URL`)
- **Value field:** Enter the value for the variable
- **Environment checkboxes:** Select which environments should use this variable:
  - **Production:** Variables used when deploying from your production branch (usually `main`)
  - **Preview:** Variables used for preview deployments (all other branches)
  - **Development:** Variables used for local development (optional)

### Setting Variables for Specific Environments

**Method 1: Single Variable, Multiple Environments (Same Value)**
- Enter the variable name and value
- Check all applicable environments (Production, Preview, Development)
- Click "Add" or "Save"

**Method 2: Single Variable, Different Values per Environment**
- First, add the variable for Production:
  - Enter name: `PUBLIC_URL`
  - Enter value: `https://atomcp.kooshapari.com`
  - Check only "Production"
  - Click "Add"
- Then, add the same variable for Preview:
  - Enter name: `PUBLIC_URL`
  - Enter value: `https://devmcp.atoms.tech`
  - Check only "Preview"
  - Click "Add"

**Important Notes:**
- Variables are case-sensitive
- Changes to environment variables require a new deployment to take effect
- You can edit or delete variables at any time from the same page

---

## 2. Required Environment Variables

### Shared Variables (All Environments)

These variables should have the **same value** across Production, Preview, and Development. Set them once and check all three environment checkboxes.

| Variable Name | Description | Where to Find |
|--------------|-------------|---------------|
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key for server-side operations | Supabase Dashboard > Project Settings > API |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anonymous key for client-side operations | Supabase Dashboard > Project Settings > API |
| `NEXT_PUBLIC_SUPABASE_URL` | Your Supabase project URL | Supabase Dashboard > Project Settings > API |
| `GOOGLE_CLOUD_PROJECT` | Google Cloud project ID | Google Cloud Console > Project Info |
| `GOOGLE_CLOUD_LOCATION` | Google Cloud region (e.g., `us-central1`) | Based on your GCP setup |
| `FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN` | WorkOS AuthKit domain | WorkOS Dashboard > Configuration |
| `FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_REQUIRED_SCOPES` | OAuth scopes required (e.g., `openid profile email`) | Your OAuth configuration |

**Setup Steps:**
1. For each variable above, enter the name and value
2. Check "Production", "Preview", and "Development"
3. Click "Add"

### Production-Specific Variables

These variables should **only** be used in production deployments. Check only the "Production" checkbox.

| Variable Name | Value | Description |
|--------------|-------|-------------|
| `FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL` | `https://atomcp.kooshapari.com` | Base URL for OAuth callbacks in production |
| `PUBLIC_URL` | `https://atomcp.kooshapari.com` | Public-facing URL for production |

**Setup Steps:**
1. Enter variable name: `FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL`
2. Enter value: `https://atomcp.kooshapari.com`
3. Check **only** "Production"
4. Click "Add"
5. Repeat for `PUBLIC_URL`

### Preview-Specific Variables

These variables should **only** be used in preview deployments. Check only the "Preview" checkbox.

| Variable Name | Value | Description |
|--------------|-------|-------------|
| `FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL` | `https://devmcp.atoms.tech` | Base URL for OAuth callbacks in preview |
| `PUBLIC_URL` | `https://devmcp.atoms.tech` | Public-facing URL for preview |

**Setup Steps:**
1. Enter variable name: `FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL`
2. Enter value: `https://devmcp.atoms.tech`
3. Check **only** "Preview"
4. Click "Add"
5. Repeat for `PUBLIC_URL`

### Complete Environment Variables Checklist

After setup, you should have:

- [ ] 7 shared variables (checked for Production, Preview, Development)
- [ ] 2 production-specific variables (checked only for Production)
- [ ] 2 preview-specific variables (checked only for Preview)
- [ ] Total: 11 environment variable entries in Vercel

---

## 3. Git Workflow

Vercel automatically determines which environment to use based on the branch you push to.

### Branch-to-Environment Mapping

```
main branch → Production Environment
├─ Uses: Production environment variables
└─ Deploys to: https://atomcp.kooshapari.com

any other branch → Preview Environment
├─ Uses: Preview environment variables
└─ Deploys to: https://devmcp.atoms.tech (or vercel auto-generated URL)
```

### How Vercel Uses VERCEL_ENV

Vercel automatically sets the `VERCEL_ENV` environment variable:
- `VERCEL_ENV=production` when deploying from `main`
- `VERCEL_ENV=preview` when deploying from any other branch
- `VERCEL_ENV=development` when running locally with `vercel dev`

You can use this in your code to conditionally execute logic:

```javascript
// Example usage in your code
if (process.env.VERCEL_ENV === 'production') {
  // Production-specific logic
  console.log('Running in production');
} else if (process.env.VERCEL_ENV === 'preview') {
  // Preview-specific logic
  console.log('Running in preview');
}
```

### Deployment Workflow

**For Production Deployments:**
```bash
git checkout main
git add .
git commit -m "Your commit message"
git push origin main
```
- Vercel automatically detects the push
- Builds and deploys to production
- Uses production environment variables
- Available at https://atomcp.kooshapari.com

**For Preview Deployments:**
```bash
git checkout -b feature/my-new-feature
git add .
git commit -m "Your commit message"
git push origin feature/my-new-feature
```
- Vercel automatically detects the push
- Builds and deploys to preview
- Uses preview environment variables
- Available at https://devmcp.atoms.tech (plus auto-generated Vercel URLs)

### Setting Production Branch

To ensure Vercel knows which branch is production:

1. Go to Project Settings > Git
2. Under "Production Branch", select `main`
3. Click "Save"

Now only pushes to `main` will trigger production deployments.

---

## 4. Domain Setup

### Production Domain: atomcp.kooshapari.com

**Step 1: Add Domain in Vercel**
1. Go to your project in Vercel
2. Click "Settings" → "Domains"
3. Enter `atomcp.kooshapari.com` in the domain field
4. Click "Add"
5. Select "Production" as the Git branch

**Step 2: Configure DNS**

Add the following DNS record at your domain registrar (e.g., GoDaddy, Namecheap, Cloudflare):

```
Type:  CNAME
Name:  atomcp (or atomcp.kooshapari)
Value: cname.vercel-dns.com
TTL:   Auto or 3600
```

**Alternative: A Record (if CNAME doesn't work)**
```
Type:  A
Name:  atomcp (or atomcp.kooshapari)
Value: 76.76.21.21
TTL:   Auto or 3600
```

**Step 3: Verify**
- Vercel will automatically verify the domain (may take up to 48 hours)
- Once verified, a green checkmark will appear
- Your site will be accessible at https://atomcp.kooshapari.com

### Preview Domain: devmcp.atoms.tech

**Step 1: Add Domain in Vercel**
1. Go to your project in Vercel
2. Click "Settings" → "Domains"
3. Enter `devmcp.atoms.tech` in the domain field
4. Click "Add"
5. **Important:** Select "Preview" or assign it to a specific branch (not `main`)

**Step 2: Configure DNS**

Add the following DNS record at your domain registrar:

```
Type:  CNAME
Name:  devmcp (or devmcp.atoms)
Value: cname.vercel-dns.com
TTL:   Auto or 3600
```

**Alternative: A Record**
```
Type:  A
Name:  devmcp (or devmcp.atoms)
Value: 76.76.21.21
TTL:   Auto or 3600
```

**Step 3: Configure Branch Alias (Optional)**

To ensure preview deployments always use this domain:
1. In Vercel, go to Settings → Domains
2. Click on `devmcp.atoms.tech`
3. Under "Git Branch", select the branch you want (or leave as "All non-production branches")
4. Save

### Domain Configuration Checklist

- [ ] `atomcp.kooshapari.com` added and verified in Vercel
- [ ] `atomcp.kooshapari.com` assigned to Production branch
- [ ] DNS CNAME record created for `atomcp.kooshapari.com`
- [ ] `devmcp.atoms.tech` added and verified in Vercel
- [ ] `devmcp.atoms.tech` assigned to Preview deployments
- [ ] DNS CNAME record created for `devmcp.atoms.tech`
- [ ] SSL certificates automatically provisioned by Vercel

---

## 5. Testing the Deployment

### Testing Production (atomcp.kooshapari.com)

**Step 1: Basic Connectivity**
```bash
# Test if the domain resolves
curl -I https://atomcp.kooshapari.com

# Expected: HTTP/2 200 OK (or 301/302 redirect)
```

**Step 2: Verify Environment Variables**

Add a test API route in your project (temporary, for testing):

```javascript
// pages/api/test-env.js
export default function handler(req, res) {
  res.status(200).json({
    environment: process.env.VERCEL_ENV,
    publicUrl: process.env.PUBLIC_URL,
    baseUrl: process.env.FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL,
    supabaseUrl: process.env.NEXT_PUBLIC_SUPABASE_URL,
  });
}
```

Visit: https://atomcp.kooshapari.com/api/test-env

Expected response:
```json
{
  "environment": "production",
  "publicUrl": "https://atomcp.kooshapari.com",
  "baseUrl": "https://atomcp.kooshapari.com",
  "supabaseUrl": "https://your-project.supabase.co"
}
```

**Step 3: Test OAuth Flow**

1. Navigate to https://atomcp.kooshapari.com
2. Click "Sign In" or "Login"
3. Complete the OAuth flow
4. Verify you're redirected back to https://atomcp.kooshapari.com (not localhost or preview domain)
5. Check that authentication succeeds

**Common Issues:**
- **OAuth redirect mismatch:** Ensure your OAuth provider (WorkOS) has `https://atomcp.kooshapari.com/api/auth/callback` whitelisted
- **Mixed content errors:** Check that all resources load via HTTPS

### Testing Preview (devmcp.atoms.tech)

**Step 1: Create a Test Branch**
```bash
git checkout -b test/preview-deployment
git push origin test/preview-deployment
```

**Step 2: Find the Deployment**
1. Go to Vercel dashboard → Deployments
2. Find the deployment for `test/preview-deployment`
3. Note the auto-generated URL (e.g., `your-project-git-test-preview-deployment.vercel.app`)
4. Also accessible at https://devmcp.atoms.tech

**Step 3: Basic Connectivity**
```bash
# Test both URLs
curl -I https://devmcp.atoms.tech
curl -I https://your-project-git-test-preview-deployment.vercel.app
```

**Step 4: Verify Environment Variables**

Visit: https://devmcp.atoms.tech/api/test-env

Expected response:
```json
{
  "environment": "preview",
  "publicUrl": "https://devmcp.atoms.tech",
  "baseUrl": "https://devmcp.atoms.tech",
  "supabaseUrl": "https://your-project.supabase.co"
}
```

**Step 5: Test OAuth Flow**

1. Navigate to https://devmcp.atoms.tech
2. Click "Sign In" or "Login"
3. Complete the OAuth flow
4. Verify you're redirected back to https://devmcp.atoms.tech
5. Check that authentication succeeds

**Common Issues:**
- **OAuth redirect mismatch:** Ensure your OAuth provider has `https://devmcp.atoms.tech/api/auth/callback` whitelisted
- **Wrong environment variables:** Double-check that preview variables are set correctly in Vercel

### Testing Checklist

- [ ] Production URL (atomcp.kooshapari.com) is accessible
- [ ] Production environment variables are correct
- [ ] Production OAuth flow works end-to-end
- [ ] Preview URL (devmcp.atoms.tech) is accessible
- [ ] Preview environment variables are correct
- [ ] Preview OAuth flow works end-to-end
- [ ] Deployments from `main` go to production
- [ ] Deployments from other branches go to preview

---

## 6. Troubleshooting

### Environment Variables Not Working

**Problem:** Environment variables are not being used in deployment.

**Solutions:**
1. **Redeploy after changes:**
   - Environment variable changes require a new deployment
   - Go to Deployments → Latest Deployment → Click "⋯" → "Redeploy"

2. **Check environment selection:**
   - Ensure variables are checked for the correct environment (Production/Preview)
   - Verify you're testing the correct deployment URL

3. **Clear cache:**
   - Sometimes Vercel caches old builds
   - Try: Settings → General → "Clear Build Cache" → Redeploy

### OAuth Redirect Issues

**Problem:** OAuth redirects to wrong URL or fails.

**Solutions:**
1. **Update OAuth provider:**
   - Add both domains to your OAuth provider's allowed callback URLs:
     - `https://atomcp.kooshapari.com/api/auth/callback`
     - `https://devmcp.atoms.tech/api/auth/callback`

2. **Check BASE_URL variable:**
   - Ensure `FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL` is set correctly for each environment
   - Verify no trailing slashes

3. **Test environment detection:**
   - Add logging to see which environment is detected:
   ```javascript
   console.log('VERCEL_ENV:', process.env.VERCEL_ENV);
   console.log('BASE_URL:', process.env.FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL);
   ```

### Domain Not Resolving

**Problem:** Custom domain shows "Domain not found" or doesn't load.

**Solutions:**
1. **Wait for DNS propagation:**
   - DNS changes can take up to 48 hours
   - Check status: `nslookup atomcp.kooshapari.com`

2. **Verify DNS records:**
   - Ensure CNAME points to `cname.vercel-dns.com`
   - No extra records conflicting (like duplicate A records)

3. **Check Vercel domain status:**
   - Go to Settings → Domains in Vercel
   - Look for verification checkmark
   - If showing error, follow Vercel's instructions

### Build Failures

**Problem:** Deployment builds fail in Vercel but work locally.

**Solutions:**
1. **Check build logs:**
   - Go to Deployments → Failed Deployment → Click to view logs
   - Look for specific error messages

2. **Environment variable issues:**
   - Ensure all required variables are set
   - Check for typos in variable names

3. **Node version mismatch:**
   - Specify Node version in `package.json`:
   ```json
   {
     "engines": {
       "node": "18.x"
     }
   }
   ```

4. **Missing dependencies:**
   - Ensure all dependencies are in `package.json`
   - Run `npm install` and commit any changes

### Preview Domain Not Using Correct Variables

**Problem:** Preview deployments use production variables or vice versa.

**Solutions:**
1. **Double-check environment selection:**
   - Review each variable in Settings → Environment Variables
   - Ensure checkboxes are correct (Production vs Preview)

2. **Verify branch:**
   - Confirm you're not accidentally pushing to `main`
   - Check: Settings → Git → Production Branch setting

3. **Clear and re-add variables:**
   - If issues persist, delete and re-add the problematic variables
   - Ensure you click "Add" after entering each one

### Getting Help

If you're still experiencing issues:

1. **Check Vercel Status:** https://www.vercel-status.com/
2. **Vercel Documentation:** https://vercel.com/docs
3. **Vercel Support:** https://vercel.com/support
4. **Community Forum:** https://github.com/vercel/vercel/discussions

---

## Summary

You've successfully set up:

1. Environment variables for production and preview environments
2. Git workflow that automatically deploys to the correct environment
3. Custom domains for both production and preview
4. Testing procedures to verify everything works

Your deployment pipeline should now work as follows:

```
Push to main
    ↓
Production Deployment
    ↓
Uses Production Environment Variables
    ↓
Deploys to https://atomcp.kooshapari.com

Push to any other branch
    ↓
Preview Deployment
    ↓
Uses Preview Environment Variables
    ↓
Deploys to https://devmcp.atoms.tech
```

Remember to always test OAuth flows in both environments after making changes to ensure your authentication works correctly across all deployments.
