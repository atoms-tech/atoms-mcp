# OAuth Mock Adapters - Complete Usage Guide

This guide shows how to use `MockOAuthAuthAdapter` for testing FastMCP servers with OAuth PKCE and DCR authentication.

## Quick Start

### 1. Basic OAuth Flow (PKCE)

```python
import asyncio
from infrastructure.mock_oauth_adapters import MockOAuthAuthAdapter, create_pkce_pair

async def test_oauth_flow():
    adapter = MockOAuthAuthAdapter()
    
    # Step 1: Generate PKCE pair (client-side)
    code_verifier, code_challenge = create_pkce_pair()
    
    # Step 2: Request authorization (client → server)
    auth_code = adapter.create_authorization_request(
        client_id="my-app",
        redirect_uri="http://localhost:3000/callback",
        code_challenge=code_challenge,
        code_challenge_method="S256",  # SHA256 PKCE
        state="state-123"  # CSRF protection
    )
    
    # Step 3: Exchange code for tokens (client → server)
    tokens = await adapter.exchange_code_for_token(
        code=auth_code,
        client_id="my-app",
        redirect_uri="http://localhost:3000/callback",
        code_verifier=code_verifier
    )
    
    # Step 4: Use the tokens
    print(f"Access Token: {tokens['access_token']}")
    print(f"ID Token: {tokens['id_token']}")
    print(f"Refresh Token: {tokens['refresh_token']}")
    
    # Step 5: Validate tokens
    user = await adapter.validate_token(tokens["access_token"])
    print(f"User: {user['email']}")

asyncio.run(test_oauth_flow())
```

### 2. Dynamic Client Registration (DCR)

```python
from infrastructure.mock_oauth_adapters import MockOAuthAuthAdapter

adapter = MockOAuthAuthAdapter()

# Register a new OAuth client
client = adapter.register_client(
    client_name="My MCP Application",
    redirect_uris=[
        "http://localhost:3000/callback",
        "http://localhost:3000/auth/callback"
    ],
    # Optional metadata
    client_type="web",
    logo_uri="https://example.com/logo.png"
)

print(f"Client ID: {client['client_id']}")
print(f"Client Secret: {client['client_secret']}")

# Verify redirect URIs are registered
assert adapter.validate_redirect_uri(client["client_id"], "http://localhost:3000/callback")
```

### 3. Pending Authentication (AuthKit Pattern)

```python
import asyncio
from infrastructure.mock_oauth_adapters import MockOAuthAuthAdapter

async def test_pending_auth():
    adapter = MockOAuthAuthAdapter()
    
    # Create pending authentication (user starts login)
    pending_token = adapter.create_pending_authentication(
        user_id="user-123",
        email="user@example.com",
        redirect_uri="http://localhost:3000/callback"
    )
    
    # Later, complete the authentication (AuthKit callback)
    session_token = await adapter.complete_pending_authentication(
        pending_authentication_token=pending_token,
        external_auth_id="authkit-ext-id",
        user_data={
            "id": "user-123",
            "email": "user@example.com",
            "name": "John Doe"
        }
    )
    
    # Use the session token
    user = await adapter.validate_token(session_token)
    print(f"Logged in as: {user['email']}")

asyncio.run(test_pending_auth())
```

## Integration with Pytest

### Using FastMCP Testing Patterns

