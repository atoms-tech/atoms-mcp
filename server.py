"""New atoms_fastmcp server with consolidated, agent-optimized tools."""

from __future__ import annotations

import os
import logging
import secrets
from dataclasses import dataclass
from typing import Any, Dict, Optional

from fastmcp import FastMCP
from .auth.supabase_provider import create_supabase_jwt_verifier
from .supabase_client import get_supabase, MissingSupabaseConfig
from .infrastructure.factory import get_adapter_factory
from .tools import (
    workspace_operation,
    entity_operation,
    relationship_operation,
    workflow_execute,
    data_query
)

logger = logging.getLogger("atoms_fastmcp")


# Global auth adapter (shared with tools via factory)
def get_auth_adapter():
    """Get the same auth adapter instance used by tools."""
    return get_adapter_factory().get_auth_adapter()


def _verify_credentials(username: str, password: str) -> Optional[dict]:
    """
    Authentication for development mode using direct credential passing.

    This is the WORKING authentication method until OAuth2/PKCE prod flow is implemented.

    Current behavior:
    - If FASTMCP_DEMO_USER and FASTMCP_DEMO_PASS env vars are set, verify against them.
    - Otherwise performs real Supabase authentication via sign_in_with_password()
    - Falls back to accepting any credentials only when Supabase is unavailable.
    """
    env_user = os.getenv("FASTMCP_DEMO_USER")
    env_pass = os.getenv("FASTMCP_DEMO_PASS")

    if env_user is not None and env_pass is not None:
        if username == env_user and password == env_pass:
            return {"id": f"user_{username}", "username": username}
        return None

    # Try real Supabase auth first if configured
    try:
        supabase = get_supabase()
        # We expect username to be an email for Supabase auth
        auth_res = supabase.auth.sign_in_with_password({
            "email": username,
            "password": password,
        })
        user = getattr(auth_res, "user", None)
        if user and getattr(user, "id", None):
            return {"id": user.id, "username": username}
        # If we get here, Supabase auth failed with invalid credentials
        return None
    except MissingSupabaseConfig:
        # Only fall back to dev mode if explicitly enabled
        if os.getenv("ATOMS_FASTMCP_DEV_MODE") == "true":
            if username and password:
                return {"id": f"user_{username}", "username": username}
        return None
    except Exception:
        # Authentication failed - return None to indicate invalid credentials
        return None


