# Phase 4: Token Refresh and Session Management Implementation

## Executive Summary

This document outlines the complete Phase 4 implementation for advanced token refresh and session management in the atoms-mcp-prod system. The design addresses token lifecycle management, multi-session handling, secure token storage, and revocation mechanisms while maintaining compatibility with the existing AuthKit integration and Vercel serverless deployment.

## Architecture Overview

### Core Components

1. **Token Refresh Service** - Proactive and reactive token refresh
2. **Session Manager** - Multi-session lifecycle management
3. **Storage Layer** - Persistent session storage (Vercel KV/Redis)
4. **Revocation Service** - Token invalidation and audit
5. **Security Middleware** - Rate limiting and hijacking prevention
6. **Migration Tools** - Phase 2 to Phase 4 migration utilities

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Application                        │
└────────────────┬───────────────────────────────────┬─────────────┘
                 │                                   │
                 ▼                                   ▼
        ┌────────────────┐                  ┌────────────────┐
        │  Auth Endpoints │                  │  API Endpoints  │
        └────────┬────────┘                  └────────┬────────┘
                 │                                     │
                 ▼                                     ▼
        ┌─────────────────────────────────────────────────────┐
        │              Security Middleware Layer               │
        │  - Rate Limiting                                     │
        │  - Session Validation                               │
        │  - Anti-Hijacking                                   │
        └────────┬─────────────────────────────────┬──────────┘
                 │                                 │
                 ▼                                 ▼
        ┌──────────────────┐            ┌──────────────────┐
        │  Token Refresh    │            │ Session Manager   │
        │     Service       │◄───────────┤                  │
        └──────────┬────────┘            └──────────┬───────┘
                   │                                 │
                   └────────────┬────────────────────┘
                                │
                                ▼
                   ┌────────────────────────┐
                   │   Storage Layer        │
                   │  (Vercel KV/Redis)     │
                   └────────────────────────┘
```

## Data Models

### Session Model
```python
@dataclass
class Session:
    session_id: str
    user_id: str
    access_token: str
    refresh_token: str
    expires_at: datetime
    refresh_expires_at: datetime
    created_at: datetime
    last_activity: datetime
    device_info: Optional[DeviceInfo]
    ip_address: str
    is_active: bool
    revoked_at: Optional[datetime]
    revocation_reason: Optional[str]
```

### Token Pair Model
```python
@dataclass
class TokenPair:
    access_token: str
    refresh_token: str
    access_expires_in: int
    refresh_expires_in: int
    scope: str
    token_type: str = "Bearer"
```

### Device Info Model
```python
@dataclass
class DeviceInfo:
    user_agent: str
    device_type: str  # mobile, desktop, tablet
    browser: str
    os: str
    device_id: Optional[str]
```

## API Endpoints

### Token Management Endpoints

#### POST /auth/token/refresh
Refresh access token using refresh token
```python
Request:
{
    "refresh_token": "string",
    "session_id": "string (optional)"
}

Response:
{
    "access_token": "string",
    "refresh_token": "string (if rotation enabled)",
    "expires_in": 3600,
    "token_type": "Bearer"
}
```

#### POST /auth/token/revoke
Revoke tokens immediately
```python
Request:
{
    "token": "string",
    "token_type_hint": "access_token|refresh_token",
    "reason": "string (optional)"
}

Response:
{
    "success": true,
    "revoked_at": "2024-01-01T00:00:00Z"
}
```

### Session Management Endpoints

#### GET /auth/sessions
List active sessions for user
```python
Response:
{
    "sessions": [
        {
            "session_id": "string",
            "device_info": {...},
            "last_activity": "2024-01-01T00:00:00Z",
            "ip_address": "string",
            "is_current": true
        }
    ]
}
```

#### DELETE /auth/sessions/{session_id}
Terminate specific session
```python
Response:
{
    "success": true,
    "terminated_at": "2024-01-01T00:00:00Z"
}
```

#### POST /auth/sessions/revoke-all
Revoke all sessions except current
```python
Response:
{
    "success": true,
    "sessions_revoked": 5
}
```

## Environment Variables

```bash
# Storage Configuration
STORAGE_PROVIDER=vercel_kv  # vercel_kv, redis, supabase
VERCEL_KV_URL=https://...
VERCEL_KV_TOKEN=...
REDIS_URL=redis://...

# Token Configuration
ACCESS_TOKEN_EXPIRES_IN=3600  # 1 hour
REFRESH_TOKEN_EXPIRES_IN=604800  # 7 days
REFRESH_TOKEN_ROTATION=true
REFRESH_BUFFER_SECONDS=300  # Refresh 5 minutes before expiry

