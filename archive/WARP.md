# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

The **Atoms FastMCP Server** is a Python-based MCP (Model Context Protocol) server providing comprehensive access to the Atoms API domains. It's built with FastMCP 2.12+ and integrates with Supabase for data persistence and WorkOS AuthKit for OAuth 2.0 authentication.

**Key Characteristics:**
- **Authentication-first**: All operations require explicit authentication via session tokens
- **Consolidated tool architecture**: Five high-level tools replace granular API endpoints  
- **Dual deployment modes**: STDIO (development) and HTTP (production/serverless)
- **Serverless-optimized**: Stateless HTTP mode for Vercel deployment with session persistence

## Essential Commands

### Development & Testing

```bash
# Start development server (STDIO mode)
python -m atoms_mcp-old

# Start HTTP server for testing
ATOMS_FASTMCP_TRANSPORT=http ATOMS_FASTMCP_PORT=8000 python -m atoms_mcp-old

# Start with local services (MCP + Cloudflare tunnel)
python -m atoms_mcp-old --local

# Run comprehensive test suite
pytest tests/ -v -s

# Run specific test categories
pytest tests/test_integration_workflows.py -v -s        # End-to-end workflows
pytest tests/test_error_handling.py -v -s              # Error scenarios
pytest tests/test_performance.py -v -s                 # Performance benchmarks

# Run individual tool tests
pytest tests/test_entity_tool_comprehensive.py -v -s
pytest tests/test_workspace_tool_comprehensive.py -v -s
pytest tests/test_query_tool_comprehensive.py -v -s
pytest tests/test_relationship_tool.py -v -s
pytest tests/test_workflow_tool_comprehensive.py -v -s

# Generate test reports
./tests/run_integration_tests.sh                       # Full integration suite with coverage
```

### Deployment

```bash
# Vercel deployment (uses app.py)
# Automatically uses stateless_http=True for serverless compatibility

# Health check endpoints
curl http://localhost:8000/health                      # Local development
curl https://your-domain.com/health                    # Production
```

## High-Level Architecture

### Core Tool Structure

The server provides **5 consolidated tools** that abstract away the underlying 80+ granular API endpoints:

1. **`workspace_operation`** - Organization and project management, member operations
2. **`entity_operation`** - CRUD operations for documents, requirements, properties, etc.
3. **`relationship_operation`** - Trace links and entity relationships
4. **`workflow_execute`** - Multi-step business processes with transaction support
5. **`data_query`** - Advanced search, filtering, and semantic queries

### Authentication Flow

**Development Mode:**
- Uses demo credentials (`FASTMCP_DEMO_USER`/`FASTMCP_DEMO_PASS`)
- In-memory session storage

**Production Mode:**
- OAuth 2.0 PKCE + Dynamic Client Registration (DCR) via WorkOS AuthKit
- Session persistence via Supabase `mcp_sessions` table
- Stateless serverless deployment support

### Key Architectural Patterns

**Adapter Pattern (`infrastructure/`):**
- `SupabaseDatabaseAdapter` - Database operations with RLS
- `SupabaseAuthAdapter` - Authentication and user management  
- `SupabaseStorageAdapter` - File storage operations
- `factory.py` - Dependency injection container

**Tool Base Class (`tools/base.py`):**
- Common authentication validation
- Database query abstractions
- Entity sanitization (prevents token overflow)
- Error normalization

**Session Management (`auth/`):**
- `SessionMiddleware` - ASGI middleware for stateless session handling
- `session_manager.py` - Supabase-backed session persistence
- `persistent_authkit_provider.py` - Custom FastMCP auth provider

### Response Serialization

All tool responses are **automatically converted to Markdown** for optimal readability and token efficiency:
- Structured data becomes tables and lists
- Success/error states get clear visual indicators (✅/❌)
- Large objects are sanitized to prevent context overflow

## Critical Implementation Details

### Serverless Deployment Fixes

The codebase includes specific patches for Vercel serverless deployment:

- **Task Group Patching** (`app.py`): Monkey-patches `StreamableHTTPSessionManager` to handle serverless execution contexts
- **Stateless HTTP Mode**: `stateless_http=True` prevents FastMCP from maintaining persistent connections
- **Session Persistence**: Uses Supabase instead of in-memory storage for OAuth sessions

### Database Context Management

**Row Level Security (RLS):** All database operations automatically set the user's access token on the Supabase client, ensuring `auth.uid()` returns the correct user ID for RLS policies.

**Transaction Support:** The `workflow_execute` tool supports explicit transaction management with rollback capabilities for multi-step operations.

### Performance Optimizations

- **Entity Sanitization**: Large fields (embeddings, nested structures) are automatically stripped from responses
- **Batch Operations**: Bulk import/update operations handle 100+ items efficiently 
- **Semantic Search**: Vector embedding integration for intelligent content discovery

## Environment Configuration

### Required (Supabase)
```bash
NEXT_PUBLIC_SUPABASE_URL=your-supabase-url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

### Required (OAuth Production)
```bash
FASTMCP_SERVER_AUTH=fastmcp.server.auth.providers.workos.AuthKitProvider
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN=your-authkit-domain
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL=your-public-server-url
WORKOS_API_KEY=your-workos-api-key  
WORKOS_CLIENT_ID=your-workos-client-id
```

### Optional (Development)
```bash
FASTMCP_DEMO_USER=test-user
FASTMCP_DEMO_PASS=test-password
ATOMS_FASTMCP_TRANSPORT=http|stdio
ATOMS_FASTMCP_PORT=8000
```

## Common Patterns

### Error Handling
All tools use the `normalize_error()` function to provide consistent, informative error messages. Authentication failures, validation errors, and database constraints are handled gracefully with appropriate HTTP status codes.

### Tool Parameter Structure
Each consolidated tool accepts:
- `session_token` (required) - Authentication token
- `operation` (required) - Specific operation to perform
- `params` (optional) - Operation-specific parameters
- `context` (optional) - Additional context for the operation

### Testing Patterns
The test suite follows a comprehensive matrix approach:
- **Unit tests** for individual tool operations
- **Integration tests** for end-to-end workflows
- **Performance tests** with realistic load scenarios
- **Error handling tests** for edge cases and failures

## Troubleshooting

### Common Issues

**OAuth/CORS Errors:**
- Verify `AUTHKIT_DOMAIN` is correct: `curl https://your-domain/.well-known/oauth-authorization-server`
- Ensure Dynamic Client Registration is enabled in WorkOS Dashboard
- Check CORS configuration in Vercel deployment settings

**Session Issues:**
- Sessions are stored in `mcp_sessions` Supabase table
- Session tokens include Supabase JWT for RLS context
- Clear sessions: `DELETE FROM mcp_sessions WHERE expires_at < NOW()`

**Performance Issues:**
- Large entity responses are auto-sanitized
- Use `data_query` tool with filters instead of fetching all records
- Monitor embedding generation with `scripts/check_embedding_status.py`

### Debug Commands

```bash
# View server logs
tail -f /tmp/atoms_mcp.log

# Test authentication
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/mcp

# Check Supabase connection
python -c "from infrastructure.factory import get_adapters; print(get_adapters()['database'])"
```

This codebase is designed for AI-assisted development workflows, with clear separation of concerns, comprehensive test coverage, and robust error handling patterns.