async def _require_session(session_token: str) -> Dict[str, Any]:
    """Validate session token and return user info or raise error."""
    try:
        auth_adapter = get_auth_adapter()
        user_info = await auth_adapter.validate_token(session_token)
        return user_info
    except Exception:
        raise ValueError("Invalid or expired session_token. Please login again.")


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
            merged.update({k: v for k, v in (dotenv_values(".env") or {}).items() if v is not None})
        except Exception as e:
            logger.warning(f"Failed loading .env: {e}")
    if os.path.exists(".env.local"):
        try:
            local_vals = {k: v for k, v in (dotenv_values(".env.local") or {}).items() if v is not None}
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
    logger.info(f"🔍 DEBUG: FASTMCP environment variables after loading .env: {fastmcp_vars}")

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
    logger.info(f"Resolved base URL for AuthKit/public metadata: {base_url}")
    print(f"🌐 AUTH BASE URL -> {base_url}")

    # Manually configure AuthKit provider + add discovery endpoints for MCP client compatibility
    fastmcp_vars = {k: v for k, v in os.environ.items() if "FASTMCP" in k}
    logger.info(f"DEBUG: All FASTMCP environment variables: {fastmcp_vars}")

    public_base_url = os.getenv("ATOMS_FASTMCP_PUBLIC_BASE_URL") or base_url

    # Create AuthKit provider manually (works reliably) but default to optional HTTP auth
    auth_provider = None
    try:
        from fastmcp.server.auth.providers.workos import AuthKitProvider

        authkit_domain = os.getenv("FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN")
        base_url_auth = os.getenv(
            "FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL",
            base_url or "http://127.0.0.1:8000",
        )

        if authkit_domain:
            auth_provider = AuthKitProvider(
                authkit_domain=authkit_domain,
                base_url=base_url_auth,
                required_scopes=["openid", "profile", "email"],
            )
            logger.info(f"✅ AuthKit provider configured: {authkit_domain}")
            print(f"✅ AuthKit provider configured: {authkit_domain}")
        else:
            logger.warning("❌ AuthKit domain not found in environment variables")
            print("❌ AuthKit domain not found in environment variables")
    except Exception as e:
        logger.error(f"❌ Failed to create AuthKit provider: {e}")
        print(f"❌ Failed to create AuthKit provider: {e}")
        auth_provider = None

    # Allow opting into strict HTTP auth only when explicitly requested. This keeps
    # the development login(session_token) flow working by default while still
    # letting production deployments enforce OAuth by setting the env var below.
    allow_unauth = os.getenv("FASTMCP_ALLOW_UNAUTH", "").lower() in {"1", "true", "yes", "on"}
    http_auth_mode_env = os.getenv("ATOMS_FASTMCP_HTTP_AUTH_MODE")
    if http_auth_mode_env:
        http_auth_mode = http_auth_mode_env.lower()
    elif os.getenv("ENV", "dev").lower() in {"prod", "production"}:
        http_auth_mode = "required"
    else:
        http_auth_mode = "optional" if allow_unauth else "required"
    logger.info(
        "HTTP auth configuration -> mode=%s allow_unauth=%s env=%s",
        http_auth_mode,
        allow_unauth,
        os.getenv("ENV", "dev"),
    )
    print(
        f"🔐 HTTP AUTH MODE -> {http_auth_mode} (allow unauth={allow_unauth}, env={os.getenv('ENV', 'dev')})"
    )
    if http_auth_mode not in {"optional", "required"}:
        logger.warning(
            "Unknown ATOMS_FASTMCP_HTTP_AUTH_MODE=%s, defaulting to optional", http_auth_mode
        )
        http_auth_mode = "optional"

    if http_auth_mode != "required":
        if auth_provider is not None:
            logger.info(
                "🚧 HTTP auth via AuthKit disabled (ATOMS_FASTMCP_HTTP_AUTH_MODE=%s)",
                http_auth_mode,
            )
        auth_provider_for_server = None
    else:
        auth_provider_for_server = auth_provider

    # Create FastMCP server, defaulting to no HTTP auth to keep development login flow working
    mcp = FastMCP(
        name="atoms-fastmcp-consolidated",
        instructions=(
            "Atoms MCP server with consolidated, agent-optimized tools. "
            "First call login(username, password) to obtain a session_token. "
            "Include session_token in every subsequent tool call. "
            "Use workspace_tool to manage context, entity_tool for CRUD, "
            "relationship_tool for associations, workflow_tool for complex tasks, "
            "and query_tool for data exploration including RAG search."
        ),
        auth=auth_provider_for_server,
    )

    # Development mode authentication tools
    @mcp.tool(tags={"auth", "public"})
    async def login(username: str, password: str) -> dict:
        """Development mode authentication via direct credential passing.

        User provides credentials explicitly: "Use my email/pass: user@example.com/mypassword"
        Agent calls this tool to authenticate and get session_token for subsequent API calls.

        This is the WORKING authentication method until OAuth2/PKCE production flow is complete.

        Returns { success: bool, session_token?: str, user_id?: str, error?: str }
        """
        auth_adapter = get_auth_adapter()
        user = await auth_adapter.verify_credentials(username, password)
        if not user:
            return {"success": False, "error": "Invalid credentials"}
        token = await auth_adapter.create_session(user_id=user["id"], username=user["username"])
        return {"success": True, "session_token": token, "user_id": user["id"]}

    @mcp.tool(tags={"auth"})
    async def logout(session_token: str) -> dict:
        """Invalidate a session_token."""
        auth_adapter = get_auth_adapter()
        await auth_adapter.revoke_session(session_token)
        return {"success": True}

    # Register consolidated tools
    @mcp.tool(tags={"workspace", "context"})
    async def workspace_tool(
        session_token: str,
        operation: str,
        context_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        format_type: str = "detailed"
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
            # Validate session and get user info
            user_info = await _require_session(session_token)

            return await workspace_operation(
                auth_token=session_token,  # Pass session token as auth_token
                operation=operation,
                context_type=context_type,
                entity_id=entity_id,
                format_type=format_type
            )
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "operation": operation
            }

    @mcp.tool(tags={"entity", "crud"})
    async def entity_tool(
        session_token: str,
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
        format_type: str = "detailed"
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
            # Validate session and get user info
            user_info = await _require_session(session_token)

            return await entity_operation(
                auth_token=session_token,  # Pass session token as auth_token
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
                format_type=format_type
            )
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "operation": operation,
                "entity_type": entity_type
            }

    @mcp.tool(tags={"relationship", "association"})
    async def relationship_tool(
        session_token: str,
        operation: str,
        relationship_type: str,
        source: dict,
        target: Optional[dict] = None,
        metadata: Optional[dict] = None,
        filters: Optional[dict] = None,
        source_context: Optional[str] = None,
        soft_delete: bool = True,
        format_type: str = "detailed"
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
            # Validate session and get user info
            user_info = await _require_session(session_token)

            return await relationship_operation(
                auth_token=session_token,  # Pass session token as auth_token
                operation=operation,
                relationship_type=relationship_type,
                source=source,
                target=target,
                metadata=metadata,
                filters=filters,
                source_context=source_context,
                soft_delete=soft_delete,
                format_type=format_type
            )
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "operation": operation,
                "relationship_type": relationship_type
            }

    @mcp.tool(tags={"workflow", "automation"})
    async def workflow_tool(
        session_token: str,
        workflow: str,
        parameters: dict,
        transaction_mode: bool = True,
        format_type: str = "detailed"
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
            # Validate session and get user info
            user_info = await _require_session(session_token)

            return await workflow_execute(
                auth_token=session_token,  # Pass session token as auth_token
                workflow=workflow,
                parameters=parameters,
                transaction_mode=transaction_mode,
                format_type=format_type
            )
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "workflow": workflow
            }

    # OAuth 2.0 endpoints are now handled automatically by FastMCP AuthKitProvider
    # No need for custom OAuth endpoints - they're built into FastMCP

    @mcp.tool(tags={"query", "analysis", "rag"})
    async def query_tool(
        session_token: str,
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
        exclude_id: Optional[str] = None
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
            # Validate session and get user info
            user_info = await _require_session(session_token)

            return await data_query(
                auth_token=session_token,  # Pass session token as auth_token
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
                exclude_id=exclude_id
            )
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query_type": query_type
            }


    # Add OAuth discovery endpoints for MCP client compatibility (e.g., Augment)
    async def _build_oidc_metadata():
        authkit_domain = os.getenv("FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN")
        if not authkit_domain:
            return None

        issuer = authkit_domain.rstrip("/")
        return {
            "issuer": issuer,
            "authorization_endpoint": f"{issuer}/oauth/authorize",
            "token_endpoint": f"{issuer}/oauth/token",
            "userinfo_endpoint": f"{issuer}/oauth/userinfo",
            "jwks_uri": f"{issuer}/oauth/jwks",
            "registration_endpoint": f"{issuer}/oauth/register",
            "scopes_supported": ["openid", "profile", "email"],
            "response_types_supported": ["code"],
            "grant_types_supported": ["authorization_code", "refresh_token"],
            "subject_types_supported": ["public"],
            "id_token_signing_alg_values_supported": ["RS256"],
            "code_challenge_methods_supported": ["S256"],
            "token_endpoint_auth_methods_supported": ["client_secret_post", "client_secret_basic"],
        }

    def _set_cors_headers(resp):
        try:
            resp.headers.setdefault("Access-Control-Allow-Origin", "*")
            resp.headers.setdefault("Access-Control-Allow-Methods", "GET,OPTIONS")
            resp.headers.setdefault(
                "Access-Control-Allow-Headers",
                "Authorization, Content-Type, MCP-Protocol-Version"
            )
        except Exception:
            pass
        return resp

    async def _openid_configuration_handler(request):
        from starlette.responses import JSONResponse, Response

        if request.method == "OPTIONS":
            return _set_cors_headers(Response(status_code=204))

        metadata = await _build_oidc_metadata()
        if metadata is None:
            return _set_cors_headers(
                JSONResponse({"error": "OpenID configuration not available"}, status_code=404)
            )
        return _set_cors_headers(JSONResponse(metadata))

    async def _oauth_authorization_server_handler(request):
        from starlette.responses import JSONResponse, Response

        if request.method == "OPTIONS":
            return _set_cors_headers(Response(status_code=204))

        metadata = await _build_oidc_metadata()
        if metadata is None:
            return _set_cors_headers(
                JSONResponse(
                    {"error": "OAuth authorization server metadata not available"},
                    status_code=404,
                )
            )
        # Remove fields that are OIDC-only when serving OAuth AS metadata
        oauth_metadata = metadata.copy()
        oauth_metadata.pop("userinfo_endpoint", None)
        oauth_metadata.pop("id_token_signing_alg_values_supported", None)
        oauth_metadata.pop("subject_types_supported", None)
        return _set_cors_headers(JSONResponse(oauth_metadata))

    async def _build_resource_metadata(request=None):
        authkit_domain = os.getenv("FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN")
        resource_path = os.getenv("ATOMS_FASTMCP_HTTP_PATH", "/api/mcp")

        request_base = None
        if request is not None:
            try:
                request_base = str(request.base_url).rstrip("/")
            except Exception:
                request_base = None

        resource_base = request_base or (public_base_url or base_url or "http://127.0.0.1:8000").rstrip("/")
        if resource_base.endswith(resource_path):
            resource_base = resource_base[: -len(resource_path)]
        resource_url = resource_base.rstrip("/") + resource_path

        metadata: Dict[str, Any] = {
            "resource": resource_url,
            "scopes_supported": ["openid", "profile", "email"],
            "token_endpoint_auth_methods_supported": [
                "client_secret_post",
                "client_secret_basic",
            ],
        }

        if authkit_domain:
            metadata["authorization_servers"] = [authkit_domain.rstrip("/")]

        return metadata

    async def _oauth_protected_resource_handler(request):
        from starlette.responses import JSONResponse, Response

        if request.method == "OPTIONS":
            return _set_cors_headers(Response(status_code=204))

        metadata = await _build_resource_metadata(request)
        return _set_cors_headers(JSONResponse(metadata))

    # Register discovery endpoints with a few aliases that some clients request
    for path in (
        "/.well-known/openid-configuration",
        "/api/mcp/.well-known/openid-configuration",
        "/.well-known/openid-configuration/api/mcp",
        "/.well-known/openid-configurationapi/mcp",
    ):
        mcp.custom_route(path, methods=["GET", "OPTIONS"])(_openid_configuration_handler)

    for path in (
        "/.well-known/oauth-authorization-server",
        "/api/mcp/.well-known/oauth-authorization-server",
        "/.well-known/oauth-authorization-server/api/mcp",
        "/.well-known/oauth-authorization-serverapi/mcp",
    ):
        mcp.custom_route(path, methods=["GET", "OPTIONS"])(_oauth_authorization_server_handler)

    for path in (
        "/.well-known/oauth-protected-resource",
        "/api/mcp/.well-known/oauth-protected-resource",
        "/.well-known/oauth-protected-resource/api/mcp",
        "/.well-known/oauth-protected-resourceapi/mcp",
    ):
        mcp.custom_route(path, methods=["GET", "OPTIONS"])(_oauth_protected_resource_handler)


        # Standalone Connect endpoints: Login UI and completion handler
        async def _auth_login_handler(request):
            from starlette.responses import HTMLResponse
            # Render minimal login form that preserves external_auth_id
            try:
                ext = request.query_params.get("external_auth_id")
            except Exception:
                ext = None
            html = f"""
            <!doctype html>
            <html><head><meta charset='utf-8'><title>Sign in</title></head>
            <body>
              <h2>Sign in</h2>
              {'<p style=\"color:red\">Missing external_auth_id</p>' if not ext else ''}
              <form method="post" action="/auth/complete">
                <input type="hidden" name="external_auth_id" value="{ext or ''}" />
                <label>Email <input name="email" type="email" required /></label><br/>
                <label>Password <input name="password" type="password" required /></label><br/>
                <button type="submit">Continue</button>
              </form>
            </body>
            </html>
            """
            return HTMLResponse(html)

        async def _auth_complete_handler(request):
            import os
            import aiohttp
            from starlette.responses import JSONResponse, RedirectResponse
            # Accept either form-encoded or JSON body
            try:
                content_type = request.headers.get("content-type", "")
                if "application/json" in content_type.lower():
                    data = await request.json()
                else:
                    data = await request.form()
            except Exception:
                data = {}

            external_auth_id = (data.get("external_auth_id") if isinstance(data, dict) else None) or None
            email = (data.get("email") if isinstance(data, dict) else None) or None
            password = (data.get("password") if isinstance(data, dict) else None) or None

            if not external_auth_id:
                return JSONResponse({"error": "external_auth_id required"}, status_code=400)

            # Option A: Verify Supabase JWT from Authorization header
            auth_header = request.headers.get("authorization", "")
            bearer_token = None
            if auth_header.lower().startswith("bearer "):
                bearer_token = auth_header.split(" ", 1)[1].strip()

            verified_user_id = None
            verified_user_email = None

            if bearer_token:
                supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL") or os.getenv("SUPABASE_URL")
                if not supabase_url:
                    return JSONResponse({"error": "Supabase URL not configured"}, status_code=500)
                supabase_apikey = (
                    os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
                    or os.getenv("SUPABASE_ANON_KEY")
                    or os.getenv("SUPABASE_SERVICE_ROLE_SECRET")
                )
                if not supabase_apikey:
                    return JSONResponse({"error": "Supabase API key not configured (set NEXT_PUBLIC_SUPABASE_ANON_KEY or SUPABASE_ANON_KEY)"}, status_code=500)
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(
                            f"{supabase_url.rstrip('/')}/auth/v1/user",
                            headers={
                                "Authorization": f"Bearer {bearer_token}",
                                "apikey": supabase_apikey,
                            },
                        ) as resp:
                            user_json_text = await resp.text()
                            if resp.status != 200:
                                return JSONResponse({"error": "invalid_supabase_token", "status": resp.status, "body": user_json_text}, status_code=401)
                            try:
                                user_json = await resp.json()
                            except Exception:
                                return JSONResponse({"error": "invalid_supabase_user_response", "body": user_json_text}, status_code=502)
                            verified_user_id = user_json.get("id") or user_json.get("user", {}).get("id")
                            verified_user_email = user_json.get("email") or user_json.get("user", {}).get("email")
                except Exception as e:
                    return JSONResponse({"error": f"supabase_user_fetch_failed: {e}"}, status_code=502)

            # Option B: Fallback to email/password against Supabase (for direct /auth/login flow)
            if not verified_user_id:
                if not email or not password:
                    return JSONResponse({"error": "email and password required"}, status_code=400)
                try:
                    supabase = get_supabase()
                    auth_res = supabase.auth.sign_in_with_password({
                        "email": email,
                        "password": password,
                    })
                    user = getattr(auth_res, "user", None)
                    if not user or not getattr(user, "id", None):
                        return JSONResponse({"error": "invalid_credentials"}, status_code=401)
                    verified_user_id = user.id
                    verified_user_email = getattr(user, "email", email)
                except Exception as e:
                    return JSONResponse({"error": f"supabase_auth_failed: {e}"}, status_code=500)

            # Complete OAuth with AuthKit (WorkOS)
            workos_api_url = os.getenv("WORKOS_API_URL", "https://api.workos.com").rstrip("/")
            payload = {
                "external_auth_id": external_auth_id,
                "user": {
                    "id": verified_user_id,
                    "email": verified_user_email,
                },
            }
            headers = {
                "Authorization": f"Bearer {os.getenv('WORKOS_API_KEY', '')}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
            if not headers["Authorization"].strip():
                return JSONResponse({"error": "WORKOS_API_KEY not configured"}, status_code=500)

            # Debug (redacted) to help diagnose upstream failures
            try:
                key_len = len(os.getenv('WORKOS_API_KEY', ''))
                print(f"🔎 WORKOS complete call -> url={workos_api_url}/authkit/oauth2/complete key_len={key_len}")
            except Exception:
                pass

            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(f"{workos_api_url}/authkit/oauth2/complete", json=payload, headers=headers) as resp:
                        text = await resp.text()
                        if resp.status >= 400:
                            # Return 400 to avoid Cloudflare 502 HTML replacement and surface JSON/text to client
                            return JSONResponse({"error": "workos_complete_failed", "status": resp.status, "body": text}, status_code=400)
                        try:
                            data = await resp.json()
                        except Exception:
                            return JSONResponse({"error": "invalid_workos_response", "body": text}, status_code=400)
                        redirect_uri = data.get("redirect_uri")
                        if not redirect_uri:
                            return JSONResponse({"error": "missing_redirect_uri", "workos": data}, status_code=400)
                        return RedirectResponse(url=redirect_uri, status_code=302)
            except Exception as e:
                return JSONResponse({"error": f"workos_request_failed: {e}"}, status_code=400)

        # Register Standalone Connect routes
        mcp.custom_route("/auth/login", methods=["GET"])(_auth_login_handler)
        mcp.custom_route("/auth/complete", methods=["POST"])(_auth_complete_handler)

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
