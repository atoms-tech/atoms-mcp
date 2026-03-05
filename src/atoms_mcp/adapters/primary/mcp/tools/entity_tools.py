"""
MCP tools for entity operations.

This module defines FastMCP tools for creating, reading, updating,
and deleting entities.
"""

from typing import TYPE_CHECKING, Any, Optional

from fastmcp import Tool

from .....application.commands.entity_commands import (
    ArchiveEntityCommand,
    CreateEntityCommand,
    DeleteEntityCommand,
    RestoreEntityCommand,
    UpdateEntityCommand,
)
from .....application.queries.entity_queries import (
    CountEntitiesQuery,
    GetEntityQuery,
    ListEntitiesQuery,
    SearchEntitiesQuery,
)

if TYPE_CHECKING:
    from ..server import AtomsServer


def register_entity_tools(mcp: Any, server: "AtomsServer") -> None:
    """
    Register all entity tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        server: AtomsServer instance with handlers
    """

    @mcp.tool()
    async def create_entity(
        entity_type: str,
        name: str,
        description: str = "",
        properties: Optional[dict[str, Any]] = None,
        metadata: Optional[dict[str, Any]] = None,
        created_by: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Create a new entity in the workspace.

        Args:
            entity_type: Type of entity to create (workspace, project, task, document)
            name: Name of the entity
            description: Optional description
            properties: Entity-specific properties
            metadata: Additional metadata
            created_by: User ID creating the entity

        Returns:
            Created entity details

        Examples:
            Create a project:
            ```
            create_entity(
                entity_type="project",
                name="My Project",
                description="A test project",
                properties={"workspace_id": "ws_123", "priority": 1}
            )
            ```

            Create a task:
            ```
            create_entity(
                entity_type="task",
                name="Implement feature",
                properties={"project_id": "proj_123", "priority": 2}
            )
            ```
        """
        command = CreateEntityCommand(
            entity_type=entity_type,
            name=name,
            description=description,
            properties=properties or {},
            metadata=metadata or {},
            created_by=created_by,
        )

        result = server.entity_command_handler.handle_create_entity(command)

        if result.is_error:
            raise Exception(result.error)

        return result.to_dict()

    @mcp.tool()
    async def get_entity(
        entity_id: str,
        use_cache: bool = True,
    ) -> dict[str, Any]:
        """
        Get an entity by ID.

        Args:
            entity_id: ID of entity to retrieve
            use_cache: Whether to use cached data

        Returns:
            Entity details

        Example:
            ```
            get_entity(entity_id="ent_123")
            ```
        """
        query = GetEntityQuery(entity_id=entity_id, use_cache=use_cache)
        result = server.entity_query_handler.handle_get_entity(query)

        if result.is_error:
            raise Exception(result.error)

        return result.to_dict()

    @mcp.tool()
    async def list_entities(
        filters: Optional[dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        """
        List entities with optional filtering and pagination.

        Args:
            filters: Filter criteria (e.g., {"entity_type": "project", "status": "active"})
            limit: Maximum number of results
            offset: Number of results to skip
            order_by: Field to order by
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Paginated list of entities

        Examples:
            List all projects:
            ```
            list_entities(filters={"entity_type": "project"})
            ```

            List active tasks with pagination:
            ```
            list_entities(
                filters={"entity_type": "task", "status": "active"},
                page=1,
                page_size=10
            )
            ```
        """
        query = ListEntitiesQuery(
            filters=filters or {},
            limit=limit,
            offset=offset,
            order_by=order_by,
            page=page,
            page_size=page_size,
        )

        result = server.entity_query_handler.handle_list_entities(query)

        if result.is_error:
            raise Exception(result.error)

        return result.to_dict()

    @mcp.tool()
    async def update_entity(
        entity_id: str,
        updates: dict[str, Any],
        validate_updates: bool = True,
    ) -> dict[str, Any]:
        """
        Update an existing entity.

        Args:
            entity_id: ID of entity to update
            updates: Dictionary of field updates
            validate_updates: Whether to validate updates

        Returns:
            Updated entity details

        Examples:
            Update project name:
            ```
            update_entity(
                entity_id="proj_123",
                updates={"name": "Updated Project Name"}
            )
            ```

            Update task status and priority:
            ```
            update_entity(
                entity_id="task_456",
                updates={"status": "in_progress", "priority": 1}
            )
            ```
        """
        command = UpdateEntityCommand(
            entity_id=entity_id,
            updates=updates,
            validate_updates=validate_updates,
        )

        result = server.entity_command_handler.handle_update_entity(command)

        if result.is_error:
            raise Exception(result.error)

        return result.to_dict()

    @mcp.tool()
    async def delete_entity(
        entity_id: str,
        soft_delete: bool = True,
        deleted_by: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Delete an entity.

        Args:
            entity_id: ID of entity to delete
            soft_delete: Whether to soft delete (default) or hard delete
            deleted_by: User ID deleting the entity

        Returns:
            Deletion confirmation

        Examples:
            Soft delete (mark as deleted):
            ```
            delete_entity(entity_id="ent_123", soft_delete=True)
            ```

            Hard delete (permanently remove):
            ```
            delete_entity(entity_id="ent_123", soft_delete=False)
            ```
        """
        command = DeleteEntityCommand(
            entity_id=entity_id,
            soft_delete=soft_delete,
            deleted_by=deleted_by,
        )

        result = server.entity_command_handler.handle_delete_entity(command)

        if result.is_error:
            raise Exception(result.error)

        return result.to_dict()

    @mcp.tool()
    async def archive_entity(
        entity_id: str,
        archived_by: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Archive an entity (mark as archived but keep accessible).

        Args:
            entity_id: ID of entity to archive
            archived_by: User ID archiving the entity

        Returns:
            Archived entity details

        Example:
            ```
            archive_entity(entity_id="proj_123")
            ```
        """
        command = ArchiveEntityCommand(
            entity_id=entity_id,
            archived_by=archived_by,
        )

        result = server.entity_command_handler.handle_archive_entity(command)

        if result.is_error:
            raise Exception(result.error)

        return result.to_dict()

    @mcp.tool()
    async def restore_entity(
        entity_id: str,
        restored_by: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Restore a deleted or archived entity.

        Args:
            entity_id: ID of entity to restore
            restored_by: User ID restoring the entity

        Returns:
            Restored entity details

        Example:
            ```
            restore_entity(entity_id="proj_123")
            ```
        """
        command = RestoreEntityCommand(
            entity_id=entity_id,
            restored_by=restored_by,
        )

        result = server.entity_command_handler.handle_restore_entity(command)

        if result.is_error:
            raise Exception(result.error)

        return result.to_dict()

    @mcp.tool()
    async def search_entities(
        query: str,
        fields: Optional[list[str]] = None,
        filters: Optional[dict[str, Any]] = None,
        limit: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        """
        Search entities using text search.

        Args:
            query: Search query string
            fields: Fields to search in (default: all fields)
            filters: Additional filters to apply
            limit: Maximum number of results
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Search results with matching entities

        Examples:
            Search for entities containing "api":
            ```
            search_entities(query="api")
            ```

            Search projects with "backend" in name or description:
            ```
            search_entities(
                query="backend",
                fields=["name", "description"],
                filters={"entity_type": "project"}
            )
            ```
        """
        search_query = SearchEntitiesQuery(
            query=query,
            fields=fields,
            filters=filters or {},
            limit=limit,
            page=page,
            page_size=page_size,
        )

        result = server.entity_query_handler.handle_search_entities(search_query)

        if result.is_error:
            raise Exception(result.error)

        return result.to_dict()

    @mcp.tool()
    async def count_entities(
        filters: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Count entities matching filters.

        Args:
            filters: Filter criteria

        Returns:
            Count of matching entities

        Examples:
            Count all projects:
            ```
            count_entities(filters={"entity_type": "project"})
            ```

            Count active tasks:
            ```
            count_entities(filters={"entity_type": "task", "status": "active"})
            ```
        """
        query = CountEntitiesQuery(filters=filters or {})
        result = server.entity_query_handler.handle_count_entities(query)

        if result.is_error:
            raise Exception(result.error)

        return result.to_dict()


__all__ = ["register_entity_tools"]
