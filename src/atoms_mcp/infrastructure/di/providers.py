"""
Dependency providers for different component types.

This module provides factory functions for creating repositories,
services, adapters, and other dependencies based on configuration.
"""

from typing import Any, Optional

from ...domain.ports.cache import Cache
from ...domain.ports.logger import Logger
from ..cache.provider import create_cache_provider
from ..config.settings import CacheBackend, Settings
from ..logging.logger import StdLibLogger


class LoggerProvider:
    """Provider for logger instances."""

    @staticmethod
    def create(name: str = "atoms_mcp") -> Logger:
        """
        Create a logger instance.

        Args:
            name: Logger name

        Returns:
            Logger instance
        """
        return StdLibLogger(name)

    @staticmethod
    def create_for_module(module_name: str) -> Logger:
        """
        Create a logger for a specific module.

        Args:
            module_name: Module name (e.g., "domain.services.entity")

        Returns:
            Logger instance
        """
        logger_name = f"atoms_mcp.{module_name}"
        return StdLibLogger(logger_name)


class CacheProvider:
    """Provider for cache instances."""

    @staticmethod
    def create(settings: Settings) -> Cache:
        """
        Create a cache instance based on settings.

        Args:
            settings: Application settings

        Returns:
            Cache instance
        """
        return create_cache_provider(
            backend=settings.cache.backend.value,
            redis_url=settings.cache.redis_url,
            max_size=settings.cache.max_size,
            default_ttl=settings.cache.default_ttl,
        )

    @staticmethod
    def create_memory_cache(
        max_size: int = 1000,
        default_ttl: int = 300,
    ) -> Cache:
        """
        Create an in-memory cache instance.

        Args:
            max_size: Maximum cache size
            default_ttl: Default TTL in seconds

        Returns:
            In-memory cache instance
        """
        return create_cache_provider(
            backend="memory",
            max_size=max_size,
            default_ttl=default_ttl,
        )

    @staticmethod
    def create_redis_cache(
        redis_url: str,
        default_ttl: int = 300,
    ) -> Cache:
        """
        Create a Redis cache instance.

        Args:
            redis_url: Redis connection URL
            default_ttl: Default TTL in seconds

        Returns:
            Redis cache instance
        """
        return create_cache_provider(
            backend="redis",
            redis_url=redis_url,
            default_ttl=default_ttl,
        )


class RepositoryProvider:
    """Provider for repository instances."""

    @staticmethod
    def create_supabase_repository(
        settings: Settings,
        logger: Logger,
    ) -> Any:
        """
        Create a Supabase repository instance.

        Args:
            settings: Application settings
            logger: Logger instance

        Returns:
            Supabase repository instance

        Note:
            Actual implementation will be in infrastructure/adapters/supabase/
            This is a placeholder for the provider pattern.
        """
        # Import here to avoid circular dependencies
        # from ...adapters.supabase.repository import SupabaseRepository
        # return SupabaseRepository(settings, logger)
        raise NotImplementedError(
            "Supabase repository implementation is in adapters layer"
        )

    @staticmethod
    def create_mock_repository(logger: Logger) -> Any:
        """
        Create a mock repository for testing.

        Args:
            logger: Logger instance

        Returns:
            Mock repository instance
        """
        # Import here to avoid circular dependencies
        # from ...adapters.mock.repository import MockRepository
        # return MockRepository(logger)
        raise NotImplementedError(
            "Mock repository implementation is in adapters layer"
        )


class ServiceProvider:
    """Provider for service instances."""

    @staticmethod
    def create_entity_service(
        repository: Any,
        logger: Logger,
        cache: Optional[Cache] = None,
    ) -> Any:
        """
        Create an entity service instance.

        Args:
            repository: Repository instance
            logger: Logger instance
            cache: Optional cache instance

        Returns:
            Entity service instance

        Note:
            Actual implementation will be in domain/services/
            This is a placeholder for the provider pattern.
        """
        # Import here to avoid circular dependencies
        # from ...domain.services.entity import EntityService
        # return EntityService(repository, logger, cache)
        raise NotImplementedError(
            "Entity service implementation is in domain layer"
        )

    @staticmethod
    def create_relationship_service(
        repository: Any,
        logger: Logger,
        cache: Optional[Cache] = None,
    ) -> Any:
        """
        Create a relationship service instance.

        Args:
            repository: Repository instance
            logger: Logger instance
            cache: Optional cache instance

        Returns:
            Relationship service instance
        """
        # Import here to avoid circular dependencies
        # from ...domain.services.relationship import RelationshipService
        # return RelationshipService(repository, logger, cache)
        raise NotImplementedError(
            "Relationship service implementation is in domain layer"
        )

    @staticmethod
    def create_workflow_service(
        entity_service: Any,
        relationship_service: Any,
        logger: Logger,
    ) -> Any:
        """
        Create a workflow service instance.

        Args:
            entity_service: Entity service instance
            relationship_service: Relationship service instance
            logger: Logger instance

        Returns:
            Workflow service instance
        """
        # Import here to avoid circular dependencies
        # from ...domain.services.workflow import WorkflowService
        # return WorkflowService(entity_service, relationship_service, logger)
        raise NotImplementedError(
            "Workflow service implementation is in domain layer"
        )


class AdapterProvider:
    """Provider for adapter instances."""

    @staticmethod
    def create_vertex_ai_adapter(
        settings: Settings,
        logger: Logger,
    ) -> Any:
        """
        Create a Vertex AI adapter instance.

        Args:
            settings: Application settings
            logger: Logger instance

        Returns:
            Vertex AI adapter instance
        """
        # Import here to avoid circular dependencies
        # from ...adapters.vertex_ai.embeddings import VertexAIEmbeddingsAdapter
        # return VertexAIEmbeddingsAdapter(settings, logger)
        raise NotImplementedError(
            "Vertex AI adapter implementation is in adapters layer"
        )

    @staticmethod
    def create_workos_adapter(
        settings: Settings,
        logger: Logger,
    ) -> Any:
        """
        Create a WorkOS adapter instance.

        Args:
            settings: Application settings
            logger: Logger instance

        Returns:
            WorkOS adapter instance
        """
        # Import here to avoid circular dependencies
        # from ...adapters.workos.auth import WorkOSAuthAdapter
        # return WorkOSAuthAdapter(settings, logger)
        raise NotImplementedError(
            "WorkOS adapter implementation is in adapters layer"
        )


def create_full_dependency_graph(settings: Optional[Settings] = None) -> dict[str, Any]:
    """
    Create full dependency graph with all services and adapters.

    Args:
        settings: Application settings (uses global if not provided)

    Returns:
        Dictionary with all dependencies

    Note:
        This is a helper function for setting up the complete application.
        In practice, you would use the Container class for DI.
    """
    from ..config.settings import get_settings

    # Get or use provided settings
    settings = settings or get_settings()

    # Create core dependencies
    logger = LoggerProvider.create()
    cache = CacheProvider.create(settings)

    # Note: Repository, service, and adapter creation would happen here
    # once those layers are implemented. For now, this serves as a template.

    dependencies = {
        "settings": settings,
        "logger": logger,
        "cache": cache,
        # "repository": repository,
        # "entity_service": entity_service,
        # "relationship_service": relationship_service,
        # "workflow_service": workflow_service,
    }

    return dependencies
