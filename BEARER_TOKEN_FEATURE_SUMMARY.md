# Bearer Token Authentication Feature Summary

## Overview

Added support for frontend clients to pass AuthKit JWT tokens directly to the MCP server via HTTP `Authorization: Bearer <token>` headers. This enables seamless integration between frontend authentication flows and MCP server operations.

This implementation follows FastMCP's [Token Verification](https://gofastmcp.com/servers/auth/token-verification) pattern, treating the MCP server as a resource server that validates bearer tokens. The hybrid approach supports both:

- **MCP Clients**: Using FastMCP's AuthKitProvider OAuth flow
- **Frontend Clients**: Using direct bearer token authentication via HTTP headers

Both authentication paths validate tokens against the same AuthKit/Supabase backend, ensuring consistent security and user context.

## Changes Made

### 1. Core Authentication Module (`server/auth.py`)

**Modified:** `extract_bearer_token()` function

**Changes:**
- Added import for `get_http_headers` from `fastmcp.server.dependencies`
- Implemented priority-based token extraction:
  1. **HTTP Authorization header** (highest priority) - for frontend clients
  2. **FastMCP OAuth context** - for MCP clients  
  3. **Claims dict fallback** - for backward compatibility
- Added graceful error handling for non-HTTP contexts (e.g., stdio transport)
- Updated docstring to document the new functionality

**Key Features:**
- Extracts Bearer tokens from `Authorization: Bearer <token>` headers
- Validates token format (strips "Bearer " prefix and whitespace)
- Falls back to existing OAuth flow if no HTTP header present
- Maintains backward compatibility with existing authentication methods

### 2. Documentation

**Created:** `docs/deployment/FRONTEND_BEARER_TOKEN.md`

Comprehensive guide covering:
- How bearer token authentication works
- Frontend integration examples (TypeScript/React)
- Python client examples
- Token validation flow
- Security considerations (HTTPS, token expiration, CORS)
- Debugging tips
- Migration guide from other auth methods
- Compatibility matrix

**Updated:** `README.md`

Added new "Authentication" section with:
- Overview of authentication methods
- Bearer token usage examples
- Configuration instructions
- Links to detailed documentation

### 3. Examples

**Created:** `examples/frontend-bearer-token-example.ts`

Complete TypeScript/JavaScript example featuring:
- `MCPClient` class for authenticated MCP requests
- Integration with AuthKit for token management
- React hook (`useAtomsMCP`) for easy component integration
- CRUD operations for all entity types
- Workspace context management
- Workflow execution
- RAG search queries
- Error handling and token refresh

### 4. Tests

**Created:** `tests/unit/test_bearer_token_auth.py`

Comprehensive test suite with 14 tests covering:
- Bearer token extraction from HTTP headers
- Whitespace handling
- Case-insensitive header matching
- Non-Bearer auth scheme rejection
- Empty token handling
- Fallback to FastMCP OAuth
- Priority ordering (HTTP header > OAuth > claims)
- Exception handling for non-HTTP contexts
- Claims dict fallback
- Token masking for security
- Integration with rate limiting
- Real JWT format validation

**Test Results:** ✅ All 14 tests passing

## Technical Details

### Hybrid Authentication Architecture

The implementation uses a hybrid approach that combines:

1. **FastMCP's `get_http_headers()`**: To extract bearer tokens from HTTP requests
2. **FastMCP's `get_access_token()`**: To access OAuth context from AuthKitProvider
3. **Custom Priority Logic**: To support both authentication methods seamlessly

This differs from using FastMCP's built-in token verification providers (like `JWTVerifier`) because:

- **JWTVerifier**: Pure token verification, no OAuth discovery
- **AuthKitProvider**: OAuth flow with discovery, but doesn't automatically check HTTP headers
- **Our Hybrid**: Combines both approaches for maximum flexibility

### Token Extraction Priority

```python
def extract_bearer_token() -> BearerToken | None:
    # Priority 1: HTTP Authorization header (for frontend clients)
    try:
        headers = get_http_headers()
        if headers.get("authorization", "").startswith("Bearer "):
            return BearerToken(token=..., source="http.authorization.bearer")
    except Exception:
        pass  # Not in HTTP context (e.g., stdio transport)

    # Priority 2: FastMCP OAuth context (for MCP clients)
    access_token = get_access_token()
    if access_token and access_token.token:
        return BearerToken(token=..., source="authkit.token")

    # Priority 3: Claims dict fallback (for compatibility)
    if access_token and access_token.claims:
        # Check for token in claims
        ...

    return None
```

