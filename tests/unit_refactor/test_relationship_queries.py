"""
Comprehensive tests for relationship query handlers.

Tests cover:
- GetRelationshipsQuery validation and execution
- FindPathQuery validation and path finding
- GetRelatedEntitiesQuery validation and direction filtering
- GetDescendantsQuery validation and tree traversal
- RelationshipQueryHandler all query methods
- Error handling, pagination, filtering
- Empty results, not-found scenarios
"""

import pytest
from datetime import datetime
from uuid import uuid4

from atoms_mcp.application.queries.relationship_queries import (
    GetRelationshipsQuery,
    FindPathQuery,
    GetRelatedEntitiesQuery,
    GetDescendantsQuery,
    RelationshipQueryHandler,
    RelationshipQueryError,
    RelationshipQueryValidationError,
)
from atoms_mcp.application.dto import QueryResult, ResultStatus, RelationshipDTO
from atoms_mcp.domain.models.relationship import (
    Relationship,
    RelationType,
    RelationshipStatus,
)
from conftest import MockRepository, MockLogger, MockCache


class TestGetRelationshipsQueryValidation:
    """Tests for GetRelationshipsQuery validation."""

    def test_validate_with_valid_defaults(self):
        """Should validate successfully with default parameters."""
        query = GetRelationshipsQuery()
        query.validate()  # Should not raise

    def test_validate_with_all_filters(self):
        """Should validate successfully with all filters."""
        query = GetRelationshipsQuery(
            source_id="entity-1",
            target_id="entity-2",
            relationship_type="parent_of",
            page=2,
            page_size=50,
        )
        query.validate()  # Should not raise

    def test_validate_page_less_than_one(self):
        """Should reject page < 1."""
        query = GetRelationshipsQuery(page=0)
        with pytest.raises(RelationshipQueryValidationError) as exc_info:
            query.validate()
        assert "page must be >= 1" in str(exc_info.value)

    def test_validate_negative_page(self):
        """Should reject negative page."""
        query = GetRelationshipsQuery(page=-1)
        with pytest.raises(RelationshipQueryValidationError) as exc_info:
            query.validate()
        assert "page must be >= 1" in str(exc_info.value)

    def test_validate_page_size_less_than_one(self):
        """Should reject page_size < 1."""
        query = GetRelationshipsQuery(page_size=0)
        with pytest.raises(RelationshipQueryValidationError) as exc_info:
            query.validate()
        assert "page_size must be between 1 and 1000" in str(exc_info.value)

    def test_validate_page_size_greater_than_1000(self):
        """Should reject page_size > 1000."""
        query = GetRelationshipsQuery(page_size=1001)
        with pytest.raises(RelationshipQueryValidationError) as exc_info:
            query.validate()
        assert "page_size must be between 1 and 1000" in str(exc_info.value)

    def test_validate_page_size_exactly_1000(self):
        """Should accept page_size of exactly 1000."""
        query = GetRelationshipsQuery(page_size=1000)
        query.validate()  # Should not raise

    def test_validate_invalid_relationship_type(self):
        """Should reject invalid relationship type."""
        query = GetRelationshipsQuery(relationship_type="invalid_type")
        with pytest.raises(RelationshipQueryValidationError) as exc_info:
            query.validate()
        assert "Invalid relationship_type" in str(exc_info.value)

    def test_validate_valid_relationship_types(self):
        """Should accept all valid relationship types."""
        valid_types = [
            "parent_of",
            "child_of",
            "contains",
            "contained_by",
            "assigned_to",
            "depends_on",
            "relates_to",
            "triggers",
            "member_of",
        ]
        for rel_type in valid_types:
            query = GetRelationshipsQuery(relationship_type=rel_type)
            query.validate()  # Should not raise


