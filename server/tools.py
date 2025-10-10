"""
MCP tool registration and wrappers.

This module provides functions to register MCP tools with the FastMCP server,
including rate limiting and error handling.

Pythonic Patterns Applied:
- Type hints throughout
- Decorator pattern for tool wrapping
- Dependency injection for rate limiter
- Async context managers for rate limiting
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastmcp import FastMCP

from .auth import RateLimiter, apply_rate_limit_if_configured, get_token_string


def register_workspace_tool(
    mcp: FastMCP,
    workspace_operation: Callable,
    rate_limiter: RateLimiter | None = None
) -> None:
    """Register workspace management tool.

    Args:
        mcp: FastMCP server instance
        workspace_operation: Workspace operation function
        rate_limiter: Optional rate limiter
    """
    @mcp.tool(tags={"workspace", "context"})
    async def workspace_tool(
        operation: str,
        context_type: str | None = None,
        entity_id: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        format_type: str = "detailed",
        organization_id: str | None = None,
        project_id: str | None = None,
        type: str | None = None,
        id: str | None = None,
    ) -> dict[str, Any]:
        """Manage workspace context and get smart defaults.

        Operations:
        - get_context: Get current workspace context
        - set_context: Set active organization/project/document
        - list_workspaces: List available workspaces
        - get_defaults: Get smart default values for operations

        Context Hierarchy Parameters (for set_context):
        - organization_id: Optional organization context (for project/document operations)
        - project_id: Optional project context (for document operations)

        Backward Compatibility:
        - type: Alias for context_type (deprecated, use context_type)
        - id: Alias for entity_id (deprecated, use entity_id)

        Examples:
        - Set active project: operation="set_context", context_type="project", entity_id="proj_123"
        - Set project with org: operation="set_context", context_type="project", entity_id="proj_123", organization_id="org_456"
        - Set document with hierarchy: operation="set_context", context_type="document", entity_id="doc_123", project_id="proj_456", organization_id="org_789"
        - Get current context: operation="get_context"
        - List organizations: operation="list_workspaces"
        """
        try:
            bearer_token = await apply_rate_limit_if_configured(rate_limiter)
            auth_token = get_token_string(bearer_token)

            # Support backward compatibility: type -> context_type, id -> entity_id
            final_context_type = context_type or type
            final_entity_id = entity_id or id

            return await workspace_operation(
                auth_token=auth_token,
                operation=operation,
                context_type=final_context_type,
                entity_id=final_entity_id,
                limit=limit,
                offset=offset,
                format_type=format_type,
                organization_id=organization_id,
                project_id=project_id,
            )
        except Exception as e:
            return {"success": False, "error": str(e), "operation": operation}


def register_entity_tool(
    mcp: FastMCP,
    entity_operation: Callable,
    rate_limiter: RateLimiter | None = None
) -> None:
    """Register entity CRUD tool.

    Args:
        mcp: FastMCP server instance
        entity_operation: Entity operation function
        rate_limiter: Optional rate limiter
    """
    @mcp.tool(tags={"entity", "crud"})
    async def entity_tool(
        entity_type: str,
        operation: str | None = None,
        data: dict[str, Any] | None = None,
        filters: dict[str, Any] | None = None,
        entity_id: str | None = None,
        include_relations: bool = False,
        batch: list | None = None,
        search_term: str | None = None,
        parent_type: str | None = None,
        parent_id: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        order_by: str | None = None,
        soft_delete: bool = True,
        format_type: str = "detailed",
    ) -> dict[str, Any]:
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
        - Read by name: entity_type="project", entity_id="Vehicle"
        - Create: entity_type="project", data={"name": "My Project"}
        - Update: entity_type="document", entity_id="MCP Test", data={"description": "..."}
        - List: entity_type="document", parent_type="project", parent_id="Vehicle Project"
        """
        try:
            bearer_token = await apply_rate_limit_if_configured(rate_limiter)
            auth_token = get_token_string(bearer_token)

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
                    operation = "list"

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


