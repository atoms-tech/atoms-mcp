# Atoms Session Management

Production-ready session and token management for OAuth2/OIDC flows with comprehensive security features.

## Features

### Token Management
- **Proactive Token Refresh**: Automatically refresh tokens 5 minutes before expiry
- **Token Rotation**: Secure refresh token rotation with grace periods
- **Token Introspection**: Validate tokens using OAuth2 introspection
- **Exponential Backoff**: Automatic retry with exponential backoff on failures
- **Error Recovery**: Comprehensive error handling and recovery

### Session Management
- **Multi-Session Support**: Multiple concurrent sessions per user
- **Device Fingerprinting**: Track and validate device characteristics
- **IP Address Tracking**: Monitor and validate IP addresses
- **Timeout Enforcement**: Idle and absolute timeout support
- **Automatic Cleanup**: Background task for expired session cleanup

### Token Revocation
- **Immediate Invalidation**: Instantly revoke tokens
- **Cascading Revocation**: Revoke all related tokens when refresh token is revoked
- **Revocation List**: TTL-based revocation list with automatic cleanup
- **Complete Audit Trail**: Track all revocation events

### Security Features
- **Rate Limiting**: Exponential backoff rate limiting per user/IP
- **Session Hijacking Detection**: Detect suspicious activity based on device/IP changes
- **Suspicious Activity Monitoring**: Pattern-based anomaly detection
- **Comprehensive Audit Logging**: Full audit trail of all security events

### Storage Backends
- **Vercel KV**: Serverless-optimized Upstash Redis backend
- **Redis**: Production Redis with connection pooling
- **In-Memory**: Fast in-memory storage for testing

## Installation

```bash
# Core package
pip install atoms-session

# With Vercel KV support
pip install atoms-session[vercel]

# With Redis support
pip install atoms-session[redis]

# With all backends
pip install atoms-session[all]
```

## Quick Start

```python
import asyncio
from atoms.session import (
    SessionManager,
    TokenManager,
    RevocationService,
    SecurityService,
    DeviceFingerprint,
)
from atoms.session.storage import InMemoryStorage

async def main():
    # Initialize storage
    storage = InMemoryStorage()

    # Initialize managers
    token_manager = TokenManager(
        storage=storage,
        token_endpoint="https://provider.com/token",
        client_id="your_client_id",
        client_secret="your_client_secret",
    )

    session_manager = SessionManager(
        storage=storage,
        token_manager=token_manager,
    )

    # Create session
    session = await session_manager.create_session(
        user_id="user_123",
        access_token="access_token",
        refresh_token="refresh_token",
        expires_in=3600,
    )

    # Retrieve session
    retrieved = await session_manager.get_session(session.session_id)

    # Refresh token if needed
    if session.needs_refresh():
        updated_session, refresh_record = await token_manager.refresh_token(session)

    # Cleanup
    await token_manager.close()

asyncio.run(main())
```

## Usage Examples

### Session Creation with Device Fingerprinting

```python
from atoms.session import DeviceFingerprint

# Create device fingerprint
fingerprint = DeviceFingerprint(
    user_agent="Mozilla/5.0...",
    platform="MacIntel",
    timezone="America/New_York",
    screen_resolution="1920x1080",
    color_depth=24,
)

# Create session with fingerprint
session = await session_manager.create_session(
    user_id="user_123",
    access_token="access_token",
    refresh_token="refresh_token",
    device_fingerprint=fingerprint,
    ip_address="192.168.1.100",
)
```

### Proactive Token Refresh

```python
# Token manager automatically refreshes 5 minutes before expiry
session, refresh_record = await token_manager.refresh_token(
    session=session,
    force=False,  # Only refresh if needed
    reason="proactive",
)

# Get refresh history
history = await token_manager.get_refresh_history(
    session_id=session.session_id,
    limit=10,
)
```

### Token Revocation