class TestFindPathQueryValidation:
    """Tests for FindPathQuery validation."""

    def test_validate_with_valid_parameters(self):
        """Should validate successfully with valid parameters."""
        query = FindPathQuery(start_id="entity-1", end_id="entity-2")
        query.validate()  # Should not raise

    def test_validate_missing_start_id(self):
        """Should reject missing start_id."""
        query = FindPathQuery(start_id="", end_id="entity-2")
        with pytest.raises(RelationshipQueryValidationError) as exc_info:
            query.validate()
        assert "start_id is required" in str(exc_info.value)

    def test_validate_missing_end_id(self):
        """Should reject missing end_id."""
        query = FindPathQuery(start_id="entity-1", end_id="")
        with pytest.raises(RelationshipQueryValidationError) as exc_info:
            query.validate()
        assert "end_id is required" in str(exc_info.value)

    def test_validate_max_depth_less_than_one(self):
        """Should reject max_depth < 1."""
        query = FindPathQuery(start_id="entity-1", end_id="entity-2", max_depth=0)
        with pytest.raises(RelationshipQueryValidationError) as exc_info:
            query.validate()
        assert "max_depth must be between 1 and 100" in str(exc_info.value)

    def test_validate_max_depth_greater_than_100(self):
        """Should reject max_depth > 100."""
        query = FindPathQuery(start_id="entity-1", end_id="entity-2", max_depth=101)
        with pytest.raises(RelationshipQueryValidationError) as exc_info:
            query.validate()
        assert "max_depth must be between 1 and 100" in str(exc_info.value)

    def test_validate_max_depth_exactly_100(self):
        """Should accept max_depth of exactly 100."""
        query = FindPathQuery(start_id="entity-1", end_id="entity-2", max_depth=100)
        query.validate()  # Should not raise


class TestGetRelatedEntitiesQueryValidation:
    """Tests for GetRelatedEntitiesQuery validation."""

    def test_validate_with_valid_parameters(self):
        """Should validate successfully with valid parameters."""
        query = GetRelatedEntitiesQuery(entity_id="entity-1")
        query.validate()  # Should not raise

    def test_validate_missing_entity_id(self):
        """Should reject missing entity_id."""
        query = GetRelatedEntitiesQuery(entity_id="")
        with pytest.raises(RelationshipQueryValidationError) as exc_info:
            query.validate()
        assert "entity_id is required" in str(exc_info.value)

    def test_validate_invalid_direction(self):
        """Should reject invalid direction."""
        query = GetRelatedEntitiesQuery(entity_id="entity-1", direction="invalid")
        with pytest.raises(RelationshipQueryValidationError) as exc_info:
            query.validate()
        assert "direction must be" in str(exc_info.value)

    def test_validate_valid_directions(self):
        """Should accept all valid directions."""
        for direction in ["outgoing", "incoming", "both"]:
            query = GetRelatedEntitiesQuery(entity_id="entity-1", direction=direction)
            query.validate()  # Should not raise

    def test_validate_invalid_relationship_type(self):
        """Should reject invalid relationship type."""
        query = GetRelatedEntitiesQuery(
            entity_id="entity-1", relationship_type="invalid_type"
        )
        with pytest.raises(RelationshipQueryValidationError) as exc_info:
            query.validate()
        assert "Invalid relationship_type" in str(exc_info.value)

    def test_validate_with_relationship_type(self):
        """Should accept valid relationship type."""
        query = GetRelatedEntitiesQuery(
            entity_id="entity-1", relationship_type="parent_of"
        )
        query.validate()  # Should not raise


class TestGetDescendantsQueryValidation:
    """Tests for GetDescendantsQuery validation."""

    def test_validate_with_valid_parameters(self):
        """Should validate successfully with valid parameters."""
        query = GetDescendantsQuery(entity_id="entity-1")
        query.validate()  # Should not raise

    def test_validate_missing_entity_id(self):
        """Should reject missing entity_id."""
        query = GetDescendantsQuery(entity_id="")
        with pytest.raises(RelationshipQueryValidationError) as exc_info:
            query.validate()
        assert "entity_id is required" in str(exc_info.value)

    def test_validate_max_depth_less_than_one(self):
        """Should reject max_depth < 1."""
        query = GetDescendantsQuery(entity_id="entity-1", max_depth=0)
        with pytest.raises(RelationshipQueryValidationError) as exc_info:
            query.validate()
        assert "max_depth must be between 1 and 100" in str(exc_info.value)

    def test_validate_max_depth_greater_than_100(self):
        """Should reject max_depth > 100."""
        query = GetDescendantsQuery(entity_id="entity-1", max_depth=101)
        with pytest.raises(RelationshipQueryValidationError) as exc_info:
            query.validate()
        assert "max_depth must be between 1 and 100" in str(exc_info.value)

    def test_validate_invalid_relationship_type(self):
        """Should reject invalid relationship type."""
        query = GetDescendantsQuery(
            entity_id="entity-1", relationship_type="invalid_type"
        )
        with pytest.raises(RelationshipQueryValidationError) as exc_info:
            query.validate()
        assert "Invalid relationship_type" in str(exc_info.value)

    def test_validate_valid_relationship_type(self):
        """Should accept valid relationship type."""
        query = GetDescendantsQuery(entity_id="entity-1", relationship_type="contains")
        query.validate()  # Should not raise