# Session Configuration
MAX_SESSIONS_PER_USER=10
SESSION_IDLE_TIMEOUT=1800  # 30 minutes
SESSION_ABSOLUTE_TIMEOUT=86400  # 24 hours

# Security Configuration
RATE_LIMIT_REFRESH_PER_MINUTE=10
RATE_LIMIT_WINDOW_SECONDS=60
ENABLE_SESSION_BINDING=true  # Bind sessions to IP/device
ENABLE_AUDIT_LOGGING=true
```

## Security Considerations

### 1. Token Storage Security
- Encrypted storage in Vercel KV/Redis
- Separate storage for access and refresh tokens
- Token hashing before storage (for comparison)

### 2. Refresh Token Rotation
- One-time use refresh tokens
- Grace period for race conditions
- Automatic revocation of old tokens

### 3. Session Hijacking Prevention
- IP address validation
- Device fingerprinting
- Suspicious activity detection

### 4. Rate Limiting
- Per-user rate limits on refresh
- Global rate limits for protection
- Exponential backoff on failures

### 5. Audit Trail
- All token operations logged
- Revocation events tracked
- Session lifecycle events recorded

## Implementation Modules

### Core Modules Structure
```
phase4/
├── __init__.py
├── models/
│   ├── __init__.py
│   ├── session.py
│   ├── token.py
│   └── device.py
├── services/
│   ├── __init__.py
│   ├── token_refresh.py
│   ├── session_manager.py
│   ├── revocation.py
│   └── audit.py
├── storage/
│   ├── __init__.py
│   ├── base.py
│   ├── vercel_kv.py
│   ├── redis.py
│   └── supabase.py
├── middleware/
│   ├── __init__.py
│   ├── rate_limit.py
│   ├── session_validator.py
│   └── security.py
├── endpoints/
│   ├── __init__.py
│   ├── token.py
│   └── session.py
├── utils/
│   ├── __init__.py
│   ├── crypto.py
│   └── device_parser.py
└── migrations/
    ├── __init__.py
    └── phase2_to_phase4.py
```

## Testing Strategy

### Unit Tests
- Token refresh logic
- Session lifecycle management
- Storage operations
- Security validations

### Integration Tests
- End-to-end token refresh flow
- Multi-session scenarios
- Revocation propagation
- Rate limiting behavior

### Performance Tests
- Token refresh latency
- Storage operation speed
- Concurrent session handling

### Security Tests
- Token rotation security
- Session hijacking prevention
- Rate limiting effectiveness

## Migration Path from Phase 2

### Step 1: Deploy Storage Infrastructure
1. Set up Vercel KV or Redis
2. Configure environment variables
3. Test connectivity

### Step 2: Deploy Phase 4 Code
1. Deploy new endpoints alongside Phase 2
2. Enable feature flags for gradual rollout
3. Monitor for issues

### Step 3: Migrate Active Sessions
1. Run migration script for existing tokens
2. Convert to new session format
3. Maintain backward compatibility

### Step 4: Cut Over
1. Switch clients to new endpoints
2. Deprecate Phase 2 endpoints
3. Clean up old code

## Performance Considerations

### Caching Strategy
- Cache valid tokens in memory (5-minute TTL)
- Cache user session lists
- Use write-through cache for updates

### Storage Optimization
- Batch operations where possible
- Use pipelining for Redis
- Implement connection pooling

### Latency Targets
- Token refresh: < 100ms p95
- Session lookup: < 50ms p95
- Revocation: < 200ms p95

## Monitoring and Observability

### Key Metrics
- Token refresh rate
- Token refresh failures
- Active sessions per user
- Revocation events
- Rate limit violations

### Alerts
- High token refresh failure rate
- Unusual session creation patterns
- Storage latency spikes
- Security events

## Success Criteria

1. **Reliability**: 99.9% uptime for auth services
2. **Performance**: Meet latency targets
3. **Security**: Zero security breaches
4. **User Experience**: Seamless token refresh
5. **Scalability**: Support 10K concurrent sessions

## Implementation Timeline

### Week 1: Core Infrastructure
- Storage layer implementation
- Basic models and services
- Unit tests

### Week 2: Token Refresh
- Refresh service implementation
- Rotation mechanism
- Integration tests

### Week 3: Session Management
- Session manager implementation
- Multi-session support
- Revocation service

### Week 4: Security & Migration
- Security middleware
- Rate limiting
- Migration tools
- Performance testing

## Risk Assessment

### Technical Risks
- Storage provider outages
- Token rotation race conditions
- Migration data loss

### Mitigation Strategies
- Multi-region storage deployment
- Implement grace periods
- Comprehensive backup strategy
- Gradual rollout with rollback plan