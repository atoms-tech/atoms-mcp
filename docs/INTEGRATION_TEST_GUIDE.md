# Integration Test Authentication Guide

This guide explains how to run integration tests with proper authentication using test JWT tokens.

## Overview

Integration tests (`tests/integration/`) need to authenticate API calls to the MCP server. Rather than relying on live Supabase authentication (which requires valid credentials and network access), we generate unsigned JWT tokens locally that work with the test server.

### Token Flow

```
┌─────────────────────────────────────────────────────────────┐
│ Integration Test                                            │
└────────────┬────────────────────────────────────────────────┘
             │
             │ 1. Generate unsigned JWT
             │    (alg: "none")
             ├─────────────────────────────────────┐
             │                                     │
    ┌────────▼────────────────────────┐    ┌──────▼──────────────┐
    │ conftest.py fixture:             │    │ Or use script:      │
    │ integration_auth_token           │    │ generate_authkit    │
    │ (auto-generates locally)         │    │ _token.py           │
    │                                  │    │ (manual generation) │
    └────────┬────────────────────────┘    └──────┬──────────────┘
             │                                     │
             └──────────────┬──────────────────────┘
                            │
             2. Pass as Bearer token header
             ┌──────────────▼──────────────────────┐
             │ HTTP Request to MCP server         │
             │ Authorization: Bearer <token>      │
             └──────────────┬──────────────────────┘
                            │
             3. Server validates unsigned JWT
             ┌──────────────▼──────────────────────┐
             │ HybridAuthProvider (server.py)      │
             │ _verify_unsigned_jwt()              │
             │ Requires: ATOMS_TEST_MODE=true      │
             └──────────────┬──────────────────────┘
                            │
                            ✅ Authenticated
```

## Running Integration Tests

### Option 1: Automatic (Recommended)

The integration test suite automatically generates tokens when run:

```bash
# Run integration tests with auto-generated token
python cli.py test run --scope integration

# Or run specific test
python cli.py test run tests/integration/test_database_operations.py -k test_connection_pool_reuse
```

**What happens automatically:**
1. `conftest.py` creates `integration_auth_token` fixture
2. Token is generated locally (no external API calls)
3. Server starts with `ATOMS_TEST_MODE=true`
4. All requests use the generated token

### Option 2: Pre-generate Token for Manual Testing

For debugging or manual API testing:

```bash
# Generate token and output as JSON
python scripts/generate_authkit_token.py --output json

# Or output as environment variable
export ATOMS_TEST_AUTH_TOKEN=$(python scripts/generate_authkit_token.py)

# Or output as HTTP headers
python scripts/generate_authkit_token.py --output headers
```

### Option 3: Custom Token

Use environment variables to customize the token:

```bash
export AUTHKIT_EMAIL="custom@example.com"
export AUTHKIT_USER_ID="custom-user-id"
export AUTHKIT_NAME="Custom User"
export AUTHKIT_TOKEN_DURATION="7200"  # 2 hours

python cli.py test run --scope integration
```

## Token Structure

Unsigned JWT tokens have 3 parts separated by dots: `header.payload.signature`

### Header
```json
{
  "alg": "none",
  "typ": "JWT"
}
```

### Payload (Claims)
```json
{
  "sub": "uuid-of-user",
  "email": "kooshapari@kooshapari.com",
  "email_verified": true,
  "aud": "fastmcp-mcp-server",
  "iss": "authkit-test-generator",
  "iat": 1763186398,
  "exp": 1763189998,
  "name": "Kosh Apari",
  "given_name": "Kosh",
  "family_name": "Apari"
}
```

### Signature
Empty (no signature for unsigned tokens)

### Decode a Token

```bash
# View token claims
python scripts/generate_authkit_token.py --decode

# Output:
# Token Claims:
# {
#   "sub": "abc-123-def-456",
#   "email": "kooshapari@kooshapari.com",
#   ...
# }
```

## Requirements for Token Acceptance

For unsigned tokens to work, the MCP server must:

1. **Have `ATOMS_TEST_MODE=true`** in environment variables
2. **Use HybridAuthProvider** with unsigned JWT verification enabled
3. **Handle Bearer tokens** in Authorization header

### Verify Server Configuration

```bash
# Check if ATOMS_TEST_MODE is set
echo $ATOMS_TEST_MODE

# Check server auth configuration (from logs)
# Should see: "✅ Unsigned JWT verified in test mode: sub=..."

# Start server with test mode
export ATOMS_TEST_MODE=true
python app.py
```

