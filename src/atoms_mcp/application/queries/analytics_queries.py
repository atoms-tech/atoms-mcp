"""
Analytics queries for the application layer.

This module implements query handlers for analytics and aggregate data.
Queries include caching for performance optimization.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Optional

from ...domain.models.entity import Entity, EntityStatus
from ...domain.ports.cache import Cache
from ...domain.ports.logger import Logger
from ...domain.ports.repository import Repository, RepositoryError
from ...domain.services.entity_service import EntityService
from ..dto import QueryResult, ResultStatus


class AnalyticsQueryError(Exception):
    """Base exception for analytics query errors."""

    pass


class AnalyticsQueryValidationError(AnalyticsQueryError):
    """Exception raised for query validation failures."""

    pass


@dataclass
class EntityCountQuery:
    """
    Query to get entity counts grouped by type or status.

    Attributes:
        group_by: Field to group by ("type", "status", or "workspace_id")
        filters: Optional filters to apply
    """

    group_by: str = "type"
    filters: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        """
        Validate query parameters.

        Raises:
            AnalyticsQueryValidationError: If validation fails
        """
        if self.group_by not in ("type", "status", "workspace_id", "project_id"):
            raise AnalyticsQueryValidationError(
                "group_by must be 'type', 'status', 'workspace_id', or 'project_id'"
            )


@dataclass
class WorkspaceStatsQuery:
    """
    Query to get workspace statistics.

    Attributes:
        workspace_id: Optional workspace ID to filter by
    """

    workspace_id: Optional[str] = None

    def validate(self) -> None:
        """Validate query parameters."""
        pass  # No validation needed


@dataclass
class ActivityQuery:
    """
    Query to get activity statistics over time.

    Attributes:
        start_date: Start date for activity range
        end_date: End date for activity range
        granularity: Time granularity ("hour", "day", "week", "month")
        entity_types: Optional filter by entity types
    """

    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    granularity: str = "day"
    entity_types: list[str] = field(default_factory=list)

    def validate(self) -> None:
        """
        Validate query parameters.

        Raises:
            AnalyticsQueryValidationError: If validation fails
        """
        if self.granularity not in ("hour", "day", "week", "month"):
            raise AnalyticsQueryValidationError(
                "granularity must be 'hour', 'day', 'week', or 'month'"
            )

        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise AnalyticsQueryValidationError("end_date cannot be before start_date")

    def get_start_date(self) -> datetime:
        """Get effective start date."""
        if self.start_date:
            return self.start_date
        # Default to 30 days ago
        return datetime.utcnow() - timedelta(days=30)

    def get_end_date(self) -> datetime:
        """Get effective end date."""
        if self.end_date:
            return self.end_date
        return datetime.utcnow()


class AnalyticsQueryHandler:
    """
    Handler for analytics queries.

    This class handles analytics and aggregate data operations
    with caching for performance optimization.

    Attributes:
        entity_service: Domain service for entity operations
        logger: Logger for recording events
        cache: Cache for performance optimization
    """

    def __init__(
        self,
        repository: Repository[Entity],
        logger: Logger,
        cache: Optional[Cache] = None,
    ):
        """
        Initialize analytics query handler.

        Args:
            repository: Repository for entity persistence
            logger: Logger for recording events
            cache: Optional cache for performance
        """
        self.entity_service = EntityService(repository, logger, cache)
        self.logger = logger
        self.cache = cache

    def handle_entity_count(
        self, query: EntityCountQuery
    ) -> QueryResult[dict[str, int]]:
        """
        Handle entity count query.

        Args:
            query: Entity count query

        Returns:
            Query result with counts grouped by specified field
        """
        try:
            # Validate query
            query.validate()

            # Check cache
            cache_key = self._get_cache_key("entity_count", query)
            if self.cache:
                cached = self.cache.get(cache_key)
                if cached:
                    self.logger.debug("Entity count found in cache")
                    return QueryResult(
                        status=ResultStatus.SUCCESS,
                        data=cached,
                        total_count=sum(cached.values()),
                        page=1,
                        page_size=1,
                        metadata={"cached": True, "group_by": query.group_by},
                    )

            # Get all entities with filters
            entities = self.entity_service.list_entities(filters=query.filters)

            # Group and count
            counts: dict[str, int] = {}
            for entity in entities:
                group_value = self._get_group_value(entity, query.group_by)
                counts[group_value] = counts.get(group_value, 0) + 1

            # Cache result
            if self.cache:
                self.cache.set(cache_key, counts, ttl=300)  # 5 minutes

            return QueryResult(
                status=ResultStatus.SUCCESS,
                data=counts,
                total_count=sum(counts.values()),
                page=1,
                page_size=1,
                metadata={"cached": False, "group_by": query.group_by},
            )

        except AnalyticsQueryValidationError as e:
            self.logger.error(f"Analytics query validation failed: {e}")
            return QueryResult(
                status=ResultStatus.ERROR,
                error=f"Validation error: {str(e)}",
            )

        except RepositoryError as e:
            self.logger.error(f"Repository error during entity count: {e}")
            return QueryResult(
                status=ResultStatus.ERROR,
                error=f"Failed to count entities: {str(e)}",
            )

        except Exception as e:
            self.logger.error(f"Unexpected error during entity count: {e}")
            return QueryResult(
                status=ResultStatus.ERROR,
                error=f"Unexpected error: {str(e)}",
            )

    def handle_workspace_stats(
        self, query: WorkspaceStatsQuery
    ) -> QueryResult[dict[str, Any]]:
        """
        Handle workspace stats query.

        Args:
            query: Workspace stats query

        Returns:
            Query result with workspace statistics
        """
        try:
            # Validate query
            query.validate()

            # Check cache
            cache_key = self._get_cache_key("workspace_stats", query)
            if self.cache:
                cached = self.cache.get(cache_key)
                if cached:
                    self.logger.debug("Workspace stats found in cache")
                    return QueryResult(
                        status=ResultStatus.SUCCESS,
                        data=cached,
                        total_count=1,
                        page=1,
                        page_size=1,
                        metadata={"cached": True},
                    )

            # Build filters
            filters = {}
            if query.workspace_id:
                filters["workspace_id"] = query.workspace_id

            # Get entities
            entities = self.entity_service.list_entities(filters=filters)

            # Calculate statistics
            stats = {
                "total_entities": len(entities),
                "active_entities": sum(1 for e in entities if e.is_active()),
                "deleted_entities": sum(1 for e in entities if e.is_deleted()),
                "archived_entities": sum(
                    1 for e in entities if e.status == EntityStatus.ARCHIVED
                ),
                "entity_types": {},
                "recent_activity": self._get_recent_activity_count(entities),
            }

            # Count by type
            for entity in entities:
                entity_type = entity.metadata.get("entity_type", "unknown")
                stats["entity_types"][entity_type] = (
                    stats["entity_types"].get(entity_type, 0) + 1
                )

            # Cache result
            if self.cache:
                self.cache.set(cache_key, stats, ttl=600)  # 10 minutes

            return QueryResult(
                status=ResultStatus.SUCCESS,
                data=stats,
                total_count=1,
                page=1,
                page_size=1,
                metadata={"cached": False, "workspace_id": query.workspace_id},
            )

        except AnalyticsQueryValidationError as e:
            self.logger.error(f"Analytics query validation failed: {e}")
            return QueryResult(
                status=ResultStatus.ERROR,
                error=f"Validation error: {str(e)}",
            )

        except RepositoryError as e:
            self.logger.error(f"Repository error during workspace stats: {e}")
            return QueryResult(
                status=ResultStatus.ERROR,
                error=f"Failed to get workspace stats: {str(e)}",
            )

        except Exception as e:
            self.logger.error(f"Unexpected error during workspace stats: {e}")
            return QueryResult(
                status=ResultStatus.ERROR,
                error=f"Unexpected error: {str(e)}",
            )

    def handle_activity(
        self, query: ActivityQuery
    ) -> QueryResult[dict[str, Any]]:
        """
        Handle activity query.

        Args:
            query: Activity query

        Returns:
            Query result with activity statistics
        """
        try:
            # Validate query
            query.validate()

            # Check cache
            cache_key = self._get_cache_key("activity", query)
            if self.cache:
                cached = self.cache.get(cache_key)
                if cached:
                    self.logger.debug("Activity stats found in cache")
                    return QueryResult(
                        status=ResultStatus.SUCCESS,
                        data=cached,
                        total_count=1,
                        page=1,
                        page_size=1,
                        metadata={"cached": True},
                    )

            # Get entities
            entities = self.entity_service.list_entities()

            # Filter by date range
            start_date = query.get_start_date()
            end_date = query.get_end_date()

            filtered_entities = [
                e
                for e in entities
                if start_date <= e.created_at <= end_date
            ]

            # Filter by entity types if specified
            if query.entity_types:
                filtered_entities = [
                    e
                    for e in filtered_entities
                    if e.metadata.get("entity_type") in query.entity_types
                ]

            # Group by time period
            activity = self._group_by_time(
                filtered_entities, query.granularity, start_date, end_date
            )

            result = {
                "activity": activity,
                "total_entities": len(filtered_entities),
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "granularity": query.granularity,
            }

            # Cache result
            if self.cache:
                self.cache.set(cache_key, result, ttl=900)  # 15 minutes

            return QueryResult(
                status=ResultStatus.SUCCESS,
                data=result,
                total_count=1,
                page=1,
                page_size=1,
                metadata={"cached": False},
            )

        except AnalyticsQueryValidationError as e:
            self.logger.error(f"Analytics query validation failed: {e}")
            return QueryResult(
                status=ResultStatus.ERROR,
                error=f"Validation error: {str(e)}",
            )

        except RepositoryError as e:
            self.logger.error(f"Repository error during activity query: {e}")
            return QueryResult(
                status=ResultStatus.ERROR,
                error=f"Failed to get activity: {str(e)}",
            )

        except Exception as e:
            self.logger.error(f"Unexpected error during activity query: {e}")
            return QueryResult(
                status=ResultStatus.ERROR,
                error=f"Unexpected error: {str(e)}",
            )

    def _get_group_value(self, entity: Entity, group_by: str) -> str:
        """Get value to group by."""
        if group_by == "type":
            return entity.metadata.get("entity_type", "unknown")
        elif group_by == "status":
            return entity.status.value
        elif group_by in ("workspace_id", "project_id"):
            return entity.metadata.get(group_by, "unknown")
        return "unknown"

    def _get_recent_activity_count(self, entities: list[Entity]) -> int:
        """Get count of entities updated in last 24 hours."""
        cutoff = datetime.utcnow() - timedelta(days=1)
        return sum(1 for e in entities if e.updated_at >= cutoff)

    def _group_by_time(
        self,
        entities: list[Entity],
        granularity: str,
        start_date: datetime,
        end_date: datetime,
    ) -> dict[str, int]:
        """Group entities by time period."""
        activity = {}

        # Generate time buckets
        current = start_date
        while current <= end_date:
            bucket_key = self._get_time_bucket_key(current, granularity)
            activity[bucket_key] = 0
            current = self._increment_time(current, granularity)

        # Count entities in each bucket
        for entity in entities:
            bucket_key = self._get_time_bucket_key(entity.created_at, granularity)
            if bucket_key in activity:
                activity[bucket_key] += 1

        return activity

    def _get_time_bucket_key(self, dt: datetime, granularity: str) -> str:
        """Get time bucket key for a datetime."""
        if granularity == "hour":
            return dt.strftime("%Y-%m-%d %H:00")
        elif granularity == "day":
            return dt.strftime("%Y-%m-%d")
        elif granularity == "week":
            return dt.strftime("%Y-W%W")
        elif granularity == "month":
            return dt.strftime("%Y-%m")
        return dt.isoformat()

    def _increment_time(self, dt: datetime, granularity: str) -> datetime:
        """Increment datetime by granularity."""
        if granularity == "hour":
            return dt + timedelta(hours=1)
        elif granularity == "day":
            return dt + timedelta(days=1)
        elif granularity == "week":
            return dt + timedelta(weeks=1)
        elif granularity == "month":
            # Approximate month increment
            return dt + timedelta(days=30)
        return dt

    def _get_cache_key(self, query_type: str, query: Any) -> str:
        """Generate cache key for query."""
        import hashlib
        import json

        query_dict = query.__dict__
        query_str = json.dumps(query_dict, sort_keys=True, default=str)
        query_hash = hashlib.md5(query_str.encode()).hexdigest()
        return f"analytics:{query_type}:{query_hash}"


__all__ = [
    "EntityCountQuery",
    "WorkspaceStatsQuery",
    "ActivityQuery",
    "AnalyticsQueryHandler",
    "AnalyticsQueryError",
    "AnalyticsQueryValidationError",
]