```python
from atoms.session import RevocationService

revocation_service = RevocationService(storage=storage)

# Revoke single token
record = await revocation_service.revoke_token(
    token=access_token,
    token_type="access_token",
    session_id=session.session_id,
    reason="user_logout",
)

# Revoke entire session (all tokens)
records = await revocation_service.revoke_session(
    session=session,
    reason="user_logout",
)

# Revoke all user sessions
records = await revocation_service.revoke_user_sessions(
    user_id="user_123",
    except_session_id=current_session_id,  # Keep current session
    reason="logout_all_devices",
)

# Check if token is revoked
is_revoked = await revocation_service.is_revoked(token)
```

### Security Features

```python
from atoms.session import SecurityService

security_service = SecurityService(
    storage=storage,
    enable_rate_limiting=True,
    enable_hijacking_detection=True,
)

# Check rate limit
try:
    await security_service.check_rate_limit(
        rule_name="token_refresh",
        key=user_id,
    )
except RateLimitError as e:
    print(f"Rate limit exceeded: {e}")

# Detect session hijacking
is_suspicious, risk_score, reasons = await security_service.detect_session_hijacking(
    session=session,
    current_ip="192.168.1.101",
    current_fingerprint=new_fingerprint,
)

if is_suspicious:
    print(f"Suspicious activity detected: {reasons}")
    print(f"Risk score: {risk_score}")

# Get security summary
summary = await security_service.get_security_summary(
    user_id="user_123",
    hours=24,
)
```

### Storage Backends

#### Vercel KV (Recommended for Vercel deployments)

```python
from atoms.session.storage import VercelKVStorage

# Using environment variables (KV_REST_API_URL, KV_REST_API_TOKEN)
storage = VercelKVStorage()

# Or explicitly provide credentials
storage = VercelKVStorage(
    rest_api_url="https://your-kv.upstash.io",
    rest_api_token="your_token",
)
```

#### Redis

```python
from atoms.session.storage import RedisStorage

# Using connection string
storage = RedisStorage(
    redis_url="redis://localhost:6379/0",
)

# Or with existing client
import redis.asyncio as redis

client = await redis.from_url("redis://localhost:6379")
storage = RedisStorage(redis_client=client)
```

#### In-Memory (Testing only)

```python
from atoms.session.storage import InMemoryStorage

storage = InMemoryStorage()
```

## Configuration

### Token Manager Configuration

```python
from atoms.session.token_manager import RefreshConfig, RetryConfig

refresh_config = RefreshConfig(
    proactive_refresh_minutes=5,      # Refresh 5 min before expiry
    rotation_enabled=True,             # Enable refresh token rotation
    grace_period_minutes=5,            # Grace period for old tokens
    introspection_enabled=True,        # Enable token introspection
    audit_enabled=True,                # Enable audit logging
)

retry_config = RetryConfig(
    max_retries=3,                     # Maximum retry attempts
    initial_delay=1.0,                 # Initial delay in seconds
    max_delay=30.0,                    # Maximum delay in seconds
    exponential_base=2.0,              # Exponential backoff base
    jitter=True,                       # Add random jitter
)

token_manager = TokenManager(
    storage=storage,
    token_endpoint="https://provider.com/token",
    refresh_config=refresh_config,
    retry_config=retry_config,
)
```

### Session Manager Configuration

```python
session_manager = SessionManager(
    storage=storage,
    token_manager=token_manager,
    default_idle_timeout_minutes=30,        # 30 min idle timeout
    default_absolute_timeout_minutes=480,   # 8 hour absolute timeout
    max_sessions_per_user=5,                # Max 5 concurrent sessions
    device_validation_enabled=True,         # Validate device fingerprints
    device_match_threshold=0.8,             # 80% similarity threshold
    ip_validation_enabled=False,            # Don't require same IP
    audit_enabled=True,                     # Enable audit logging
)
```

### Security Configuration

```python
from atoms.session.security import RateLimitRule

# Add custom rate limit rule
security_service.add_rate_limit_rule(
    RateLimitRule(
        name="api_calls",
        max_requests=100,
        window_seconds=60,
        exponential_backoff=True,
        backoff_multiplier=2.0,
        max_backoff_seconds=1800,
    )
)
```

