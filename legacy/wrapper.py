"""Legacy wrapper that maps old tool calls to new consolidated tools."""

from __future__ import annotations

import logging
import warnings
from typing import Any, Dict, Optional

from fastmcp import FastMCP
from ..new_server import create_consolidated_server
from ..tools import entity_operation, relationship_operation, workflow_execute

logger = logging.getLogger("atoms_fastmcp.legacy")


class LegacyToolMapper:
    """Maps legacy tool calls to new consolidated tools."""
    
    def __init__(self):
        # Cache for the new tools
        self._new_server_tools = None
    
    def _get_new_tools(self):
        """Get reference to new consolidated tools."""
        if self._new_server_tools is None:
            # Import the tool functions directly
            from ..tools import (
                workspace_operation,
                entity_operation,
                relationship_operation,
                workflow_execute,
                data_query
            )
            self._new_server_tools = {
                "workspace": workspace_operation,
                "entity": entity_operation,
                "relationship": relationship_operation,
                "workflow": workflow_execute,
                "query": data_query
            }
        return self._new_server_tools
    
    def _warn_deprecated(self, old_tool: str, new_approach: str):
        """Issue deprecation warning."""
        warnings.warn(
            f"Tool '{old_tool}' is deprecated. Use {new_approach} instead.",
            DeprecationWarning,
            stacklevel=3
        )
    
    async def map_organizations_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Map organization-related tools to entity_operation."""
        tools = self._get_new_tools()
        
        if tool_name == "list_organizations":
            self._warn_deprecated(tool_name, "entity_operation with operation='list', entity_type='organization'")
            return await tools["entity"](
                auth_token=kwargs["session_token"],
                operation="list",
                entity_type="organization",
                parent_type=kwargs.get("parent_type"),
                parent_id=kwargs.get("user_id")
            )
        
        elif tool_name == "get_organization":
            self._warn_deprecated(tool_name, "entity_operation with operation='read'")
            return await tools["entity"](
                auth_token=kwargs["session_token"],
                operation="read",
                entity_type="organization",
                entity_id=kwargs["org_id"]
            )
        
        elif tool_name == "organizations_create":
            self._warn_deprecated(tool_name, "entity_operation with operation='create'")
            return await tools["entity"](
                auth_token=kwargs["session_token"],
                operation="create",
                entity_type="organization",
                data=kwargs["insert"]
            )
        
        elif tool_name == "organizations_list_members":
            self._warn_deprecated(tool_name, "relationship_operation with relationship_type='member'")
            return await tools["relationship"](
                auth_token=kwargs["session_token"],
                operation="list",
                relationship_type="member",
                source={"type": "organization", "id": kwargs["organization_id"]}
            )
        
        elif tool_name == "organizations_add_member":
            self._warn_deprecated(tool_name, "relationship_operation with operation='link'")
            return await tools["relationship"](
                auth_token=kwargs["session_token"],
                operation="link",
                relationship_type="member",
                source={"type": "organization", "id": kwargs["input"]["organization_id"]},
                target={"type": "user", "id": kwargs["input"]["user_id"]},
                metadata={"role": kwargs["input"].get("role", "member"), "status": "active"}
            )
        
        else:
            raise ValueError(f"Unknown legacy organization tool: {tool_name}")
    
    async def map_projects_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Map project-related tools to entity_operation."""
        tools = self._get_new_tools()
        
        if tool_name == "list_projects_by_org":
            self._warn_deprecated(tool_name, "entity_operation with parent filtering")
            return await tools["entity"](
                auth_token=kwargs["session_token"],
                operation="list",
                entity_type="project",
                parent_type="organization",
                parent_id=kwargs["organization_id"]
            )
        
        elif tool_name == "projects_create":
            self._warn_deprecated(tool_name, "entity_operation with operation='create'")
            return await tools["entity"](
                auth_token=kwargs["session_token"],
                operation="create",
                entity_type="project",
                data=kwargs["insert"]
            )
        
        elif tool_name == "projects_list_members":
            self._warn_deprecated(tool_name, "relationship_operation")
            return await tools["relationship"](
                auth_token=kwargs["session_token"],
                operation="list",
                relationship_type="member",
                source={"type": "project", "id": kwargs["project_id"]}
            )
        
        else:
            raise ValueError(f"Unknown legacy project tool: {tool_name}")
    
    async def map_documents_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Map document-related tools to entity_operation."""
        tools = self._get_new_tools()
        
        if tool_name == "list_documents":
            self._warn_deprecated(tool_name, "entity_operation with operation='list'")
            return await tools["entity"](
                auth_token=kwargs["session_token"],
                operation="list", 
                entity_type="document",
                parent_type="project" if kwargs.get("project_id") else None,
                parent_id=kwargs.get("project_id")
            )
        
        elif tool_name == "documents_create":
            self._warn_deprecated(tool_name, "entity_operation with operation='create'")
            return await tools["entity"](
                auth_token=kwargs["session_token"],
                operation="create",
                entity_type="document",
                data=kwargs["insert"]
            )
        
        else:
            raise ValueError(f"Unknown legacy document tool: {tool_name}")
    
    async def map_requirements_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Map requirement-related tools to entity_operation."""
        tools = self._get_new_tools()
        
        if tool_name == "list_requirements_by_document":
            self._warn_deprecated(tool_name, "entity_operation with parent filtering")
            return await tools["entity"](
                auth_token=kwargs["session_token"],
                operation="list",
                entity_type="requirement",
                parent_type="document",
                parent_id=kwargs["document_id"]
            )
        
        elif tool_name == "requirements_create":
            self._warn_deprecated(tool_name, "entity_operation with operation='create'")
            return await tools["entity"](
                auth_token=kwargs["session_token"],
                operation="create",
                entity_type="requirement",
                data=kwargs["input"]
            )
        
        else:
            raise ValueError(f"Unknown legacy requirement tool: {tool_name}")


