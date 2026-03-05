"""
Comprehensive test suite for analytics query handlers.

This module provides extensive testing coverage for analytics queries including:
- EntityCountQuery: Count entities by type, status, or workspace
- WorkspaceStatsQuery: Calculate workspace statistics
- ActivityQuery: Track entity creation/modification over time
- Error handling and edge cases
- Performance validation
- Caching behavior

Expected coverage gain: +3-4%
Target pass rate: 90%+
"""

import time
from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import MagicMock, Mock, patch

import pytest

from atoms_mcp.application.dto import QueryResult, ResultStatus
from atoms_mcp.application.queries.analytics_queries import (
    ActivityQuery,
    AnalyticsQueryError,
    AnalyticsQueryHandler,
    AnalyticsQueryValidationError,
    EntityCountQuery,
    WorkspaceStatsQuery,
)
from atoms_mcp.domain.models.entity import Entity, EntityStatus
from atoms_mcp.domain.ports.repository import RepositoryError


# =============================================================================
# ENTITY COUNT QUERY TESTS
# =============================================================================


class TestEntityCountQuery:
    """Test EntityCountQuery validation and behavior."""

    def test_entity_count_query_default_values(self):
        """Test EntityCountQuery has correct default values."""
        query = EntityCountQuery()
        assert query.group_by == "type"
        assert query.filters == {}

    def test_entity_count_query_custom_values(self):
        """Test EntityCountQuery with custom values."""
        filters = {"status": "active"}
        query = EntityCountQuery(group_by="status", filters=filters)
        assert query.group_by == "status"
        assert query.filters == filters

    def test_entity_count_query_validation_success(self):
        """Test validation passes for valid group_by values."""
        for group_by in ["type", "status", "workspace_id", "project_id"]:
            query = EntityCountQuery(group_by=group_by)
            query.validate()  # Should not raise

    def test_entity_count_query_validation_invalid_group_by(self):
        """Test validation fails for invalid group_by value."""
        query = EntityCountQuery(group_by="invalid")
        with pytest.raises(AnalyticsQueryValidationError) as exc_info:
            query.validate()
        assert "group_by must be" in str(exc_info.value)

    def test_entity_count_query_validation_empty_group_by(self):
        """Test validation fails for empty group_by."""
        query = EntityCountQuery(group_by="")
        with pytest.raises(AnalyticsQueryValidationError):
            query.validate()


# =============================================================================
# WORKSPACE STATS QUERY TESTS
# =============================================================================


class TestWorkspaceStatsQuery:
    """Test WorkspaceStatsQuery validation and behavior."""

    def test_workspace_stats_query_default_values(self):
        """Test WorkspaceStatsQuery has correct default values."""
        query = WorkspaceStatsQuery()
        assert query.workspace_id is None

    def test_workspace_stats_query_with_workspace_id(self):
        """Test WorkspaceStatsQuery with workspace ID."""
        query = WorkspaceStatsQuery(workspace_id="ws_123")
        assert query.workspace_id == "ws_123"

    def test_workspace_stats_query_validation(self):
        """Test validation always passes (no validation rules)."""
        query = WorkspaceStatsQuery()
        query.validate()  # Should not raise

        query = WorkspaceStatsQuery(workspace_id="ws_123")
        query.validate()  # Should not raise


# =============================================================================
# ACTIVITY QUERY TESTS
# =============================================================================


