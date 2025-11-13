"""New atoms_fastmcp server with consolidated, agent-optimized tools."""

from __future__ import annotations

import os
import logging
import warnings
import sys
from datetime import datetime
from typing import Any, Dict, Optional

# Suppress websockets deprecation warnings from uvicorn
warnings.filterwarnings("ignore", category=DeprecationWarning, module="websockets")

# Fix Python path for Vercel deployment
# This ensures all modules are available in the serverless environment
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
# Also add /var/task explicitly for Vercel
if '/var/task' not in sys.path and os.path.exists('/var/task'):
    sys.path.insert(0, '/var/task')

from fastmcp import FastMCP  # noqa: E402
from fastmcp.server.dependencies import get_access_token  # noqa: E402

# Import tools with fallback for different environments
try:
    from .tools import (
        workspace_operation,
        entity_operation,
        relationship_operation,
        workflow_execute,
        data_query,
    )
except ImportError:
    # For Vercel deployment and other flat structures
    from tools import (
        workspace_operation,
        entity_operation,
        relationship_operation,
        workflow_execute,
        data_query,
    )

logger = logging.getLogger("atoms_fastmcp")


def _markdown_serializer(data: Any) -> str:
    """Serialize tool responses as Markdown for better readability and token efficiency.

    Converts Python objects to well-formatted Markdown:
    - Dicts → Tables or code blocks
    - Lists → Bulleted or numbered lists
    - Primitives → Inline code or plain text
    """
    if data is None:
        return "*No data*"

    if isinstance(data, str):
        return data  # Already a string, bypass serialization

    if isinstance(data, bool):
        return "✅ Yes" if data else "❌ No"

    if isinstance(data, (int, float)):
        return f"`{data}`"

    if isinstance(data, dict):
        return _dict_to_markdown(data)

    if isinstance(data, list):
        return _list_to_markdown(data)

    # Fallback to string representation
    return f"```\n{str(data)}\n```"


def _dict_to_markdown(d: Dict[str, Any], indent: int = 0) -> str:
    """Convert dict to Markdown format."""
    if not d:
        return "*Empty*"

    # Check if dict looks like a single result with success/data structure
    if "success" in d and "data" in d:
        lines = []
        success = d.get("success")
        lines.append(f"**Status**: {'✅ Success' if success else '❌ Failed'}")

        if not success and "error" in d:
            lines.append(f"**Error**: `{d['error']}`")

        if "data" in d:
            data = d["data"]
            if isinstance(data, list) and len(data) > 0:
                lines.append(f"\n**Results** ({len(data)} items):\n")
                lines.append(_list_to_markdown(data))
            elif isinstance(data, dict):
                lines.append("\n**Data**:")
                lines.append(_dict_to_markdown(data, indent=1))
            elif data:
                lines.append(f"**Data**: {data}")

        # Add metadata if present
        metadata_fields = ["count", "total_results", "search_time_ms", "timestamp"]
        metadata = {k: v for k, v in d.items() if k in metadata_fields}
        if metadata:
            lines.append("\n**Metadata**:")
            for key, value in metadata.items():
                lines.append(f"- {key}: `{value}`")

        return "\n".join(lines)

    # Regular dict - format as key-value list
    lines = []
    prefix = "  " * indent
    for key, value in d.items():
        if isinstance(value, dict):
            lines.append(f"{prefix}**{key}**:")
            lines.append(_dict_to_markdown(value, indent + 1))
        elif isinstance(value, list):
            lines.append(f"{prefix}**{key}**: ({len(value)} items)")
            if len(value) <= 3:
                lines.append(_list_to_markdown(value, indent + 1))
        elif value is None:
            continue  # Skip null values
        else:
            # Truncate long strings
            str_value = str(value)
            if len(str_value) > 100:
                str_value = str_value[:100] + "..."
            lines.append(f"{prefix}**{key}**: `{str_value}`")

    return "\n".join(lines)


