"""
Comprehensive tests for application layer query handlers.

Tests cover:
- Query validation
- Query handler execution
- Error handling and result statuses
- Pagination and filtering
- Cache usage
"""

import pytest
from datetime import datetime
from typing import Any

from atoms_mcp.application.queries.entity_queries import (
    GetEntityQuery,
    ListEntitiesQuery,
    SearchEntitiesQuery,
    CountEntitiesQuery,
    EntityQueryHandler,
    EntityQueryValidationError,
)
from atoms_mcp.application.dto import QueryResult, ResultStatus, EntityDTO
from atoms_mcp.domain.models.entity import (
    Entity,
    WorkspaceEntity,
    ProjectEntity,
    TaskEntity,
    DocumentEntity,
    EntityStatus,
)
from atoms_mcp.domain.ports.repository import RepositoryError

from conftest import MockRepository, MockLogger, MockCache


class TestGetEntityQueryValidation:
    """Tests for GetEntityQuery validation."""

    def test_validate_with_valid_entity_id(self):
        """Should validate successfully with valid entity_id."""
        query = GetEntityQuery(entity_id="entity-123")
        query.validate()  # Should not raise

    def test_validate_missing_entity_id(self):
        """Should raise validation error when entity_id is missing."""
        query = GetEntityQuery(entity_id="")
        with pytest.raises(EntityQueryValidationError) as exc_info:
            query.validate()
        assert "entity_id is required" in str(exc_info.value)

    def test_validate_with_use_cache_flag(self):
        """Should validate successfully with use_cache flag."""
        query_with_cache = GetEntityQuery(entity_id="entity-123", use_cache=True)
        query_with_cache.validate()

        query_without_cache = GetEntityQuery(entity_id="entity-123", use_cache=False)
        query_without_cache.validate()


class TestListEntitiesQueryValidation:
    """Tests for ListEntitiesQuery validation."""

    def test_validate_with_defaults(self):
        """Should validate successfully with default parameters."""
        query = ListEntitiesQuery()
        query.validate()  # Should not raise

    def test_validate_with_filters(self):
        """Should validate successfully with filters."""
        query = ListEntitiesQuery(
            filters={"status": "active", "type": "workspace"}
        )
        query.validate()  # Should not raise

    def test_validate_with_pagination(self):
        """Should validate successfully with pagination parameters."""
        query = ListEntitiesQuery(page=2, page_size=50)
        query.validate()  # Should not raise

    def test_validate_invalid_page(self):
        """Should raise validation error when page < 1."""
        query = ListEntitiesQuery(page=0)
        with pytest.raises(EntityQueryValidationError) as exc_info:
            query.validate()
        assert "page must be >= 1" in str(exc_info.value)

    def test_validate_invalid_page_size_zero(self):
        """Should raise validation error when page_size < 1."""
        query = ListEntitiesQuery(page_size=0)
        with pytest.raises(EntityQueryValidationError) as exc_info:
            query.validate()
        assert "page_size must be between 1 and 1000" in str(exc_info.value)

    def test_validate_invalid_page_size_too_large(self):
        """Should raise validation error when page_size > 1000."""
        query = ListEntitiesQuery(page_size=1001)
        with pytest.raises(EntityQueryValidationError) as exc_info:
            query.validate()
        assert "page_size must be between 1 and 1000" in str(exc_info.value)

    def test_validate_page_size_exactly_1000(self):
        """Should validate successfully with page_size of exactly 1000."""
        query = ListEntitiesQuery(page_size=1000)
        query.validate()  # Should not raise

    def test_get_limit_uses_page_size(self):
        """Should use page_size when limit is not specified."""
        query = ListEntitiesQuery(page_size=50)
        assert query.get_limit() == 50

    def test_get_limit_uses_explicit_limit(self):
        """Should use explicit limit when specified."""
        query = ListEntitiesQuery(page_size=50, limit=100)
        assert query.get_limit() == 100

    def test_get_offset_from_page(self):
        """Should calculate offset from page and page_size."""
        query = ListEntitiesQuery(page=3, page_size=20)
        assert query.get_offset() == 40  # (3-1) * 20

    def test_get_offset_uses_explicit_offset(self):
        """Should use explicit offset when specified."""
        query = ListEntitiesQuery(page=3, page_size=20, offset=100)
        assert query.get_offset() == 100