### Why Not Use JWTVerifier Directly?

FastMCP's `JWTVerifier` is excellent for pure resource server scenarios:

```python
# Pure JWTVerifier approach (frontend-only)
from fastmcp.server.auth.providers.jwt import JWTVerifier

verifier = JWTVerifier(
    jwks_uri="https://auth.company.com/.well-known/jwks.json",
    issuer="https://auth.company.com",
    audience="mcp-server"
)
```

However, this doesn't support MCP client OAuth flows. Our hybrid implementation provides:

- ✅ MCP client OAuth with AuthKitProvider
- ✅ Frontend bearer token authentication
- ✅ Unified token validation via Supabase
- ✅ Consistent RLS enforcement

### Frontend Usage Pattern

```typescript
// Get AuthKit token
const accessToken = await authkit.getAccessToken();

// Call MCP server with Bearer token
const response = await fetch('https://mcp-server.com/api/mcp', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    jsonrpc: '2.0',
    id: 1,
    method: 'tools/call',
    params: {
      name: 'entity_tool',
      arguments: { /* ... */ },
    },
  }),
});
```

## Benefits

1. **Unified Authentication**: Frontend can use the same AuthKit JWT for both Supabase and MCP server
2. **Simplified Integration**: No need for separate OAuth flow in frontend
3. **Backward Compatible**: Existing MCP clients continue to work unchanged
4. **Secure**: Tokens validated against Supabase/AuthKit, RLS enforced
5. **Flexible**: Supports multiple authentication methods with clear priority
6. **Production Ready**: Comprehensive tests, documentation, and examples

## Security Considerations

- ✅ HTTPS required in production
- ✅ Token validation against Supabase/AuthKit
- ✅ Row Level Security (RLS) enforced based on user context
- ✅ Token masking in logs
- ✅ Graceful handling of expired tokens
- ✅ CORS configuration required for frontend access

## Compatibility

### Compatible With:
- ✅ AuthKit JWT tokens
- ✅ Supabase authentication
- ✅ FastMCP OAuth flow (fallback)
- ✅ HTTP and HTTPS transports
- ✅ Vercel serverless deployment
- ✅ All existing MCP tools

### Not Compatible With:
- ❌ stdio transport (no HTTP headers available)
- ❌ Non-JWT token formats (unless configured in Supabase)

## Migration Path

Existing deployments require **no changes**. The feature is additive:

1. **MCP Clients**: Continue using OAuth flow (no changes needed)
2. **Frontend Clients**: Can now use Bearer tokens (new capability)
3. **Configuration**: No new environment variables required (uses existing AuthKit config)

## Testing

Run the test suite:

```bash
# Run bearer token tests
pytest tests/unit/test_bearer_token_auth.py -v

# Run all auth-related tests
pytest tests/unit/test_bearer_token_auth.py tests/unit/test_server_auth_errors.py -v
```

## Files Modified

1. `server/auth.py` - Core authentication logic
2. `README.md` - Added authentication section
3. `docs/deployment/FRONTEND_BEARER_TOKEN.md` - New documentation
4. `examples/frontend-bearer-token-example.ts` - New example
5. `tests/unit/test_bearer_token_auth.py` - New test suite

## Next Steps

### For Developers:
1. Review the documentation in `docs/deployment/FRONTEND_BEARER_TOKEN.md`
2. Check the example in `examples/frontend-bearer-token-example.ts`
3. Run tests to verify functionality: `pytest tests/unit/test_bearer_token_auth.py -v`

### For Frontend Integration:
1. Install AuthKit client: `npm install @workos-inc/authkit-js`
2. Get access token from AuthKit
3. Pass token in `Authorization: Bearer <token>` header
4. Make JSON-RPC 2.0 requests to MCP endpoint

### For Deployment:
1. Ensure HTTPS is enabled in production
2. Configure CORS to allow frontend domain
3. Set AuthKit environment variables (already configured)
4. No additional configuration needed

## Support

For questions or issues:
- See documentation: `docs/deployment/FRONTEND_BEARER_TOKEN.md`
- Check examples: `examples/frontend-bearer-token-example.ts`
- Review tests: `tests/unit/test_bearer_token_auth.py`
- Refer to AuthKit docs: `docs/deployment/AUTHKIT_FASTMCP.md`

