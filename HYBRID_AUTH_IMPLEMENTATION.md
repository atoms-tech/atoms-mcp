# HybridAuthProvider: Dual Authentication Implementation

## Problem Solved

FastMCP issue #2385 and #2448: **Support both Bearer tokens and OAuth simultaneously**

When an MCP server is configured with OAuth (AuthKit), it defaults to OAuth flow only. The `HybridAuthProvider` enables the same server to accept:
- ✅ OAuth flow (AuthKit) for IDE integrations (Cursor, VS Code)
- ✅ Bearer tokens (WorkOS User Management JWTs) for API calls
  - AuthKit API (headless) uses WorkOS User Management API under the hood
  - Both return the same JWT format and can be used interchangeably
- ✅ Unsigned JWTs for local testing

## Architecture

```
Request with Bearer Token
    ↓
HybridAuthProvider.authenticate()
    ↓
Try OAuth (AuthKit) → Try WorkOS User Management JWT → Try unsigned JWT
    ↓
Return AccessToken object
```

**Note:** AuthKit API (headless) and WorkOS User Management API return the same JWT format, so they're verified by the same verifier.

## Key Components

### 1. HybridAuthProvider (`services/auth/hybrid_auth_provider.py`)
- Wraps AuthKitProvider for OAuth flow
- Implements custom `verify_token()` method
- Returns `AccessToken` objects (not dicts)
- Supports 4 authentication methods

### 2. WorkOSTokenVerifier (`services/auth/workos_token_verifier.py`)
- Verifies WorkOS User Management JWTs
- Also verifies AuthKit API JWTs (same format)
- Validates JWT signature and claims
- Handles token expiration

### 3. Configuration (`infrastructure_modules/server_auth.py`)
- Respects `FASTMCP_SERVER_AUTH` environment variable
- Creates HybridAuthProvider when configured
- Falls back to RemoteAuthProvider if not configured

## Usage

### Configuration
```bash
# .env
FASTMCP_SERVER_AUTH=services.auth.hybrid_auth_provider.HybridAuthProvider
WORKOS_API_KEY=sk_test_...
WORKOS_CLIENT_ID=client_...
```

### Server Setup
```python
from infrastructure_modules.server_auth import create_auth_provider

base_url = "http://localhost:8000"
auth_provider = create_auth_provider(base_url)

mcp = FastMCP(
    name="atoms-fastmcp",
    auth=auth_provider
)
```

## Authentication Methods

1. **OAuth (AuthKit)** - IDE integrations (full OAuth flow)
2. **Bearer Token (WorkOS User Management / AuthKit API JWT)** - API calls
   - AuthKit API (headless) uses WorkOS User Management API under the hood
   - Both return the same JWT format
   - Can be used interchangeably as Bearer tokens
   - Verified by WorkOSTokenVerifier
3. **Unsigned JWT** - Local testing (test mode)

## Testing

### Local Testing
```bash
atoms test --scope e2e --env local
```
- Uses real WorkOS authentication
- Same keys as production
- No unsigned JWTs needed

### Dev/Prod Testing
```bash
atoms test --scope e2e --env dev
atoms test --scope e2e --env prod
```
- Uses deployed servers
- Real WorkOS authentication

## Benefits

✅ Single MCP server supports multiple auth methods
✅ No need for separate servers per auth type
✅ Seamless IDE integration + API authentication
✅ Production-ready authentication
✅ Backward compatible with existing OAuth setup

## Related FastMCP Issues

- #2385: Need combined security provider
- #2448: Support for Dual Auth methods
- #1579: Different auth for different servers

