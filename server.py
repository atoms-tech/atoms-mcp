"""New atoms_fastmcp server with consolidated, agent-optimized tools."""

from __future__ import annotations

import os
import logging
import warnings
from typing import Any, Dict, Optional

# Suppress websockets deprecation warnings from uvicorn
warnings.filterwarnings("ignore", category=DeprecationWarning, module="websockets")

from fastmcp import FastMCP
from fastmcp.server.dependencies import get_access_token

# Support both relative and absolute imports
try:
    from .tools import (
        workspace_operation,
        entity_operation,
        relationship_operation,
        workflow_execute,
        data_query,
    )
except ImportError:
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
    """Return the bearer token from the FastMCP access token context.

    For persistent server deployment (Render/Railway/Fly.io), FastMCP's
    built-in OAuth handles sessions in-memory - no external persistence needed!
    """
    access_token = get_access_token()
    if not access_token:
        return None

    token = getattr(access_token, "token", None)
    if token:
        return token

    claims = getattr(access_token, "claims", None)
    if isinstance(claims, dict):
        for key in ("access_token", "session_token", "supabase_jwt", "supabase_token"):
            candidate = claims.get(key)
            if candidate:
                return candidate

    return None


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

    # Create auth provider with base URL, preferring public URLs configured for AuthKit/Cloudflare
    base_url = os.getenv("ATOMS_FASTMCP_BASE_URL")
    if not base_url:
        # Construct from environment if not provided
        host = os.getenv("ATOMS_FASTMCP_HOST", "127.0.0.1")
        port = os.getenv("ATOMS_FASTMCP_PORT", "8000")
        transport = os.getenv("ATOMS_FASTMCP_TRANSPORT", "stdio")

        if transport == "http":
            base_url = f"http://{host}:{port}"

    public_base_url = (
        os.getenv("ATOMS_FASTMCP_PUBLIC_BASE_URL")
        or os.getenv("FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL")
        or os.getenv("PUBLIC_URL")
    )
    if public_base_url:
        cleaned = public_base_url.rstrip("/")
        if cleaned.endswith("/api/mcp"):
            cleaned = cleaned[: -len("/api/mcp")]
        if cleaned.endswith("/mcp"):
            cleaned = cleaned[: -len("/mcp")]
        base_url = cleaned

    # Vercel-specific: use VERCEL_URL if no public URL is configured
    vercel_url = os.getenv("VERCEL_URL")
    if not public_base_url and vercel_url:
        guess = f"https://{vercel_url}".rstrip("/")
        # Strip /api/mcp suffix if present
        if guess.endswith("/api/mcp"):
            guess = guess[: -len("/api/mcp")]
        base_url = guess
        logger.info(f"Using VERCEL_URL for base URL: {base_url}")

    logger.info(f"Resolved base URL for AuthKit/public metadata: {base_url}")
    print(f"🌐 AUTH BASE URL -> {base_url}")

    # Manually configure AuthKit provider + add discovery endpoints for MCP client compatibility
    fastmcp_vars = {k: v for k, v in os.environ.items() if "FASTMCP" in k}
    logger.info(f"DEBUG: All FASTMCP environment variables: {fastmcp_vars}")

    public_base_url = os.getenv("ATOMS_FASTMCP_PUBLIC_BASE_URL") or base_url

    # Configure AuthKitProvider for OAuth with Standalone Connect
    authkit_domain = os.getenv("FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN")
    if not authkit_domain:
        raise ValueError("FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN required")

    from fastmcp.server.auth.providers.workos import AuthKitProvider

    auth_provider = AuthKitProvider(
        authkit_domain=authkit_domain,
        base_url=base_url,
        required_scopes=["openid", "profile", "email"],
    )
    logger.info(f"✅ AuthKitProvider configured: {authkit_domain}")
    print(f"✅ AuthKitProvider configured: {authkit_domain}")

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
        tool_serializer=_markdown_serializer,  # Custom Markdown output for better readability
    )

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
            auth_token = _extract_bearer_token()
            return await workspace_operation(
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
        operation: str,
        entity_type: str,
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
    ) -> dict:
        """Unified CRUD operations for any entity type.

        Operations:
        - create: Create new entity (requires data)
        - read: Get entity by ID (requires entity_id)
        - update: Update entity (requires entity_id and data)
        - delete: Delete entity (requires entity_id)
        - search: Search entities with filters
        - list: List entities, optionally by parent

        Entity types: organization, project, document, requirement, test, property, etc.

        Smart features:
        - Use "auto" for organization_id/project_id to use workspace context
        - Set include_relations=true for related data
        - Use batch for multiple operations

        Examples:
        - Create project: operation="create", entity_type="project", data={"name": "My Project", "organization_id": "auto"}
        - List requirements: operation="list", entity_type="requirement", parent_type="document", parent_id="doc_123"
        - Search projects: operation="search", entity_type="project", search_term="test"
        """
        try:
            auth_token = _extract_bearer_token()
            # Apply default limit to prevent oversized responses
            if operation == "list" and limit is None:
                limit = 100

            return await entity_operation(
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
            auth_token = _extract_bearer_token()
            return await relationship_operation(
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
            auth_token = _extract_bearer_token()
            return await workflow_execute(
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
            auth_token = _extract_bearer_token()
            return await data_query(
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

    # OAuth metadata endpoints for MCP client discovery
    async def _oauth_protected_resource_handler(request):
        from starlette.responses import JSONResponse
        authkit_domain = os.getenv("FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN")

        # Determine resource URL from request headers (for Vercel preview/custom domains)
        scheme = request.headers.get("x-forwarded-proto", "https")
        host = request.headers.get("x-forwarded-host") or request.headers.get("host")
        if host:
            resource = f"{scheme}://{host}"
        else:
            # Fallback to base_url
            resource = f"{base_url}"

        return JSONResponse({
            "resource": resource,
            "authorization_servers": [authkit_domain] if authkit_domain else [],
            "bearer_methods_supported": ["header"],
        })

    async def _oauth_authorization_server_handler(request):
        import httpx
        from starlette.responses import JSONResponse
        authkit_domain = os.getenv("FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN")
        if not authkit_domain:
            return JSONResponse({"error": "AuthKit not configured"}, status_code=404)

        # Proxy to AuthKit
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{authkit_domain}/.well-known/oauth-authorization-server")
            return JSONResponse(resp.json())

    mcp.custom_route("/.well-known/oauth-protected-resource", methods=["GET"])(_oauth_protected_resource_handler)
    mcp.custom_route("/.well-known/oauth-authorization-server", methods=["GET"])(_oauth_authorization_server_handler)

    # Standalone Connect endpoint for custom login page
    async def _auth_complete_handler(request):
        import aiohttp
        from starlette.responses import JSONResponse, Response
        import traceback

        # Handle OPTIONS for CORS
        if request.method == "OPTIONS":
            resp = Response(status_code=204)
            resp.headers["Access-Control-Allow-Origin"] = "*"
            resp.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
            resp.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
            return resp

        try:
            data = await request.json()
        except Exception as e:
            logger.error(f"Failed to parse request body: {e}")
            resp = JSONResponse({"error": "Invalid request body", "details": str(e)}, status_code=400)
            resp.headers["Access-Control-Allow-Origin"] = "*"
            return resp

        try:
            external_auth_id = data.get("external_auth_id")
            if not external_auth_id:
                resp = JSONResponse({"error": "external_auth_id required"}, status_code=400)
                resp.headers["Access-Control-Allow-Origin"] = "*"
                return resp

            # Get Supabase JWT from Authorization header
            auth_header = request.headers.get("authorization", "")
            if not auth_header.startswith("Bearer "):
                logger.error("Missing Bearer token in Authorization header")
                resp = JSONResponse({"error": "Authorization header required"}, status_code=401)
                resp.headers["Access-Control-Allow-Origin"] = "*"
                return resp

            bearer_token = auth_header.split(" ", 1)[1].strip()

            # Verify with Supabase
            supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL", "").strip().rstrip("/")
            supabase_key = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY", "").strip()

            if not supabase_url or not supabase_key:
                logger.error("Supabase env vars not configured")
                resp = JSONResponse({"error": "Supabase not configured"}, status_code=500)
                resp.headers["Access-Control-Allow-Origin"] = "*"
                return resp

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{supabase_url}/auth/v1/user",
                    headers={"Authorization": f"Bearer {bearer_token}", "apikey": supabase_key},
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        logger.error(f"Supabase verification failed ({resp.status}): {error_text}")
                        json_resp = JSONResponse({"error": "Invalid Supabase token", "details": error_text}, status_code=401)
                        json_resp.headers["Access-Control-Allow-Origin"] = "*"
                        return json_resp
                    user = await resp.json()

            # Complete OAuth with WorkOS
            workos_url = os.getenv("WORKOS_API_URL", "https://api.workos.com").strip().rstrip("/")
            workos_key = os.getenv("WORKOS_API_KEY", "").strip()

            if not workos_key:
                logger.error("WORKOS_API_KEY not configured")
                resp = JSONResponse({"error": "WorkOS not configured"}, status_code=500)
                resp.headers["Access-Control-Allow-Origin"] = "*"
                return resp

            logger.info(f"Completing WorkOS OAuth for user {user.get('email')}")
            logger.info(f"WorkOS API Key prefix: {workos_key[:15]}... (length: {len(workos_key)})")

            complete_url = f"{workos_url}/authkit/oauth2/complete"
            payload = {
                "external_auth_id": external_auth_id,
                "user": {"id": user["id"], "email": user["email"]},
            }
            logger.info(f"WorkOS request: POST {complete_url}")

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    complete_url,
                    json=payload,
                    headers={"Authorization": f"Bearer {workos_key}", "Content-Type": "application/json"},
                ) as resp:
                    if resp.status >= 400:
                        text = await resp.text()
                        logger.error(f"WorkOS completion failed ({resp.status}): {text}")
                        json_resp = JSONResponse({"error": "WorkOS failed", "status": resp.status, "body": text}, status_code=400)
                        json_resp.headers["Access-Control-Allow-Origin"] = "*"
                        return json_resp
                    result = await resp.json()

                    # Return success - OAuth session handled by FastMCP in-memory
                    json_resp = JSONResponse({
                        "success": True,
                        "redirect_uri": result["redirect_uri"]
                    })
                    json_resp.headers["Access-Control-Allow-Origin"] = "*"
                    return json_resp

        except Exception as e:
            logger.error(f"Unhandled exception in /auth/complete: {e}")
            logger.error(traceback.format_exc())
            resp = JSONResponse({
                "error": "Internal server error",
                "details": str(e),
                "type": type(e).__name__
            }, status_code=500)
            resp.headers["Access-Control-Allow-Origin"] = "*"
            return resp

    mcp.custom_route("/auth/complete", methods=["POST", "OPTIONS"])(_auth_complete_handler)
    mcp.custom_route("/api/mcp/auth/complete", methods=["POST", "OPTIONS"])(_auth_complete_handler)

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
        async def _health(_request):  # pragma: no cover
            from starlette.responses import PlainTextResponse

            return PlainTextResponse("OK")

        path = os.getenv("ATOMS_FASTMCP_HTTP_PATH", "/api/mcp")
        server.run(transport="http", host=host, port=port, path=path)
    else:
        server.run(transport="stdio")


if __name__ == "__main__":
    main()