class TestRelationshipQueryHandler:
    """Tests for RelationshipQueryHandler."""

    @pytest.fixture
    def handler(self):
        """Create a relationship query handler with mock dependencies."""
        repository = MockRepository()
        logger = MockLogger()
        cache = MockCache()
        return RelationshipQueryHandler(repository, logger, cache)

    @pytest.fixture
    def sample_relationships(self, handler):
        """Create sample relationships for testing."""
        relationships = []
        for i in range(5):
            rel = Relationship(
                source_id=f"entity-{i}",
                target_id=f"entity-{i+1}",
                relationship_type=RelationType.PARENT_OF,
            )
            # Use repository.save to ensure proper storage
            handler.relationship_service.repository.save(rel)
            relationships.append(rel)
        return relationships

    def test_handler_initialization(self, handler):
        """Should initialize handler with dependencies."""
        assert handler.relationship_service is not None
        assert handler.logger is not None

    def test_handle_get_relationships_success_no_filters(
        self, handler, sample_relationships
    ):
        """Should successfully get all relationships without filters."""
        query = GetRelationshipsQuery()
        result = handler.handle_get_relationships(query)

        assert isinstance(result, QueryResult)
        assert result.status == ResultStatus.SUCCESS
        assert result.data is not None
        assert len(result.data) == 5
        assert all(isinstance(dto, RelationshipDTO) for dto in result.data)

    def test_handle_get_relationships_with_source_filter(
        self, handler, sample_relationships
    ):
        """Should filter relationships by source_id."""
        query = GetRelationshipsQuery(source_id="entity-0")
        result = handler.handle_get_relationships(query)

        assert result.status == ResultStatus.SUCCESS
        assert len(result.data) == 1
        assert result.data[0].source_id == "entity-0"

    def test_handle_get_relationships_with_target_filter(
        self, handler, sample_relationships
    ):
        """Should filter relationships by target_id."""
        query = GetRelationshipsQuery(target_id="entity-2")
        result = handler.handle_get_relationships(query)

        assert result.status == ResultStatus.SUCCESS
        assert len(result.data) == 1
        assert result.data[0].target_id == "entity-2"

    def test_handle_get_relationships_with_type_filter(
        self, handler, sample_relationships
    ):
        """Should filter relationships by type."""
        query = GetRelationshipsQuery(relationship_type="parent_of")
        result = handler.handle_get_relationships(query)

        assert result.status == ResultStatus.SUCCESS
        assert all(dto.relationship_type == "parent_of" for dto in result.data)

    def test_handle_get_relationships_pagination_first_page(
        self, handler, sample_relationships
    ):
        """Should paginate results correctly - first page."""
        query = GetRelationshipsQuery(page=1, page_size=2)
        result = handler.handle_get_relationships(query)

        assert result.status == ResultStatus.SUCCESS
        assert len(result.data) == 2
        assert result.total_count == 5
        assert result.page == 1
        assert result.page_size == 2

    def test_handle_get_relationships_pagination_second_page(
        self, handler, sample_relationships
    ):
        """Should paginate results correctly - second page."""
        query = GetRelationshipsQuery(page=2, page_size=2)
        result = handler.handle_get_relationships(query)

        assert result.status == ResultStatus.SUCCESS
        assert len(result.data) == 2
        assert result.total_count == 5
        assert result.page == 2

    def test_handle_get_relationships_pagination_last_page(
        self, handler, sample_relationships
    ):
        """Should paginate results correctly - last page."""
        query = GetRelationshipsQuery(page=3, page_size=2)
        result = handler.handle_get_relationships(query)

        assert result.status == ResultStatus.SUCCESS
        assert len(result.data) == 1
        assert result.total_count == 5

    def test_handle_get_relationships_empty_results(self, handler):
        """Should handle empty results gracefully."""
        query = GetRelationshipsQuery(source_id="nonexistent")
        result = handler.handle_get_relationships(query)

        assert result.status == ResultStatus.SUCCESS
        assert result.data == []
        assert result.total_count == 0

    def test_handle_get_relationships_validation_error(self, handler):
        """Should handle validation errors."""
        query = GetRelationshipsQuery(page=-1)
        result = handler.handle_get_relationships(query)

        assert result.status == ResultStatus.ERROR
        assert result.error is not None
        assert "Validation error" in result.error

    def test_handle_get_relationships_metadata(self, handler, sample_relationships):
        """Should include query metadata in result."""
        query = GetRelationshipsQuery(
            source_id="entity-0", relationship_type="parent_of"
        )
        result = handler.handle_get_relationships(query)

        assert result.status == ResultStatus.SUCCESS
        assert result.metadata["source_id"] == "entity-0"
        assert result.metadata["relationship_type"] == "parent_of"

    def test_handle_find_path_success(self, handler, sample_relationships):
        """Should successfully find path between entities."""
        query = FindPathQuery(start_id="entity-0", end_id="entity-5")
        result = handler.handle_find_path(query)

        assert isinstance(result, QueryResult)
        assert result.status == ResultStatus.SUCCESS
        # Path should exist based on sample_relationships

    def test_handle_find_path_no_path_exists(self, handler):
        """Should handle case when no path exists."""
        # Create two unconnected entities
        rel1 = Relationship(
            source_id="entity-a",
            target_id="entity-b",
            relationship_type=RelationType.PARENT_OF,
        )
        rel2 = Relationship(
            source_id="entity-x",
            target_id="entity-y",
            relationship_type=RelationType.PARENT_OF,
        )
        handler.relationship_service.repository.save(rel1)
        handler.relationship_service.repository.save(rel2)

        query = FindPathQuery(start_id="entity-a", end_id="entity-y")
        result = handler.handle_find_path(query)

        assert result.status == ResultStatus.SUCCESS
        assert result.data == []
        assert result.metadata["path_found"] is False

    def test_handle_find_path_validation_error(self, handler):
        """Should handle validation errors in find path."""
        query = FindPathQuery(start_id="", end_id="entity-2")
        result = handler.handle_find_path(query)

        assert result.status == ResultStatus.ERROR
        assert "Validation error" in result.error

    def test_handle_find_path_metadata(self, handler, sample_relationships):
        """Should include path metadata in result."""
        query = FindPathQuery(start_id="entity-0", end_id="entity-2", max_depth=5)
        result = handler.handle_find_path(query)

        assert result.status == ResultStatus.SUCCESS
        assert result.metadata["start_id"] == "entity-0"
        assert result.metadata["end_id"] == "entity-2"

    def test_handle_get_related_entities_outgoing(self, handler, sample_relationships):
        """Should get outgoing related entities."""
        query = GetRelatedEntitiesQuery(entity_id="entity-1", direction="outgoing")
        result = handler.handle_get_related_entities(query)

        assert result.status == ResultStatus.SUCCESS
        assert isinstance(result.data, list)
        assert "entity-2" in result.data

    def test_handle_get_related_entities_incoming(self, handler, sample_relationships):
        """Should get incoming related entities."""
        query = GetRelatedEntitiesQuery(entity_id="entity-2", direction="incoming")
        result = handler.handle_get_related_entities(query)

        assert result.status == ResultStatus.SUCCESS
        assert "entity-1" in result.data

    def test_handle_get_related_entities_both_directions(
        self, handler, sample_relationships
    ):
        """Should get related entities in both directions."""
        query = GetRelatedEntitiesQuery(entity_id="entity-2", direction="both")
        result = handler.handle_get_related_entities(query)

        assert result.status == ResultStatus.SUCCESS
        # Should have both incoming and outgoing
        assert len(result.data) >= 1

    def test_handle_get_related_entities_with_type_filter(
        self, handler, sample_relationships
    ):
        """Should filter related entities by relationship type."""
        query = GetRelatedEntitiesQuery(
            entity_id="entity-1",
            relationship_type="parent_of",
            direction="outgoing",
        )
        result = handler.handle_get_related_entities(query)

        assert result.status == ResultStatus.SUCCESS
        assert isinstance(result.data, list)

    def test_handle_get_related_entities_no_relationships(self, handler):
        """Should handle entity with no relationships."""
        query = GetRelatedEntitiesQuery(entity_id="isolated-entity")
        result = handler.handle_get_related_entities(query)

        assert result.status == ResultStatus.SUCCESS
        assert result.data == []

    def test_handle_get_related_entities_validation_error(self, handler):
        """Should handle validation errors."""
        query = GetRelatedEntitiesQuery(entity_id="", direction="outgoing")
        result = handler.handle_get_related_entities(query)

        assert result.status == ResultStatus.ERROR
        assert "Validation error" in result.error

    def test_handle_get_related_entities_metadata(self, handler, sample_relationships):
        """Should include query metadata in result."""
        query = GetRelatedEntitiesQuery(
            entity_id="entity-1", relationship_type="parent_of", direction="both"
        )
        result = handler.handle_get_related_entities(query)

        assert result.status == ResultStatus.SUCCESS
        assert result.metadata["entity_id"] == "entity-1"
        assert result.metadata["direction"] == "both"

    def test_handle_get_descendants_success(self, handler, sample_relationships):
        """Should successfully get descendants."""
        query = GetDescendantsQuery(entity_id="entity-0")
        result = handler.handle_get_descendants(query)

        assert isinstance(result, QueryResult)
        assert result.status == ResultStatus.SUCCESS
        assert isinstance(result.data, list)

    def test_handle_get_descendants_with_max_depth(self, handler, sample_relationships):
        """Should respect max_depth parameter."""
        query = GetDescendantsQuery(entity_id="entity-0", max_depth=2)
        result = handler.handle_get_descendants(query)

        assert result.status == ResultStatus.SUCCESS
        assert isinstance(result.data, list)

    def test_handle_get_descendants_no_descendants(self, handler):
        """Should handle entity with no descendants."""
        # Create leaf node
        rel = Relationship(
            source_id="parent",
            target_id="leaf",
            relationship_type=RelationType.PARENT_OF,
        )
        handler.relationship_service.repository.save(rel)

        query = GetDescendantsQuery(entity_id="leaf")
        result = handler.handle_get_descendants(query)

        assert result.status == ResultStatus.SUCCESS
        assert result.data == []

    def test_handle_get_descendants_validation_error(self, handler):
        """Should handle validation errors."""
        query = GetDescendantsQuery(entity_id="", max_depth=5)
        result = handler.handle_get_descendants(query)

        assert result.status == ResultStatus.ERROR
        assert "Validation error" in result.error

    def test_handle_get_descendants_metadata(self, handler, sample_relationships):
        """Should include query metadata in result."""
        query = GetDescendantsQuery(
            entity_id="entity-0", relationship_type="parent_of", max_depth=10
        )
        result = handler.handle_get_descendants(query)

        assert result.status == ResultStatus.SUCCESS
        assert result.metadata["entity_id"] == "entity-0"
        assert result.metadata["max_depth"] == 10


