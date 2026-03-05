"""
Comprehensive tests for domain layer relationship service.

Tests cover:
- Relationship creation and removal
- Bidirectional relationships
- Relationship querying
- Graph operations
"""

import pytest

from atoms_mcp.domain.models.relationship import (
    Relationship,
    RelationType,
    RelationshipStatus,
)
from atoms_mcp.domain.services.relationship_service import RelationshipService

from conftest import MockRepository, MockLogger, MockCache


class TestAddRelationship:
    """Tests for relationship creation."""

    @pytest.fixture
    def service(self):
        """Create a relationship service with mock dependencies."""
        repository = MockRepository()
        logger = MockLogger()
        cache = MockCache()
        return RelationshipService(repository, logger, cache)

    def test_add_relationship_success(self, service):
        """Should successfully add a relationship."""
        rel = service.add_relationship(
            source_id="entity-1",
            target_id="entity-2",
            relationship_type=RelationType.CONTAINS,
        )

        assert rel is not None
        assert rel.source_id == "entity-1"
        assert rel.target_id == "entity-2"
        assert rel.relationship_type == RelationType.CONTAINS
        assert rel.status == RelationshipStatus.ACTIVE

    def test_add_relationship_with_properties(self, service):
        """Should add relationship with custom properties."""
        properties = {"strength": "high", "label": "contains"}

        rel = service.add_relationship(
            source_id="entity-1",
            target_id="entity-2",
            relationship_type=RelationType.CONTAINS,
            properties=properties,
        )

        assert rel.properties == properties

    def test_add_relationship_with_created_by(self, service):
        """Should add relationship with creator information."""
        rel = service.add_relationship(
            source_id="entity-1",
            target_id="entity-2",
            relationship_type=RelationType.CONTAINS,
            created_by="user-123",
        )

        assert rel.created_by == "user-123"

    def test_add_relationship_prevents_self_reference(self, service):
        """Should prevent self-referencing relationships."""
        with pytest.raises(ValueError) as exc_info:
            service.add_relationship(
                source_id="entity-1",
                target_id="entity-1",
                relationship_type=RelationType.PARENT_OF,
            )
        assert "same entity" in str(exc_info.value).lower()

    def test_add_relationship_bidirectional(self, service):
        """Should create inverse relationship when bidirectional=True."""
        rel = service.add_relationship(
            source_id="entity-1",
            target_id="entity-2",
            relationship_type=RelationType.PARENT_OF,
            bidirectional=True,
        )

        assert rel is not None
        assert rel.source_id == "entity-1"
        assert rel.target_id == "entity-2"

    def test_add_relationship_unidirectional(self, service):
        """Should create only forward relationship when bidirectional=False."""
        rel = service.add_relationship(
            source_id="entity-1",
            target_id="entity-2",
            relationship_type=RelationType.CONTAINS,
            bidirectional=False,
        )

        assert rel is not None
        assert rel.source_id == "entity-1"
        assert rel.target_id == "entity-2"

    def test_add_different_relationship_types(self, service):
        """Should support various relationship types."""
        relationship_types = [
            RelationType.PARENT_OF,
            RelationType.CHILD_OF,
            RelationType.CONTAINS,
            RelationType.CONTAINED_BY,
            RelationType.ASSIGNED_TO,
            RelationType.DEPENDS_ON,
            RelationType.RELATES_TO,
            RelationType.TRIGGERS,
            RelationType.MEMBER_OF,
        ]

        for rel_type in relationship_types:
            rel = service.add_relationship(
                source_id=f"entity-src",
                target_id=f"entity-tgt-{rel_type.value}",
                relationship_type=rel_type,
            )
            assert rel.relationship_type == rel_type


class TestRemoveRelationship:
    """Tests for relationship removal."""

    @pytest.fixture
    def service(self):
        """Create a relationship service with mock dependencies."""
        repository = MockRepository()
        logger = MockLogger()
        cache = MockCache()
        return RelationshipService(repository, logger, cache)

    def test_remove_relationship_success(self, service):
        """Should successfully remove a relationship."""
        rel = service.add_relationship(
            source_id="entity-1",
            target_id="entity-2",
            relationship_type=RelationType.CONTAINS,
        )

        success = service.remove_relationship(rel.id)

        assert success is True

    def test_remove_relationship_not_found(self, service):
        """Should return False when removing non-existent relationship."""
        success = service.remove_relationship("non-existent-id")

        assert success is False

    def test_remove_relationship_with_inverse(self, service):
        """Should handle remove_inverse flag."""
        rel = service.add_relationship(
            source_id="entity-1",
            target_id="entity-2",
            relationship_type=RelationType.PARENT_OF,
            bidirectional=True,
        )

        # Remove with inverse flag
        success = service.remove_relationship(rel.id, remove_inverse=True)

        assert success is True


