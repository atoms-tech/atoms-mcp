"""
Domain models for relationships between entities.

This module defines relationship models that connect entities together.
Pure Python implementation with no external dependencies.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4


class RelationType(Enum):
    """Type enumeration for relationships between entities."""

    # Hierarchical relationships
    PARENT_OF = "parent_of"
    CHILD_OF = "child_of"
    CONTAINS = "contains"
    CONTAINED_BY = "contained_by"

    # Assignment relationships
    ASSIGNED_TO = "assigned_to"
    ASSIGNED_BY = "assigned_by"
    OWNS = "owns"
    OWNED_BY = "owned_by"

    # Dependency relationships
    DEPENDS_ON = "depends_on"
    BLOCKS = "blocks"
    BLOCKED_BY = "blocked_by"

    # Association relationships
    RELATES_TO = "relates_to"
    REFERENCES = "references"
    REFERENCED_BY = "referenced_by"
    LINKS_TO = "links_to"

    # Workflow relationships
    TRIGGERS = "triggers"
    TRIGGERED_BY = "triggered_by"
    FOLLOWS = "follows"
    PRECEDES = "precedes"

    # Membership relationships
    MEMBER_OF = "member_of"
    HAS_MEMBER = "has_member"


class RelationshipStatus(Enum):
    """Status enumeration for relationships."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    DELETED = "deleted"


@dataclass
class Relationship:
    """
    Generic relationship model connecting two entities.

    Relationships are directed edges in the entity graph, connecting
    a source entity to a target entity with a specific type.

    Attributes:
        id: Unique identifier for the relationship
        source_id: ID of the source entity
        target_id: ID of the target entity
        relationship_type: Type of relationship
        status: Current status of the relationship
        created_at: Timestamp when relationship was created
        updated_at: Timestamp when relationship was last updated
        created_by: ID of user who created the relationship
        metadata: Additional flexible metadata
        properties: Relationship-specific properties
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    source_id: str = ""
    target_id: str = ""
    relationship_type: RelationType = RelationType.RELATES_TO
    status: RelationshipStatus = RelationshipStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    properties: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate relationship after initialization."""
        if not self.source_id:
            raise ValueError("Source ID cannot be empty")
        if not self.target_id:
            raise ValueError("Target ID cannot be empty")
        if self.source_id == self.target_id:
            raise ValueError("Source and target cannot be the same entity")

    def mark_updated(self) -> None:
        """Update the updated_at timestamp to current time."""
        self.updated_at = datetime.utcnow()

    def activate(self) -> None:
        """Activate this relationship."""
        self.status = RelationshipStatus.ACTIVE
        self.mark_updated()

    def deactivate(self) -> None:
        """Deactivate this relationship."""
        self.status = RelationshipStatus.INACTIVE
        self.mark_updated()

    def delete(self) -> None:
        """Soft delete this relationship."""
        self.status = RelationshipStatus.DELETED
        self.mark_updated()

    def is_active(self) -> bool:
        """Check if relationship is active."""
        return self.status == RelationshipStatus.ACTIVE

    def is_deleted(self) -> bool:
        """Check if relationship is deleted."""
        return self.status == RelationshipStatus.DELETED

    def get_property(self, key: str, default: Any = None) -> Any:
        """
        Get relationship property by key.

        Args:
            key: Property key to retrieve
            default: Default value if key doesn't exist

        Returns:
            Property value or default
        """
        return self.properties.get(key, default)

    def set_property(self, key: str, value: Any) -> None:
        """
        Set relationship property.

        Args:
            key: Property key to set
            value: Value to store
        """
        self.properties[key] = value
        self.mark_updated()

    def get_inverse_type(self) -> Optional[RelationType]:
        """
        Get the inverse relationship type.

        Returns:
            Inverse relationship type if it exists, None otherwise
        """
        inverse_map = {
            RelationType.PARENT_OF: RelationType.CHILD_OF,
            RelationType.CHILD_OF: RelationType.PARENT_OF,
            RelationType.CONTAINS: RelationType.CONTAINED_BY,
            RelationType.CONTAINED_BY: RelationType.CONTAINS,
            RelationType.ASSIGNED_TO: RelationType.ASSIGNED_BY,
            RelationType.ASSIGNED_BY: RelationType.ASSIGNED_TO,
            RelationType.OWNS: RelationType.OWNED_BY,
            RelationType.OWNED_BY: RelationType.OWNS,
            RelationType.DEPENDS_ON: RelationType.BLOCKED_BY,
            RelationType.BLOCKS: RelationType.BLOCKED_BY,
            RelationType.BLOCKED_BY: RelationType.BLOCKS,
            RelationType.REFERENCES: RelationType.REFERENCED_BY,
            RelationType.REFERENCED_BY: RelationType.REFERENCES,
            RelationType.TRIGGERS: RelationType.TRIGGERED_BY,
            RelationType.TRIGGERED_BY: RelationType.TRIGGERS,
            RelationType.FOLLOWS: RelationType.PRECEDES,
            RelationType.PRECEDES: RelationType.FOLLOWS,
            RelationType.MEMBER_OF: RelationType.HAS_MEMBER,
            RelationType.HAS_MEMBER: RelationType.MEMBER_OF,
        }
        return inverse_map.get(self.relationship_type)

    def create_inverse(self) -> Optional["Relationship"]:
        """
        Create an inverse relationship.

        Returns:
            Inverse relationship if inverse type exists, None otherwise
        """
        inverse_type = self.get_inverse_type()
        if inverse_type is None:
            return None

        return Relationship(
            source_id=self.target_id,
            target_id=self.source_id,
            relationship_type=inverse_type,
            status=self.status,
            created_by=self.created_by,
            metadata=self.metadata.copy(),
            properties=self.properties.copy(),
        )


