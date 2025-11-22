# E2E Testing Guide

## What is E2E Testing?

**E2E (End-to-End) tests** = Live HTTP calls against the **deployed server** with **real actions on your account**.

- ✅ Tests make actual HTTP requests to `mcpdev.atoms.tech`
- ✅ Tests use real WorkOS authentication tokens
- ✅ Tests create/modify/delete real data in your Supabase database
- ✅ Tests verify the entire system works end-to-end

## Test Environments

### 1. **Unit Tests** (Local, Fast, Mocked)
```bash
python -m pytest tests/unit
```
- In-memory mocks
- No external services
- ~1 second per test
- Use: `tests/unit/`

### 2. **E2E Tests** (Flexible Targeting via atoms CLI)
All E2E tests use **real WorkOS authentication** with the same keys from `.env`

**Local Server:**
```bash
# Terminal 1: Start local server
python server.py

# Terminal 2: Run E2E tests against local server
atoms test:e2e --env local
```
- Local server at `http://localhost:8000`
- Real Supabase database
- Real WorkOS JWT (same keys as prod)
- ~2-5 seconds per test

**Development Server:**
```bash
atoms test:e2e --env dev
```
- Deployed server at `mcpdev.atoms.tech`
- Real WorkOS authentication
- Real data on dev account
- ~5-10 seconds per test

**Production Server:**
```bash
atoms test:e2e --env prod
```
- Deployed server at `mcp.atoms.tech`
- Real WorkOS authentication
- Real data on prod account
- ~5-10 seconds per test

## Authentication Flow

All environments use **real WorkOS authentication** with the same keys:

```
Test → WorkOS Password Grant → Real JWT → Target Server → Validates JWT
                                              ↓
                                    Local (localhost:8000)
                                    Dev (mcpdev.atoms.tech)
                                    Prod (mcp.atoms.tech)
```

**Key Point:** Local server uses the same WorkOS keys as dev/prod (from `.env`)

## Running Tests

### Using atoms CLI (Recommended)

**Run E2E tests against local server:**
```bash
atoms test:e2e --env local
```

**Run E2E tests against dev server:**
```bash
atoms test:e2e --env dev
```

**Run E2E tests against prod server:**
```bash
atoms test:e2e --env prod
```

**Run unit tests:**
```bash
atoms test:unit
```

### Using pytest directly

**Run all E2E tests (uses dev by default):**
```bash
python -m pytest tests/e2e -m e2e
```

**Run specific E2E test:**
```bash
python -m pytest tests/e2e/test_organization_crud.py -xvs
```

**Run unit tests:**
```bash
python -m pytest tests/unit -m unit
```

## Important Notes

1. **E2E tests make REAL changes** - They create/modify/delete actual data
2. **All environments use real WorkOS JWT** - Same keys from `.env` for local/dev/prod
3. **Use `--scope` not `--marker`** - `atoms test --scope e2e` respects `--env` flag
4. **Slower than unit tests** - Network latency + real database operations
5. **Use for production validation** - Verify system works end-to-end
6. **Local server uses same WorkOS keys as prod** - No special test mode needed

## Common Mistakes

❌ **Wrong:** `atoms test --marker e2e --env local`
- `--marker` doesn't properly set up environment

✅ **Right:** `atoms test --scope e2e --env local`
- `--scope` properly sets up environment via TestEnvManager

❌ **Wrong:** `pytest tests/e2e -m e2e`
- Bypasses atoms CLI environment setup

✅ **Right:** `atoms test:e2e --env local`
- Uses atoms CLI to set up environment

## Troubleshooting

### Tests fail with "invalid_token"
- Check `WORKOS_API_KEY` and `WORKOS_CLIENT_ID` are set
- Token may have expired - tests will get a new one
- Check server logs for auth errors

### Tests pass but no data created
- Check you're using the right server (mcpdev.atoms.tech for E2E)
- Check Supabase database for created entities
- Check test output for actual HTTP requests

### Tests are slow
- E2E tests are slower (network + database)
- Use integration tests for faster feedback
- Use unit tests for TDD

