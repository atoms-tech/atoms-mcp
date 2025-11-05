"""
Cache adapter module with provider factory.

This module provides cache implementations and a factory for
creating the appropriate cache based on configuration.
"""

from __future__ import annotations

from typing import Optional

from atoms_mcp.adapters.secondary.cache.adapters.memory import MemoryCache
from atoms_mcp.adapters.secondary.cache.adapters.redis import RedisCache, RedisCacheError
from atoms_mcp.domain.ports.cache import Cache
from atoms_mcp.infrastructure.config.settings import CacheBackend, get_settings


class CacheFactory:
    """
    Factory for creating cache instances based on configuration.

    This factory supports:
    - In-memory cache (default)
    - Redis cache (if Redis is available)
    - Automatic fallback to memory cache on Redis errors
    """

    @staticmethod
    def create_cache(
        backend: Optional[CacheBackend] = None,
        fallback_to_memory: bool = True,
    ) -> Cache:
        """
        Create cache instance based on backend type.

        Args:
            backend: Cache backend type (uses settings if None)
            fallback_to_memory: If True, fall back to memory cache on Redis errors

        Returns:
            Cache instance

        Raises:
            RuntimeError: If cache creation fails and fallback is disabled
        """
        settings = get_settings()

        # Use provided backend or get from settings
        backend = backend or settings.cache.backend

        if backend == CacheBackend.REDIS:
            try:
                # Try to create Redis cache
                return RedisCache(
                    redis_url=settings.cache.redis_url,
                    host=settings.cache.redis_host,
                    port=settings.cache.redis_port,
                    db=settings.cache.redis_db,
                    password=settings.cache.redis_password,
                    max_connections=settings.cache.redis_max_connections,
                    default_ttl=settings.cache.default_ttl,
                )
            except (RedisCacheError, ImportError) as e:
                if fallback_to_memory:
                    # Fall back to memory cache
                    import logging

                    logger = logging.getLogger(__name__)
                    logger.warning(
                        f"Failed to create Redis cache, falling back to memory: {e}"
                    )
                    return MemoryCache(
                        max_size=settings.cache.max_size,
                        default_ttl=settings.cache.default_ttl,
                    )
                else:
                    raise RuntimeError(f"Failed to create Redis cache: {e}") from e

        # Default to memory cache
        return MemoryCache(
            max_size=settings.cache.max_size,
            default_ttl=settings.cache.default_ttl,
        )


# Global cache instance
_cache: Optional[Cache] = None


def get_cache() -> Cache:
    """
    Get the global cache instance.

    Returns:
        Cache instance
    """
    global _cache

    if _cache is None:
        _cache = CacheFactory.create_cache()

    return _cache


def reset_cache() -> None:
    """
    Reset the global cache instance.

    This clears the cached instance and forces recreation
    on the next get_cache() call.
    """
    global _cache
    _cache = None


__all__ = [
    "Cache",
    "MemoryCache",
    "RedisCache",
    "RedisCacheError",
    "CacheFactory",
    "get_cache",
    "reset_cache",
]
