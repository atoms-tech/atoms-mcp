"""
Relationship service - business logic for relationship operations.

This module implements the core business logic for managing relationships
between entities, including graph operations.
"""

from typing import Any, Optional

from ..models.relationship import (
    Relationship,
    RelationshipGraph,
    RelationshipStatus,
    RelationType,
)
from ..ports.cache import Cache
from ..ports.logger import Logger
from ..ports.repository import Repository


class RelationshipService:
    """
    Service for managing relationship business logic.

    This service implements relationship-related business rules and operations,
    including graph traversal and relationship constraints.

    Attributes:
        repository: Repository for relationship persistence
        logger: Logger for recording events
        cache: Cache for performance optimization
    """

    def __init__(
        self,
        repository: Repository[Relationship],
        logger: Logger,
        cache: Optional[Cache] = None,
    ):
        """
        Initialize relationship service.

        Args:
            repository: Repository for relationship persistence
            logger: Logger for recording events
            cache: Optional cache for performance
        """
        self.repository = repository
        self.logger = logger
        self.cache = cache

    def add_relationship(
        self,
        source_id: str,
        target_id: str,
        relationship_type: RelationType,
        properties: Optional[dict[str, Any]] = None,
        bidirectional: bool = False,
        created_by: Optional[str] = None,
    ) -> Relationship:
        """
        Add a relationship between two entities.

        Args:
            source_id: Source entity ID
            target_id: Target entity ID
            relationship_type: Type of relationship
            properties: Optional relationship properties
            bidirectional: Whether to create inverse relationship
            created_by: ID of user creating the relationship

        Returns:
            Created relationship

        Raises:
            ValueError: If relationship is invalid
            RepositoryError: If persistence fails
        """
        self.logger.info(
            f"Adding {relationship_type.value} relationship: {source_id} -> {target_id}"
        )

        # Create relationship
        relationship = Relationship(
            source_id=source_id,
            target_id=target_id,
            relationship_type=relationship_type,
            properties=properties or {},
            created_by=created_by,
        )

        # Check for cycles if this is a hierarchical relationship
        if self._is_hierarchical(relationship_type):
            if self._would_create_cycle(source_id, target_id):
                raise ValueError("Relationship would create a cycle")

        # Save relationship
        created = self.repository.save(relationship)

        # Create inverse if bidirectional
        if bidirectional:
            inverse = relationship.create_inverse()
            if inverse:
                self.repository.save(inverse)
                self.logger.debug("Created inverse relationship")

        # Invalidate cache
        self._invalidate_relationship_cache(source_id, target_id)

        self.logger.info(f"Relationship {created.id} added successfully")
        return created

    def remove_relationship(
        self,
        relationship_id: str,
        remove_inverse: bool = False,
    ) -> bool:
        """
        Remove a relationship.

        Args:
            relationship_id: ID of relationship to remove
            remove_inverse: Whether to also remove inverse relationship

        Returns:
            True if relationship was removed
        """
        self.logger.info(f"Removing relationship {relationship_id}")

        relationship = self.repository.get(relationship_id)
        if not relationship:
            self.logger.warning(f"Relationship {relationship_id} not found")
            return False

        # Mark as deleted
        relationship.delete()
        self.repository.save(relationship)

        # Remove inverse if requested
        if remove_inverse:
            inverse_type = relationship.get_inverse_type()
            if inverse_type:
                inverses = self.get_relationships(
                    source_id=relationship.target_id,
                    target_id=relationship.source_id,
                    relationship_type=inverse_type,
                )
                for inv in inverses:
                    inv.delete()
                    self.repository.save(inv)

        # Invalidate cache
        self._invalidate_relationship_cache(
            relationship.source_id, relationship.target_id
        )

        self.logger.info(f"Relationship {relationship_id} removed successfully")
        return True

    def get_relationships(
        self,
        source_id: Optional[str] = None,
        target_id: Optional[str] = None,
        relationship_type: Optional[RelationType] = None,
        status: RelationshipStatus = RelationshipStatus.ACTIVE,
    ) -> list[Relationship]:
        """
        Get relationships matching criteria.

        Args:
            source_id: Filter by source entity ID
            target_id: Filter by target entity ID
            relationship_type: Filter by relationship type
            status: Filter by status

        Returns:
            List of matching relationships
        """
        filters = {"status": status.value}

        if source_id:
            filters["source_id"] = source_id
        if target_id:
            filters["target_id"] = target_id
        if relationship_type:
            filters["relationship_type"] = relationship_type.value

        relationships = self.repository.list(filters=filters)

        self.logger.debug(
            f"Found {len(relationships)} relationships matching filters"
        )
        return relationships

    def get_outgoing_relationships(
        self,
        entity_id: str,
        relationship_type: Optional[RelationType] = None,
    ) -> list[Relationship]:
        """
        Get all outgoing relationships from an entity.

        Args:
            entity_id: Source entity ID
            relationship_type: Optional filter by relationship type

        Returns:
            List of outgoing relationships
        """
        return self.get_relationships(
            source_id=entity_id, relationship_type=relationship_type
        )

    def get_incoming_relationships(
        self,
        entity_id: str,
        relationship_type: Optional[RelationType] = None,
    ) -> list[Relationship]:
        """
        Get all incoming relationships to an entity.

        Args:
            entity_id: Target entity ID
            relationship_type: Optional filter by relationship type

        Returns:
            List of incoming relationships
        """
        return self.get_relationships(
            target_id=entity_id, relationship_type=relationship_type
        )

    def get_related_entities(
        self,
        entity_id: str,
        relationship_type: Optional[RelationType] = None,
        direction: str = "outgoing",
    ) -> list[str]:
        """
        Get IDs of entities related to the given entity.

        Args:
            entity_id: Entity ID to get related entities for
            relationship_type: Optional filter by relationship type
            direction: "outgoing", "incoming", or "both"

        Returns:
            List of related entity IDs
        """
        related_ids = []

        if direction in ("outgoing", "both"):
            outgoing = self.get_outgoing_relationships(
                entity_id, relationship_type
            )
            related_ids.extend([rel.target_id for rel in outgoing])

        if direction in ("incoming", "both"):
            incoming = self.get_incoming_relationships(
                entity_id, relationship_type
            )
            related_ids.extend([rel.source_id for rel in incoming])

        return list(set(related_ids))

    def build_graph(
        self,
        entity_ids: Optional[list[str]] = None,
        relationship_type: Optional[RelationType] = None,
    ) -> RelationshipGraph:
        """
        Build a relationship graph.

        Args:
            entity_ids: Optional list of entity IDs to include (None = all)
            relationship_type: Optional filter by relationship type

        Returns:
            RelationshipGraph instance
        """
        self.logger.debug("Building relationship graph")

        graph = RelationshipGraph()

        # Get relationships
        filters = {"status": RelationshipStatus.ACTIVE.value}
        if relationship_type:
            filters["relationship_type"] = relationship_type.value

        relationships = self.repository.list(filters=filters)

        # Filter by entity IDs if provided
        if entity_ids:
            entity_id_set = set(entity_ids)
            relationships = [
                rel
                for rel in relationships
                if rel.source_id in entity_id_set
                or rel.target_id in entity_id_set
            ]

        # Build graph
        for rel in relationships:
            graph.add_edge(rel)

        self.logger.debug(
            f"Built graph with {len(graph.nodes)} nodes and {len(graph.edges)} edges"
        )
        return graph

    def find_path(
        self,
        start_id: str,
        end_id: str,
        max_depth: int = 10,
    ) -> Optional[list[Relationship]]:
        """
        Find a path between two entities.

        Args:
            start_id: Starting entity ID
            end_id: Target entity ID
            max_depth: Maximum path length

        Returns:
            List of relationships forming the path, or None if no path exists
        """
        self.logger.debug(f"Finding path from {start_id} to {end_id}")

        graph = self.build_graph()
        path = graph.find_path(start_id, end_id, max_depth)

        if path:
            self.logger.debug(f"Found path of length {len(path)}")
        else:
            self.logger.debug("No path found")

        return path

    def get_descendants(
        self,
        entity_id: str,
        relationship_type: RelationType = RelationType.PARENT_OF,
        max_depth: int = 10,
    ) -> set[str]:
        """
        Get all descendant entities.

        Args:
            entity_id: Root entity ID
            relationship_type: Type of parent-child relationship
            max_depth: Maximum depth to traverse

        Returns:
            Set of descendant entity IDs
        """
        self.logger.debug(f"Getting descendants of {entity_id}")

        graph = self.build_graph(relationship_type=relationship_type)
        descendants = graph.get_descendants(entity_id, max_depth)

        self.logger.debug(f"Found {len(descendants)} descendants")
        return descendants

    def _would_create_cycle(
        self,
        source_id: str,
        target_id: str,
    ) -> bool:
        """
        Check if adding a relationship would create a cycle.

        Args:
            source_id: Source entity ID
            target_id: Target entity ID

        Returns:
            True if adding relationship would create a cycle
        """
        # Build current graph
        graph = self.build_graph()

        # If target already has a path to source, adding source->target would create a cycle
        path = graph.find_path(target_id, source_id)
        return path is not None

    def _is_hierarchical(self, relationship_type: RelationType) -> bool:
        """
        Check if a relationship type is hierarchical.

        Args:
            relationship_type: Relationship type to check

        Returns:
            True if relationship is hierarchical
        """
        hierarchical_types = {
            RelationType.PARENT_OF,
            RelationType.CHILD_OF,
            RelationType.CONTAINS,
            RelationType.CONTAINED_BY,
        }
        return relationship_type in hierarchical_types

    def _invalidate_relationship_cache(
        self, source_id: str, target_id: str
    ) -> None:
        """
        Invalidate relationship cache for entities.

        Args:
            source_id: Source entity ID
            target_id: Target entity ID
        """
        if self.cache:
            self.cache.delete(f"relationships:outgoing:{source_id}")
            self.cache.delete(f"relationships:incoming:{target_id}")
            self.cache.delete(f"relationships:graph")
