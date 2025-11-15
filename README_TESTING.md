# Testing & Deployment - Quick Start

## TL;DR - Just Run These Commands

### Local Development (No Deployment)
```bash
atoms test                    # Run unit tests locally
atoms test:cov               # With coverage report
```

### Test Against Dev Deployment (mcpdev.atoms.tech)
```bash
atoms test:int               # Integration tests
atoms test:e2e               # E2E tests
```

### Test Against Production (mcp.atoms.tech)
```bash
atoms test:e2e --env prod    # Full E2E against production
```

That's it! The CLI automatically selects the correct environment.

---

## Deployment Status

✅ **Vercel Deployment**: `https://mcpdev.atoms.tech`  
✅ **Auto-Targeting CLI**: Implemented & working  
✅ **Test Fixtures**: Updated to use deployed instance  
✅ **Documentation**: Complete  

---

## How It Works

| Test Type | Default Target | Can Override? |
|-----------|----------------|--------------|
| Unit tests | Local | No (always local) |
| Integration | Dev | Yes (`--env local\|prod`) |
| E2E | Dev | Yes (`--env local\|prod`) |

---

## Environment Targets

**Local**: `http://127.0.0.1:8000` (development)  
**Dev**: `https://mcpdev.atoms.tech` (testing)  
**Prod**: `https://mcp.atoms.tech` (production)

---

## Common Commands

```bash
# Development
atoms test                              # Unit tests
atoms test:cov                          # With coverage

# Test deployment
atoms test:int                          # Integration → dev
atoms test:e2e                          # E2E → dev

# Production
atoms test:e2e --env prod              # E2E → production

# Override to local (troubleshooting)
atoms test:int --env local             # Integration → local
atoms test:e2e --env local             # E2E → local
```

---

## Documentation

- **USAGE_GUIDE.md** - Complete usage reference
- **DEPLOYMENT_TEST_GUIDE.md** - Detailed deployment guide
- **TEST_ENVIRONMENT_AUTO_TARGETING.md** - Architecture & implementation
- **VALIDATION_SUMMARY.md** - Architecture overview

---

## Key Features

✨ **Zero Configuration** - Just run tests, environment is auto-selected  
✨ **Smart Defaults** - Unit→local, Integration/E2E→dev  
✨ **Flexible Overrides** - Change targets with `--env` flag  
✨ **Clear Feedback** - CLI prints which environment it's using  
✨ **Automatic Setup** - Environment variables configured automatically  

---

## What Was Deployed

### 1. Vercel Deployment
- MCP Server live at `https://mcpdev.atoms.tech`
- Production deployment at `https://mcp.atoms.tech`
- Ready for integration & E2E testing

### 2. Test Environment Manager
- `cli_modules/test_env_manager.py` - Core logic
- Auto-detection based on test scope
- Health check verification
- Safe environment variable handling

### 3. Updated CLI Commands
- `atoms test` - with `--scope` and `--env` options
- `atoms test:unit` - always local
- `atoms test:int` - default dev, override with `--env`
- `atoms test:e2e` - default dev, override with `--env`
- `atoms test:cov` - coverage report

### 4. Updated Test Fixtures
- Integration tests read `MCP_INTEGRATION_BASE_URL`
- E2E tests read `MCP_E2E_BASE_URL`
- Both support deployed and local testing

---

## Next Steps

1. **Run unit tests** (no setup needed):
   ```bash
   atoms test
   ```

2. **Run integration tests** (auto-targets dev):
   ```bash
   atoms test:int
   ```

3. **Run E2E tests** (auto-targets dev):
   ```bash
   atoms test:e2e
   ```

4. **Test against production** (when ready):
   ```bash
   atoms test:e2e --env prod
   ```

---

## Verify It's Working

```bash
# Check unit tests run
atoms test -k "test_auth" | head -20

# Check environment detection
python3 -c "
from cli_modules.test_env_manager import TestEnvManager
env = TestEnvManager.get_environment_for_scope('integration')
print(f'Integration tests target: {env.value}')
"
```

---

## Troubleshooting

### Tests timeout or fail
1. Check which environment is being used (CLI prints it)
2. Verify that environment is accessible
3. Try local first: `atoms test:int --env local`

### Deployment unreachable
1. Check health: `curl https://mcpdev.atoms.tech/health`
2. Override to local: `atoms test:int --env local`

### Wrong environment targeted
1. Check help: `atoms test:int --help`
2. Remember: only `--env` overrides defaults
3. Unit tests ALWAYS use local (correct behavior)

---

## Summary

✅ **Deployment**: Live at mcpdev.atoms.tech  
✅ **CLI**: Auto-targets correct environments  
✅ **Tests**: Configured to work with deployed instance  
✅ **Documentation**: Complete with examples  

**Status**: READY TO USE 🚀

See USAGE_GUIDE.md for complete reference.
