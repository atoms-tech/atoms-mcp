# Bearer Token Implementation Guide

This document provides technical details about the bearer token authentication implementation in the Atoms MCP server.

## Overview

The Atoms MCP server implements a **hybrid authentication approach** that combines:

1. **FastMCP's Token Verification Pattern**: Following [FastMCP's token verification model](https://gofastmcp.com/servers/auth/token-verification)
2. **AuthKitProvider OAuth Flow**: For MCP clients requiring full OAuth discovery
3. **HTTP Bearer Token Extraction**: For frontend clients passing tokens directly

This hybrid approach provides maximum flexibility while maintaining security and compatibility.

## Architecture

### Token Flow Diagram

```
┌─────────────────┐
│ Frontend Client │
│  (React/Vue)    │
└────────┬────────┘
         │ 1. Get AuthKit JWT
         │    from AuthKit
         ▼
┌─────────────────┐
│   AuthKit       │
│ (WorkOS)        │
└────────┬────────┘
         │ 2. Return JWT
         ▼
┌─────────────────┐
│ Frontend Client │
└────────┬────────┘
         │ 3. HTTP Request
         │    Authorization: Bearer <JWT>
         ▼
┌─────────────────────────────────────┐
│      Atoms MCP Server               │
│                                     │
│  ┌──────────────────────────────┐  │
│  │ extract_bearer_token()       │  │
│  │                              │  │
│  │ Priority 1: HTTP Header      │  │
│  │ Priority 2: OAuth Context    │  │
│  │ Priority 3: Claims Fallback  │  │
│  └──────────┬───────────────────┘  │
│             │                       │
│             ▼                       │
│  ┌──────────────────────────────┐  │
│  │ Validate Token via Supabase  │  │
│  └──────────┬───────────────────┘  │
│             │                       │
│             ▼                       │
│  ┌──────────────────────────────┐  │
│  │ Establish User Context       │  │
│  │ (RLS, Permissions)           │  │
│  └──────────┬───────────────────┘  │
│             │                       │
│             ▼                       │
│  ┌──────────────────────────────┐  │
│  │ Execute Tool Operation       │  │
│  └──────────────────────────────┘  │
└─────────────────────────────────────┘
```

### MCP Client Flow

```
┌─────────────────┐
│   MCP Client    │
│  (AI Assistant) │
└────────┬────────┘
         │ 1. OAuth Discovery
         ▼
┌─────────────────────────────────────┐
│      Atoms MCP Server               │
│  (AuthKitProvider)                  │
└────────┬────────────────────────────┘
         │ 2. OAuth Metadata
         ▼
┌─────────────────┐
│   MCP Client    │
└────────┬────────┘
         │ 3. OAuth Flow
         ▼
┌─────────────────┐
│   AuthKit       │
└────────┬────────┘
         │ 4. Access Token
         ▼
┌─────────────────┐
│   MCP Client    │
└────────┬────────┘
         │ 5. MCP Request
         │    (Token in OAuth context)
         ▼
┌─────────────────────────────────────┐
│      Atoms MCP Server               │
│  extract_bearer_token()             │
│  → get_access_token()               │
└─────────────────────────────────────┘
```

## Implementation Details

### Core Function: `extract_bearer_token()`

Located in `server/auth.py`, this function implements the priority-based token extraction:

```python
def extract_bearer_token() -> BearerToken | None:
    """Extract bearer token from multiple sources with priority."""
    
    # Priority 1: HTTP Authorization header
    try:
        headers = get_http_headers()
        auth_header = headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token_str = auth_header[7:].strip()
            if token_str:
                return BearerToken(
                    token=token_str,
                    source="http.authorization.bearer",
                    claims=None
                )
    except Exception as e:
        # Not in HTTP context (e.g., stdio transport)
        logger.debug(f"Could not access HTTP headers: {e}")
    
    # Priority 2: FastMCP OAuth context
    access_token = get_access_token()
    if not access_token:
        return None
    
    token_str = getattr(access_token, "token", None)
    if token_str:
        claims = getattr(access_token, "claims", None)
        return BearerToken(
            token=token_str,
            source="authkit.token",
            claims=claims if isinstance(claims, dict) else None
        )
    
    # Priority 3: Claims dict fallback
    claims = getattr(access_token, "claims", None)
    if isinstance(claims, dict):
        for key in ("access_token", "token", "supabase_jwt"):
            candidate = claims.get(key)
            if candidate:
                return BearerToken(
                    token=candidate,
                    source=f"authkit.claims.{key}",
                    claims=claims
                )
    
    return None
```

### Key Design Decisions

#### 1. Priority-Based Extraction

**Why**: Different client types provide tokens in different ways:
- Frontend clients: HTTP `Authorization` header
- MCP clients: OAuth context via `get_access_token()`
- Legacy systems: Claims dict

**Benefit**: Single codebase supports all client types without configuration.

#### 2. Graceful Fallback

**Why**: `get_http_headers()` fails in non-HTTP contexts (e.g., stdio transport).

**Implementation**: Try-except block allows graceful fallback to OAuth context.

**Benefit**: Server works in both HTTP and stdio transports.

#### 3. Token Source Tracking

**Why**: Debugging and monitoring require knowing where tokens came from.

**Implementation**: `BearerToken.source` field tracks extraction method.

**Benefit**: Clear audit trail and easier troubleshooting.

## FastMCP Integration

### Using FastMCP's Context Functions

The implementation leverages FastMCP's context access functions:

```python
from fastmcp.server.dependencies import get_access_token, get_http_headers

# Access HTTP headers (HTTP transport only)
headers = get_http_headers()

# Access OAuth context (when using AuthKitProvider)
access_token = get_access_token()
```

These functions provide access to request context without requiring explicit dependency injection.

### Comparison with FastMCP's Built-in Providers

| Feature | Our Hybrid | JWTVerifier | AuthKitProvider |
|---------|-----------|-------------|-----------------|
| HTTP Bearer Tokens | ✅ | ✅ | ❌ |
| OAuth Discovery | ✅ | ❌ | ✅ |
| MCP Client Support | ✅ | ❌ | ✅ |
| Frontend Support | ✅ | ✅ | ⚠️ (OAuth) |
| Token Refresh | ✅ | ❌ | ✅ |

### When to Use Each Approach

**Use Our Hybrid Approach When**:
- You have both frontend and MCP clients
- You want maximum flexibility
- You're using AuthKit for authentication

**Use FastMCP's JWTVerifier When**:
- You only have frontend clients
- You want pure token verification
- You have an existing JWT infrastructure

**Use FastMCP's AuthKitProvider When**:
- You only have MCP clients
- You want full OAuth compliance
- You don't need frontend integration

## Token Validation

### Validation Flow

1. **Extract Token**: `extract_bearer_token()` gets token from request
2. **Validate with Supabase**: Token validated against Supabase/AuthKit
3. **Establish Context**: User context set for RLS enforcement
4. **Execute Operation**: Tool runs with proper permissions

### Validation Code

```python
async def apply_rate_limit_if_configured(
    rate_limiter: RateLimiter | None = None,
) -> BearerToken | None:
    """Apply rate limiting and extract bearer token."""
    
    # Extract token
    token = extract_bearer_token()
    
    if not token:
        logger.debug("No bearer token found")
        return None
    
    # Rate limiting (if configured)
    if rate_limiter:
        await rate_limiter.check_rate_limit(token.token)
    
    return token
```

### Supabase Integration

The token is validated via Supabase's authentication system:

```python
# In tool implementations
async with get_supabase_client(bearer_token) as supabase:
    # Token automatically validated
    # User context established
    # RLS enforced on all queries
    result = await supabase.table("projects").select("*").execute()
```

## Security Considerations

### Token Security

1. **HTTPS Required**: Tokens transmitted over HTTPS only in production
2. **Token Masking**: Tokens masked in logs and error messages
3. **Validation**: All tokens validated against Supabase/AuthKit
4. **RLS Enforcement**: Row Level Security enforced based on user context

### Implementation

```python
@dataclass
class BearerToken:
    """Bearer token with security features."""
    token: str
    source: str
    claims: dict[str, Any] | None = None
    
    def __str__(self) -> str:
        """Mask token in string representation."""
        if len(self.token) <= 8:
            return "***"
        return f"{self.token[:4]}...{self.token[-4:]}"
```

### Rate Limiting

Optional rate limiting per token:

```python
rate_limiter = RateLimiter(
    max_requests=100,
    window_seconds=60
)

token = await apply_rate_limit_if_configured(rate_limiter)
```

## Testing

### Unit Tests

Comprehensive test suite in `tests/unit/test_bearer_token_auth.py`:

- ✅ HTTP header extraction
- ✅ OAuth context fallback
- ✅ Priority ordering
- ✅ Error handling
- ✅ Token masking
- ✅ Integration scenarios

### Running Tests

```bash
# Run bearer token tests
pytest tests/unit/test_bearer_token_auth.py -v

# Run with coverage
pytest tests/unit/test_bearer_token_auth.py --cov=server.auth --cov-report=html
```

### Integration Testing

Example integration test in `examples/test_bearer_token_integration.py`:

```bash
python examples/test_bearer_token_integration.py
```

## Deployment

### Environment Variables

No additional environment variables required! The implementation uses existing AuthKit configuration:

```bash
# Existing AuthKit configuration
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN=https://your-project.authkit.app
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL=https://your-mcp-server.com

# Existing Supabase configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

### CORS Configuration

For frontend clients, configure CORS:

```python
from starlette.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=['https://your-frontend.com'],
    allow_credentials=True,
    allow_methods=['POST', 'GET'],
    allow_headers=['Authorization', 'Content-Type'],
)
```

## Monitoring and Debugging

### Logging

Enable debug logging to see token extraction:

```python
import logging
logging.getLogger("server.auth").setLevel(logging.DEBUG)
```

Example log output:

```
DEBUG: Using Bearer token from Authorization header
DEBUG: Token source: http.authorization.bearer
```

### Metrics

Track token sources for monitoring:

```python
from collections import Counter

token_sources = Counter()

def extract_bearer_token() -> BearerToken | None:
    token = # ... extraction logic
    if token:
        token_sources[token.source] += 1
    return token
```

## See Also

- [Authentication Methods Comparison](./AUTHENTICATION_COMPARISON.md) - Choose the right approach
- [Frontend Bearer Token Guide](./FRONTEND_BEARER_TOKEN.md) - Frontend integration
- [FastMCP Token Verification](https://gofastmcp.com/servers/auth/token-verification) - Official docs
- [Bearer Token Feature Summary](../../BEARER_TOKEN_FEATURE_SUMMARY.md) - Feature overview

