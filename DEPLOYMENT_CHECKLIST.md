# Deployment Checklist

## Pre-Deployment

### ✅ Files Ready

- [x] `build.sh` - Replaces requirements.txt with requirements-prod.txt
- [x] `vercel.json` - Runs build.sh, updated config
- [x] `requirements-prod.txt` - No editable installs
- [x] `pheno_vendor/` - Vendored packages committed
- [x] `sitecustomize.py` - Adds pheno_vendor to path
- [x] `lib/` - 3-layer architecture complete

### ✅ Architecture Complete

- [x] `lib/base/` - Abstract interfaces (→ pheno-sdk)
- [x] `lib/platforms/` - Platform implementations (→ pheno-sdk)
- [x] `lib/atoms/` - Atoms-specific (stays here)
- [x] `atoms-mcp.py` - Uses new Atoms functions

### ✅ Documentation

- [x] `lib/ARCHITECTURE.md` - Architecture overview
- [x] `lib/MIGRATION_TO_PHENO_SDK.md` - Migration guide
- [x] `DEPLOYMENT_FIX_SUMMARY.md` - Deployment fix details
- [x] `FINAL_ARCHITECTURE_SUMMARY.md` - Complete summary
- [x] `DEPLOYMENT_CHECKLIST.md` - This file

## Deployment Steps

### 1. Commit Changes

```bash
# Add all updated files
git add build.sh vercel.json lib/ atoms-mcp.py \
        DEPLOYMENT_FIX_SUMMARY.md \
        FINAL_ARCHITECTURE_SUMMARY.md \
        DEPLOYMENT_CHECKLIST.md

# Commit
git commit -m "Refactor to 3-layer architecture + fix Vercel deployment

- Created framework-agnostic 3-layer architecture
- lib/base/ - Abstract interfaces (ready for pheno-sdk)
- lib/platforms/ - Platform implementations (ready for pheno-sdk)
- lib/atoms/ - Atoms-specific implementations
- Fixed Vercel deployment: build.sh replaces requirements.txt
- Updated atoms-mcp.py to use new Atoms functions
- Comprehensive documentation added"

# Push
git push
```

### 2. Deploy to Preview

```bash
# Deploy
./atoms deploy --preview

# Expected output:
# - build.sh runs and replaces requirements.txt
# - Vercel installs from requirements-prod.txt (no editable installs)
# - Deployment succeeds
# - Health check passes
```

### 3. Verify Deployment

```bash
# Check health
curl https://devmcp.atoms.tech/health

# Check MCP endpoint
curl https://devmcp.atoms.tech/api/mcp

# Test with MCP client
# Use URL: https://devmcp.atoms.tech/api/mcp
```

### 4. Deploy to Production (if preview works)

```bash
# Deploy
./atoms deploy --production

# Type 'yes' to confirm

# Verify
curl https://atomcp.kooshapari.com/health
curl https://atomcp.kooshapari.com/api/mcp
```

## Post-Deployment

### ✅ Verify Everything Works

- [ ] Preview deployment succeeded
- [ ] Health check passes
- [ ] MCP endpoint responds
- [ ] OAuth flow works
- [ ] Tests pass against preview
- [ ] Production deployment succeeded (if deployed)

### ✅ Monitor

- [ ] Check Vercel dashboard for logs
- [ ] Monitor error rates
- [ ] Check performance metrics
- [ ] Verify all features work

## Migration to Pheno-SDK (Optional)

### When Ready

Follow `lib/MIGRATION_TO_PHENO_SDK.md`:

```bash
# 1. Copy to pheno-sdk
cp -r lib/base/ ../pheno-sdk/deploy-kit/base/
cp -r lib/platforms/ ../pheno-sdk/deploy-kit/platforms/

# 2. Update Atoms imports
# Edit lib/atoms/deployment.py
# Change: from ..base.deployment import ...
# To: from deploy_kit.base import ...

# 3. Remove migrated files
rm -rf lib/base/ lib/platforms/

# 4. Update requirements.txt
echo "-e ../pheno-sdk/deploy-kit" >> requirements.txt

# 5. Test
./atoms --help
./atoms deploy --preview
```

## Troubleshooting

### Deployment Fails with Editable Install Error

**Problem:** Vercel still trying to install from requirements.txt

**Solution:**
```bash
# Verify build.sh is executable
chmod +x build.sh

# Verify vercel.json has buildCommand
cat vercel.json | grep buildCommand

# Should see: "buildCommand": "bash build.sh"
```

### Import Errors

**Problem:** Cannot import from lib.atoms

**Solution:**
```bash
# Verify lib structure
ls -la lib/
ls -la lib/base/
ls -la lib/platforms/
ls -la lib/atoms/

# Test imports
python -c "from lib.atoms import deploy_atoms_to_vercel; print('OK')"
```

### Health Check Fails

**Problem:** Deployment succeeds but health check fails

**Solution:**
```bash
# Check Vercel logs
vercel logs

# Check environment variables in Vercel dashboard
# Ensure WORKOS_CLIENT_ID, WORKOS_API_KEY, etc. are set

# Wait longer (deployment may still be propagating)
sleep 10
curl https://devmcp.atoms.tech/health
```

## Success Criteria

### ✅ Deployment

- [x] build.sh replaces requirements.txt
- [ ] Vercel deployment succeeds
- [ ] No editable install errors
- [ ] Health check passes
- [ ] MCP endpoint responds

### ✅ Architecture

- [x] 3-layer architecture implemented
- [x] Framework-agnostic base classes
- [x] Platform-specific implementations
- [x] Atoms-specific wrappers
- [x] Comprehensive documentation

### ✅ Ready for Pheno-SDK

- [x] Base classes are framework-agnostic
- [x] Platform classes are app-agnostic
- [x] Clear migration path documented
- [x] Easy to extract to pheno-sdk

## Summary

### What Was Done

1. ✅ Created 3-layer architecture (base, platforms, atoms)
2. ✅ Fixed Vercel deployment (build.sh replaces requirements.txt)
3. ✅ Updated atoms-mcp.py to use new functions
4. ✅ Comprehensive documentation
5. ✅ Ready for pheno-sdk migration

### Next Steps

1. [ ] Commit and push changes
2. [ ] Deploy to preview
3. [ ] Verify deployment works
4. [ ] Deploy to production
5. [ ] (Optional) Migrate to pheno-sdk

### Files to Commit

```
build.sh
vercel.json
lib/base/
lib/platforms/
lib/atoms/
lib/ARCHITECTURE.md
lib/MIGRATION_TO_PHENO_SDK.md
atoms-mcp.py
DEPLOYMENT_FIX_SUMMARY.md
FINAL_ARCHITECTURE_SUMMARY.md
DEPLOYMENT_CHECKLIST.md
```

**Ready to deploy!** 🚀

