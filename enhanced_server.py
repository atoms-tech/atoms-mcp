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
    
    # Create auth provider with base URL
    base_url = os.getenv("ATOMS_FASTMCP_BASE_URL")
    if not base_url:
        # Construct from environment if not provided
        host = os.getenv("ATOMS_FASTMCP_HOST", "127.0.0.1")
        port = os.getenv("ATOMS_FASTMCP_PORT", "8000")
        transport = os.getenv("ATOMS_FASTMCP_TRANSPORT", "stdio")
        
        if transport == "http":
            base_url = f"http://{host}:{port}"
    
    # Choose auth provider based on configuration
    auth_mode = os.getenv("ATOMS_FASTMCP_AUTH_MODE", "oauth").lower()
    
    if auth_mode == "disabled":
        # No authentication - for development only
        auth_provider = None
        logger.warning("Authentication disabled - development mode only!")
    elif auth_mode == "oauth":
        # OAuth Proxy for full MCP OAuth 2.1 + DCR compatibility (recommended)
        from .auth.supabase_oauth_provider import create_supabase_oauth_provider
        auth_provider = create_supabase_oauth_provider(base_url=base_url)
        
        if auth_provider:
            logger.info("Using Supabase OAuth Proxy with full MCP OAuth 2.1 + DCR support")
        else:
            logger.warning("OAuth Proxy disabled - missing configuration (need SUPABASE_OAUTH_CLIENT_SECRET)")
            auth_provider = None
    elif auth_mode == "simple":
        # Simple Auth with /auth/login endpoint (alternative for testing)
        from .auth.simple_auth_provider import create_supabase_simple_auth_provider
        auth_provider = create_supabase_simple_auth_provider()
        
        if auth_provider:
            logger.info("Using Supabase Simple Auth with /auth/login endpoint")
        else:
            logger.warning("Simple Auth disabled - missing Supabase configuration")
            auth_provider = None
    elif auth_mode == "bearer":
        # Bearer Auth using Supabase auth/v1/user endpoint (for existing tokens)
        from .auth.supabase_bearer_provider import create_supabase_bearer_provider
        auth_provider = create_supabase_bearer_provider()
        
        if auth_provider:
            logger.info("Using Supabase Bearer Auth with auth/v1/user validation")
        else:
            logger.warning("Bearer Auth disabled - missing Supabase configuration")
            auth_provider = None
    elif auth_mode == "jwt":
        # JWT verification with Supabase JWKS (alternative approach)
        auth_provider = create_supabase_jwt_verifier(
            base_url=base_url,
            required_scopes=None
        )
        
        if auth_provider:
            logger.info("Using Supabase JWT verification with JWKS")
        else:
            logger.warning("JWT Auth disabled - no Supabase configuration found")
            auth_provider = None
    else:
        logger.error(f"Unknown auth mode: {auth_mode}. Use 'oauth', 'simple', 'bearer', 'jwt', or 'disabled'")
        auth_provider = None
    
    # Create FastMCP server with auth
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
        auth=auth_provider
    )
    
    # Setup auth routes if using simple auth  
    if auth_mode == "simple" and auth_provider:
        # Setup routes synchronously during server creation
        auth_provider.setup_routes_sync(mcp)
    
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
        - rag_search: AI-powered semantic search with OpenAI embeddings
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
    
    return mcp


def main() -> None:
    """CLI runner for the consolidated server."""
    # Load env files early
    _load_env_files()
    
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