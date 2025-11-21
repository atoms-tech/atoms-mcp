# How to Get a Real AuthKit JWT Token for E2E Testing

## Problem
AuthKit requires OAuth flow, which can't be done directly with email/password. To use real AuthKit JWTs in E2E tests, you need to obtain a token through the OAuth flow.

## Solution Options

### Option 1: Use Pre-Obtained Token (Recommended)

1. **Manually perform OAuth flow** to get an AuthKit token:
   - Visit your AuthKit authorization URL
   - Complete the OAuth flow
   - Extract the `access_token` from the response

2. **Set the token as environment variable**:
   ```bash
   export ATOMS_TEST_AUTH_TOKEN="your-authkit-jwt-token-here"
   ```

3. **Run tests**:
   ```bash
   pytest -q -n 8 tests/e2e/test_data_management.py
   ```

The `authkit_auth_token` fixture will automatically use this token if set.

### Option 2: Use Internal Token

If your server has `ATOMS_INTERNAL_TOKEN` configured:

```bash
export ATOMS_INTERNAL_TOKEN="your-internal-token"
pytest -q -n 8 tests/e2e/test_data_management.py
```

### Option 3: Use Test Mode (Unsigned JWT)

If your server has `ATOMS_TEST_MODE=true`:

```bash
# Server should have ATOMS_TEST_MODE=true
# Tests will automatically generate unsigned JWTs
pytest -q -n 8 tests/e2e/test_data_management.py
```

## Getting AuthKit Token Manually

### Method 1: Using Browser Developer Tools

1. Open your browser and navigate to your AuthKit domain
2. Complete the OAuth login flow
3. Open Developer Tools → Network tab
4. Look for requests to `/oauth2/token` or `/api/auth/sessions`
5. Copy the `access_token` from the response

### Method 2: Using curl/HTTP Client

```bash
# Step 1: Get authorization URL (requires OAuth flow)
# This is complex and typically requires browser interaction

# Step 2: After getting authorization code, exchange for token:
curl -X POST "https://YOUR-AUTHKIT-DOMAIN/oauth2/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=authorization_code" \
  -d "code=YOUR_AUTHORIZATION_CODE" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "redirect_uri=YOUR_REDIRECT_URI"
```

### Method 3: Use WorkOS Dashboard

1. Go to [WorkOS Dashboard](https://dashboard.workos.com)
2. Navigate to your AuthKit application
3. Use the testing tools to generate a token (if available)

## Quick Setup

```bash
# 1. Get your AuthKit token (manually via OAuth flow)
# 2. Set it as environment variable
export ATOMS_TEST_AUTH_TOKEN="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."

# 3. Run tests
pytest -q -n 8 tests/e2e/test_data_management.py
```

The fixture will automatically detect and use this token.
