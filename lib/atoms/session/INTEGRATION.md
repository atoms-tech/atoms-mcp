# Phase 4 Session Management Integration Guide

This guide shows how to integrate the Phase 4 session management system with the existing Atoms AuthKit.

> **Note:** The FastMCP server now relies on AuthKit's remote OAuth flow directly (no custom SessionMiddleware). The legacy middleware remains documented below for historical context only.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      Application Layer                       │
│  (FastAPI, Flask, Django, etc.)                             │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                  Atoms Session Management                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Session    │  │    Token     │  │  Revocation  │     │
│  │   Manager    │  │   Manager    │  │   Service    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │   Security   │  │   Storage    │                        │
│  │   Service    │  │   Backend    │                        │
│  └──────────────┘  └──────────────┘                        │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                     Atoms AuthKit                            │
│  (OAuth2/OIDC Providers)                                    │
└─────────────────────────────────────────────────────────────┘
```

## Integration Steps

### 1. Install Dependencies

```bash
# Install session management with Vercel KV support
pip install -e "lib/atoms/session[vercel]"

# Or with all storage backends
pip install -e "lib/atoms/session[all]"
```

### 2. Configure Storage Backend

#### Vercel KV (Recommended for Vercel deployments)

```python
# config.py
from atoms.session.storage import VercelKVStorage

def get_storage():
    """Get Vercel KV storage backend."""
    return VercelKVStorage(
        # Automatically uses KV_REST_API_URL and KV_REST_API_TOKEN from env
        key_prefix="atoms:session:",
        default_ttl_hours=24,
    )
```

#### Redis

```python
# config.py
from atoms.session.storage import RedisStorage
import os

def get_storage():
    """Get Redis storage backend."""
    return RedisStorage(
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
        key_prefix="atoms:session:",
        default_ttl_hours=24,
    )
```

### 3. Initialize Session Management

```python
# session_config.py
from atoms.session import (
    SessionManager,
    TokenManager,
    RevocationService,
    SecurityService,
)
from atoms.session.token_manager import RefreshConfig, RetryConfig
from .config import get_storage

# Global instances
_storage = None
_session_manager = None
_token_manager = None
_revocation_service = None
_security_service = None


def get_session_manager() -> SessionManager:
    """Get or create session manager singleton."""
    global _session_manager, _token_manager, _storage

    if _session_manager is None:
        _storage = get_storage()

        # Configure token manager
        _token_manager = TokenManager(
            storage=_storage,
            token_endpoint="https://openrouter.ai/api/v1/auth/token",
            introspection_endpoint="https://openrouter.ai/api/v1/auth/introspect",
            client_id=os.getenv("OPENROUTER_CLIENT_ID"),
            client_secret=os.getenv("OPENROUTER_CLIENT_SECRET"),
            refresh_config=RefreshConfig(
                proactive_refresh_minutes=5,
                rotation_enabled=True,
                grace_period_minutes=5,
            ),
            retry_config=RetryConfig(
                max_retries=3,
                initial_delay=1.0,
                max_delay=30.0,
            ),
        )

        # Configure session manager
        _session_manager = SessionManager(
            storage=_storage,
            token_manager=_token_manager,
            default_idle_timeout_minutes=30,
            default_absolute_timeout_minutes=480,
            max_sessions_per_user=5,
            device_validation_enabled=True,
        )

    return _session_manager


def get_revocation_service() -> RevocationService:
    """Get or create revocation service singleton."""
    global _revocation_service, _storage

    if _revocation_service is None:
        if _storage is None:
            _storage = get_storage()

        _revocation_service = RevocationService(
            storage=_storage,
            enable_cascading=True,
            revocation_list_ttl_hours=24,
        )

    return _revocation_service


def get_security_service() -> SecurityService:
    """Get or create security service singleton."""
    global _security_service, _storage

    if _security_service is None:
        if _storage is None:
            _storage = get_storage()

        _security_service = SecurityService(
            storage=_storage,
            enable_rate_limiting=True,
            enable_hijacking_detection=True,
        )

    return _security_service
```

### 4. Integrate with OAuth Flow

```python
# auth.py
from fastapi import APIRouter, Request, HTTPException
from atoms.session import DeviceFingerprint
from .session_config import get_session_manager, get_security_service

router = APIRouter()


