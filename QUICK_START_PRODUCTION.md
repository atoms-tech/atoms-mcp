# Quick Start Guide: 5-Minute Production Deployment

## Overview
Get the Atoms MCP Production system running in under 5 minutes with this streamlined quick start guide. This guide focuses on essential steps only - for detailed configuration, see the full documentation.

---

## Prerequisites (1 minute)

### Required Accounts
- ✅ Vercel account (for deployment)
- ✅ Supabase account (for database)
- ✅ GitHub account (for repository)

### Required Tools
```bash
# Check if installed
node --version     # Node.js 18+
python --version   # Python 3.11+
git --version      # Git 2.0+

# Install UV (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## Step 1: Clone & Setup (30 seconds)

```bash
# Clone the repository
git clone https://github.com/your-org/atoms-mcp-prod
cd atoms-mcp-prod

# Install dependencies
uv sync
npm install
```

---

## Step 2: Configure Environment (1 minute)

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your values (use your favorite editor)
nano .env
```

### Essential Environment Variables
```bash
# Supabase (get from Supabase dashboard)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-key

# AuthKit (get from WorkOS dashboard)
AUTHKIT_CLIENT_ID=your-client-id
AUTHKIT_CLIENT_SECRET=your-client-secret
AUTHKIT_REDIRECT_URI=https://your-app.vercel.app/auth/callback

# Vercel KV (auto-configured on Vercel)
KV_URL=will-be-set-by-vercel
KV_REST_API_URL=will-be-set-by-vercel
KV_REST_API_TOKEN=will-be-set-by-vercel

# Application
APP_ENV=production
API_BASE_URL=https://your-app.vercel.app
LOG_LEVEL=INFO
```

---

## Step 3: Database Setup (1 minute)

```bash
# Run database migrations
python scripts/sync_schema.py --mode production

# Verify RLS policies
python scripts/verify_rls.py

# Output should show:
# ✅ 47 tables synchronized
# ✅ 15 RLS policies active
# ✅ Schema version: 1.0.0
```

---

## Step 4: Deploy to Vercel (2 minutes)

### Option A: CLI Deployment
```bash
# Install Vercel CLI if needed
npm i -g vercel

# Login to Vercel
vercel login

# Deploy to production
vercel --prod

# Follow prompts:
# - Link to existing project? No
# - What's your project name? atoms-mcp-prod
# - In which directory? ./
# - Override settings? No
```

### Option B: GitHub Integration
```bash
# Push to GitHub
git add .
git commit -m "Initial deployment"
git push origin main

# In Vercel Dashboard:
# 1. Import Git Repository
# 2. Select your repo
# 3. Configure environment variables
# 4. Deploy
```

---

## Step 5: Verify Deployment (30 seconds)

```bash
# Get your deployment URL from Vercel output
DEPLOYMENT_URL=https://atoms-mcp-prod.vercel.app

# Check health endpoint
curl $DEPLOYMENT_URL/health

# Expected response:
# {
#   "status": "healthy",
#   "version": "1.0.0",
#   "components": {
#     "database": "healthy",
#     "auth": "healthy",
#     "cache": "healthy"
#   }
# }

# Check metrics endpoint
curl $DEPLOYMENT_URL/metrics

# Verify MCP server
curl $DEPLOYMENT_URL/api/mcp/tools
```

---

## Quick Health Check Commands

### Verify All Systems
```bash
# Run all health checks
./scripts/health_check.sh

# Expected output:
# ✅ API: Responding
# ✅ Database: Connected
# ✅ Auth: Configured
# ✅ Cache: Available
# ✅ Metrics: Collecting
# ✅ All systems operational
```

### Run Smoke Tests
```bash
# Basic functionality test
./scripts/smoke_test.sh

# Expected output:
# ✅ Token refresh: Working
# ✅ Session creation: Working
# ✅ RLS policies: Enforced
# ✅ Metrics collection: Active
# ✅ Smoke tests passed
```

---

## Minimal Viable Configuration

### For Testing Only
If you just want to test the system quickly, use these minimal settings:

```bash
# .env.minimal
SUPABASE_URL=https://demo.supabase.co
SUPABASE_ANON_KEY=demo-key
APP_ENV=development
LOG_LEVEL=DEBUG
```

```bash
# Start locally
uv run uvicorn main:app --reload --port 8000

# Access at http://localhost:8000
```

---

## Essential API Endpoints

Once deployed, these endpoints are immediately available:

### Health & Monitoring
- `GET /health` - System health check
- `GET /metrics` - Prometheus metrics
- `GET /api/observability/dashboard` - Dashboard data

### Authentication
- `POST /auth/token/refresh` - Refresh access token
- `GET /auth/sessions` - List user sessions
- `POST /auth/sessions/revoke-all` - Logout everywhere

### MCP Server
- `GET /api/mcp/tools` - List available tools
- `POST /api/mcp/execute` - Execute MCP tool

---

## Quick Troubleshooting

### Common Issues & Fixes

#### 1. Database Connection Failed
```bash
# Check Supabase credentials
curl $SUPABASE_URL/rest/v1/ -H "apikey: $SUPABASE_ANON_KEY"

# If fails, regenerate keys in Supabase dashboard
```

#### 2. Deployment Failed
```bash
# Check build logs
vercel logs

# Common fix: Clear cache and redeploy
vercel --prod --force
```

#### 3. Auth Not Working
```bash
# Verify AuthKit configuration
python -c "from lib.auth import verify_config; verify_config()"

# Check redirect URI matches exactly
```

