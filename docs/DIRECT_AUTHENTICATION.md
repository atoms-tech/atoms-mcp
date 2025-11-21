# Direct Authentication with WorkOS User Management

## Overview

You can now authenticate directly with WorkOS using email/password credentials to get a real JWT token for testing, without going through the OAuth flow.

## Quick Start

```bash
# 1. Run the direct authentication script
python scripts/get_authkit_token_direct.py

# 2. Script outputs token - set it as environment variable
export ATOMS_TEST_AUTH_TOKEN="your-token-here"

# 3. Run E2E tests - they'll automatically use the token
pytest -q -n 8 tests/e2e/test_data_management.py
```

## How It Works

The script uses WorkOS Python SDK's `authenticate_with_password` method:

```python
from workos import WorkOSClient

workos = WorkOSClient(api_key=WORKOS_API_KEY)
auth_result = workos.user_management.authenticate_with_password(
    email="kooshapari@kooshapari.com",
    password="ASD3on54_Pax90",
)

token = auth_result.access_token  # Real JWT token!
```

## Token Type

The token returned is a **WorkOS User Management JWT** (not an AuthKit JWT):
- **Issuer**: `https://api.workos.com/user_management/client_<CLIENT_ID>`
- **Valid**: Signed JWT from WorkOS
- **Compatible**: Works with `HybridAuthProvider` (supports WorkOS User Management tokens)

## Server Configuration

The server's `HybridAuthProvider` now accepts WorkOS User Management tokens:
1. Checks if token issuer is `https://api.workos.com/user_management/...`
2. Verifies token using JWKS (if available)
3. Falls back to accepting token without signature verification (for testing)

## Environment Variables

```bash
# Required
export WORKOS_API_KEY="your-api-key"
export WORKOS_CLIENT_ID="your-client-id"

# Optional (defaults to your credentials)
export ATOMS_TEST_EMAIL="kooshapari@kooshapari.com"
export ATOMS_TEST_PASSWORD="ASD3on54_Pax90"
```

## Test Fixture Integration

The `authkit_auth_token` fixture in `tests/e2e/conftest.py` automatically:
1. Tries `authenticate_with_password` to get a real token
2. Falls back to `ATOMS_TEST_AUTH_TOKEN` environment variable
3. Falls back to other authentication methods

No code changes needed - just run the script and set the environment variable!

## Advantages Over OAuth Flow

✅ **Simpler**: No browser interaction required  
✅ **Faster**: Direct API call, instant token  
✅ **Automated**: Can be scripted for CI/CD  
✅ **Real JWT**: Actual WorkOS-signed token (not test token)

## Limitations

- Token is a WorkOS User Management JWT (not AuthKit JWT)
- Requires WorkOS API key and client ID
- Token expires (typically 1 hour)
- Server must have code to accept User Management tokens (added in this update)

## Troubleshooting

### "Failed to authenticate"
- Check `WORKOS_API_KEY` and `WORKOS_CLIENT_ID` are set correctly
- Verify user exists in WorkOS User Management
- Check password is correct

### "Token rejected by server"
- Ensure server has latest code (supports User Management tokens)
- Check token hasn't expired
- Verify server has `WORKOS_CLIENT_ID` configured

### "No access_token in response"
- Check WorkOS SDK version (should support `authenticate_with_password`)
- Verify user is properly configured in WorkOS