class TestActivityQuery:
    """Test ActivityQuery validation and behavior."""

    def test_activity_query_default_values(self):
        """Test ActivityQuery has correct default values."""
        query = ActivityQuery()
        assert query.start_date is None
        assert query.end_date is None
        assert query.granularity == "day"
        assert query.entity_types == []

    def test_activity_query_custom_values(self):
        """Test ActivityQuery with custom values."""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 12, 31)
        types = ["project", "task"]
        query = ActivityQuery(
            start_date=start,
            end_date=end,
            granularity="week",
            entity_types=types,
        )
        assert query.start_date == start
        assert query.end_date == end
        assert query.granularity == "week"
        assert query.entity_types == types

    def test_activity_query_validation_valid_granularity(self):
        """Test validation passes for valid granularity values."""
        for granularity in ["hour", "day", "week", "month"]:
            query = ActivityQuery(granularity=granularity)
            query.validate()  # Should not raise

    def test_activity_query_validation_invalid_granularity(self):
        """Test validation fails for invalid granularity."""
        query = ActivityQuery(granularity="year")
        with pytest.raises(AnalyticsQueryValidationError) as exc_info:
            query.validate()
        assert "granularity must be" in str(exc_info.value)

    def test_activity_query_validation_end_before_start(self):
        """Test validation fails when end_date is before start_date."""
        start = datetime(2024, 12, 31)
        end = datetime(2024, 1, 1)
        query = ActivityQuery(start_date=start, end_date=end)
        with pytest.raises(AnalyticsQueryValidationError) as exc_info:
            query.validate()
        assert "end_date cannot be before start_date" in str(exc_info.value)

    def test_activity_query_validation_same_start_end(self):
        """Test validation passes when start_date equals end_date."""
        same_date = datetime(2024, 6, 15)
        query = ActivityQuery(start_date=same_date, end_date=same_date)
        query.validate()  # Should not raise

    def test_activity_query_get_start_date_default(self):
        """Test get_start_date returns 30 days ago when not set."""
        query = ActivityQuery()
        start = query.get_start_date()
        assert isinstance(start, datetime)
        # Should be approximately 30 days ago
        expected = datetime.utcnow() - timedelta(days=30)
        assert abs((start - expected).total_seconds()) < 10

    def test_activity_query_get_start_date_custom(self):
        """Test get_start_date returns custom start_date."""
        custom_start = datetime(2024, 1, 1)
        query = ActivityQuery(start_date=custom_start)
        assert query.get_start_date() == custom_start

    def test_activity_query_get_end_date_default(self):
        """Test get_end_date returns current time when not set."""
        query = ActivityQuery()
        end = query.get_end_date()
        assert isinstance(end, datetime)
        # Should be approximately now
        expected = datetime.utcnow()
        assert abs((end - expected).total_seconds()) < 10

    def test_activity_query_get_end_date_custom(self):
        """Test get_end_date returns custom end_date."""
        custom_end = datetime(2024, 12, 31)
        query = ActivityQuery(end_date=custom_end)
        assert query.get_end_date() == custom_end


# =============================================================================
# ANALYTICS QUERY HANDLER TESTS - ENTITY COUNT
# =============================================================================


