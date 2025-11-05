"""
Dependency injection container.

This module provides a simple DI container for managing application
dependencies using factory pattern without complex frameworks.
"""

from typing import Any, Callable, Optional, TypeVar

from ..cache.provider import create_cache_provider
from ..config.settings import Settings, get_settings
from ..logging.logger import get_logger

T = TypeVar("T")


class Container:
    """
    Dependency injection container.

    Manages singleton and transient dependencies with factory methods
    for creating and retrieving instances.
    """

    def __init__(self):
        """Initialize container with empty registries."""
        self._singletons: dict[str, Any] = {}
        self._factories: dict[str, Callable[[], Any]] = {}
        self._initialized = False

    def initialize(self, settings: Optional[Settings] = None) -> None:
        """
        Initialize container with settings and register core dependencies.

        Args:
            settings: Application settings (uses global if not provided)
        """
        if self._initialized:
            return

        # Use provided settings or get global instance
        self._settings = settings or get_settings()

        # Register core singletons
        self._register_core_singletons()

        self._initialized = True

    def _register_core_singletons(self) -> None:
        """Register core singleton dependencies."""
        # Settings singleton
        self._singletons["settings"] = self._settings

        # Logger singleton
        logger = get_logger("atoms_mcp")
        self._singletons["logger"] = logger

        # Cache singleton
        cache = create_cache_provider(
            backend=self._settings.cache.backend.value,
            redis_url=self._settings.cache.redis_url,
            max_size=self._settings.cache.max_size,
            default_ttl=self._settings.cache.default_ttl,
        )
        self._singletons["cache"] = cache

    def get(self, key: str) -> Any:
        """
        Get dependency by key.

        Args:
            key: Dependency identifier

        Returns:
            Dependency instance

        Raises:
            KeyError: If dependency not found
        """
        if not self._initialized:
            raise RuntimeError("Container not initialized. Call initialize() first.")

        # Check singletons first
        if key in self._singletons:
            return self._singletons[key]

        # Check factories
        if key in self._factories:
            return self._factories[key]()

        raise KeyError(f"Dependency not found: {key}")

    def register_singleton(self, key: str, instance: Any) -> None:
        """
        Register a singleton instance.

        Args:
            key: Dependency identifier
            instance: Singleton instance
        """
        self._singletons[key] = instance

    def register_factory(self, key: str, factory: Callable[[], Any]) -> None:
        """
        Register a factory function for transient dependencies.

        Args:
            key: Dependency identifier
            factory: Factory function that creates instances
        """
        self._factories[key] = factory

    def register_transient(self, key: str, factory: Callable[[], Any]) -> None:
        """
        Register a transient dependency (alias for register_factory).

        Args:
            key: Dependency identifier
            factory: Factory function that creates instances
        """
        self.register_factory(key, factory)

    def has(self, key: str) -> bool:
        """
        Check if dependency is registered.

        Args:
            key: Dependency identifier

        Returns:
            True if dependency exists, False otherwise
        """
        return key in self._singletons or key in self._factories

    def clear(self) -> None:
        """Clear all registered dependencies (mainly for testing)."""
        self._singletons.clear()
        self._factories.clear()
        self._initialized = False

    @property
    def settings(self) -> Settings:
        """Get settings instance."""
        return self.get("settings")

    @property
    def logger(self) -> Any:
        """Get logger instance."""
        return self.get("logger")

    @property
    def cache(self) -> Any:
        """Get cache instance."""
        return self.get("cache")

    def create_scope(self) -> "Scope":
        """
        Create a new dependency scope.

        Returns:
            New scope instance
        """
        return Scope(self)


class Scope:
    """
    Dependency scope for request-scoped dependencies.

    Provides a way to create short-lived dependency instances
    that are cleaned up after the scope is exited.
    """

    def __init__(self, container: Container):
        """
        Initialize scope.

        Args:
            container: Parent container
        """
        self._container = container
        self._scoped_instances: dict[str, Any] = {}

    def get(self, key: str) -> Any:
        """
        Get dependency from scope or parent container.

        Args:
            key: Dependency identifier

        Returns:
            Dependency instance
        """
        # Check scoped instances first
        if key in self._scoped_instances:
            return self._scoped_instances[key]

        # Fall back to container
        return self._container.get(key)

    def register(self, key: str, instance: Any) -> None:
        """
        Register scoped instance.

        Args:
            key: Dependency identifier
            instance: Instance to register
        """
        self._scoped_instances[key] = instance

    def clear(self) -> None:
        """Clear scoped instances."""
        self._scoped_instances.clear()

    def __enter__(self) -> "Scope":
        """Enter scope context."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit scope context and clear instances."""
        self.clear()


# Global container instance
_container: Optional[Container] = None


def get_container() -> Container:
    """
    Get the global container instance.

    Returns:
        Global container instance
    """
    global _container
    if _container is None:
        _container = Container()
        _container.initialize()
    return _container


def reset_container() -> None:
    """Reset the global container (mainly for testing)."""
    global _container
    if _container is not None:
        _container.clear()
    _container = None


def inject(key: str) -> Any:
    """
    Inject dependency by key.

    Convenience function for dependency injection.

    Args:
        key: Dependency identifier

    Returns:
        Dependency instance
    """
    return get_container().get(key)