## Testing API Endpoints Manually

Once you have a token, you can test the API:

```bash
# Generate token
TOKEN=$(python scripts/generate_authkit_token.py)

# Test MCP endpoint with Bearer token
curl -X POST http://localhost:8000/api/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "1",
    "method": "tools/list"
  }'

# Expected response:
# {
#   "jsonrpc": "2.0",
#   "id": "1",
#   "result": {
#     "tools": [...]
#   }
# }
```

## Troubleshooting

### Problem: "401 Unauthorized" on Integration Tests

**Cause:** Server not accepting unsigned JWT tokens.

**Solutions:**

1. **Check ATOMS_TEST_MODE is enabled:**
   ```bash
   echo $ATOMS_TEST_MODE
   # Should output: true
   ```

2. **Verify HybridAuthProvider is configured:**
   ```bash
   # In server.py, check that HybridAuthProvider is used with unsigned JWT support
   grep -A 5 "unsigned.*jwt\|ATOMS_TEST_MODE" server.py
   ```

3. **Check server logs for auth errors:**
   ```bash
   export LOG_LEVEL=DEBUG
   python cli.py test run --scope integration
   # Look for: "Unsigned JWT verified" or "Bearer token verification failed"
   ```

### Problem: Token Expired

**Cause:** Default token expiration is 1 hour.

**Solution:** Generate new token or increase duration:

```bash
# Generate token that's valid for 24 hours
export AUTHKIT_TOKEN_DURATION="86400"
export ATOMS_TEST_AUTH_TOKEN=$(python scripts/generate_authkit_token.py)

python cli.py test run --scope integration
```

### Problem: "Invalid JWT format"

**Cause:** Token doesn't have 3 parts separated by dots.

**Solution:** Regenerate token:

```bash
# Should output something like:
# eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiI4MTU2YTQ5ZC1mNzUyLTQzZGEtOTQwMi1kMDA0MjgyMDU5YmIiLCJlbWFpbCI6Imtvb3NoYXBhcmhAa29vc2hhcGFyaS5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiYXVkIjoiZmFzdG1jcC1tY3Atc2VydmVyIiwiaXNzIjoiYXV0aGtpdC10ZXN0LWdlbmVyYXRvciIsImlhdCI6MTc2MzE4NjUyMiwiZXhwIjoxNzYzMTkwMTIyLCJuYW1lIjoiS29zaCBBcGFyaSIsImdpdmVuX25hbWUiOiJLb3NoIiwiZmFtaWx5X25hbWUiOiJBcGFyaSJ9.

python scripts/generate_authkit_token.py
```

## CI/CD Integration

For GitHub Actions or other CI/CD systems:

```yaml
# .github/workflows/integration-tests.yml
name: Integration Tests
on: [push]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.12"
      
      - name: Generate Auth Token
        run: |
          export ATOMS_TEST_AUTH_TOKEN=$(python scripts/generate_authkit_token.py)
          echo "ATOMS_TEST_AUTH_TOKEN=$ATOMS_TEST_AUTH_TOKEN" >> $GITHUB_ENV
      
      - name: Run Integration Tests
        env:
          ATOMS_TEST_MODE: "true"
        run: |
          python cli.py test run --scope integration
```

## Understanding Test Modes

The system supports three auth modes:

| Mode | Token Type | Use Case | Setup |
|------|-----------|----------|-------|
| **Unit** | In-Memory | Fast local testing | No auth needed |
| **Integration** | Unsigned JWT | Test with real server | `ATOMS_TEST_MODE=true` |
| **Production** | AuthKit OAuth | Live user auth | Real AuthKit domain |

### Unit Tests (Fast, No Auth Needed)

```bash
python cli.py test run --scope unit
# Uses InMemoryMcpClient (no authentication)
```

### Integration Tests (With Test Token)

```bash
export ATOMS_TEST_MODE=true
python cli.py test run --scope integration
# Generates unsigned JWT automatically
```

### Production Tests (With Real OAuth)

```bash
export ATOMS_TEST_MODE=false
python cli.py test run --scope integration --env prod
# Requires live AuthKit and valid credentials
```

## References

- **Token Generation**: `scripts/generate_authkit_token.py`
- **Server Auth**: `services/auth/hybrid_auth_provider.py`
- **Test Fixtures**: `tests/integration/conftest.py`
- **OAuth Setup**: `docs/authkit_setup_guide.md`
- **FastMCP Auth**: `llms-full.txt` (section 0-15)
