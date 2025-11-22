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

### 2. **Integration Tests** (Local Server, Real Services)
```bash
# Terminal 1: Start local server
python server.py

# Terminal 2: Run integration tests
MCP_E2E_BASE_URL=http://localhost:8000/api/mcp python -m pytest tests/e2e
```
- Real local server at `http://localhost:8000`
- Real Supabase database
- Unsigned JWTs (test mode)
- ~2-5 seconds per test
- Use: `tests/e2e/` with `MCP_E2E_BASE_URL=http://localhost:8000/api/mcp`

### 3. **E2E Tests** (Deployed Server, Real Authentication)
```bash
# Requires WorkOS credentials
export WORKOS_API_KEY=<your_key>
export WORKOS_CLIENT_ID=<your_client_id>

# Run E2E tests against deployed server
python -m pytest tests/e2e
```
- Deployed server at `mcpdev.atoms.tech`
- Real WorkOS authentication
- Real data on your account
- ~5-10 seconds per test
- Use: `tests/e2e/` (default)

## Authentication Flow

### Local Testing (Integration)
```
Test → Unsigned JWT (test mode) → Local Server → Accepts unsigned JWT
```

### Deployed Testing (E2E)
```
Test → WorkOS Password Grant → Real JWT → mcpdev.atoms.tech → Validates JWT
```

## Running Tests

### Run all E2E tests (deployed server)
```bash
python cli.py test --scope e2e
```

### Run specific E2E test
```bash
python -m pytest tests/e2e/test_organization_crud.py -xvs
```

### Run integration tests (local server)
```bash
MCP_E2E_BASE_URL=http://localhost:8000/api/mcp python -m pytest tests/e2e
```

### Run unit tests
```bash
python cli.py test --scope unit
```

## Important Notes

1. **E2E tests make REAL changes** - They create/modify/delete actual data
2. **Requires authentication** - Set `WORKOS_API_KEY` and `WORKOS_CLIENT_ID`
3. **Slower than unit tests** - Network latency + real database operations
4. **Use for production validation** - Verify system works end-to-end
5. **Use integration tests for development** - Faster feedback loop

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

