"""
Abstract cache interface (port).

This module defines the cache interface that infrastructure
implementations must satisfy. Pure ABC with no external dependencies.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class Cache(ABC):
    """
    Abstract base class for caching.

    Caches provide temporary storage for frequently accessed data
    without coupling the domain to specific cache implementations.
    """

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve a value from the cache.

        Args:
            key: Cache key

        Returns:
            Cached value if exists and not expired, None otherwise
        """
        pass

    @abstractmethod
    def set(
        self, key: str, value: Any, ttl: Optional[int] = None
    ) -> bool:
        """
        Store a value in the cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (None = no expiration)

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.

        Args:
            key: Cache key

        Returns:
            True if key existed and was deleted, False otherwise
        """
        pass

    @abstractmethod
    def clear(self) -> bool:
        """
        Clear all values from the cache.

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """
        Check if a key exists in the cache.

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise
        """
        pass

    @abstractmethod
    def get_many(self, keys: list[str]) -> dict[str, Any]:
        """
        Retrieve multiple values from the cache.

        Args:
            keys: List of cache keys

        Returns:
            Dictionary mapping keys to values (missing keys are omitted)
        """
        pass

    @abstractmethod
    def set_many(
        self, mapping: dict[str, Any], ttl: Optional[int] = None
    ) -> bool:
        """
        Store multiple values in the cache.

        Args:
            mapping: Dictionary mapping keys to values
            ttl: Time-to-live in seconds (None = no expiration)

        Returns:
            True if all successful, False otherwise
        """
        pass