def create_legacy_wrapper_server() -> FastMCP:
    """Create a server that provides legacy tools for backward compatibility."""
    
    # Create auth provider
    import os
    base_url = os.getenv("ATOMS_FASTMCP_BASE_URL")
    if not base_url:
        host = os.getenv("ATOMS_FASTMCP_HOST", "127.0.0.1")
        port = os.getenv("ATOMS_FASTMCP_PORT", "8000")
        transport = os.getenv("ATOMS_FASTMCP_TRANSPORT", "stdio")
        if transport == "http":
            base_url = f"http://{host}:{port}"
    
    from ..auth.supabase_provider import create_supabase_jwt_verifier
    auth_provider = create_supabase_jwt_verifier(base_url=base_url)
    
    # Create server with correct name and instructions
    from fastmcp import FastMCP
    server = FastMCP(
        name="atoms-fastmcp-legacy-compatible",
        instructions=(
            "Atoms MCP server with both new consolidated tools and legacy compatibility. "
            "Prefer using the new consolidated tools: workspace_tool, entity_tool, relationship_tool, "
            "workflow_tool, and query_tool. Legacy tools are deprecated and will be removed in future versions."
        ),
        auth=auth_provider
    )
    mapper = LegacyToolMapper()
    
    # First, add the new consolidated tools
    from ..tools import (
        workspace_operation,
        entity_operation,
        relationship_operation,
        workflow_execute,
        data_query
    )
    
    @server.tool(tags={"workspace", "context"})
    def workspace_tool(
        auth_token: str,
        operation: str,
        context_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        format_type: str = "detailed"
    ) -> dict:
        """Manage workspace context and get smart defaults."""
        import asyncio
        return asyncio.run(workspace_operation(
            auth_token=auth_token,
            operation=operation,
            context_type=context_type,
            entity_id=entity_id,
            format_type=format_type
        ))
    
    @server.tool(tags={"entity", "crud"})
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
        """Unified CRUD operations for any entity type."""
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
    
    @server.tool(tags={"relationship", "association"})
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
        """Manage relationships between entities."""
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
    
    @server.tool(tags={"workflow", "automation"})
    def workflow_tool(
        auth_token: str,
        workflow: str,
        parameters: dict,
        transaction_mode: bool = True,
        format_type: str = "detailed"
    ) -> dict:
        """Execute complex multi-step workflows."""
        import asyncio
        return asyncio.run(workflow_execute(
            auth_token=auth_token,
            workflow=workflow,
            parameters=parameters,
            transaction_mode=transaction_mode,
            format_type=format_type
        ))
    
    @server.tool(tags={"query", "analysis"})
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
        """Query and analyze data across multiple entity types."""
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
    
    # Now add the legacy organization tools
    @server.tool(tags={"legacy", "organizations"})
    def list_organizations(session_token: str, user_id: Optional[str] = None) -> dict:
        """DEPRECATED: Use entity_operation instead."""
        import asyncio
        return asyncio.run(mapper.map_organizations_tool(
            "list_organizations", session_token=session_token, user_id=user_id
        ))
    
    @server.tool(tags={"legacy", "organizations"})
    def get_organization(session_token: str, org_id: str) -> dict:
        """DEPRECATED: Use entity_operation instead."""
        import asyncio
        return asyncio.run(mapper.map_organizations_tool(
            "get_organization", session_token=session_token, org_id=org_id
        ))
    
    @server.tool(tags={"legacy", "organizations"})
    def organizations_create(session_token: str, insert: dict) -> dict:
        """DEPRECATED: Use entity_operation instead."""
        import asyncio
        return asyncio.run(mapper.map_organizations_tool(
            "organizations_create", session_token=session_token, insert=insert
        ))
    
    @server.tool(tags={"legacy", "organizations"})
    def organizations_list_members(session_token: str, organization_id: str) -> list:
        """DEPRECATED: Use relationship_operation instead."""
        import asyncio
        return asyncio.run(mapper.map_organizations_tool(
            "organizations_list_members", session_token=session_token, organization_id=organization_id
        ))
    
    @server.tool(tags={"legacy", "organizations"})
    def organizations_add_member(session_token: str, input: dict) -> dict:
        """DEPRECATED: Use relationship_operation instead."""
        import asyncio
        return asyncio.run(mapper.map_organizations_tool(
            "organizations_add_member", session_token=session_token, input=input
        ))
    
    # Add legacy project tools
    @server.tool(tags={"legacy", "projects"})
    def list_projects_by_org(session_token: str, organization_id: str) -> list:
        """DEPRECATED: Use entity_operation instead."""
        import asyncio
        return asyncio.run(mapper.map_projects_tool(
            "list_projects_by_org", session_token=session_token, organization_id=organization_id
        ))
    
    @server.tool(tags={"legacy", "projects"})
    def projects_create(session_token: str, insert: dict) -> dict:
        """DEPRECATED: Use entity_operation instead."""
        import asyncio
        return asyncio.run(mapper.map_projects_tool(
            "projects_create", session_token=session_token, insert=insert
        ))
    
    # Add legacy document tools
    @server.tool(tags={"legacy", "documents"})
    def list_documents(session_token: str, project_id: Optional[str] = None) -> list:
        """DEPRECATED: Use entity_operation instead."""
        import asyncio
        return asyncio.run(mapper.map_documents_tool(
            "list_documents", session_token=session_token, project_id=project_id
        ))
    
    @server.tool(tags={"legacy", "documents"})
    def documents_create(session_token: str, insert: dict) -> dict:
        """DEPRECATED: Use entity_operation instead."""
        import asyncio
        return asyncio.run(mapper.map_documents_tool(
            "documents_create", session_token=session_token, insert=insert
        ))
    
    # Add legacy requirement tools  
    @server.tool(tags={"legacy", "requirements"})
    def list_requirements_by_document(session_token: str, document_id: str) -> list:
        """DEPRECATED: Use entity_operation instead."""
        import asyncio
        return asyncio.run(mapper.map_requirements_tool(
            "list_requirements_by_document", session_token=session_token, document_id=document_id
        ))
    
    @server.tool(tags={"legacy", "requirements"})
    def requirements_create(session_token: str, input: dict) -> dict:
        """DEPRECATED: Use entity_operation instead."""
        import asyncio
        return asyncio.run(mapper.map_requirements_tool(
            "requirements_create", session_token=session_token, input=input
        ))
    
    # Note: Can't update server name after creation in FastMCP
    # The server instructions were set during creation
    
    return server