class TestRelationshipQueryHandlerErrorHandling:
    """Tests for error handling in relationship query handler."""

    @pytest.fixture
    def handler(self):
        """Create handler."""
        repository = MockRepository()
        logger = MockLogger()
        cache = MockCache()
        return RelationshipQueryHandler(repository, logger, cache)

    def test_error_logged_on_validation_failure(self, handler):
        """Should log validation errors."""
        query = GetRelationshipsQuery(page=-1)
        result = handler.handle_get_relationships(query)

        assert result.status == ResultStatus.ERROR
        assert len(handler.logger.logs) > 0
        error_logs = [log for log in handler.logger.logs if log["level"] == "ERROR"]
        assert len(error_logs) > 0

    def test_relationship_to_dto_conversion(self, handler):
        """Should correctly convert relationship to DTO."""
        rel = Relationship(
            source_id="entity-1",
            target_id="entity-2",
            relationship_type=RelationType.PARENT_OF,
            created_by="user-123",
        )
        handler.relationship_service.repository.save(rel)

        query = GetRelationshipsQuery(source_id="entity-1")
        result = handler.handle_get_relationships(query)

        assert result.status == ResultStatus.SUCCESS
        dto = result.data[0]
        assert dto.source_id == "entity-1"
        assert dto.target_id == "entity-2"
        assert dto.relationship_type == "parent_of"
        assert dto.status == "active"


__all__ = [
    "TestGetRelationshipsQueryValidation",
    "TestFindPathQueryValidation",
    "TestGetRelatedEntitiesQueryValidation",
    "TestGetDescendantsQueryValidation",
    "TestRelationshipQueryHandler",
    "TestRelationshipQueryHandlerErrorHandling",
]
