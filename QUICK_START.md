# Atoms MCP - Quick Start Guide

## 3-Tier Deployment Overview

```
Local Development → Dev/Preview → Production
  (CloudFlare tunnel)   (Vercel)     (Vercel)
```

| Environment | How to Deploy | URL |
|-------------|--------------|-----|
| **Local** | `python start_server.py` | https://atomcp.kooshapari.com (via tunnel) |
| **Dev** | `git push origin feature-branch` | https://devmcp.atoms.tech |
| **Production** | `git push origin main` | https://atomcp.kooshapari.com |

---

## Start Local Server

**Default behavior includes CloudFlare tunnel (required for OAuth):**

```bash
python start_server.py
```

**What you get:**
- Local Server: `http://localhost:50002`
- Public URL (via tunnel): `https://atomcp.kooshapari.com`
- MCP Endpoint: `https://atomcp.kooshapari.com/api/mcp`
- OAuth works (HTTPS required)

**Disable tunnel (OAuth won't work):**
```bash
python start_server.py --no-tunnel
```

---

## Deploy to Dev Environment

Deploy to dev/preview environment at `https://devmcp.atoms.tech`:

```bash
# 1. Create feature branch
git checkout -b feature/my-feature

# 2. Make changes and commit
git add .
git commit -m "Add my feature"

# 3. Push to trigger automatic deployment
git push origin feature/my-feature

# → Vercel automatically deploys to devmcp.atoms.tech
```

**Test the deployment:**
```bash
curl https://devmcp.atoms.tech/health
curl https://devmcp.atoms.tech/api/mcp
```

---

## Deploy to Production

Deploy to production at `https://atomcp.kooshapari.com`:

```bash
# 1. Merge to main branch
git checkout main
git merge feature/my-feature

# 2. Push to trigger automatic deployment
git push origin main

# → Vercel automatically deploys to atomcp.kooshapari.com
```

**Test the deployment:**
```bash
curl https://atomcp.kooshapari.com/health
curl https://atomcp.kooshapari.com/api/mcp
```

---

## Run Tests

### Test Against Local Server
```bash
pytest -m unit
pytest -m integration
```

### Test Against Dev Environment
```bash
pytest --base-url=https://devmcp.atoms.tech
```

### Test Against Production
```bash
pytest -m "unit and not slow" --base-url=https://atomcp.kooshapari.com
```

## Configuration Files

- **Server config**: `~/.atoms_mcp_infra/atoms_mcp_config.json`
- **Test config**: `~/.atoms_mcp_test_cache/local_server_config.json`
- **Environment**: `.env` (in project root)

## Common Commands

### Check if Server is Running
```bash
curl http://localhost:50002/health
```

### Kill Port 50002
```bash
lsof -i :50002 | grep LISTEN | awk '{print $2}' | xargs kill -9
```

### View Server Logs
```bash
python start_server.py --verbose
```

## WorkOS OAuth Setup

See `WORKOS_SETUP.md` for detailed instructions.

**All Redirect URIs to add in WorkOS Dashboard**:
- Production: `https://atomcp.kooshapari.com/callback`
- Dev: `https://devmcp.atoms.tech/callback`
- Local: `http://localhost:50002/callback`

**All CORS Origins to add in WorkOS Dashboard**:
- Production: `https://atomcp.kooshapari.com`
- Dev: `https://devmcp.atoms.tech`
- Local: `http://localhost:50002`

## Port Allocation

- **Atoms MCP**: Port 50002
- **Zen MCP**: Port 50001

## Documentation

- **Deployment Guide**: `DEPLOYMENT_GUIDE.md` - Complete 3-tier deployment workflow
- **WorkOS Config**: `WORKOS_SETUP.md` - OAuth configuration for all environments
- **Testing Guide**: `TESTING_GUIDE.md` - Comprehensive testing documentation
- **This Guide**: `QUICK_START.md` - Quick reference

## Troubleshooting

### Server Won't Start
```bash
# Kill existing process
lsof -i :50002 | grep LISTEN | awk '{print $2}' | xargs kill -9

# Try again
python start_server.py
```

### Tests Can't Find Server
```bash
# Check server is running
curl http://localhost:50002/health

# Check config file
cat ~/.atoms_mcp_test_cache/local_server_config.json
```

### OAuth Redirect Error
- Check WorkOS Dashboard → Redirect URIs
- Wait 2-5 minutes after adding new URI
- Clear browser cache

## Quick Verification

```bash
# Check all components
python verify_setup.py

# Test server imports
python -c "from server import create_consolidated_server; print('✓ OK')"

# Test auth imports
python -c "from auth import SessionMiddleware; print('✓ OK')"
```

## Development Workflow

```bash
# 1. Start local server
python start_server.py

# 2. In another terminal, run tests
pytest -m integration

# 3. Make changes and commit
git add .
git commit -m "My changes"

# 4. Push to dev for testing
git push origin feature/my-feature
# → Auto-deploys to devmcp.atoms.tech

# 5. Test dev deployment
curl https://devmcp.atoms.tech/health
pytest --base-url=https://devmcp.atoms.tech

# 6. Merge to main for production
git checkout main
git merge feature/my-feature
git push origin main
# → Auto-deploys to atomcp.kooshapari.com

# 7. Verify production
curl https://atomcp.kooshapari.com/health
```