```python
import pytest
from infrastructure.mock_oauth_adapters import MockOAuthAuthAdapter, create_pkce_pair

@pytest.fixture
def oauth_adapter():
    """FastMCP pytest fixture for OAuth adapter."""
    return MockOAuthAuthAdapter()

@pytest.mark.asyncio
async def test_oauth_flow_with_pkce(oauth_adapter):
    """Test complete OAuth flow with PKCE."""
    code_verifier, code_challenge = create_pkce_pair()
    
    # Request authorization
    auth_code = oauth_adapter.create_authorization_request(
        client_id="test-client",
        redirect_uri="http://localhost:3000/callback",
        code_challenge=code_challenge
    )
    
    # Exchange for tokens
    tokens = await oauth_adapter.exchange_code_for_token(
        code=auth_code,
        client_id="test-client",
        redirect_uri="http://localhost:3000/callback",
        code_verifier=code_verifier
    )
    
    assert "access_token" in tokens
    assert "id_token" in tokens
    assert tokens["token_type"] == "Bearer"

@pytest.mark.parametrize(
    "client_id,redirect_uri",
    [
        ("app-1", "http://localhost:3000/callback"),
        ("app-2", "http://localhost:4000/callback"),
        ("app-3", "http://app.example.com/callback"),
    ]
)
@pytest.mark.asyncio
async def test_multiple_clients(oauth_adapter, client_id, redirect_uri):
    """Test OAuth flow with multiple clients (parametrized)."""
    code_verifier, code_challenge = create_pkce_pair()
    
    auth_code = oauth_adapter.create_authorization_request(
        client_id=client_id,
        redirect_uri=redirect_uri,
        code_challenge=code_challenge
    )
    
    tokens = await oauth_adapter.exchange_code_for_token(
        code=auth_code,
        client_id=client_id,
        redirect_uri=redirect_uri,
        code_verifier=code_verifier
    )
    
    assert "access_token" in tokens
```

## Advanced Usage

### Custom User Data

```python
from infrastructure.mock_oauth_adapters import MockOAuthAuthAdapter

custom_user = {
    "user_id": "alice-123",
    "email": "alice@company.com",
    "email_verified": True,
    "name": "Alice Smith",
    "given_name": "Alice",
    "family_name": "Smith",
    "picture": "https://example.com/alice.jpg"
}

adapter = MockOAuthAuthAdapter(default_user=custom_user)

# All tokens will contain this user data
tokens = await adapter.exchange_code_for_token(...)
user = await adapter.validate_token(tokens["access_token"])
assert user["name"] == "Alice Smith"
```

### OpenID Connect Nonce Validation

```python
import json
import base64
from infrastructure.mock_oauth_adapters import MockOAuthAuthAdapter, create_pkce_pair

adapter = MockOAuthAuthAdapter()
code_verifier, code_challenge = create_pkce_pair()
nonce = "nonce-123"

auth_code = adapter.create_authorization_request(
    client_id="test-client",
    redirect_uri="http://localhost:3000/callback",
    code_challenge=code_challenge,
    nonce=nonce  # OpenID Connect nonce for replay attack prevention
)

tokens = await adapter.exchange_code_for_token(
    code=auth_code,
    client_id="test-client",
    redirect_uri="http://localhost:3000/callback",
    code_verifier=code_verifier
)

# Decode and verify ID token
id_token = tokens["id_token"]
parts = id_token.split(".")
payload = parts[1]
payload += "=" * (4 - len(payload) % 4)
id_token_data = json.loads(base64.urlsafe_b64decode(payload))

assert id_token_data["nonce"] == nonce
assert id_token_data["sub"] == "mock-user-123"
```

### PKCE Plain vs SHA256

```python
import secrets
from infrastructure.mock_oauth_adapters import MockOAuthAuthAdapter

adapter = MockOAuthAuthAdapter()

# PKCE with SHA256 (recommended)
code_verifier = secrets.token_urlsafe(32)
from hashlib import sha256
import base64
code_challenge = base64.urlsafe_b64encode(
    sha256(code_verifier.encode()).digest()
).decode().rstrip("=")

auth_code = adapter.create_authorization_request(
    client_id="test-client",
    redirect_uri="http://localhost:3000/callback",
    code_challenge=code_challenge,
    code_challenge_method="S256"
)

# PKCE with plain (for testing only, not secure)
code_verifier_plain = secrets.token_urlsafe(32)
auth_code_plain = adapter.create_authorization_request(
    client_id="test-client",
    redirect_uri="http://localhost:3000/callback",
    code_challenge=code_verifier_plain,
    code_challenge_method="plain"
)
```

## Error Handling