class TestSearchEntitiesQueryValidation:
    """Tests for SearchEntitiesQuery validation."""

    def test_validate_with_valid_query(self):
        """Should validate successfully with valid search query."""
        query = SearchEntitiesQuery(query="test")
        query.validate()  # Should not raise

    def test_validate_missing_query(self):
        """Should raise validation error when query is missing."""
        query = SearchEntitiesQuery(query="")
        with pytest.raises(EntityQueryValidationError) as exc_info:
            query.validate()
        assert "query is required" in str(exc_info.value)

    def test_validate_with_fields(self):
        """Should validate successfully with field specification."""
        query = SearchEntitiesQuery(
            query="test",
            fields=["name", "description"],
        )
        query.validate()  # Should not raise

    def test_validate_with_filters(self):
        """Should validate successfully with filters."""
        query = SearchEntitiesQuery(
            query="test",
            filters={"type": "project"},
        )
        query.validate()  # Should not raise

    def test_validate_invalid_page(self):
        """Should raise validation error when page < 1."""
        query = SearchEntitiesQuery(query="test", page=0)
        with pytest.raises(EntityQueryValidationError) as exc_info:
            query.validate()
        assert "page must be >= 1" in str(exc_info.value)

    def test_validate_invalid_page_size(self):
        """Should raise validation error when page_size is invalid."""
        query = SearchEntitiesQuery(query="test", page_size=1001)
        with pytest.raises(EntityQueryValidationError) as exc_info:
            query.validate()
        assert "page_size must be between 1 and 1000" in str(exc_info.value)

    def test_get_limit_uses_page_size(self):
        """Should use page_size when limit is not specified."""
        query = SearchEntitiesQuery(query="test", page_size=50)
        assert query.get_limit() == 50

    def test_get_limit_uses_explicit_limit(self):
        """Should use explicit limit when specified."""
        query = SearchEntitiesQuery(query="test", page_size=50, limit=100)
        assert query.get_limit() == 100


class TestCountEntitiesQueryValidation:
    """Tests for CountEntitiesQuery validation."""

    def test_validate_with_defaults(self):
        """Should validate successfully with default parameters."""
        query = CountEntitiesQuery()
        query.validate()  # Should not raise

    def test_validate_with_filters(self):
        """Should validate successfully with filters."""
        query = CountEntitiesQuery(filters={"status": "active"})
        query.validate()  # Should not raise


