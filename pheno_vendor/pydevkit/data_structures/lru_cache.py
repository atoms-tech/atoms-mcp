"""LRU (Least Recently Used) Cache implementation."""

from typing import Any, Optional, Dict
from collections import OrderedDict


class LRUCache:
    """
    LRU Cache with O(1) get and set operations.

    Example:
        cache = LRUCache(capacity=100)
        cache.set('key', 'value')
        value = cache.get('key')
    """

    def __init__(self, capacity: int = 128):
        """
        Initialize LRU cache.

        Args:
            capacity: Maximum number of items to store
        """
        if capacity <= 0:
            raise ValueError("Capacity must be positive")

        self.capacity = capacity
        self._cache: OrderedDict = OrderedDict()
        self._hits = 0
        self._misses = 0

    def get(self, key: Any, default: Any = None) -> Any:
        """
        Get value from cache.

        Args:
            key: Cache key
            default: Default value if not found

        Returns:
            Cached value or default
        """
        if key in self._cache:
            self._hits += 1
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            return self._cache[key]

        self._misses += 1
        return default

    def set(self, key: Any, value: Any) -> None:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
        """
        if key in self._cache:
            # Update existing key
            self._cache.move_to_end(key)
        else:
            # Add new key
            if len(self._cache) >= self.capacity:
                # Remove least recently used item
                self._cache.popitem(last=False)

        self._cache[key] = value

    def delete(self, key: Any) -> bool:
        """
        Delete key from cache.

        Args:
            key: Cache key

        Returns:
            True if key was deleted, False if not found
        """
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def clear(self) -> None:
        """Clear all items from cache."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0

    def has(self, key: Any) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists
        """
        return key in self._cache

    def size(self) -> int:
        """Get current cache size."""
        return len(self._cache)

    def hit_rate(self) -> float:
        """
        Calculate cache hit rate.

        Returns:
            Hit rate as percentage (0.0 to 1.0)
        """
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0

    def stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        return {
            'size': self.size(),
            'capacity': self.capacity,
            'hits': self._hits,
            'misses': self._misses,
            'hit_rate': self.hit_rate(),
        }

    def __len__(self) -> int:
        """Get cache size."""
        return len(self._cache)

    def __contains__(self, key: Any) -> bool:
        """Check if key exists."""
        return key in self._cache

    def __repr__(self) -> str:
        """String representation."""
        return f"LRUCache(size={self.size()}, capacity={self.capacity}, hit_rate={self.hit_rate():.2%})"