def extract_device_fingerprint(request: Request) -> DeviceFingerprint:
    """Extract device fingerprint from request."""
    return DeviceFingerprint(
        user_agent=request.headers.get("user-agent"),
        accept_language=request.headers.get("accept-language"),
        # Additional fields from client-side JavaScript
        **request.state.fingerprint_data
    )


@router.post("/auth/callback")
async def oauth_callback(request: Request):
    """Handle OAuth callback and create session."""
    session_manager = get_session_manager()
    security_service = get_security_service()

    # Extract OAuth token response
    token_response = await get_token_from_oauth_provider()

    # Get user info
    user_id = token_response["user_id"]

    # Check rate limits
    try:
        await security_service.check_rate_limit(
            rule_name="session_create",
            key=user_id,
        )
    except RateLimitError as e:
        raise HTTPException(status_code=429, detail=str(e))

    # Extract device fingerprint
    fingerprint = extract_device_fingerprint(request)

    # Create session
    session = await session_manager.create_session(
        user_id=user_id,
        access_token=token_response["access_token"],
        refresh_token=token_response.get("refresh_token"),
        id_token=token_response.get("id_token"),
        expires_in=token_response.get("expires_in"),
        scopes=token_response.get("scope", "").split(),
        device_fingerprint=fingerprint,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
        provider="openrouter",
    )

    # Log security event
    await security_service.log_security_event(
        event_type="login_success",
        user_id=user_id,
        session_id=session.session_id,
        details="User logged in via OAuth",
    )

    return {
        "session_id": session.session_id,
        "access_token": session.access_token,
        "expires_in": token_response.get("expires_in"),
    }
```

### 5. Add Middleware for Session Validation

```python
# middleware.py
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from .session_config import get_session_manager, get_security_service


class SessionMiddleware(BaseHTTPMiddleware):
    """Middleware for session validation and refresh."""

    async def dispatch(self, request: Request, call_next):
        # Skip for public endpoints
        if request.url.path in ["/health", "/auth/login"]:
            return await call_next(request)

        session_manager = get_session_manager()
        security_service = get_security_service()

        # Get session ID from header or cookie
        session_id = request.headers.get("X-Session-ID") or \
                     request.cookies.get("session_id")

        if not session_id:
            raise HTTPException(status_code=401, detail="No session")

        try:
            # Get session with device validation
            fingerprint = extract_device_fingerprint(request)
            session = await session_manager.get_session(
                session_id=session_id,
                device_fingerprint=fingerprint,
                ip_address=request.client.host,
            )

            # Check for hijacking
            is_suspicious, risk_score, reasons = await security_service.detect_session_hijacking(
                session=session,
                current_ip=request.client.host,
                current_fingerprint=fingerprint,
            )

            if is_suspicious and risk_score > 0.7:
                # Terminate suspicious session
                await session_manager.terminate_session(
                    session_id,
                    reason="suspected_hijacking",
                )
                raise HTTPException(
                    status_code=401,
                    detail="Session terminated due to suspicious activity",
                )

            # Check if token needs refresh
            if session.needs_refresh():
                try:
                    session, _ = await session_manager.refresh_session(session_id)
                except Exception as e:
                    logger.error(f"Token refresh failed: {e}")
                    # Continue with expired token, will fail on provider API

            # Attach session to request
            request.state.session = session
            request.state.user_id = session.user_id

        except SessionExpiredError:
            raise HTTPException(status_code=401, detail="Session expired")
        except DeviceValidationError:
            raise HTTPException(status_code=401, detail="Device validation failed")
        except Exception as e:
            logger.error(f"Session validation error: {e}")
            raise HTTPException(status_code=401, detail="Invalid session")

        return await call_next(request)
```

### 6. Add Logout Endpoints

```python
# auth.py (continued)
@router.post("/auth/logout")
async def logout(request: Request):
    """Logout current session."""
    session = request.state.session
    revocation_service = get_revocation_service()
    security_service = get_security_service()

    # Revoke session
    await revocation_service.revoke_session(
        session=session,
        reason="user_logout",
        revoked_by=session.user_id,
    )

    # Log event
    await security_service.log_security_event(
        event_type="logout",
        user_id=session.user_id,
        session_id=session.session_id,
        details="User logged out",
    )

    return {"status": "logged_out"}