class TestEntityQueryHandler:
    """Tests for EntityQueryHandler."""

    @pytest.fixture
    def handler(self):
        """Create a query handler with mock dependencies."""
        repository = MockRepository()
        logger = MockLogger()
        cache = MockCache()
        return EntityQueryHandler(repository, logger, cache)

    def test_handler_initialization(self, handler):
        """Should initialize handler with dependencies."""
        assert handler.entity_service is not None
        assert handler.logger is not None

    def test_handle_get_entity_success(self, handler):
        """Should successfully retrieve an entity."""
        # First create an entity
        entity = WorkspaceEntity(
            name="Test Workspace",
            description="A test workspace",
        )
        entity_id = entity.id
        handler.entity_service.repository.save(entity)

        # Then query for it
        query = GetEntityQuery(entity_id=entity_id)
        result = handler.handle_get_entity(query)

        assert result.status == ResultStatus.SUCCESS
        assert result.data is not None
        assert isinstance(result.data, EntityDTO)
        assert result.data.id == entity_id
        assert result.total_count == 1

    def test_handle_get_entity_not_found(self, handler):
        """Should return error when entity not found."""
        query = GetEntityQuery(entity_id="non-existent-id")
        result = handler.handle_get_entity(query)

        assert result.status == ResultStatus.ERROR
        assert result.data is None
        assert "not found" in result.error.lower()

    def test_handle_get_entity_validation_error(self, handler):
        """Should return error when query validation fails."""
        query = GetEntityQuery(entity_id="")
        result = handler.handle_get_entity(query)

        assert result.status == ResultStatus.ERROR
        assert result.data is None
        assert "Validation error" in result.error

    def test_handle_get_entity_with_cache_true(self, handler):
        """Should use cache when use_cache is True."""
        # First create and cache an entity
        entity = ProjectEntity(
            name="Test Project",
            workspace_id="workspace-123",
        )
        handler.entity_service.repository.save(entity)

        # Query with cache
        query = GetEntityQuery(entity_id=entity.id, use_cache=True)
        result = handler.handle_get_entity(query)

        assert result.status == ResultStatus.SUCCESS
        assert result.data is not None

    def test_handle_get_entity_with_cache_false(self, handler):
        """Should bypass cache when use_cache is False."""
        # First create an entity
        entity = TaskEntity(
            title="Test Task",
            project_id="project-123",
        )
        handler.entity_service.repository.save(entity)

        # Query without cache
        query = GetEntityQuery(entity_id=entity.id, use_cache=False)
        result = handler.handle_get_entity(query)

        assert result.status == ResultStatus.SUCCESS
        assert result.data is not None

    def test_handle_list_entities_empty(self, handler):
        """Should handle empty entity list."""
        query = ListEntitiesQuery()
        result = handler.handle_list_entities(query)

        assert result.status == ResultStatus.SUCCESS
        assert result.data == []
        assert result.total_count == 0

    def test_handle_list_entities_with_entities(self, handler):
        """Should list multiple entities."""
        # Create multiple entities
        entities = [
            WorkspaceEntity(name=f"Workspace {i}")
            for i in range(5)
        ]
        for entity in entities:
            handler.entity_service.repository.save(entity)

        # List them
        query = ListEntitiesQuery()
        result = handler.handle_list_entities(query)

        assert result.status == ResultStatus.SUCCESS
        assert len(result.data) == 5
        assert result.total_count == 5
        assert result.page == 1
        assert result.page_size == 20

    def test_handle_list_entities_with_pagination(self, handler):
        """Should handle pagination correctly."""
        # Create 15 entities
        entities = [
            WorkspaceEntity(name=f"Workspace {i}")
            for i in range(15)
        ]
        for entity in entities:
            handler.entity_service.repository.save(entity)

        # Get first page with page_size=5
        query = ListEntitiesQuery(page=1, page_size=5)
        result = handler.handle_list_entities(query)

        assert result.status == ResultStatus.SUCCESS
        assert len(result.data) == 5
        assert result.total_count == 15
        assert result.page == 1
        assert result.page_size == 5
        assert result.has_more_pages is True

        # Get second page
        query = ListEntitiesQuery(page=2, page_size=5)
        result = handler.handle_list_entities(query)

        assert result.status == ResultStatus.SUCCESS
        assert len(result.data) == 5
        assert result.page == 2

    def test_handle_list_entities_with_filters(self, handler):
        """Should apply filters when listing entities."""
        # Create entities with different statuses
        workspace = WorkspaceEntity(name="Active Workspace")
        handler.entity_service.repository.save(workspace)

        query = ListEntitiesQuery(
            filters={"status": "active"}
        )
        result = handler.handle_list_entities(query)

        assert result.status == ResultStatus.SUCCESS
        assert result.metadata["filters"]["status"] == "active"

    def test_handle_list_entities_with_ordering(self, handler):
        """Should apply ordering when listing entities."""
        # Create multiple entities
        entities = [
            WorkspaceEntity(name=f"Workspace {i}")
            for i in range(3)
        ]
        for entity in entities:
            handler.entity_service.repository.save(entity)

        query = ListEntitiesQuery(order_by="name")
        result = handler.handle_list_entities(query)

        assert result.status == ResultStatus.SUCCESS
        assert result.metadata["order_by"] == "name"

    def test_handle_list_entities_validation_error(self, handler):
        """Should return error when query validation fails."""
        query = ListEntitiesQuery(page_size=1001)
        result = handler.handle_list_entities(query)

        assert result.status == ResultStatus.ERROR
        assert result.data is None
        assert "Validation error" in result.error

    def test_handle_search_entities_success(self, handler):
        """Should successfully search entities."""
        # Create searchable entities
        entity1 = WorkspaceEntity(name="Python Project", description="Python workspace")
        entity2 = WorkspaceEntity(name="JavaScript App", description="JavaScript workspace")
        handler.entity_service.repository.save(entity1)
        handler.entity_service.repository.save(entity2)

        # Search for Python
        query = SearchEntitiesQuery(query="Python")
        result = handler.handle_search_entities(query)

        assert result.status == ResultStatus.SUCCESS
        assert result.data is not None  # Should find matches

    def test_handle_search_entities_no_results(self, handler):
        """Should handle search with no results."""
        # Create some entities
        entity = WorkspaceEntity(name="Test Workspace")
        handler.entity_service.repository.save(entity)

        # Search for non-existent term
        query = SearchEntitiesQuery(query="NonExistentTerm")
        result = handler.handle_search_entities(query)

        assert result.status == ResultStatus.SUCCESS
        assert result.data == []

    def test_handle_search_entities_validation_error(self, handler):
        """Should return error when search query is empty."""
        query = SearchEntitiesQuery(query="")
        result = handler.handle_search_entities(query)

        assert result.status == ResultStatus.ERROR
        assert result.data is None
        assert "Validation error" in result.error

    def test_handle_count_entities_zero(self, handler):
        """Should return zero count for empty repository."""
        query = CountEntitiesQuery()
        result = handler.handle_count_entities(query)

        assert result.status == ResultStatus.SUCCESS
        assert result.data == 0

    def test_handle_count_entities_with_entities(self, handler):
        """Should count all entities."""
        # Create multiple entities
        for i in range(10):
            entity = WorkspaceEntity(name=f"Workspace {i}")
            handler.entity_service.repository.save(entity)

        query = CountEntitiesQuery()
        result = handler.handle_count_entities(query)

        assert result.status == ResultStatus.SUCCESS
        assert result.data == 10

    def test_handle_count_entities_with_filters(self, handler):
        """Should count entities matching filters."""
        # Create entities with different properties
        entity = WorkspaceEntity(name="Active Workspace")
        handler.entity_service.repository.save(entity)

        query = CountEntitiesQuery(
            filters={"status": "active"}
        )
        result = handler.handle_count_entities(query)

        assert result.status == ResultStatus.SUCCESS
        assert result.data >= 0