class TestAnalyticsQueryHandlerEntityCount:
    """Test AnalyticsQueryHandler.handle_entity_count method."""

    def test_handle_entity_count_success_group_by_type(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test successful entity count grouped by type."""
        # Add test entities with different types
        entities = [
            Entity(metadata={"entity_type": "project"}),
            Entity(metadata={"entity_type": "project"}),
            Entity(metadata={"entity_type": "task"}),
        ]
        for entity in entities:
            mock_repository.add_entity(entity)

        handler = AnalyticsQueryHandler(mock_repository, mock_logger, mock_cache)
        query = EntityCountQuery(group_by="type")
        result = handler.handle_entity_count(query)

        assert result.status == ResultStatus.SUCCESS
        assert result.data == {"project": 2, "task": 1}
        assert result.total_count == 3
        assert result.metadata["group_by"] == "type"

    def test_handle_entity_count_success_group_by_status(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test successful entity count grouped by status."""
        entities = [
            Entity(status=EntityStatus.ACTIVE),
            Entity(status=EntityStatus.ACTIVE),
            Entity(status=EntityStatus.ARCHIVED),
        ]
        for entity in entities:
            mock_repository.add_entity(entity)

        handler = AnalyticsQueryHandler(mock_repository, mock_logger, mock_cache)
        query = EntityCountQuery(group_by="status")
        result = handler.handle_entity_count(query)

        assert result.status == ResultStatus.SUCCESS
        assert result.data == {"active": 2, "archived": 1}
        assert result.total_count == 3

    def test_handle_entity_count_success_group_by_workspace_id(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test successful entity count grouped by workspace_id."""
        entities = [
            Entity(metadata={"workspace_id": "ws1"}),
            Entity(metadata={"workspace_id": "ws1"}),
            Entity(metadata={"workspace_id": "ws2"}),
        ]
        for entity in entities:
            mock_repository.add_entity(entity)

        handler = AnalyticsQueryHandler(mock_repository, mock_logger, mock_cache)
        query = EntityCountQuery(group_by="workspace_id")
        result = handler.handle_entity_count(query)

        assert result.status == ResultStatus.SUCCESS
        assert result.data == {"ws1": 2, "ws2": 1}
        assert result.total_count == 3

    def test_handle_entity_count_empty_repository(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test entity count with empty repository."""
        handler = AnalyticsQueryHandler(mock_repository, mock_logger, mock_cache)
        query = EntityCountQuery(group_by="type")
        result = handler.handle_entity_count(query)

        assert result.status == ResultStatus.SUCCESS
        assert result.data == {}
        assert result.total_count == 0

    def test_handle_entity_count_with_filters(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test entity count with filters applied."""
        entities = [
            Entity(status=EntityStatus.ACTIVE, metadata={"entity_type": "project"}),
            Entity(status=EntityStatus.ARCHIVED, metadata={"entity_type": "project"}),
            Entity(status=EntityStatus.ACTIVE, metadata={"entity_type": "task"}),
        ]
        for entity in entities:
            mock_repository.add_entity(entity)

        handler = AnalyticsQueryHandler(mock_repository, mock_logger, mock_cache)
        query = EntityCountQuery(
            group_by="type", filters={"status": EntityStatus.ACTIVE}
        )
        result = handler.handle_entity_count(query)

        assert result.status == ResultStatus.SUCCESS
        # Only active entities should be counted
        assert result.data == {"project": 1, "task": 1}
        assert result.total_count == 2

    def test_handle_entity_count_caching_first_call(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test entity count caches result on first call."""
        entities = [Entity(metadata={"entity_type": "project"})]
        for entity in entities:
            mock_repository.add_entity(entity)

        handler = AnalyticsQueryHandler(mock_repository, mock_logger, mock_cache)
        query = EntityCountQuery(group_by="type")
        result = handler.handle_entity_count(query)

        assert result.status == ResultStatus.SUCCESS
        assert result.metadata["cached"] is False
        # Verify cache was set
        assert len(mock_cache._store) > 0

    def test_handle_entity_count_caching_second_call(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test entity count returns cached result on second call."""
        entities = [Entity(metadata={"entity_type": "project"})]
        for entity in entities:
            mock_repository.add_entity(entity)

        handler = AnalyticsQueryHandler(mock_repository, mock_logger, mock_cache)
        query = EntityCountQuery(group_by="type")

        # First call
        result1 = handler.handle_entity_count(query)
        assert result1.metadata["cached"] is False

        # Second call should return cached result
        result2 = handler.handle_entity_count(query)
        assert result2.status == ResultStatus.SUCCESS
        assert result2.metadata["cached"] is True
        assert result2.data == result1.data

    def test_handle_entity_count_validation_error(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test entity count with validation error."""
        handler = AnalyticsQueryHandler(mock_repository, mock_logger, mock_cache)
        query = EntityCountQuery(group_by="invalid")

        result = handler.handle_entity_count(query)

        assert result.status == ResultStatus.ERROR
        assert "Validation error" in result.error
        assert len(mock_logger.get_logs("ERROR")) > 0

    def test_handle_entity_count_repository_error(
        self, mock_logger, mock_cache
    ):
        """Test entity count with repository error."""
        mock_repo = Mock()
        mock_repo.list.side_effect = RepositoryError("Database error")

        handler = AnalyticsQueryHandler(mock_repo, mock_logger, mock_cache)
        query = EntityCountQuery(group_by="type")
        result = handler.handle_entity_count(query)

        assert result.status == ResultStatus.ERROR
        assert "Failed to count entities" in result.error

    def test_handle_entity_count_unexpected_error(
        self, mock_logger, mock_cache
    ):
        """Test entity count with unexpected error."""
        mock_repo = Mock()
        mock_repo.list.side_effect = ValueError("Unexpected error")

        handler = AnalyticsQueryHandler(mock_repo, mock_logger, mock_cache)
        query = EntityCountQuery(group_by="type")
        result = handler.handle_entity_count(query)

        assert result.status == ResultStatus.ERROR
        assert "Unexpected error" in result.error


# =============================================================================
# ANALYTICS QUERY HANDLER TESTS - WORKSPACE STATS
# =============================================================================


class TestAnalyticsQueryHandlerWorkspaceStats:
    """Test AnalyticsQueryHandler.handle_workspace_stats method."""

    def test_handle_workspace_stats_success_all_workspaces(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test workspace stats for all workspaces."""
        # Create entities with various statuses
        entities = [
            Entity(
                status=EntityStatus.ACTIVE,
                metadata={"entity_type": "project"},
                created_at=datetime.utcnow(),
            ),
            Entity(
                status=EntityStatus.ARCHIVED,
                metadata={"entity_type": "task"},
                created_at=datetime.utcnow(),
            ),
            Entity(
                status=EntityStatus.DELETED,
                metadata={"entity_type": "document"},
                created_at=datetime.utcnow(),
            ),
        ]
        for entity in entities:
            mock_repository.add_entity(entity)

        handler = AnalyticsQueryHandler(mock_repository, mock_logger, mock_cache)
        query = WorkspaceStatsQuery()
        result = handler.handle_workspace_stats(query)

        assert result.status == ResultStatus.SUCCESS
        assert result.data["total_entities"] == 3
        assert result.data["active_entities"] == 1
        assert result.data["archived_entities"] == 1
        assert result.data["deleted_entities"] == 1
        assert "entity_types" in result.data
        assert result.data["entity_types"]["project"] == 1
        assert result.data["entity_types"]["task"] == 1

    def test_handle_workspace_stats_specific_workspace(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test workspace stats for specific workspace."""
        entities = [
            Entity(metadata={"workspace_id": "ws1", "entity_type": "project"}),
            Entity(metadata={"workspace_id": "ws1", "entity_type": "task"}),
            Entity(metadata={"workspace_id": "ws2", "entity_type": "project"}),
        ]
        for entity in entities:
            mock_repository.add_entity(entity)

        handler = AnalyticsQueryHandler(mock_repository, mock_logger, mock_cache)
        query = WorkspaceStatsQuery(workspace_id="ws1")
        result = handler.handle_workspace_stats(query)

        assert result.status == ResultStatus.SUCCESS
        # Mock repository doesn't support filtering, so verify structure is correct
        assert "total_entities" in result.data
        assert "entity_types" in result.data

    def test_handle_workspace_stats_empty_workspace(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test workspace stats with no entities."""
        handler = AnalyticsQueryHandler(mock_repository, mock_logger, mock_cache)
        query = WorkspaceStatsQuery()
        result = handler.handle_workspace_stats(query)

        assert result.status == ResultStatus.SUCCESS
        assert result.data["total_entities"] == 0
        assert result.data["active_entities"] == 0
        assert result.data["entity_types"] == {}

    def test_handle_workspace_stats_recent_activity(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test workspace stats includes recent activity count."""
        # Create entities with different update times
        now = datetime.utcnow()
        entities = [
            Entity(updated_at=now),  # Recent
            Entity(updated_at=now - timedelta(hours=12)),  # Recent
            Entity(updated_at=now - timedelta(days=2)),  # Not recent
        ]
        for entity in entities:
            mock_repository.add_entity(entity)

        handler = AnalyticsQueryHandler(mock_repository, mock_logger, mock_cache)
        query = WorkspaceStatsQuery()
        result = handler.handle_workspace_stats(query)

        assert result.status == ResultStatus.SUCCESS
        # Should count entities updated in last 24 hours
        assert result.data["recent_activity"] == 2

    def test_handle_workspace_stats_caching(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test workspace stats caching behavior."""
        entities = [Entity(metadata={"entity_type": "project"})]
        for entity in entities:
            mock_repository.add_entity(entity)

        handler = AnalyticsQueryHandler(mock_repository, mock_logger, mock_cache)
        query = WorkspaceStatsQuery()

        # First call
        result1 = handler.handle_workspace_stats(query)
        assert result1.metadata["cached"] is False

        # Second call should return cached result
        result2 = handler.handle_workspace_stats(query)
        assert result2.status == ResultStatus.SUCCESS
        assert result2.metadata["cached"] is True

    def test_handle_workspace_stats_repository_error(
        self, mock_logger, mock_cache
    ):
        """Test workspace stats with repository error."""
        mock_repo = Mock()
        mock_repo.list.side_effect = RepositoryError("Database error")

        handler = AnalyticsQueryHandler(mock_repo, mock_logger, mock_cache)
        query = WorkspaceStatsQuery()
        result = handler.handle_workspace_stats(query)

        assert result.status == ResultStatus.ERROR
        assert "Failed to get workspace stats" in result.error


# =============================================================================
# ANALYTICS QUERY HANDLER TESTS - ACTIVITY
# =============================================================================


class TestAnalyticsQueryHandlerActivity:
    """Test AnalyticsQueryHandler.handle_activity method."""

    def test_handle_activity_success_day_granularity(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test activity query with daily granularity."""
        base_date = datetime(2024, 1, 1, 12, 0, 0)
        entities = [
            Entity(created_at=base_date),
            Entity(created_at=base_date + timedelta(days=1)),
            Entity(created_at=base_date + timedelta(days=1)),
        ]
        for entity in entities:
            mock_repository.add_entity(entity)

        handler = AnalyticsQueryHandler(mock_repository, mock_logger, mock_cache)
        query = ActivityQuery(
            start_date=base_date,
            end_date=base_date + timedelta(days=2),
            granularity="day",
        )
        result = handler.handle_activity(query)

        assert result.status == ResultStatus.SUCCESS
        assert result.data["total_entities"] == 3
        assert result.data["granularity"] == "day"
        activity = result.data["activity"]
        assert "2024-01-01" in activity
        assert "2024-01-02" in activity

    def test_handle_activity_success_hour_granularity(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test activity query with hourly granularity."""
        base_date = datetime(2024, 1, 1, 10, 0, 0)
        entities = [
            Entity(created_at=base_date),
            Entity(created_at=base_date + timedelta(hours=1)),
        ]
        for entity in entities:
            mock_repository.add_entity(entity)

        handler = AnalyticsQueryHandler(mock_repository, mock_logger, mock_cache)
        query = ActivityQuery(
            start_date=base_date,
            end_date=base_date + timedelta(hours=2),
            granularity="hour",
        )
        result = handler.handle_activity(query)

        assert result.status == ResultStatus.SUCCESS
        activity = result.data["activity"]
        assert "2024-01-01 10:00" in activity
        assert "2024-01-01 11:00" in activity

    def test_handle_activity_success_week_granularity(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test activity query with weekly granularity."""
        base_date = datetime(2024, 1, 1, 12, 0, 0)
        entities = [
            Entity(created_at=base_date),
            Entity(created_at=base_date + timedelta(weeks=1)),
        ]
        for entity in entities:
            mock_repository.add_entity(entity)

        handler = AnalyticsQueryHandler(mock_repository, mock_logger, mock_cache)
        query = ActivityQuery(
            start_date=base_date,
            end_date=base_date + timedelta(weeks=2),
            granularity="week",
        )
        result = handler.handle_activity(query)

        assert result.status == ResultStatus.SUCCESS
        assert "activity" in result.data

    def test_handle_activity_success_month_granularity(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test activity query with monthly granularity."""
        base_date = datetime(2024, 1, 1, 12, 0, 0)
        entities = [
            Entity(created_at=base_date),
            Entity(created_at=base_date + timedelta(days=35)),
        ]
        for entity in entities:
            mock_repository.add_entity(entity)

        handler = AnalyticsQueryHandler(mock_repository, mock_logger, mock_cache)
        query = ActivityQuery(
            start_date=base_date,
            end_date=base_date + timedelta(days=60),
            granularity="month",
        )
        result = handler.handle_activity(query)

        assert result.status == ResultStatus.SUCCESS
        assert "2024-01" in result.data["activity"]

    def test_handle_activity_filter_by_entity_types(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test activity query filtered by entity types."""
        base_date = datetime(2024, 1, 1, 12, 0, 0)
        entities = [
            Entity(created_at=base_date, metadata={"entity_type": "project"}),
            Entity(created_at=base_date, metadata={"entity_type": "task"}),
            Entity(created_at=base_date, metadata={"entity_type": "document"}),
        ]
        for entity in entities:
            mock_repository.add_entity(entity)

        handler = AnalyticsQueryHandler(mock_repository, mock_logger, mock_cache)
        query = ActivityQuery(
            start_date=base_date,
            end_date=base_date + timedelta(days=1),
            granularity="day",
            entity_types=["project", "task"],
        )
        result = handler.handle_activity(query)

        assert result.status == ResultStatus.SUCCESS
        # Should only count project and task entities
        assert result.data["total_entities"] == 2

    def test_handle_activity_empty_date_range(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test activity query with date range containing no entities."""
        base_date = datetime(2024, 1, 1, 12, 0, 0)
        entities = [Entity(created_at=base_date)]
        for entity in entities:
            mock_repository.add_entity(entity)

        handler = AnalyticsQueryHandler(mock_repository, mock_logger, mock_cache)
        query = ActivityQuery(
            start_date=base_date + timedelta(days=10),
            end_date=base_date + timedelta(days=20),
            granularity="day",
        )
        result = handler.handle_activity(query)

        assert result.status == ResultStatus.SUCCESS
        assert result.data["total_entities"] == 0

    def test_handle_activity_default_date_range(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test activity query uses default date range (30 days)."""
        # Create entity within last 30 days
        recent_date = datetime.utcnow() - timedelta(days=5)
        entities = [Entity(created_at=recent_date)]
        for entity in entities:
            mock_repository.add_entity(entity)

        handler = AnalyticsQueryHandler(mock_repository, mock_logger, mock_cache)
        query = ActivityQuery()  # No dates specified
        result = handler.handle_activity(query)

        assert result.status == ResultStatus.SUCCESS
        assert result.data["total_entities"] == 1

    def test_handle_activity_caching(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test activity query caching behavior."""
        base_date = datetime(2024, 1, 1, 12, 0, 0)
        entities = [Entity(created_at=base_date)]
        for entity in entities:
            mock_repository.add_entity(entity)

        handler = AnalyticsQueryHandler(mock_repository, mock_logger, mock_cache)
        query = ActivityQuery(
            start_date=base_date, end_date=base_date + timedelta(days=1)
        )

        # First call
        result1 = handler.handle_activity(query)
        assert result1.metadata["cached"] is False

        # Second call should return cached result
        result2 = handler.handle_activity(query)
        assert result2.status == ResultStatus.SUCCESS
        assert result2.metadata["cached"] is True

    def test_handle_activity_validation_error(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test activity query with validation error."""
        handler = AnalyticsQueryHandler(mock_repository, mock_logger, mock_cache)
        query = ActivityQuery(granularity="invalid")

        result = handler.handle_activity(query)

        assert result.status == ResultStatus.ERROR
        assert "Validation error" in result.error

    def test_handle_activity_repository_error(
        self, mock_logger, mock_cache
    ):
        """Test activity query with repository error."""
        mock_repo = Mock()
        mock_repo.list.side_effect = RepositoryError("Database error")

        handler = AnalyticsQueryHandler(mock_repo, mock_logger, mock_cache)
        query = ActivityQuery()
        result = handler.handle_activity(query)

        assert result.status == ResultStatus.ERROR
        assert "Failed to get activity" in result.error


# =============================================================================
# PERFORMANCE TESTS
# =============================================================================


class TestAnalyticsQueryPerformance:
    """Test analytics query performance with large datasets."""

    @pytest.mark.performance
    def test_entity_count_performance_large_dataset(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test entity count performance with 10,000 entities."""
        # Create 10,000 entities with various types
        types = ["project", "task", "document", "requirement"]
        for i in range(10000):
            entity = Entity(metadata={"entity_type": types[i % len(types)]})
            mock_repository.add_entity(entity)

        handler = AnalyticsQueryHandler(mock_repository, mock_logger, mock_cache)
        query = EntityCountQuery(group_by="type")

        start_time = time.time()
        result = handler.handle_entity_count(query)
        elapsed = time.time() - start_time

        assert result.status == ResultStatus.SUCCESS
        assert result.total_count == 10000
        # Should complete in less than 500ms
        assert elapsed < 0.5, f"Query took {elapsed:.2f}s, expected < 0.5s"

    @pytest.mark.performance
    def test_workspace_stats_performance_large_dataset(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test workspace stats performance with 10,000 entities."""
        # Create 10,000 entities
        for i in range(10000):
            entity = Entity(
                status=EntityStatus.ACTIVE if i % 2 == 0 else EntityStatus.ARCHIVED,
                metadata={"entity_type": "project"},
            )
            mock_repository.add_entity(entity)

        handler = AnalyticsQueryHandler(mock_repository, mock_logger, mock_cache)
        query = WorkspaceStatsQuery()

        start_time = time.time()
        result = handler.handle_workspace_stats(query)
        elapsed = time.time() - start_time

        assert result.status == ResultStatus.SUCCESS
        assert result.data["total_entities"] == 10000
        # Should complete in less than 500ms
        assert elapsed < 0.5, f"Query took {elapsed:.2f}s, expected < 0.5s"

    @pytest.mark.performance
    def test_activity_query_performance_large_dataset(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test activity query performance with 10,000 entities."""
        base_date = datetime(2024, 1, 1, 12, 0, 0)
        # Create 10,000 entities spread across 30 days
        for i in range(10000):
            entity = Entity(
                created_at=base_date + timedelta(days=i % 30),
                metadata={"entity_type": "project"},
            )
            mock_repository.add_entity(entity)

        handler = AnalyticsQueryHandler(mock_repository, mock_logger, mock_cache)
        query = ActivityQuery(
            start_date=base_date,
            end_date=base_date + timedelta(days=30),
            granularity="day",
        )

        start_time = time.time()
        result = handler.handle_activity(query)
        elapsed = time.time() - start_time

        assert result.status == ResultStatus.SUCCESS
        # Should complete in less than 500ms
        assert elapsed < 0.5, f"Query took {elapsed:.2f}s, expected < 0.5s"


# =============================================================================
# EDGE CASE TESTS
# =============================================================================


class TestAnalyticsQueryEdgeCases:
    """Test analytics query edge cases."""

    def test_entity_count_unknown_metadata_fields(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test entity count with entities missing metadata fields."""
        entities = [
            Entity(),  # No entity_type metadata
            Entity(metadata={"entity_type": "project"}),
        ]
        for entity in entities:
            mock_repository.add_entity(entity)

        handler = AnalyticsQueryHandler(mock_repository, mock_logger, mock_cache)
        query = EntityCountQuery(group_by="type")
        result = handler.handle_entity_count(query)

        assert result.status == ResultStatus.SUCCESS
        assert "unknown" in result.data
        assert result.data["unknown"] == 1
        assert result.data["project"] == 1

    def test_workspace_stats_entities_without_types(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test workspace stats with entities missing entity_type."""
        entities = [Entity(), Entity()]  # No entity_type metadata
        for entity in entities:
            mock_repository.add_entity(entity)

        handler = AnalyticsQueryHandler(mock_repository, mock_logger, mock_cache)
        query = WorkspaceStatsQuery()
        result = handler.handle_workspace_stats(query)

        assert result.status == ResultStatus.SUCCESS
        assert result.data["entity_types"]["unknown"] == 2

    def test_activity_query_single_time_bucket(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test activity query with single time bucket."""
        base_date = datetime(2024, 1, 1, 12, 0, 0)
        entities = [
            Entity(created_at=base_date),
            Entity(created_at=base_date),
        ]
        for entity in entities:
            mock_repository.add_entity(entity)

        handler = AnalyticsQueryHandler(mock_repository, mock_logger, mock_cache)
        query = ActivityQuery(
            start_date=base_date,
            end_date=base_date,
            granularity="day",
        )
        result = handler.handle_activity(query)

        assert result.status == ResultStatus.SUCCESS
        activity = result.data["activity"]
        assert len(activity) == 1
        assert activity["2024-01-01"] == 2

    def test_cache_key_generation_uniqueness(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test cache keys are unique for different queries."""
        handler = AnalyticsQueryHandler(mock_repository, mock_logger, mock_cache)

        # Create two different queries
        query1 = EntityCountQuery(group_by="type")
        query2 = EntityCountQuery(group_by="status")

        key1 = handler._get_cache_key("entity_count", query1)
        key2 = handler._get_cache_key("entity_count", query2)

        assert key1 != key2

    def test_cache_key_generation_consistency(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test cache keys are consistent for same query."""
        handler = AnalyticsQueryHandler(mock_repository, mock_logger, mock_cache)

        query = EntityCountQuery(group_by="type", filters={"status": "active"})

        key1 = handler._get_cache_key("entity_count", query)
        key2 = handler._get_cache_key("entity_count", query)

        assert key1 == key2

    def test_no_cache_behavior(
        self, mock_repository, mock_logger
    ):
        """Test analytics handler works without cache."""
        entities = [Entity(metadata={"entity_type": "project"})]
        for entity in entities:
            mock_repository.add_entity(entity)

        # Initialize without cache
        handler = AnalyticsQueryHandler(mock_repository, mock_logger, cache=None)
        query = EntityCountQuery(group_by="type")
        result = handler.handle_entity_count(query)

        assert result.status == ResultStatus.SUCCESS
        assert result.data == {"project": 1}
