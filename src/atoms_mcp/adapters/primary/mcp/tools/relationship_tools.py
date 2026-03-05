"""
MCP tools for relationship operations.

This module defines FastMCP tools for creating, reading, and managing
relationships between entities.
"""

from typing import TYPE_CHECKING, Any, Optional

from .....application.commands.relationship_commands import (
    CreateRelationshipCommand,
    DeleteRelationshipCommand,
    UpdateRelationshipCommand,
)
from .....application.queries.relationship_queries import (
    FindPathQuery,
    GetRelationshipsQuery,
)

if TYPE_CHECKING:
    from ..server import AtomsServer


def register_relationship_tools(mcp: Any, server: "AtomsServer") -> None:
    """
    Register all relationship tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        server: AtomsServer instance with handlers
    """

    @mcp.tool()
    async def create_relationship(
        source_id: str,
        target_id: str,
        relationship_type: str,
        properties: Optional[dict[str, Any]] = None,
        bidirectional: bool = False,
        created_by: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Create a relationship between two entities.

        Args:
            source_id: Source entity ID
            target_id: Target entity ID
            relationship_type: Type of relationship (PARENT_CHILD, DEPENDS_ON, REFERENCES, etc.)
            properties: Optional relationship properties
            bidirectional: Whether to create inverse relationship
            created_by: User ID creating the relationship

        Returns:
            Created relationship details

        Examples:
            Create parent-child relationship:
            ```
            create_relationship(
                source_id="proj_123",
                target_id="task_456",
                relationship_type="PARENT_CHILD"
            )
            ```

            Create task dependency:
            ```
            create_relationship(
                source_id="task_123",
                target_id="task_456",
                relationship_type="DEPENDS_ON",
                properties={"dependency_type": "blocking"}
            )
            ```

            Create bidirectional reference:
            ```
            create_relationship(
                source_id="doc_123",
                target_id="req_456",
                relationship_type="REFERENCES",
                bidirectional=True
            )
            ```
        """
        command = CreateRelationshipCommand(
            source_id=source_id,
            target_id=target_id,
            relationship_type=relationship_type,
            properties=properties or {},
            bidirectional=bidirectional,
            created_by=created_by,
        )

        result = server.relationship_command_handler.handle_create_relationship(command)

        if result.is_error:
            raise Exception(result.error)

        return result.to_dict()

    @mcp.tool()
    async def delete_relationship(
        relationship_id: Optional[str] = None,
        source_id: Optional[str] = None,
        target_id: Optional[str] = None,
        relationship_type: Optional[str] = None,
        remove_inverse: bool = False,
        deleted_by: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Delete a relationship.

        Args:
            relationship_id: ID of relationship to delete (optional if source/target provided)
            source_id: Source entity ID (optional if relationship_id provided)
            target_id: Target entity ID (optional if relationship_id provided)
            relationship_type: Type of relationship (optional if relationship_id provided)
            remove_inverse: Whether to also remove inverse relationship
            deleted_by: User ID deleting the relationship

        Returns:
            Deletion confirmation

        Examples:
            Delete by relationship ID:
            ```
            delete_relationship(relationship_id="rel_123")
            ```

            Delete by source and target:
            ```
            delete_relationship(
                source_id="proj_123",
                target_id="task_456",
                relationship_type="PARENT_CHILD"
            )
            ```

            Delete with inverse:
            ```
            delete_relationship(
                relationship_id="rel_123",
                remove_inverse=True
            )
            ```
        """
        command = DeleteRelationshipCommand(
            relationship_id=relationship_id,
            source_id=source_id,
            target_id=target_id,
            relationship_type=relationship_type,
            remove_inverse=remove_inverse,
            deleted_by=deleted_by,
        )

        result = server.relationship_command_handler.handle_delete_relationship(command)

        if result.is_error:
            raise Exception(result.error)

        return result.to_dict()

    @mcp.tool()
    async def update_relationship(
        relationship_id: str,
        properties: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Update a relationship's properties.

        Args:
            relationship_id: ID of relationship to update
            properties: Properties to update

        Returns:
            Updated relationship details

        Example:
            ```
            update_relationship(
                relationship_id="rel_123",
                properties={"weight": 5, "metadata": {"priority": "high"}}
            )
            ```
        """
        command = UpdateRelationshipCommand(
            relationship_id=relationship_id,
            properties=properties,
        )

        result = server.relationship_command_handler.handle_update_relationship(command)

        if result.is_error:
            raise Exception(result.error)

        return result.to_dict()

    @mcp.tool()
    async def get_relationships(
        source_id: Optional[str] = None,
        target_id: Optional[str] = None,
        relationship_type: Optional[str] = None,
        bidirectional: bool = False,
        limit: Optional[int] = None,
    ) -> dict[str, Any]:
        """
        Get relationships with optional filtering.

        Args:
            source_id: Filter by source entity ID
            target_id: Filter by target entity ID
            relationship_type: Filter by relationship type
            bidirectional: Whether to include inverse relationships
            limit: Maximum number of results

        Returns:
            List of matching relationships

        Examples:
            Get all relationships for an entity:
            ```
            get_relationships(source_id="proj_123")
            ```

            Get dependencies of a task:
            ```
            get_relationships(
                source_id="task_123",
                relationship_type="DEPENDS_ON"
            )
            ```

            Get all relationships between two entities:
            ```
            get_relationships(
                source_id="doc_123",
                target_id="req_456",
                bidirectional=True
            )
            ```
        """
        query = GetRelationshipsQuery(
            source_id=source_id,
            target_id=target_id,
            relationship_type=relationship_type,
        )

        result = server.relationship_query_handler.handle_get_relationships(query)

        if result.is_error:
            raise Exception(result.error)

        return result.to_dict()

    @mcp.tool()
    async def find_path(
        source_id: str,
        target_id: str,
        max_depth: int = 5,
        relationship_types: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """
        Find a path between two entities through relationships.

        Args:
            source_id: Starting entity ID
            target_id: Target entity ID
            max_depth: Maximum depth to search
            relationship_types: Types of relationships to follow

        Returns:
            Path details if found, including intermediate nodes

        Examples:
            Find any path:
            ```
            find_path(
                source_id="proj_123",
                target_id="doc_456"
            )
            ```

            Find path through specific relationship types:
            ```
            find_path(
                source_id="task_123",
                target_id="task_789",
                relationship_types=["DEPENDS_ON", "BLOCKS"],
                max_depth=3
            )
            ```
        """
        query = FindPathQuery(
            start_id=source_id,
            end_id=target_id,
            max_depth=max_depth,
        )

        result = server.relationship_query_handler.handle_find_path(query)

        if result.is_error:
            raise Exception(result.error)

        return result.to_dict()


__all__ = ["register_relationship_tools"]