#### 4. Metrics Not Showing
```bash
# Verify metrics endpoint
curl localhost:8000/metrics

# Check Prometheus scraping
docker logs prometheus
```

---

## Post-Deployment Checklist

### Immediate Actions (5 minutes)
- [ ] Verify all health endpoints returning `healthy`
- [ ] Test token refresh endpoint
- [ ] Check metrics are being collected
- [ ] Verify RLS policies are enforced
- [ ] Test one MCP tool execution

### Within 1 Hour
- [ ] Configure monitoring alerts
- [ ] Set up error notifications
- [ ] Review security headers
- [ ] Enable rate limiting
- [ ] Test backup/restore

### Within 24 Hours
- [ ] Run load tests
- [ ] Configure auto-scaling
- [ ] Set up log aggregation
- [ ] Enable security scanning
- [ ] Document custom configuration

---

## Quick Performance Validation

```bash
# Simple load test (requires Apache Bench)
ab -n 1000 -c 10 $DEPLOYMENT_URL/health

# Expected results:
# Requests per second: > 500
# Mean response time: < 100ms
# Failed requests: 0
```

```python
# Python performance test
import asyncio
import aiohttp
import time

async def test_performance():
    url = "https://your-app.vercel.app/health"
    async with aiohttp.ClientSession() as session:
        start = time.time()
        tasks = [session.get(url) for _ in range(100)]
        await asyncio.gather(*tasks)
        elapsed = time.time() - start
        print(f"100 requests in {elapsed:.2f}s")
        print(f"Rate: {100/elapsed:.0f} req/s")

asyncio.run(test_performance())
```

---

## Monitoring Setup (Optional - 5 minutes)

### Quick Grafana Setup
```bash
# Start Grafana locally
docker run -d -p 3000:3000 grafana/grafana

# Access at http://localhost:3000 (admin/admin)

# Add Prometheus data source
# URL: http://host.docker.internal:9090

# Import dashboard
# Dashboard ID: atoms-mcp-prod
```

### Enable Alerts
```bash
# Configure webhook in .env
ALERT_WEBHOOK_URL=https://hooks.slack.com/your-webhook

# Test alert
curl -X POST $DEPLOYMENT_URL/api/observability/test-alert
```

---

## Security Quick Check

```bash
# Verify security headers
curl -I $DEPLOYMENT_URL/health | grep -E "X-Frame|X-Content|Strict-Transport"

# Expected headers:
# X-Frame-Options: DENY
# X-Content-Type-Options: nosniff
# Strict-Transport-Security: max-age=31536000

# Check rate limiting
for i in {1..15}; do
  curl -s -o /dev/null -w "%{http_code}\n" $DEPLOYMENT_URL/auth/token/refresh
done
# Should see 429 (Too Many Requests) after 10 requests
```

---

## Next Steps

### After Successful Deployment

1. **Configure Production Monitoring**
   ```bash
   ./scripts/setup_monitoring.sh --production
   ```

2. **Enable Advanced Features**
   ```bash
   # Enable WebAuthn
   echo "ENABLE_WEBAUTHN=true" >> .env

   # Enable ML monitoring
   echo "ENABLE_ML_MONITORING=true" >> .env

   # Redeploy
   vercel --prod
   ```

3. **Scale for Production**
   ```bash
   # Configure auto-scaling
   vercel scale atoms-mcp-prod --min 2 --max 10

   # Enable edge caching
   vercel edge --enable
   ```

---

## Quick Reference Card

### Essential Commands
```bash
# Deploy
vercel --prod

# Check status
curl $DEPLOYMENT_URL/health

# View logs
vercel logs

# Rollback
vercel rollback

# Scale
vercel scale --min 2 --max 10
```

### Key URLs
- **Application**: `https://your-app.vercel.app`
- **Health Check**: `/health`
- **Metrics**: `/metrics`
- **API Docs**: `/docs`
- **Dashboard**: `/api/observability/dashboard`

### Support Resources
- Documentation: `/docs`
- API Reference: `/api/docs`
- Troubleshooting: `/troubleshooting.md`
- GitHub Issues: `github.com/your-org/atoms-mcp-prod/issues`

---

## Emergency Procedures

### Quick Rollback
```bash
# List deployments
vercel ls

# Rollback to previous
vercel rollback

# Or specific version
vercel rollback dpl_xxxxx
```

### Emergency Shutdown
```bash
# Disable all traffic
vercel scale atoms-mcp-prod --min 0 --max 0

# Investigate issue
vercel logs --follow

# Re-enable when fixed
vercel scale atoms-mcp-prod --min 2 --max 10
```

---

## Conclusion

You now have a fully functional Atoms MCP Production system deployed!

**Time to Production**: < 5 minutes ⚡

### What's Running:
- ✅ Full authentication system with token management
- ✅ Enterprise observability with metrics and logging
- ✅ MCP server with all tools available
- ✅ Health monitoring and alerting
- ✅ Production-grade security

### Quick Validation:
```bash
# One command to verify everything
curl $DEPLOYMENT_URL/health && \
curl $DEPLOYMENT_URL/metrics > /dev/null && \
echo "✅ All systems operational!"
```

For detailed configuration and advanced features, see the full documentation.

---

**Quick Start Version**: 1.0.0
**Last Updated**: October 16, 2025
**Deployment Time**: < 5 minutes
**Production Ready**: ✅ YES

---

*End of Quick Start Guide*