def _list_to_markdown(lst: list, indent: int = 0) -> str:
    """Convert list to Markdown format."""
    if not lst:
        return "*Empty list*"

    lines = []
    prefix = "  " * indent

    # If list of dicts (common for entity results), format as cards
    if all(isinstance(item, dict) for item in lst):
        for i, item in enumerate(lst, 1):
            lines.append(f"\n{prefix}### {i}. {item.get('name', item.get('id', 'Item'))}")
            # Show key fields only
            key_fields = ["id", "name", "type", "status", "created_at", "similarity_score"]
            for key in key_fields:
                if key in item and item[key] is not None:
                    lines.append(f"{prefix}- **{key}**: `{item[key]}`")
    else:
        # Simple list
        for item in lst:
            lines.append(f"{prefix}- {item}")

    return "\n".join(lines)


def _extract_bearer_token() -> Optional[str]:
    """Return the bearer token from FastMCP's AuthKit OAuth.

    For stateless serverless with AuthKit:
    - FastMCP's AuthKitProvider validates OAuth tokens
    - Token is available via get_access_token()
    - No SessionMiddleware needed

    Returns:
        AuthKit JWT token or None
    """
    # Get token from FastMCP's OAuth context
    access_token = get_access_token()
    if not access_token:
        logger.debug("No access token from FastMCP")
        return None

    # AuthKit tokens are stored in .token attribute
    token = getattr(access_token, "token", None)
    if token:
        logger.debug("Using AuthKit token from FastMCP")
        return str(token) if token else None  # type: ignore[return-value]

    # Fallback: check claims dict
    claims = getattr(access_token, "claims", None)
    if isinstance(claims, dict):
        for key in ("access_token", "token", "supabase_jwt"):
            candidate = claims.get(key)
            if candidate:
                logger.debug(f"Using token from claims.{key}")
                return str(candidate) if candidate else None  # type: ignore[return-value]

    logger.debug("No valid token found in access_token object")
    return None


async def _check_rate_limit(user_id: str) -> None:
    """Check rate limit for user and raise exception if exceeded.

    Args:
        user_id: User identifier for rate limiting

    Raises:
        RuntimeError: If rate limit exceeded
    """
    global _rate_limiter
    if _rate_limiter and not await _rate_limiter.check_limit(user_id):
        remaining = _rate_limiter.get_remaining(user_id)
        raise RuntimeError(
            f"Rate limit exceeded. Please wait before making more requests. "
            f"Remaining: {remaining} requests in current window."
        )


async def _apply_rate_limit_if_configured() -> Optional[str]:
    """Apply rate limiting if configured. Returns auth token.

    Returns:
        auth_token for use in operations

    Raises:
        RuntimeError: If rate limit exceeded
    """
    auth_token = _extract_bearer_token()

    # Only apply rate limiting if we have a token and rate limiter is configured
    global _rate_limiter
    if auth_token and _rate_limiter:
        # Extract user_id from token without full validation (tools will validate)
        try:
            from tools.base import ToolBase
            tool_base = ToolBase()
            await tool_base._validate_auth(auth_token)
            user_id = tool_base._get_user_id()
            await _check_rate_limit(user_id)
        except Exception as e:
            # If rate limit check fails, let it propagate
            # But if auth parsing fails, tools will handle it
            if "Rate limit" in str(e):
                raise

    return auth_token


def _load_env_files() -> None:
    """Load environment variables from .env and .env.local if available."""
    try:
        from dotenv import dotenv_values  # type: ignore
    except Exception:
        if os.path.exists(".env") or os.path.exists(".env.local"):
            logger.info(
                "python-dotenv not installed; skipping .env loading. Install python-dotenv to enable."
            )
        return

    merged: Dict[str, str] = {}
    if os.path.exists(".env"):
        try:
            merged.update(
                {
                    k: v
                    for k, v in (dotenv_values(".env") or {}).items()
                    if v is not None
                }
            )
        except Exception as e:
            logger.warning(f"Failed loading .env: {e}")
    if os.path.exists(".env.local"):
        try:
            local_vals = {
                k: v
                for k, v in (dotenv_values(".env.local") or {}).items()
                if v is not None
            }
            merged.update(local_vals)
        except Exception as e:
            logger.warning(f"Failed loading .env.local: {e}")

    for k, v in merged.items():
        os.environ.setdefault(k, v)


# Global rate limiter instance
_rate_limiter = None