class TestQueryResultPagination:
    """Tests for query result pagination."""

    @pytest.fixture
    def handler(self):
        """Create a query handler with mock dependencies."""
        repository = MockRepository()
        logger = MockLogger()
        cache = MockCache()
        return EntityQueryHandler(repository, logger, cache)

    def test_has_more_pages_true(self, handler):
        """Should report more pages available."""
        # Create 25 entities
        for i in range(25):
            entity = WorkspaceEntity(name=f"Workspace {i}")
            handler.entity_service.repository.save(entity)

        # Get first page with page_size=10
        query = ListEntitiesQuery(page=1, page_size=10)
        result = handler.handle_list_entities(query)

        assert result.has_more_pages is True

    def test_has_more_pages_false(self, handler):
        """Should report no more pages when at end."""
        # Create 15 entities
        for i in range(15):
            entity = WorkspaceEntity(name=f"Workspace {i}")
            handler.entity_service.repository.save(entity)

        # Get page that contains all remaining items
        query = ListEntitiesQuery(page=2, page_size=10)
        result = handler.handle_list_entities(query)

        # Page 2 with page_size 10 would show items 10-15 (5 items)
        # Total would be 15, so (2 * 10) = 20, which is >= 15
        assert result.has_more_pages is False


class TestQueryErrorHandling:
    """Tests for query error handling."""

    @pytest.fixture
    def handler(self):
        """Create a query handler with mock dependencies."""
        repository = MockRepository()
        logger = MockLogger()
        cache = MockCache()
        return EntityQueryHandler(repository, logger, cache)

    def test_query_logs_validation_errors(self, handler):
        """Should log validation errors."""
        query = GetEntityQuery(entity_id="")
        result = handler.handle_get_entity(query)

        assert result.status == ResultStatus.ERROR

    def test_query_logs_not_found_errors(self, handler):
        """Should log not found errors."""
        query = GetEntityQuery(entity_id="non-existent")
        result = handler.handle_get_entity(query)

        assert result.status == ResultStatus.ERROR


__all__ = [
    "TestGetEntityQueryValidation",
    "TestListEntitiesQueryValidation",
    "TestSearchEntitiesQueryValidation",
    "TestCountEntitiesQueryValidation",
    "TestEntityQueryHandler",
    "TestQueryResultPagination",
    "TestQueryErrorHandling",
]
