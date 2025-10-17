# 3-Tier Deployment Architecture - Complete Guide

**Date:** October 9, 2025
**Status:** PRODUCTION READY

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Atoms MCP Deployment Tiers                    │
└─────────────────────────────────────────────────────────────────┘

Tier 1: LOCAL          Tier 2: DEV            Tier 3: PRODUCTION
─────────────          ────────────           ───────────────────
localhost:50002        devmcp.atoms.tech      atomcp.kooshapari.com
CloudFlare Tunnel      Vercel Preview         Vercel Production

Development            Testing/Staging        Live Users
Fast iteration         Pre-prod validation    Stable releases
```

---

## 🎯 Quick Reference

| Environment | URL | Deploy Method | Use For |
|-------------|-----|---------------|---------|
| **Local** | https://atomcp.kooshapari.com (tunnel) | `python start_server.py` | Development, debugging |
| **Dev** | https://devmcp.atoms.tech | `git push origin <branch>` | Feature testing, QA |
| **Production** | https://atomcp.kooshapari.com | `git push origin main` | Live users |

---

## 🚀 Deployment Workflows

### Tier 1: Local Development

**Purpose:** Fast iteration, debugging, local testing

**Start:**
```bash
python start_server.py
```

**What happens:**
1. SmartInfraManager allocates port 50002
2. CloudFlare tunnel connects to atomcp.kooshapari.com
3. Server starts with hot reload
4. OAuth works via HTTPS tunnel

**Test against local:**
```bash
python tests/test_main.py --local
```

**When to use:**
- Writing new features
- Debugging issues
- Running tests quickly
- No deployment needed

---

### Tier 2: Dev/Preview (Vercel)

**Purpose:** Feature testing, QA validation, stakeholder reviews

**Deploy:**
```bash
git checkout -b feature/my-feature
# Make changes
git commit -am "Add my feature"
git push origin feature/my-feature
```

**What happens:**
1. Vercel detects push to non-main branch
2. Sets `VERCEL_ENV=preview`
3. Uses `.env.preview` variables
4. Deploys to devmcp.atoms.tech
5. Sends deployment URL in GitHub PR

**Test against dev:**
```bash
python tests/test_main.py --dev
```

**When to use:**
- Testing features before production
- QA validation
- Stakeholder demos
- Integration testing
- Pre-release checks

---

### Tier 3: Production (Vercel)

**Purpose:** Live user traffic, stable releases

**Deploy:**
```bash
git checkout main
git merge feature/my-feature
git push origin main
```

**What happens:**
1. Vercel detects push to main branch
2. Sets `VERCEL_ENV=production`
3. Uses production environment variables
4. Deploys to atomcp.kooshapari.com
5. Goes live immediately

**Test against production:**
```bash
python tests/test_main.py
```

**When to use:**
- Releasing validated features
- Hotfixes
- Stable updates
- After QA approval

---

## 🔐 WorkOS OAuth Configuration

**Single AuthKit Environment:** `decent-hymn-17-staging`

**All 3 Redirect URIs Required:**
```
https://atomcp.kooshapari.com/callback    (Production)
https://devmcp.atoms.tech/callback         (Dev/Preview)
http://localhost:50002/callback            (Local)
```

**All 3 CORS Origins:**
```
https://atomcp.kooshapari.com
https://devmcp.atoms.tech
http://localhost:50002
```

**Configure in:** WorkOS Dashboard → AuthKit → Configuration

---

## 🌐 DNS Configuration

### Local (No DNS needed)
- CloudFlare tunnel handles routing
- atomcp.kooshapari.com resolves to tunnel

### Dev (CNAME)
```
devmcp.atoms.tech → CNAME → cname.vercel-dns.com
```

### Production (CNAME)
```
atomcp.kooshapari.com → CNAME → cname.vercel-dns.com
```

**Configure in:** Google Cloud DNS or your DNS provider

---

## 📦 Vercel Configuration

### vercel.json
```json
{
  "alias": [
    "atomcp.kooshapari.com",  // Production
    "devmcp.atoms.tech"       // Preview
  ],
  "github": {
    "silent": true,
    "autoAlias": true
  }
}
```

### Environment Variables in Vercel Dashboard

**Production Environment:**
- BASE_URL: `https://atomcp.kooshapari.com`
- PUBLIC_URL: `https://atomcp.kooshapari.com`
- (+ all shared variables)

**Preview Environment:**
- BASE_URL: `https://devmcp.atoms.tech`
- PUBLIC_URL: `https://devmcp.atoms.tech`
- (+ all shared variables)

---

