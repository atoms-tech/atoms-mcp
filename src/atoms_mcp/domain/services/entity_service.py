"""
Entity service - business logic for entity operations.

This module implements the core business logic for managing entities.
Uses dependency injection for ports (repository, logger, cache).
"""

from typing import Any, Optional

from ..models.entity import Entity, EntityStatus, EntityType
from ..ports.cache import Cache
from ..ports.logger import Logger
from ..ports.repository import Repository


class EntityService:
    """
    Service for managing entity business logic.

    This service implements entity-related business rules and operations,
    using injected dependencies for persistence, logging, and caching.

    Attributes:
        repository: Repository for entity persistence
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
        Initialize entity service.

        Args:
            repository: Repository for entity persistence
            logger: Logger for recording events
            cache: Optional cache for performance
        """
        self.repository = repository
        self.logger = logger
        self.cache = cache

    def create_entity(
        self,
        entity: Entity,
        validate: bool = True,
    ) -> Entity:
        """
        Create a new entity.

        Args:
            entity: Entity to create
            validate: Whether to validate entity before creation

        Returns:
            Created entity

        Raises:
            ValueError: If validation fails
            RepositoryError: If persistence fails
        """
        self.logger.info(f"Creating entity with ID {entity.id}")

        if validate:
            self._validate_entity(entity)

        # Save to repository
        created_entity = self.repository.save(entity)

        # Cache the entity if cache is available
        if self.cache:
            cache_key = self._get_cache_key(created_entity.id)
            self.cache.set(cache_key, created_entity, ttl=300)

        self.logger.info(f"Entity {created_entity.id} created successfully")
        return created_entity

    def get_entity(
        self,
        entity_id: str,
        use_cache: bool = True,
    ) -> Optional[Entity]:
        """
        Retrieve an entity by ID.

        Args:
            entity_id: Entity ID to retrieve
            use_cache: Whether to check cache first

        Returns:
            Entity if found, None otherwise
        """
        self.logger.debug(f"Retrieving entity {entity_id}")

        # Check cache first if enabled
        if use_cache and self.cache:
            cache_key = self._get_cache_key(entity_id)
            cached = self.cache.get(cache_key)
            if cached:
                self.logger.debug(f"Entity {entity_id} found in cache")
                return cached

        # Fetch from repository
        entity = self.repository.get(entity_id)

        if entity:
            # Cache for future use
            if self.cache:
                cache_key = self._get_cache_key(entity_id)
                self.cache.set(cache_key, entity, ttl=300)
            self.logger.debug(f"Entity {entity_id} retrieved successfully")
        else:
            self.logger.warning(f"Entity {entity_id} not found")

        return entity

    def update_entity(
        self,
        entity_id: str,
        updates: dict[str, Any],
        validate: bool = True,
    ) -> Optional[Entity]:
        """
        Update an existing entity.

        Args:
            entity_id: ID of entity to update
            updates: Dictionary of field updates
            validate: Whether to validate after update

        Returns:
            Updated entity if found, None otherwise

        Raises:
            ValueError: If validation fails
            RepositoryError: If persistence fails
        """
        self.logger.info(f"Updating entity {entity_id}")

        # Retrieve existing entity
        entity = self.repository.get(entity_id)
        if not entity:
            self.logger.warning(f"Entity {entity_id} not found for update")
            return None

        # Apply updates
        for field, value in updates.items():
            if hasattr(entity, field):
                setattr(entity, field, value)
            else:
                self.logger.warning(
                    f"Field {field} does not exist on entity {entity_id}"
                )

        # Mark as updated
        entity.mark_updated()

        # Validate if requested
        if validate:
            self._validate_entity(entity)

        # Save to repository
        updated_entity = self.repository.save(entity)

        # Invalidate cache
        if self.cache:
            cache_key = self._get_cache_key(entity_id)
            self.cache.delete(cache_key)

        self.logger.info(f"Entity {entity_id} updated successfully")
        return updated_entity

    def delete_entity(
        self,
        entity_id: str,
        soft_delete: bool = True,
    ) -> bool:
        """
        Delete an entity.

        Args:
            entity_id: ID of entity to delete
            soft_delete: Whether to soft delete (mark as deleted) or hard delete

        Returns:
            True if entity was deleted, False if not found
        """
        self.logger.info(
            f"Deleting entity {entity_id} (soft={soft_delete})"
        )

        if soft_delete:
            entity = self.repository.get(entity_id)
            if not entity:
                self.logger.warning(f"Entity {entity_id} not found for deletion")
                return False

            entity.delete()
            self.repository.save(entity)
        else:
            result = self.repository.delete(entity_id)
            if not result:
                self.logger.warning(f"Entity {entity_id} not found for deletion")
                return False

        # Invalidate cache
        if self.cache:
            cache_key = self._get_cache_key(entity_id)
            self.cache.delete(cache_key)

        self.logger.info(f"Entity {entity_id} deleted successfully")
        return True

    def list_entities(
        self,
        filters: Optional[dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[str] = None,
    ) -> list[Entity]:
        """
        List entities with filtering and pagination.

        Args:
            filters: Dictionary of field:value filters
            limit: Maximum number of results
            offset: Number of results to skip
            order_by: Field to order by

        Returns:
            List of entities matching criteria
        """
        self.logger.debug(
            f"Listing entities with filters={filters}, limit={limit}"
        )

        entities = self.repository.list(
            filters=filters,
            limit=limit,
            offset=offset,
            order_by=order_by,
        )

        self.logger.debug(f"Found {len(entities)} entities")
        return entities

    def search_entities(
        self,
        query: str,
        fields: Optional[list[str]] = None,
        limit: Optional[int] = None,
    ) -> list[Entity]:
        """
        Search entities using text search.

        Args:
            query: Search query string
            fields: Fields to search in
            limit: Maximum number of results

        Returns:
            List of entities matching search criteria
        """
        self.logger.debug(f"Searching entities with query='{query}'")

        entities = self.repository.search(
            query=query,
            fields=fields,
            limit=limit,
        )

        self.logger.debug(f"Found {len(entities)} entities matching search")
        return entities

    def count_entities(
        self,
        filters: Optional[dict[str, Any]] = None,
    ) -> int:
        """
        Count entities matching filters.

        Args:
            filters: Dictionary of field:value filters

        Returns:
            Number of entities matching criteria
        """
        count = self.repository.count(filters=filters)
        self.logger.debug(f"Counted {count} entities with filters={filters}")
        return count

    def archive_entity(self, entity_id: str) -> Optional[Entity]:
        """
        Archive an entity.

        Args:
            entity_id: ID of entity to archive

        Returns:
            Archived entity if found, None otherwise
        """
        self.logger.info(f"Archiving entity {entity_id}")

        entity = self.repository.get(entity_id)
        if not entity:
            self.logger.warning(f"Entity {entity_id} not found for archiving")
            return None

        entity.archive()
        archived_entity = self.repository.save(entity)

        # Invalidate cache
        if self.cache:
            cache_key = self._get_cache_key(entity_id)
            self.cache.delete(cache_key)

        self.logger.info(f"Entity {entity_id} archived successfully")
        return archived_entity

    def restore_entity(self, entity_id: str) -> Optional[Entity]:
        """
        Restore a deleted or archived entity.

        Args:
            entity_id: ID of entity to restore

        Returns:
            Restored entity if found, None otherwise
        """
        self.logger.info(f"Restoring entity {entity_id}")

        entity = self.repository.get(entity_id)
        if not entity:
            self.logger.warning(f"Entity {entity_id} not found for restoration")
            return None

        entity.restore()
        restored_entity = self.repository.save(entity)

        # Invalidate cache
        if self.cache:
            cache_key = self._get_cache_key(entity_id)
            self.cache.delete(cache_key)

        self.logger.info(f"Entity {entity_id} restored successfully")
        return restored_entity

    def _validate_entity(self, entity: Entity) -> None:
        """
        Validate an entity.

        Args:
            entity: Entity to validate

        Raises:
            ValueError: If validation fails
        """
        if not entity.id:
            raise ValueError("Entity ID cannot be empty")

        # Additional validation can be added here
        # For example, checking required fields based on entity type

    def _get_cache_key(self, entity_id: str) -> str:
        """
        Generate cache key for an entity.

        Args:
            entity_id: Entity ID

        Returns:
            Cache key string
        """
        return f"entity:{entity_id}"
