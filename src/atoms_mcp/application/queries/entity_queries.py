"""
Entity queries for the application layer.

This module implements query handlers for entity retrieval operations.
Queries use domain services and return QueryResult DTOs.
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from ...domain.models.entity import Entity
from ...domain.ports.cache import Cache
from ...domain.ports.logger import Logger
from ...domain.ports.repository import Repository, RepositoryError
from ...domain.services.entity_service import EntityService
from ..dto import EntityDTO, QueryResult, ResultStatus


class EntityQueryError(Exception):
    """Base exception for entity query errors."""

    pass


class EntityQueryValidationError(EntityQueryError):
    """Exception raised for query validation failures."""

    pass


@dataclass
class GetEntityQuery:
    """
    Query to get a single entity by ID.

    Attributes:
        entity_id: ID of entity to retrieve
        use_cache: Whether to use cache for retrieval
    """

    entity_id: str
    use_cache: bool = True

    def validate(self) -> None:
        """
        Validate query parameters.

        Raises:
            EntityQueryValidationError: If validation fails
        """
        if not self.entity_id:
            raise EntityQueryValidationError("entity_id is required")


@dataclass
class ListEntitiesQuery:
    """
    Query to list entities with filtering and pagination.

    Attributes:
        filters: Optional filters to apply
        limit: Maximum number of results
        offset: Number of results to skip
        order_by: Field to order by
        page: Page number (1-indexed)
        page_size: Number of items per page
    """

    filters: dict[str, Any] = field(default_factory=dict)
    limit: Optional[int] = None
    offset: Optional[int] = None
    order_by: Optional[str] = None
    page: int = 1
    page_size: int = 20

    def validate(self) -> None:
        """
        Validate query parameters.

        Raises:
            EntityQueryValidationError: If validation fails
        """
        if self.page < 1:
            raise EntityQueryValidationError("page must be >= 1")
        if self.page_size < 1 or self.page_size > 1000:
            raise EntityQueryValidationError("page_size must be between 1 and 1000")

    def get_limit(self) -> int:
        """Get effective limit."""
        return self.limit if self.limit is not None else self.page_size

    def get_offset(self) -> int:
        """Get effective offset."""
        if self.offset is not None:
            return self.offset
        return (self.page - 1) * self.page_size


@dataclass
class SearchEntitiesQuery:
    """
    Query to search entities using text search.

    Attributes:
        query: Search query string
        fields: Fields to search in
        filters: Optional filters to apply
        limit: Maximum number of results
        page: Page number (1-indexed)
        page_size: Number of items per page
    """

    query: str
    fields: Optional[list[str]] = None
    filters: dict[str, Any] = field(default_factory=dict)
    limit: Optional[int] = None
    page: int = 1
    page_size: int = 20

    def validate(self) -> None:
        """
        Validate query parameters.

        Raises:
            EntityQueryValidationError: If validation fails
        """
        if not self.query:
            raise EntityQueryValidationError("query is required")
        if self.page < 1:
            raise EntityQueryValidationError("page must be >= 1")
        if self.page_size < 1 or self.page_size > 1000:
            raise EntityQueryValidationError("page_size must be between 1 and 1000")

    def get_limit(self) -> int:
        """Get effective limit."""
        return self.limit if self.limit is not None else self.page_size


@dataclass
class CountEntitiesQuery:
    """
    Query to count entities matching filters.

    Attributes:
        filters: Optional filters to apply
    """

    filters: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        """Validate query parameters."""
        pass  # No validation needed


class EntityQueryHandler:
    """
    Handler for entity queries.

    This class handles entity retrieval operations using the domain service
    and returns DTOs suitable for serialization.

    Attributes:
        entity_service: Domain service for entity operations
        logger: Logger for recording events
    """

    def __init__(
        self,
        repository: Repository[Entity],
        logger: Logger,
        cache: Optional[Cache] = None,
    ):
        """
        Initialize entity query handler.

        Args:
            repository: Repository for entity persistence
            logger: Logger for recording events
            cache: Optional cache for performance
        """
        self.entity_service = EntityService(repository, logger, cache)
        self.logger = logger

    def handle_get_entity(self, query: GetEntityQuery) -> QueryResult[EntityDTO]:
        """
        Handle get entity query.

        Args:
            query: Get entity query

        Returns:
            Query result with entity DTO
        """
        try:
            # Validate query
            query.validate()

            # Get entity using service
            entity = self.entity_service.get_entity(
                query.entity_id, use_cache=query.use_cache
            )

            if not entity:
                return QueryResult(
                    status=ResultStatus.ERROR,
                    error=f"Entity {query.entity_id} not found",
                )

            # Convert to DTO
            dto = self._entity_to_dto(entity)

            return QueryResult(
                status=ResultStatus.SUCCESS,
                data=dto,
                total_count=1,
                page=1,
                page_size=1,
            )

        except EntityQueryValidationError as e:
            self.logger.error(f"Entity query validation failed: {e}")
            return QueryResult(
                status=ResultStatus.ERROR,
                error=f"Validation error: {str(e)}",
            )

        except RepositoryError as e:
            self.logger.error(f"Repository error during entity retrieval: {e}")
            return QueryResult(
                status=ResultStatus.ERROR,
                error=f"Failed to retrieve entity: {str(e)}",
            )

        except Exception as e:
            self.logger.error(f"Unexpected error during entity retrieval: {e}")
            return QueryResult(
                status=ResultStatus.ERROR,
                error=f"Unexpected error: {str(e)}",
            )

    def handle_list_entities(
        self, query: ListEntitiesQuery
    ) -> QueryResult[list[EntityDTO]]:
        """
        Handle list entities query.

        Args:
            query: List entities query

        Returns:
            Query result with list of entity DTOs
        """
        try:
            # Validate query
            query.validate()

            # Get total count
            total_count = self.entity_service.count_entities(filters=query.filters)

            # List entities using service
            entities = self.entity_service.list_entities(
                filters=query.filters,
                limit=query.get_limit(),
                offset=query.get_offset(),
                order_by=query.order_by,
            )

            # Convert to DTOs
            dtos = [self._entity_to_dto(entity) for entity in entities]

            return QueryResult(
                status=ResultStatus.SUCCESS,
                data=dtos,
                total_count=total_count,
                page=query.page,
                page_size=query.page_size,
                metadata={
                    "filters": query.filters,
                    "order_by": query.order_by,
                },
            )

        except EntityQueryValidationError as e:
            self.logger.error(f"Entity query validation failed: {e}")
            return QueryResult(
                status=ResultStatus.ERROR,
                error=f"Validation error: {str(e)}",
            )

        except RepositoryError as e:
            self.logger.error(f"Repository error during entity listing: {e}")
            return QueryResult(
                status=ResultStatus.ERROR,
                error=f"Failed to list entities: {str(e)}",
            )

        except Exception as e:
            self.logger.error(f"Unexpected error during entity listing: {e}")
            return QueryResult(
                status=ResultStatus.ERROR,
                error=f"Unexpected error: {str(e)}",
            )

    def handle_search_entities(
        self, query: SearchEntitiesQuery
    ) -> QueryResult[list[EntityDTO]]:
        """
        Handle search entities query.

        Args:
            query: Search entities query

        Returns:
            Query result with list of entity DTOs
        """
        try:
            # Validate query
            query.validate()

            # Search entities using service
            entities = self.entity_service.search_entities(
                query=query.query,
                fields=query.fields,
                limit=query.get_limit(),
            )

            # Apply additional filters if provided
            if query.filters:
                entities = self._apply_filters(entities, query.filters)

            # Get total count before pagination
            total_count = len(entities)

            # Apply pagination
            start_idx = (query.page - 1) * query.page_size
            end_idx = start_idx + query.page_size
            paginated_entities = entities[start_idx:end_idx]

            # Convert to DTOs
            dtos = [self._entity_to_dto(entity) for entity in paginated_entities]

            return QueryResult(
                status=ResultStatus.SUCCESS,
                data=dtos,
                total_count=total_count,
                page=query.page,
                page_size=query.page_size,
                metadata={
                    "query": query.query,
                    "fields": query.fields,
                    "filters": query.filters,
                },
            )

        except EntityQueryValidationError as e:
            self.logger.error(f"Entity query validation failed: {e}")
            return QueryResult(
                status=ResultStatus.ERROR,
                error=f"Validation error: {str(e)}",
            )

        except RepositoryError as e:
            self.logger.error(f"Repository error during entity search: {e}")
            return QueryResult(
                status=ResultStatus.ERROR,
                error=f"Failed to search entities: {str(e)}",
            )

        except Exception as e:
            self.logger.error(f"Unexpected error during entity search: {e}")
            return QueryResult(
                status=ResultStatus.ERROR,
                error=f"Unexpected error: {str(e)}",
            )

    def handle_count_entities(self, query: CountEntitiesQuery) -> QueryResult[int]:
        """
        Handle count entities query.

        Args:
            query: Count entities query

        Returns:
            Query result with entity count
        """
        try:
            # Validate query
            query.validate()

            # Count entities using service
            count = self.entity_service.count_entities(filters=query.filters)

            return QueryResult(
                status=ResultStatus.SUCCESS,
                data=count,
                total_count=count,
                page=1,
                page_size=1,
                metadata={"filters": query.filters},
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

    def _entity_to_dto(self, entity: Entity) -> EntityDTO:
        """
        Convert entity to DTO.

        Args:
            entity: Entity to convert

        Returns:
            EntityDTO instance
        """
        from ..commands.entity_commands import EntityCommandHandler

        # Reuse conversion logic from command handler
        # In practice, this would be in a shared converter module
        handler = EntityCommandHandler(
            self.entity_service.repository,
            self.logger,
            self.entity_service.cache,
        )
        return handler._entity_to_dto(entity)

    def _apply_filters(
        self, entities: list[Entity], filters: dict[str, Any]
    ) -> list[Entity]:
        """
        Apply filters to entity list.

        Args:
            entities: List of entities
            filters: Filters to apply

        Returns:
            Filtered entity list
        """
        filtered = []
        for entity in entities:
            matches = True
            for key, value in filters.items():
                entity_value = getattr(entity, key, None)
                if entity_value is None:
                    entity_value = entity.metadata.get(key)

                if entity_value != value:
                    matches = False
                    break

            if matches:
                filtered.append(entity)

        return filtered


__all__ = [
    "GetEntityQuery",
    "ListEntitiesQuery",
    "SearchEntitiesQuery",
    "CountEntitiesQuery",
    "EntityQueryHandler",
    "EntityQueryError",
    "EntityQueryValidationError",
]
