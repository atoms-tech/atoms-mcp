# Getting Real AuthKit JWT Token via OAuth Flow

## Quick Start

To get a real AuthKit JWT token for E2E testing:

```bash
# 1. Set required environment variables
export WORKOS_API_KEY="your-api-key"
export WORKOS_CLIENT_ID="your-client-id"
export WORKOS_REDIRECT_URI="http://localhost:3000/callback"

# 2. Run the OAuth flow script
python scripts/get_authkit_token_oauth.py

# 3. Complete OAuth flow in browser (script opens it automatically)

# 4. Script outputs token - set it as environment variable
export ATOMS_TEST_AUTH_TOKEN="your-token-here"

# 5. Run E2E tests
pytest -q -n 8 tests/e2e/test_data_management.py
```

## How It Works

The script performs the standard OAuth 2.0 authorization code flow:

1. **Get Authorization URL**: Uses WorkOS SDK to get AuthKit authorization URL
2. **Start Local Server**: Starts HTTP server on `localhost:3000` to receive callback
3. **Open Browser**: Automatically opens browser to authorization URL
4. **User Authentication**: You login with your credentials (kooshapari@kooshapari.com)
5. **Receive Callback**: Local server receives authorization code
6. **Exchange for Token**: Exchanges authorization code for AuthKit JWT token
7. **Output Token**: Prints token that you can use for testing

## Environment Variables

### Required

- `WORKOS_API_KEY`: Your WorkOS API key
- `WORKOS_CLIENT_ID`: Your WorkOS Client ID (AuthKit application)
- `WORKOS_REDIRECT_URI`: OAuth redirect URI (default: `http://localhost:3000/callback`)

### Optional

- `WORKOS_COOKIE_PASSWORD`: For sealed sessions (advanced)

## Manual Flow (Alternative)

If you prefer to do the OAuth flow manually:

1. **Get Authorization URL**:
   ```python
   from workos import WorkOS
   workos = WorkOS(api_key="your-key")
   auth_url = workos.user_management.get_authorization_url(
       provider="authkit",
       redirect_uri="http://localhost:3000/callback"
   )
   print(auth_url)
   ```

2. **Visit URL in Browser**: Complete login

3. **Extract Code**: From callback URL `http://localhost:3000/callback?code=...`

4. **Exchange for Token**:
   ```python
   auth_response = workos.user_management.authenticate_with_code(
       code="authorization-code",
       redirect_uri="http://localhost:3000/callback"
   )
   token = auth_response.access_token  # or auth_response.token
   ```

5. **Set Environment Variable**:
   ```bash
   export ATOMS_TEST_AUTH_TOKEN="your-token"
   ```

## Using the Token in Tests

The `authkit_auth_token` fixture automatically detects and uses `ATOMS_TEST_AUTH_TOKEN`:

```python
# tests/e2e/conftest.py automatically uses:
# - ATOMS_TEST_AUTH_TOKEN (if set)
# - ATOMS_INTERNAL_TOKEN (if set and no AuthKit token)
# - Unsigned JWT (if ATOMS_TEST_MODE=true)
```

No code changes needed - just set the environment variable!

## Troubleshooting

### "Failed to get authorization URL"

- Check `WORKOS_API_KEY` and `WORKOS_CLIENT_ID` are set correctly
- Verify AuthKit is configured in WorkOS Dashboard
- Check redirect URI matches WorkOS configuration

### "No code in callback"

- Ensure redirect URI in script matches WorkOS Dashboard configuration
- Check that local server started successfully (port 3000 available)
- Verify browser completed OAuth flow

### "Failed to authenticate with code"

- Authorization code may have expired (they're single-use)
- Check WorkOS API key has correct permissions
- Verify redirect URI matches exactly

### "No token in response"

- WorkOS response structure may vary
- Check if using sealed sessions (requires `WORKOS_COOKIE_PASSWORD`)
- Token might be in different field (`access_token` vs `token`)

## Token Expiration

AuthKit tokens typically expire after 1 hour. If tests start failing with authentication errors:

1. Re-run `scripts/get_authkit_token_oauth.py` to get a fresh token
2. Update `ATOMS_TEST_AUTH_TOKEN` environment variable
3. Re-run tests

## Security Notes

- **Never commit tokens to git**: Use environment variables only
- **Tokens are sensitive**: Treat them like passwords
- **Rotate regularly**: Get new tokens periodically
- **Use test accounts**: Don't use production user accounts for testing
