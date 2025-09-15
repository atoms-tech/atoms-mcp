"""New atoms_fastmcp server with consolidated, agent-optimized tools."""

from __future__ import annotations

import os
import logging
from typing import Any, Dict, Optional

from fastmcp import FastMCP
from .auth.supabase_provider import create_supabase_jwt_verifier
from .tools import (
    workspace_operation,
    entity_operation,
    relationship_operation,
    workflow_execute,
    data_query
)

logger = logging.getLogger("atoms_fastmcp")


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
            "Use workspace_operation to manage context, entity_operation for CRUD, "
            "relationship_operation for associations, workflow_execute for complex tasks, "
            "and data_query for exploration. All tools require auth_token parameter."
        ),
        auth=auth_provider
    )
    
    # Setup auth routes if using simple auth  
    if auth_mode == "simple" and auth_provider:
        # Setup routes synchronously during server creation
        auth_provider.setup_routes_sync(mcp)
    
    # Register consolidated tools
    @mcp.tool(tags={"workspace", "context"})
    def workspace_tool(
        auth_token: str,
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
        import asyncio
        return asyncio.run(workspace_operation(
            auth_token=auth_token,
            operation=operation,
            context_type=context_type,
            entity_id=entity_id,
            format_type=format_type
        ))
    
    @mcp.tool(tags={"entity", "crud"})
    def entity_tool(
        auth_token: str,
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
        import asyncio
        return asyncio.run(entity_operation(
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
            format_type=format_type
        ))
    
    @mcp.tool(tags={"relationship", "association"})
    def relationship_tool(
        auth_token: str,
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
        import asyncio
        return asyncio.run(relationship_operation(
            auth_token=auth_token,
            operation=operation,
            relationship_type=relationship_type,
            source=source,
            target=target,
            metadata=metadata,
            filters=filters,
            source_context=source_context,
            soft_delete=soft_delete,
            format_type=format_type
        ))
    
    @mcp.tool(tags={"workflow", "automation"})
    def workflow_tool(
        auth_token: str,
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
        import asyncio
        return asyncio.run(workflow_execute(
            auth_token=auth_token,
            workflow=workflow,
            parameters=parameters,
            transaction_mode=transaction_mode,
            format_type=format_type
        ))
    
    @mcp.tool(tags={"query", "analysis"})
    def query_tool(
        auth_token: str,
        query_type: str,
        entities: list,
        conditions: Optional[dict] = None,
        projections: Optional[list] = None,
        search_term: Optional[str] = None,
        limit: Optional[int] = None,
        format_type: str = "detailed"
    ) -> dict:
        """Query and analyze data across multiple entity types.
        
        Query types:
        - search: Cross-entity text search
        - aggregate: Summary statistics and counts
        - analyze: Deep analysis with relationships
        - relationships: Relationship analysis
        
        Examples:
        - Search across entities: query_type="search", entities=["project", "document"], search_term="api"
        - Get statistics: query_type="aggregate", entities=["organization", "project"]
        - Analyze requirements: query_type="analyze", entities=["requirement"], conditions={"status": "active"}
        - Relationship analysis: query_type="relationships", entities=["organization", "project"]
        """
        import asyncio
        return asyncio.run(data_query(
            auth_token=auth_token,
            query_type=query_type,
            entities=entities,
            conditions=conditions,
            projections=projections,
            search_term=search_term,
            limit=limit,
            format_type=format_type
        ))
    
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