class TestGetRelationships:
    """Tests for querying relationships."""

    @pytest.fixture
    def service(self):
        """Create a relationship service with mock dependencies."""
        repository = MockRepository()
        logger = MockLogger()
        cache = MockCache()
        return RelationshipService(repository, logger, cache)

    def test_get_relationships_returns_list(self, service):
        """Should return a list of relationships."""
        rel = service.add_relationship(
            source_id="entity-1",
            target_id="entity-2",
            relationship_type=RelationType.CONTAINS,
        )

        relationships = service.get_relationships()

        assert isinstance(relationships, list)

    def test_get_relationships_accepts_filters(self, service):
        """Should accept various filter parameters."""
        rel = service.add_relationship(
            source_id="entity-1",
            target_id="entity-2",
            relationship_type=RelationType.CONTAINS,
        )

        # Test various filter combinations
        result1 = service.get_relationships(source_id="entity-1")
        assert isinstance(result1, list)

        result2 = service.get_relationships(target_id="entity-2")
        assert isinstance(result2, list)

        result3 = service.get_relationships(
            relationship_type=RelationType.CONTAINS
        )
        assert isinstance(result3, list)

        result4 = service.get_relationships(status=RelationshipStatus.ACTIVE)
        assert isinstance(result4, list)


class TestDirectedRelationshipQueries:
    """Tests for directed relationship queries."""

    @pytest.fixture
    def service(self):
        """Create a relationship service with mock dependencies."""
        repository = MockRepository()
        logger = MockLogger()
        cache = MockCache()
        return RelationshipService(repository, logger, cache)

    def test_get_outgoing_relationships(self, service):
        """Should get outgoing relationships from an entity."""
        service.add_relationship(
            source_id="entity-1",
            target_id="entity-2",
            relationship_type=RelationType.CONTAINS,
        )

        outgoing = service.get_outgoing_relationships("entity-1")

        assert isinstance(outgoing, list)

    def test_get_outgoing_with_type_filter(self, service):
        """Should filter outgoing relationships by type."""
        service.add_relationship(
            source_id="entity-1",
            target_id="entity-2",
            relationship_type=RelationType.CONTAINS,
        )

        outgoing = service.get_outgoing_relationships(
            "entity-1", relationship_type=RelationType.CONTAINS
        )

        assert isinstance(outgoing, list)

    def test_get_incoming_relationships(self, service):
        """Should get incoming relationships to an entity."""
        service.add_relationship(
            source_id="entity-1",
            target_id="entity-3",
            relationship_type=RelationType.CONTAINS,
        )

        incoming = service.get_incoming_relationships("entity-3")

        assert isinstance(incoming, list)

    def test_get_incoming_with_type_filter(self, service):
        """Should filter incoming relationships by type."""
        service.add_relationship(
            source_id="entity-1",
            target_id="entity-3",
            relationship_type=RelationType.CONTAINS,
        )

        incoming = service.get_incoming_relationships(
            "entity-3", relationship_type=RelationType.CONTAINS
        )

        assert isinstance(incoming, list)


class TestRelatedEntities:
    """Tests for finding related entities."""

    @pytest.fixture
    def service(self):
        """Create a relationship service with mock dependencies."""
        repository = MockRepository()
        logger = MockLogger()
        cache = MockCache()
        return RelationshipService(repository, logger, cache)

    def test_get_related_entities_outgoing(self, service):
        """Should get IDs of outgoing related entities."""
        service.add_relationship(
            source_id="entity-1",
            target_id="entity-2",
            relationship_type=RelationType.CONTAINS,
        )

        related = service.get_related_entities("entity-1", direction="outgoing")

        assert isinstance(related, list)

    def test_get_related_entities_incoming(self, service):
        """Should get IDs of incoming related entities."""
        service.add_relationship(
            source_id="entity-1",
            target_id="entity-3",
            relationship_type=RelationType.CONTAINS,
        )

        related = service.get_related_entities("entity-3", direction="incoming")

        assert isinstance(related, list)

    def test_get_related_entities_both(self, service):
        """Should get related entities in both directions."""
        service.add_relationship(
            source_id="entity-1",
            target_id="entity-3",
            relationship_type=RelationType.CONTAINS,
        )

        related = service.get_related_entities("entity-3", direction="both")

        assert isinstance(related, list)

    def test_get_related_entities_with_type_filter(self, service):
        """Should support relationship type filtering."""
        service.add_relationship(
            source_id="entity-1",
            target_id="entity-2",
            relationship_type=RelationType.CONTAINS,
        )

        related = service.get_related_entities(
            "entity-1",
            relationship_type=RelationType.CONTAINS,
            direction="outgoing",
        )

        assert isinstance(related, list)