```python
import pytest
from infrastructure.mock_oauth_adapters import MockOAuthAuthAdapter, create_pkce_pair

adapter = MockOAuthAuthAdapter()
code_verifier, code_challenge = create_pkce_pair()

# Create valid authorization code
auth_code = adapter.create_authorization_request(
    client_id="test-client",
    redirect_uri="http://localhost:3000/callback",
    code_challenge=code_challenge
)

# Error: Invalid PKCE verifier
with pytest.raises(ValueError, match="PKCE verification failed"):
    await adapter.exchange_code_for_token(
        code=auth_code,
        client_id="test-client",
        redirect_uri="http://localhost:3000/callback",
        code_verifier="wrong-verifier"
    )

# Error: Client ID mismatch
with pytest.raises(ValueError, match="Client ID mismatch"):
    await adapter.exchange_code_for_token(
        code=auth_code,
        client_id="different-client",
        redirect_uri="http://localhost:3000/callback",
        code_verifier=code_verifier
    )

# Error: Redirect URI mismatch
with pytest.raises(ValueError, match="Redirect URI mismatch"):
    await adapter.exchange_code_for_token(
        code=auth_code,
        client_id="test-client",
        redirect_uri="http://localhost:4000/callback",
        code_verifier=code_verifier
    )

# Error: Expired code
adapter._auth_codes[auth_code]["expires_at"] = 0
with pytest.raises(ValueError, match="expired"):
    await adapter.exchange_code_for_token(
        code=auth_code,
        client_id="test-client",
        redirect_uri="http://localhost:3000/callback",
        code_verifier=code_verifier
    )
```

## Integration with Your MCP Server

### Test a FastMCP Server with OAuth

```python
import pytest
from fastmcp.client import Client
from fastmcp.client.transports import FastMCPTransport
from infrastructure.mock_oauth_adapters import MockOAuthAuthAdapter, create_pkce_pair

from your_mcp_server import mcp  # Your FastMCP server instance

@pytest.fixture
def oauth_adapter():
    return MockOAuthAuthAdapter()

@pytest.fixture
async def mcp_client():
    async with Client(transport=mcp) as client:
        yield client

@pytest.mark.asyncio
async def test_mcp_with_oauth(mcp_client, oauth_adapter):
    """Test MCP server that requires OAuth authentication."""
    
    # Setup OAuth flow
    code_verifier, code_challenge = create_pkce_pair()
    auth_code = oauth_adapter.create_authorization_request(
        client_id="mcp-test-client",
        redirect_uri="http://localhost:3000/callback",
        code_challenge=code_challenge
    )
    
    # Exchange for token
    tokens = await oauth_adapter.exchange_code_for_token(
        code=auth_code,
        client_id="mcp-test-client",
        redirect_uri="http://localhost:3000/callback",
        code_verifier=code_verifier
    )
    
    # Call MCP tool with OAuth token
    result = await mcp_client.call_tool(
        name="my-tool",
        arguments={"param": "value"},
        meta={
            "authorization": f"Bearer {tokens['access_token']}"
        }
    )
    
    assert result is not None
```

## Security Considerations

### PKCE (Proof Key for Code Exchange)

PKCE prevents authorization code interception by native apps and SPAs:

```python
# ✅ CORRECT: Use SHA256 PKCE (S256)
code_verifier = secrets.token_urlsafe(32)  # Min 43 chars
code_challenge = base64.urlsafe_b64encode(
    hashlib.sha256(code_verifier.encode()).digest()
).decode().rstrip("=")

auth_code = adapter.create_authorization_request(
    client_id="my-app",
    redirect_uri="http://localhost:3000/callback",
    code_challenge=code_challenge,
    code_challenge_method="S256"  # Always use S256
)

# ❌ AVOID: Plain method (only for testing)
auth_code = adapter.create_authorization_request(
    client_id="my-app",
    redirect_uri="http://localhost:3000/callback",
    code_challenge=code_verifier,
    code_challenge_method="plain"  # Only for testing!
)
```

### Token Storage

```python
# ✅ CORRECT: Store tokens securely
tokens = await adapter.exchange_code_for_token(...)
access_token = tokens["access_token"]
# Store in secure session/storage

# ❌ AVOID: Logging tokens
print(tokens)  # Never log tokens!
logging.error(f"Token: {access_token}")  # Never log!
```