def create_consolidated_server() -> FastMCP:
    """Create the new FastMCP server with consolidated tools.

    This server replaces the 100+ individual tools with 5 smart, agent-optimized tools:
    - workspace_operation: Context management
    - entity_operation: Unified CRUD for all entities
    - relationship_operation: Manage entity relationships
    - workflow_execute: Complex multi-step operations
    - data_query: Data exploration and analysis
    """

    # Load env files early for auth configuration
    _load_env_files()

    # Debug environment loading
    fastmcp_vars = {k: v for k, v in os.environ.items() if "FASTMCP" in k}
    print(f"🔍 DEBUG: FASTMCP environment variables after loading .env: {fastmcp_vars}")
    logger.info(
        f"🔍 DEBUG: FASTMCP environment variables after loading .env: {fastmcp_vars}"
    )

    # Create auth provider with base URL
    # Use FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL which is set per environment:
    # - Local: http://localhost:8000 or http://127.0.0.1:8000
    # - Vercel Preview: https://mcpdev.atoms.tech
    # - Vercel Production: https://mcp.atoms.tech

    base_url_raw = os.getenv("FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL")
    logger.info(f"🔍 DEBUG: Raw FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL from env: '{base_url_raw}'")
    print(f"🔍 DEBUG: Raw BASE_URL from env: '{base_url_raw}'")

    base_url = base_url_raw

    # Clean up the URL (remove /api/mcp or /mcp suffix if present)
    if base_url:
        base_url = base_url.rstrip("/")
        if base_url.endswith("/api/mcp"):
            base_url = base_url[: -len("/api/mcp")]
            logger.info("🔍 DEBUG: Stripped /api/mcp suffix")
        elif base_url.endswith("/mcp"):
            base_url = base_url[: -len("/mcp")]
            logger.info("🔍 DEBUG: Stripped /mcp suffix")

    # Fallback if not set
    if not base_url:
        host = os.getenv("ATOMS_FASTMCP_HOST", "127.0.0.1")
        port = os.getenv("ATOMS_FASTMCP_PORT", "8000")
        base_url = f"http://{host}:{port}"
        logger.warning(f"⚠️  FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL not set, using fallback: {base_url}")

    logger.info(f"✅ Resolved base URL for OAuth resource: {base_url}")
    print(f"🌐 AUTH BASE URL -> {base_url}")

    # Configure hybrid authentication (OAuth + Bearer tokens)
    authkit_domain = os.getenv("FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN")
    if not authkit_domain:
        raise ValueError("FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN required")

    # Get optional bearer token configuration
    internal_token = os.getenv("ATOMS_INTERNAL_TOKEN")
    authkit_client_id = os.getenv("WORKOS_CLIENT_ID")

    # Construct AuthKit JWKS URI from domain
    authkit_jwks_uri = None
    if authkit_domain:
        # AuthKit JWKS endpoint is at /.well-known/jwks.json
        authkit_jwks_uri = f"{authkit_domain}/.well-known/jwks.json"

    # Use hybrid auth provider supporting both OAuth and Bearer tokens
    try:
        from services.auth.hybrid_auth_provider import create_hybrid_auth_provider
    except ImportError:
        from .services.auth.hybrid_auth_provider import create_hybrid_auth_provider  # type: ignore[no-redef]

    auth_provider = create_hybrid_auth_provider(
        authkit_domain=authkit_domain,
        base_url=base_url,
        internal_token=internal_token,
        authkit_client_id=authkit_client_id,
        authkit_jwks_uri=authkit_jwks_uri
    )

    logger.info("✅ Hybrid authentication configured:")
    logger.info(f"  - OAuth (AuthKit): {authkit_domain}")
    if internal_token:
        logger.info("  - Internal bearer token: enabled")
    if authkit_client_id and authkit_jwks_uri:
        logger.info("  - AuthKit JWT: enabled")

    print("✅ Hybrid authentication configured: OAuth + Bearer tokens")

    # Initialize distributed rate limiter (Upstash Redis with in-memory fallback)
    try:
        from .infrastructure.distributed_rate_limiter import get_distributed_rate_limiter
    except ImportError:
        from infrastructure.distributed_rate_limiter import get_distributed_rate_limiter  # type: ignore[no-redef]
    
    # Initialize async rate limiter
    global _rate_limiter
    try:
        import asyncio
        # Get the distributed rate limiter asynchronously
        loop = asyncio.new_event_loop()
        _rate_limiter_instance = loop.run_until_complete(get_distributed_rate_limiter())
        
        # Wrap it to work with sync context
        class _SyncRateLimiterWrapper:
            def __init__(self, async_limiter):
                self.async_limiter = async_limiter
                self.loop = asyncio.new_event_loop()
            
            def check_limit(self, user_id: str, operation_type: str = "default") -> bool:
                """Sync wrapper for async rate limit check."""
                try:
                    result = self.loop.run_until_complete(
                        self.async_limiter.check_rate_limit(user_id, operation_type)
                    )
                    return result.get("allowed", False)
                except Exception as e:
                    logger.warning(f"Rate limit check failed: {e}, allowing request")
                    return True
            
            def get_remaining(self, user_id: str, operation_type: str = "default") -> int:
                """Get remaining requests."""
                try:
                    return self.loop.run_until_complete(
                        self.async_limiter.get_remaining(user_id, operation_type)
                    )
                except:
                    return 0
        
        _rate_limiter = _SyncRateLimiterWrapper(_rate_limiter_instance)
        rate_limit_rpm = int(os.getenv("MCP_RATE_LIMIT_RPM", "120"))
        logger.info(f"✅ Distributed rate limiter initialized: {rate_limit_rpm} requests/minute")
        print("✅ Distributed rate limiter: Upstash Redis (or in-memory fallback)")
    except Exception as e:
        logger.warning(f"Failed to initialize distributed rate limiter: {e}, using in-memory")
        try:
            from .infrastructure.rate_limiter import SlidingWindowRateLimiter
        except ImportError:
            from infrastructure.rate_limiter import SlidingWindowRateLimiter  # type: ignore[no-redef]
        
        rate_limit_rpm = int(os.getenv("MCP_RATE_LIMIT_RPM", "120"))
        _rate_limiter = SlidingWindowRateLimiter(window_seconds=60, max_requests=rate_limit_rpm)
        logger.info(f"✅ In-memory rate limiter configured: {rate_limit_rpm} requests/minute")

    mcp = FastMCP(
        name="atoms-fastmcp-consolidated",
        instructions=(
            "Atoms MCP server with consolidated, agent-optimized tools. "
            "Authenticate via OAuth (AuthKit). "
            "Use workspace_tool to manage context, entity_tool for CRUD, "
            "relationship_tool for associations, workflow_tool for complex tasks, "
            "and query_tool for data exploration including RAG search."
        ),
        auth=auth_provider,
        # No custom serializer - use default JSON for performance (minified)
    )

    # Add response caching middleware if Redis available
    try:
        if os.getenv("UPSTASH_REDIS_REST_URL"):
            try:
                from fastmcp.server.middleware.caching import ResponseCachingMiddleware
                from .infrastructure.upstash_provider import get_upstash_store
            except ImportError:
                from fastmcp.server.middleware.caching import ResponseCachingMiddleware  # type: ignore[no-redef]
                from infrastructure.upstash_provider import get_upstash_store  # type: ignore[no-redef]
            
            import asyncio
            try:
                # Initialize cache store
                loop = asyncio.new_event_loop()
                cache_store = loop.run_until_complete(get_upstash_store())
                
                # Add caching middleware
                cache_ttl = int(os.getenv("CACHE_TTL_RESPONSE", "3600"))
                mcp.add_middleware(ResponseCachingMiddleware(
                    cache_storage=cache_store,
                    ttl=cache_ttl
                ))
                logger.info(f"✅ Response caching middleware enabled (TTL: {cache_ttl}s)")
                print("✅ Response caching: Upstash Redis enabled")
            except Exception as e:
                logger.warning(f"Failed to enable caching middleware: {e}")
    except Exception as e:
        logger.warning(f"Caching middleware setup error: {e}")

    # Register consolidated tools
    @mcp.tool(tags={"workspace", "context"})
    async def workspace_tool(
        operation: str,
        context_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        format_type: str = "detailed",
    ) -> dict:
        """Manage workspace context and get smart defaults.

        Operations:
        - get_context: Get current workspace context
        - set_context: Set active organization/project/document
        - list_workspaces: List available workspaces
        - get_defaults: Get smart default values for operations

        Examples:
        - Set active project: operation="set_context", context_type="project", entity_id="proj_123"
        - Get current context: operation="get_context"
        - List organizations: operation="list_workspaces"
        """
        try:
            auth_token = await _apply_rate_limit_if_configured()
            return await workspace_operation(  # type: ignore[no-any-return]
                auth_token=auth_token,
                operation=operation,
                context_type=context_type,
                entity_id=entity_id,
                format_type=format_type,
            )
        except Exception as e:
            return {"success": False, "error": str(e), "operation": operation}

    @mcp.tool(tags={"entity", "crud"})
    async def entity_tool(
        entity_type: str,
        operation: Optional[str] = None,  # Now optional - can be inferred
        data: Optional[dict] = None,
        filters: Optional[dict] = None,
        entity_id: Optional[str] = None,
        include_relations: bool = False,
        batch: Optional[list] = None,
        search_term: Optional[str] = None,
        parent_type: Optional[str] = None,
        parent_id: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[str] = None,
        soft_delete: bool = True,
        format_type: str = "detailed",
        pagination: Optional[dict] = None,
        filter_list: Optional[list] = None,
        sort_list: Optional[list] = None,
        include_archived: bool = False,
    ) -> dict:
        """Unified CRUD operations with smart parameter inference and fuzzy matching.

        Operations (optional - auto-inferred from parameters):
        - create: Inferred when only `data` provided
        - read: Inferred when only `entity_id` provided
        - update: Inferred when both `entity_id` and `data` provided
        - delete: Must be explicit or inferred from soft_delete=True
        - search: Inferred when `search_term` provided
        - list: Inferred when `parent_type`/`parent_id` provided or no other params

        Entity ID Fuzzy Matching:
        - Accept entity names instead of UUIDs: entity_id="Vehicle Project"
        - Partial matches work: entity_id="Vehicle"
        - Auto-selects best match (70%+ similarity)
        - Returns suggestions if ambiguous

        Examples:
        - Read by name: entity_type="project", entity_id="Vehicle" (auto-resolves to UUID)
        - Create: entity_type="project", data={"name": "My Project"} (operation inferred)
        - Update: entity_type="document", entity_id="MCP Test", data={"description": "..."} (both inferred + resolved)
        - List: entity_type="document", parent_type="project", parent_id="Vehicle Project" (fuzzy parent resolution)
        """
        try:
            auth_token = await _apply_rate_limit_if_configured()

            # Backwards-compatible param aliases used by tests/older clients
            # Map `entities` -> `batch` for batch_create
            if batch is None:
                # Some FastMCP clients might pass extra kwargs; guard via attributes on filters/data
                # No-op here; alias handled by tool signature only
                pass

            # FastMCP validates signature strictly; emulate alias support via operation inference
            # If operation is batch_create and data-like list is provided via invalid name, accept it
            # We can’t capture unknown kwargs directly, so infer from typical patterns when possible
            if operation == "batch_create" and batch is None and isinstance(data, list):
                # If user mistakenly sent list in `data`, treat as batch
                batch = data  # type: ignore[assignment]
                data = None

            # Smart operation inference
            if not operation:
                if data and not entity_id:
                    operation = "create"
                elif entity_id and data:
                    operation = "update"
                elif entity_id:
                    operation = "read"
                elif search_term:
                    operation = "search"
                elif parent_type or parent_id:
                    operation = "list"
                else:
                    operation = "list"  # Default to list
            # Apply default limit to prevent oversized responses
            if operation == "list" and limit is None:
                limit = 100

            # Support legacy/alias values for format argument (tests may send `format`)
            # The signature already exposes `format_type`; nothing to do if already set
            if format_type not in ("detailed", "summary"):
                # Normalize unexpected values to detailed
                format_type = "detailed"

            # Normalize batch_create op name to create with batch populated
            if operation == "batch_create":
                operation = "create"

            return await entity_operation(  # type: ignore[no-any-return]
                auth_token=auth_token,
                operation=operation,
                entity_type=entity_type,
                data=data,
                filters=filters,
                entity_id=entity_id,
                include_relations=include_relations,
                batch=batch,
                search_term=search_term,
                parent_type=parent_type,
                parent_id=parent_id,
                limit=limit,
                offset=offset,
                order_by=order_by,
                soft_delete=soft_delete,
                format_type=format_type,
                pagination=pagination,
                filter_list=filter_list,
                sort_list=sort_list,
            )
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "operation": operation,
                "entity_type": entity_type,
            }

    @mcp.tool(tags={"relationship", "association"})
    async def relationship_tool(
        operation: str,
        relationship_type: str,
        source: dict,
        target: Optional[dict] = None,
        metadata: Optional[dict] = None,
        filters: Optional[dict] = None,
        source_context: Optional[str] = None,
        soft_delete: bool = True,
        limit: Optional[int] = 100,
        offset: Optional[int] = 0,
        format_type: str = "detailed",
    ) -> dict:
        """Manage relationships between entities.

        Operations:
        - link: Create relationship between entities
        - unlink: Remove relationship
        - list: List relationships
        - check: Check if relationship exists
        - update: Update relationship metadata

        Relationship types:
        - member: Organization/project members
        - assignment: Task assignments
        - trace_link: Requirement traceability
        - requirement_test: Test coverage
        - invitation: Organization invitations

        Examples:
        - Add member: operation="link", relationship_type="member",
          source={"type": "organization", "id": "org_123"},
          target={"type": "user", "id": "user_456"},
          metadata={"role": "admin"}
        - List members: operation="list", relationship_type="member",
          source={"type": "project", "id": "proj_123"}
        """
        try:
            auth_token = await _apply_rate_limit_if_configured()
            return await relationship_operation(  # type: ignore[no-any-return]
                auth_token=auth_token,
                operation=operation,
                relationship_type=relationship_type,
                source=source,
                target=target,
                metadata=metadata,
                filters=filters,
                source_context=source_context,
                soft_delete=soft_delete,
                limit=limit,
                offset=offset,
                format_type=format_type,
            )
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "operation": operation,
                "relationship_type": relationship_type,
            }

    @mcp.tool(tags={"workflow", "automation"})
    async def workflow_tool(
        workflow: str,
        parameters: dict,
        transaction_mode: bool = True,
        format_type: str = "detailed",
    ) -> dict:
        """Execute complex multi-step workflows.

        Available workflows:
        - setup_project: Create project with initial structure
        - import_requirements: Import requirements from external source
        - setup_test_matrix: Set up test matrix for a project
        - bulk_status_update: Update status for multiple entities
        - organization_onboarding: Complete organization setup

        Examples:
        - Setup project: workflow="setup_project", parameters={"name": "My Project", "organization_id": "org_123", "initial_documents": ["Requirements", "Design"]}
        - Import requirements: workflow="import_requirements", parameters={"document_id": "doc_123", "requirements": [{"name": "REQ-1", "description": "..."}]}
        - Bulk update: workflow="bulk_status_update", parameters={"entity_type": "requirement", "entity_ids": ["req_1", "req_2"], "new_status": "approved"}
        """
        try:
            auth_token = await _apply_rate_limit_if_configured()
            return await workflow_execute(  # type: ignore[no-any-return]
                auth_token=auth_token,
                workflow=workflow,
                parameters=parameters,
                transaction_mode=transaction_mode,
                format_type=format_type,
            )
        except Exception as e:
            return {"success": False, "error": str(e), "workflow": workflow}

    # OAuth 2.0 endpoints are now handled automatically by FastMCP AuthKitProvider
    # No need for custom OAuth endpoints - they're built into FastMCP

    @mcp.tool(tags={"query", "analysis", "rag"})
    async def query_tool(
        query_type: str,
        entities: list,
        conditions: Optional[dict] = None,
        projections: Optional[list] = None,
        search_term: Optional[str] = None,
        limit: Optional[int] = None,
        format_type: str = "detailed",
        # RAG-specific parameters
        rag_mode: str = "auto",
        similarity_threshold: float = 0.7,
        content: Optional[str] = None,
        entity_type: Optional[str] = None,
        exclude_id: Optional[str] = None,
    ) -> dict:
        """Query and analyze data across multiple entity types with RAG capabilities.

        Query types:
        - search: Cross-entity text search
        - aggregate: Summary statistics and counts
        - analyze: Deep analysis with relationships
        - relationships: Relationship analysis
        - rag_search: AI-powered semantic search with Vertex AI embeddings
        - similarity: Find content similar to provided text

        RAG modes (for rag_search):
        - auto: Automatically choose best mode based on query
        - semantic: Vector similarity search using embeddings
        - keyword: Traditional keyword-based search
        - hybrid: Combination of semantic and keyword search

        Examples:
        - Traditional search: query_type="search", entities=["project", "document"], search_term="api"
        - Semantic search: query_type="rag_search", entities=["requirement"], search_term="user authentication flow", rag_mode="semantic"
        - Find similar content: query_type="similarity", content="Login system requirements", entity_type="requirement"
        - Hybrid search: query_type="rag_search", entities=["document"], search_term="performance", rag_mode="hybrid"
        - Get statistics: query_type="aggregate", entities=["organization", "project"]
        """
        try:
            auth_token = await _apply_rate_limit_if_configured()
            return await data_query(  # type: ignore[no-any-return]
                auth_token=auth_token,
                query_type=query_type,
                entities=entities,
                conditions=conditions,
                projections=projections,
                search_term=search_term,
                limit=limit,
                format_type=format_type,
                rag_mode=rag_mode,
                similarity_threshold=similarity_threshold,
                content=content,
                entity_type=entity_type,
                exclude_id=exclude_id,
            )
        except Exception as e:
            return {"success": False, "error": str(e), "query_type": query_type}

    @mcp.tool(tags={"system", "health", "monitoring"})
    async def health_check() -> dict:
        """Comprehensive system health check.

        Returns status of all system components including:
        - Database connectivity and performance
        - Authentication service
        - Cache status
        - Performance metrics
        - Error statistics
        - Rate limiter status

        Returns:
            Dict with overall status and component details
        """
        try:
            from infrastructure.health import get_health_checker

            health_checker = get_health_checker()
            result = await health_checker.comprehensive_check()

            return {
                "success": True,
                **result
            }
        except Exception as e:
            return {
                "success": False,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    # OAuth endpoints are now handled automatically by FastMCP's native AuthKitProvider
    # No need for custom OAuth endpoints - FastMCP generates them automatically:
    # - /.well-known/oauth-protected-resource
    # - /.well-known/oauth-authorization-server
    # - /auth/start
    # - /auth/complete

    logger.info("✅ Server created - FastMCP handles OAuth endpoints and session management automatically")
    
    # Log tool registration status (tools are registered via decorators above)
    # FastMCP automatically exposes tools via the MCP protocol
    logger.info("✅ Tools registered via @mcp.tool decorators:")
    logger.info("   - workspace_tool (workspace, context)")
    logger.info("   - entity_tool (entity, crud)")
    logger.info("   - relationship_tool (relationship, association)")
    logger.info("   - workflow_tool (workflow, automation)")
    logger.info("   - query_tool (query, analysis, rag)")
    logger.info("   - health_check (system, health, monitoring)")

    return mcp


def main() -> None:
    """CLI runner for the consolidated server."""
    # Load env files early
    _load_env_files()

    # Debug environment loading in main()
    fastmcp_vars = {k: v for k, v in os.environ.items() if "FASTMCP" in k}
    print(f"🚀 MAIN DEBUG: FASTMCP environment variables: {fastmcp_vars}")
    print(f"🚀 MAIN DEBUG: Current working directory: {os.getcwd()}")
    print(f"🚀 MAIN DEBUG: .env file exists: {os.path.exists('.env')}")

    transport = os.getenv("ATOMS_FASTMCP_TRANSPORT", "stdio")
    host = os.getenv("ATOMS_FASTMCP_HOST", "127.0.0.1")
    port_str = os.getenv("ATOMS_FASTMCP_PORT", "8000")

    try:
        port = int(port_str)
    except ValueError:
        port = 8000

    server = create_consolidated_server()

    if transport == "http":
        # Optional health check route
        @server.custom_route("/health", methods=["GET"])  # type: ignore[attr-defined]
        async def _health(_request: Any) -> Any:  # pragma: no cover
            from starlette.responses import PlainTextResponse

            return PlainTextResponse("OK")

        path = os.getenv("ATOMS_FASTMCP_HTTP_PATH", "/api/mcp")
        server.run(transport="http", host=host, port=port, path=path)
    else:
        server.run(transport="stdio")


if __name__ == "__main__":
    main()