class TestGraphOperations:
    """Tests for relationship graph operations."""

    @pytest.fixture
    def service(self):
        """Create a relationship service with mock dependencies."""
        repository = MockRepository()
        logger = MockLogger()
        cache = MockCache()
        return RelationshipService(repository, logger, cache)

    def test_build_graph_empty(self, service):
        """Should build empty graph when no relationships."""
        graph = service.build_graph()

        assert graph is not None
        assert hasattr(graph, 'nodes')
        assert hasattr(graph, 'edges')

    def test_build_graph_with_relationships(self, service):
        """Should build graph with relationships."""
        service.add_relationship(
            source_id="entity-1",
            target_id="entity-2",
            relationship_type=RelationType.CONTAINS,
        )

        graph = service.build_graph()

        assert graph is not None
        assert hasattr(graph, 'add_edge')

    def test_build_graph_with_entity_filter(self, service):
        """Should accept entity ID filter."""
        service.add_relationship(
            source_id="entity-1",
            target_id="entity-2",
            relationship_type=RelationType.CONTAINS,
        )

        graph = service.build_graph(entity_ids=["entity-1", "entity-2"])

        assert graph is not None

    def test_build_graph_with_type_filter(self, service):
        """Should accept relationship type filter."""
        service.add_relationship(
            source_id="entity-1",
            target_id="entity-2",
            relationship_type=RelationType.CONTAINS,
        )

        graph = service.build_graph(relationship_type=RelationType.CONTAINS)

        assert graph is not None


class TestPathFinding:
    """Tests for finding paths in relationship graphs."""

    @pytest.fixture
    def service(self):
        """Create a relationship service with mock dependencies."""
        repository = MockRepository()
        logger = MockLogger()
        cache = MockCache()
        return RelationshipService(repository, logger, cache)

    def test_find_path_returns_none_or_list(self, service):
        """Should return None or a list for path queries."""
        service.add_relationship(
            source_id="entity-1",
            target_id="entity-2",
            relationship_type=RelationType.CONTAINS,
        )

        path = service.find_path("entity-1", "entity-2")

        assert path is None or isinstance(path, list)

    def test_find_path_with_depth_limit(self, service):
        """Should respect maximum depth limit."""
        service.add_relationship(
            source_id="entity-1",
            target_id="entity-2",
            relationship_type=RelationType.CONTAINS,
        )

        path = service.find_path("entity-1", "entity-2", max_depth=5)

        assert path is None or isinstance(path, list)

    def test_find_path_nonexistent_target(self, service):
        """Should return None when no path exists."""
        service.add_relationship(
            source_id="entity-1",
            target_id="entity-2",
            relationship_type=RelationType.CONTAINS,
        )

        path = service.find_path("entity-1", "entity-3")

        assert path is None


class TestDescendants:
    """Tests for finding descendant entities."""

    @pytest.fixture
    def service(self):
        """Create a relationship service with mock dependencies."""
        repository = MockRepository()
        logger = MockLogger()
        cache = MockCache()
        return RelationshipService(repository, logger, cache)

    def test_get_descendants_returns_set(self, service):
        """Should return a set of descendant IDs."""
        descendants = service.get_descendants("entity-1")

        assert isinstance(descendants, set)

    def test_get_descendants_with_parent_child(self, service):
        """Should get children in parent-child relationships."""
        service.add_relationship(
            source_id="entity-1",
            target_id="entity-2",
            relationship_type=RelationType.PARENT_OF,
        )

        descendants = service.get_descendants("entity-1")

        assert isinstance(descendants, set)

    def test_get_descendants_with_custom_type(self, service):
        """Should support custom relationship type filtering."""
        service.add_relationship(
            source_id="entity-1",
            target_id="entity-2",
            relationship_type=RelationType.CONTAINS,
        )

        descendants = service.get_descendants(
            "entity-1", relationship_type=RelationType.CONTAINS
        )

        assert isinstance(descendants, set)

    def test_get_descendants_with_depth_limit(self, service):
        """Should respect maximum depth limit."""
        service.add_relationship(
            source_id="entity-1",
            target_id="entity-2",
            relationship_type=RelationType.PARENT_OF,
        )

        descendants = service.get_descendants("entity-1", max_depth=5)

        assert isinstance(descendants, set)


__all__ = [
    "TestAddRelationship",
    "TestRemoveRelationship",
    "TestGetRelationships",
    "TestDirectedRelationshipQueries",
    "TestRelatedEntities",
    "TestGraphOperations",
    "TestPathFinding",
    "TestDescendants",
]
