# Getting AuthKit JWT Tokens for Testing

This guide explains different methods to obtain AuthKit JWT tokens for testing and development.

## Quick Start

The easiest way is to use the direct authentication script:

```bash
python scripts/get_authkit_token_direct.py
```

This will use your default credentials (`kooshapari@kooshapari.com` / `ASD3on54_Pax90`) or you can set:

```bash
ATOMS_TEST_EMAIL=your@email.com ATOMS_TEST_PASSWORD=yourpass python scripts/get_authkit_token_direct.py
```

## Available Methods

### 1. Direct API Authentication (Recommended First Try)

**Script**: `scripts/get_authkit_token_direct.py`

Attempts to authenticate directly with WorkOS User Management API using email/password.

```bash
python scripts/get_authkit_token_direct.py
```

**Pros:**
- ✅ No browser required
- ✅ Fast and automated
- ✅ Works if WorkOS API supports it

**Cons:**
- ❌ May not return JWT tokens directly (WorkOS might return sessions instead)
- ❌ AuthKit typically requires OAuth flow

### 2. Playwright Automated OAuth Flow

**Script**: `scripts/get_authkit_token_playwright.py`

Automates the full OAuth flow using Playwright browser automation.

**Setup:**
```bash
# Install Playwright
pip install playwright

# Install browser binaries
playwright install chromium
```

**Usage:**
```bash
python scripts/get_authkit_token_playwright.py
```

**Pros:**
- ✅ Fully automated OAuth flow
- ✅ Handles browser-based authentication
- ✅ Extracts token from callback

**Cons:**
- ❌ Requires Playwright installation
- ❌ Requires browser binaries
- ❌ Slower than direct API

### 3. Manual OAuth Flow

**Script**: `scripts/get_authkit_token_oauth.py`

Opens browser for you to manually complete OAuth flow.

```bash
python scripts/get_authkit_token_oauth.py
```

**Pros:**
- ✅ Works with any OAuth provider
- ✅ No automation complexity

**Cons:**
- ❌ Requires manual interaction
- ❌ Requires local HTTP server

## Environment Variables

All scripts require:

```bash
WORKOS_API_KEY=sk_test_...
WORKOS_CLIENT_ID=client_123456789
```

For Playwright script, also need:

```bash
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN=https://authkit.workos.com
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL=https://your-app.com
```

Optional (defaults provided):

```bash
ATOMS_TEST_EMAIL=kooshapari@kooshapari.com
ATOMS_TEST_PASSWORD=ASD3on54_Pax90
```

## Using the Token

Once you have a token, set it as an environment variable:

```bash
export ATOMS_TEST_AUTH_TOKEN="your_jwt_token_here"
```

Or add to your `.env` file:

```env
ATOMS_TEST_AUTH_TOKEN=your_jwt_token_here
```

The token will be automatically used by:
- E2E test fixtures (`e2e_auth_token`)
- Integration tests
- Any code that checks `ATOMS_TEST_AUTH_TOKEN`

## Troubleshooting

### "Playwright not installed"

```bash
pip install playwright
playwright install chromium
```

### "WORKOS_API_KEY required"

Set your WorkOS credentials in environment or `.env` file.

### "Authentication succeeded but no token"

WorkOS User Management API might not return JWT tokens directly. Try:
1. Playwright automated flow (method 2)
2. Manual OAuth flow (method 3)
3. Check if token is in a different response field

### "OAuth callback timeout"

- Check that `FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL` is correct
- Verify redirect URI matches your WorkOS configuration
- Check browser console for errors (Playwright script shows browser)

### Token format issues

If you get a token but it's not a JWT:
- Check if it's an authorization code (needs server-side exchange)
- Verify WorkOS configuration
- Try a different authentication method

## Which Method to Use?

1. **Start with Direct API** (`get_authkit_token_direct.py`)
   - Fastest, simplest
   - Works if WorkOS supports direct token return

2. **If that fails, use Playwright** (`get_authkit_token_playwright.py`)
   - Fully automated OAuth
   - Handles browser-based flows

3. **As last resort, use Manual OAuth** (`get_authkit_token_oauth.py`)
   - Most reliable
   - Requires manual interaction

## Token Validation

All scripts validate the token format:
- Must be a JWT (3 parts separated by dots)
- Shows token claims (user_id, email, expiration)
- Provides usage instructions

## Security Notes

⚠️ **Never commit tokens to git**
- Tokens are sensitive credentials
- Use environment variables or `.env` (which should be in `.gitignore`)
- Tokens expire - regenerate as needed
