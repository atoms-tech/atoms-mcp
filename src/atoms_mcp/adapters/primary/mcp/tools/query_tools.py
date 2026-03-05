"""
MCP tools for search and analytics operations.

This module defines FastMCP tools for searching entities and
retrieving analytics and statistics.
"""

from typing import TYPE_CHECKING, Any, Optional

from .....application.queries.analytics_queries import (
    EntityCountQuery,
    WorkspaceStatsQuery,
    ActivityQuery,
)

if TYPE_CHECKING:
    from ..server import AtomsServer


def register_query_tools(mcp: Any, server: "AtomsServer") -> None:
    """
    Register all query and analytics tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        server: AtomsServer instance with handlers
    """

    @mcp.tool()
    async def search_entities(
        query: str,
        entity_types: Optional[list[str]] = None,
        fields: Optional[list[str]] = None,
        filters: Optional[dict[str, Any]] = None,
        limit: int = 20,
        use_cache: bool = True,
    ) -> dict[str, Any]:
        """
        Search entities across multiple types using text search.

        Args:
            query: Search query string
            entity_types: Types of entities to search (default: all types)
            fields: Fields to search in (default: all fields)
            filters: Additional filters to apply
            limit: Maximum number of results
            use_cache: Whether to use cached results

        Returns:
            Search results with matching entities

        Examples:
            Search all entities:
            ```
            search_entities(query="authentication")
            ```

            Search only projects and documents:
            ```
            search_entities(
                query="api design",
                entity_types=["project", "document"]
            )
            ```

            Search with filters:
            ```
            search_entities(
                query="backend",
                entity_types=["task"],
                filters={"status": "active", "priority": 1}
            )
            ```
        """
        from .....application.queries.entity_queries import SearchEntitiesQuery

        search_query = SearchEntitiesQuery(
            query=query,
            fields=fields,
            filters={**(filters or {}), **{"entity_type": entity_types}} if entity_types else (filters or {}),
            limit=limit,
        )

        result = server.entity_query_handler.handle_search_entities(search_query)

        if result.is_error:
            raise Exception(result.error)

        # Add cache metadata
        response = result.to_dict()
        response["metadata"]["cached"] = use_cache
        return response

    @mcp.tool()
    async def get_analytics(
        entity_type: Optional[str] = None,
        aggregation: str = "count",
        group_by: Optional[str] = None,
        filters: Optional[dict[str, Any]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Get analytics and aggregated statistics.

        Args:
            entity_type: Type of entity to analyze (default: all types)
            aggregation: Type of aggregation (count, sum, avg, min, max)
            group_by: Field to group by
            filters: Filters to apply
            start_date: Start date for time-based analysis (ISO format)
            end_date: End date for time-based analysis (ISO format)

        Returns:
            Analytics results

        Examples:
            Count all entities by type:
            ```
            get_analytics(aggregation="count", group_by="entity_type")
            ```

            Count tasks by status:
            ```
            get_analytics(
                entity_type="task",
                aggregation="count",
                group_by="status"
            )
            ```

            Get project statistics in date range:
            ```
            get_analytics(
                entity_type="project",
                aggregation="count",
                group_by="status",
                start_date="2024-01-01",
                end_date="2024-12-31"
            )
            ```
        """
        # Use EntityCountQuery for analytics
        query = EntityCountQuery(
            entity_type=entity_type,
            filters=filters or {},
            start_date=start_date,
            end_date=end_date,
        )

        result = server.analytics_query_handler.handle_entity_count(query)

        if result.is_error:
            raise Exception(result.error)

        return result.to_dict()

    @mcp.tool()
    async def get_workspace_stats(
        workspace_id: str,
        include_archived: bool = False,
    ) -> dict[str, Any]:
        """
        Get comprehensive statistics for a workspace.

        Args:
            workspace_id: Workspace ID
            include_archived: Whether to include archived entities

        Returns:
            Workspace statistics including:
            - Total entities by type
            - Entity status breakdown
            - Relationship counts
            - Activity metrics

        Example:
            ```
            get_workspace_stats(workspace_id="ws_123")
            ```
        """
        query = WorkspaceStatsQuery(
            workspace_id=workspace_id,
            include_archived=include_archived,
        )

        result = server.analytics_query_handler.handle_workspace_stats(query)

        if result.is_error:
            raise Exception(result.error)

        return result.to_dict()

    @mcp.tool()
    async def get_entity_activity(
        entity_id: str,
        days: int = 7,
    ) -> dict[str, Any]:
        """
        Get activity history for a specific entity.

        Args:
            entity_id: Entity ID
            days: Number of days of history (default: 7)

        Returns:
            Entity activity including:
            - Recent changes
            - Related entities count
            - Relationship breakdown
            - Metadata summary

        Example:
            ```
            get_entity_activity(entity_id="proj_123", days=30)
            ```
        """
        query = ActivityQuery(
            entity_id=entity_id,
            days=days,
        )
        result = server.analytics_query_handler.handle_activity(query)

        if result.is_error:
            raise Exception(result.error)

        return result.to_dict()

    @mcp.tool()
    async def get_relationship_summary(
        source_id: Optional[str] = None,
        target_id: Optional[str] = None,
        relationship_type: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Get summary of relationships.

        Args:
            source_id: Filter by source entity ID
            target_id: Filter by target entity ID
            relationship_type: Filter by relationship type

        Returns:
            Relationship summary including:
            - Total count
            - Breakdown by type
            - Most connected entities

        Examples:
            Get all relationships summary:
            ```
            get_relationship_summary()
            ```

            Get relationships for entity:
            ```
            get_relationship_summary(source_id="proj_123")
            ```

            Get specific relationship type summary:
            ```
            get_relationship_summary(relationship_type="DEPENDS_ON")
            ```
        """
        from .....application.queries.relationship_queries import GetRelationshipsQuery

        query = GetRelationshipsQuery(
            source_id=source_id,
            target_id=target_id,
            relationship_type=relationship_type,
        )

        result = server.relationship_query_handler.handle_get_relationships(query)

        if result.is_error:
            raise Exception(result.error)

        # Add summary statistics
        data = result.to_dict()
        relationships = data.get("data", [])

        # Calculate summary
        type_counts = {}
        for rel in relationships:
            rel_type = rel.get("relationship_type", "unknown")
            type_counts[rel_type] = type_counts.get(rel_type, 0) + 1

        data["metadata"]["summary"] = {
            "total": len(relationships),
            "by_type": type_counts,
        }

        return data


__all__ = ["register_query_tools"]