## Background Tasks

### Session Cleanup

```python
# Start automatic cleanup every 15 minutes
await session_manager.start_cleanup_task(interval_minutes=15)

# Stop cleanup task
await session_manager.stop_cleanup_task()
```

### Revocation Cleanup

```python
# Start automatic cleanup every hour
await revocation_service.start_cleanup_task(interval_hours=1)

# Stop cleanup task
await revocation_service.stop_cleanup_task()
```

## Error Handling

```python
from atoms.session import (
    SessionError,
    SessionExpiredError,
    SessionNotFoundError,
    DeviceValidationError,
    TokenRefreshError,
    TokenValidationError,
    RevocationError,
    RateLimitError,
    SuspiciousActivityError,
)

try:
    session = await session_manager.get_session(session_id)
except SessionExpiredError:
    # Handle expired session
    pass
except DeviceValidationError:
    # Handle device mismatch
    pass
except SessionNotFoundError:
    # Handle missing session
    pass
```

## Testing

```bash
# Run tests
pytest lib/atoms/session/tests/

# Run with coverage
pytest lib/atoms/session/tests/ --cov=lib/atoms/session --cov-report=html

# Run specific test file
pytest lib/atoms/session/tests/test_session_manager.py -v
```

## Architecture

```
lib/atoms/session/
├── __init__.py              # Public API exports
├── models.py                # Data models (Session, Token, Audit, etc.)
├── token_manager.py         # Token refresh and rotation
├── session_manager.py       # Session lifecycle management
├── revocation.py            # Token revocation service
├── security.py              # Security features (rate limiting, etc.)
├── storage/
│   ├── __init__.py
│   ├── base.py             # Abstract storage interface
│   ├── memory.py           # In-memory implementation
│   ├── redis.py            # Redis implementation
│   └── vercel_kv.py        # Vercel KV implementation
├── tests/
│   ├── __init__.py
│   ├── test_session_manager.py
│   ├── test_token_manager.py
│   └── test_revocation.py
└── examples/
    └── complete_example.py  # Full usage example
```

## Integration with Atoms AuthKit

```python
from atoms.authkit import AuthKitProvider
from atoms.session import SessionManager, TokenManager

# Initialize with AuthKit
provider = AuthKitProvider(
    provider_type="openrouter",
    client_id="your_client_id",
    client_secret="your_client_secret",
)

# Create token manager with provider endpoints
token_manager = TokenManager(
    storage=storage,
    token_endpoint=provider.token_endpoint,
    introspection_endpoint=provider.introspection_endpoint,
    client_id=provider.client_id,
    client_secret=provider.client_secret,
)

# Use in session manager
session_manager = SessionManager(
    storage=storage,
    token_manager=token_manager,
)
```

## Production Deployment

### Vercel Deployment

```python
# vercel.json
{
  "env": {
    "KV_REST_API_URL": "@kv_rest_api_url",
    "KV_REST_API_TOKEN": "@kv_rest_api_token"
  }
}
```

```python
# app.py
from atoms.session.storage import VercelKVStorage
from atoms.session import SessionManager, TokenManager

# Storage automatically uses environment variables
storage = VercelKVStorage()

# Initialize managers
token_manager = TokenManager(storage=storage, ...)
session_manager = SessionManager(storage=storage, ...)

# Start background cleanup
await session_manager.start_cleanup_task()
await revocation_service.start_cleanup_task()
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

# Install dependencies
RUN pip install atoms-session[redis]

# Copy app
COPY . /app
WORKDIR /app

# Run app
CMD ["python", "app.py"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  app:
    build: .
    environment:
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

## License

MIT License - see LICENSE file for details

## Support

- Documentation: https://docs.atoms.dev/session
- Issues: https://github.com/atoms/atoms-mcp/issues
- Discord: https://discord.gg/atoms