### Redirect URI Validation

```python
# Always validate redirect URIs in production
client = adapter.register_client(
    client_name="My App",
    redirect_uris=["https://myapp.com/callback"]  # HTTPS in production
)

# Never accept dynamic redirect URIs
# adapter.allowed_client_redirect_uris = input()  # ❌ WRONG

# Whitelist specific URIs
assert adapter.validate_redirect_uri(
    client["client_id"],
    "https://myapp.com/callback"
)
```

## Performance Tips

### Reuse Adapters

```python
# ✅ CORRECT: Create once, reuse
adapter = MockOAuthAuthAdapter()

for i in range(100):
    tokens = await adapter.exchange_code_for_token(...)

# ❌ AVOID: Creating new instances
for i in range(100):
    adapter = MockOAuthAuthAdapter()  # Don't do this
    tokens = await adapter.exchange_code_for_token(...)
```

### Batch Operations

```python
import asyncio

# Register multiple clients efficiently
adapters = [
    adapter.register_client(
        client_name=f"App {i}",
        redirect_uris=[f"http://app{i}:3000/callback"]
    )
    for i in range(10)
]

# Exchange codes in parallel
async def exchange_all(auth_codes):
    tasks = [
        adapter.exchange_code_for_token(
            code=code,
            client_id=f"client-{i}",
            redirect_uri=f"http://app{i}:3000/callback",
            code_verifier=verifiers[i]
        )
        for i, code in enumerate(auth_codes)
    ]
    return await asyncio.gather(*tasks)
```

## Testing Best Practices

### Follow FastMCP Patterns

```python
import pytest
from infrastructure.mock_oauth_adapters import MockOAuthAuthAdapter, create_pkce_pair

# ✅ Use pytest fixtures
@pytest.fixture
def oauth_adapter():
    return MockOAuthAuthAdapter()

# ✅ Use parametrize for variants
@pytest.mark.parametrize("method", ["S256", "plain"])
@pytest.mark.asyncio
async def test_pkce_methods(oauth_adapter, method):
    code_verifier = secrets.token_urlsafe(32)
    # ... test both methods

# ✅ Use asyncio marker
@pytest.mark.asyncio
async def test_async_token_exchange():
    adapter = MockOAuthAuthAdapter()
    tokens = await adapter.exchange_code_for_token(...)

# ✅ Test error cases
@pytest.mark.asyncio
async def test_invalid_code(oauth_adapter):
    with pytest.raises(ValueError):
        await oauth_adapter.exchange_code_for_token(
            code="invalid-code",
            client_id="test",
            redirect_uri="http://localhost:3000/callback",
            code_verifier="verifier"
        )
```

## Running Tests

```bash
# Run OAuth tests
pytest tests/unit/test_oauth_mock_adapters.py -v

# Run with coverage
pytest tests/unit/test_oauth_mock_adapters.py --cov=infrastructure.mock_oauth_adapters

# Run specific test class
pytest tests/unit/test_oauth_mock_adapters.py::TestOAuthPKCEFlow -v

# Run with markers
pytest tests/unit/test_oauth_mock_adapters.py -m asyncio -v
```

## FastMCP References

- **Token Verification**: https://fastmcp.wiki/en/servers/auth/token-verification
- **Remote OAuth**: https://fastmcp.wiki/en/servers/auth/remote-oauth
- **Testing Patterns**: https://fastmcp.wiki/en/patterns/testing
- **WorkOS AuthKit**: https://fastmcp.wiki/integrations/authkit

## Summary

The `MockOAuthAuthAdapter` provides:

✅ Complete OAuth 2.0 PKCE flow simulation
✅ DCR (Dynamic Client Registration) for client management
✅ OpenID Connect (ID tokens with nonce)
✅ Pending authentication (AuthKit pattern)
✅ FastMCP testing best practices
✅ Zero external dependencies
✅ Production-ready error handling
✅ Security best practices built-in
