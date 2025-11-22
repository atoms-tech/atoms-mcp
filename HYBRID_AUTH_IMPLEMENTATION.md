# HybridAuthProvider: Dual Authentication Implementation

## Problem Solved

FastMCP issue #2385 and #2448: **Support both Bearer tokens and OAuth simultaneously**

When an MCP server is configured with OAuth (AuthKit), it defaults to OAuth flow only. The `HybridAuthProvider` enables the same server to accept:
- ✅ OAuth flow (AuthKit) for IDE integrations (Cursor, VS Code)
- ✅ Bearer tokens (WorkOS User Management JWTs) for API calls
- ✅ AuthKit JWTs forwarded from frontend/backend
- ✅ Unsigned JWTs for local testing

## Architecture

```
Request with Bearer Token
    ↓
HybridAuthProvider.authenticate()
    ↓
Try internal token → Try WorkOS JWT → Try AuthKit JWT → Try unsigned JWT
    ↓
Return AccessToken object
```

## Key Components

### 1. HybridAuthProvider (`services/auth/hybrid_auth_provider.py`)
- Wraps AuthKitProvider for OAuth flow
- Implements custom `verify_token()` method
- Returns `AccessToken` objects (not dicts)
- Supports 4 authentication methods

### 2. WorkOSTokenVerifier (`services/auth/workos_token_verifier.py`)
- Verifies WorkOS User Management JWTs
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

1. **OAuth (AuthKit)** - IDE integrations
2. **Bearer Token (WorkOS JWT)** - API calls
3. **AuthKit JWT** - Frontend/backend forwarding
4. **Unsigned JWT** - Local testing (test mode)

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

