"""
In-memory cache implementation with LRU eviction.

This module provides a thread-safe in-memory cache with automatic
expiration and LRU (Least Recently Used) eviction policy.
"""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from typing import Any, Optional

from atoms_mcp.domain.ports.cache import Cache


class MemoryCache(Cache):
    """
    Thread-safe in-memory cache with LRU eviction.

    This cache implementation:
    - Uses OrderedDict for LRU tracking
    - Thread-safe operations with locks
    - Automatic expiration based on TTL
    - Configurable maximum size
    - No external dependencies
    """

    def __init__(self, max_size: int = 1000, default_ttl: int = 300) -> None:
        """
        Initialize memory cache.

        Args:
            max_size: Maximum number of items in cache
            default_ttl: Default time-to-live in seconds
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self._lock = threading.RLock()

    def _is_expired(self, expiry: float) -> bool:
        """
        Check if an item has expired.

        Args:
            expiry: Expiry timestamp (0 means no expiration)

        Returns:
            True if expired, False otherwise
        """
        if expiry == 0:
            return False
        return time.time() > expiry

    def _evict_expired(self) -> None:
        """Remove expired items from cache."""
        current_time = time.time()
        expired_keys = [
            key
            for key, (_, expiry) in self._cache.items()
            if expiry > 0 and current_time > expiry
        ]

        for key in expired_keys:
            del self._cache[key]

    def _evict_lru(self) -> None:
        """Evict least recently used item if cache is full."""
        if len(self._cache) >= self.max_size:
            # Remove oldest item (first in OrderedDict)
            self._cache.popitem(last=False)

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve a value from the cache.

        Args:
            key: Cache key

        Returns:
            Cached value if exists and not expired, None otherwise
        """
        with self._lock:
            # Clean up expired items periodically
            if len(self._cache) % 100 == 0:
                self._evict_expired()

            if key not in self._cache:
                return None

            value, expiry = self._cache[key]

            # Check expiration
            if self._is_expired(expiry):
                del self._cache[key]
                return None

            # Move to end (mark as recently used)
            self._cache.move_to_end(key)

            return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Store a value in the cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (None = use default, 0 = no expiration)

        Returns:
            True if successful
        """
        with self._lock:
            # Calculate expiry time
            if ttl is None:
                ttl = self.default_ttl

            expiry = time.time() + ttl if ttl > 0 else 0

            # Evict LRU if needed
            if key not in self._cache:
                self._evict_lru()

            # Store value
            self._cache[key] = (value, expiry)

            # Move to end (mark as recently used)
            self._cache.move_to_end(key)

            return True

    def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.

        Args:
            key: Cache key

        Returns:
            True if key existed and was deleted, False otherwise
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> bool:
        """
        Clear all values from the cache.

        Returns:
            True if successful
        """
        with self._lock:
            self._cache.clear()
            return True

    def exists(self, key: str) -> bool:
        """
        Check if a key exists in the cache.

        Args:
            key: Cache key

        Returns:
            True if key exists and not expired, False otherwise
        """
        with self._lock:
            if key not in self._cache:
                return False

            _, expiry = self._cache[key]

            # Check expiration
            if self._is_expired(expiry):
                del self._cache[key]
                return False

            return True

    def get_many(self, keys: list[str]) -> dict[str, Any]:
        """
        Retrieve multiple values from the cache.

        Args:
            keys: List of cache keys

        Returns:
            Dictionary mapping keys to values (missing keys are omitted)
        """
        result = {}

        for key in keys:
            value = self.get(key)
            if value is not None:
                result[key] = value

        return result

    def set_many(self, mapping: dict[str, Any], ttl: Optional[int] = None) -> bool:
        """
        Store multiple values in the cache.

        Args:
            mapping: Dictionary mapping keys to values
            ttl: Time-to-live in seconds (None = use default)

        Returns:
            True if all successful
        """
        for key, value in mapping.items():
            if not self.set(key, value, ttl):
                return False

        return True

    def size(self) -> int:
        """
        Get current cache size.

        Returns:
            Number of items in cache
        """
        with self._lock:
            # Clean up expired items
            self._evict_expired()
            return len(self._cache)

    def get_stats(self) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        with self._lock:
            self._evict_expired()

            total_items = len(self._cache)
            expired_items = sum(
                1
                for _, (_, expiry) in self._cache.items()
                if self._is_expired(expiry)
            )

            return {
                "total_items": total_items,
                "expired_items": expired_items,
                "max_size": self.max_size,
                "utilization": total_items / self.max_size if self.max_size > 0 else 0,
            }