@dataclass
class RelationshipConstraint:
    """
    Constraint for validating relationships.

    Defines rules for valid relationships between entity types.

    Attributes:
        source_type: Required source entity type
        target_type: Required target entity type
        relationship_type: Type of relationship
        allow_multiple: Whether multiple relationships of this type are allowed
        required: Whether this relationship is required
        bidirectional: Whether relationship should be bidirectional
    """

    source_type: str = ""
    target_type: str = ""
    relationship_type: RelationType = RelationType.RELATES_TO
    allow_multiple: bool = True
    required: bool = False
    bidirectional: bool = False

    def validate(self, relationship: Relationship) -> tuple[bool, Optional[str]]:
        """
        Validate a relationship against this constraint.

        Args:
            relationship: Relationship to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if relationship.relationship_type != self.relationship_type:
            return False, "Relationship type mismatch"

        return True, None


@dataclass
class RelationshipGraph:
    """
    In-memory graph structure for relationship navigation.

    Provides efficient traversal of relationships between entities.

    Attributes:
        nodes: Set of entity IDs in the graph
        edges: List of relationships (edges)
        adjacency: Adjacency list for quick lookups
    """

    nodes: set[str] = field(default_factory=set)
    edges: list[Relationship] = field(default_factory=list)
    adjacency: dict[str, list[Relationship]] = field(default_factory=dict)

    def add_node(self, node_id: str) -> None:
        """
        Add a node to the graph.

        Args:
            node_id: Entity ID to add
        """
        self.nodes.add(node_id)
        if node_id not in self.adjacency:
            self.adjacency[node_id] = []

    def add_edge(self, relationship: Relationship) -> None:
        """
        Add an edge (relationship) to the graph.

        Args:
            relationship: Relationship to add
        """
        self.add_node(relationship.source_id)
        self.add_node(relationship.target_id)
        self.edges.append(relationship)
        self.adjacency[relationship.source_id].append(relationship)

    def get_outgoing(self, node_id: str) -> list[Relationship]:
        """
        Get all outgoing relationships from a node.

        Args:
            node_id: Source entity ID

        Returns:
            List of outgoing relationships
        """
        return self.adjacency.get(node_id, [])

    def get_incoming(self, node_id: str) -> list[Relationship]:
        """
        Get all incoming relationships to a node.

        Args:
            node_id: Target entity ID

        Returns:
            List of incoming relationships
        """
        return [edge for edge in self.edges if edge.target_id == node_id]

    def find_path(
        self, start_id: str, end_id: str, max_depth: int = 10
    ) -> Optional[list[Relationship]]:
        """
        Find a path between two nodes using BFS.

        Args:
            start_id: Starting entity ID
            end_id: Target entity ID
            max_depth: Maximum search depth

        Returns:
            List of relationships forming the path, or None if no path exists
        """
        if start_id not in self.nodes or end_id not in self.nodes:
            return None

        visited = {start_id}
        queue = [(start_id, [])]

        while queue:
            current_id, path = queue.pop(0)

            if len(path) >= max_depth:
                continue

            if current_id == end_id:
                return path

            for relationship in self.get_outgoing(current_id):
                if relationship.target_id not in visited:
                    visited.add(relationship.target_id)
                    queue.append((relationship.target_id, path + [relationship]))

        return None

    def get_descendants(self, node_id: str, max_depth: int = 10) -> set[str]:
        """
        Get all descendant nodes (recursive).

        Args:
            node_id: Starting entity ID
            max_depth: Maximum recursion depth

        Returns:
            Set of descendant entity IDs
        """
        descendants = set()
        visited = {node_id}
        queue = [(node_id, 0)]

        while queue:
            current_id, depth = queue.pop(0)

            if depth >= max_depth:
                continue

            for relationship in self.get_outgoing(current_id):
                if relationship.target_id not in visited:
                    visited.add(relationship.target_id)
                    descendants.add(relationship.target_id)
                    queue.append((relationship.target_id, depth + 1))

        return descendants
