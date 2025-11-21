# How to Get Real AuthKit JWT Token for Testing

## Quick Answer

Since AuthKit requires OAuth flow (not direct email/password), you have two options:

### Option 1: Use Pre-Obtained Token (Easiest)

1. **Get token manually via OAuth** (see steps below)
2. **Set it as environment variable**:
   ```bash
   export ATOMS_TEST_AUTH_TOKEN="your-authkit-jwt-token-here"
   ```
3. **Run tests** - the fixture will automatically use it

### Option 2: Use Internal Token or Test Mode

```bash
# Option A: Internal token (if server has it configured)
export ATOMS_INTERNAL_TOKEN="your-internal-token"

# Option B: Test mode (server needs ATOMS_TEST_MODE=true)
# Tests will automatically generate unsigned JWTs
```

## Getting AuthKit Token via OAuth Flow

### Step 1: Get Authorization URL

Your AuthKit authorization URL is typically:
```
https://YOUR-AUTHKIT-DOMAIN/authorize?client_id=YOUR_CLIENT_ID&response_type=code&redirect_uri=YOUR_REDIRECT_URI
```

### Step 2: Complete OAuth Flow

1. Visit the authorization URL in your browser
2. Login with your credentials (kooshapari@kooshapari.com / ASD3on54_Pax90)
3. Authorize the application
4. You'll be redirected with an authorization code

### Step 3: Exchange Code for Token

```bash
curl -X POST "https://YOUR-AUTHKIT-DOMAIN/oauth2/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=authorization_code" \
  -d "code=YOUR_AUTHORIZATION_CODE" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "redirect_uri=YOUR_REDIRECT_URI"
```

### Step 4: Extract and Use Token

The response will contain an `access_token`. Set it:

```bash
export ATOMS_TEST_AUTH_TOKEN="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
pytest -q -n 8 tests/e2e/test_data_management.py
```

## Automated Solution (Future)

For fully automated testing, we could:
1. Use Playwright to perform OAuth flow programmatically
2. Extract token automatically
3. Use it in tests

This would require additional setup and dependencies.