def register_relationship_tool(
    mcp: FastMCP,
    relationship_operation: Callable,
    rate_limiter: RateLimiter | None = None
) -> None:
    """Register relationship management tool.

    Args:
        mcp: FastMCP server instance
        relationship_operation: Relationship operation function
        rate_limiter: Optional rate limiter
    """
    @mcp.tool(tags={"relationship", "association"})
    async def relationship_tool(
        operation: str,
        relationship_type: str,
        source: dict[str, Any],
        target: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        filters: dict[str, Any] | None = None,
        source_context: str | None = None,
        soft_delete: bool = True,
        limit: int | None = 100,
        offset: int | None = 0,
        format_type: str = "detailed",
    ) -> dict[str, Any]:
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
            bearer_token = await apply_rate_limit_if_configured(rate_limiter)
            auth_token = get_token_string(bearer_token)

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


def register_workflow_tool(
    mcp: FastMCP,
    workflow_execute: Callable,
    rate_limiter: RateLimiter | None = None
) -> None:
    """Register workflow execution tool.

    Args:
        mcp: FastMCP server instance
        workflow_execute: Workflow execution function
        rate_limiter: Optional rate limiter
    """
    @mcp.tool(tags={"workflow", "automation"})
    async def workflow_tool(
        workflow: str,
        parameters: dict[str, Any],
        transaction_mode: bool = True,
        format_type: str = "detailed",
    ) -> dict[str, Any]:
        """Execute complex multi-step workflows.

        Available workflows:
        - setup_project: Create project with initial structure
        - import_requirements: Import requirements from external source
        - setup_test_matrix: Set up test matrix for a project
        - bulk_status_update: Update status for multiple entities
        - organization_onboarding: Complete organization setup

        Examples:
        - Setup project: workflow="setup_project",
          parameters={"name": "My Project", "organization_id": "org_123"}
        - Import requirements: workflow="import_requirements",
          parameters={"document_id": "doc_123", "requirements": [...]}
        - Bulk update: workflow="bulk_status_update",
          parameters={"entity_type": "requirement", "entity_ids": [...], "new_status": "approved"}
        """
        try:
            bearer_token = await apply_rate_limit_if_configured(rate_limiter)
            auth_token = get_token_string(bearer_token)

            return await workflow_execute(
                auth_token=auth_token,
                workflow=workflow,
                parameters=parameters,
                transaction_mode=transaction_mode,
                format_type=format_type,
            )
        except Exception as e:
            return {"success": False, "error": str(e), "workflow": workflow}


def register_query_tool(
    mcp: FastMCP,
    data_query: Callable,
    rate_limiter: RateLimiter | None = None
) -> None:
    """Register data query and analysis tool.

    Args:
        mcp: FastMCP server instance
        data_query: Data query function
        rate_limiter: Optional rate limiter
    """
    @mcp.tool(tags={"query", "analysis", "rag"})
    async def query_tool(
        query_type: str,
        entities: list,
        conditions: dict[str, Any] | None = None,
        projections: list | None = None,
        search_term: str | None = None,
        limit: int | None = None,
        format_type: str = "detailed",
        # RAG-specific parameters
        rag_mode: str = "auto",
        similarity_threshold: float = 0.7,
        content: str | None = None,
        entity_type: str | None = None,
        exclude_id: str | None = None,
    ) -> dict[str, Any]:
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
        - Semantic search: query_type="rag_search", entities=["requirement"],
          search_term="user authentication flow", rag_mode="semantic"
        - Find similar: query_type="similarity", content="Login system requirements",
          entity_type="requirement"
        - Hybrid search: query_type="rag_search", entities=["document"],
          search_term="performance", rag_mode="hybrid"
        """
        try:
            bearer_token = await apply_rate_limit_if_configured(rate_limiter)
            auth_token = get_token_string(bearer_token)

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


__all__ = [
    "register_entity_tool",
    "register_query_tool",
    "register_relationship_tool",
    "register_workflow_tool",
    "register_workspace_tool",
]

