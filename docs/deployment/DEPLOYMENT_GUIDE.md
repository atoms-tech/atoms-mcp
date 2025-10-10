# Deployment Guide: 3-Tier Workflow

**Comprehensive guide for deploying Atoms MCP Server across Local → Dev → Production environments**

---

## Table of Contents

1. [Overview](#overview)
2. [Deployment Tiers](#deployment-tiers)
3. [Environment Configuration](#environment-configuration)
4. [WorkOS Configuration](#workos-configuration)
5. [Deployment Workflows](#deployment-workflows)
6. [Testing Matrix](#testing-matrix)
7. [CI/CD Integration](#cicd-integration)
8. [Monitoring & Rollback](#monitoring--rollback)
9. [Troubleshooting](#troubleshooting)

---

## Overview

The Atoms MCP Server uses a 3-tier deployment architecture to ensure reliable, tested deployments:

```
Local Development → Dev/Preview → Production
   (localhost)        (Vercel)      (Vercel)
```

### Key Principles

- **Test locally first** - All changes tested on localhost before deployment
- **Preview before production** - Use dev environment for integration testing
- **Git-based deployments** - Push to main → production, push to any branch → preview
- **Automatic environment detection** - Vercel uses VERCEL_ENV to determine environment
- **Stateless architecture** - No session storage, serverless-ready
- **Shared authentication** - Same WorkOS AuthKit across all tiers

---

## Deployment Tiers

### 1. Local Development

**Purpose:** Development, debugging, and initial testing

| Property | Value |
|----------|-------|
| **URL** | `http://localhost:50002` |
| **Public URL** | `https://atomcp.kooshapari.com` (via CloudFlare tunnel) |
| **MCP Endpoint** | `http://localhost:50002/api/mcp` |
| **Public MCP** | `https://atomcp.kooshapari.com/api/mcp` |
| **Environment** | Local machine (development) |
| **Auth Required** | Yes (WorkOS AuthKit via tunnel) |
| **Database** | Supabase (shared with all tiers) |

**Characteristics:**
- Runs on your local machine
- CloudFlare tunnel provides HTTPS for OAuth
- Fast iteration and debugging
- Full access to logs and debugging tools
- Uses local `.env` file

### 2. Dev/Preview

**Purpose:** Integration testing, PR previews, stakeholder review

| Property | Value |
|----------|-------|
| **URL** | `https://devmcp.atoms.tech` |
| **MCP Endpoint** | `https://devmcp.atoms.tech/api/mcp` |
| **Environment** | Vercel (preview) |
| **Auth Required** | Yes (WorkOS AuthKit) |
| **Database** | Supabase (shared with all tiers) |
| **Deployment** | Automatic on PR or manual |

**Characteristics:**
- Deployed to Vercel preview environment
- Automatic deployment on any non-main branch push
- Shared by team for testing
- Production-like environment
- Uses Vercel environment variables (VERCEL_ENV=preview)
- Domain automatically routed to devmcp.atoms.tech

### 3. Production

**Purpose:** Live production environment for end users

| Property | Value |
|----------|-------|
| **URL** | `https://atomcp.kooshapari.com` |
| **MCP Endpoint** | `https://atomcp.kooshapari.com/api/mcp` |
| **Environment** | Vercel (production) |
| **Auth Required** | Yes (WorkOS AuthKit) |
| **Database** | Supabase (shared with all tiers) |
| **Deployment** | Manual promotion from dev |

**Characteristics:**
- Deployed to Vercel production
- Automatic deployment from main branch
- High availability and performance
- Monitoring and alerting enabled
- Uses Vercel environment variables (VERCEL_ENV=production)
- Domain automatically routed to atomcp.kooshapari.com

---

## Environment Configuration

### Vercel Environment Variable Configuration

Vercel automatically manages environment variables based on VERCEL_ENV. Configure them in the Vercel dashboard:

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Select your project
3. Go to Settings → Environment Variables
4. Add variables for each environment:

**Preview Environment (VERCEL_ENV=preview):**
```
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL=https://devmcp.atoms.tech
PUBLIC_URL=https://devmcp.atoms.tech
MCP_ENDPOINT=https://devmcp.atoms.tech/api/mcp
WORKOS_API_KEY=<staging key>
WORKOS_CLIENT_ID=<staging client>
... (other variables)
```

**Production Environment (VERCEL_ENV=production):**
```
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL=https://atomcp.kooshapari.com
PUBLIC_URL=https://atomcp.kooshapari.com
MCP_ENDPOINT=https://atomcp.kooshapari.com/api/mcp
WORKOS_API_KEY=<production key>
WORKOS_CLIENT_ID=<production client>
... (other variables)
```

**Note:** The `.env.preview` and `.env.production` files in the repository serve as documentation and templates. The actual values are managed in Vercel dashboard for security.

### Local Environment (`.env`)

Create a `.env` file in the project root:

```env
# Server Configuration
ATOMS_FASTMCP_TRANSPORT=http
ATOMS_FASTMCP_HOST=127.0.0.1
ATOMS_FASTMCP_PORT=50002
ATOMS_FASTMCP_HTTP_AUTH_MODE=required
ATOMS_LOCAL_PORT=50002
ATOMS_USE_LOCAL_SERVER=true

# KInfra Configuration (for CloudFlare tunnel)
PORT=50002
SRVC=atoms-mcp
TUNNEL_DOMAIN=kooshapari.com
ENABLE_TUNNEL=true
PUBLIC_URL=https://atomcp.kooshapari.com

# WorkOS AuthKit - Shared across all environments
WORKOS_API_KEY=sk_test_YOUR_API_KEY
WORKOS_CLIENT_ID=client_YOUR_CLIENT_ID
FASTMCP_SERVER_AUTH=fastmcp.server.auth.providers.workos.AuthKitProvider
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN=https://decent-hymn-17-staging.authkit.app
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL=https://atomcp.kooshapari.com
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_REQUIRED_SCOPES=openid,profile,email

# Supabase - Shared database for all environments
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Google Cloud (Optional - for Vertex AI embeddings)
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_CLOUD_LOCATION=us-central1
VERTEX_EMBEDDINGS_MODEL=gemini-embedding-001

# Logging
LOG_LEVEL=INFO
NX_DAEMON=false

# MCP Session Configuration
MCP_SESSION_TTL_HOURS=24
```

### Dev/Preview Environment (`.env.preview`)

Create a `.env.preview` file or configure in Vercel dashboard:

```env
# Server Configuration
ATOMS_FASTMCP_TRANSPORT=http
ATOMS_FASTMCP_HTTP_PATH=/api/mcp

# WorkOS AuthKit - Same as local
WORKOS_API_KEY=sk_test_YOUR_API_KEY
WORKOS_CLIENT_ID=client_YOUR_CLIENT_ID
FASTMCP_SERVER_AUTH=fastmcp.server.auth.providers.workos.AuthKitProvider
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN=https://decent-hymn-17-staging.authkit.app
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL=https://devmcp.atoms.tech
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_REQUIRED_SCOPES=openid,profile,email

# Supabase - Same as local
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Google Cloud
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_CLOUD_LOCATION=us-central1

# Vercel Configuration
VERCEL=1
VERCEL_ENV=preview
VERCEL_TARGET_ENV=preview

# Logging
LOG_LEVEL=INFO
```

### Production Environment (`.env.production`)

Create a `.env.production` file or configure in Vercel dashboard:

```env
# Server Configuration
ATOMS_FASTMCP_TRANSPORT=http
ATOMS_FASTMCP_HTTP_PATH=/api/mcp

# WorkOS AuthKit - Same client, production base URL
WORKOS_API_KEY=sk_live_YOUR_PRODUCTION_API_KEY
WORKOS_CLIENT_ID=client_YOUR_CLIENT_ID
FASTMCP_SERVER_AUTH=fastmcp.server.auth.providers.workos.AuthKitProvider
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN=https://decent-hymn-17-staging.authkit.app
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL=https://atomcp.kooshapari.com
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_REQUIRED_SCOPES=openid,profile,email

# Supabase - Consider separate production database
NEXT_PUBLIC_SUPABASE_URL=https://your-production-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-production-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-production-service-role-key

# Google Cloud
GOOGLE_CLOUD_PROJECT=your-production-gcp-project-id
GOOGLE_CLOUD_LOCATION=us-central1

# Vercel Configuration
VERCEL=1
VERCEL_ENV=production
VERCEL_TARGET_ENV=production

# Logging
LOG_LEVEL=WARNING
```

---

## WorkOS Configuration

All three environments share the same WorkOS AuthKit environment (`decent-hymn-17-staging`) but use different redirect URIs.

### Required Redirect URIs

Configure all three redirect URIs in [WorkOS Dashboard](https://dashboard.workos.com/) → Authentication → Redirect URIs:

```
https://atomcp.kooshapari.com/callback
https://atomcp.kooshapari.com/auth/callback
https://atomcp.kooshapari.com/api/mcp/auth/callback
https://devmcp.atoms.tech/callback
https://devmcp.atoms.tech/auth/callback
https://devmcp.atoms.tech/api/mcp/auth/callback
http://localhost:50002/callback
http://localhost:50002/auth/callback
http://localhost:50002/api/mcp/auth/callback
```

### Required Allowed Origins (CORS)

Configure all three origins in WorkOS Dashboard → Authentication → CORS Settings:

```
https://atomcp.kooshapari.com
https://devmcp.atoms.tech
http://localhost:50002
```

**Important:**
- No trailing slashes
- Must match exactly (including protocol and port)
- Case-sensitive

### Logout Redirect URLs

Configure in WorkOS Dashboard → Authentication → Logout URLs:

```
https://atomcp.kooshapari.com/
https://atomcp.kooshapari.com/login
https://devmcp.atoms.tech/
https://devmcp.atoms.tech/login
http://localhost:50002/
http://localhost:50002/login
```

### Configuration Summary

| Environment | Base URL | AuthKit Domain | Client ID |
|-------------|----------|----------------|-----------|
| **Local** | `https://atomcp.kooshapari.com` | `https://decent-hymn-17-staging.authkit.app` | Same for all |
| **Dev** | `https://devmcp.atoms.tech` | `https://decent-hymn-17-staging.authkit.app` | Same for all |
| **Production** | `https://atomcp.kooshapari.com` | `https://decent-hymn-17-staging.authkit.app` | Same for all |

**Note:** Local and Production share the same domain because local uses CloudFlare tunnel.

---

## Deployment Workflows

### Workflow 1: Local Development

**Use Case:** Developing new features, fixing bugs, initial testing

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your credentials

# 3. Start local server with CloudFlare tunnel
python start_server.py

# Output:
# ======================================================================
#   Atoms MCP Local Server Startup
#   (CloudFlare tunnel required for OAuth)
# ======================================================================
#
# Port: 50002
#
# Starting CloudFlare tunnel...
# Tunnel URL: https://atomcp.kooshapari.com
# MCP Endpoint: https://atomcp.kooshapari.com/api/mcp
#
# ----------------------------------------------------------------------
#   Server Configuration
# ----------------------------------------------------------------------
#   Local URL:     http://localhost:50002
#   MCP Endpoint:  http://localhost:50002/api/mcp
#   Public URL:    https://atomcp.kooshapari.com
#   Public MCP:    https://atomcp.kooshapari.com/api/mcp
#   Domain:        atomcp.kooshapari.com
# ----------------------------------------------------------------------

# 4. Run tests
pytest -m unit                    # Fast unit tests only
pytest -m integration             # Integration tests (requires server running)
pytest -n auto                    # Run tests in parallel

# 5. Test specific functionality
curl http://localhost:50002/health
curl https://atomcp.kooshapari.com/health

# 6. Stop server
# Press Ctrl+C
```

**Without CloudFlare Tunnel (OAuth won't work):**

```bash
python start_server.py --no-tunnel
# WARNING: OAuth will not work without HTTPS
```

### Workflow 2: Deploy to Dev/Preview

**Use Case:** Testing on production-like environment, sharing with team, PR previews

#### Automatic Deployment (via Git Push)

```bash
# 1. Create a new branch (any branch except main)
git checkout -b feature/new-feature

# 2. Make changes and commit
git add .
git commit -m "Add new feature"

# 3. Push to GitHub
git push origin feature/new-feature

# → Vercel automatically detects VERCEL_ENV=preview and deploys to devmcp.atoms.tech

# 4. Test preview deployment
curl https://devmcp.atoms.tech/health
curl https://devmcp.atoms.tech/api/mcp
```

**How it works:**
- Vercel automatically detects non-main branches and sets VERCEL_ENV=preview
- The consolidated `vercel.json` has both domains in the `alias` array
- Vercel routes preview deployments to devmcp.atoms.tech
- No manual configuration or CLI commands needed

#### Consolidated Vercel Configuration

The consolidated `vercel.json` handles both environments automatically:

```json
{
  "version": 2,
  "builds": [
    {
      "src": "app.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/health",
      "dest": "app.py",
      "headers": {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization"
      }
    },
    {
      "src": "/api/mcp",
      "dest": "app.py",
      "headers": {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization"
      }
    },
    {
      "src": "/auth/complete",
      "dest": "app.py"
    },
    {
      "src": "/.well-known/(.*)",
      "dest": "app.py"
    },
    {
      "src": "/(.*)",
      "dest": "app.py"
    }
  ],
  "env": {
    "ATOMS_FASTMCP_TRANSPORT": "http",
    "ATOMS_FASTMCP_HTTP_PATH": "/api/mcp"
  },
  "github": {
    "silent": true
  },
  "alias": ["atomcp.kooshapari.com", "devmcp.atoms.tech"]
}
```

**Key features:**
- **Both domains in alias array**: Vercel automatically routes based on VERCEL_ENV
- **No hardcoded BASE_URL**: Environment-specific URLs configured in Vercel dashboard
- **Single build command**: Works for both preview and production
- **Git branch mapping**: main → production, all others → preview

### Workflow 3: Deploy to Production

**Use Case:** Promoting tested changes to production

#### Automatic Deployment (via Main Branch)

```bash
# 1. Verify preview deployment is working
curl https://devmcp.atoms.tech/health

# 2. Run full test suite against preview
pytest -m "unit or integration" --base-url=https://devmcp.atoms.tech

# 3. Merge to main branch (triggers production deployment)
git checkout main
git merge feature/new-feature
git push origin main

# → Vercel automatically detects VERCEL_ENV=production and deploys to atomcp.kooshapari.com

# 4. Verify production deployment
curl https://atomcp.kooshapari.com/health

# 5. Run smoke tests
pytest -m "unit and not slow" --base-url=https://atomcp.kooshapari.com

# 6. Monitor logs (if Vercel CLI is installed)
vercel logs atomcp.kooshapari.com --follow
```

**How it works:**
- Vercel automatically detects main branch and sets VERCEL_ENV=production
- The consolidated `vercel.json` routes production deployments to atomcp.kooshapari.com
- Environment-specific variables loaded from Vercel dashboard based on VERCEL_ENV
- No manual promotion or CLI commands needed

#### Production Deployment Checklist

Before deploying to production:

- [ ] All tests passing on dev
- [ ] Manual testing completed on dev
- [ ] Performance tested on dev
- [ ] Security review completed
- [ ] Documentation updated
- [ ] Team notified of deployment
- [ ] Rollback plan ready
- [ ] Monitoring enabled

### Workflow 4: Test Against Specific Environment

**Local:**
```bash
# Start local server
python start_server.py

# In another terminal, run tests
pytest -m integration --base-url=http://localhost:50002
```

**Dev:**
```bash
pytest -m integration --base-url=https://devmcp.atoms.tech
```

**Production:**
```bash
# Run only smoke tests on production
pytest -m "unit and not slow" --base-url=https://atomcp.kooshapari.com
```

### Workflow 5: Rollback Procedures

#### Rollback Production to Previous Version

```bash
# 1. List recent deployments
vercel list

# Output:
# NAME              URL                                    AGE
# atoms-mcp         atoms-mcp-abc123.vercel.app           2m
# atoms-mcp         atoms-mcp-xyz789.vercel.app (current) 1h
# atoms-mcp         atoms-mcp-def456.vercel.app           2h

# 2. Promote previous deployment
vercel promote atoms-mcp-xyz789.vercel.app

# 3. Verify rollback
curl https://atomcp.kooshapari.com/health

# 4. Run smoke tests
pytest -m "unit and not slow" --base-url=https://atomcp.kooshapari.com
```

#### Emergency Rollback

```bash
# Quick rollback to last known good deployment
vercel rollback

# Verify immediately
curl https://atomcp.kooshapari.com/health
```

---

## Testing Matrix

### Test Types by Environment

| Test Type | Local | Dev | Production |
|-----------|-------|-----|------------|
| **Unit Tests** | ✓ Required | ✓ Required | ✓ Required |
| **Integration Tests** | ✓ Required | ✓ Required | ✓ Smoke tests only |
| **E2E Tests** | - Optional | ✓ Required | ✓ Smoke tests only |
| **Performance Tests** | - Optional | ✓ Required | - Monitoring only |
| **Security Tests** | ✓ Required | ✓ Required | - Monitoring only |
| **Load Tests** | - Not recommended | ✓ Optional | - Monitoring only |

### Test Commands

#### Unit Tests (Fast, No External Dependencies)

```bash
# Run all unit tests
pytest -m unit

# Run in parallel
pytest -m unit -n auto

# Run with coverage
pytest -m unit --cov=. --cov-report=html

# Expected: <1s per test, 100% pass rate
```

#### Integration Tests (Requires Server Running)

```bash
# Start server first
python start_server.py

# In another terminal, run integration tests
pytest -m integration

# Test specific tools
pytest -m entity              # Entity management tests
pytest -m workspace           # Workspace tests
pytest -m workflow            # Workflow tests
pytest -m relationship        # Relationship tests
pytest -m query               # Query and search tests
```

#### End-to-End Tests (Full Workflows)

```bash
# Run all E2E tests
pytest -m e2e

# Run with authentication
pytest -m "e2e and auth" --validate-auth

# Expected: May take several seconds per test
```

#### Environment-Specific Testing

```bash
# Test local environment
pytest --base-url=http://localhost:50002

# Test dev environment
pytest --base-url=https://devmcp.atoms.tech

# Test production (smoke tests only)
pytest -m "unit and not slow" --base-url=https://atomcp.kooshapari.com
```

#### Parallel Testing

```bash
# Auto-detect number of CPUs
pytest -n auto

# Specify number of workers
pytest -n 4

# Parallel with progress display
pytest -n auto --enable-rich-progress
```

### Test Reports

```bash
# Generate comprehensive reports
pytest --enable-reports --enable-rich-progress

# Reports generated:
# - test_report.json          # JSON report with all test results
# - test_report.md            # Markdown summary
# - test_matrix.md            # Test matrix by category
# - ~/.atoms_mcp_test_cache/  # Cached auth tokens
```

### Testing Best Practices

1. **Always test locally first** - Run unit and integration tests before deploying
2. **Use session-scoped auth** - OAuth performed once per test session
3. **Run in parallel** - Use `pytest -n auto` for faster execution
4. **Skip slow tests during development** - Use `pytest -m "not slow"`
5. **Validate auth before testing** - Use `--validate-auth` flag
6. **Monitor test performance** - Use `--durations=10` to find slow tests

---

## CI/CD Integration

### GitHub Actions Workflow

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Vercel

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

env:
  VERCEL_ORG_ID: ${{ secrets.VERCEL_ORG_ID }}
  VERCEL_PROJECT_ID: ${{ secrets.VERCEL_PROJECT_ID }}

jobs:
  test:
    name: Run Tests
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-xdist pytest-cov

      - name: Run unit tests
        run: pytest -m unit -n auto --cov=.

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml

  deploy-preview:
    name: Deploy to Preview
    runs-on: ubuntu-latest
    needs: test
    if: github.event_name == 'pull_request'
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Install Vercel CLI
        run: npm install --global vercel@latest

      - name: Pull Vercel Environment Information
        run: vercel pull --yes --environment=preview --token=${{ secrets.VERCEL_TOKEN }}

      - name: Build Project Artifacts
        run: vercel build --token=${{ secrets.VERCEL_TOKEN }}

      - name: Deploy to Vercel Preview
        id: deploy
        run: |
          DEPLOYMENT_URL=$(vercel deploy --prebuilt --token=${{ secrets.VERCEL_TOKEN }})
          echo "deployment_url=$DEPLOYMENT_URL" >> $GITHUB_OUTPUT

      - name: Alias to devmcp.atoms.tech
        run: vercel alias set ${{ steps.deploy.outputs.deployment_url }} devmcp.atoms.tech --token=${{ secrets.VERCEL_TOKEN }}

      - name: Comment PR with Preview URL
        uses: actions/github-script@v6
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `🚀 Preview deployment ready!\n\n**URL:** https://devmcp.atoms.tech\n**MCP Endpoint:** https://devmcp.atoms.tech/api/mcp`
            })

  deploy-production:
    name: Deploy to Production
    runs-on: ubuntu-latest
    needs: test
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    environment:
      name: production
      url: https://atomcp.kooshapari.com
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Install Vercel CLI
        run: npm install --global vercel@latest

      - name: Pull Vercel Environment Information
        run: vercel pull --yes --environment=production --token=${{ secrets.VERCEL_TOKEN }}

      - name: Build Project Artifacts
        run: vercel build --prod --token=${{ secrets.VERCEL_TOKEN }}

      - name: Deploy to Vercel Production
        run: vercel deploy --prebuilt --prod --token=${{ secrets.VERCEL_TOKEN }}

      - name: Run Smoke Tests
        run: |
          pip install pytest
          pytest -m "unit and not slow" --base-url=https://atomcp.kooshapari.com
```

### Required GitHub Secrets

Configure in GitHub repository → Settings → Secrets and variables → Actions:

```
VERCEL_TOKEN=your_vercel_token
VERCEL_ORG_ID=your_vercel_org_id
VERCEL_PROJECT_ID=your_vercel_project_id
WORKOS_API_KEY=your_workos_api_key
WORKOS_CLIENT_ID=your_workos_client_id
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

### Workflow Behavior

**On Pull Request:**
1. Run unit tests
2. Deploy to preview environment
3. Alias to `devmcp.atoms.tech`
4. Comment PR with preview URL

**On Push to Main:**
1. Run unit tests
2. Deploy to production
3. Run smoke tests
4. Notify team (via Slack/Discord webhook)

### Manual Approval for Production

Add manual approval step:

```yaml
deploy-production:
  # ... (same as above)
  environment:
    name: production
    url: https://atomcp.kooshapari.com
  # This requires manual approval in GitHub UI
```

Configure in GitHub repository → Settings → Environments → production → Required reviewers

---

## Monitoring & Rollback

### Health Checks

**Endpoint:** `GET /health`

```bash
# Check local
curl http://localhost:50002/health

# Check dev
curl https://devmcp.atoms.tech/health

# Check production
curl https://atomcp.kooshapari.com/health

# Expected response (200 OK):
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "production",
  "timestamp": "2025-10-09T12:00:00Z"
}
```

### Monitoring Tools

#### Vercel Dashboard

Monitor deployments, logs, and performance:
- **URL:** https://vercel.com/dashboard
- **Logs:** Real-time function logs
- **Analytics:** Request counts, response times, error rates
- **Vitals:** Core Web Vitals metrics

#### Vercel CLI Monitoring

```bash
# View logs in real-time
vercel logs atomcp.kooshapari.com --follow

# View logs for specific deployment
vercel logs atoms-mcp-abc123.vercel.app

# View logs with filters
vercel logs atomcp.kooshapari.com --filter="error" --since 1h
```

#### WorkOS Dashboard

Monitor authentication:
- **URL:** https://dashboard.workos.com/
- **Metrics:** Login success/failure rates
- **Events:** Recent authentication events
- **Users:** Active user sessions

#### Supabase Dashboard

Monitor database:
- **URL:** https://supabase.com/dashboard
- **Metrics:** Database connections, query performance
- **Logs:** Query logs, error logs
- **Storage:** Database size, row counts

### Alerting

#### Set Up Vercel Alerts

1. Go to Vercel Dashboard → Project → Settings → Alerts
2. Configure alerts for:
   - Deployment failures
   - High error rates (>1%)
   - Slow response times (>1000ms p95)
   - High memory usage (>80%)

#### Set Up WorkOS Alerts

1. Go to WorkOS Dashboard → Settings → Notifications
2. Configure alerts for:
   - Authentication failures (>5% failure rate)
   - Suspicious login attempts
   - API key issues

### Rollback Decision Matrix

| Condition | Action |
|-----------|--------|
| **Error rate >5%** | Immediate rollback |
| **Response time >2s** | Investigate, consider rollback |
| **Authentication failures** | Investigate, check WorkOS config |
| **Database connection errors** | Check Supabase, consider rollback |
| **Memory/CPU issues** | Monitor, scale if needed |

### Rollback Procedures

See [Workflow 5: Rollback Procedures](#workflow-5-rollback-procedures) for detailed rollback commands.

---

## Troubleshooting

### Common Issues

#### Issue 1: OAuth Redirect URI Mismatch

**Symptoms:**
- Error: "Invalid redirect URI"
- Login fails with WorkOS error

**Solution:**
1. Verify redirect URI in WorkOS Dashboard matches exactly
2. Check `FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL` environment variable
3. Ensure no trailing slashes
4. Wait 2-5 minutes for WorkOS to propagate changes

**Commands:**
```bash
# Check current configuration
curl https://devmcp.atoms.tech/.well-known/openid-configuration

# Verify WorkOS configuration
curl https://decent-hymn-17-staging.authkit.app/.well-known/openid-configuration
```

#### Issue 2: CORS Errors

**Symptoms:**
- Browser console: "CORS policy: No 'Access-Control-Allow-Origin' header"
- API requests fail from browser

**Solution:**
1. Add origin to WorkOS Dashboard → CORS Settings
2. Verify `vercel.json` has correct CORS headers
3. Clear browser cache

**Verify:**
```bash
# Check CORS headers
curl -X OPTIONS -H "Origin: https://devmcp.atoms.tech" https://devmcp.atoms.tech/api/mcp -v
```

#### Issue 3: Vercel Deployment Fails

**Symptoms:**
- Deployment fails during build
- "Build exceeded maximum duration"

**Solution:**
1. Check build logs: `vercel logs`
2. Verify `vercel.json` is correctly configured
3. Check for missing dependencies in `requirements.txt`
4. Ensure Python version is correct (3.11+)

**Commands:**
```bash
# View build logs
vercel logs --since 1h

# Test build locally
vercel build
```

#### Issue 4: Environment Variables Not Set

**Symptoms:**
- Server starts but authentication fails
- Missing configuration errors

**Solution:**
1. Check Vercel Dashboard → Project → Settings → Environment Variables
2. Verify environment variables are set for correct environment (preview/production)
3. Redeploy after adding variables

**Commands:**
```bash
# List environment variables
vercel env ls

# Add environment variable
vercel env add WORKOS_API_KEY production

# Pull environment variables
vercel env pull .env.production
```

#### Issue 5: CloudFlare Tunnel Not Starting

**Symptoms:**
- Local server starts but tunnel fails
- OAuth redirects to localhost instead of public URL

**Solution:**
1. Install CloudFlare: `brew install cloudflare/cloudflare/cloudflared`
2. Login: `cloudflared tunnel login`
3. Check tunnel status: `cloudflared tunnel list`
4. Restart server with tunnel: `python start_server.py`

**Commands:**
```bash
# Check if cloudflared is installed
which cloudflared

# Check tunnel status
cloudflared tunnel list

# Manual tunnel test
cloudflared tunnel --url http://localhost:50002
```

#### Issue 6: Tests Failing on CI

**Symptoms:**
- Tests pass locally but fail on GitHub Actions
- Timeout errors on CI

**Solution:**
1. Verify GitHub Secrets are set correctly
2. Check that CI has access to required services (Supabase, WorkOS)
3. Increase timeouts for integration tests
4. Run tests with `--verbose` flag for more details

**Debug:**
```bash
# Run tests with verbose output
pytest -m unit -vv

# Run tests with timeout
pytest -m unit --timeout=60
```

### Debugging Tips

1. **Check logs first:**
   - Vercel: `vercel logs --follow`
   - Local: Console output from `start_server.py`

2. **Verify configuration:**
   - WorkOS Dashboard: All URLs configured
   - Vercel Dashboard: Environment variables set
   - `.env` files: Correct for each environment

3. **Test incrementally:**
   - Start with unit tests
   - Then integration tests
   - Finally E2E tests

4. **Use health checks:**
   - `/health` endpoint should always return 200
   - Check before and after deployment

5. **Monitor metrics:**
   - Vercel Analytics for performance
   - WorkOS Dashboard for auth issues
   - Supabase Dashboard for database issues

### Getting Help

1. **Check documentation:**
   - [WORKOS_SETUP.md](/Users/kooshapari/temp-PRODVERCEL/485/kush/atoms_mcp-old/WORKOS_SETUP.md) - WorkOS configuration
   - [TESTING_GUIDE.md](/Users/kooshapari/temp-PRODVERCEL/485/kush/atoms_mcp-old/TESTING_GUIDE.md) - Testing documentation
   - [README.md](/Users/kooshapari/temp-PRODVERCEL/485/kush/atoms_mcp-old/README.md) - General documentation

2. **Check status pages:**
   - [Vercel Status](https://www.vercel-status.com/)
   - [WorkOS Status](https://status.workos.com/)
   - [Supabase Status](https://status.supabase.com/)

3. **Community resources:**
   - Vercel Discord
   - WorkOS Support
   - GitHub Issues

---

## Best Practices

### Development

1. **Always test locally first** - Use `start_server.py` with CloudFlare tunnel
2. **Use feature branches** - Create branches for each feature/fix
3. **Write tests** - Add unit tests for new functionality
4. **Update documentation** - Keep README and guides updated

### Deployment

1. **Test on dev first** - Always deploy to dev/preview before production
2. **Manual promotion** - Never auto-deploy to production
3. **Monitor after deployment** - Watch logs and metrics for 15-30 minutes
4. **Have a rollback plan** - Know how to rollback quickly

### Security

1. **Never commit secrets** - Use `.env` files (excluded from git)
2. **Use environment-specific keys** - Different keys for dev/production
3. **Rotate credentials regularly** - Update WorkOS and Supabase keys quarterly
4. **Enable MFA** - On WorkOS, Vercel, and Supabase accounts

### Monitoring

1. **Set up alerts** - Configure Vercel alerts for errors and performance
2. **Review logs daily** - Check for errors and anomalies
3. **Monitor authentication** - Watch WorkOS dashboard for auth issues
4. **Track performance** - Use Vercel Analytics to track response times

---

## Quick Reference

### Essential Commands

```bash
# Local development
python start_server.py                    # Start local server with tunnel
pytest -m unit                                  # Run unit tests
pytest -m integration                           # Run integration tests

# Deployment (via Git - Vercel auto-deploys)
git push origin feature-branch                  # Deploy to dev (devmcp.atoms.tech)
git push origin main                            # Deploy to production (atomcp.kooshapari.com)

# Testing
pytest -m unit -n auto                          # Fast parallel unit tests
pytest -m integration --base-url=https://devmcp.atoms.tech
pytest -m "unit and not slow" --base-url=https://atomcp.kooshapari.com

# Monitoring
curl https://atomcp.kooshapari.com/health      # Health check
curl https://devmcp.atoms.tech/health           # Dev health check

# Rollback (requires Vercel CLI)
vercel list                                     # List deployments
vercel promote [deployment-url]                 # Promote specific deployment
vercel rollback                                 # Quick rollback to previous
```

### Environment URLs

| Environment | URL | MCP Endpoint |
|-------------|-----|--------------|
| **Local** | http://localhost:50002 | http://localhost:50002/api/mcp |
| **Local (Tunnel)** | https://atomcp.kooshapari.com | https://atomcp.kooshapari.com/api/mcp |
| **Dev/Preview** | https://devmcp.atoms.tech | https://devmcp.atoms.tech/api/mcp |
| **Production** | https://atomcp.kooshapari.com | https://atomcp.kooshapari.com/api/mcp |

### Configuration Files

| File | Purpose |
|------|---------|
| `.env` | Local environment configuration |
| `.env.preview` | Dev/preview environment (optional, use Vercel UI) |
| `.env.production` | Production environment (optional, use Vercel UI) |
| `vercel.json` | Vercel deployment configuration |
| `pytest.ini` | Test framework configuration |
| `requirements.txt` | Python dependencies |

---

## Appendix

### A. Environment Variable Reference

Complete list of environment variables used across all tiers:

| Variable | Local | Dev | Production | Description |
|----------|-------|-----|------------|-------------|
| `ATOMS_FASTMCP_TRANSPORT` | http | http | http | Transport protocol |
| `ATOMS_FASTMCP_HOST` | 127.0.0.1 | N/A | N/A | Server host (local only) |
| `ATOMS_FASTMCP_PORT` | 50002 | N/A | N/A | Server port (local only) |
| `ATOMS_FASTMCP_HTTP_PATH` | N/A | /api/mcp | /api/mcp | HTTP path for MCP |
| `WORKOS_API_KEY` | sk_test_... | sk_test_... | sk_live_... | WorkOS API key |
| `WORKOS_CLIENT_ID` | client_... | client_... | client_... | WorkOS OAuth client ID |
| `FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN` | https://decent-hymn-17-staging.authkit.app | (same) | (same) | AuthKit domain |
| `FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL` | https://atomcp.kooshapari.com | https://devmcp.atoms.tech | https://atomcp.kooshapari.com | OAuth redirect base |
| `NEXT_PUBLIC_SUPABASE_URL` | https://... | https://... | https://... | Supabase URL |
| `SUPABASE_SERVICE_ROLE_KEY` | eyJ... | eyJ... | eyJ... | Supabase service role key |
| `GOOGLE_CLOUD_PROJECT` | your-project | your-project | prod-project | GCP project ID |
| `LOG_LEVEL` | INFO | INFO | WARNING | Logging level |
| `VERCEL_ENV` | N/A | preview | production | Vercel environment |

### B. Vercel Configuration Reference

Complete `vercel.json` with all options:

```json
{
  "version": 2,
  "builds": [
    {
      "src": "app.py",
      "use": "@vercel/python",
      "config": {
        "maxLambdaSize": "50mb"
      }
    }
  ],
  "routes": [
    {
      "src": "/health",
      "dest": "app.py",
      "headers": {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization"
      }
    },
    {
      "src": "/api/mcp",
      "dest": "app.py",
      "headers": {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization"
      }
    },
    {
      "src": "/auth/(.*)",
      "dest": "app.py"
    },
    {
      "src": "/.well-known/(.*)",
      "dest": "app.py"
    },
    {
      "src": "/(.*)",
      "dest": "app.py"
    }
  ],
  "env": {
    "ATOMS_FASTMCP_TRANSPORT": "http",
    "ATOMS_FASTMCP_HTTP_PATH": "/api/mcp"
  },
  "github": {
    "silent": true,
    "autoAlias": true
  },
  "alias": ["devmcp.atoms.tech"],
  "regions": ["iad1"]
}
```

### C. Test Markers Reference

All pytest markers available:

```python
# Test type markers
@pytest.mark.unit                    # Fast unit tests (<1s)
@pytest.mark.integration             # Integration tests (requires server)
@pytest.mark.e2e                     # End-to-end tests
@pytest.mark.slow                    # Slow tests (>5s)

# Feature markers
@pytest.mark.auth                    # Authentication tests
@pytest.mark.http                    # HTTP/MCP tests
@pytest.mark.tool                    # MCP tool tests
@pytest.mark.provider                # OAuth provider tests

# Tool-specific markers
@pytest.mark.entity                  # Entity management tests
@pytest.mark.relationship            # Relationship tests
@pytest.mark.workflow                # Workflow tests
@pytest.mark.workspace               # Workspace tests
@pytest.mark.query                   # Query and search tests

# Execution markers
@pytest.mark.parallel                # Can run in parallel
@pytest.mark.skip_if_no_oauth        # Skip if OAuth not available
```

### D. Deployment Checklist

Complete checklist for production deployments:

#### Pre-Deployment
- [ ] All unit tests passing locally
- [ ] All integration tests passing locally
- [ ] Code reviewed by team member
- [ ] Documentation updated
- [ ] Environment variables verified
- [ ] WorkOS redirect URIs configured
- [ ] Supabase database migrations applied

#### Deployment to Dev
- [ ] Deploy to dev/preview
- [ ] Verify health check: `curl https://devmcp.atoms.tech/health`
- [ ] Test authentication flow
- [ ] Run integration tests against dev
- [ ] Manual testing completed
- [ ] Performance testing completed
- [ ] Team review and approval

#### Deployment to Production
- [ ] Final review of changes
- [ ] Rollback plan prepared
- [ ] Team notified of deployment
- [ ] Deploy to production: `vercel --prod`
- [ ] Verify health check: `curl https://atomcp.kooshapari.com/health`
- [ ] Run smoke tests
- [ ] Monitor logs for 15-30 minutes
- [ ] Monitor error rates
- [ ] Monitor response times
- [ ] Verify authentication working
- [ ] Team notified of successful deployment

#### Post-Deployment
- [ ] Update deployment log
- [ ] Create git tag for release
- [ ] Close related GitHub issues
- [ ] Update changelog
- [ ] Monitor for 24 hours

---

**Document Version:** 1.0.0
**Last Updated:** 2025-10-09
**Maintainers:** Atoms MCP Team
**Related Documentation:** [WORKOS_SETUP.md](/Users/kooshapari/temp-PRODVERCEL/485/kush/atoms_mcp-old/WORKOS_SETUP.md), [TESTING_GUIDE.md](/Users/kooshapari/temp-PRODVERCEL/485/kush/atoms_mcp-old/TESTING_GUIDE.md), [README.md](/Users/kooshapari/temp-PRODVERCEL/485/kush/atoms_mcp-old/README.md)
