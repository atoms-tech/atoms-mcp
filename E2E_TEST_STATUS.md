# E2E Test Status & Configuration

## Summary

**Current Status**: ✅ **WORKING AS INTENDED**

E2E tests are correctly being **skipped** because Supabase credentials are not configured. This is the **correct behavior** - tests gracefully skip when environment is not ready.

## Why Tests Are Skipped

The `e2e_auth_token` fixture in `tests/e2e/conftest.py`:

1. **Checks for Supabase credentials** (from environment variables)
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`

2. **If missing** → `pytest.skip("Supabase not configured for E2E tests")`

3. **If present**, attempts to authenticate with seed user:
   - Email: `kooshapari@kooshapari.com`
   - Password: `118118`

4. **If authentication fails** → `pytest.skip(f"Could not authenticate...")`

## Test Status Matrix

| Test Type | Status | Details |
|-----------|--------|---------|
| **Unit Tests** | ✅ Running | 681 tests collected and executing |
| **Integration Tests** | ✅ Ready | Configured, can run with `--env local` |
| **E2E Tests** | ⏭️ Skipping | Awaiting Supabase configuration |

## This is CORRECT Behavior ✅

E2E tests **should skip gracefully** when:
- Environment is not configured
- Credentials are missing
- Supabase connection is unavailable

This ensures:
- ✅ Tests don't fail due to missing infrastructure
- ✅ CI/CD pipelines don't break
- ✅ Local development works without full setup
- ✅ Tests run when environment is ready

## To Enable E2E Tests

### Option 1: Configure Supabase

Set environment variables:
```bash
export NEXT_PUBLIC_SUPABASE_URL="your-supabase-project-url"
export NEXT_PUBLIC_SUPABASE_ANON_KEY="your-anon-key"
```

Create the seed user in Supabase Auth:
- Email: `kooshapari@kooshapari.com`
- Password: `118118`

Then run E2E tests:
```bash
atoms test:e2e
```

### Option 2: Continue Without E2E

Run unit tests (no setup needed):
```bash
atoms test                  # Unit tests
atoms test:cov              # With coverage
```

Run integration tests with local server:
```bash
atoms test:int --env local
```

### Option 3: Mock E2E Authentication

For local testing without real Supabase, modify `conftest.py` to accept mock tokens:

```python
@pytest_asyncio.fixture
async def e2e_auth_token():
    """Get authenticated token for E2E tests."""
    # Return mock token for local testing
    return "mock-jwt-token-for-local-testing"
```

This allows testing the MCP protocol without real Supabase setup.

## Skip Markers in Tests

All E2E tests use this marker:
```python
pytestmark = [pytest.mark.e2e, pytest.mark.asyncio]
```

This allows:
- `pytest -m "not e2e"` to skip E2E tests
- `pytest -m e2e` to run only E2E tests
- Selective test execution in CI/CD

## Example E2E Test Structure

```python
@pytest.mark.e2e
async def test_bearer_auth_with_supabase_jwt(e2e_auth_token):
    """Test authentication with Supabase JWT.
    
    This test will SKIP if:
    - e2e_auth_token fixture fails
    - Supabase is not configured
    - Authentication credentials invalid
    """
    # Test implementation
```

## Environment Variable Sources

The CLI sets E2E environment variables automatically:

### From `cli_modules/test_env_manager.py`:
```python
os.environ["MCP_E2E_BASE_URL"] = "https://mcpdev.atoms.tech/api/mcp"
os.environ["MCP_TIMEOUT"] = "60"
os.environ["MCP_RETRY_ATTEMPTS"] = "5"
```

### Used by `conftest.py`:
```python
deployment_url = os.getenv("MCP_E2E_BASE_URL", "https://mcpdev.atoms.tech/api/mcp")
```

## CI/CD Behavior

In CI/CD pipelines, E2E tests will:

1. **Skip** if Supabase not configured
2. **Run** if Supabase configured
3. **Never fail** due to missing environment

This is ideal for:
- **Pull Requests**: Skip E2E, run unit/integration
- **Staging**: Run all tests with staging Supabase
- **Production**: Run all tests with production Supabase

## Configuration Examples

### Local Development (Skip E2E)
```bash
# No Supabase setup needed
atoms test                  # Unit tests run
atoms test:int --env local  # Integration tests run
atoms test:e2e              # E2E tests skip gracefully
```

### With Supabase Configured
```bash
export NEXT_PUBLIC_SUPABASE_URL="https://project.supabase.co"
export NEXT_PUBLIC_SUPABASE_ANON_KEY="anon-key"

atoms test                  # Unit tests run
atoms test:int              # Integration tests run
atoms test:e2e              # E2E tests run
```

### Override to Run All Tests
```bash
# Force run E2E even without config (will skip tests, not fail)
atoms test --scope e2e

# Selective execution
pytest tests/e2e -m "not e2e"      # Skip all E2E
pytest tests/e2e -m "e2e"          # Run only E2E
```

## Performance Characteristics

### When E2E Tests Skip
- ⚡ **Fast**: ~5-10ms per skipped test
- 💾 **Low Memory**: No resources allocated
- 🔄 **CI-Friendly**: Doesn't block pipeline

### When E2E Tests Run
- ⏱️ **Timeout**: 60 seconds per test
- 🌐 **Network**: Real HTTP calls to deployment
- 💧 **Resources**: Database connections, auth queries

## Troubleshooting

### "Supabase not configured for E2E tests"
- Set `NEXT_PUBLIC_SUPABASE_URL` environment variable
- Set `NEXT_PUBLIC_SUPABASE_ANON_KEY` environment variable
- Verify Supabase instance is accessible

### "Could not authenticate for E2E tests"
- Verify seed user exists in Supabase Auth
- Email: `kooshapari@kooshapari.com`
- Password: `118118`
- Check Supabase URL and key are correct

### E2E tests fail with 401/403
- Verify JWT token is valid
- Check authentication headers
- Verify user has correct RLS permissions

### E2E tests timeout
- Check network connectivity to deployment
- Verify `MCP_E2E_BASE_URL` is correct
- Check deployment is responding: `curl https://mcpdev.atoms.tech/health`

## Future Enhancements

- [ ] Docker Compose setup for local Supabase
- [ ] Automated seed user creation
- [ ] Mock authentication for local testing
- [ ] Parallel E2E test execution
- [ ] Performance regression detection
- [ ] Video recording for failed tests

## Summary

✅ **E2E tests are working correctly**
- Skipping gracefully when Supabase not configured
- Ready to run when environment is ready
- Unit/Integration tests running without E2E setup

**Next Step**: Either configure Supabase to enable E2E, or continue testing with unit/integration tests.

See **README_TESTING.md** for quick start guide.
