# Phase 4 Session Management - Quick Start

Get up and running with Atoms Session Management in 5 minutes.

## Installation

```bash
# Install with Vercel KV support (recommended for Vercel)
pip install httpx upstash-redis

# Or with Redis support
pip install httpx redis

# Or just core (in-memory testing only)
pip install httpx
```

## Basic Usage

### 1. Initialize Storage

```python
from atoms.session.storage import InMemoryStorage

# For testing/development
storage = InMemoryStorage()

# For production with Vercel KV
# from atoms.session.storage import VercelKVStorage
# storage = VercelKVStorage()  # Uses env vars KV_REST_API_URL and KV_REST_API_TOKEN
```

### 2. Create Session Manager

```python
from atoms.session import SessionManager, TokenManager

# Create token manager
token_manager = TokenManager(
    storage=storage,
    token_endpoint="https://openrouter.ai/api/v1/auth/token",
    client_id="your_client_id",
    client_secret="your_client_secret",
)

# Create session manager
session_manager = SessionManager(
    storage=storage,
    token_manager=token_manager,
)
```

### 3. Create Session (After OAuth Login)

```python
# After successful OAuth callback
session = await session_manager.create_session(
    user_id="user_123",
    access_token=oauth_response["access_token"],
    refresh_token=oauth_response["refresh_token"],
    expires_in=oauth_response["expires_in"],  # seconds
)

print(f"Session created: {session.session_id}")
```

### 4. Retrieve and Validate Session

```python
# Get session
session = await session_manager.get_session(session_id)

# Check if needs refresh
if session.needs_refresh():
    # Auto-refresh
    session, refresh_record = await session_manager.refresh_session(session_id)
    print(f"Token refreshed: {refresh_record.record_id}")
```

### 5. Logout (Revoke Session)

```python
from atoms.session import RevocationService

revocation_service = RevocationService(storage=storage)

# Revoke all session tokens
records = await revocation_service.revoke_session(
    session=session,
    reason="user_logout",
)

print(f"Revoked {len(records)} tokens")
```

## FastAPI Integration

```python
from fastapi import FastAPI, Request, HTTPException, Depends
from atoms.session import SessionManager, TokenManager, DeviceFingerprint
from atoms.session.storage import VercelKVStorage

app = FastAPI()

# Global instances
storage = VercelKVStorage()
token_manager = TokenManager(
    storage=storage,
    token_endpoint="https://openrouter.ai/api/v1/auth/token",
)
session_manager = SessionManager(storage=storage, token_manager=token_manager)


async def get_current_session(request: Request):
    """Dependency to get current session."""
    session_id = request.headers.get("X-Session-ID")
    if not session_id:
        raise HTTPException(status_code=401, detail="No session")

    try:
        session = await session_manager.get_session(session_id)

        # Auto-refresh if needed
        if session.needs_refresh():
            session, _ = await session_manager.refresh_session(session_id)

        return session
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@app.post("/auth/callback")
async def oauth_callback(request: Request):
    """Handle OAuth callback."""
    # Get OAuth token response (implementation depends on your provider)
    oauth_response = await get_oauth_tokens(request)

    # Create session
    session = await session_manager.create_session(
        user_id=oauth_response["user_id"],
        access_token=oauth_response["access_token"],
        refresh_token=oauth_response["refresh_token"],
        expires_in=oauth_response["expires_in"],
    )

    return {
        "session_id": session.session_id,
        "expires_at": session.access_token_expires_at.isoformat(),
    }


@app.get("/api/protected")
async def protected_route(session = Depends(get_current_session)):
    """Protected route requiring valid session."""
    return {
        "user_id": session.user_id,
        "message": "Access granted!",
    }


@app.post("/auth/logout")
async def logout(session = Depends(get_current_session)):
    """Logout and revoke session."""
    from atoms.session import RevocationService

    revocation_service = RevocationService(storage=storage)
    await revocation_service.revoke_session(session, reason="user_logout")

    return {"status": "logged_out"}
```

## Environment Variables

```bash
# Vercel KV (Upstash)
KV_REST_API_URL=https://your-kv.upstash.io
KV_REST_API_TOKEN=your_token_here

# OAuth Provider
OPENROUTER_CLIENT_ID=your_client_id
OPENROUTER_CLIENT_SECRET=your_client_secret
```

## Common Patterns

### Device Fingerprinting

```python
def extract_fingerprint(request: Request) -> DeviceFingerprint:
    """Extract device fingerprint from request."""
    return DeviceFingerprint(
        user_agent=request.headers.get("user-agent"),
        accept_language=request.headers.get("accept-language"),
        # Add more fields from client-side JavaScript
    )

session = await session_manager.create_session(
    user_id="user_123",
    access_token="token",
    device_fingerprint=extract_fingerprint(request),
    ip_address=request.client.host,
)
```

### Rate Limiting

```python
from atoms.session import SecurityService, RateLimitError

security_service = SecurityService(storage=storage)

try:
    await security_service.check_rate_limit(
        rule_name="token_refresh",
        key=user_id,
    )
except RateLimitError as e:
    raise HTTPException(status_code=429, detail=str(e))
```

### Multi-Session Management

```python
# Get all user sessions
sessions = await session_manager.get_user_sessions("user_123")

# Logout all sessions except current
from atoms.session import RevocationService

revocation_service = RevocationService(storage=storage)
await revocation_service.revoke_user_sessions(
    user_id="user_123",
    except_session_id=current_session_id,
    reason="logout_all_devices",
)
```

### Background Cleanup

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app):
    # Startup
    await session_manager.start_cleanup_task(interval_minutes=15)

    yield

    # Shutdown
    await session_manager.stop_cleanup_task()
    await storage.close()

app = FastAPI(lifespan=lifespan)
```

## Testing

```python
import pytest
from atoms.session import SessionManager, TokenManager
from atoms.session.storage import InMemoryStorage

@pytest.mark.asyncio
async def test_session_flow():
    storage = InMemoryStorage()
    token_manager = TokenManager(
        storage=storage,
        token_endpoint="https://test.com/token",
    )
    session_manager = SessionManager(
        storage=storage,
        token_manager=token_manager,
    )

    # Create session
    session = await session_manager.create_session(
        user_id="test_user",
        access_token="test_token",
        refresh_token="test_refresh",
    )

    assert session.user_id == "test_user"

    # Retrieve session
    retrieved = await session_manager.get_session(session.session_id)
    assert retrieved.session_id == session.session_id
```

## Next Steps

1. Read [README.md](README.md) for complete API reference
2. Check [INTEGRATION.md](INTEGRATION.md) for integration guide
3. Review [examples/complete_example.py](examples/complete_example.py) for advanced usage
4. Run tests: `pytest lib/atoms/session/tests/`

## Support

- Issues: Create an issue in the repository
- Documentation: See README.md and INTEGRATION.md
- Examples: See examples/complete_example.py

## Key Features

✅ Automatic token refresh (5 min before expiry)
✅ Token rotation with grace periods
✅ Device fingerprinting
✅ Rate limiting
✅ Session hijacking detection
✅ Multi-session support
✅ Complete audit trail
✅ Production-ready
✅ Vercel KV optimized
✅ Zero configuration

You're ready to go! 🚀