@router.post("/auth/logout-all")
async def logout_all(request: Request):
    """Logout all sessions except current."""
    session = request.state.session
    revocation_service = get_revocation_service()

    # Revoke all user sessions except current
    await revocation_service.revoke_user_sessions(
        user_id=session.user_id,
        except_session_id=session.session_id,
        reason="user_logout_all",
        revoked_by=session.user_id,
    )

    return {"status": "all_sessions_logged_out"}
```

### 7. Add Background Tasks

```python
# startup.py
from contextlib import asynccontextmanager
from .session_config import get_session_manager, get_revocation_service


@asynccontextmanager
async def lifespan(app):
    """Application lifespan manager."""
    # Startup
    session_manager = get_session_manager()
    revocation_service = get_revocation_service()

    # Start cleanup tasks
    await session_manager.start_cleanup_task(interval_minutes=15)
    await revocation_service.start_cleanup_task(interval_hours=1)

    yield

    # Shutdown
    await session_manager.stop_cleanup_task()
    await revocation_service.stop_cleanup_task()
    await session_manager.storage.close()


# In your FastAPI app
from fastapi import FastAPI

app = FastAPI(lifespan=lifespan)
```

### 8. Add Admin Endpoints

```python
# admin.py
from fastapi import APIRouter, HTTPException
from .session_config import get_session_manager, get_security_service

router = APIRouter(prefix="/admin")


@router.get("/sessions/{user_id}")
async def get_user_sessions(user_id: str):
    """Get all sessions for a user."""
    session_manager = get_session_manager()

    sessions = await session_manager.get_user_sessions(user_id)

    return {
        "user_id": user_id,
        "session_count": len(sessions),
        "sessions": [
            {
                "session_id": s.session_id,
                "state": s.state.value,
                "created_at": s.created_at.isoformat(),
                "last_accessed_at": s.last_accessed_at.isoformat(),
                "ip_address": s.ip_address,
            }
            for s in sessions
        ],
    }


@router.get("/security/{user_id}")
async def get_security_summary(user_id: str, hours: int = 24):
    """Get security summary for a user."""
    security_service = get_security_service()

    summary = await security_service.get_security_summary(
        user_id=user_id,
        hours=hours,
    )

    return summary


@router.delete("/sessions/{session_id}")
async def terminate_session(session_id: str):
    """Terminate a specific session."""
    session_manager = get_session_manager()

    await session_manager.terminate_session(
        session_id=session_id,
        reason="admin_termination",
    )

    return {"status": "terminated"}
```

## Environment Variables

```bash
# Storage
KV_REST_API_URL=https://your-kv.upstash.io
KV_REST_API_TOKEN=your_token

# Or for Redis
REDIS_URL=redis://localhost:6379

# OAuth Provider
OPENROUTER_CLIENT_ID=your_client_id
OPENROUTER_CLIENT_SECRET=your_client_secret
```

## Testing Integration

```python
# test_integration.py
import pytest
from httpx import AsyncClient
from .main import app


@pytest.mark.asyncio
async def test_login_flow():
    """Test complete login flow."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Login
        response = await client.post("/auth/callback", json={
            "code": "auth_code",
        })

        assert response.status_code == 200
        data = response.json()
        session_id = data["session_id"]

        # Access protected endpoint
        response = await client.get(
            "/api/protected",
            headers={"X-Session-ID": session_id},
        )

        assert response.status_code == 200

        # Logout
        response = await client.post(
            "/auth/logout",
            headers={"X-Session-ID": session_id},
        )

        assert response.status_code == 200
```

## Monitoring and Observability

```python
# monitoring.py
from prometheus_client import Counter, Histogram
import logging

# Metrics
session_created = Counter("session_created_total", "Sessions created")
session_expired = Counter("session_expired_total", "Sessions expired")
token_refreshed = Counter("token_refreshed_total", "Tokens refreshed")
token_refresh_failed = Counter("token_refresh_failed_total", "Token refresh failures")
session_hijack_detected = Counter("session_hijack_detected_total", "Hijacking attempts")

# Instrument session creation
async def create_session_with_metrics(*args, **kwargs):
    session = await session_manager.create_session(*args, **kwargs)
    session_created.inc()
    return session
```

## Next Steps

1. **Deploy to Vercel**: Update `vercel.json` with KV environment variables
2. **Add Monitoring**: Integrate with your monitoring solution
3. **Configure Alerts**: Set up alerts for suspicious activity
4. **Load Testing**: Test with production-like load
5. **Documentation**: Document API endpoints and integration points