## 🧪 Testing Matrix

| Test Suite | Local | Dev | Production |
|------------|-------|-----|------------|
| **Unit Tests** | ✅ Fast | ✅ Fast | ✅ Fast |
| **Integration** | ✅ | ✅ | ⚠️ Careful |
| **E2E Workflows** | ✅ | ✅ Recommended | ⚠️ Read-only |
| **Load Tests** | ❌ | ✅ Recommended | ❌ |
| **Auth Flow** | ✅ | ✅ | ✅ |

**Recommendations:**
- Local: All tests safe
- Dev: Perfect for integration/E2E/load testing
- Production: Unit tests + read-only validation only

---

## 🔄 Development Workflow

### Feature Development
```bash
# 1. Start local server
python start_server.py

# 2. Develop and test locally
python tests/test_main.py --local

# 3. Push to feature branch (deploys to dev)
git push origin feature/my-feature

# 4. Test against dev
python tests/test_main.py --dev

# 5. Merge to main (deploys to production)
git checkout main
git merge feature/my-feature
git push origin main

# 6. Verify production
python tests/test_main.py
```

---

## 🛠️ Troubleshooting

### Local Server Won't Start
```bash
# Check if port 50002 is in use
lsof -i :50002

# Check CloudFlare tunnel
cloudflared tunnel list

# Restart with verbose logging
python start_server.py --verbose
```

### Dev Deployment Not Working
```bash
# Check Vercel deployment logs
vercel logs devmcp.atoms.tech

# Verify environment variables
vercel env ls

# Check if devmcp.atoms.tech DNS resolves
nslookup devmcp.atoms.tech
```

### Production Issues
```bash
# Check Vercel production logs
vercel logs atomcp.kooshapari.com --prod

# Rollback to previous deployment
vercel rollback

# Check DNS
nslookup atomcp.kooshapari.com
```

---

## 📊 Environment Comparison

| Feature | Local | Dev | Production |
|---------|-------|-----|------------|
| **Deployment** | Manual | Auto (git push) | Auto (git push) |
| **Port** | 50002 | - | - |
| **Tunnel** | CloudFlare | - | - |
| **Platform** | Local machine | Vercel | Vercel |
| **Domain** | atomcp (tunnel) | devmcp.atoms.tech | atomcp.kooshapari.com |
| **HTTPS** | ✅ (tunnel) | ✅ (Vercel) | ✅ (Vercel) |
| **OAuth** | ✅ | ✅ | ✅ |
| **Database** | Production (Supabase) | Production (Supabase) | Production (Supabase) |
| **Auth** | Staging (decent-hymn-17) | Staging (decent-hymn-17) | Staging (decent-hymn-17) |
| **Cost** | Free | Free (hobby) | $$$ (varies) |

---

## ✅ Setup Checklist

### One-Time Setup
- [ ] Configure WorkOS redirect URIs (all 3)
- [ ] Configure WorkOS CORS origins (all 3)
- [ ] Set up DNS CNAME for devmcp.atoms.tech
- [ ] Set up DNS CNAME for atomcp.kooshapari.com (if not done)
- [ ] Configure Vercel environment variables (production + preview)
- [ ] Set Vercel production branch to `main`
- [ ] Install CloudFlare tunnel: `brew install cloudflared`

### Per Developer
- [ ] Clone repository
- [ ] Install dependencies: `uv sync`
- [ ] Copy `.env.example` to `.env` and configure
- [ ] Run: `python start_server.py`
- [ ] Verify: OAuth works locally

---

## 🎉 Benefits

### Simplified Workflow
- ✅ One command for local: `python start_server.py`
- ✅ Git push for deployments (no CLI commands)
- ✅ Automatic environment detection
- ✅ Consistent across all tiers

### Better Testing
- ✅ Test locally before pushing
- ✅ Validate on dev before production
- ✅ Production tests are read-only
- ✅ Same test suite across all environments

### Reduced Risk
- ✅ Feature branches don't affect production
- ✅ Dev environment for QA
- ✅ Automatic rollback available
- ✅ Clear separation of concerns

---

## 📞 Quick Commands

```bash
# Local Development
python start_server.py                   # Start local server
python tests/test_main.py --local        # Test locally

# Deploy to Dev
git push origin feature-branch           # Auto-deploys to devmcp
python tests/test_main.py --dev          # Test dev

# Deploy to Production
git push origin main                     # Auto-deploys to atomcp
python tests/test_main.py                # Test production

# Rollback Production
vercel rollback atomcp.kooshapari.com --prod
```

---

**Everything is now streamlined and production-ready!** 🚀
